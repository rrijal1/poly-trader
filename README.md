# Polymarket Price Arbitrage Trader

An automated trading bot for Polymarket prediction markets that exploits price arbitrage opportunities where the sum of YES and NO prices is less than $1.

## Features

- Real-time market data fetching from Polymarket
- Price arbitrage detection (YES + NO < $1)
- Automated order execution on both sides
- Risk management and position sizing
- Dry-run mode for testing

## Strategy

The bot monitors prediction markets and places orders on both YES and NO outcomes when their combined price is below $1, profiting from the arbitrage opportunity.

## Setup

1. Clone the repository
2. Create virtual environment: `python -m venv poly`
3. Activate: `source poly/bin/activate` (macOS/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your Polymarket API credentials and wallet private key
6. Run the bot: `python -m src.main live --dry-run` (for testing)

## Configuration

- Set your Polygon wallet private key in `.env`
- Configure Polymarket API credentials
- Strategy parameters are configured in `src/main.py`

## Usage

```bash
# Dry run (recommended first)
python -m src.main live --dry-run

# Live trading (use with caution)
python -m src.main live
```

## Disclaimer

Trading involves significant risk. Use at your own risk. This is for educational purposes. Always test with small amounts first.
