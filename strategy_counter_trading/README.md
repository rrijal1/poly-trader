# Dynamic Counter Trading Strategy

This folder contains the standalone Dynamic Counter Trading Strategy for Railway deployment.

## Railway Deployment

1. **Connect Repository**: Point Railway to this specific folder (`strategy_counter_trading`)
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python main.py`
4. **Environment Variables**:
   - `COUNTER_TOTAL_BUDGET`: Total counter trading budget (default: 5000)
   - `COUNTER_MIN_TRADES`: Minimum trades required (default: 50)
   - `COUNTER_MIN_WALLET`: Minimum wallet balance (default: 1000)
   - `COUNTER_MAX_TRADERS`: Maximum traders to counter (default: 5)
   - `COUNTER_MAX_POS_WALLET`: Max position vs wallet ratio (default: 0.03)
   - `COUNTER_MAX_POS_TRADER`: Max position vs trader wallet ratio (default: 0.05)
   - `COUNTER_REBALANCE_HOURS`: Rebalance interval (default: 24)
   - `COUNTER_UPDATE_HOURS`: Update interval (default: 6)
   - `COUNTER_*_PRIVATE_KEY`: Wallet keys for losing traders

## Strategy Overview

Dynamically discovers and counters traders with negative PnL across all timeframes (7-day, 30-day, all-time).

## Files
- `main.py`: Standalone runner script
- `counter_strategy.py`: Core counter trading strategy implementation
- `requirements.txt`: Python dependencies
- `README.md`: This documentation
