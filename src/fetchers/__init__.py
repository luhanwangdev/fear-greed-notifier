"""
Data fetchers for market indices
"""
from .fear_greed_fetcher import FearGreedFetcher
from .vix_fetcher import VIXFetcher

__all__ = ["FearGreedFetcher", "VIXFetcher"]
