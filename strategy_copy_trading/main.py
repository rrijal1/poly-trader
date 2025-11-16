#!/usr/bin/env python3
"""
Dynamic Copy Trading Strategy Runner
Standalone runner for Railway deployment
"""

import os
import sys
import logging
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common import TradeSignal
from strategy_copy_trading.copy_strategy import DynamicCopyTradingStrategy

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the dynamic copy trading strategy."""
    logger.info("Starting Dynamic Copy Trading Strategy")
    
    config = {
        'total_copy_budget': float(os.getenv('COPY_TOTAL_BUDGET', '10000')),
        'min_trades': int(os.getenv('COPY_MIN_TRADES', '50')),
        'min_wallet_balance': float(os.getenv('COPY_MIN_WALLET', '1000')),
        'max_traders_to_follow': int(os.getenv('COPY_MAX_TRADERS', '5')),
        'max_position_vs_wallet': float(os.getenv('COPY_MAX_POS_WALLET', '0.05')),
        'max_position_vs_trader_wallet': float(os.getenv('COPY_MAX_POS_TRADER', '0.1')),
        'wallet_rebalance_interval_hours': float(os.getenv('COPY_REBALANCE_HOURS', '24')),
        'update_interval_hours': float(os.getenv('COPY_UPDATE_HOURS', '6'))
    }
    
    strategy = DynamicCopyTradingStrategy(config)
    
    # Mock market data for testing
    markets_df = pd.DataFrame({
        'market_id': ['politics_market'],
        'yes_price': [0.6],
        'no_price': [0.4]
    })
    
    signals = strategy.analyze_markets(markets_df)
    logger.info(f"Generated {len(signals)} copy trading signals")
    
    for signal in signals:
        logger.info(f"Signal: {signal}")

if __name__ == "__main__":
    main()
