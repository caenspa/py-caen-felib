"""
@ingroup Python
"""

from __future__ import annotations  # MyPy not supporting Self

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2020-2022 CAEN SpA'
__license__ = 'LGPLv3+'

import ctypes as ct
from enum import Enum
from json import dumps, loads
from typing import Any, Dict, List, Optional, Tuple, Type, TypedDict

import numpy as np
# from typing_extensions import Self # MyPy 0.991 not supporting Self, use annotations

from caen_felib import lib, utils


_type_map: Dict[str, Type] = {
    'U8': ct.c_uint8,
    'U16': ct.c_uint16,
    'U32': ct.c_uint32,
    'U64': ct.c_uint64,
    'I8': ct.c_int8,
    'I16': ct.c_int16,
    'I32': ct.c_int32,
    'I64': ct.c_int64,
    'CHAR': ct.c_char,
    'BOOL': ct.c_bool,
    'SIZE_T': ct.c_size_t,
    # 'PTRDIFF_T' unsupported on Python
    'FLOAT': ct.c_float,
    'DOUBLE': ct.c_double,
    'LONG DOUBLE': ct.c_longdouble,
}


class _Data:
    """
    Class representing data set by Node.set_read_data_format().
    It holds a `numpy.ndarray` allocated with shape specified
    in the data format.
    """

    # Public fields
    name: str
    type: str
    dim: int
    shape: List[int]
    dtype: np.dtype
    value: np.ndarray
    proxy_value_2d: Optional[np.ndarray]
    arg: Any

    # Type aliases
    class _DataField(TypedDict, total=False):
        name: str
        type: str
        dim: int
        shape: List[int]

    def __init__(self, data_field: _DataField) -> None:

        # Default attributes from fields passed to C library

        ## Field name
        self.name = data_field['name']
        ## Field type
        self.type = data_field['type']
        ## Field dimension
        self.dim = data_field.get('dim', 0)
        ## Field shape (it is a Python extension to allow local allocation)
        self.shape = data_field.get('shape', [])

        if self.dim != len(self.shape):
            raise RuntimeError('shape length must match dim')

        ## Data type of value
        self.dtype = np.dtype(_type_map[self.type])
        ## Instance of `numpy.ndarray` that holds data
        self.value = np.empty(self.shape, dtype=self.dtype)
        ## Proxy array of pointers used when dim >= 2 (see below)
        self.proxy_value_2d = None
        ## ctypes pointer to _Data.value that is used within Node.read_data
        self.arg = self.__generate_arg()

    def __generate_arg(self) -> Any:
        value: np.ndarray
        if self.dim < 2:
            # NumPy 0D and 1D arrays can be used directly.
            value = self.value
        else:
            # NumPy 2D arrays cannot be directly used because they are
            # implemented as contiguous memory blocks instead of arrays of
            # pointers, used by CAEN_FELib.
            # To overcome the problem we generate a proxy ndarray of pointers.
            ptr_gen = (v.ctypes.data for v in self.value)
            self.proxy_value_2d = np.fromiter(ptr_gen, dtype=ct.c_void_p)
            value = self.proxy_value_2d
        # value.ctypes is equivalent to value.ctypes.data_as(ctypes.c_void_p),
        # that is fine for us.
        return value.ctypes

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name}, {self.type})'

    def __str__(self) -> str:
        return self.name


class NodeType(Enum):
    """
    Wrapper to ::CAEN_FELib_NodeType_t
    """
    UNKNOWN = -1
    PARAMETER = 0
    COMMAND = 1
    FEATURE = 2
    ATTRIBUTE = 3
    ENDPOINT = 4
    CHANNEL = 5
    DIGITIZER = 6
    FOLDER = 7
    LVDS = 8
    VGA = 9
    HV_CHANNEL = 10
    MONOUT = 11
    VTRACE = 12
    GROUP = 13


