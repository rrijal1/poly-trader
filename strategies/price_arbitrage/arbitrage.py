"""
Price Arbitrage Strategy
Places trades on both sides when yes_price + no_price < 1 USD.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd

from ..common import TradeSignal

logger = logging.getLogger(__name__)

class PriceArbitrageStrategy:
    """Arbitrage strategy that places orders on both sides when sum < 1."""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def analyze_market(self, market_data: Dict) -> List[TradeSignal]:
        """Analyze market for arbitrage opportunities."""
        signals = []
        
        yes_price = market_data.get('yes_price', 0)
        no_price = market_data.get('no_price', 0)
        
        if yes_price == 0 or no_price == 0:
            return signals
        
        total = yes_price + no_price
        threshold = self.config.get('threshold', 0.01)  # Default 1 cent
        
        if total < (1 - threshold):
            # Arbitrage opportunity: place orders on both sides
            market_id = market_data['market_id']
            size = min(self.config.get('max_size', 100), market_data.get('volume', 0) * 0.01)
            
            # Calculate sizes based on prices (buy more of the cheaper side)
            total_cost = total * size
            profit = (1 - total) * size
            
            # Signal for YES
            signals.append(TradeSignal(
                market_id=market_id,
                action='buy_yes',
                price=yes_price,
                size=size,
                reason=f'Arbitrage: total {total:.4f} < 1, potential profit ${profit:.2f}',
                confidence=min(1.0, (1 - total) / threshold)
            ))
            
            # Signal for NO
            signals.append(TradeSignal(
                market_id=market_id,
                action='buy_no',
                price=no_price,
                size=size,
                reason=f'Arbitrage: total {total:.4f} < 1, potential profit ${profit:.2f}',
                confidence=min(1.0, (1 - total) / threshold)
            ))
        
        return signals
    
    def analyze_markets(self, markets_df: pd.DataFrame) -> List[TradeSignal]:
        """Analyze multiple markets."""
        all_signals = []
        for _, market in markets_df.iterrows():
            signals = self.analyze_market(market.to_dict())
            all_signals.extend(signals)
        return all_signals