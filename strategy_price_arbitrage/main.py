#!/usr/bin/env python3
"""
Price Arbitrage Strategy Runner
Standalone runner for Railway deployment
"""

import os
import sys
import logging
import pandas as pd
from dotenv import load_dotenv

from common import TradeSignal, get_clob_client
from arbitrage import PriceArbitrageStrategy

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the price arbitrage strategy."""
    logger.info("Starting Price Arbitrage Strategy with Market Orders")
    
    config = {
        'threshold': float(os.getenv('ARBITRAGE_THRESHOLD', '0.01')),
        'max_size': float(os.getenv('MAX_POSITION_SIZE', '100'))
    }
    
    strategy = PriceArbitrageStrategy(config)
    
    # Get real market data from Gamma API via OptimizedClobClient
    client = get_clob_client()
    
    # Mock market data for testing - in production would scan all markets
    markets_df = pd.DataFrame({
        'market_id': ['market1', 'market2'],
        'yes_price': [0.5, 0.48],
        'no_price': [0.5, 0.52],
        'token_ids': [['0x123...yes', '0x123...no'], ['0x456...yes', '0x456...no']],
        'volume': [1000, 2000]
    })
    
    signals = strategy.analyze_markets(markets_df)
    logger.info(f"Generated {len(signals)} arbitrage signals")
    
    # Execute arbitrage signals using market orders
    executed_trades = []
    for signal in signals:
        if signal.token_id:
            logger.info(f"Executing arbitrage signal: {signal.market_id} - {signal.action} "
                       f"${signal.size:.2f} (token: {signal.token_id[:10]}...)")
            
            # Execute market order for arbitrage
            side = 'yes' if 'yes' in signal.action else 'no'
            result = client.execute_market_order(signal.token_id, side, signal.size)
            
            if result:
                executed_trades.append({
                    'signal': signal,
                    'result': result
                })
                logger.info(f"Successfully executed arbitrage trade: {result}")
            else:
                logger.warning(f"Failed to execute arbitrage trade for {signal.market_id}")
        else:
            logger.warning(f"No token_id for arbitrage signal: {signal.market_id}")
    
    logger.info(f"Completed arbitrage execution: {len(executed_trades)}/{len(signals)} trades executed")

if __name__ == "__main__":
    main()
