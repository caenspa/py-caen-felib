import ctypes
from sys import platform

from pyfelib.error import FELibError

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

		# Load API of function not related to devices
		self.__GetLibInfo = lib.CAEN_FELib_GetLibInfo
		self.__GetLibVersion = lib.CAEN_FELib_GetLibVersion
		self.__GetErrorName = lib.CAEN_FELib_GetErrorName
		self.__GetErrorDescription = lib.CAEN_FELib_GetErrorDescription
		self.__GetLastError = lib.CAEN_FELib_GetLastError
		self.__DevicesDiscovery = lib.CAEN_FELib_DevicesDiscovery

		# Load API
		self.Open = lib.CAEN_FELib_Open
		self.Close = lib.CAEN_FELib_Close
		self.GetDeviceTree = lib.CAEN_FELib_GetDeviceTree
		self.GetChildHandles = lib.CAEN_FELib_GetChildHandles
		self.GetParentHandle = lib.CAEN_FELib_GetParentHandle
		self.GetHandle = lib.CAEN_FELib_GetHandle
		self.GetPath = lib.CAEN_FELib_GetPath
		self.GetNodeProperties = lib.CAEN_FELib_GetNodeProperties
		self.GetValue = lib.CAEN_FELib_GetValue
		self.SetValue = lib.CAEN_FELib_SetValue
		self.GetUserRegister = lib.CAEN_FELib_GetUserRegister
		self.SetUserRegister = lib.CAEN_FELib_SetUserRegister
		self.SendCommand = lib.CAEN_FELib_SendCommand
		self.SetReadDataFormat = lib.CAEN_FELib_SetReadDataFormat
		self.HasData = lib.CAEN_FELib_HasData

		# Load variadic API
		# Remember to manually apply default argument promotions
		# when calling variadic functions!
		self.ReadData = lib_variadic.CAEN_FELib_ReadData

	def get_lib_version(self):
		value = ctypes.create_string_buffer(16)
		ret = self.__GetLibVersion(value)
		if ret != 0:
			raise FELibError(self.get_last_error(), res)
		return value.value.decode()

	def get_last_error(self):
		value = ctypes.create_string_buffer(1024)
		ret = self.__GetLastError(value)
		if ret != 0:
			raise FELibError('get_last_error failed', res)
		return value.value.decode('ascii')

_lib = Lib()
