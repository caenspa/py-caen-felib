__author__		= 'Giovanni Cerretani'
__copyright__	= 'Copyright (C) 2020-2022 CAEN SpA'
__license__		= 'LGPLv3+'

import ctypes as ct
import json

import numpy as np

from caen_felib import lib

class Data:

	def __init__(self, field):

		# Default fields passed to C library
		self.name = field['name']
		self.type = field['type']
		self.dim = field.get('dim', 0)

		# 'shape' is a Python extension to allow local allocation
		self.shape = field.get('shape', [])

		if (self.dim != len(self.shape)):
			raise RuntimeError('unexpected shape length')

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


class Endpoint:

	def __init__(self, handle):
		self.__h = handle
		self.data = []

	def set_read_data_format(self, format):
		'''Wrapper to CAEN_FELib_SetReadDataFormat'''
		lib.SetReadDataFormat(self.__h, json.dumps(format).encode())

		# Allocate requested fields
		self.data = [Data(f) for f in format]

		# Set lib.ReadData.argtypes (mandatory on Apple ARM64)
		lib.ReadData.argtypes = [ct.c_uint64, ct.c_int] + [d.argtype for d in self.data]

	def read_data(self, timeout):
		'''Wrapper to CAEN_FELib_ReadData'''
		lib.ReadData(self.__h, timeout, *[d.arg for d in self.data])

	def has_data(self, timeout):
		'''Wrapper to CAEN_FELib_HasData'''
		lib.HasData(self.__h, timeout)


class Device:

	def __init__(self, url):
		self.__h = self.__connect(url)
		self.endpoints = dict(self.__endpoints())

	def __del__(self):
		lib.Close(self.__h)

	@staticmethod
	def __connect(url):
		handle = ct.c_uint64()
		lib.Open(url.encode(), handle)
		return handle

	def __endpoints(self):
		for h in self.__get_child_handles(self.__h, '/endpoint'):
			name, type = self.__get_node_properties(h, None)
			if type == 4:
				yield name, Endpoint(h)

	@staticmethod
	def __get_child_handles(handle, path, initial_size = 2 ** 6):
		b_path = None if path is None else path.encode()
		while True:
			child_handles = (ct.c_uint64 * initial_size)()
			res = lib.GetChildHandles(handle, b_path, child_handles, initial_size)
			if res <= initial_size:
				return [ct.c_uint64(h) for h in child_handles[:res]]
			initial_size = res

	@staticmethod
	def __get_node_properties(handle, path):
		b_path = None if path is None else path.encode()
		name = ct.create_string_buffer(32)
		type = ct.c_int()
		lib.GetNodeProperties(handle, b_path, name, type)
		return name.value.decode(), type.value

	def get_device_tree(self, initial_size = 2 ** 22):
		'''Wrapper to CAEN_FELib_GetDeviceTree'''
		while True:
			device_tree = ct.create_string_buffer(initial_size)
			res = lib.GetDeviceTree(self.__h, device_tree, initial_size)
			if res < initial_size: # equal not fine, see docs
				return json.loads(device_tree.value.decode())
			initial_size = res

	def get_value(self, path):
		'''Wrapper to CAEN_FELib_GetValue'''
		value = ct.create_string_buffer(256)
		lib.GetValue(self.__h, path.encode(), value)
		return value.value.decode()

	def get_value_with_arg(self, path, arg):
		'''Wrapper to CAEN_FELib_GetValue'''
		value = ct.create_string_buffer(arg.encode(), 256)
		lib.GetValue(self.__h, path.encode(), value)
		return value.value.decode()

	def set_value(self, path, value):
		'''Wrapper to CAEN_FELib_setValue'''
		lib.SetValue(self.__h, path.encode(), value.encode())

	def get_user_register(self, addr):
		'''Wrapper to CAEN_FELib_GetUserRegister'''
		value = ct.c_uint32()
		lib.GetUserRegister(self.__h, addr, value)
		return value.value

	def set_user_register(self, addr, value):
		'''Wrapper to CAEN_FELib_SetUserRegister'''
		lib.SetUserRegister(self.__h, addr, value)

	def send_command(self, path):
		'''Wrapper to CAEN_FELib_SendCommand'''
		lib.SendCommand(self.__h, path.encode())
