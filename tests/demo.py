import ctypes
import matplotlib.pyplot as plt
import numpy as np

from pyfelib import device

dig = device.Device('dig2://10.105.250.7')

nch_str = dig.get_value('/par/numch')
nch = int(nch_str)

dig.send_command('/cmd/reset')

dig.set_value('/endpoint/par/activeendpoint', 'scope')
dig.set_value('/par/TestPulsePeriod', '1000000')
dig.set_value('/par/TestPulseWidth', '16')
dig.set_value('/par/AcqTriggerSource', 'SwTrg|TestPulse')

ep_scope = dig.endpoints['scope']
ep_scope.set_read_data_format('[{"name":"EVENT_SIZE","type":"SIZE_T"},{"name":"TIMESTAMP","type":"U64"},{"name":"WAVEFORM","type":"U16","dim":2},{"name":"WAVEFORM_SIZE","type":"U64","dim":1}]')

plt.ion()
figure, ax = plt.subplots(figsize=(10, 8))
line1, = ax.plot([], [])
ax.set_ylim(8000, 8200)

def wrap_array_v0(data):
	type = np.ctypeslib.as_ctypes_type(data.dtype)
	return data.ctypes.data_as(ctypes.POINTER(type))

def wrap_array_v1(data):
	return data.ctypes.data_as(ctypes.c_void_p)

def wrap_matrix_v0(data):
	type = np.ctypeslib.as_ctypes_type(data.dtype)
	data_ptr = [i.ctypes.data_as(ctypes.POINTER(type)) for i in data]
	return (ctypes.POINTER(type) * len(data_ptr))(*data_ptr)

def wrap_matrix_v1(data):
	type = np.ctypeslib.as_ctypes_type(data.dtype)
	ptr_gen = (i.ctypes.data_as(ctypes.POINTER(type)) for i in data)
	size = data.shape[0]
	return (ctypes.POINTER(type) * size)(*ptr_gen)

def wrap_matrix_v2(data):
	ptr_gen = (i.ctypes.data for i in data)
	waveform_ptr = np.fromiter(ptr_gen, dtype=np.uintp)
	return waveform_ptr.ctypes.data_as(ctypes.c_void_p)

for i in range(10000000):
	reclen = 4 + i * 4

	dig.set_value('/par/recordlengths', f'{reclen}')

	waveform = [np.empty(reclen, dtype=np.uint16) for i in range(nch)]
	waveform = np.empty([nch, reclen], dtype=np.uint16)
	waveform_arg = wrap_matrix_v2(waveform)

	waveform_size = np.empty(nch, dtype=np.uint64)
	waveform_size_arg = wrap_array_v1(waveform_size)

	event_size = ctypes.c_size_t()
	event_size_arg = ctypes.byref(event_size)

	timestamp = ctypes.c_uint64()
	timestamp_arg = ctypes.byref(timestamp)

	dig.send_command('/cmd/armacquisition')
	dig.send_command('/cmd/swstartacquisition')

	ep_scope.read_data(-1, event_size_arg, timestamp_arg, waveform_arg, waveform_size_arg)

	line1.set_data(range(waveform_size[0]), waveform[0])

	ax.relim()
	ax.autoscale_view(True, True, False)
	figure.canvas.draw()
	figure.canvas.flush_events()

	dig.send_command('/cmd/disarmacquisition')
