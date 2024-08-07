"""
@ingroup Python
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2023 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

import ctypes as ct
from functools import lru_cache, wraps, _lru_cache_wrapper
import sys
from typing import Any, List, Optional, Tuple, TypeVar, overload
from weakref import ref, ReferenceType

from typing_extensions import ParamSpec

# Comments on imports:
# - ReferenceType is not subscriptable on Python <= 3.8
# - Concatenate and ParamSpec moved to typing on Python 3.10


class Lib:
    """
    This class loads the shared library and
    exposes its functions on its public attributes
    using ctypes.
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

        ## Library path on the filesystem
        self.__path = path

        # Load library
        try:
            self.__lib = loader.LoadLibrary(path)
            self.__lib_variadic = loader_variadic.LoadLibrary(self.path)
        except FileNotFoundError as ex:
            raise RuntimeError(
                f'Library {self.name} not found. '
                'This module requires the latest version of '
                'the library to be installed on your system. '
                'You may find the official installers at '
                'https://www.caen.it/. '
                'Please install it and retry.'
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


def version_to_tuple(version: str) -> Tuple[int, ...]:
    """Version string in the form N.N.N to tuple (N, N, N)"""
    return tuple(map(int, version.split('.')))


class CacheManager(List[_lru_cache_wrapper]):
    """
    A simple list of functions returned by `@lru_cache` decorator.

    To be used with the optional parameter @p cache_manager of
    lru_cache_method(), that will store a reference to the cached function
    inside this list. This is a typing-safe way to call `cache_clear` and
    `cache_info` of the internal cached functions, even if not exposed
    directly by the inner function returned by lru_cache_method().
    """
    def clear_all(self) -> None:
        """Invoke `cache_clear` on all functions in the list"""
        for wrapper in self:
            wrapper.cache_clear()


_S = TypeVar('_S')
_P = ParamSpec('_P')
_T = TypeVar('_T')


# Typing support for decorators comes with Python 3.10.
# Omitted because very verbose.


def lru_cache_method(cache_manager: Optional[CacheManager] = None, maxsize: int = 128, typed: bool = False):
    """
    LRU cache decorator that keeps a weak reference to self.

    To be used as decorator on methods that are known to return always
    the same value. This can improve the performances of some methods
    by a factor > 1000.
    This wrapper using weak references is required: functools.lru_cache
    holds a reference to all arguments: using directly on the methods it
    would hold a reference to self, introducing subdle memory leaks.

    @sa https://stackoverflow.com/a/68052994/3287591
    """

    def wrapper(method):

        @lru_cache(maxsize, typed)
        # ReferenceType is not subscriptable on Python <= 3.8
        def cached_method(self_ref: ReferenceType, *args, **kwargs):
            self = self_ref()
            assert self is not None  # this function is always called by inner()
            return method(self, *args, **kwargs)

        @wraps(method)
        def inner(self, *args, **kwargs):
            # Ignore MyPy type checks because of bugs on lru_cache support.
            # See https://stackoverflow.com/a/73517689/3287591.
            return cached_method(ref(self), *args, **kwargs)  # type: ignore

        # Optionally store a reference to lru_cache decorated function to
        # simplify cache management. See CacheManager documentation.
        if cache_manager is not None:
            cache_manager.append(cached_method)

        return inner

    return wrapper


def lru_cache_clear(cache_manager: CacheManager):
    """
    LRU cache decorator that clear cache.

    To be used as decorator on methods that are known to invalidate
    the cache.
    """

    def wrapper(method):

        # ReferenceType is not subscriptable on Python <= 3.8
        def not_cached_method(self_ref: ReferenceType, *args, **kwargs):
            self = self_ref()
            assert self is not None  # this function is always called by inner()
            return method(self, *args, **kwargs)

        @wraps(method)
        def inner(self, *args, **kwargs):
            # Ignore MyPy type checks because of bugs on lru_cache support.
            # See https://stackoverflow.com/a/73517689/3287591.
            cache_manager.clear_all()
            return not_cached_method(ref(self), *args, **kwargs)  # type: ignore

        return inner

    return wrapper



def to_bytes(path: str) -> bytes:
    """Convert string to bytes"""
    return path.encode()


@overload
def to_bytes_opt(path: None) -> None:
    ...


@overload
def to_bytes_opt(path: str) -> bytes:
    ...


def to_bytes_opt(path: Optional[str]) -> Optional[bytes]:
    """Convert string to bytes"""
    return None if path is None else to_bytes(path)
