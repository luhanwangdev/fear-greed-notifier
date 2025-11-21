"""
Data models and enums for market signal analysis
"""
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MarketPhase(Enum):
    """市場階段"""
    CALM = "平靜期"
    TENSION = "緊張期"
    PANIC_RISING = "恐慌加速"
    PANIC_PEAK = "恐慌高峰"
    PANIC_FALLING = "恐慌消退"
    RECOVERY = "復甦期"


class Signal(Enum):
    """進場訊號"""
    STAY_OUT = "觀望"
    WATCH_CLOSELY = "密切關注"
    PREPARE = "準備進場"
    ENTRY_30 = "可投入30%"
    ENTRY_60 = "可投入60%"
    ENTRY_100 = "可全部進場"
    NORMAL = "正常持有"


@dataclass
class VIXData:
    """VIX 數據"""
    date: datetime
    value: float


@dataclass
class MarketSignal:
    """市場訊號"""
    phase: MarketPhase
    signal: Signal
    vix_current: float
    vix_peak: Optional[float]
    vix_change_from_peak: Optional[float]
    days_declining: int
    reason: str
    risk_level: str  # "低", "中", "高", "極高"
