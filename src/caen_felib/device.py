"""
@ingroup Python
"""

__author__		= 'Giovanni Cerretani'
__copyright__	= 'Copyright (C) 2020-2022 CAEN SpA'
__license__		= 'LGPLv3+'

import ctypes as ct
from enum import Enum
import json

import numpy as np

from caen_felib import lib

class _Data:
	"""
	Class representing data set by Node.set_read_data_format().
	It holds a numpy ndarray allocated with size specified
	in the data format.
	"""

	def __init__(self, field):

		# Default attributes from fields passed to C library
		self.name = field['name']
		self.type = field['type']
		self.dim = field.get('dim', 0)

		# 'shape' is a Python extension to allow local allocation
		self.shape = field.get('shape', [])

		if (self.dim != len(self.shape)):
			raise RuntimeError('shape length must match dim')

		# Private attributes
		self.__underlying_type = self.__generate_underlying_type()
		self.__2d_proxy_value = None

		# Other public attributes
		self.argtype = self.__generate_argtype()
		self.value = self.__generate_value()
		self.arg = self.__generate_arg()

	def __generate_underlying_type(self):
		return {
			# 'PTRDIFF_T' unsupported on Python
			'U8'			: ct.c_uint8,
			'U16'			: ct.c_uint16,
			'U32'			: ct.c_uint32,
			'U64'			: ct.c_uint64,
			'I8'			: ct.c_int8,
			'I16'			: ct.c_int16,
			'I32'			: ct.c_int32,
			'I64'			: ct.c_int64,
			'CHAR'			: ct.c_char,
			'BOOL'			: ct.c_bool,
			'SIZE_T'		: ct.c_size_t,
			'FLOAT'			: ct.c_float,
			'DOUBLE'		: ct.c_double,
			'LONG DOUBLE'	: ct.c_longdouble,
		}[self.type]

	def __generate_argtype(self):
		if self.dim < 2:
			return ct.POINTER(self.__underlying_type)
		else:
			return ct.POINTER(ct.POINTER(self.__underlying_type))

	def __generate_value(self):
		return np.empty(self.shape, dtype=self.__underlying_type)

	def __generate_arg(self):
		if self.dim < 2:
			# NumPy 0D and 1D arrays can be used directly.
			return self.value.ctypes.data_as(self.argtype)
		else:
			# NumPy 2D arrays cannot be directly used because
			# they areimplemented as contiguous memory blocks
			# instead of arrays of pointers that are used by
			# CAEN_FELib. To overcome the problem we generate
			# a local array of pointers.
			ptr_gen = (v.ctypes.data for v in self.value)
			self.__2d_proxy_value = np.fromiter(ptr_gen, dtype=ct.c_void_p)
			return self.__2d_proxy_value.ctypes.data_as(self.argtype)


class NodeType(Enum):
	"""
	Wrapper to ::CAEN_FELib_NodeType_t
	"""
	UNKNOWN		= -1
	PARAMETER	= 0
	COMMAND		= 1
	FEATURE		= 2
	ATTRIBUTE	= 3
	ENDPOINT	= 4
	CHANNEL		= 5
	DIGITIZER	= 6
	FOLDER		= 7
	LVDS		= 8
	VGA			= 9
	HV_CHANNEL	= 10
	MONOUT		= 11
	VTRACE		= 12
	GROUP		= 13


def _convert_str(path):
	return None if path is None else path.encode()


