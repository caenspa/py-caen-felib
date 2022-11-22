import ctypes
import numpy as np

from pyfelib import device

dig = device.Device('dig2://10.105.250.7')

dig.send_command('/cmd/reset')

dig.set_value('/par/recordlengths', '256')
dig.set_value('/endpoint/par/activeendpoint', 'scope')
dig.set_value('/par/AcqTriggerSource', 'SwTrg')
dig.set_value('/ch/4/par/chenable', 'false')

ep_scope = dig.endpoints['scope']
ep_scope.set_data_format('[{"name":"EVENT_SIZE","type":"SIZE_T"},{"name":"TIMESTAMP","type":"U64"},{"name":"WAVEFORM","type":"U16","dim":2},{"name":"WAVEFORM_SIZE","type":"U64","dim":1}]')

dig.send_command('/cmd/armacquisition')
dig.send_command('/cmd/swstartacquisition')

waveform = [np.empty(100, dtype=np.uint16) for i in range(32)]
waveform_ptr = [i.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16)) for i in waveform]
waveform_arg = (ctypes.POINTER(ctypes.c_uint16) * len(waveform_ptr))(*waveform_ptr)

waveform_size = np.empty(32, dtype=np.uint64)
waveform_size_arg = waveform_size.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))

for i in range(10000000):
	dig.send_command('/cmd/sendswtrigger')

	event_size = ctypes.c_size_t()
	event_size_arg = ctypes.byref(event_size)

	timestamp = ctypes.c_uint64()
	timestamp_arg = ctypes.byref(timestamp)

	ep_scope.read_data(-1, event_size_arg, timestamp_arg, waveform_arg, waveform_size_arg)

	print(timestamp.value, waveform_size[0], waveform[0][:10])

dig.send_command('/cmd/disarmacquisition')
