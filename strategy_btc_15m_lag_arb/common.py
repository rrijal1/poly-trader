import os
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

# Add parent directory to path for kalshi_client import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kalshi_client import get_kalshi_client, KalshiClient

logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    """Trade signal with minimal data for fast execution."""
    market_id: str  # Kalshi ticker
    action: str  # 'buy_yes', 'buy_no', 'sell_yes', 'sell_no'
    price: float  # Price in dollars (converted from cents internally)
    size: int  # Number of contracts
    reason: str
    confidence: float
    ticker: Optional[str] = None  # Kalshi market ticker


def get_client() -> KalshiClient:
    """Get or create Kalshi client instance."""
    return get_kalshi_client()
