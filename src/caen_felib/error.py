"""
@ingroup Python
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2023 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'  # SPDX-License-Identifier

from enum import IntEnum, unique


@unique
class ErrorCode(IntEnum):
    """
    Wrapper to ::CAEN_FELib_ErrorCode
    """
    SUCCESS = 0
    GENERIC_ERROR = -1
    INVALID_PARAM = -2
    DEVICE_ALREADY_OPEN = -3
    DEVICE_NOT_FOUND = -4
    MAX_DEVICES_ERROR = -5
    COMMAND_ERROR = -6
    INTERNAL_ERROR = -7
    NOT_IMPLEMENTED = -8
    INVALID_HANDLE = -9
    DEVICE_LIBRARY_NOT_AVAILABLE = -10
    TIMEOUT = -11
    STOP = -12
    DISABLED = -13
    BAD_LIBRARY_VERSION = -14
    COMMUNICATION_ERROR = -15


class Error(RuntimeError):
    """
    Raised when a wrapped C API function returns
    negative values.
    """

    code: ErrorCode
    func: str

    def __init__(self, message: str, res: int, func: str) -> None:
        super().__init__(message)

        ## Error code as instance of ErrorCode
        self.code = ErrorCode(res)

        ## Name of failed function
        self.func = func
