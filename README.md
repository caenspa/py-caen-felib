# caen_felib
The official Python wrapper for the CAEN FELib.

## Install
You need to install both the latest version of CAEN FELib and an implementation like the CAEN Dig2 from [the CAEN website](https://www.caen.it/products/caen-felib-library/).

Then, install this module and have fun.

## Examples
Few examples may be found on the official documentation and in the function docstrings.

This example show the simplest way to perform a data acquisition with the scope firmware:

```python
import numpy as np
from matplotlib import pyplot as plt

from caen_felib import device, error

with device.connect('dig2://<host>') as dig:
    # Reset
    dig.cmd.Reset()

    # Read-only parameters
    nch = int(dig.par.NumCh.value)
    adc_nbit = int(dig.par.ADC_NBit.value)

    # Configuration parameters
    reclen = 4096
    dc_offset = 50
    pre_trigger = 128

    # Set some digitizer parameters
    dig.par.AcqTriggerSource.value = 'SwTrg'
    dig.par.RecordLengthS.value = f'{reclen}'
    dig.par.PreTriggerS.value = f'{pre_trigger}'

    # Set some channel parameters
    for ch in dig.ch:
        ch.par.DCOffset.value = f'{dc_offset}'

    # Set enabled endpoint to activate decode
    dig.endpoint.par.ActiveEndpoint.value = 'scope'

    # Configure endpoint
    data_format = [
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

    # Store endpoint node
    ep_scope = dig.endpoint.scope

    # set_read_data_format returns allocated buffers
    data = ep_scope.set_read_data_format(data_format)
    timestamp = data[0].value
    waveform = data[1].value
    waveform_size = data[2].value

    # Configure plot
    plt.ion()
    figure, ax = plt.subplots(figsize=(10, 8))
    lines = []
    for i in range(nch):
        line, = ax.plot([], [])
        lines.append(line)
    ax.set_xlim(0, reclen - 1)
    ax.set_ylim(0, 2 ** adc_nbit - 1)

    # Start acquisition
    dig.cmd.ArmAcquisition()
    dig.cmd.SwStartAcquisition()

    # Acquisition loop
    while True:

        # Send trigger
        dig.cmd.SendSwTrigger()

        # Wait for event
        try:
            dig.endpoint.scope.read_data(100, data)
        except error.Error as ex:
            if ex.code == error.ErrorCode.TIMEOUT:
                # Timeout expired, waiting againg
                continue
            elif ex.code == error.ErrorCode.STOP:
                # End of run, exit the loop
                print('End of run.')
                break
            else:
                # Other critical error, propagate it
                raise ex

        for i in range(nch):
            lines[i].set_data(np.arange(0, waveform_size[i]), waveform[i])

        ax.title.set_text(f'Timestamp: {timestamp}')

        figure.canvas.draw()
        figure.canvas.flush_events()

    # Stop acquisition
    dig.cmd.DisarmAcquisition()
```

## Documentation
Python API is described on the CAEN FELib library documentation, starting from CAEN FELib v1.2.3.

## References
Requirements and documentation can be found at 
https://www.caen.it/products/caen-felib-library/.
