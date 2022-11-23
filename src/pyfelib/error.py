class FELibError(RuntimeError):
	def __init__(self, message, error):
		super().__init__(message)
		self.error = error
