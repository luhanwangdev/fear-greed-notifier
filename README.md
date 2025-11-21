# Fear & Greed + VIX Market Signal Notifier

Comprehensive market analysis tool that combines CNN Fear & Greed Index with VIX volatility analysis to provide actionable trading signals.

## Features

### Fear & Greed Index
- Fetches the latest Fear & Greed Index data from CNN API
- Visual sentiment indicators with color-coded ratings

### VIX Market Signal Analysis
- Real-time VIX (Volatility Index) tracking
- 30-day historical trend analysis
- Intelligent market phase detection:
  - 平靜期 (Calm)
  - 緊張期 (Tension)
  - 恐慌加速 (Panic Rising)
  - 恐慌高峰 (Panic Peak)
  - 恐慌消退 (Panic Falling)
  - 復甦期 (Recovery)
- Smart entry signals with position sizing recommendations (30%/60%/100%)
- Risk level assessment
- Actionable trading recommendations

### Notifications
- Sends comprehensive market reports to Discord
- Scheduled execution via GitHub Actions (10:27 AM and 10:27 PM Taiwan Time)
- Fallback to Fear & Greed only if VIX data unavailable

## Project Structure

```
fear-greed-notifier/
├── src/
│   ├── fetchers/          # Data fetching modules
│   │   ├── fear_greed_fetcher.py  # CNN F&G API
│   │   └── vix_fetcher.py         # Yahoo Finance VIX
│   ├── monitors/          # Signal analysis
│   │   └── vix_monitor.py         # VIX trend analyzer
│   ├── notifiers/         # Notification services
│   │   └── discord_notifier.py    # Discord webhook
│   ├── models/            # Data models
│   │   └── market_signal.py       # Enums & dataclasses
│   └── main.py            # Main application logic
├── main.py                # Entry point wrapper
├── pyproject.toml         # Dependencies
└── .env                   # Environment variables
```

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

- UTC 02:27 (Taiwan Time 10:27)
- UTC 14:27 (Taiwan Time 22:27)

You can also trigger it manually from the GitHub Actions page.

## How It Works

### VIX Signal Logic (Plan B)

The VIX monitor analyzes volatility trends and generates entry signals based on:

1. **Market Phase Detection**
   - Monitors VIX levels and trend direction
   - Identifies panic peaks and recovery periods

2. **Entry Signals**
   - **ENTRY_30**: VIX declined 30%+ from peak → Invest 30%
   - **ENTRY_60**: VIX declined 40%+ from peak → Invest 60%
   - **ENTRY_100**: VIX declined 50%+ from peak → Invest remaining 100%

3. **Risk Assessment**
   - Tracks consecutive declining days (minimum 5 days for confirmation)
   - Provides risk levels: 極高/高/中/低

### Fear & Greed Index Ratings

| Score Range | Rating | Color |
|-------------|--------|-------|
| 0-25 | Extreme Fear | Red |
| 26-45 | Fear | Orange |
| 46-55 | Neutral | Yellow |
| 56-75 | Greed | Light Green |
| 76-100 | Extreme Greed | Green |

## Backtesting

The VIX signal logic was backtested against the April 2025 tariff crisis:
- **4/4**: VIX peak at 60.1 (Panic Peak)
- **4/11**: ENTRY_60 signal (VIX 31.9, -47% from peak)
- **4/14**: ENTRY_100 signal (VIX 28.5, -52% from peak)
- **Result**: Market turned positive by 5/13, new highs by 6/27 🚀

## License

MIT License
