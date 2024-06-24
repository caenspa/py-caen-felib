"""
@ingroup Python
"""

__author__ = 'Giovanni Cerretani'
__copyright__ = 'Copyright (C) 2024 CAEN SpA'
__license__ = 'LGPL-3.0-or-later'
# SPDX-License-Identifier: LGPL-3.0-or-later

from enum import Flag, IntEnum, unique


@unique
class DppProbeType(IntEnum):
    """
    Probe types for Dig1 DPP events
    """
    INVALID         = -1
    NONE            = 0
    INPUT           = 1
    DELTA           = 2
    DELTA2          = 3
    TRAPEZOID       = 4
    BASELINE        = 5
    THRESHOLD       = 6
    CFD             = 7
    TRAPCORRECTED   = 8
    RTDISCWID       = 9
    ARMED           = 10
    PKRUN           = 11
    PEAKING         = 12
    TRGVALWIN       = 13
    BLHOLDOFF       = 14
    TRGHOLDOFF      = 15
    TRGVAL          = 16
    ACQVETO         = 17
    BFMVETO         = 18
    EXTTRG          = 19
    OVERTHRESHOLD   = 20
    TRGOUT          = 21
    COINCIDENCE     = 22
    PILEUP          = 23
    GATE            = 24
    GATESHORT       = 25
    TRIGGER         = 26
    BUSY            = 27
    PILEUPTRIG      = 28
    ISNEUTRON       = 29
    TRIGGER_ACCEPT  = 30
    TRGWIN          = 31
    COINCWIN        = 32
    FAST_TRIANG     = 33
    SLOW_TRIANG     = 34
    BSL_FREEZE      = 35
    INHIBIT_FLAG    = 36
    PEAK_READY      = 37
    ARMED_ST        = 38
    GATE_INH        = 39
    TEST_WAVE       = 40
    SMOOTHINPUT     = 41
    ADCSAT          = 42
    ADCSAT_PROTECT  = 43
    POSTSAT         = 44
    ENERGYSAT       = 45
    PILEUPGUARD     = 46
    CRG_READY       = 47
    CHARGESAT       = 48
    NEG_OVERTHR     = 49
    TRAPBASELINE    = 50

class HighPriorityFlagsPsd(Flag):
    """
    Flags on Dig1 DPP events
    """
    DEADTIME    = 0x0000001  # Identifies the first event after a dead time.
    TTROLLOVER  = 0x0000002  # Identifies a trigger time stamp roll-over that occurred before this event.
    TTRESET     = 0x0000004  # Identifies a trigger time stamp reset forced from external signals in S-IN (GPI for Desktop).
    EVTFAKE     = 0x0000008  # Identifies a fake event (which does not correspond to any physical event).
    MEMFULL     = 0x0000010  # Reading memory full.
    TRGLOST     = 0x0000020  # Identifies the first event after a trigger lost.
    NTRGLOST    = 0x0000040  # Every N lost events this flag is high (see board documentation to set N).
    OVERRNG     = 0x0000080  # Energy overranged.
    F1024TRG    = 0x0000100  # 1024 triggers counted (every 1024 counted events this flag is high).
    LOSTEVT     = 0x0000200  # Identifies the first event after when one or more events is lost due to a memory board FULL. The memory can be FULL due to a write event.
    INPUTSAT    = 0x0000400  # Identifies an event saturating the input dynamics (clipping).
    NTRGTOT     = 0x0000800  # Every N total events this flag is high (see board documentation to set N).
    OLDSORT     = 0x0001000  # Identifies an event not sorted but sent for waveform.
    EOR         = 0x0002000  # Identifies a fake event occurring at the end of run.
    FINETT      = 0x0004000  # Identifies an event with fine time stamp.
    PILEUP      = 0x0008000  # Identifies a pile up event.
    TIMEVALUE   = 0x0010000  # Identifies a fake event occurring on a time stamp roll-over.
    ENERGY_SKIM = 0x0020000  # Energy skimming.
    SATREJ      = 0x0040000  # Identifies an event occurred when detector was inibited due to saturation.
    PLLLOCKLOSS = 0x0080000  # Identifies a fake event sent to report a PLL lock loss.
    OVERTEMP    = 0x0100000  # Identifies a fake event sent to report an over temperature condition.
    SHUTDOWN    = 0x0200000  # Identifies a fake event sent to report an ADC shutdown.
    MEMORYSORT  = 0x0400000  # Identifies a fake event sent to report a memory overload during data sorting.
    MCS         = 0x0800000  # Identifies a MCS event
    STOPCOND    = 0x1000000  # Identifies the first event after a stop condition has been met.
