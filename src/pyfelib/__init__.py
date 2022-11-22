import ctypes
from sys import platform

class Lib:

	def __init__(self):

		# Platform dependent stuff
		if platform.startswith('win32'):
			# API Functions are declared as __stdcall, but variadic
			# functions are __cdecl even if declared as __stdcall.
			# This difference applies only to 32 bit applications,
			# 64 bit applications have its own calling convention.
			lib_name = 'CAEN_FELib.dll'
			loader = ctypes.windll
			loader_variadic = ctypes.cdll

		elif platform.startswith('linux'):
			lib_name = 'libCAEN_FELib.so'
			loader = ctypes.cdll
			loader_variadic = loader

		elif platform.startswith('darwin'):
			lib_name = 'libCAEN_FELib.dylib'
			loader = ctypes.cdll
			loader_variadic = loader

		lib = loader.LoadLibrary(lib_name)
		lib_variadic = loader_variadic.LoadLibrary(lib_name)

		# Load API
		self._get_last_error = lib.CAEN_FELib_GetLastError
		self._get_lib_version = lib.CAEN_FELib_GetLibVersion
		self._open = lib.CAEN_FELib_Open
		self._close = lib.CAEN_FELib_Close
		self._get_handle = lib.CAEN_FELib_GetHandle
		self._get_child_handles = lib.CAEN_FELib_GetChildHandles
		self._get_node_properties = lib.CAEN_FELib_GetNodeProperties
		self._get_value = lib.CAEN_FELib_GetValue
		self._set_value = lib.CAEN_FELib_SetValue
		self._get_user_register = lib.CAEN_FELib_GetUserRegister
		self._set_user_register = lib.CAEN_FELib_SetUserRegister
		self._send_command = lib.CAEN_FELib_SendCommand
		self._set_data_format = lib.CAEN_FELib_SetReadDataFormat

		# Load variadic API
		# Remember to manually apply default argument promotions
		# when calling variadic functions!
		self._read_data = lib_variadic.CAEN_FELib_ReadData

	def get_last_error(self):
		value = ctypes.create_string_buffer(1024)
		ret = self._get_last_error(value)
		if ret != 0:
			raise Exception('print_last_error failed')
		return value.value.decode()

	def get_lib_version(self):
		value = ctypes.create_string_buffer(16)
		ret = self.get_lib_version(value)
		if ret != 0:
			raise Exception('print_last_error failed')
		return value.value.decode()

_lib = Lib()
