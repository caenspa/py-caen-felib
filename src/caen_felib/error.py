__author__		= 'Giovanni Cerretani'
__copyright__	= 'Copyright (C) 2020-2022 CAEN SpA'
__license__		= 'LGPLv3+'

class FELibError(RuntimeError):
	def __init__(self, message, error):
		super().__init__(message)
		self.error = error

class FELibTimeout(FELibError):
	def __init__(self, error):
		super().__init__('timeout', error)

class FELibStop(FELibError):
	def __init__(self, error):
		super().__init__('stop', error)
