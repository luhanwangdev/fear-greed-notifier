"""
VIX data fetcher using Yahoo Finance
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Tuple


class VIXFetcher:
    """Fetches VIX data from Yahoo Finance"""

    SYMBOL = "^VIX"

    @staticmethod
    def fetch_current() -> float:
        """
        Fetch the current VIX value

        Returns:
            float: Current VIX value

        Raises:
            Exception: If data fetch fails
        """
        vix = yf.Ticker(VIXFetcher.SYMBOL)
        data = vix.history(period="1d")

        if data.empty:
            raise Exception("Failed to fetch VIX data")

        return float(data['Close'].iloc[-1])

    @staticmethod
    def fetch_history(days: int = 30) -> List[Tuple[datetime, float]]:
        """
        Fetch historical VIX data

        Args:
            days: Number of days of historical data to fetch

        Returns:
            List of (date, vix_value) tuples

        Raises:
            Exception: If data fetch fails
        """
        vix = yf.Ticker(VIXFetcher.SYMBOL)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        data = vix.history(start=start_date, end=end_date)

        if data.empty:
            raise Exception("Failed to fetch VIX historical data")

        history = []
        for date, row in data.iterrows():
            # Convert pandas Timestamp to datetime and remove timezone
            dt = date.to_pydatetime()
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            value = float(row['Close'])
            history.append((dt, value))

        return history
