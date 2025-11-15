# Polymarket Price Arbitrage & BTC Prediction Trader

An automated trading bot for Polymarket prediction markets that exploits:

1. **Price Arbitrage**: Places trades on both sides when YES + NO < $1
2. **BTC Price Prediction**: Detects mispriced Bitcoin markets based on historical volatility patterns
3. **Counter Trading**: Bets against consistently losing traders to capture behavioral edges

## Features

- Real-time market data fetching from Polymarket
- Price arbitrage detection (YES + NO < $1)
- BTC market mispricing detection using historical data
- Automated order execution on both sides
- Risk management and position sizing
- Dry-run mode for testing

## Strategies

### 1. Price Arbitrage Strategy

Places trades on both sides of markets where the combined price of YES and NO outcomes is less than $1, guaranteeing profit.

### 2. BTC Price Prediction Strategy

Specialized strategy for Bitcoin price prediction markets that:

- Analyzes historical BTC volatility patterns
- Detects when Polymarket prices don't match actual probability distributions
- Exploits short-term market inefficiencies (like the 15-minute windows mentioned in X posts)

### 3. Counter Trading Strategy

Behavioral strategy that profits from the consistent mistakes of losing traders:

- Tracks performance of identified poor-performing traders
- Bets against their positions when they trade
- Exploits persistent biases and poor decision-making patterns

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

## Alpha Opportunities

The bot is designed to capture alpha from:

- Pure arbitrage opportunities (YES + NO < $1)
- Mispriced BTC markets where implied probabilities don't match historical patterns
- Behavioral edges from counter trading consistently losing traders
- Short-term market inefficiencies that get corrected quickly

## Disclaimer

Trading involves significant risk. Use at your own risk. This is for educational purposes. Always test with small amounts first.
