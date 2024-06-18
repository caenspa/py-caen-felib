import matplotlib.pyplot as plt
import numpy as np

from caen_felib import lib, device, error

print(f'CAEN FELib binding loaded (lib version {lib.version})')

# Connect
dig = device.connect('dig2://10.105.250.7')

# Reset
dig.cmd.reset()

# Get board info
nch = int(dig.par.numch.value)

# Configure digitizer
reclen = 4096

dig.set_value('/par/TestPulsePeriod', '1000000000')
dig.set_value('/par/TestPulseWidth', '16')
dig.set_value('/par/AcqTriggerSource', 'TestPulse|ITLA')
dig.set_value('/par/RecordLengthS', f'{reclen}')
dig.set_value('/par/PreTriggerS', '128')

dig.set_value('/ch/0/par/SamplesOverThreshold', '16')
dig.set_value('/ch/0/par/ITLConnect', 'ITLA')
dig.set_value('/ch/0/par/TriggerThr', '8000')
dig.set_value('/ch/0/par/TriggerThrMode', 'Absolute')
dig.set_value('/ch/0/par/SelfTriggerEdge', 'Fall')

for i in range(nch):
	dig.set_value(f'/ch/{i}/par/DCOffset', f'{50 + i}')
	dig.set_value(f'/ch/{i}/par/WaveDataSource', 'adc_data')

dig.set_value('/endpoint/par/activeendpoint', 'scope')
ep_scope = dig.get_node('/endpoint/scope')

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
		'shape': [nch, reclen],
	},
	{
		'name': 'WAVEFORM_SIZE',
		'type': 'U64',
		'dim': 1,
		'shape': [nch],
	},
]

data = ep_scope.set_read_data_format(data_format)

# Configure plot
plt.ion()
figure, ax = plt.subplots(figsize=(10, 8))
lines = []
for i in range(4):
	line, = ax.plot([], [])
	lines.append(line)
ax.set_xlim(0, reclen - 1)
ax.set_ylim(0, 2 ** 14 - 1)

# Initialize data
event_size = data[0].value
timestamp = data[1].value
waveform = data[2].value
waveform_size = data[3].value

# Start acquisition
dig.send_command('/cmd/armacquisition')
dig.send_command('/cmd/swstartacquisition')

while True:

	try:
		ep_scope.read_data(100, data)
	except error.Error as ex:
		if ex.code == error.ErrorCode.TIMEOUT:
			continue
		elif ex.code == error.ErrorCode.STOP:
			print('stop')
			break
		else:
			raise ex

	for i in range(4):
		lines[i].set_data(np.arange(0, waveform_size[i]), waveform[i])

	ax.title.set_text(f'Timestamp: {timestamp}')

	figure.canvas.draw()
	figure.canvas.flush_events()

dig.send_command('/cmd/disarmacquisition')
