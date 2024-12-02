"""
Python demo for Dig2 digitizers running a DPP-PSD firmware.
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
address = '192.0.2.1'
#############################

dig2_scheme = 'dig2'
dig2_authority = address
dig2_query = ''
dig2_path = ''
dig2_uri = f'{dig2_scheme}://{dig2_authority}/{dig2_path}?{dig2_query}'

# Connect
with device.connect(dig2_uri) as dig:

    # Reset
    dig.cmd.RESET()

    # Get board info
    adc_samplrate_msps = float(dig.par.ADC_SAMPLRATE.value)  # in Msps
    adc_n_bits = int(dig.par.ADC_NBIT.value)
    sampling_period_ns = int(1e3 / adc_samplrate_msps)
    fw_type = dig.par.FWTYPE.value

    # Configuration parameters
    reclen_ns = 4096  # in ns
    pretrg_ns = 512  # in ns

    # Configure digitizer
    dig.par.GLOBALTRIGGERSOURCE.value = 'SWTRG'  # Enable software triggers
    for i, ch in enumerate(dig.ch):
        ch.par.CHENABLE.value = 'TRUE' if i == 0 else 'FALSE'  # Enable only channel 0
        ch.par.EVENTTRIGGERSOURCE.value = 'GLOBALTRIGGERSOURCE'
        ch.par.WAVETRIGGERSOURCE.value = 'GLOBALTRIGGERSOURCE'
        ch.par.CHRECORDLENGTHT.value = f'{reclen_ns}'
        ch.par.CHPRETRIGGERT.value = f'{pretrg_ns}'
        ch.par.WAVEANALOGPROBE0.value = 'ADCINPUT'
        ch.par.WAVEDIGITALPROBE0.value = 'TRIGGER'

    # Compute record length in samples
    reclen_ns = int(dig.ch[0].par.CHRECORDLENGTHT.value)  # Read back CHRECORDLENGTHT to check if there have been rounding
    reclen = int(reclen_ns / sampling_period_ns)

    # Configure endpoint
    data_format = [
        {
            'name': 'CHANNEL',
            'type': 'U8',
            'dim' : 0,
        },
        {
            'name': 'TIMESTAMP',
            'type': 'U64',
            'dim': 0,
        },
        {
            'name': 'ENERGY',
            'type': 'U16',
            'dim': 0,
        },
        {
            'name': 'ANALOG_PROBE_1',
            'type': 'I16',
            'dim': 1,
            'shape': [reclen],
        },
        {
            'name': 'ANALOG_PROBE_1_TYPE',
            'type': 'I32',
            'dim': 0,
        },
        {
            'name': 'DIGITAL_PROBE_1',
            'type': 'U8',
            'dim': 1,
            'shape': [reclen],
        },
        {
            'name': 'DIGITAL_PROBE_1_TYPE',
            'type': 'I32',
            'dim': 0,
        },
        {
            'name': 'WAVEFORM_SIZE',
            'type': 'SIZE_T',
            'dim': 0,
        },
    ]
    decoded_endpoint_path = 'dpppsd'
    endpoint = dig.endpoint[decoded_endpoint_path]
    data = endpoint.set_read_data_format(data_format)
    dig.endpoint.par.ACTIVEENDPOINT.value = decoded_endpoint_path

    # Get reference to data fields
    channel = data[0].value
    timestamp = data[1].value
    energy = data[2].value
    analog_probe_1 = data[3].value
    analog_probe_1_type = data[4].value  # Integer value described in Supported Endpoints > Probe type meaning
    digital_probe_1 = data[5].value
    digital_probe_1_type = data[6].value  # Integer value described in Supported Endpoints > Probe type meaning
    waveform_size = data[7].value

    # Configure plot
    plt.ion()
    figure, ax = plt.subplots(figsize=(10, 8))
    lines: list[plt.Line2D] = []
    for i in range(2):
        line, = ax.plot([], [], drawstyle='steps-post')
        lines.append(line)
    ax.set_xlim(0, reclen - 1)
    ax.set_ylim(0, 2 ** adc_n_bits - 1)

    # Start acquisition
    dig.cmd.ARMACQUISITION()
    dig.cmd.SWSTARTACQUISITION()

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

        assert analog_probe_1_type == 0  # 0 -> 'adc_input'
        assert digital_probe_1_type == 0  # 0 -> 'trigger'
        valid_sample_range = np.arange(0, waveform_size, dtype=waveform_size.dtype)
        lines[0].set_data(valid_sample_range, analog_probe_1)
        lines[1].set_data(valid_sample_range, digital_probe_1.astype(np.uint16) * 2000 + 1000)  # scale digital probe to be visible

        ax.title.set_text(f'Channel: {channel} Timestamp: {timestamp} Energy: {energy}')

        figure.canvas.draw()
        figure.canvas.flush_events()

    dig.cmd.DISARMACQUISITION()