class Node:
    """
    Class representing a node.
    """

    handle: int
    data: Tuple[_Data, ...]

    def __init__(self, handle: int) -> None:
        ## Handle representing the node on the C library
        self.handle = handle
        ## Endpoint data (inizialized by set_read_data_format())
        self.data = ()

    # C API wrappers

    @classmethod
    def open(cls: Type[Node], url: str) -> Node:
        """
        Wrapper to CAEN_FELib_Open()

        @param[in] url				URL of device to connect (a string, with format `scheme://[host][/path][?query][#fragment]`)
        @return						the digitizer node
        @exception					error.Error in case of error
        """
        value = ct.c_uint64()
        lib.open(utils.to_bytes(url), value)
        return cls(value.value)

    def close(self) -> None:
        """
        Wrapper to CAEN_FELib_Close()

        @exception					error.Error in case of error
        """
        lib.close(self.handle)

    @utils.lru_cache_method
    def get_child_nodes(self, path: Optional[str] = None, initial_size: int = 2**6) -> Tuple[Node, ...]:
        """
        Wrapper to CAEN_FELib_GetChildHandles()

        @sa child_nodes
        @param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
        @param[in] initial_size		inizial size to allocate for the first iteration
        @return						child nodes (a list)
        @exception					error.Error in case of error
        """
        b_path = utils.to_bytes_opt(path)
        while True:
            child_handles = np.empty([initial_size], dtype=ct.c_uint64)
            child_handles_arg = child_handles.ctypes.data_as(ct.POINTER(ct.c_uint64))
            res = lib.get_child_handles(self.handle, b_path, child_handles_arg, initial_size)
            if res <= initial_size:
                return *(Node(handle.item()) for handle in child_handles[:res]),
            initial_size = res

    @utils.lru_cache_method
    def get_parent_node(self, path: Optional[str] = None) -> Node:
        """
        Wrapper to CAEN_FELib_GetParentHandle()

        @sa parent_node
        @param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
        @return						parent node
        @exception					error.Error in case of error
        """
        value = ct.c_uint64()
        lib.get_parent_handle(self.handle, utils.to_bytes_opt(path), value)
        return Node(value.value)

    @utils.lru_cache_method
    def get_node(self, path: Optional[str] = None) -> Node:
        """
        Wrapper to CAEN_FELib_GetHandle()

        @param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
        @return						node at the provided path
        @exception					error.Error in case of error
        """
        value = ct.c_uint64()
        lib.get_handle(self.handle, utils.to_bytes_opt(path), value)
        return Node(value.value)

    @utils.lru_cache_method
    def get_path(self) -> str:
        """
        Wrapper to CAEN_FELib_GetPath()

        @sa path
        @return						absolute path of the provided handle (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(256)
        lib.get_path(self.handle, value)
        return value.value.decode()

    @utils.lru_cache_method
    def get_node_properties(self, path: Optional[str] = None) -> Tuple[str, NodeType]:
        """
        Wrapper to CAEN_FELib_GetNodeProperties()

        @sa name and Node.type
        @param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
        @return						tuple containing node name (a string) and the node type (a NodeType)
        @exception					error.Error in case of error
        """
        name = ct.create_string_buffer(32)
        node_type = ct.c_int()
        lib.get_node_properties(self.handle, utils.to_bytes_opt(path), name, node_type)
        return name.value.decode(), NodeType(node_type.value)

    def get_device_tree(self, initial_size: int = 2**22) -> Dict:
        """
        Wrapper to CAEN_FELib_GetDeviceTree()

        @param[in] initial_size		inizial size to allocate for the first iteration
        @return						JSON representation of the node structure (a dictionary)
        @exception					error.Error in case of error
        """
        while True:
            device_tree = ct.create_string_buffer(initial_size)
            res = lib.get_device_tree(self.handle, device_tree, initial_size)
            if res < initial_size:  # equal not fine, see docs
                return loads(device_tree.value.decode())
            initial_size = res

    def get_value(self, path: Optional[str] = None) -> str:
        """
        Wrapper to CAEN_FELib_GetValue()

        @sa value
        @param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
        @return						value of the node (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(256)
        lib.get_value(self.handle, utils.to_bytes_opt(path), value)
        return value.value.decode()

    def get_value_with_arg(self, path: Optional[str], arg: str) -> str:
        """
        Wrapper to CAEN_FELib_GetValue()

        @param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
        @param[in] arg				optional argument (either a string or `None` that is interpreted as an empty string)
        @return						value of the node (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(utils.to_bytes(arg), 256)
        lib.get_value(self.handle, utils.to_bytes_opt(path), value)
        return value.value.decode()

    def set_value(self, path: Optional[str], value: str) -> None:
        """
        Wrapper to CAEN_FELib_SetValue()

        @sa value
        @param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
        @param[in] value			value to set (a string)
        @exception					error.Error in case of error
        """
        lib.set_value(self.handle, utils.to_bytes_opt(path), utils.to_bytes(value))

    def get_user_register(self, address: int) -> int:
        """
        Wrapper to CAEN_FELib_GetUserRegister()

        @param[in] address			user register address
        @return						value of the register (a int)
        @exception					error.Error in case of error
        """
        value = ct.c_uint32()
        lib.get_user_register(self.handle, address, value)
        return value.value

    def set_user_register(self, address: int, value: int) -> None:
        """
        Wrapper to CAEN_FELib_SetUserRegister()

        @param[in] address			user register address
        @param[in] value			value of the register
        @exception					error.Error in case of error
        """
        lib.set_user_register(self.handle, address, value)

    def send_command(self, path: Optional[str] = None) -> None:
        """
        Wrapper to CAEN_FELib_SendCommand()

        @sa __call__
        @param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
        @exception					error.Error in case of error
        """
        lib.send_command(self.handle, utils.to_bytes_opt(path))

    def set_read_data_format(self, fmt: List[_Data._DataField]) -> None:
        """
        Wrapper to CAEN_FELib_SetReadDataFormat()

        In addition to what happens in C library, it also allocate data. Size of fields
        with `dim > 0` must be specified by a `"shape"` entry in the field description,
        that is a vector passed to the `shape` argument of `np.empty` constructor.
        On fields with `dim == 0` the shape can be omitted, and is set to `[]` by default.
        Fields can be accessed on data attribute of this class, that is a list of _Data
        inizialized with the field descriptions, in the same order of @p format.

        Example:
        ```
        nch = dig.par.numch.value
        reclen = dig.par.recordlengths.value
        format = [
            {
                'name': 'WAVEFORM',
                'type': 'U16',
                'dim': 2,
                'shape': [nch, reclen],
            },
        ]
        ep_node.set_read_data_format(format)
        print(ep_node.data[0])
        ```

        @param[in] fmt				JSON representation of the format, in compliance with the endpoint "format" property (a list of dictionaries)
        @exception					error.Error in case of error
        """
        lib.set_read_data_format(self.handle, dumps(fmt).encode())

        # Allocate requested fields
        self.data = *(_Data(f) for f in fmt),

        # Important:
        # Do not update lib.ReadData.argtypes with data.argtype because lib.ReadData
        # is shared with all other endpoints and it would not be thread safe.
        # More details on a comment on the caen_felib.lib constructor.
        # Possible unsafe code could be:
        # lib.ReadData.argtypes = [ct.c_uint64, ct.c_int] + [d.argtype for d in self.data]

    def read_data(self, timeout: int) -> None:
        """
        Wrapper to CAEN_FELib_ReadData()

        Unlike what happens in C library, variadic arguments are added automatically
        according to what has been specified by set_read_data_format(). Data can be
        retrieved using the data attribute of this class.

        Example:
        ```
        # Get reference to data
        data_0 = ep_node.data[0].value

        # Start acquisition
        dig.cmd.armacquisition()
        dig.cmd.swstartacquisition()

        while True:
            try:
                ep_node.read_data(100)
            except error.Error as ex:
                if ex.code == error.ErrorCode.Timeout:
                    continue
                elif ex.code == error.ErrorCode.Stop:
                    break
                else:
                    raise ex

            # Do stuff with data
            print(data_0)

        dig.cmd.disarmacquisition()
        ```

        @param[in] timeout			timeout of the function in milliseconds; if this value is -1 the function is blocking with infinite timeout
        @return						data
        @exception					error.Error in case of error
        """
        lib.read_data(self.handle, timeout, *(d.arg for d in self.data))

    def has_data(self, timeout: int) -> None:
        """
        Wrapper to CAEN_FELib_HasData()

        @param[in] timeout			timeout of the function in milliseconds; if this value is -1 the function is blocking with infinite timeout
        @exception					error.Error in case of error
        """
        lib.has_data(self.handle, timeout)

    # Python utilities

    @property
    def name(self) -> str:
        """Node name"""
        return self.get_node_properties(None)[0]

    @property
    def type(self) -> NodeType:
        """Node type"""
        return self.get_node_properties(None)[1]

    @property
    def path(self) -> str:
        """Node absolute path"""
        return self.get_path()

    @property
    def parent_node(self) -> Node:
        """Parent node"""
        return self.get_parent_node(None)

    @property
    def child_nodes(self) -> Tuple[Node, ...]:
        """List of child nodes"""
        return self.get_child_nodes(None)

    @property
    def value(self) -> str:
        """Current value"""
        return self.get_value(None)

    @value.setter
    def value(self, value: str) -> None:
        self.set_value(None, value)

    def __call__(self) -> None:
        """Execute node"""
        self.send_command(None)

    def __enter__(self) -> Node:
        """Used by `with`"""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Called when exiting from `with` block"""
        self.close()

    def __getitem__(self, index: Any) -> Node:
        return self.get_node(f'/{index}')

    def __getattr__(self, name: str) -> Node:
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        return self.__getitem__(name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.path})'

    def __str__(self) -> str:
        return self.path


def connect(url: str) -> Node:
    """
    Connect to a device. Same of Node.open().

    Example:
    ```
    with device.connect("dig2://<host>") as dig:
        # Do stuff here...
    ```
    @sa Node.open()
    @param[in] url				URL of device to connect (a string, with format `scheme://[host][/path][?query][#fragment]`)
    @return						the digitizer node
    @exception					error.Error in case of error
    """
    return Node.open(url)
