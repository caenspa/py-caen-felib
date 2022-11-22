import ctypes
import numpy as np

from pyfelib import _lib

class Endpoint:

	def __init__(self, handle):
		self.__h = handle

	def set_data_format(self, json_string):
		res = _lib._set_data_format(self.__h, json_string.encode('ascii'))
		if res != 0:
			raise Exception(_lib.get_last_error())

	def read_data(self, timeout, *args):
		res = _lib._read_data(self.__h, ctypes.c_int(timeout), *args)
		if res == 0:
			return
		elif res == -11:
			raise Exception('timeout')
		elif res == -12:
			raise Exception('stop')
		else:
			raise Exception(_lib.get_last_error())

class Device:

	def __init__(self, url):
		self.__h = self.__connect(url)
		self.endpoints = self.__load_endpoints()

	def __del__(self):
		res = _lib._close(self.__h)
		if res != 0:
			raise Exception(_lib.get_last_erro())

	@staticmethod
	def __connect(url):
		handle = ctypes.c_uint64()
		res = _lib._open(url.encode('ascii'), ctypes.byref(handle))
		if res != 0:
			raise Exception(_lib.get_last_error())
		return handle

	def __load_endpoints(self):
		endpoints = {}
		path = b'/endpoint'
		res = _lib._get_child_handles(self.__h, path, None, ctypes.c_size_t(0))
		if res < 0:
			raise Exception(_lib.get_last_error())
		child_handles_size = res
		child_handles = (ctypes.c_uint64 * child_handles_size)()
		res = _lib._get_child_handles(self.__h, path, child_handles, ctypes.c_size_t(res))
		if res < 0:
			raise Exception(_lib.get_last_error())
		elif res != child_handles_size:
			raise Exception('unexpected size')
		for handle in child_handles:
			h = ctypes.c_uint64(handle);
			name = ctypes.create_string_buffer(32)
			type = ctypes.c_int()
			res = _lib._get_node_properties(h, None, name, ctypes.byref(type))
			if res != 0:
				raise Exception(_lib.get_last_error())
			if type.value == 4:
				endpoints[name.value.decode('ascii')] = Endpoint(h)
		return endpoints

	def get_handle(self, path):
		value = ctypes.c_uint64()
		res = _lib._get_handle(self.__h, path.encode('ascii'), ctypes.byref(value))
		if res != 0:
			raise Exception(_lib.get_last_error())
		return value

	def get_value(self, path):
		value = ctypes.create_string_buffer(256)
		res = _lib._get_value(self.__h, path.encode('ascii'), value)
		if res != 0:
			raise Exception(_lib.get_last_error())
		return value.value.decode('ascii')

	def set_value(self, path, value):
		res = _lib._set_value(self.__h, path.encode('ascii'), value.encode('ascii'))
		if res != 0:
			raise Exception(_lib.get_last_error())

	def get_user_register(self, addr):
		value = ctypes.c_uint32()
		res = _lib._get_user_register(self.__h, ctypes.c_uint32(addr), ctypes.byref(value))
		if res != 0:
			raise Exception(_lib.get_last_error())
		return value.value

	def set_user_register(self, addr, value):
		res = _lib._set_user_register(self.__h, ctypes.c_uint32(addr), ctypes.c_uint32(value))
		if res != 0:
			raise Exception(_lib.get_last_error())

	def send_command(self, path):
		res = _lib._send_command(self.__h, path.encode('ascii'))
		if res != 0:
			raise Exception(_lib.get_last_error())
