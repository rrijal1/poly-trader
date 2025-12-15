#!/usr/bin/env python3
"""
BTC Lag Arbitrage Strategy Runner

Note: This strategy is simplified for Kalshi. It monitors external BTC price
movements and looks for stale pricing in Kalshi BTC markets.
"""

import os
import time
import logging
from dotenv import load_dotenv

from common import get_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    load_dotenv()
    
    # Configuration
    btc_ticker = os.getenv('KALSHI_BTC_TICKER')  # e.g., specific BTC market ticker
    poll_interval_seconds = int(os.getenv('POLL_INTERVAL_SECONDS', '60'))
    
    if not btc_ticker:
        logger.warning("No KALSHI_BTC_TICKER set. Listing BTC markets...")
        client = get_client()
        markets = client.get_markets(limit=100, status='open')
        btc_markets = [m for m in markets.get('markets', []) 
                      if 'bitcoin' in m.get('title', '').lower() or 'btc' in m.get('title', '').lower()]
        
        logger.info(f"Found {len(btc_markets)} BTC markets:")
        for market in btc_markets:
            logger.info(f"  - {market.get('ticker')}: {market.get('title')}")
        
        return
    
    client = get_client()
    logger.info(f"Starting BTC lag-arb for ticker: {btc_ticker}")
    
    # Simple loop
    while True:
        try:
            # Get current orderbook
            orderbook = client.get_orderbook(btc_ticker)
            
            # TODO: Implement lag arbitrage logic:
            # 1. Fetch external BTC price from a fast feed (e.g., Coinbase, Binance)
            # 2. Compare with Kalshi market prices
            # 3. If Kalshi is stale relative to external price movement, place orders
            
            logger.info(f"Orderbook: {orderbook}")
            
        except Exception as e:
            logger.error(f"Error in lag-arb loop: {e}", exc_info=True)
        
        time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    main()
