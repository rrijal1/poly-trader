# BTC Price Prediction Strategy

This folder contains the standalone BTC Price Prediction Strategy for Railway deployment.

## Railway Deployment

1. **Connect Repository**: Point Railway to this specific folder (`strategy_btc_price_prediction`)
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python main.py`
4. **Environment Variables**:
   - `BTC_MISPRICING_THRESHOLD`: Mispricing threshold (default: 0.05)
   - `BTC_ARBITRAGE_THRESHOLD`: Arbitrage threshold (default: 0.01)
   - `MAX_POSITION_SIZE`: Maximum position size in USDC (default: 50)

## Strategy Overview

Uses technical analysis to predict BTC price movements and identify mispriced BTC-related markets on Polymarket.

## Files
- `main.py`: Standalone runner script
- `btc_strategy.py`: Core BTC prediction strategy implementation
- `requirements.txt`: Python dependencies
- `README.md`: This documentation
