"""
Common utilities and data structures for Polymarket trading strategies.
Optimized for minimal fees, low latency, and maximum efficiency.
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from py_clob_client.clob_types import OrderBookSummary

logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    """Optimized trade signal with minimal data for fast execution."""
    market_id: str
    action: str  # 'buy_yes', 'buy_no', 'sell_yes', 'sell_no'
    price: float
    size: float
    reason: str
    confidence: float
    token_id: Optional[str] = None  # For direct CLOB trading

@dataclass
class MarketData:
    """Streamlined market data structure."""
    market_id: str
    question: str
    outcomes: List[str]
    outcome_prices: List[float]
    volume: float
    liquidity: float
    end_date: Optional[datetime]
    token_ids: List[str]

@dataclass
class TraderProfile:
    """Minimal trader profile for copy trading."""
    address: str
    username: str
    pnl_7d: float
    pnl_30d: float
    pnl_all_time: float
    win_rate: float
    total_trades: int
    wallet_balance: float
    last_updated: datetime

class OptimizedClobClient:
    """
    Streamlined CLOB client using official py-clob-client.
    Supports agent wallets with funder addresses for trading-only access.
    Minimizes API calls and optimizes for speed.
    """

    def __init__(self, host: str = "https://clob.polymarket.com", chain_id: int = 137):
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds

        self.host = host
        self.chain_id = chain_id
        self.private_key = os.getenv('POLYGON_WALLET_PRIVATE_KEY')
        self.funder_address = os.getenv('FUNDER_WALLET_ADDRESS')

        if not self.private_key:
            logger.warning("No POLYGON_WALLET_PRIVATE_KEY found - running in read-only mode")
            self.client = ClobClient(host)
            self.mode = "read-only"
        else:
            # Initialize with agent wallet setup
            # If funder address is provided, use proxy wallet mode (signature_type=1)
            # This creates a trading-only agent that cannot withdraw funds
            if self.funder_address:
                logger.info(f"Initializing agent wallet with funder: {self.funder_address}")
                self.client = ClobClient(
                    host=host,
                    key=self.private_key,
                    chain_id=chain_id,
                    signature_type=1,  # Email/Magic wallet signatures (delegated signing)
                    funder=self.funder_address  # Address holding the funds
                )
                self.mode = "agent-trading"
            else:
                # Standard EOA wallet (full control)
                logger.info("Initializing standard EOA wallet")
                self.client = ClobClient(
                    host=host,
                    key=self.private_key,
                    chain_id=chain_id
                )
                self.mode = "trading"

            # Set up API credentials for authenticated requests
            creds = self.client.create_or_derive_api_creds()
            self.client.set_api_creds(creds)

        logger.info(f"Initialized CLOB client in {self.mode} mode")

    def get_market_data(self, market_id: str) -> Optional[MarketData]:
        """Get streamlined market data with minimal API calls."""
        try:
            # Use Gamma API for market metadata (faster than CLOB)
            import requests
            gamma_url = f"https://gamma-api.polymarket.com/markets/{market_id}"
            response = requests.get(gamma_url, timeout=5)
            data = response.json()

            return MarketData(
                market_id=market_id,
                question=data.get('question', ''),
                outcomes=data.get('outcomes', []),
                outcome_prices=data.get('outcomePrices', []),
                volume=data.get('volume', 0),
                liquidity=data.get('liquidity', 0),
                end_date=datetime.fromisoformat(data.get('endDate', '').replace('Z', '+00:00')) if data.get('endDate') else None,
                token_ids=data.get('clobTokenIds', [])
            )
        except Exception as e:
            logger.error(f"Failed to get market data for {market_id}: {e}")
            return None

    def get_trader_trades(self, trader_address: str, limit: int = 50) -> List[Dict]:
        """Get recent trades for a specific trader using optimized TradeParams."""
        if self.mode != "trading":
            logger.warning("Cannot get trader trades in read-only mode")
            return []

        try:
            from py_clob_client.clob_types import TradeParams

            # Get recent trades for this trader
            params = TradeParams(maker_address=trader_address)
            trades = self.client.get_trades(params)

            # Return only the most recent trades
            return trades[:limit] if trades else []
        except Exception as e:
            logger.error(f"Failed to get trades for trader {trader_address}: {e}")
            return []

    def execute_market_order(self, token_id: str, side: str, amount: float) -> Optional[Dict]:
        """Execute market order with minimal fees and maximum speed."""
        if self.mode != "trading":
            logger.warning("Cannot execute orders in read-only mode")
            return None

        try:
            from py_clob_client.clob_types import MarketOrderArgs, OrderType
            from py_clob_client.order_builder.constants import BUY, SELL

            # Determine side
            order_side = BUY if side.lower() in ['buy', 'yes'] else SELL

            # Create market order for immediate execution
            order_args = MarketOrderArgs(
                token_id=token_id,
                amount=amount,
                side=order_side
            )

            # Create and post order immediately
            signed_order = self.client.create_market_order(order_args)
            result = self.client.post_order(signed_order, orderType=OrderType.FOK)  # type: ignore  # Fill or Kill for immediate execution

            logger.info(f"Executed market order: {side} ${amount} on {token_id}")
            return result if isinstance(result, dict) else None

        except Exception as e:
            logger.error(f"Failed to execute market order: {e}")
            return None

    def get_orderbook(self, token_id: str) -> Optional[OrderBookSummary]:
        """Get orderbook with minimal latency."""
        try:
            return self.client.get_order_book(token_id)
        except Exception as e:
            logger.error(f"Failed to get orderbook for {token_id}: {e}")
            return None

    def get_balance(self) -> float:
        """Get USDC balance efficiently."""
        if self.mode != "trading":
            return 0.0

        try:
            # Use the client's balance method if available
            balance_info = self.client.get_balance_allowance()
            if isinstance(balance_info, dict):
                return float(balance_info.get('usdc', 0))
            else:
                logger.warning(f"Unexpected balance_info type: {type(balance_info)}")
                return 0.0
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0

# Global client instance for reuse
_clob_client = None

def get_clob_client() -> OptimizedClobClient:
    """Get or create optimized CLOB client instance."""
    global _clob_client
    if _clob_client is None:
        _clob_client = OptimizedClobClient()
    return _clob_client