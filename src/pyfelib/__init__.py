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
		self.__GetLibInfo.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
		self.__GetLibInfo.restype = ctypes.c_int

		self.__GetLibVersion = lib.CAEN_FELib_GetLibVersion
		self.__GetLibVersion.argtypes = [ctypes.c_char_p]
		self.__GetLibVersion.restype = ctypes.c_int

		self.__GetErrorName = lib.CAEN_FELib_GetErrorName
		self.__GetErrorName.argtypes = [ctypes.c_int, ctypes.c_char_p]
		self.__GetErrorName.restype = ctypes.c_int

		self.__GetErrorDescription = lib.CAEN_FELib_GetErrorDescription
		self.__GetErrorDescription.argtypes = [ctypes.c_int, ctypes.c_char_p]
		self.__GetErrorDescription.restype = ctypes.c_int

		self.__GetLastError = lib.CAEN_FELib_GetLastError
		self.__GetLastError.argtypes = [ctypes.c_char_p]
		self.__GetLastError.restype = ctypes.c_int

		self.__DevicesDiscovery = lib.CAEN_FELib_DevicesDiscovery
		self.__DevicesDiscovery.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]
		self.__DevicesDiscovery.restype = ctypes.c_int

		# Load API
		self.Open = lib.CAEN_FELib_Open
		self.Open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint64)]
		self.Open.restype = ctypes.c_int

		self.Close = lib.CAEN_FELib_Close
		self.Close.argtypes = [ctypes.c_uint64]
		self.Close.restype = ctypes.c_int

		self.GetDeviceTree = lib.CAEN_FELib_GetDeviceTree
		self.GetDeviceTree.argtypes = [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_size_t]
		self.GetDeviceTree.restype = ctypes.c_int

		self.GetChildHandles = lib.CAEN_FELib_GetChildHandles
		self.GetChildHandles.argtypes = [ctypes.c_uint64, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t]
		self.GetChildHandles.restype = ctypes.c_int

		self.GetParentHandle = lib.CAEN_FELib_GetParentHandle
		self.GetParentHandle.argtypes = [ctypes.c_uint64, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint64)]
		self.GetParentHandle.restype = ctypes.c_int

		self.GetHandle = lib.CAEN_FELib_GetHandle
		self.GetHandle.argtypes = [ctypes.c_uint64, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint64)]
		self.GetHandle.restype = ctypes.c_int

		self.GetPath = lib.CAEN_FELib_GetPath
		self.GetPath.argtypes = [ctypes.c_uint64, ctypes.c_char_p]
		self.GetPath.restype = ctypes.c_int

		self.GetNodeProperties = lib.CAEN_FELib_GetNodeProperties
		self.GetNodeProperties.argtypes = [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
		self.GetNodeProperties.restype = ctypes.c_int

		self.GetValue = lib.CAEN_FELib_GetValue
		self.GetValue.argtypes = [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p]
		self.GetValue.restype = ctypes.c_int

		self.SetValue = lib.CAEN_FELib_SetValue
		self.SetValue.argtypes = [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_char_p]
		self.SetValue.restype = ctypes.c_int

		self.GetUserRegister = lib.CAEN_FELib_GetUserRegister
		self.GetUserRegister.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
		self.GetUserRegister.restype = ctypes.c_int

		self.SetUserRegister = lib.CAEN_FELib_SetUserRegister
		self.SetUserRegister.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32]
		self.SetUserRegister.restype = ctypes.c_int

		self.SendCommand = lib.CAEN_FELib_SendCommand
		self.SendCommand.argtypes = [ctypes.c_uint64, ctypes.c_char_p]
		self.SendCommand.restype = ctypes.c_int

		self.SetReadDataFormat = lib.CAEN_FELib_SetReadDataFormat
		self.SetReadDataFormat.argtypes = [ctypes.c_uint64, ctypes.c_char_p]
		self.SetReadDataFormat.restype = ctypes.c_int

		self.HasData = lib.CAEN_FELib_HasData
		self.HasData.argtypes = [ctypes.c_uint64, ctypes.c_int]
		self.HasData.restype = ctypes.c_int

		# Load variadic API
		# Remember to manually apply default argument promotions
		# when calling variadic functions!
		self.ReadData = lib_variadic.CAEN_FELib_ReadData
		self.ReadData.restype = ctypes.c_int

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
		return value.value.decode('ascii')

	def get_error_description(self, error):
		value = ctypes.create_string_buffer(256)
		res = _lib.__GetErrorDescription(error, value)
		if res != 0:
			raise FELibError(_lib.get_last_error(), res)
		return value.value.decode('ascii')

	def get_last_error(self):
		value = ctypes.create_string_buffer(1024)
		ret = self.__GetLastError(value)
		if ret != 0:
			raise FELibError('get_last_error failed', res)
		return value.value.decode('ascii')

# Initialize library
lib = Lib()
