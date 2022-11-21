import ctypes

from pyfelib import _lib, _last_error

class Device:
	def __init__(self, url):
		self.handle = self.__connect(url)

	def __del__(self):
		res = _lib.CAEN_FELib_Close(self.handle)
		if res != 0:
			raise Exception(last_error())

	@staticmethod
	def __connect(url):
		handle = ctypes.c_uint64()
		res = _lib.CAEN_FELib_Open(url.encode('ascii'), ctypes.byref(handle))
		if res != 0:
			raise Exception(_last_error())
		return handle

	def get_value(self, path):
		value = ctypes.create_string_buffer(256)
		res = _lib.CAEN_FELib_GetValue(self.handle, path.encode('ascii'), value)
		if res != 0:
			raise Exception(_last_error())
		return value.value.decode('ascii')

	def set_value(self, path, value):
		res = _lib.CAEN_FELib_SetValue(self.handle, path.encode('ascii'), value.encode('ascii'))
		if res != 0:
			raise Exception(_last_error())

	def send_command(self, path):
		res = _lib.CAEN_FELib_SendCommand(self.handle, path.encode('ascii'))
		if res != 0:
			raise Exception(_last_error())
