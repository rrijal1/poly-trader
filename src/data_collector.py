"""
Data Collection Module for Polymarket Trader
Handles fetching market data, prices, and order book information.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, TradeParams
from py_clob_client.constants import POLYGON
import requests
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataCollector:
    """Handles data collection from Polymarket."""

    def __init__(self):
        """Initialize the data collector."""
        self.host = "https://clob.polymarket.com"
        self.api_creds = self._load_api_creds()
        self.chain_id = 137  # Polygon mainnet
        self.private_key = os.getenv('PRIVATE_KEY')
        
        # Initialize client - read-only if no creds
        if self.api_creds and self.private_key:
            self.client = ClobClient(
                self.host, 
                key=self.private_key, 
                chain_id=self.chain_id, 
                creds=self.api_creds
            )
        else:
            self.client = ClobClient(self.host)

    def _load_api_creds(self) -> Optional[ApiCreds]:
        """Load API credentials from environment variables."""
        api_key = os.getenv('POLYMARKET_API_KEY')
        api_secret = os.getenv('POLYMARKET_API_SECRET')
        api_passphrase = os.getenv('POLYMARKET_API_PASSPHRASE')

        if not all([api_key, api_secret, api_passphrase]):
            logger.warning("API credentials not found in environment variables")
            return None

        assert api_key is not None
        assert api_secret is not None
        assert api_passphrase is not None
        return ApiCreds(api_key=api_key, api_secret=api_secret, api_passphrase=api_passphrase)

    def get_markets(self, active: bool = True, closed: bool = False, limit: int = 100) -> Any:
        """
        Fetch markets from Polymarket.

        Args:
            active: Include active markets
            closed: Include closed markets
            limit: Maximum number of markets to return

        Returns:
            List of market dictionaries
        """
        try:
            params = {
                'active': active,
                'closed': closed,
                'limit': limit
            }
            response = self.client.get_markets(**params)
            return response
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []

    def get_market_data(self, market_id: str) -> Any:
        """
        Get detailed data for a specific market.

        Args:
            market_id: The market ID

        Returns:
            Market data dictionary or None if error
        """
        try:
            response = self.client.get_market(market_id)
            return response
        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")
            return None

    def get_order_book(self, market_id: str) -> Any:
        """
        Get order book for a market.

        Args:
            market_id: The market ID

        Returns:
            Order book data or None if error
        """
        try:
            response = self.client.get_order_book(market_id)
            return response
        except Exception as e:
            logger.error(f"Error fetching order book for {market_id}: {e}")
            return None

    def get_trades(self, market_id: str, limit: int = 100) -> List[Dict]:
        """
        Get recent trades for a market.

        Args:
            market_id: The market ID
            limit: Maximum number of trades to return

        Returns:
            List of trade dictionaries
        """
        try:
            params = TradeParams(market=market_id)
            response = self.client.get_trades(params)
            if isinstance(response, list):
                return response[:limit]
            elif isinstance(response, dict):
                return response.get('data', [])[:limit]
            else:
                return []
        except Exception as e:
            logger.error(f"Error fetching trades for {market_id}: {e}")
            return []

    def filter_markets_by_niche(self, markets: List[Dict], niches: List[str]) -> List[Dict]:
        """
        Filter markets by niche categories.

        Args:
            markets: List of market dictionaries
            niches: List of niche categories to include

        Returns:
            Filtered list of markets
        """
        filtered = []
        for market in markets:
            category = market.get('category', '').lower()
            if any(niche.lower() in category for niche in niches):
                filtered.append(market)
        return filtered

    def get_market_prices(self, market_id: str) -> Dict[str, float]:
        """
        Get current prices for a market.

        Args:
            market_id: The market ID

        Returns:
            Dictionary with 'yes' and 'no' prices
        """
        order_book = self.get_order_book(market_id)
        if not order_book:
            return {}

        # Extract best bid/ask prices
        try:
            yes_book = getattr(order_book, 'yes', None)
            no_book = getattr(order_book, 'no', None)
            
            yes_price = 0
            if yes_book and hasattr(yes_book, 'bids') and yes_book.bids:
                yes_price = float(yes_book.bids[0].price)
            
            no_price = 0
            if no_book and hasattr(no_book, 'bids') and no_book.bids:
                no_price = float(no_book.bids[0].price)
            
            return {
                'yes': yes_price,
                'no': no_price
            }
        except Exception as e:
            logger.error(f"Error parsing order book for {market_id}: {e}")
            return {}

    def collect_market_data(self, niches: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Collect comprehensive market data for analysis.

        Args:
            niches: List of niches to focus on

        Returns:
            DataFrame with market data
        """
        markets_response = self.get_markets(limit=500)
        if isinstance(markets_response, dict):
            markets = markets_response.get('data', [])
        elif isinstance(markets_response, list):
            markets = markets_response
        else:
            markets = []

        if niches:
            markets = self.filter_markets_by_niche(markets, niches)

        data = []
        for market in markets[:50]:  # Limit to 50 for performance
            market_id = market.get('id')
            if not market_id:
                continue

            prices = self.get_market_prices(market_id)
            trades = self.get_trades(market_id, limit=10)

            data.append({
                'market_id': market_id,
                'question': market.get('question', ''),
                'category': market.get('category', ''),
                'volume': market.get('volume', 0),
                'yes_price': prices.get('yes', 0),
                'no_price': prices.get('no', 0),
                'spread': abs(prices.get('yes', 0) - prices.get('no', 0)),
                'active': market.get('active', False),
                'end_date': market.get('end_date', ''),
                'recent_trades': len(trades)
            })

        return pd.DataFrame(data)