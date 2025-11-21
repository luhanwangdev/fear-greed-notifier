#!/usr/bin/env python3
"""
Fear & Greed + VIX Market Signal Notifier
Fetches market indices and sends comprehensive analysis to Discord.
"""
import os
import sys
import asyncio
import aiohttp

from datetime import datetime
from dotenv import load_dotenv, find_dotenv

from .fetchers import FearGreedFetcher, VIXFetcher
from .monitors import VIXMonitor
from .notifiers import DiscordNotifier

load_dotenv(find_dotenv())


async def main() -> int:
    """
    Main function to fetch market data and send to Discord.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Get webhook URL from environment variable
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL environment variable is not set")
        return 1

    try:
        async with aiohttp.ClientSession() as session:
            # Initialize notifier
            notifier = DiscordNotifier(webhook_url)

            # Fetch Fear & Greed Index
            print("Fetching CNN Fear & Greed Index...")
            fng_data = await FearGreedFetcher.fetch(session)
            print(f"Fear & Greed: {fng_data['score']} - {fng_data['rating']}")

            # Fetch VIX data
            print("\nFetching VIX data...")
            try:
                # Get current VIX
                current_vix = VIXFetcher.fetch_current()
                print(f"Current VIX: {current_vix:.2f}")

                # Get historical VIX data
                vix_history = VIXFetcher.fetch_history(days=30)
                print(f"Fetched {len(vix_history)} days of VIX history")

                # Initialize VIX monitor and add historical data
                monitor = VIXMonitor(lookback_days=30)
                for date, value in vix_history:
                    monitor.add_data(date, value)

                # Add current VIX
                monitor.add_data(datetime.now(), current_vix)

                # Generate market signal
                market_signal = monitor.generate_signal()
                print(f"\nMarket Phase: {market_signal.phase.value}")
                print(f"Signal: {market_signal.signal.value}")
                print(f"Risk Level: {market_signal.risk_level}")

                # Send combined report to Discord
                print("\nSending combined report to Discord...")
                await notifier.send_combined_report(session, fng_data, market_signal)
                print("Combined report sent successfully!")

            except Exception as vix_error:
                print(f"Warning: VIX data fetch failed - {vix_error}")
                print("Falling back to Fear & Greed Index only...")

                # Send Fear & Greed only
                await notifier.send_fear_greed_only(session, fng_data)
                print("Fear & Greed notification sent successfully!")

            return 0

    except aiohttp.ClientError as e:
        print(f"Error: Network request failed - {e}")
        return 1
    except ValueError as e:
        print(f"Error: Invalid data - {e}")
        return 1
    except Exception as e:
        print(f"Error: Unexpected error - {e}")
        return 1


def run():
    """CLI entry point"""
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    run()
