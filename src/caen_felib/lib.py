"""
@ingroup Python
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2023 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'  # SPDX-License-Identifier

import ctypes as ct
import ctypes.util as ctutil
from json import loads
from sys import platform
from typing import Callable, Dict, Tuple, Type
from typing_extensions import TypeAlias

from caen_felib import error

# Comments on imports:
# - TypeAlias moved to typing on Python 3.10


class _Lib:
    """
    This class loads the CAEN_FELib shared library and
    exposes its functions on its public attributes
    using ctypes.
    """

    APIType: TypeAlias = Callable[..., int]

    name: str
    path: str

    open: APIType
    close: APIType
    get_device_tree: APIType
    get_child_handles: APIType
    get_parent_handle: APIType
    get_handle: APIType
    get_path: APIType
    get_node_properties: APIType
    get_value: APIType
    set_value: APIType
    get_user_register: APIType
    set_user_register: APIType
    send_command: APIType
    set_read_data_format: APIType
    has_data: APIType
    read_data: APIType

    def __init__(self, name: str) -> None:
        self.name = name
        self.__load_lib()
        self.__load_api()

    def __load_lib(self) -> None:
        loader: ct.LibraryLoader
        loader_variadic: ct.LibraryLoader

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

        path = ctutil.find_library(self.name)
        if path is None:
            raise RuntimeError(
                f'Library {self.name} not found. '
                'This module requires the latest version of '
                'the library to be installed on your system. '
                'You may find the official installers at '
                'https://www.caen.it/. '
                'Please install it and retry.'
            )

        ## Library path on the filesystem
        self.path = path

        # Load library
        self.__lib = loader.LoadLibrary(self.path)
        self.__lib_variadic = loader_variadic.LoadLibrary(self.path)

    def __load_api(self) -> None:
        # Load API not related to devices
        self.__get_lib_info = self.__get('GetLibInfo', ct.c_char_p, ct.c_size_t)
        self.__get_lib_version = self.__get('GetLibVersion', ct.c_char_p)
        self.__get_error_name = self.__get('GetErrorName', ct.c_int, ct.c_char_p)
        self.__get_error_description = self.__get('GetErrorDescription', ct.c_int, ct.c_char_p)
        self.__get_last_error = self.__get('GetLastError', ct.c_char_p)
        self.__devices_discovery = self.__get('DevicesDiscovery', ct.c_char_p, ct.c_size_t, ct.c_int)

        # Load API
        self.open = self.__get('Open', ct.c_char_p, ct.POINTER(ct.c_uint64))
        self.close = self.__get('Close', ct.c_uint64)
        self.get_impl_lib_version = self.__get('GetImplLibVersion', ct.c_uint64, ct.c_char_p, min_version=(1, 3, 0))
        self.get_device_tree = self.__get('GetDeviceTree', ct.c_uint64, ct.c_char_p, ct.c_size_t)
        self.get_child_handles = self.__get('GetChildHandles', ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64), ct.c_size_t)
        self.get_parent_handle = self.__get('GetParentHandle', ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64))
        self.get_handle = self.__get('GetHandle', ct.c_uint64, ct.c_char_p, ct.POINTER(ct.c_uint64))
        self.get_path = self.__get('GetPath', ct.c_uint64, ct.c_char_p)
        self.get_node_properties = self.__get('GetNodeProperties', ct.c_uint64, ct.c_char_p, ct.c_char_p, ct.POINTER(ct.c_int))
        self.get_value = self.__get('GetValue', ct.c_uint64, ct.c_char_p, ct.c_char_p)
        self.set_value = self.__get('SetValue', ct.c_uint64, ct.c_char_p, ct.c_char_p)
        self.get_user_register = self.__get('GetUserRegister', ct.c_uint64, ct.c_uint32, ct.POINTER(ct.c_uint32))
        self.set_user_register = self.__get('SetUserRegister', ct.c_uint64, ct.c_uint32, ct.c_uint32)
        self.send_command = self.__get('SendCommand', ct.c_uint64, ct.c_char_p)
        self.set_read_data_format = self.__get('SetReadDataFormat', ct.c_uint64, ct.c_char_p)
        self.has_data = self.__get('HasData', ct.c_uint64, ct.c_int, min_version=(1, 2, 0))

        # Load variadic API
        # Notes:
        # - Remember to manually apply default argument promotions when calling variadic functions;
        #     anyway it is not necessary with ReadData since variadic arguments are always pointers,
        #     that are not subject to default argument promotion. More details on
        #     https://en.cppreference.com/w/c/language/conversion#Default_argument_promotions
        # - On some platforms, like Apple ARM64, "it is required to specify the argtypes attribute for
        #     the regular, non-variadic, function arguments" (see ctypes documentation); the other
        #     variadic arguments could be set at runtime after a call to SetReadDataFormat, but this
        #     would not be safe because ReadData can be called concurrently from multiple threads with
        #     different signatures, so arguments (always pointers in this case) must be placed without
        #     relying on ctypes automatic conversions with from_param methods. For more details, see
        #     https://stackoverflow.com/q/74630617/3287591
        self.read_data = self.__get('ReadData', ct.c_uint64, ct.c_int, variadic=True)

    def __api_errcheck(self, res: int, func: Callable, _: Tuple) -> int:
        # res can be positive on GetChildHandles and GetDeviceTree
        if res < 0:
            raise error.Error(self.last_error, res, func.__name__)
        return res

    def __get(self, name: str, *args: Type, **kwargs) -> Callable[..., int]:
        min_version = kwargs.get('min_version')
        if min_version is not None:
            # This feature requires __get_lib_version to be already defined
            assert self.__get_lib_version is not None
            if not self.__ver_at_least(min_version):
                def fallback(*args, **kwargs):
                    raise RuntimeError(f'{name} requires {self.name} >= {min_version}. Please update it.')
                return fallback
        lib = self.__lib if not kwargs.get('variadic', False) else self.__lib_variadic
        func = getattr(lib, f'CAEN_FELib_{name}')
        func.argtypes = args
        func.restype = ct.c_int
        func.errcheck = self.__api_errcheck
        return func

    @staticmethod
    def __ver_tuple(version: str) -> Tuple[int, ...]:
        return tuple(map(int, version.split('.')))

    def __ver_at_least(self, target: Tuple[int, ...]) -> bool:
        ver = self.get_lib_version()
        return self.__ver_tuple(ver) >= target

    # C API wrappers

    def get_lib_info(self, initial_size: int = 2**22) -> Dict:
        """
        Wrapper to CAEN_FELib_GetLibInfo()

        @sa info
        @param[in] initial_size		initial size to be allocated for the first iteration
        @return						JSON representation of the library info (a dictionary)
        """
        while True:
            lib_info = ct.create_string_buffer(initial_size)
            res = self.__get_lib_info(lib_info, initial_size)
            if res < initial_size:  # equal not fine, see docs
                return loads(lib_info.value.decode())
            initial_size = res

    def get_lib_version(self) -> str:
        """
        Wrapper to CAEN_FELib_GetLibVersion()

        @sa version
        @return						version (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(16)
        self.__get_lib_version(value)
        return value.value.decode()

    def get_error_name(self, error_code: int) -> str:
        """
        Wrapper to CAEN_FELib_GetErrorName()

        @param[in] error_code		error code returned by library functions
        @return						error name (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(32)
        self.__get_error_name(error_code, value)
        return value.value.decode()

    def get_error_description(self, error_code: int) -> str:
        """
        Wrapper to CAEN_FELib_GetErrorDescription()

        @param[in] error_code		error code returned by library functions
        @return						error description (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(256)
        self.__get_error_description(error_code, value)
        return value.value.decode()

    def get_last_error(self) -> str:
        """
        Wrapper to CAEN_FELib_GetLastError()

        @sa last_error
        @return						last error description (a string)
        @exception					error.Error in case of error
        """
        value = ct.create_string_buffer(1024)
        self.__get_last_error(value)
        return value.value.decode()

    # Python utilities

    @property
    def info(self) -> Dict:
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

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.path})'

    def __str__(self) -> str:
        return self.path
