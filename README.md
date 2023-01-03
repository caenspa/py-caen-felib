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

from caen_felib import device

with device.connect("dig2://<host>") as dig:
    # Reset
    dig.cmd.Reset()

    # Set some digitizer parameters
    dig.par.AcqTriggerSource.value = 'SwTrg'
    dig.par.RecordLengthS.value = f'{4096}'
    dig.par.PreTriggerS.value = f'{128}'

    # Set some channel parameters
    for ch in dig.ch:
        ch.par.DCOffset.value = f'{50}'

    # Set enabled endpoint to activate decode
    dig.endpoint.par.ActiveEndpoint.value = 'scope'

    # Configure endpoint
    nch = int(dig.par.NumCh.value)
    reclen = int(dig.par.RecordLengthS.value)

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

    # set_read_data_format returns allocated buffers
    data = dig.endpoint.scope.set_read_data_format(data_format)
    timestamp = data[0].value
    waveform = data[1].value
    waveform_size = data[2].value

    # Start acquisition
    dig.cmd.ArmAcquisition()
    dig.cmd.SwStartAcquisition()

    # Send trigger and wait for first event
    dig.cmd.SendSwTrigger()
    dig.endpoint.scope.read_data(-1, data)

    # Stop acquisition
    dig.cmd.DisarmAcquisiton()

    # Plot waveforms
    for i in range(nch):
        size = waveform_size[i]
        plt.plot(np.arange(size), waveform[i][:size])
    plt.title(f'Timestamp: {timestamp}')
    plt.show()
```

## Documentation
Python API is described on the CAEN FELib library documentation, starting from CAEN FELib v1.2.3.

## References
Requirements and documentation can be found at 
https://www.caen.it/products/caen-felib-library/.
