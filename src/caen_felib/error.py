'''
@ingroup Python
'''

__author__		= 'Giovanni Cerretani'
__copyright__	= 'Copyright (C) 2020-2022 CAEN SpA'
__license__		= 'LGPLv3+'

from enum import Enum

class ErrorCode(Enum):
	'''Wrapper to ::CAEN_FELib_ErrorCode'''
	Success						= 0
	GenericError				= -1
	InvalidParam				= -2
	DeviceAlreadyOpen			= -3
	DeviceNotFound				= -4
	MaxDevicesError				= -5
	CommandError				= -6
	InternalError				= -7
	NotImplemented				= -8
	InvalidHandle				= -9
	DeviceLibraryNotAvailable	= -10
	Timeout						= -11
	Stop						= -12
	Disabled					= -13
	BadLibraryVersion			= -14
	CommunicationError			= -15

class Error(RuntimeError):

	def __init__(self, message, res):
		super().__init__(message)
		self.code = ErrorCode(res)
