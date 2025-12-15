"""
Price Arbitrage Strategy
Places trades on both sides when yes_price + no_price < 1 USD.
Adapted for Kalshi markets.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import pandas as pd

from common import TradeSignal, get_client

logger = logging.getLogger(__name__)

class PriceArbitrageStrategy:
    """Arbitrage strategy that places market orders on both sides when sum < 1."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = get_client()  # Use Kalshi client
    
    def analyze_market(self, market_data: Dict) -> List[TradeSignal]:
        """Analyze market for arbitrage opportunities using market orders."""
        signals = []
        
        yes_price = market_data.get('yes_price', 0)
        no_price = market_data.get('no_price', 0)
        ticker = market_data.get('ticker', '')
        
        if yes_price == 0 or no_price == 0 or not ticker:
            return signals
        
        total = yes_price + no_price
        # Threshold for arbitrage accounting for fees and slippage
        threshold = self.config.get('threshold', 0.03)
        
        if total < (1 - threshold):
            # Arbitrage opportunity: place market orders on both sides
            size = min(
                self.config.get('max_size', 100),
                market_data.get('volume', 0) * 0.01
            )
            
            # Convert size to integer contracts (Kalshi uses integer contracts)
            size_contracts = int(size)
            if size_contracts < 1:
                size_contracts = 1
            
            # Calculate potential profit
            total_cost = (yes_price + no_price) * size_contracts
            profit = (1 - total) * size_contracts
            
            # Signal for YES (market order)
            signals.append(TradeSignal(
                market_id=ticker,
                action='buy_yes',
                price=yes_price,
                size=size_contracts,
                reason=f'Arbitrage: total {total:.4f} < 1, potential profit ${profit:.2f}',
                confidence=min(1.0, (1 - total) / threshold),
                ticker=ticker
            ))
            
            # Signal for NO (market order)
            signals.append(TradeSignal(
                market_id=ticker,
                action='buy_no',
                price=no_price,
                size=size_contracts,
                reason=f'Arbitrage: total {total:.4f} < 1, potential profit ${profit:.2f}',
                confidence=min(1.0, (1 - total) / threshold),
                ticker=ticker
            ))
        
        return signals
    
    def analyze_markets(self, markets_df: pd.DataFrame) -> List[TradeSignal]:
        """Analyze multiple markets."""
        all_signals = []
        for _, market in markets_df.iterrows():
            signals = self.analyze_market(market.to_dict())
            all_signals.extend(signals)
        return all_signals