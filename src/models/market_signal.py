"""
Data models and enums for market signal analysis
"""
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MarketPhase(Enum):
    """Market Phase / 市場階段"""
    CALM = "平靜期 / Calm"
    TENSION = "緊張期 / Tension"
    PANIC_RISING = "恐慌加速 / Panic Rising"
    PANIC_PEAK = "恐慌高峰 / Panic Peak"
    PANIC_FALLING = "恐慌消退 / Panic Falling"
    RECOVERY = "復甦期 / Recovery"


class Signal(Enum):
    """Entry Signal / 進場訊號"""
    STAY_OUT = "觀望 / Stay Out"
    WATCH_CLOSELY = "密切關注 / Watch Closely"
    PREPARE = "準備進場 / Prepare"
    ENTRY_30 = "可投入30% / Deploy 30%"
    ENTRY_60 = "可投入60% / Deploy 60%"
    ENTRY_100 = "可全部進場 / Full Entry"
    NORMAL = "正常持有 / Normal"


@dataclass
class VIXData:
    """VIX Data / VIX 數據"""
    date: datetime
    value: float


@dataclass
class MarketSignal:
    """Market Signal / 市場訊號"""
    phase: MarketPhase
    signal: Signal
    vix_current: float
    vix_peak: Optional[float]
    vix_change_from_peak: Optional[float]
    days_declining: int
    reason: str
    risk_level: str  # "低 / Low", "中 / Medium", "高 / High", "極高 / Very High"
