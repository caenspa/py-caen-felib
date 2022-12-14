"""
@ingroup Python
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2020-2022 CAEN SpA'
__license__ = 'LGPLv3+'

from functools import lru_cache, wraps, _lru_cache_wrapper
from typing import Callable, List, Optional, TypeVar, overload
from weakref import ref, ReferenceType

from typing_extensions import Concatenate, ParamSpec  # Required on Python 3.8


class CacheManager(List[_lru_cache_wrapper]):
    def clear_all(self) -> None:
        for wrapper in self:
            wrapper.cache_clear()


_PSelf = TypeVar('_PSelf')
_P = ParamSpec('_P')
_T = TypeVar('_T')


def lru_cache_method(
    cache_manager: Optional[CacheManager] = None,
    maxsize: int = 128,
    typed: bool = False,
) -> Callable[[Callable[Concatenate[_PSelf, _P], _T]], Callable[Concatenate[_PSelf, _P], _T]]:
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

    def wrapper(method: Callable[Concatenate[_PSelf, _P], _T]) -> Callable[Concatenate[_PSelf, _P], _T]:

        @lru_cache(maxsize, typed)
        def cached_method(self_ref: ReferenceType[_PSelf], *args: _P.args, **kwargs: _P.kwargs) -> _T:
            self = self_ref()
            # cannot be null here because this function is called by inner()
            assert self is not None
            return method(self, *args, **kwargs)

        @wraps(method)
        def inner(self: _PSelf, *args: _P.args, **kwargs: _P.kwargs) -> _T:
            # Ignore MyPy type checks because of bugs on lru_cache support.
            # See https://stackoverflow.com/a/73517689/3287591.
            return cached_method(ref(self), *args, **kwargs)  # type: ignore

        if cache_manager is not None:
            cache_manager.append(cached_method)

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
