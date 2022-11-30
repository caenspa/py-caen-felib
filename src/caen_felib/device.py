__author__		= 'Giovanni Cerretani'
__copyright__	= 'Copyright (C) 2020-2022 CAEN SpA'
__license__		= 'LGPLv3+'

import ctypes as ct
import json

import numpy as np

from caen_felib import lib

class data:

	def __init__(self, field):

		# Default fields passed to C library
		self.name = field['name']
		self.type = field['type']
		self.dim = field.get('dim', 0)

		# 'shape' is a Python extension to allow local allocation
		self.shape = field.get('shape', [])

		if (self.dim != len(self.shape)):
			raise RuntimeError('shape length must match dim')

		# Private fields
		self.__underlying_type = self.__generate_underlying_type()
		self.__2d_proxy_value = None

		# Public fields
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


class node:

	def __init__(self, handle):
		self._h = handle
		# endpoint data
		self.data = None

	@staticmethod
	def _convert_path(path):
		return None if path is None else path.encode()

	###################
	# C API wrappers
	###################

	def get_child_nodes(self, path, initial_size = 2 ** 6):
		'''Wrapper to CAEN_FELib_GetChildHandles'''
		b_path = self._convert_path(path)
		while True:
			child_handles = np.empty([initial_size], dtype=ct.c_uint64)
			child_handles_arg = child_handles.ctypes.data_as(ct.POINTER(ct.c_uint64))
			res = lib.GetChildHandles(self._h, b_path, child_handles_arg, initial_size)
			if res <= initial_size:
				return [node(h) for h in child_handles[:res]]
			initial_size = res

	def get_parent_node(self, path):
		'''Wrapper to CAEN_FELib_GetParendHandle'''
		value = ct.c_uint64()
		lib.GetParentHandle(self._h, self._convert_path(path), value)
		return node(value)

	def get_node(self, path):
		'''Wrapper to CAEN_FELib_GetHandle'''
		value = ct.c_uint64()
		lib.GetHandle(self._h, self._convert_path(path), value)
		return node(value)

	def get_path(self):
		'''Wrapper to CAEN_FELib_GetPath'''
		value = ct.create_string_buffer(256)
		lib.GetPath(self._h, value)
		return value.value.decode()

	def get_node_properties(self, path):
		'''Wrapper to CAEN_FELib_GetNodeProperties'''
		name = ct.create_string_buffer(32)
		type = ct.c_int()
		lib.GetNodeProperties(self._h, self._convert_path(path), name, type)
		return name.value.decode(), type.value

	def get_device_tree(self, initial_size = 2 ** 22):
		'''Wrapper to CAEN_FELib_GetDeviceTree'''
		while True:
			device_tree = ct.create_string_buffer(initial_size)
			res = lib.GetDeviceTree(self._h, device_tree, initial_size)
			if res < initial_size: # equal not fine, see docs
				return json.loads(device_tree.value.decode())
			initial_size = res

	def get_value(self, path):
		'''Wrapper to CAEN_FELib_GetValue'''
		value = ct.create_string_buffer(256)
		lib.GetValue(self._h, self._convert_path(path), value)
		return value.value.decode()

	def get_value_with_arg(self, path, arg):
		'''Wrapper to CAEN_FELib_GetValue'''
		value = ct.create_string_buffer(self._convert_path(arg), 256)
		lib.GetValue(self._h, self._convert_path(path), value)
		return value.value.decode()

	def set_value(self, path, value):
		'''Wrapper to CAEN_FELib_setValue'''
		lib.SetValue(self._h, self._convert_path(path), self._convert_path(value))

	def get_user_register(self, addr):
		'''Wrapper to CAEN_FELib_GetUserRegister'''
		value = ct.c_uint32()
		lib.GetUserRegister(self._h, addr, value)
		return value.value

	def set_user_register(self, addr, value):
		'''Wrapper to CAEN_FELib_SetUserRegister'''
		lib.SetUserRegister(self._h, addr, value)

	def send_command(self, path):
		'''Wrapper to CAEN_FELib_SendCommand'''
		lib.SendCommand(self._h, self._convert_path(path))

	def set_read_data_format(self, format):
		'''Wrapper to CAEN_FELib_SetReadDataFormat'''
		lib.SetReadDataFormat(self._h, json.dumps(format).encode())

		# Allocate requested fields
		self.data = [data(f) for f in format]

		# Set lib.ReadData.argtypes (mandatory on Apple ARM64)
		lib.ReadData.argtypes = [ct.c_uint64, ct.c_int] + [d.argtype for d in self.data]

	def read_data(self, timeout):
		'''Wrapper to CAEN_FELib_ReadData'''
		lib.ReadData(self._h, timeout, *[d.arg for d in self.data])

	def has_data(self, timeout):
		'''Wrapper to CAEN_FELib_HasData'''
		lib.HasData(self._h, timeout)

	###################
	# Python utilities
	###################

	def __getattr__(self, name):
		return self.get_node(f'/{name}')

	def __getitem__(self, id):
		return self.get_node(f'/{id}')

	def __iter__(self):
		for n in self.get_child_nodes(None):
			yield n

	@property
	def name(self):
		return self.get_node_properties(None)[0]

	@property
	def value(self):
		return self.get_value(None)

	@value.setter
	def value(self, value):
		return self.set_value(None, value)

	def __call__(self):
		self.send_command(None)


class device(node):

	def __init__(self, url):
		super().__init__(self.__open(url))

	def __del__(self):
		'''Wrapper to CAEN_FELib_Close'''
		lib.Close(self._h)

	@staticmethod
	def __open(url):
		'''Wrapper to CAEN_FELib_Open'''
		handle = ct.c_uint64()
		lib.Open(device._convert_path(url), handle)
		return handle
