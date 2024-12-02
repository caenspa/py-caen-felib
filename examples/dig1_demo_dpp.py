"""
Python demo for Dig1 digitizers running a DPP firmware.

It has been tested with a DT5740 DPP-QDC, but should be
generic enough to support every digitizers running DPP.
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
    n_analog_traces = int(dig.par.NUMANALOGTRACES.value)
    n_digital_traces = int(dig.par.NUMDIGITALTRACES.value)
    adc_samplrate_msps = float(dig.par.ADC_SAMPLRATE.value)  # in Msps
    adc_n_bits = int(dig.par.ADC_NBIT.value)
    sampling_period_ns = int(1e3 / adc_samplrate_msps)
    fw_type = dig.par.FWTYPE.value

    # Configuration parameters
    reclen_ns = 4096  # in ns
    pretrg_ns = 512  # in ns

    # Configure digitizer
    dig.par.RECLEN.value = f'{reclen_ns}'
    dig.par.TRG_SW_ENABLE.value = 'TRUE'  # Enable software triggers
    dig.par.STARTMODE.value = 'START_MODE_SW'  # Set software start mode
    dig.par.WAVEFORMS.value = 'TRUE'  # Enable waveforms
    for i, ch in enumerate(dig.ch):
        ch.par.CH_ENABLED.value = 'TRUE' if i == 0 else 'FALSE'  # Enable only channel 0
        ch.par.CH_PRETRG.value = f'{pretrg_ns}'

    # Invoke CalibrationADC command at the end of the configuration.
    # This is required by x725, x730 and x751 digitizers, no-op otherwise.
    dig.cmd.CALIBRATEADC()

    # Compute record length in samples
    reclen_ns = int(dig.par.RECLEN.value)  # Read back RECLEN to check if there have been rounding
    reclen = int(reclen_ns / sampling_period_ns)

    # Configure probe types
    analog_probe_1_node = dig.vtrace[0]
    analog_probe_1_node.par.VTRACE_PROBE.value = 'VPROBE_INPUT'
    digital_probe_1_node = dig.vtrace[n_analog_traces + 0]
    digital_probe_1_node.par.VTRACE_PROBE.value = 'VPROBE_TRIGGER'

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
        }
    ]
    decoded_endpoint_path = fw_type.replace('-', '')  # decoded endpoint path is just firmware type without -
    endpoint = dig.endpoint[decoded_endpoint_path]
    data = endpoint.set_read_data_format(data_format)

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

        assert analog_probe_1_type == 1  # 1 -> 'VPROBE_INPUT'
        assert digital_probe_1_type == 26  # 26 -> 'VPROBE_TRIGGER'
        valid_sample_range = np.arange(0, waveform_size, dtype=waveform_size.dtype)
        lines[0].set_data(valid_sample_range, analog_probe_1)
        lines[1].set_data(valid_sample_range, digital_probe_1.astype(np.uint16) * 2000 + 1000)  # scale digital probe to be visible

        ax.title.set_text(f'Channel: {channel} Timestamp: {timestamp} Energy: {energy}')

        figure.canvas.draw()
        figure.canvas.flush_events()

    dig.cmd.DISARMACQUISITION()
