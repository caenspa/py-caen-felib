"""
@ingroup Python
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2023 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
import sys
from typing import Any, Optional, overload


class Lib:
    """
    This class loads the shared library and exposes its functions on its
    public attributes using ctypes.
    """

    def __init__(self, name: str) -> None:
        self.__name = name
        self.__load_lib()

    def __load_lib(self) -> None:
        loader: ct.LibraryLoader
        loader_variadic: ct.LibraryLoader

        # Platform dependent stuff
        if sys.platform == 'win32':
            # API functions are declared as __stdcall, but variadic
            # functions are __cdecl even if declared as __stdcall.
            # This difference applies only to 32 bit applications,
            # 64 bit applications have its own calling convention.
            loader = ct.windll
            loader_variadic = ct.cdll
            path = f'{self.name}.dll'
        else:
            loader = ct.cdll
            loader_variadic = ct.cdll
            path = f'lib{self.name}.so'

        self.__path = path

        # Load library
        try:
            self.__lib = loader.LoadLibrary(self.path)
            self.__lib_variadic = loader_variadic.LoadLibrary(self.path)
        except FileNotFoundError as ex:
            raise RuntimeError(
                f'Library {self.name} not found. This module requires '
                'the latest version of the library to be installed on '
                'your system. You may find the official installers at '
                'https://www.caen.it/. Please install it and retry.'
            ) from ex

    @property
    def name(self) -> str:
        """Name of the shared library"""
        return self.__name

    @property
    def path(self) -> Any:
        """Path of the shared library"""
        return self.__path

    @property
    def lib(self) -> Any:
        """ctypes object to shared library"""
        return self.__lib

    @property
    def lib_variadic(self) -> Any:
        """ctypes object to shared library (for variadic functions)"""
        return self.__lib_variadic

    # Python utilities

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.path})'

    def __str__(self) -> str:
        return self.path


def version_to_tuple(version: str) -> tuple[int, ...]:
    """Version string in the form N.N.N to tuple (N, N, N)"""
    return tuple(map(int, version.split('.')))


def to_bytes(path: str) -> bytes:
    """Convert string to bytes"""
    return path.encode()


@overload
def to_bytes_opt(path: None) -> None: ...
@overload
def to_bytes_opt(path: str) -> bytes: ...


def to_bytes_opt(path: Optional[str]) -> Optional[bytes]:
    """Convert string to bytes"""
    return None if path is None else to_bytes(path)


# Slots brings some performance improvements and memory savings.
# In caen_felib are also a trick to prevent users from trying to set
# Node values using the `__setattr__` method instead of the value
# attribute.
if sys.version_info >= (3, 10):
    dataclass_slots = {'slots': True}
else:
    dataclass_slots = {}


# Weakref support is required by the cache manager.
if sys.version_info >= (3, 11):
    dataclass_slots_weakref = dataclass_slots | {'weakref_slot': True}
else:
    dataclass_slots_weakref = {}
