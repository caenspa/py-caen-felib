import ctypes as ct
from ctypes.util import find_library
from sys import platform

from pyfeself.__lib.error import FELibError

class Lib:

	def __init__(self):

		# Platform dependent stuff
		if platform.startswith('win32'):
			# API functions are declared as __stdcall, but variadic
			# functions are __cdecl even if declared as __stdcall.
			# This difference applies only to 32 bit applications,
			# 64 bit applications have its own calling convention.
			loader = ct.windll
			loader_variadic = ct.cdll
		else:
			loader = ct.cdll
			loader_variadic = ct.cdll

		# Locate library path
		lib_path = find_library('CAEN_FELib')

		# Load library
		self.__lib = loader.LoadLibrary(lib_path)
		self.__lib_variadic = loader_variadic.LoadLibrary(lib_path)

		# Load API not related to devices
		self.__GetLibInfo = self.__lib.CAEN_FELib_GetLibInfo
		self.__set_type(self.__GetLibInfo, [ct.c_char_p, ct.c_size_t])

		self.__GetLibVersion = self.__lib.CAEN_FELib_GetLibVersion
		self.__set_type(self.__GetLibVersion, [ct.c_char_p])

		self.__GetErrorName = self.__lib.CAEN_FELib_GetErrorName
		self.__set_type(self.__GetErrorName, [ct.c_int, ct.c_char_p])

		self.__GetErrorDescription = self.__lib.CAEN_FELib_GetErrorDescription
		self.__set_type(self.__GetErrorDescription, [ct.c_int, ct.c_char_p])

		self.__GetLastError = self.__lib.CAEN_FELib_GetLastError
		self.__set_type(self.__GetLastError, [ct.c_char_p])

		self.__DevicesDiscovery = self.__lib.CAEN_FELib_DevicesDiscovery
		self.__set_type(self.__DevicesDiscovery, [ct.c_char_p, ct.c_size_t, ct.c_int])

		# Load API
		self.Open = self.__lib.CAEN_FELib_Open
		self.__set_type(self.Open, [ct.c_char_p, ct.POINTER(ct.c_uint64)])

		self.Close = self.__lib.CAEN_FELib_Close
		self.__set_type(self.Close, [ct.c_uint64])

		self.GetDeviceTree = self.__lib.CAEN_FELib_GetDeviceTree
		self.__set_type(self.GetDeviceTree, [ct.c_uint64, ct.c_char_p, ct.c_size_t])

		self.GetChildHandles = self.__lib.CAEN_FELib_GetChildHandles
		self.__set_type(self.GetChildHandles, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64), ct.c_size_t])

		self.GetParentHandle = self.__lib.CAEN_FELib_GetParentHandle
		self.__set_type(self.GetParentHandle, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64)])

		self.GetHandle = self.__lib.CAEN_FELib_GetHandle
		self.__set_type(self.GetHandle, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64)])

		self.GetPath = self.__lib.CAEN_FELib_GetPath
		self.__set_type(self.GetPath, [ct.c_uint64, ct.c_char_p])

		self.GetNodeProperties = self.__lib.CAEN_FELib_GetNodeProperties
		self.__set_type(self.GetNodeProperties, [ct.c_uint64, ct.c_char_p, ct.c_char_p, ct.POINTER(ct.c_int)])

		self.GetValue = self.__lib.CAEN_FELib_GetValue
		self.__set_type(self.GetValue, [ct.c_uint64, ct.c_char_p, ct.c_char_p])

		self.SetValue = self.__lib.CAEN_FELib_SetValue
		self.__set_type(self.SetValue, [ct.c_uint64, ct.c_char_p, ct.c_char_p])

		self.GetUserRegister = self.__lib.CAEN_FELib_GetUserRegister
		self.__set_type(self.GetUserRegister, [ct.c_uint64, ct.c_uint32, ct.POINTER(ct.c_uint32)])

		self.SetUserRegister = self.__lib.CAEN_FELib_SetUserRegister
		self.__set_type(self.SetUserRegister, [ct.c_uint64, ct.c_uint32, ct.c_uint32])

		self.SendCommand = self.__lib.CAEN_FELib_SendCommand
		self.__set_type(self.SendCommand, [ct.c_uint64, ct.c_char_p])

		self.SetReadDataFormat = self.__lib.CAEN_FELib_SetReadDataFormat
		self.__set_type(self.SetReadDataFormat, [ct.c_uint64, ct.c_char_p])

		self.HasData = self.__lib.CAEN_FELib_HasData
		self.__set_type(self.HasData, [ct.c_uint64, ct.c_int])

		# Load variadic API
		# Notes:
		# - remember to manually apply default argument promotions when calling variadic functions!
		# - argtypes is not set; anyway, according to ct documentation, there could be problems
		#   on ARM64 for Apple Platforms.
		self.ReadData = self.__lib_variadic.CAEN_FELib_ReadData
		self.__set_type(self.ReadData, None)

		# Initialize local variables
		self.version = self.get_lib_version()

	def __api_errcheck(self, res, func, args):
		if res < 0:
			raise FELibError(self.get_last_error(), res)
		return res

	def __set_type(self, func, argtypes):
		func.argtypes = argtypes
		func.restype = ct.c_int
		func.errcheck = self.__api_errcheck

	def get_lib_version(self):
		'''Wrapper to CAEN_FELib_GetLibVersion'''
		value = ct.create_string_buffer(16)
		self.__GetLibVersion(value)
		return value.value.decode()

	def get_error_name(self, error):
		'''Wrapper to CAEN_FELib_GetErrorName'''
		value = ct.create_string_buffer(32)
		_self.__GetErrorName(error, value)
		return value.value.decode()

	def get_error_description(self, error):
		'''Wrapper to CAEN_FELib_GetErrorDescription'''
		value = ct.create_string_buffer(256)
		_self.__GetErrorDescription(error, value)
		return value.value.decode()

	def get_last_error(self):
		'''Wrapper to CAEN_FELib_GetLastError'''
		value = ct.create_string_buffer(1024)
		self.__GetLastError(value)
		return value.value.decode()

