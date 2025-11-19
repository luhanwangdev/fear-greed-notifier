#!/usr/bin/env python3
"""
CNN Fear & Greed Index Notifier
Fetches the current Fear & Greed Index and sends it to Discord.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

import aiohttp


async def get_fear_greed_index(session: aiohttp.ClientSession) -> dict:
    """
    Fetch the CNN Fear & Greed Index from their API.

    Returns:
        dict: Contains 'score', 'rating', 'timestamp'

    Raises:
        aiohttp.ClientError: If the API request fails
        ValueError: If the response format is unexpected
    """
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
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


def get_emoji_for_rating(rating: str) -> str:
    """Get an appropriate emoji for the fear/greed rating."""
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


def get_color_for_score(score: int) -> int:
    """Get Discord embed color based on score (0-100)."""
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


async def send_discord_notification(session: aiohttp.ClientSession, webhook_url: str, fng_data: dict) -> None:
    """
    Send Fear & Greed Index data to Discord via webhook.

    Args:
        session: aiohttp client session
        webhook_url: Discord webhook URL
        fng_data: Dictionary containing score, rating, and timestamp

    Raises:
        aiohttp.ClientError: If the webhook request fails
    """
    score = fng_data["score"]
    rating = fng_data["rating"]
    emoji = get_emoji_for_rating(rating)
    color = get_color_for_score(score)

    # Format timestamp
    now = datetime.now(timezone.utc)
    formatted_time = now.strftime("%Y-%m-%d %H:%M UTC")

    embed = {
        "title": f"{emoji} CNN Fear & Greed Index",
        "color": color,
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

    # Add a progress bar visualization
    filled = int(score / 10)
    empty = 10 - filled
    progress_bar = "🟩" * filled + "⬜" * empty

    embed["description"] = f"{progress_bar}\n\n0 ← Fear | Greed → 100"

    payload = {
        "embeds": [embed]
    }

    async with session.post(
        webhook_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=aiohttp.ClientTimeout(total=30)
    ) as response:
        response.raise_for_status()


async def main() -> int:
    """
    Main function to fetch Fear & Greed Index and send to Discord.

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
            # Fetch Fear & Greed Index
            print("Fetching CNN Fear & Greed Index...")
            fng_data = await get_fear_greed_index(session)

            print(f"Score: {fng_data['score']} - {fng_data['rating']}")

            # Send to Discord
            print("Sending notification to Discord...")
            await send_discord_notification(session, webhook_url, fng_data)

            print("Notification sent successfully!")
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


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
