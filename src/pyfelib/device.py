import ctypes

from pyfelib import _lib
from pyfelib.error import FELibError

class Endpoint:

	def __init__(self, handle):
		self.__h = handle

	def set_read_data_format(self, json_string):
		res = _lib.SetReadDataFormat(self.__h, json_string.encode('ascii'))
		if res != 0:
			raise FELibError(_lib.get_last_error(), res)

	@staticmethod
	def __decode_read_data_error(res):
		if res == -11:
			raise FELibError('timeout', res)
		elif res == -12:
			raise FELibError('stop', res)
		else:
			raise FELibError(_lib.get_last_error(), res)

	def read_data(self, timeout, *args):
		res = _lib.ReadData(self.__h, ctypes.c_int(timeout), *args)
		if res != 0:
			self.__decode_error()

	def has_data(self, timeout):
		res = _lib.HasData(self.__h, ctypes.c_int(timeout))
		if res != 0:
			self.__decode_error()


class Device:

	def __init__(self, url):
		self.__h = self.__connect(url)
		self.endpoints = dict(self.__endpoints())

	def __del__(self):
		res = _lib.Close(self.__h)
		if res != 0:
			raise FELibError(_lib.get_last_error(), res)

	@staticmethod
	def __connect(url):
		handle = ctypes.c_uint64()
		res = _lib.Open(url.encode('ascii'), ctypes.byref(handle))
		if res not in [0, 14]:
			raise FELibError(_lib.get_last_error(), res)
		return handle

	def __endpoints(self):
		for h in self.__get_child_handles('/endpoint'):
			name = ctypes.create_string_buffer(32)
			type = ctypes.c_int()
			res = _lib.GetNodeProperties(h, None, name, ctypes.byref(type))
			if res != 0:
				raise FELibError(_lib.get_last_error(), res)
			if type.value == 4:
				yield name.value.decode('ascii'), Endpoint(h)

	def __get_child_handles(self, path):
		res = _lib.GetChildHandles(self.__h, path.encode('ascii'), None, ctypes.c_size_t(0))
		if res < 0:
			raise FELibError(_lib.get_last_error(), res)
		child_handles_size = res
		child_handles = (ctypes.c_uint64 * child_handles_size)()
		res = _lib.GetChildHandles(self.__h, path.encode('ascii'), child_handles, ctypes.c_size_t(child_handles_size))
		if res < 0:
			raise FELibError(_lib.get_last_error(), res)
		elif res != child_handles_size:
			raise FELibError('unexpected size', res)
		return [ctypes.c_uint64(h) for h in child_handles]

	def get_value(self, path):
		value = ctypes.create_string_buffer(256)
		res = _lib.GetValue(self.__h, path.encode('ascii'), value)
		if res != 0:
			raise FELibError(_lib.get_last_error(), res)
		return value.value.decode('ascii')

	def set_value(self, path, value):
		res = _lib.SetValue(self.__h, path.encode('ascii'), value.encode('ascii'))
		if res != 0:
			raise FELibError(_lib.get_last_error(), res)

	def get_user_register(self, addr):
		value = ctypes.c_uint32()
		res = _lib.GetUserRegister(self.__h, ctypes.c_uint32(addr), ctypes.byref(value))
		if res != 0:
			raise FELibError(_lib.get_last_error(), res)
		return value.value

	def set_user_register(self, addr, value):
		res = _lib.SetUserRegister(self.__h, ctypes.c_uint32(addr), ctypes.c_uint32(value))
		if res != 0:
			raise FELibError(_lib.get_last_error(), res)

	def send_command(self, path):
		res = _lib.SendCommand(self.__h, path.encode('ascii'))
		if res != 0:
			raise FELibError(_lib.get_last_error(), res)
