#!/usr/bin/env python3
"""
Price Arbitrage Strategy Runner
Standalone runner for Kalshi deployment
"""

import os
import sys
import logging
import pandas as pd
from dotenv import load_dotenv

from common import TradeSignal, get_client
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
    logger.info("Starting Kalshi Price Arbitrage Strategy")
    
    config = {
        'threshold': float(os.getenv('ARBITRAGE_THRESHOLD', '0.03')),
        'max_size': int(os.getenv('MAX_POSITION_SIZE', '100'))
    }
    
    strategy = PriceArbitrageStrategy(config)
    
    # Get real market data from Kalshi API
    client = get_client()
    
    try:
        # Fetch active markets from Kalshi
        markets_response = client.get_markets(limit=100, status='open')
        markets = markets_response.get('markets', [])
        
        if not markets:
            logger.warning("No markets found")
            return
        
        # Convert to DataFrame with orderbook data
        market_data_list = []
        for market in markets[:20]:  # Limit to first 20 markets for testing
            ticker = market.get('ticker')
            if not ticker:
                continue
            
            try:
                # Get orderbook for pricing
                orderbook = client.get_orderbook(ticker)
                
                # Extract best prices from orderbook
                yes_bids = orderbook.get('yes', [])
                no_bids = orderbook.get('no', [])
                
                if yes_bids and no_bids:
                    # Get best ask prices (what we'd pay to buy)
                    yes_ask = min([order[0] for order in yes_bids if len(order) > 0], default=0)
                    no_ask = min([order[0] for order in no_bids if len(order) > 0], default=0)
                    
                    # Convert from cents to dollars
                    yes_price = yes_ask / 100.0 if yes_ask else 0
                    no_price = no_ask / 100.0 if no_ask else 0
                    
                    market_data_list.append({
                        'ticker': ticker,
                        'yes_price': yes_price,
                        'no_price': no_price,
                        'volume': market.get('volume', 0)
                    })
            except Exception as e:
                logger.error(f"Error fetching orderbook for {ticker}: {e}")
                continue
        
        if not market_data_list:
            logger.warning("No valid market data retrieved")
            return
        
        markets_df = pd.DataFrame(market_data_list)
        
        # Analyze markets for arbitrage opportunities
        signals = strategy.analyze_markets(markets_df)
        logger.info(f"Generated {len(signals)} arbitrage signals")
        
        # Execute arbitrage signals using market orders
        executed_trades = []
        for signal in signals:
            if signal.ticker:
                logger.info(f"Executing arbitrage signal: {signal.market_id} - {signal.action} "
                           f"{signal.size} contracts @ ${signal.price:.2f}")
                
                # Determine action and side
                action = 'buy' if 'buy' in signal.action else 'sell'
                side = 'yes' if 'yes' in signal.action else 'no'
                
                # Execute market order
                result = client.execute_market_order(
                    ticker=signal.ticker,
                    side=side,
                    count=signal.size,
                    action=action
                )
                
                if result:
                    executed_trades.append({
                        'signal': signal,
                        'result': result
                    })
                    logger.info(f"Successfully executed arbitrage trade: {result}")
                else:
                    logger.warning(f"Failed to execute arbitrage trade for {signal.market_id}")
            else:
                logger.warning(f"No ticker for arbitrage signal: {signal.market_id}")
        
        logger.info(f"Completed arbitrage execution: {len(executed_trades)}/{len(signals)} trades executed")
    
    except Exception as e:
        logger.error(f"Error in arbitrage strategy: {e}", exc_info=True)

if __name__ == "__main__":
    main()
