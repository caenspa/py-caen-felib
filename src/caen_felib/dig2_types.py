"""
@ingroup Python
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

from enum import Flag, IntEnum, unique


@unique
class DppAnalogProbeType(IntEnum):
    """
    Analog probe types for Dig2 DPP-PSD and DPP-PHA events
    """
    UNKNOWN                         = 0xff
    # Common
    ADC_INPUT                       = 0b0000
    # PHA specific
    TIME_FILTER                     = 0b0001
    ENERGY_FILTER                   = 0b0010
    ENERGY_FILTER_BASELINE          = 0b0011
    ENERGY_FILTER_MINUS_BASELINE    = 0b0100
    # PSD specific
    BASELINE                        = 0b1001
    CFD                             = 0b1010


@unique
class DppDigitalProbeType(IntEnum):
    """
    Digital probe types for Dig2 DPP-PSD and DPP-PHA events
    """
    UNKNOWN                         = 0xff
    # Common
    TRIGGER                         = 0b00000
    TIME_FILTER_ARMED               = 0b00001
    RE_TRIGGER_GUARD                = 0b00010
    ENERGY_FILTER_BASELINE_FREEZE   = 0b00011
    EVENT_PILE_UP                   = 0b00111
    # PHA specific
    ENERGY_FILTER_PEAKING           = 0b00100
    ENERGY_FILTER_PEAK_READY        = 0b00101
    ENERGY_FILTER_PILE_UP_GUARD     = 0b00110
    ADC_SATURATION                  = 0b01000
    ADC_SATURATION_PROTECTION       = 0b01001
    POST_SATURATION_EVENT           = 0b01010
    ENERGY_FILTER_SATURATION        = 0b01011
    SIGNAL_INHIBIT                  = 0b01100
    # PSD specific
    OVER_THRESHOLD                  = 0b10100
    CHARGE_READY                    = 0b10101
    LONG_GATE                       = 0b10110
    SHORT_GATE                      = 0b11000
    INPUT_SATURATION                = 0b11001
    CHARGE_OVER_RANGE               = 0b11010
    NEGATIVE_OVER_THRESHOLD         = 0b11011


class HighPriorityFlagsPha(Flag):
    """
    High priority flags on Dig2 DPP-PHA events
    """
    PILE_UP                 = 0x01
    PILE_UP_REJECTOR_GUARD  = 0x02
    EVENT_SATURATION        = 0x04
    POST_SATURATION         = 0x08
    TRAPEZOID_SATURATION    = 0x10
    SCA_SELECTED            = 0x20


class HighPriorityFlagsPsd(Flag):
    """
    High priority flags on Dig2 DPP-PSD events
    """
    PILE_UP                 = 0x01
    EVENT_SATURATION        = 0x04
    POST_SATURATION         = 0x08
    CHARGE_OVERFLOW         = 0x10
    SCA_SELECTED            = 0x20
    FINE_TIMESTAMP          = 0x40


class LowPriorityFlags(Flag):
    """
    Low priority flags on Dig2 DPP-PHA and DPP-PSD events
    """
    WAVE_ON_EXT_INHIBIT     = 0x001
    WAVE_UNDER_SATURATION   = 0x002
    WAVE_OVER_SATURATION    = 0x004
    EXTERNAL_TRIGGER        = 0x008
    GLOBAL_TRIGGER          = 0x010
    SOFTWARE_TRIGGER        = 0x020
    SELF_TRIGGER            = 0x040
    LVDS_TRIGGER            = 0x080
    CH64_TRIGGER            = 0x100
    ITLA_TRIGGER            = 0x200
    ITLB_TRIGGER            = 0x400
