"""
Price Arbitrage Strategy
Places trades on both sides when yes_price + no_price < 1 USD.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd

from common import TradeSignal, get_clob_client

logger = logging.getLogger(__name__)

class PriceArbitrageStrategy:
    """Arbitrage strategy that places market orders on both sides when sum < 1."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = get_clob_client()  # Use optimized CLOB client
    
    def analyze_market(self, market_data: Dict) -> List[TradeSignal]:
        """Analyze market for arbitrage opportunities using market orders."""
        signals = []
        
        yes_price = market_data.get('yes_price', 0)
        no_price = market_data.get('no_price', 0)
        token_ids = market_data.get('token_ids', [])
        
        if yes_price == 0 or no_price == 0 or len(token_ids) < 2:
            return signals
        
        total = yes_price + no_price
        threshold = self.config.get('threshold', 0.01)  # Default 1 cent
        
        if total < (1 - threshold):
            # Arbitrage opportunity: place market orders on both sides
            market_id = market_data['market_id']
            size = min(self.config.get('max_size', 100), market_data.get('volume', 0) * 0.01)
            
            # Calculate sizes based on prices (buy more of the cheaper side)
            total_cost = total * size
            profit = (1 - total) * size
            
            # Signal for YES (market order)
            signals.append(TradeSignal(
                market_id=market_id,
                action='buy_yes',
                price=yes_price,  # Market price will be determined at execution
                size=size,
                reason=f'Arbitrage: total {total:.4f} < 1, potential profit ${profit:.2f} (market order)',
                confidence=min(1.0, (1 - total) / threshold),
                token_id=token_ids[0] if len(token_ids) > 0 else None  # YES token
            ))
            
            # Signal for NO (market order)
            signals.append(TradeSignal(
                market_id=market_id,
                action='buy_no',
                price=no_price,  # Market price will be determined at execution
                size=size,
                reason=f'Arbitrage: total {total:.4f} < 1, potential profit ${profit:.2f} (market order)',
                confidence=min(1.0, (1 - total) / threshold),
                token_id=token_ids[1] if len(token_ids) > 1 else None  # NO token
            ))
        
        return signals
    
    def analyze_markets(self, markets_df: pd.DataFrame) -> List[TradeSignal]:
        """Analyze multiple markets."""
        all_signals = []
        for _, market in markets_df.iterrows():
            signals = self.analyze_market(market.to_dict())
            all_signals.extend(signals)
        return all_signals