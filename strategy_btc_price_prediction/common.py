import os
from typing import Dict, List, Optional
from dataclasses import dataclass
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

class OptimizedClobClient:
    """
    Streamlined CLOB client using official py-clob-client.
    Minimizes API calls and optimizes for speed.
    """

    def __init__(self, host: str = "https://clob.polymarket.com", chain_id: int = 137):
        from py_clob_client.client import ClobClient

        self.host = host
        self.chain_id = chain_id
        self.private_key = os.getenv('PM_PRIVATE_KEY')
        self.funder = os.getenv('PM_PROXY_ADDRESS')

        if not self.private_key:
            logger.warning("No PM_PRIVATE_KEY found - running in read-only mode")
            self.client = ClobClient(host)
            self.mode = "read-only"
        else:
            # Initialize with full trading capabilities
            if self.funder:
                self.client = ClobClient(
                    host=host,
                    key=self.private_key,
                    chain_id=chain_id,
                    signature_type=1,
                    funder=self.funder,
                )
            else:
                self.client = ClobClient(
                    host=host,
                    key=self.private_key,
                    chain_id=chain_id
                )

            # Set up API credentials for authenticated requests
            creds = self.client.create_or_derive_api_creds()
            self.client.set_api_creds(creds)
            self.mode = "trading"

        logger.info(f"Initialized CLOB client in {self.mode} mode")

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