class Node:
	"""
	Class representing a node. It holds an handle.

	Example:
	```python
	dig = device.Digitizer("dig2://<host>")
	for node in dig.child_nodes:
	    print(node.name)
	```
	"""

	def __init__(self, handle):
		# Public attributes
		self.handle = handle

		# Endpoint data (inizialized by set_read_data_format)
		self.data = None

	# C API wrappers

	def get_child_nodes(self, path, initial_size = 2 ** 6):
		"""
		Wrapper to CAEN_FELib_GetChildHandles()
		@param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
		@param[in] initial_size		inizial size to allocate for the first iteration
		@return						child nodes (a list)
		"""
		b_path = _convert_str(path)
		while True:
			child_handles = np.empty([initial_size], dtype=ct.c_uint64)
			child_handles_arg = child_handles.ctypes.data_as(ct.POINTER(ct.c_uint64))
			res = lib.GetChildHandles(self.handle, b_path, child_handles_arg, initial_size)
			if res <= initial_size:
				return [Node(handle) for handle in child_handles[:res]]
			initial_size = res

	def get_parent_node(self, path):
		"""
		Wrapper to CAEN_FELib_GetParentHandle()
		@param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
		@return						parent node
		"""
		value = ct.c_uint64()
		lib.GetParentHandle(self.handle, _convert_str(path), value)
		return Node(value)

	def get_node(self, path):
		"""
		Wrapper to CAEN_FELib_GetHandle()
		@param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
		@return						node at the provided path
		"""
		value = ct.c_uint64()
		lib.GetHandle(self.handle, _convert_str(path), value)
		return Node(value)

	def get_path(self):
		"""
		Wrapper to CAEN_FELib_GetPath()
		@return						absolute path of the provided handle (a string)
		"""
		value = ct.create_string_buffer(256)
		lib.GetPath(self.handle, value)
		return value.value.decode()

	def get_node_properties(self, path):
		"""
		Wrapper to CAEN_FELib_GetNodeProperties()
		@param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
		@return						tuple containing node name (a string) and the node type (a NodeType)
		"""
		name = ct.create_string_buffer(32)
		type = ct.c_int()
		lib.GetNodeProperties(self.handle, _convert_str(path), name, type)
		return name.value.decode(), NodeType(type.value)

	def get_device_tree(self, initial_size = 2 ** 22):
		"""
		Wrapper to CAEN_FELib_GetDeviceTree()
		@param[in] initial_size		inizial size to allocate for the first iteration
		@return						JSON representation of the node structure (a dictionary)
		"""
		while True:
			device_tree = ct.create_string_buffer(initial_size)
			res = lib.GetDeviceTree(self.handle, device_tree, initial_size)
			if res < initial_size: # equal not fine, see docs
				return json.loads(device_tree.value.decode())
			initial_size = res

	def get_value(self, path):
		"""
		Wrapper to CAEN_FELib_GetValue()
		@param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
		@return						value of the node (a string)
		"""
		value = ct.create_string_buffer(256)
		lib.GetValue(self.handle, _convert_str(path), value)
		return value.value.decode()

	def get_value_with_arg(self, path, arg):
		"""
		Wrapper to CAEN_FELib_GetValue()
		@param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
		@param[in] arg				optional argument (either a string or `None` that is interpreted as an empty string)
		@return						value of the node (a string)
		"""
		value = ct.create_string_buffer(_convert_str(arg), 256)
		lib.GetValue(self.handle, _convert_str(path), value)
		return value.value.decode()

	def set_value(self, path, value):
		"""
		Wrapper to CAEN_FELib_SetValue()
		@param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
		@param[in] value			value to set (a string)
		"""
		lib.SetValue(self.handle, _convert_str(path), _convert_str(value))

	def get_user_register(self, address):
		"""
		Wrapper to CAEN_FELib_GetUserRegister()
		@param[in] address			user register address
		@return						value of the register
		"""
		value = ct.c_uint32()
		lib.GetUserRegister(self.handle, address, value)
		return value.value

	def set_user_register(self, address, value):
		"""
		Wrapper to CAEN_FELib_SetUserRegister()
		@param[in] address			user register address
		@param[in] value			value of the register
		"""
		lib.SetUserRegister(self.handle, address, value)

	def send_command(self, path):
		"""
		Wrapper to CAEN_FELib_SendCommand()
		@param[in] path				relative path of a node (either a string or `None` that is interpreted as an empty string)
		"""
		lib.SendCommand(self.handle, _convert_str(path))

	def set_read_data_format(self, format):
		"""
		Wrapper to CAEN_FELib_SetReadDataFormat()

		In addition to what happens in C library, it also allocate data. Size of fields
		with `dim > 0` must be specified by a `"shape"` entry in the field description,
		that is a vector passed to the `shape` argument of `np.empty` constructor.
		On fields with `dim == 0` the shape can be omitted, and is set to `[]` by default.
		Fields can be accessed on data attribute of this class, that is a list of _Data
		inizialized with the field descriptions, in the same order of @p format.

		Example:
		```python
		data_format = [
			{
				'name': 'EVENT_SIZE',
				'type': 'SIZE_T',
			},
		]
		ep_node.set_read_data_format(format)
		print(ep_node.data[0])
		```

		@param[in] format			JSON representation of the format, in compliance with the endpoint "format" property (a list of dictionaries)
		"""
		lib.SetReadDataFormat(self.handle, json.dumps(format).encode())

		# Allocate requested fields
		self.data = [_Data(field) for field in format]

		# Important:
		# Do not update lib.ReadData.argtypes with data.argtype because lib.ReadData
		# is shared with all other endpoints and it would not be thread safe.
		# More details on a comment on the caen_felib.lib constructor.
		# Possible unsafe code could be:
		# lib.ReadData.argtypes = [ct.c_uint64, ct.c_int] + [d.argtype for d in self.data]

	def read_data(self, timeout):
		"""
		Wrapper to CAEN_FELib_ReadData()

		Unlike what happens in C library, variadic arguments are added automatically
		according to what has been specified by set_read_data_format(). Data can be
		retrieved using the data attribute of this class.

		Example:
		```python
		# Get reference to data
		data_0 = ep_node.data[0].value

		# Start acquisition
		dig.send_command('/cmd/armacquisition')
		dig.send_command('/cmd/swstartacquisition')

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

			# So stuff with data
			print(data_0)

		dig.send_command('/cmd/disarmacquisition')
		```

		@param[in] timeout			timeout of the function in milliseconds; if this value is -1 the function is blocking with infinite timeout
		"""
		lib.ReadData(self.handle, timeout, *[d.arg for d in self.data])

	def has_data(self, timeout):
		"""
		Wrapper to CAEN_FELib_HasData()
		@param[in] timeout			timeout of the function in milliseconds; if this value is -1 the function is blocking with infinite timeout
		"""
		lib.HasData(self.handle, timeout)

	# Python utilities

	@property
	def name(self):
		"""Get node name"""
		return self.get_node_properties(None)[0]

	@property
	def type(self):
		"""Get node type"""
		return self.get_node_properties(None)[1]

	@property
	def path(self):
		"""Get node path"""
		return self.get_path()

	@property
	def parent_node(self):
		"""Get parent node"""
		return self.get_parent_node(None)

	@property
	def child_nodes(self):
		"""Get list of child nodes"""
		return self.get_child_nodes(None)

	@property
	def value(self):
		"""Get current value"""
		return self.get_value(None)

	@value.setter
	def value(self, value):
		return self.set_value(None, value)

	def __getitem__(self, id):
		return self.get_node(f'/{id}')

	def __getattr__(self, name):
		return self.__getitem__(name)

	def __iter__(self):
		yield from self.child_nodes

	def __call__(self):
		"""Execute node"""
		self.send_command(None)


class Digitizer(Node):
	"""
	Class representing a digitizer. It holds the handle
	returned by CAEN_FELib_Open(). CAEN_FELib_Close()
	is called on delete.

	Child nodes do not hold a reference to the digitizer.

	Example:
	```python
	dig = device.Digitizer("dig2://<host>")
	```
	"""

	def __init__(self, url):
		super().__init__(self.__open(url))

	def __del__(self):
		"""Wrapper to CAEN_FELib_Close()"""
		lib.Close(self.handle)

	@staticmethod
	def __open(url):
		"""Wrapper to CAEN_FELib_Open()"""
		handle = ct.c_uint64()
		lib.Open(_convert_str(url), handle)
		return handle
