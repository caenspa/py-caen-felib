"""
@ingroup Python
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2020-2022 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'  # SPDX-License-Identifier

import ctypes as ct
import ctypes.util as ctutil
from json import loads
from sys import platform
from typing import Any, Callable, Dict, List, Tuple, Type
from typing_extensions import TypeAlias

from caen_felib import error

# Comments on imports:
# - TypeAlias moved to typing on Python 3.10


class _Lib:
    """
    This class loads the CAEN_FELib shared library and
    exposes its functions on its public attributes
    using ctypes.
    """

    APIType: TypeAlias = Callable[..., int]

    path: str

    open: APIType
    close: APIType
    get_device_tree: APIType
    get_child_handles: APIType
    get_parent_handle: APIType
    get_handle: APIType
    get_path: APIType
    get_node_properties: APIType
    get_value: APIType
    set_value: APIType
    get_user_register: APIType
    set_user_register: APIType
    send_command: APIType
    set_read_data_format: APIType
    has_data: APIType
    read_data: APIType

    def __init__(self, name: str) -> None:
        self.__load_lib(name)
        self.__load_api()

    def __load_lib(self, name: str) -> None:
        loader: ct.LibraryLoader
        loader_variadic: ct.LibraryLoader

        # Platform dependent stuff
        if platform.startswith('win32'):
            # API functions are declared as __stdcall, but variadic
            # functions are __cdecl even if declared as __stdcall.
            # This difference applies only to 32 bit applications,
            # 64 bit applications have its own calling convention.
            loader = ct.windll
            loader_variadic = ct.cdll
        else:
            loader = ct.cdll
            loader_variadic = ct.cdll

        path = ctutil.find_library(name)
        if path is None:
            raise RuntimeError(
                f'Library {name} not found. '
                'This module requires the latest version of '
                'CAEN FE Library to be installed on your system. '
                'You may find the official installers at '
                'https://www.caen.it/products/caen-felib-library/. '
                'Please install it and retry.'
            )

        ## Library path on the filesystem
        self.path = path

        # Load library
        self.__lib = loader.LoadLibrary(self.path)
        self.__lib_variadic = loader_variadic.LoadLibrary(self.path)

    def __load_api(self) -> None:
        # Load API not related to devices
        self.__get_lib_info = self.__lib.CAEN_FELib_GetLibInfo
        self.__set(self.__get_lib_info, [ct.c_char_p, ct.c_size_t])

        self.__get_lib_version = self.__lib.CAEN_FELib_GetLibVersion
        self.__set(self.__get_lib_version, [ct.c_char_p])

        self.__get_error_name = self.__lib.CAEN_FELib_GetErrorName
        self.__set(self.__get_error_name, [ct.c_int, ct.c_char_p])

        self.__get_error_description = self.__lib.CAEN_FELib_GetErrorDescription
        self.__set(self.__get_error_description, [ct.c_int, ct.c_char_p])

        self.__get_last_error = self.__lib.CAEN_FELib_GetLastError
        self.__set(self.__get_last_error, [ct.c_char_p])

        self.__devices_discovery = self.__lib.CAEN_FELib_DevicesDiscovery
        self.__set(self.__devices_discovery, [ct.c_char_p, ct.c_size_t, ct.c_int])

        # Load API
        self.open = self.__lib.CAEN_FELib_Open
        self.__set(self.open, [ct.c_char_p, ct.POINTER(ct.c_uint64)])

        self.close = self.__lib.CAEN_FELib_Close
        self.__set(self.close, [ct.c_uint64])

        self.get_device_tree = self.__lib.CAEN_FELib_GetDeviceTree
        self.__set(self.get_device_tree, [ct.c_uint64, ct.c_char_p, ct.c_size_t])

        self.get_child_handles = self.__lib.CAEN_FELib_GetChildHandles
        self.__set(self.get_child_handles, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64), ct.c_size_t])

        self.get_parent_handle = self.__lib.CAEN_FELib_GetParentHandle
        self.__set(self.get_parent_handle, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64)])

        self.get_handle = self.__lib.CAEN_FELib_GetHandle
        self.__set(self.get_handle, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64)])

        self.get_path = self.__lib.CAEN_FELib_GetPath
        self.__set(self.get_path, [ct.c_uint64, ct.c_char_p])

        self.get_node_properties = self.__lib.CAEN_FELib_GetNodeProperties
        self.__set(self.get_node_properties, [ct.c_uint64, ct.c_char_p, ct.c_char_p, ct.POINTER(ct.c_int)])

        self.get_value = self.__lib.CAEN_FELib_GetValue
        self.__set(self.get_value, [ct.c_uint64, ct.c_char_p, ct.c_char_p])

        self.set_value = self.__lib.CAEN_FELib_SetValue
        self.__set(self.set_value, [ct.c_uint64, ct.c_char_p, ct.c_char_p])

        self.get_user_register = self.__lib.CAEN_FELib_GetUserRegister
        self.__set(self.get_user_register, [ct.c_uint64, ct.c_uint32, ct.POINTER(ct.c_uint32)])

        self.set_user_register = self.__lib.CAEN_FELib_SetUserRegister
        self.__set(self.set_user_register, [ct.c_uint64, ct.c_uint32, ct.c_uint32])

        self.send_command = self.__lib.CAEN_FELib_SendCommand
        self.__set(self.send_command, [ct.c_uint64, ct.c_char_p])

        self.set_read_data_format = self.__lib.CAEN_FELib_SetReadDataFormat
        self.__set(self.set_read_data_format, [ct.c_uint64, ct.c_char_p])

        self.has_data = self.__lib.CAEN_FELib_HasData
        self.__set(self.has_data, [ct.c_uint64, ct.c_int])

        # Load variadic API
        # Notes:
        # - Remember to manually apply default argument promotions when calling variadic functions;
        #     anyway it is not necessary with ReadData since variadic arguments are always pointers,
        #     that are not subject to default argument promotion. More details on
        #     https://en.cppreference.com/w/c/language/conversion#Default_argument_promotions
        # - On some platforms, like Apple ARM64, "it is required to specify the argtypes attribute for
        #     the regular, non-variadic, function arguments" (see ctypes documentation); the other
        #     variadic arguments could be set at runtime after a call to SetReadDataFormat, but this
        #     would not be safe because ReadData can be called concurrently from multiple threads with
        #     different signatures, so arguments (always pointers in this case) must be placed without
        #     relying on ctypes automatic conversions with from_param methods. For more details, see
        #     https://stackoverflow.com/q/74630617/3287591
        self.read_data = self.__lib_variadic.CAEN_FELib_ReadData
        self.__set(self.read_data, [ct.c_uint64, ct.c_int])

    def __api_errcheck(self, res: int, func: Callable, _: Tuple) -> int:
        # res can be positive on GetChildHandles and GetDeviceTree
        if res < 0:
            raise error.Error(self.last_error, res, func.__name__)
        return res

    def __set(self, func: Any, argtypes: List[Type]) -> None:
        func.argtypes = argtypes
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck

    # C API wrappers

    def get_lib_info(self, initial_size: int = 2**22) -> Dict:
        """
        Wrapper to CAEN_FELib_GetLibInfo()

        @sa info
        @param[in] initial_size		inizial size to allocate for the first iteration
        @return						JSON representation of the library info (a dictionary)
        """
        while True:
            lib_info = ct.create_string_buffer(initial_size)
            res = self.__get_lib_info(lib_info, initial_size)
            if res < initial_size:  # equal not fine, see docs
                return loads(lib_info.value.decode())
            initial_size = res

    def get_lib_version(self) -> str:
        """
        Wrapper to CAEN_FELib_GetLibVersion()

        @sa version
        @return						version (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(16)
        self.__get_lib_version(value)
        return value.value.decode()

    def get_error_name(self, error_code: int) -> str:
        """
        Wrapper to CAEN_FELib_GetErrorName()

        @param[in] error_code		error code returned by library functions
        @return						error name (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(32)
        self.__get_error_name(error_code, value)
        return value.value.decode()

    def get_error_description(self, error_code: int) -> str:
        """
        Wrapper to CAEN_FELib_GetErrorDescription()

        @param[in] error_code		error code returned by library functions
        @return						error description (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(256)
        self.__get_error_description(error_code, value)
        return value.value.decode()

    def get_last_error(self) -> str:
        """
        Wrapper to CAEN_FELib_GetLastError()

        @sa last_error
        @return						last error description (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(1024)
        self.__get_last_error(value)
        return value.value.decode()

    # Python utilities

    @property
    def info(self) -> Dict:
        """Get library info"""
        return self.get_lib_info()

    @property
    def version(self) -> str:
        """Get library version"""
        return self.get_lib_version()

    @property
    def last_error(self) -> str:
        """Get last error"""
        return self.get_last_error()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.path})'

    def __str__(self) -> str:
        return self.path
