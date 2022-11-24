import ctypes as ct
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
			loader = ct.windll
			loader_variadic = ct.cdll

		elif platform.startswith('linux'):
			lib_name = 'libCAEN_FELib.so'
			loader = ct.cdll
			loader_variadic = loader

		elif platform.startswith('darwin'):
			lib_name = 'libCAEN_FELib.dylib'
			loader = ct.cdll
			loader_variadic = loader

		# Load libraries
		lib = loader.LoadLibrary(lib_name)
		lib_variadic = loader_variadic.LoadLibrary(lib_name)

		# Load API not related to devices
		self.__GetLibInfo = lib.CAEN_FELib_GetLibInfo
		self.__set_prototype(self.__GetLibInfo, [ct.c_char_p, ct.c_size_t])

		self.__GetLibVersion = lib.CAEN_FELib_GetLibVersion
		self.__set_prototype(self.__GetLibVersion, [ct.c_char_p])

		self.__GetErrorName = lib.CAEN_FELib_GetErrorName
		self.__set_prototype(self.__GetErrorName, [ct.c_int, ct.c_char_p])

		self.__GetErrorDescription = lib.CAEN_FELib_GetErrorDescription
		self.__set_prototype(self.__GetErrorDescription, [ct.c_int, ct.c_char_p])

		self.__GetLastError = lib.CAEN_FELib_GetLastError
		self.__set_prototype(self.__GetLastError, [ct.c_char_p])

		self.__DevicesDiscovery = lib.CAEN_FELib_DevicesDiscovery
		self.__set_prototype(self.__DevicesDiscovery, [ct.c_char_p, ct.c_size_t, ct.c_int])

		# Load API
		self.Open = lib.CAEN_FELib_Open
		self.__set_prototype(self.Open, [ct.c_char_p, ct.POINTER(ct.c_uint64)])

		self.Close = lib.CAEN_FELib_Close
		self.__set_prototype(self.Close, [ct.c_uint64])

		self.GetDeviceTree = lib.CAEN_FELib_GetDeviceTree
		self.__set_prototype(self.GetDeviceTree, [ct.c_uint64, ct.c_char_p, ct.c_size_t])

		self.GetChildHandles = lib.CAEN_FELib_GetChildHandles
		self.__set_prototype(self.GetChildHandles, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64), ct.c_size_t])

		self.GetParentHandle = lib.CAEN_FELib_GetParentHandle
		self.__set_prototype(self.GetParentHandle, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64)])

		self.GetHandle = lib.CAEN_FELib_GetHandle
		self.__set_prototype(self.GetHandle, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64)])

		self.GetPath = lib.CAEN_FELib_GetPath
		self.__set_prototype(self.GetPath, [ct.c_uint64, ct.c_char_p])

		self.GetNodeProperties = lib.CAEN_FELib_GetNodeProperties
		self.__set_prototype(self.GetNodeProperties, [ct.c_uint64, ct.c_char_p, ct.c_char_p, ct.POINTER(ct.c_int)])

		self.GetValue = lib.CAEN_FELib_GetValue
		self.__set_prototype(self.GetValue, [ct.c_uint64, ct.c_char_p, ct.c_char_p])

		self.SetValue = lib.CAEN_FELib_SetValue
		self.__set_prototype(self.SetValue, [ct.c_uint64, ct.c_char_p, ct.c_char_p])

		self.GetUserRegister = lib.CAEN_FELib_GetUserRegister
		self.__set_prototype(self.GetUserRegister, [ct.c_uint64, ct.c_uint32, ct.POINTER(ct.c_uint32)])

		self.SetUserRegister = lib.CAEN_FELib_SetUserRegister
		self.__set_prototype(self.SetUserRegister, [ct.c_uint64, ct.c_uint32, ct.c_uint32])

		self.SendCommand = lib.CAEN_FELib_SendCommand
		self.__set_prototype(self.SendCommand, [ct.c_uint64, ct.c_char_p])

		self.SetReadDataFormat = lib.CAEN_FELib_SetReadDataFormat
		self.__set_prototype(self.SetReadDataFormat, [ct.c_uint64, ct.c_char_p])

		self.HasData = lib.CAEN_FELib_HasData
		self.__set_prototype(self.HasData, [ct.c_uint64, ct.c_int])

		# Load variadic API
		# Notes:
		# - remember to manually apply default argument promotions when calling variadic functions!
		# - argtypes is not set; anyway, according to ct documentation, there could be problems
		#   on ARM64 for Apple Platforms.
		self.ReadData = lib_variadic.CAEN_FELib_ReadData
		self.__set_prototype(self.ReadData, None)

		# Initialize local variables
		self.version = self.get_lib_version()

	def __errcheck(self, res, func, args):
		if res < 0:
			raise FELibError(self.get_last_error(), res)
		return res

	def __set_prototype(self, func, argtypes):
		func.argtypes = argtypes
		func.restype = ct.c_int
		func.errcheck = self.__errcheck

	def get_lib_version(self):
		value = ct.create_string_buffer(16)
		self.__GetLibVersion(value)
		return value.value.decode()

	def get_error_name(self, error):
		value = ct.create_string_buffer(32)
		_lib.__GetErrorName(error, value)
		return value.value.decode()

	def get_error_description(self, error):
		value = ct.create_string_buffer(256)
		_lib.__GetErrorDescription(error, value)
		return value.value.decode()

	def get_last_error(self):
		value = ct.create_string_buffer(1024)
		self.__GetLastError(value)
		return value.value.decode()

# Initialize library
lib = Lib()
