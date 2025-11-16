# Dynamic Copy Trading Strategy

This folder contains the standalone Dynamic Copy Trading Strategy for Railway deployment.

## Railway Deployment

1. **Connect Repository**: Point Railway to this specific folder (`strategy_copy_trading`)
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python main.py`
4. **Environment Variables**:
   - `COPY_TOTAL_BUDGET`: Total copy trading budget (default: 10000)
   - `COPY_MIN_TRADES`: Minimum trades required (default: 50)
   - `COPY_MIN_WALLET`: Minimum wallet balance (default: 1000)
   - `COPY_MAX_TRADERS`: Maximum traders to follow (default: 5)
   - `COPY_MAX_POS_WALLET`: Max position vs wallet ratio (default: 0.05)
   - `COPY_MAX_POS_TRADER`: Max position vs trader wallet ratio (default: 0.1)
   - `COPY_REBALANCE_HOURS`: Rebalance interval (default: 24)
   - `COPY_UPDATE_HOURS`: Update interval (default: 6)
   - `COPY_CQS_PRIVATE_KEY`: Wallet key for cqs trader
   - `COPY_CIGARETTES_PRIVATE_KEY`: Wallet key for cigarettes trader

## Strategy Overview

Dynamically discovers and follows successful traders with positive PnL across all timeframes (7-day, 30-day, all-time).

## Files
- `main.py`: Standalone runner script
- `copy_strategy.py`: Core copy trading strategy implementation
- `requirements.txt`: Python dependencies
- `README.md`: This documentation
