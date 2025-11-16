# Price Arbitrage Strategy

This folder contains the standalone Price Arbitrage Strategy for Railway deployment.

## Railway Deployment

1. **Connect Repository**: Point Railway to this specific folder (`strategy_price_arbitrage`)
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python main.py`
4. **Environment Variables**:
   - `ARBITRAGE_THRESHOLD`: Price difference threshold (default: 0.01)
   - `MAX_POSITION_SIZE`: Maximum position size in USDC (default: 100)

## Strategy Overview

Exploits price inefficiencies across Polymarket by identifying arbitrage opportunities between different markets or outcomes.

## Files
- `main.py`: Standalone runner script
- `arbitrage.py`: Core arbitrage strategy implementation
- `requirements.txt`: Python dependencies
- `README.md`: This documentation
