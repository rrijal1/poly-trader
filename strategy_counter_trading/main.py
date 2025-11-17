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

from common import TradeSignal, get_clob_client
from counter_strategy import DynamicCounterTradingStrategy

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
    logger.info("Starting Dynamic Counter Trading Strategy with Real-time Monitoring")
    
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
    
    # Get real market data from Gamma API via OptimizedClobClient
    client = get_clob_client()
    
    # Mock market data for testing - in production would scan all markets
    markets_df = pd.DataFrame({
        'market_id': ['crypto_market'],
        'yes_price': [0.4],
        'no_price': [0.6],
        'token_ids': [['0xabc...yes', '0xabc...no']],
        'volume': [2000]
    })
    
    signals = strategy.analyze_markets(markets_df)
    logger.info(f"Generated {len(signals)} counter trading signals")
    
    # Execute counter trading signals using market orders
    executed_trades = []
    for signal in signals:
        if signal.token_id:
            logger.info(f"Executing counter trading signal: {signal.market_id} - {signal.action} "
                       f"${signal.size:.2f} (token: {signal.token_id[:10]}...)")
            
            # Execute market order for counter trading
            side = 'yes' if 'yes' in signal.action else 'no'
            result = client.execute_market_order(signal.token_id, side, signal.size)
            
            if result:
                executed_trades.append({
                    'signal': signal,
                    'result': result
                })
                logger.info(f"Successfully executed counter trade: {result}")
            else:
                logger.warning(f"Failed to execute counter trade for {signal.market_id}")
        else:
            logger.warning(f"No token_id for counter trading signal: {signal.market_id}")
    
    logger.info(f"Completed counter trading execution: {len(executed_trades)}/{len(signals)} trades executed")

if __name__ == "__main__":
    main()
