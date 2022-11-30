__author__		= 'Giovanni Cerretani'
__copyright__	= 'Copyright (C) 2020-2022 CAEN SpA'
__license__		= 'LGPLv3+'

class Error(RuntimeError):
	def __init__(self, message, error):
		super().__init__(message)
		self.error = error

class Timeout(Error):
	def __init__(self, error):
		super().__init__('timeout', error)

class Stop(Error):
	def __init__(self, error):
		super().__init__('stop', error)
