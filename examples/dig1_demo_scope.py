"""
Python demo for Dig1 digitizers running a Waveform recording firmware.

It has been tested with a DT5740 Waveform recording, but should be
generic enough to support every digitizers running Waveform recording.
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2023 CAEN SpA'
__license__ = 'MIT-0'  # SPDX-License-Identifier
__contact__ = 'https://www.caen.it/'

import matplotlib.pyplot as plt
import numpy as np

# To install the module: pip install caen-felib
from caen_felib import lib, device, error

print(f'CAEN FELib wrapper loaded (lib version {lib.version})')

### CONNECTION PARAMETERS ###
connection_type = 'usb'
link_number = 0
conet_node = 0
vme_base_address = 0
#############################

dig1_scheme = 'dig1'
dig1_authority = 'caen.internal'
dig1_query = f'link_num={link_number}&conet_node={conet_node}&vme_base_address={vme_base_address}'
dig1_path = connection_type
dig1_uri = f'{dig1_scheme}://{dig1_authority}/{dig1_path}?{dig1_query}'

# Connect
with device.connect(dig1_uri) as dig:

    # Reset
    dig.cmd.RESET()

    # Get board info
    n_ch = int(dig.par.NUMCH.value)
    n_analog_traces = int(dig.par.NUMANALOGTRACES.value)
    n_digital_traces = int(dig.par.NUMDIGITALTRACES.value)
    adc_samplrate_msps = float(dig.par.ADC_SAMPLRATE.value)  # in Msps
    adc_n_bits = int(dig.par.ADC_NBIT.value)
    sampling_period_ns = int(1e3 / adc_samplrate_msps)
    fw_type = dig.par.FWTYPE.value

    # Configuration parameters
    reclen_ns = 4096  # in ns
    posttrg_ns = 4096 - 512  # in ns

    # Configure digitizer
    dig.par.RECLEN.value = f'{reclen_ns}'
    dig.par.POSTTRG.value = f'{posttrg_ns}'
    dig.par.TRG_SW_ENABLE.value = 'TRUE'  # Enable software triggers
    dig.par.STARTMODE.value = 'START_MODE_SW'  # Set software start mode

    # Invoke CalibrationADC command at the end of the configuration.
    # This is required by x725, x730 and x751 digitizers, no-op otherwise.
    dig.cmd.CALIBRATEADC()

    # Compute record length in samples
    reclen_ns = int(dig.par.RECLEN.value)  # Read back RECLEN to check if there have been rounding
    reclen = int(reclen_ns / sampling_period_ns)

    # Configure endpoint
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
            'shape': [n_ch, reclen],
        },
        {
            'name': 'WAVEFORM_SIZE',
            'type': 'U64',
            'dim': 1,
            'shape': [n_ch],
        },
    ]
    decoded_endpoint_path = fw_type.replace('-', '')  # decoded endpoint path is just firmware type without -
    endpoint = dig.endpoint[decoded_endpoint_path]
    data = endpoint.set_read_data_format(data_format)

    # Get reference to data fields
    event_size = data[0].value
    timestamp = data[1].value
    waveform = data[2].value
    waveform_size = data[3].value

    # Configure plot
    plt.ion()
    figure, ax = plt.subplots(figsize=(10, 8))
    lines: list[plt.Line2D] = []
    for i in range(n_ch):
        line, = ax.plot([], [], drawstyle='steps-post')
        lines.append(line)
    ax.set_xlim(0, reclen - 1)
    ax.set_ylim(0, 2 ** adc_n_bits - 1)

    # Start acquisition
    dig.cmd.ARMACQUISITION()

    # Read some events
    for _ in range(1000):
        # Send software trigger
        dig.cmd.SENDSWTRIGGER()

        try:
            endpoint.read_data(100, data)
        except error.Error as ex:
            if ex.code is error.ErrorCode.TIMEOUT:
                continue
            if ex.code is error.ErrorCode.STOP:
                break
            raise ex

        # Plot first 4 channels
        for i in range(n_ch):
            valid_sample_range = np.arange(0, waveform_size[i], dtype=waveform_size[i].dtype)
            lines[i].set_data(valid_sample_range, waveform[i])

        ax.title.set_text(f'Timestamp: {timestamp}')

        figure.canvas.draw()
        figure.canvas.flush_events()

    dig.cmd.DISARMACQUISITION()
