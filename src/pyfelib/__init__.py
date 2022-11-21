import ctypes
from sys import platform

try:
	if platform.startswith('win32'):
		lib_name = 'CAEN_FELib.dll'
	elif platform.startswith('linux'):
		lib_name = 'libCAEN_FELib.so'
	elif platform.startswith('darwin'):
		lib_name = 'libCAEN_FELib.dylib'
	_lib = ctypes.cdll.LoadLibrary(lib_name)
except Exception as ex:
	raise Exception(f'module not found: {ex}')

def _last_error():
	last_error = ctypes.create_string_buffer(1024)
	ret = _lib.CAEN_FELib_GetLastError(last_error)
	if ret != 0:
		raise Exception('print_last_error failed')
	return last_error.value.decode()
