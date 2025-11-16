"""
Common types and classes for trading strategies.
"""

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class TradeSignal:
    """Represents a trading signal."""
    market_id: str
    action: str  # 'buy_yes', 'buy_no', 'buy_both'
    price: float
    size: float
    reason: str
    confidence: float  # 0-1