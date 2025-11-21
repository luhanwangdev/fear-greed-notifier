"""
Discord webhook notifier
"""
import aiohttp
from datetime import datetime, timezone
from typing import Dict, Optional

from ..models import MarketSignal, MarketPhase, Signal


class DiscordNotifier:
    """Sends notifications to Discord via webhook"""

    def __init__(self, webhook_url: str):
        """
        Initialize Discord notifier

        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url

    @staticmethod
    def _get_emoji_for_rating(rating: str) -> str:
        """Get emoji for Fear & Greed rating"""
        rating_lower = rating.lower()

        if "extreme fear" in rating_lower:
            return "😱"
        elif "fear" in rating_lower:
            return "😨"
        elif "neutral" in rating_lower:
            return "😐"
        elif "extreme greed" in rating_lower:
            return "🤑"
        elif "greed" in rating_lower:
            return "😀"
        else:
            return "❓"

    @staticmethod
    def _get_color_for_score(score: int) -> int:
        """Get Discord embed color based on F&G score"""
        if score <= 25:
            return 0xFF0000  # Red - Extreme Fear
        elif score <= 45:
            return 0xFFA500  # Orange - Fear
        elif score <= 55:
            return 0xFFFF00  # Yellow - Neutral
        elif score <= 75:
            return 0x90EE90  # Light Green - Greed
        else:
            return 0x00FF00  # Green - Extreme Greed

    async def send_fear_greed_only(
        self,
        session: aiohttp.ClientSession,
        fng_data: Dict
    ) -> None:
        """
        Send Fear & Greed Index notification only

        Args:
            session: aiohttp client session
            fng_data: Fear & Greed data dict

        Raises:
            aiohttp.ClientError: If webhook request fails
        """
        score = fng_data["score"]
        rating = fng_data["rating"]
        emoji = self._get_emoji_for_rating(rating)
        color = self._get_color_for_score(score)

        now = datetime.now(timezone.utc)
        formatted_time = now.strftime("%Y-%m-%d %H:%M UTC")

        # Progress bar
        filled = int(score / 10)
        empty = 10 - filled
        progress_bar = "🟩" * filled + "⬜" * empty

        embed = {
            "title": f"{emoji} CNN Fear & Greed Index",
            "color": color,
            "description": f"{progress_bar}\n\n0 ← Fear | Greed → 100",
            "fields": [
                {
                    "name": "Score",
                    "value": f"**{score}**",
                    "inline": True
                },
                {
                    "name": "Rating",
                    "value": f"**{rating}**",
                    "inline": True
                }
            ],
            "footer": {
                "text": f"Updated: {formatted_time}"
            },
            "url": "https://www.cnn.com/markets/fear-and-greed"
        }

        payload = {"embeds": [embed]}

        async with session.post(
            self.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            response.raise_for_status()

    async def send_combined_report(
        self,
        session: aiohttp.ClientSession,
        fng_data: Dict,
        market_signal: MarketSignal
    ) -> None:
        """
        Send combined Fear & Greed + VIX Market Signal report

        Args:
            session: aiohttp client session
            fng_data: Fear & Greed data dict
            market_signal: VIX market signal

        Raises:
            aiohttp.ClientError: If webhook request fails
        """
        message = self._format_combined_message(fng_data, market_signal)

        payload = {"content": message}

        async with session.post(
            self.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            response.raise_for_status()

    def _format_combined_message(
        self,
        fng_data: Dict,
        signal: MarketSignal
    ) -> str:
        """Format combined Fear & Greed + VIX message"""

        # Emoji mappings
        phase_emoji = {
            MarketPhase.CALM: "🟢",
            MarketPhase.TENSION: "🟡",
            MarketPhase.PANIC_RISING: "🟠",
            MarketPhase.PANIC_PEAK: "🔴",
            MarketPhase.PANIC_FALLING: "🟡",
            MarketPhase.RECOVERY: "🟢"
        }

        signal_emoji = {
            Signal.STAY_OUT: "⛔",
            Signal.WATCH_CLOSELY: "👀",
            Signal.PREPARE: "⚠️",
            Signal.ENTRY_30: "💰",
            Signal.ENTRY_60: "💰💰",
            Signal.ENTRY_100: "💰💰💰",
            Signal.NORMAL: "✅"
        }

        risk_emoji = {
            "極高": "🔥🔥🔥",
            "高": "🔥🔥",
            "中": "🔥",
            "低": "✅",
            "未知": "❓"
        }

        # Build message
        msg = "**📊 市場綜合報告**\n\n"

        # Fear & Greed Index
        score = fng_data["score"]
        rating = fng_data["rating"]
        fg_emoji = self._get_emoji_for_rating(rating)

        msg += f"**Fear & Greed Index**: {fg_emoji} {score} ({rating})\n\n"

        # VIX Status
        msg += "**VIX 市場訊號**\n"
        msg += f"**當前 VIX**: {signal.vix_current:.2f}\n"
        msg += f"**市場階段**: {phase_emoji.get(signal.phase, '')} {signal.phase.value}\n"
        msg += f"**風險等級**: {risk_emoji.get(signal.risk_level, '')} {signal.risk_level}\n\n"

        # Historical data
        if signal.vix_peak:
            msg += f"**30天高點**: {signal.vix_peak:.2f}\n"
            if signal.vix_change_from_peak:
                msg += f"**從高點回落**: {signal.vix_change_from_peak*100:.1f}%\n"

        if signal.days_declining > 0:
            msg += f"**連續下降天數**: {signal.days_declining}天\n"

        msg += "\n"

        # Entry signal
        msg += f"**進場訊號**: {signal_emoji.get(signal.signal, '')} **{signal.signal.value}**\n"
        msg += f"**判斷依據**: {signal.reason}\n\n"

        # Action recommendations
        msg += "**💡 操作建議**:\n"

        if signal.signal == Signal.STAY_OUT:
            msg += "- ⛔ 保持觀望，不要進場\n"
            msg += "- 等待 VIX 達到 35+ 後開始回落\n"
            msg += "- 準備好標的清單和資金\n"

        elif signal.signal == Signal.WATCH_CLOSELY:
            msg += "- 👀 密切關注 VIX 每日變化\n"
            msg += "- 準備好資金，但還不要動\n"
            msg += "- 等待連續 5 天下降趨勢\n"

        elif signal.signal == Signal.PREPARE:
            msg += "- ⚠️ 做好進場準備\n"
            msg += "- 確認標的股票和買入價格\n"
            msg += "- 再觀察 2-3 天確認下降趨勢\n"

        elif signal.signal == Signal.ENTRY_30:
            msg += "- 💰 可投入 **30% 資金**試單\n"
            msg += "- 建議標的：NVDA、Meta、Google（基本面好的龍頭）\n"
            msg += "- 分散標的，降低風險\n"
            msg += "- 保留 70% 等待 VIX 進一步回落\n"

        elif signal.signal == Signal.ENTRY_60:
            msg += "- 💰💰 可投入 **60% 資金**\n"
            msg += "- 最恐慌階段接近尾聲\n"
            msg += "- 建議分 2-3 天買入（不要一次梭哈）\n"
            msg += "- 保留 40% 等待更好時機\n"

        elif signal.signal == Signal.ENTRY_100:
            # 區分「恐慌後恢復」vs「平常日子」
            if signal.phase == MarketPhase.RECOVERY or (signal.vix_change_from_peak and signal.vix_change_from_peak >= 0.50):
                # 剛從恐慌恢復 - 黃金進場期
                msg += "- 💰💰💰 **黃金進場機會！可投入剩餘全部資金**\n"
                if signal.vix_change_from_peak and signal.vix_change_from_peak >= 0.50:
                    msg += f"- ✅ VIX 已從高點 {signal.vix_peak:.1f} 回落 {signal.vix_change_from_peak*100:.1f}%，最恐慌已過\n"
                else:
                    msg += "- ✅ 市場從恐慌中恢復，波動趨穩\n"
                msg += "- 🎯 建議標的：分散投資於優質成長股和指數\n"
                msg += "- 建議分 2-3 天買完（分批進場）\n"
                msg += "- 保留 10% 現金應急\n"
            elif signal.phase == MarketPhase.CALM:
                # 平常日子 - 正常操作
                msg += "- ✅ **市場正常運作中**\n"
                msg += f"- VIX 維持在低位 {signal.vix_current:.1f}，波動平穩\n"
                msg += "- 可按照原定投資計劃正常操作\n"
                msg += "- 無需特別調整倉位\n"
                msg += "- 持續定期定額或逢低分批買入\n"
            else:
                # 其他情況（保險起見）
                msg += "- 💰💰💰 可投入**剩餘全部資金**\n"
                msg += "- ✅ 市場已恢復穩定\n"
                msg += "- 建議分 2-3 天買完（分批進場）\n"
                msg += "- 保留 10% 現金應急\n"

        elif signal.signal == Signal.NORMAL:
            # 平常日子 - 正常持有
            msg += "- ✅ **市場正常運作中**\n"
            msg += f"- VIX 維持在低位 {signal.vix_current:.1f}，波動平穩\n"
            msg += "- 可按照原定投資計劃正常操作\n"
            msg += "- 無需特別調整倉位\n"
            msg += "- 持續定期定額或逢低分批買入\n"

        msg += "\n"

        # Risk warning
        if signal.risk_level in ["高", "極高"]:
            msg += "⚠️ **風險提醒**: 市場仍不穩定，不建議進場。\n\n"
        elif signal.signal in [Signal.ENTRY_30, Signal.ENTRY_60, Signal.ENTRY_100]:
            msg += "📌 **重要提醒**: 即使訊號出現，也要分批進場。歷史不會完全重複，保持謹慎。\n\n"
        elif signal.signal == Signal.NORMAL:
            msg += "📊 **市場觀察**: 持續關注 VIX 變化，如出現異常波動會及時通知。\n\n"

        now = datetime.now(timezone.utc)
        msg += f"_更新時間: {now.strftime('%Y-%m-%d %H:%M UTC')}_"

        return msg
