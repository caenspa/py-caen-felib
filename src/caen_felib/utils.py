"""
@ingroup Python
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2020-2022 CAEN SpA'
__license__ = 'LGPLv3+'

from functools import lru_cache, wraps
from typing import Callable, Optional, TypeVar
from weakref import ref, ReferenceType

from typing_extensions import Concatenate, ParamSpec # Required on Python 3.8


_T = TypeVar('_T')
_Self = TypeVar('_Self')
_P = ParamSpec('_P')

def lru_cache_method(
        method: Callable[Concatenate[_Self, _P], _T],
        maxsize: int = 128,
        typed: bool = False
    ) -> Callable[Concatenate[_Self, _P], _T]:
    """
    LRU cache decorator that keeps a weak reference to self.

    To be used as decorator on methods that are known to return always
    the same value. This can improve the performances of some methods
    by a factor > 1000.
    This wrapper using weak references is required: functools.lru_cache
    holds a reference to all arguments: using directly on the methos it
    would hold a reference to self, introducing subdle memory leaks.

    @sa https://stackoverflow.com/a/68052994/3287591
    """

    @lru_cache(maxsize, typed)
    def cached_method(_self: ReferenceType[_Self], *args: _P.args, **kwargs: _P.kwargs) -> _T:
        _cached_self = _self()
        if _cached_self is None:
            raise RuntimeError('invalid cache')
        return method(_cached_self, *args, **kwargs)

    @wraps(method)
    def inner(self: _Self, *args: _P.args, **kwargs: _P.kwargs) -> _T:
        # Ignore MyPy type checks because of bugs on lru_cache support
        return cached_method(ref(self), *args, **kwargs) # type: ignore

    return inner


def to_bytes(path: str) -> bytes:
    """Convert string to bytes"""
    return path.encode()


def to_bytes_opt(path: Optional[str]) -> Optional[bytes]:
    """Convert string to bytes"""
    return None if path is None else to_bytes(path)
