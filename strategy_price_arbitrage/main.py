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

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .common import TradeSignal
except ImportError:
    from common import TradeSignal
from strategy_price_arbitrage.arbitrage import PriceArbitrageStrategy

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
    logger.info("Starting Price Arbitrage Strategy")
    
    config = {
        'threshold': float(os.getenv('ARBITRAGE_THRESHOLD', '0.01')),
        'max_size': float(os.getenv('MAX_POSITION_SIZE', '100'))
    }
    
    strategy = PriceArbitrageStrategy(config)
    
    # Mock market data for testing
    markets_df = pd.DataFrame({
        'market_id': ['market1', 'market2'],
        'yes_price': [0.5, 0.48],
        'no_price': [0.5, 0.52]
    })
    
    signals = strategy.analyze_markets(markets_df)
    logger.info(f"Generated {len(signals)} arbitrage signals")
    
    for signal in signals:
        logger.info(f"Signal: {signal}")

if __name__ == "__main__":
    main()
