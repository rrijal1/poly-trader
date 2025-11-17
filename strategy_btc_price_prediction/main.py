#!/usr/bin/env python3
"""
BTC Price Prediction Strategy Runner
Standalone runner for Railway deployment
"""

import os
import sys
import logging
import pandas as pd
from dotenv import load_dotenv

from common import TradeSignal, get_clob_client
from btc_strategy import BTCPricePredictionStrategy

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the BTC price prediction strategy."""
    logger.info("Starting BTC Price Prediction Strategy with Market Orders")
    
    config = {
        'mispricing_threshold': float(os.getenv('BTC_MISPRICING_THRESHOLD', '0.05')),
        'arbitrage_threshold': float(os.getenv('BTC_ARBITRAGE_THRESHOLD', '0.01')),
        'max_size': float(os.getenv('MAX_POSITION_SIZE', '50'))
    }
    
    strategy = BTCPricePredictionStrategy(config)
    
    # Get real market data from Gamma API via OptimizedClobClient
    client = get_clob_client()
    
    # Mock market data for testing - in production would scan BTC markets
    markets_df = pd.DataFrame({
        'market_id': ['btc_market'],
        'question': ['Will Bitcoin be above $97,005.79 at 11/15/2025 15:00?'],
        'yes_price': [0.55],
        'no_price': [0.45],
        'token_ids': [['0x789...yes', '0x789...no']],
        'volume': [1000]
    })
    
    signals = strategy.analyze_markets(markets_df)
    logger.info(f"Generated {len(signals)} BTC prediction signals")
    
    # Execute signals using market orders
    executed_trades = []
    for signal in signals:
        if signal.token_id and signal.action != 'buy_both':
            logger.info(f"Executing BTC prediction signal: {signal.market_id} - {signal.action} "
                       f"${signal.size:.2f} (token: {signal.token_id[:10]}...)")
            
            # Execute market order
            side = 'yes' if 'yes' in signal.action else 'no'
            result = client.execute_market_order(signal.token_id, side, signal.size)
            
            if result:
                executed_trades.append({
                    'signal': signal,
                    'result': result
                })
                logger.info(f"Successfully executed BTC prediction trade: {result}")
            else:
                logger.warning(f"Failed to execute BTC prediction trade for {signal.market_id}")
        elif signal.action == 'buy_both':
            # Handle arbitrage (buy both sides)
            token_ids = signal.token_id  # This would need to be a list for arbitrage
            logger.info(f"BTC arbitrage opportunity detected but not implemented for market orders")
        else:
            logger.warning(f"No token_id for BTC prediction signal: {signal.market_id}")
    
    logger.info(f"Completed BTC prediction execution: {len(executed_trades)}/{len(signals)} trades executed")

if __name__ == "__main__":
    main()
