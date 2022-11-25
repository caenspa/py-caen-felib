import ctypes
import json
import sys

import matplotlib.pyplot as plt
import numpy as np

from caen_felib import lib, device, error

# Utilities
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

print(f'CAEN FELib wrapper loaded (lib version {lib.version})')

# Connect
dig = device.Device('dig2://10.105.250.7')

# Get device tree
device_tree = dig.get_device_tree()

# Get board info
nch = int(device_tree['par']['numch']['value'])

# Reset
dig.send_command('/cmd/reset')

# Configure digitizer
reclen = 4000

dig.set_value('/par/TestPulsePeriod', '1000000000')
dig.set_value('/par/TestPulseWidth', '16')
dig.set_value('/par/AcqTriggerSource', 'ITLA|TestPulse')
dig.set_value('/par/RecordLengthS', f'{reclen}')
dig.set_value('/par/PreTriggerS', '1000')

dig.set_value('/ch/0/par/ITLConnect', 'ITLA')
dig.set_value('/ch/0/par/DCOffset', '50')
dig.set_value('/ch/0/par/TriggerThr', '9000')
dig.set_value('/ch/0/par/TriggerThrMode', 'Absolute')
dig.set_value('/ch/0/par/SelfTriggerEdge', 'Fall')

dig.set_value('/ch/1/par/DCOffset', '20')

dig.set_value('/endpoint/par/activeendpoint', 'scope')
ep_scope = dig.endpoints['scope']

data_format = [
	{
		'name': 'EVENT_SIZE',
		'type': 'SIZE_T',
	},
	{
		'name': 'TIMESTAMP',
		'type': 'U64',
	},
	{
		'name': 'WAVEFORM',
		'type': 'U16',
		'dim': 2,
	},
	{
		'name': 'WAVEFORM_SIZE',
		'type': 'U64',
		'dim': 1,
	},
]

ep_scope.set_read_data_format(data_format)

# Configure plot
plt.ion()
figure, ax = plt.subplots(figsize=(10, 8))
line0, = ax.plot([], [])
line1, = ax.plot([], [])
ax.set_ylim(0, 2 ** 14 - 1)

# Initialize data
waveform = np.empty([nch, reclen], dtype=np.uint16)
waveform_arg = wrap_matrix_v2(waveform)

waveform_size = np.empty(nch, dtype=np.uint64)
waveform_size_arg = wrap_array_v1(waveform_size)

event_size = ctypes.c_size_t()
event_size_arg = ctypes.byref(event_size)

timestamp = ctypes.c_uint64()
timestamp_arg = ctypes.byref(timestamp)

# Start acquisition
dig.send_command('/cmd/armacquisition')
dig.send_command('/cmd/swstartacquisition')

while True:

	try:
		ep_scope.read_data(-1, event_size_arg, timestamp_arg, waveform_arg, waveform_size_arg)
	except error.FELibTimeout as ex:
		print('timeout')
		continue
	except error.FELibStop as ex:
		print('stop')
		break

	line0.set_data(range(waveform_size[0]), waveform[0])
	line1.set_data(range(waveform_size[1]), waveform[1])

	ax.relim()
	ax.autoscale_view(True, True, False)
	figure.canvas.draw()
	figure.canvas.flush_events()

dig.send_command('/cmd/disarmacquisition')
