import ctypes

from pyfelib import lib
from pyfelib.error import FELibError

class Endpoint:

	def __init__(self, handle):
		self.__h = handle

	def set_read_data_format(self, json_string):
		res = lib.SetReadDataFormat(self.__h, json_string.encode('ascii'))
		if res != 0:
			raise FELibError(lib.get_last_error(), res)

	@staticmethod
	def __decode_read_data_error(res):
		if res == -11:
			raise FELibError('timeout', res)
		elif res == -12:
			raise FELibError('stop', res)
		else:
			raise FELibError(lib.get_last_error(), res)

	def read_data(self, timeout, *args):
		res = lib.ReadData(self.__h, ctypes.c_int(timeout), *args)
		if res != 0:
			self.__decode_error()

	def has_data(self, timeout):
		res = lib.HasData(self.__h, ctypes.c_int(timeout))
		if res != 0:
			self.__decode_error()


class Device:

	def __init__(self, url):
		self.__h = self.__connect(url)
		self.endpoints = dict(self.__endpoints())

	def __del__(self):
		res = lib.Close(self.__h)
		if res != 0:
			raise FELibError(lib.get_last_error(), res)

	@staticmethod
	def __connect(url):
		handle = ctypes.c_uint64()
		res = lib.Open(url.encode('ascii'), handle)
		if res not in [0, 14]:
			raise FELibError(lib.get_last_error(), res)
		return handle

	def __endpoints(self):
		for h in self.__get_child_handles('/endpoint'):
			name = ctypes.create_string_buffer(32)
			type = ctypes.c_int()
			res = lib.GetNodeProperties(h, None, name, type)
			if res != 0:
				raise FELibError(lib.get_last_error(), res)
			if type.value == 4:
				yield name.value.decode('ascii'), Endpoint(h)

	def __get_child_handles(self, path):
		b_path = path.encode('ascii')
		res = lib.GetChildHandles(self.__h, b_path, None, 0)
		if res < 0:
			raise FELibError(lib.get_last_error(), res)
		n_child_handles = res
		child_handles = (ctypes.c_uint64 * n_child_handles)()
		res = lib.GetChildHandles(self.__h, b_path, child_handles, n_child_handles)
		if res < 0:
			raise FELibError(lib.get_last_error(), res)
		elif res != n_child_handles:
			raise RuntimeError('unexpected size')
		return [ctypes.c_uint64(h) for h in child_handles]

	def get_value(self, path):
		value = ctypes.create_string_buffer(256)
		res = lib.GetValue(self.__h, path.encode('ascii'), value)
		if res != 0:
			raise FELibError(lib.get_last_error(), res)
		return value.value.decode('ascii')

	def set_value(self, path, value):
		res = lib.SetValue(self.__h, path.encode('ascii'), value.encode('ascii'))
		if res != 0:
			raise FELibError(lib.get_last_error(), res)

	def get_user_register(self, addr):
		value = ctypes.c_uint32()
		res = lib.GetUserRegister(self.__h, addr, value)
		if res != 0:
			raise FELibError(lib.get_last_error(), res)
		return value.value

	def set_user_register(self, addr, value):
		res = lib.SetUserRegister(self.__h, addr, value)
		if res != 0:
			raise FELibError(lib.get_last_error(), res)

	def send_command(self, path):
		res = lib.SendCommand(self.__h, path.encode('ascii'))
		if res != 0:
			raise FELibError(lib.get_last_error(), res)
