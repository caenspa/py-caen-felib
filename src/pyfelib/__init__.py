import ctypes
from sys import platform

# Import library
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

def last_error():
	value = ctypes.create_string_buffer(1024)
	ret = _lib.CAEN_FELib_GetLastError(value)
	if ret != 0:
		raise Exception('print_last_error failed')
	return value.value.decode()

def lib_version():
	value = ctypes.create_string_buffer(16)
	ret = _lib.CAEN_FELib_GetLibVersion(value)
	if ret != 0:
		raise Exception('print_last_error failed')
	return value.value.decode()
