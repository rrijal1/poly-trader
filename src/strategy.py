"""
Strategy Engine for Polymarket Trader
Implements various trading strategies for prediction markets.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .data_collector import DataCollector

logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    """Represents a trading signal."""
    market_id: str
    action: str  # 'buy_yes', 'buy_no', 'sell_yes', 'sell_no'
    price: float
    size: float
    reason: str
    confidence: float  # 0-1

class BaseStrategy:
    """Base class for trading strategies."""
    
    def __init__(self, data_collector: DataCollector, config: Dict):
        self.data_collector = data_collector
        self.config = config
    
    def analyze_market(self, market_data: Dict) -> Optional[TradeSignal]:
        """Analyze a single market and return trading signal if any."""
        raise NotImplementedError
    
    def analyze_markets(self, markets_df: pd.DataFrame) -> List[TradeSignal]:
        """Analyze multiple markets."""
        signals = []
        for _, market in markets_df.iterrows():
            signal = self.analyze_market(market.to_dict())
            if signal:
                signals.append(signal)
        return signals

class ArbitrageStrategy(BaseStrategy):
    """Arbitrage strategy - find price discrepancies."""
    
    def analyze_market(self, market_data: Dict) -> Optional[TradeSignal]:
        """Look for arbitrage opportunities where yes + no < 1."""
        yes_price = market_data.get('yes_price', 0)
        no_price = market_data.get('no_price', 0)
        
        if yes_price == 0 or no_price == 0:
            return None
        
        total = yes_price + no_price
        threshold = self.config.get('threshold', 0.02)
        
        if total < (1 - threshold):
            # Arbitrage opportunity: buy both sides
            market_id = market_data['market_id']
            size = min(self.config.get('max_size', 100), market_data.get('volume', 0) * 0.01)
            
            # Buy the cheaper side more
            if yes_price < no_price:
                return TradeSignal(
                    market_id=market_id,
                    action='buy_yes',
                    price=yes_price,
                    size=size,
                    reason=f'Arbitrage: total price {total:.3f} < 1',
                    confidence=min(1.0, (1 - total) / threshold)
                )
            else:
                return TradeSignal(
                    market_id=market_id,
                    action='buy_no',
                    price=no_price,
                    size=size,
                    reason=f'Arbitrage: total price {total:.3f} < 1',
                    confidence=min(1.0, (1 - total) / threshold)
                )
        
        return None

class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy - bet against extreme prices."""
    
    def __init__(self, data_collector: DataCollector, config: Dict):
        super().__init__(data_collector, config)
        self.price_history = {}  # market_id -> list of prices
    
    def analyze_market(self, market_data: Dict) -> Optional[TradeSignal]:
        """Look for prices that have moved away from mean."""
        market_id = market_data['market_id']
        current_price = market_data.get('yes_price', 0)
        
        if current_price == 0:
            return None
        
        # Update price history
        if market_id not in self.price_history:
            self.price_history[market_id] = []
        
        self.price_history[market_id].append(current_price)
        
        # Keep only recent prices
        lookback = self.config.get('lookback_period', 24)
        if len(self.price_history[market_id]) > lookback:
            self.price_history[market_id] = self.price_history[market_id][-lookback:]
        
        if len(self.price_history[market_id]) < 10:  # Need some history
            return None
        
        prices = self.price_history[market_id]
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        threshold = self.config.get('threshold', 0.05)
        
        z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
        
        if abs(z_score) > threshold:
            size = self.config.get('max_size', 50)
            confidence = min(1.0, abs(z_score) / 2.0)
            
            if z_score > threshold:  # Price too high, bet no
                return TradeSignal(
                    market_id=market_id,
                    action='buy_no',
                    price=market_data.get('no_price', 0),
                    size=size,
                    reason=f'Mean reversion: z-score {z_score:.2f}',
                    confidence=confidence
                )
            elif z_score < -threshold:  # Price too low, bet yes
                return TradeSignal(
                    market_id=market_id,
                    action='buy_yes',
                    price=current_price,
                    size=size,
                    reason=f'Mean reversion: z-score {z_score:.2f}',
                    confidence=confidence
                )
        
        return None

