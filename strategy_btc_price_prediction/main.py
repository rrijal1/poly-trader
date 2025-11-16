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

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .common import TradeSignal
except ImportError:
    from common import TradeSignal
from strategy_btc_price_prediction.btc_strategy import BTCPricePredictionStrategy

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
    logger.info("Starting BTC Price Prediction Strategy")
    
    config = {
        'mispricing_threshold': float(os.getenv('BTC_MISPRICING_THRESHOLD', '0.05')),
        'arbitrage_threshold': float(os.getenv('BTC_ARBITRAGE_THRESHOLD', '0.01')),
        'max_size': float(os.getenv('MAX_POSITION_SIZE', '50'))
    }
    
    strategy = BTCPricePredictionStrategy(config)
    
    # Mock market data for testing
    markets_df = pd.DataFrame({
        'market_id': ['btc_market'],
        'yes_price': [0.55],
        'no_price': [0.45],
        'volume': [1000]
    })
    
    signals = strategy.analyze_markets(markets_df)
    logger.info(f"Generated {len(signals)} BTC prediction signals")
    
    for signal in signals:
        logger.info(f"Signal: {signal}")

if __name__ == "__main__":
    main()
