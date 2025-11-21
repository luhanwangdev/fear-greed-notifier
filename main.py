#!/usr/bin/env python3
"""
Entry point for Fear & Greed + VIX Market Signal Notifier
"""
import sys
from src.main import main
import asyncio

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
