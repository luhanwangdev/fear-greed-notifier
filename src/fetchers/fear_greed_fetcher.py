"""
CNN Fear & Greed Index data fetcher
"""
import aiohttp
from typing import Dict


class FearGreedFetcher:
    """Fetches CNN Fear & Greed Index data"""

    API_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

    @staticmethod
    async def fetch(session: aiohttp.ClientSession) -> Dict:
        """
        Fetch the CNN Fear & Greed Index from their API.

        Args:
            session: aiohttp client session

        Returns:
            dict: Contains 'score', 'rating', 'timestamp'

        Raises:
            aiohttp.ClientError: If the API request fails
            ValueError: If the response format is unexpected
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        async with session.get(
            FearGreedFetcher.API_URL,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            response.raise_for_status()
            data = await response.json()

        if "fear_and_greed" not in data:
            raise ValueError("Unexpected API response format: missing 'fear_and_greed' key")

        fng_data = data["fear_and_greed"]

        score = round(fng_data.get("score", 0))
        rating = fng_data.get("rating", "Unknown")
        timestamp = fng_data.get("timestamp", "")

        return {
            "score": score,
            "rating": rating,
            "timestamp": timestamp
        }
