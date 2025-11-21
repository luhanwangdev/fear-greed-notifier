"""
VIX Market Signal Monitor
追蹤 VIX 趨勢並判斷進場時機
"""
from datetime import datetime, timedelta
from typing import List, Optional

from ..models import MarketPhase, Signal, VIXData, MarketSignal


class VIXMonitor:
    """VIX 監控器 - 分析 VIX 趨勢並生成進場訊號"""

    def __init__(self, lookback_days: int = 30):
        """
        初始化 VIX 監控器

        Args:
            lookback_days: 保留歷史數據天數
        """
        self.lookback_days = lookback_days
        self.vix_history: List[VIXData] = []

        # VIX 閾值設定
        self.CALM_THRESHOLD = 20
        self.TENSION_THRESHOLD = 25
        self.PANIC_THRESHOLD = 35
        self.EXTREME_PANIC_THRESHOLD = 45

        # 進場訊號閾值
        self.PEAK_DECLINE_30 = 0.30  # 從高點回落30% → ENTRY_30
        self.PEAK_DECLINE_40 = 0.40  # 從高點回落40% → ENTRY_60
        self.PEAK_DECLINE_50 = 0.50  # 從高點回落50% → ENTRY_100
        self.MIN_DECLINING_DAYS = 5  # 最少連續下降天數

    def add_data(self, date: datetime, vix_value: float):
        """
        新增 VIX 數據

        Args:
            date: 數據日期
            vix_value: VIX 值
        """
        # Ensure date is timezone-naive
        if date.tzinfo is not None:
            date = date.replace(tzinfo=None)

        self.vix_history.append(VIXData(date, vix_value))

        # 按日期排序
        self.vix_history.sort(key=lambda x: x.date)

        # 只保留最近N天（基於最新數據的日期，而非系統當前時間）
        if self.vix_history:
            latest_date = self.vix_history[-1].date
            cutoff_date = latest_date - timedelta(days=self.lookback_days)
            self.vix_history = [d for d in self.vix_history if d.date >= cutoff_date]

    def get_current_vix(self) -> Optional[float]:
        """取得最新 VIX 值"""
        if not self.vix_history:
            return None
        return self.vix_history[-1].value

    def get_peak_vix(self, days: int = 30) -> Optional[float]:
        """
        取得指定天數內的 VIX 高點

        Args:
            days: 回溯天數

        Returns:
            VIX 高點值
        """
        if not self.vix_history:
            return None

        recent_data = self.vix_history[-days:] if len(self.vix_history) >= days else self.vix_history
        return max(d.value for d in recent_data)

    def get_declining_days(self) -> int:
        """計算連續下降天數"""
        if len(self.vix_history) < 2:
            return 0

        days = 0
        for i in range(len(self.vix_history) - 1, 0, -1):
            if self.vix_history[i].value < self.vix_history[i-1].value:
                days += 1
            else:
                break
        return days

    def get_rising_days(self) -> int:
        """計算連續上升天數"""
        if len(self.vix_history) < 2:
            return 0

        days = 0
        for i in range(len(self.vix_history) - 1, 0, -1):
            if self.vix_history[i].value > self.vix_history[i-1].value:
                days += 1
            else:
                break
        return days

    def detect_phase(self) -> MarketPhase:
        """
        偵測當前市場階段

        Returns:
            MarketPhase: 市場階段
        """
        current_vix = self.get_current_vix()
        if current_vix is None:
            return MarketPhase.CALM

        peak_vix_10d = self.get_peak_vix(days=10)
        peak_vix_30d = self.get_peak_vix(days=30)
        rising_days = self.get_rising_days()
        declining_days = self.get_declining_days()

        # 恐慌消退：VIX >= 35 且連續下降
        if current_vix >= self.PANIC_THRESHOLD and declining_days >= 3:
            return MarketPhase.PANIC_FALLING

        # 恐慌高峰：VIX 極高且不再上升
        if current_vix >= self.EXTREME_PANIC_THRESHOLD and rising_days == 0:
            return MarketPhase.PANIC_PEAK

        # 恐慌加速：VIX 快速上升
        if current_vix >= self.TENSION_THRESHOLD and rising_days >= 3:
            return MarketPhase.PANIC_RISING

        # 復甦期：VIX < 35 且曾經恐慌過（30天內有超過35的高點）
        # 這包含了從恐慌消退到完全平靜的過渡期
        if current_vix < self.PANIC_THRESHOLD and peak_vix_30d and peak_vix_30d > self.PANIC_THRESHOLD:
            return MarketPhase.RECOVERY

        # 緊張期：VIX 在 25-35 之間但近期沒有恐慌
        if current_vix >= self.TENSION_THRESHOLD:
            return MarketPhase.TENSION

        # 平靜期：VIX < 20 且近期沒有恐慌
        return MarketPhase.CALM

    def generate_signal(self) -> MarketSignal:
        """
        生成進場訊號

        Returns:
            MarketSignal: 市場訊號和建議
        """
        current_vix = self.get_current_vix()
        if current_vix is None:
            return MarketSignal(
                phase=MarketPhase.CALM,
                signal=Signal.STAY_OUT,
                vix_current=0,
                vix_peak=None,
                vix_change_from_peak=None,
                days_declining=0,
                reason="無數據 / No data",
                risk_level="未知 / Unknown"
            )

        phase = self.detect_phase()
        peak_vix = self.get_peak_vix(days=30)
        declining_days = self.get_declining_days()

        # Calculate decline percentage from peak
        change_from_peak = None
        if peak_vix and peak_vix > 0:
            change_from_peak = (peak_vix - current_vix) / peak_vix

        # Determine entry signal
        signal = Signal.STAY_OUT
        reason = ""
        risk_level = "高 / High"

        if phase == MarketPhase.PANIC_FALLING:
            # 50%+ decline → ENTRY_100
            if change_from_peak and change_from_peak >= self.PEAK_DECLINE_50:
                if declining_days >= self.MIN_DECLINING_DAYS:
                    signal = Signal.ENTRY_100
                    reason = f"VIX從高點{peak_vix:.1f}回落{change_from_peak*100:.1f}%，最恐慌已過，可全部進場 / VIX dropped {change_from_peak*100:.1f}% from peak {peak_vix:.1f}, worst panic over, full entry ready"
                    risk_level = "低 / Low"
                else:
                    signal = Signal.ENTRY_60
                    reason = f"VIX回落{change_from_peak*100:.1f}%但僅{declining_days}天，建議先投入60%，確認趨勢後再加碼 / VIX dropped {change_from_peak*100:.1f}% but only {declining_days} days, suggest 60% first"
                    risk_level = "中 / Medium"

            # 40-50% decline → ENTRY_60
            elif change_from_peak and change_from_peak >= self.PEAK_DECLINE_40:
                if declining_days >= self.MIN_DECLINING_DAYS:
                    signal = Signal.ENTRY_60
                    reason = f"VIX從高點{peak_vix:.1f}回落{change_from_peak*100:.1f}%，可投入60% / VIX dropped {change_from_peak*100:.1f}% from peak {peak_vix:.1f}, 60% entry"
                    risk_level = "中 / Medium"
                else:
                    signal = Signal.PREPARE
                    reason = f"VIX回落{change_from_peak*100:.1f}%但僅{declining_days}天，做好準備但確認趨勢 / VIX dropped {change_from_peak*100:.1f}% but only {declining_days} days, prepare and confirm trend"
                    risk_level = "中 / Medium"

            # 30-40% decline → ENTRY_30
            elif change_from_peak and change_from_peak >= self.PEAK_DECLINE_30:
                if declining_days >= self.MIN_DECLINING_DAYS:
                    signal = Signal.ENTRY_30
                    reason = f"VIX從高點{peak_vix:.1f}回落{change_from_peak*100:.1f}%，可小量試單30% / VIX dropped {change_from_peak*100:.1f}% from peak {peak_vix:.1f}, 30% trial entry"
                    risk_level = "中 / Medium"
                else:
                    signal = Signal.WATCH_CLOSELY
                    reason = f"VIX回落{change_from_peak*100:.1f}%但趨勢未確認（僅{declining_days}天） / VIX dropped {change_from_peak*100:.1f}% but trend unconfirmed (only {declining_days} days)"
                    risk_level = "高 / High"
            else:
                signal = Signal.WATCH_CLOSELY
                reason = f"VIX開始下降但回落幅度不足30%（當前{change_from_peak*100:.1f}%） / VIX declining but drop less than 30% (current {change_from_peak*100:.1f}%)"
                risk_level = "高 / High"

        elif phase == MarketPhase.PANIC_PEAK:
            signal = Signal.WATCH_CLOSELY
            reason = f"VIX達到極端水平{current_vix:.1f}，等待回落訊號 / VIX at extreme level {current_vix:.1f}, waiting for decline signal"
            risk_level = "高 / High"

        elif phase == MarketPhase.PANIC_RISING:
            signal = Signal.STAY_OUT
            reason = f"VIX持續上升(連續{self.get_rising_days()}天)，恐慌加劇中 / VIX rising continuously ({self.get_rising_days()} days), panic intensifying"
            risk_level = "極高 / Very High"

        elif phase == MarketPhase.RECOVERY:
            # RECOVERY phase also checks decline percentage
            if change_from_peak and change_from_peak >= self.PEAK_DECLINE_50:
                # 50%+ decline → ENTRY_100 (even if VIX still in 20-35 range)
                signal = Signal.ENTRY_100
                reason = f"VIX從高點{peak_vix:.1f}回落{change_from_peak*100:.1f}%，最恐慌已過 / VIX dropped {change_from_peak*100:.1f}% from peak {peak_vix:.1f}, worst panic over"
                risk_level = "低 / Low"
            elif current_vix < self.CALM_THRESHOLD:
                # VIX < 20 → ENTRY_100
                signal = Signal.ENTRY_100
                reason = f"VIX已回落至{current_vix:.1f}，市場恢復平靜 / VIX declined to {current_vix:.1f}, market calm restored"
                risk_level = "低 / Low"
            else:
                # VIX 20-35 and decline < 50% → ENTRY_60
                signal = Signal.ENTRY_60
                reason = f"VIX持續回落至{current_vix:.1f}，復甦中 / VIX declining to {current_vix:.1f}, recovering"
                risk_level = "中 / Medium"

        elif phase == MarketPhase.TENSION:
            signal = Signal.STAY_OUT
            reason = f"VIX={current_vix:.1f}，市場緊張但未恐慌 / VIX={current_vix:.1f}, market tense but not panic"
            risk_level = "高 / High"

        else:  # CALM
            signal = Signal.NORMAL
            reason = f"VIX={current_vix:.1f}，市場平靜 / VIX={current_vix:.1f}, market calm"
            risk_level = "低 / Low"

        return MarketSignal(
            phase=phase,
            signal=signal,
            vix_current=current_vix,
            vix_peak=peak_vix,
            vix_change_from_peak=change_from_peak,
            days_declining=declining_days,
            reason=reason,
            risk_level=risk_level
        )