class MomentumStrategy(BaseStrategy):
    """Momentum strategy - follow price trends."""
    
    def __init__(self, data_collector: DataCollector, config: Dict):
        super().__init__(data_collector, config)
        self.price_history = {}
    
    def analyze_market(self, market_data: Dict) -> Optional[TradeSignal]:
        """Look for strong price movements."""
        market_id = market_data['market_id']
        current_price = market_data.get('yes_price', 0)
        
        if current_price == 0:
            return None
        
        # Update history
        if market_id not in self.price_history:
            self.price_history[market_id] = []
        
        self.price_history[market_id].append(current_price)
        
        lookback = self.config.get('lookback_period', 6)
        if len(self.price_history[market_id]) > lookback:
            self.price_history[market_id] = self.price_history[market_id][-lookback:]
        
        if len(self.price_history[market_id]) < lookback:
            return None
        
        prices = self.price_history[market_id]
        if len(prices) < 2:
            return None
        
        # Calculate momentum (recent - older)
        recent_avg = np.mean(prices[-3:]) if len(prices) >= 3 else prices[-1]
        older_avg = np.mean(prices[:3]) if len(prices) >= 3 else prices[0]
        
        momentum = recent_avg - older_avg
        threshold = self.config.get('threshold', 0.03)
        
        if abs(momentum) > threshold:
            size = self.config.get('max_size', 50)
            confidence = min(1.0, abs(momentum) / (threshold * 2))
            
            if momentum > threshold:  # Upward momentum, buy yes
                return TradeSignal(
                    market_id=market_id,
                    action='buy_yes',
                    price=current_price,
                    size=size,
                    reason=f'Momentum: +{momentum:.3f}',
                    confidence=confidence
                )
            elif momentum < -threshold:  # Downward momentum, buy no
                return TradeSignal(
                    market_id=market_id,
                    action='buy_no',
                    price=market_data.get('no_price', 0),
                    size=size,
                    reason=f'Momentum: {momentum:.3f}',
                    confidence=confidence
                )
        
        return None

class NicheSportsStrategy(BaseStrategy):
    """Strategy focused on sports markets with domain knowledge."""
    
    def __init__(self, data_collector: DataCollector, config: Dict):
        super().__init__(data_collector, config)
        # Could integrate with sports APIs, injury reports, etc.
    
    def analyze_market(self, market_data: Dict) -> Optional[TradeSignal]:
        """Sports-specific analysis."""
        category = market_data.get('category', '').lower()
        
        if 'nba' not in category and 'basketball' not in category:
            return None
        
        # Example: Look for underdog opportunities
        question = market_data.get('question', '').lower()
        
        # Simple rule: If favorite is heavily favored (>0.7), look for value in underdog
        yes_price = market_data.get('yes_price', 0)
        
        if 0.3 < yes_price < 0.7:  # Not too extreme
            return None
        
        if yes_price > 0.7:  # Heavy favorite, bet underdog (no)
            return TradeSignal(
                market_id=market_data['market_id'],
                action='buy_no',
                price=market_data.get('no_price', 0),
                size=self.config.get('max_size', 25),
                reason='Sports: Underdog value vs heavy favorite',
                confidence=0.6
            )
        elif yes_price < 0.3:  # Heavy underdog, but maybe not
            return TradeSignal(
                market_id=market_data['market_id'],
                action='buy_yes',
                price=yes_price,
                size=self.config.get('max_size', 25),
                reason='Sports: Potential upset opportunity',
                confidence=0.5
            )
        
        return None

class StrategyEngine:
    """Main strategy engine that combines multiple strategies."""
    
    def __init__(self, data_collector: DataCollector, config: Dict):
        self.data_collector = data_collector
        self.config = config
        self.strategies = self._initialize_strategies()
    
    def _initialize_strategies(self) -> List[BaseStrategy]:
        """Initialize enabled strategies."""
        strategies = []
        strategy_configs = self.config.get('strategies', {})
        
        if strategy_configs.get('arbitrage', {}).get('enabled', True):
            strategies.append(ArbitrageStrategy(self.data_collector, strategy_configs['arbitrage']))
        
        if strategy_configs.get('mean_reversion', {}).get('enabled', True):
            strategies.append(MeanReversionStrategy(self.data_collector, strategy_configs['mean_reversion']))
        
        if strategy_configs.get('momentum', {}).get('enabled', False):
            strategies.append(MomentumStrategy(self.data_collector, strategy_configs['momentum']))
        
        if strategy_configs.get('sports', {}).get('enabled', True):
            strategies.append(NicheSportsStrategy(self.data_collector, strategy_configs.get('sports', {})))
        
        return strategies
    
    def generate_signals(self, markets_df: pd.DataFrame) -> List[TradeSignal]:
        """Generate trading signals from all strategies."""
        all_signals = []
        
        for strategy in self.strategies:
            try:
                signals = strategy.analyze_markets(markets_df)
                all_signals.extend(signals)
            except Exception as e:
                logger.error(f"Error in strategy {strategy.__class__.__name__}: {e}")
        
        # Filter and rank signals
        filtered_signals = self._filter_signals(all_signals)
        
        return filtered_signals
    
    def _filter_signals(self, signals: List[TradeSignal]) -> List[TradeSignal]:
        """Filter and prioritize signals."""
        # Remove duplicates (same market, same action)
        seen = set()
        unique_signals = []
        
        for signal in signals:
            key = (signal.market_id, signal.action)
            if key not in seen:
                seen.add(key)
                unique_signals.append(signal)
        
        # Sort by confidence
        unique_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # Limit number of signals
        max_signals = self.config.get('max_signals_per_run', 10)
        return unique_signals[:max_signals]