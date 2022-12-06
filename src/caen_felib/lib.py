"""
@ingroup Python
"""

__author__		= 'Giovanni Cerretani'
__copyright__	= 'Copyright (C) 2020-2022 CAEN SpA'
__license__		= 'LGPLv3+'

import ctypes as ct
import ctypes.util as ctutil
from sys import platform
from typing import Callable

import caen_felib.error as error

class _Lib:
	"""
	This class loads the CAEN_FELib shared library and
	exposes its functions on its public attributes
	using ctypes.
	"""

	path: str
	Open: Callable
	Close: Callable
	GetDeviceTree: Callable
	GetChildHandles: Callable
	GetParentHandle: Callable
	GetHandle: Callable
	GetPath: Callable
	GetNodeProperties: Callable
	GetValue: Callable
	SetValue: Callable
	GetUserRegister: Callable
	SetUserRegister: Callable
	SendCommand: Callable
	SetReadDataFormat: Callable
	HasData: Callable
	ReadData: Callable

	def __init__(self, name: str):

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

		## Library path on the filesystem
		self.path = ctutil.find_library(name)

		# Load library
		self.__lib = loader.LoadLibrary(self.path)
		self.__lib_variadic = loader_variadic.LoadLibrary(self.path)

		# Load API not related to devices
		self.__GetLibInfo = self.__lib.CAEN_FELib_GetLibInfo
		self.__set(self.__GetLibInfo, [ct.c_char_p, ct.c_size_t])

		self.__GetLibVersion = self.__lib.CAEN_FELib_GetLibVersion
		self.__set(self.__GetLibVersion, [ct.c_char_p])

		self.__GetErrorName = self.__lib.CAEN_FELib_GetErrorName
		self.__set(self.__GetErrorName, [ct.c_int, ct.c_char_p])

		self.__GetErrorDescription = self.__lib.CAEN_FELib_GetErrorDescription
		self.__set(self.__GetErrorDescription, [ct.c_int, ct.c_char_p])

		self.__GetLastError = self.__lib.CAEN_FELib_GetLastError
		self.__set(self.__GetLastError, [ct.c_char_p])

		self.__DevicesDiscovery = self.__lib.CAEN_FELib_DevicesDiscovery
		self.__set(self.__DevicesDiscovery, [ct.c_char_p, ct.c_size_t, ct.c_int])

		# Load API
		self.Open = self.__lib.CAEN_FELib_Open
		self.__set(self.Open, [ct.c_char_p, ct.POINTER(ct.c_uint64)])

		self.Close = self.__lib.CAEN_FELib_Close
		self.__set(self.Close, [ct.c_uint64])

		self.GetDeviceTree = self.__lib.CAEN_FELib_GetDeviceTree
		self.__set(self.GetDeviceTree, [ct.c_uint64, ct.c_char_p, ct.c_size_t])

		self.GetChildHandles = self.__lib.CAEN_FELib_GetChildHandles
		self.__set(self.GetChildHandles, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64), ct.c_size_t])

		self.GetParentHandle = self.__lib.CAEN_FELib_GetParentHandle
		self.__set(self.GetParentHandle, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64)])

		self.GetHandle = self.__lib.CAEN_FELib_GetHandle
		self.__set(self.GetHandle, [ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64)])

		self.GetPath = self.__lib.CAEN_FELib_GetPath
		self.__set(self.GetPath, [ct.c_uint64, ct.c_char_p])

		self.GetNodeProperties = self.__lib.CAEN_FELib_GetNodeProperties
		self.__set(self.GetNodeProperties, [ct.c_uint64, ct.c_char_p, ct.c_char_p, ct.POINTER(ct.c_int)])

		self.GetValue = self.__lib.CAEN_FELib_GetValue
		self.__set(self.GetValue, [ct.c_uint64, ct.c_char_p, ct.c_char_p])

		self.SetValue = self.__lib.CAEN_FELib_SetValue
		self.__set(self.SetValue, [ct.c_uint64, ct.c_char_p, ct.c_char_p])

		self.GetUserRegister = self.__lib.CAEN_FELib_GetUserRegister
		self.__set(self.GetUserRegister, [ct.c_uint64, ct.c_uint32, ct.POINTER(ct.c_uint32)])

		self.SetUserRegister = self.__lib.CAEN_FELib_SetUserRegister
		self.__set(self.SetUserRegister, [ct.c_uint64, ct.c_uint32, ct.c_uint32])

		self.SendCommand = self.__lib.CAEN_FELib_SendCommand
		self.__set(self.SendCommand, [ct.c_uint64, ct.c_char_p])

		self.SetReadDataFormat = self.__lib.CAEN_FELib_SetReadDataFormat
		self.__set(self.SetReadDataFormat, [ct.c_uint64, ct.c_char_p])

		self.HasData = self.__lib.CAEN_FELib_HasData
		self.__set(self.HasData, [ct.c_uint64, ct.c_int])

		# Load variadic API
		# Notes:
		# - Remember to manually apply default argument promotions when calling variadic functions;
		#     anyway it is not necessary with ReadData since variadic arguments are always pointers,
		#     that are not subject to default argument promotion. For more detail, see
		#     https://en.cppreference.com/w/c/language/conversion#Default_argument_promotions
		# - On some platforms, like Apple ARM64, "it is required to specify the argtypes attribute for
		#     the regular, non-variadic, function arguments" (see ctypes documentation); the other
		#     variadic arguments could be set at runtime after a call to SetReadDataFormat, but this
		#     would not be safe because ReadData can be called concurrently from multiple threads with
		#     different signatures, so arguments (always pointers in this case) must be placed without
		#     relying on ctypes automatic conversions with from_param methods. For more details, see
		#     https://stackoverflow.com/q/74630617/3287591
		self.ReadData = self.__lib_variadic.CAEN_FELib_ReadData
		self.__set(self.ReadData, [ct.c_uint64, ct.c_int])

	def __api_errcheck(self, res, func, args):
		# res can be positive on GetChildHandles and GetDeviceTree
		if res < 0:
			raise error.Error(self.last_error, res)
		return res

	def __set(self, func, argtypes):
		func.argtypes = argtypes
		func.restype = ct.c_int
		func.errcheck = self.__api_errcheck

	# C API wrappers

	def get_lib_info(self, initial_size: int=2**22) -> dict:
		"""
		Wrapper to CAEN_FELib_GetLibInfo()

		@sa info
		@param[in] initial_size		inizial size to allocate for the first iteration
		@return						JSON representation of the library info (a dictionary)
		"""
		while True:
			lib_info = ct.create_string_buffer(initial_size)
			res = lib.__GetLibInfo(lib_info, initial_size)
			if res < initial_size: # equal not fine, see docs
				return json.loads(lib_info.value.decode())
			initial_size = res

	def get_lib_version(self) -> str:
		"""
		Wrapper to CAEN_FELib_GetLibVersion()

		@sa version
		@return						version (a string)
		@exception					error.Error in case of error
		"""
		value = ct.create_string_buffer(16)
		self.__GetLibVersion(value)
		return value.value.decode()

	def get_error_name(self, error: int) -> str:
		"""
		Wrapper to CAEN_FELib_GetErrorName()

		@param[in] error			error code returned by library functions
		@return						error name (a string)
		@exception					error.Error in case of error
		"""
		value = ct.create_string_buffer(32)
		_self.__GetErrorName(error, value)
		return value.value.decode()

	def get_error_description(self, error: int) -> str:
		"""
		Wrapper to CAEN_FELib_GetErrorDescription()

		@param[in] error			error code returned by library functions
		@return						error description (a string)
		@exception					error.Error in case of error
		"""
		value = ct.create_string_buffer(256)
		_self.__GetErrorDescription(error, value)
		return value.value.decode()

	def get_last_error(self) -> str:
		"""
		Wrapper to CAEN_FELib_GetLastError()

		@sa last_error
		@return						last error description (a string)
		@exception					error.Error in case of error
		"""
		value = ct.create_string_buffer(1024)
		self.__GetLastError(value)
		return value.value.decode()

	# Python utilities

	@property
	def info(self) -> dict:
		"""Get library info"""
		return self.get_lib_info()

	@property
	def version(self) -> str:
		"""Get library version"""
		return self.get_lib_version()

	@property
	def last_error(self) -> str:
		"""Get last error"""
		return self.get_last_error()

	def __repr__(self):
		return f'{__class__.__name__}({self.path})'

	def __str__(self):
		return self.path
