#!/usr/bin/env python3
"""
Dynamic Counter Trading Strategy Runner
Standalone runner for Railway deployment
"""

import os
import sys
import logging
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .common import TradeSignal
except ImportError:
    from common import TradeSignal
from strategy_counter_trading.counter_strategy import DynamicCounterTradingStrategy

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the dynamic counter trading strategy."""
    logger.info("Starting Dynamic Counter Trading Strategy")
    
    config = {
        'total_counter_budget': float(os.getenv('COUNTER_TOTAL_BUDGET', '5000')),
        'min_trades': int(os.getenv('COUNTER_MIN_TRADES', '50')),
        'min_wallet_balance': float(os.getenv('COUNTER_MIN_WALLET', '1000')),
        'max_traders_to_counter': int(os.getenv('COUNTER_MAX_TRADERS', '5')),
        'max_position_vs_wallet': float(os.getenv('COUNTER_MAX_POS_WALLET', '0.03')),
        'max_position_vs_trader_wallet': float(os.getenv('COUNTER_MAX_POS_TRADER', '0.05')),
        'wallet_rebalance_interval_hours': float(os.getenv('COUNTER_REBALANCE_HOURS', '24')),
        'update_interval_hours': float(os.getenv('COUNTER_UPDATE_HOURS', '6'))
    }
    
    strategy = DynamicCounterTradingStrategy(config)
    
    # Mock market data for testing
    markets_df = pd.DataFrame({
        'market_id': ['crypto_market'],
        'yes_price': [0.4],
        'no_price': [0.6]
    })
    
    signals = strategy.analyze_markets(markets_df)
    logger.info(f"Generated {len(signals)} counter trading signals")
    
    for signal in signals:
        logger.info(f"Signal: {signal}")

if __name__ == "__main__":
    main()
