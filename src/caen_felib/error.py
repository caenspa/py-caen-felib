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
