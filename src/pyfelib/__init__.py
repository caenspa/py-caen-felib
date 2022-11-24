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

		# Load libraries
		lib = loader.LoadLibrary(lib_name)
		lib_variadic = loader_variadic.LoadLibrary(lib_name)

		# Load API not related to devices
		self.__GetLibInfo = lib.CAEN_FELib_GetLibInfo
		self.__set_prototype(self.__GetLibInfo, [ctypes.c_char_p, ctypes.c_size_t])

		self.__GetLibVersion = lib.CAEN_FELib_GetLibVersion
		self.__set_prototype(self.__GetLibVersion, [ctypes.c_char_p])

		self.__GetErrorName = lib.CAEN_FELib_GetErrorName
		self.__set_prototype(self.__GetErrorName, [ctypes.c_int, ctypes.c_char_p])

		self.__GetErrorDescription = lib.CAEN_FELib_GetErrorDescription
		self.__set_prototype(self.__GetErrorDescription, [ctypes.c_int, ctypes.c_char_p])

		self.__GetLastError = lib.CAEN_FELib_GetLastError
		self.__set_prototype(self.__GetLastError, [ctypes.c_char_p])

		self.__DevicesDiscovery = lib.CAEN_FELib_DevicesDiscovery
		self.__set_prototype(self.__DevicesDiscovery, [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int])

		# Load API
		self.Open = lib.CAEN_FELib_Open
		self.__set_prototype(self.Open, [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint64)])

		self.Close = lib.CAEN_FELib_Close
		self.__set_prototype(self.Close, [ctypes.c_uint64])

		self.GetDeviceTree = lib.CAEN_FELib_GetDeviceTree
		self.__set_prototype(self.GetDeviceTree, [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_size_t])

		self.GetChildHandles = lib.CAEN_FELib_GetChildHandles
		self.__set_prototype(self.GetChildHandles, [ctypes.c_uint64, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t])

		self.GetParentHandle = lib.CAEN_FELib_GetParentHandle
		self.__set_prototype(self.GetParentHandle, [ctypes.c_uint64, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint64)])

		self.GetHandle = lib.CAEN_FELib_GetHandle
		self.__set_prototype(self.GetHandle, [ctypes.c_uint64, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint64)])

		self.GetPath = lib.CAEN_FELib_GetPath
		self.__set_prototype(self.GetPath, [ctypes.c_uint64, ctypes.c_char_p])

		self.GetNodeProperties = lib.CAEN_FELib_GetNodeProperties
		self.__set_prototype(self.GetNodeProperties, [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)])

		self.GetValue = lib.CAEN_FELib_GetValue
		self.__set_prototype(self.GetValue, [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p])

		self.SetValue = lib.CAEN_FELib_SetValue
		self.__set_prototype(self.SetValue, [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p])

		self.GetUserRegister = lib.CAEN_FELib_GetUserRegister
		self.__set_prototype(self.GetUserRegister, [ctypes.c_uint64, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)])

		self.SetUserRegister = lib.CAEN_FELib_SetUserRegister
		self.__set_prototype(self.SetUserRegister, [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32])

		self.SendCommand = lib.CAEN_FELib_SendCommand
		self.__set_prototype(self.SendCommand, [ctypes.c_uint64, ctypes.c_char_p])

		self.SetReadDataFormat = lib.CAEN_FELib_SetReadDataFormat
		self.__set_prototype(self.SetReadDataFormat, [ctypes.c_uint64, ctypes.c_char_p])

		self.HasData = lib.CAEN_FELib_HasData
		self.__set_prototype(self.HasData, [ctypes.c_uint64, ctypes.c_int])

		# Load variadic API
		# Notes:
		# - remember to manually apply default argument promotions when calling variadic functions!
		# - argtypes is not set; anyway, according to ctypes documentation, there could be problems
		#   on ARM64 for Apple Platforms.
		self.ReadData = lib_variadic.CAEN_FELib_ReadData
		self.__set_prototype(self.ReadData, None)

	def __errcheck(self, res, func, args):
		if res < 0:
			raise FELibError(self.get_last_error(), res)
		return res

	def __set_prototype(self, func, argtypes):
		func.argtypes = argtypes
		func.restype = ctypes.c_int
		func.errcheck = self.__errcheck

	def get_lib_version(self):
		value = ctypes.create_string_buffer(16)
		ret = self.__GetLibVersion(value)
		if ret != 0:
			raise FELibError(self.get_last_error(), res)
		return value.value.decode()

	def get_error_name(self, error):
		value = ctypes.create_string_buffer(32)
		res = _lib.__GetErrorName(error, value)
		if res != 0:
			raise FELibError(_lib.get_last_error(), res)
		return value.value.decode()

	def get_error_description(self, error):
		value = ctypes.create_string_buffer(256)
		res = _lib.__GetErrorDescription(error, value)
		if res != 0:
			raise FELibError(_lib.get_last_error(), res)
		return value.value.decode()

	def get_last_error(self):
		value = ctypes.create_string_buffer(1024)
		ret = self.__GetLastError(value)
		if ret != 0:
			raise FELibError('get_last_error failed', res)
		return value.value.decode()

# Initialize library
lib = Lib()
