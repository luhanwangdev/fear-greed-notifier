# Fear & Greed Index Notifier

Automatically fetches the CNN Fear & Greed Index and sends notifications to Discord.

## Features

- Fetches the latest Fear & Greed Index data from CNN API
- Sends beautiful Discord Embed notifications with:
  - Score and rating
  - Visual progress bar
  - Color-coded based on score
  - Emoji matching the sentiment
- Scheduled execution via GitHub Actions (9:00 AM and 9:00 PM Taiwan Time)

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Local Installation

```bash
# Install dependencies
uv sync

# Run
uv run python main.py
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL |

### Local Execution

Create a `.env` file:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### GitHub Actions

Add the following secret in Repository Settings > Secrets and variables > Actions:

- `DISCORD_WEBHOOK_URL`: Your Discord Webhook URL

## Schedule

GitHub Actions is configured to run automatically at:

- UTC 01:00 (Taiwan Time 09:00)
- UTC 13:00 (Taiwan Time 21:00)

You can also trigger it manually from the GitHub Actions page.

## Fear & Greed Index Ratings

| Score Range | Rating | Color |
|-------------|--------|-------|
| 0-25 | Extreme Fear | Red |
| 26-45 | Fear | Orange |
| 46-55 | Neutral | Yellow |
| 56-75 | Greed | Light Green |
| 76-100 | Extreme Greed | Green |

## License

MIT License
