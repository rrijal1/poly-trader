"""
Counter Trading Strategy
Dynamically identifies and trades against worst performing traders in recent time windows.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ..common import TradeSignal

logger = logging.getLogger(__name__)

@dataclass
class TraderProfile:
    """Profile of a tracked trader."""
    username: str
    profile_url: str
    recent_pnl: float  # Last N days PnL
    recent_win_rate: float  # Last N days win rate
    total_trades_recent: int  # Trades in recent period
    active_markets: List[str]
    risk_score: float  # 0-1, higher = more risky to counter
    last_updated: datetime

class CounterTradingStrategy:
    """
    Dynamic counter trading strategy that identifies worst performing traders
    in recent time windows and bets against their positions.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.lookback_days = config.get('lookback_days', 30)  # Last 30 days
        self.min_trades = config.get('min_trades', 10)  # Minimum trades to consider
        self.top_traders_count = config.get('top_traders_count', 10)  # Track top 10 worst
        self.update_interval_hours = config.get('update_interval_hours', 24)  # Update daily
        
        # Dynamic trader tracking
        self.tracked_traders: Dict[str, TraderProfile] = {}
        self.last_update = None
        
        # Initialize with some known traders (fallback)
        self._initialize_fallback_traders()
    
    def _initialize_fallback_traders(self):
        """Initialize with known traders as fallback."""
        self.tracked_traders = {
            'SSryjh': TraderProfile(
                username='SSryjh',
                profile_url='https://polymarket.com/@SSryjh',
                recent_pnl=-50000,  # Placeholder - would be fetched
                recent_win_rate=0.35,
                total_trades_recent=25,
                active_markets=['sports'],
                risk_score=0.8,
                last_updated=datetime.now()
            ),
            'sonnyf': TraderProfile(
                username='sonnyf',
                profile_url='https://polymarket.com/@sonnyf',
                recent_pnl=-15000,
                recent_win_rate=0.28,
                total_trades_recent=45,
                active_markets=['politics', 'sports', 'crypto'],
                risk_score=0.7,
                last_updated=datetime.now()
            ),
            'egas': TraderProfile(
                username='egas',
                profile_url='https://polymarket.com/@egas',
                recent_pnl=-3000,
                recent_win_rate=0.32,
                total_trades_recent=15,
                active_markets=['crypto'],
                risk_score=0.6,
                last_updated=datetime.now()
            )
        }

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ..common import TradeSignal

logger = logging.getLogger(__name__)

@dataclass
class TraderProfile:
    """Profile of a tracked trader."""
    username: str
    profile_url: str
    recent_pnl: float  # Last N days PnL
    recent_win_rate: float  # Last N days win rate
    total_trades_recent: int  # Trades in recent period
    active_markets: List[str]
    risk_score: float  # 0-1, higher = more risky to counter
    last_updated: datetime

class CounterTradingStrategy:
    """
    Counter trading strategy that bets against consistently losing traders.
    
    Based on the principle that poor-performing traders often have persistent biases
    that can be systematically exploited.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.lookback_days = config.get('lookback_days', 30)  # Last 30 days
        self.min_trades = config.get('min_trades', 10)  # Minimum trades to consider
        self.top_traders_count = config.get('top_traders_count', 10)  # Track top 10 worst
        self.update_interval_hours = config.get('update_interval_hours', 24)  # Update daily
        
        # Dynamic trader tracking
        self.tracked_traders: Dict[str, TraderProfile] = {}
        self.last_update = None
        
        # Initialize with some known traders (fallback)
        self._initialize_fallback_traders()
    
    def _initialize_fallback_traders(self) -> Dict[str, TraderProfile]:
        """Initialize the list of tracked losing traders (fallback data)."""
        return {
            'SSryjh': TraderProfile(
                username='SSryjh',
                profile_url='https://polymarket.com/@SSryjh',
                recent_pnl=-50000,  # Recent 30-day loss
                recent_win_rate=0.35,
                total_trades_recent=25,
                active_markets=['sports'],
                risk_score=0.8,
                last_updated=datetime.now()
            ),
            'sonnyf': TraderProfile(
                username='sonnyf',
                profile_url='https://polymarket.com/@sonnyf',
                recent_pnl=-15000,
                recent_win_rate=0.28,
                total_trades_recent=45,
                active_markets=['politics', 'sports', 'crypto'],
                risk_score=0.7,
                last_updated=datetime.now()
            ),
            'egas': TraderProfile(
                username='egas',
                profile_url='https://polymarket.com/@egas',
                recent_pnl=-3000,
                recent_win_rate=0.32,
                total_trades_recent=15,
                active_markets=['crypto'],
                risk_score=0.6,
                last_updated=datetime.now()
            )
        }
    
    def analyze_market(self, market_data: Dict) -> List[TradeSignal]:
        """
        Analyze market for counter trading opportunities.
        
        In a real implementation, this would:
        1. Monitor positions of tracked traders in real-time
        2. Detect when they open new positions
        3. Generate counter trades
        
        For now, this is a conceptual framework.
        """
        signals = []
        market_id = market_data['market_id']
        question = market_data.get('question', '').lower()
        
        # Check if any tracked traders are active in this market type
        relevant_traders = self._get_relevant_traders(question)
        
        if not relevant_traders:
            return signals
        
        # In production, this would check real-time trader positions
        # For now, we'll simulate based on market conditions
        
        for trader in relevant_traders:
            signal = self._generate_counter_signal(market_data, trader)
            if signal:
                signals.append(signal)
        
        return signals
    
    def _get_relevant_traders(self, question: str) -> List[TraderProfile]:
        """Get traders who are active in markets matching this question."""
        relevant_traders = []
        
        for trader in self.tracked_traders.values():
            # Check if trader is active in this market type
            if any(market_type in question for market_type in trader.active_markets):
                relevant_traders.append(trader)
        
        return relevant_traders
    
    def _generate_counter_signal(self, market_data: Dict, trader: TraderProfile) -> Optional[TradeSignal]:
        """
        Generate a counter trading signal against a specific trader.
        
        In production, this would analyze the trader's actual position.
        For now, this uses market conditions as a proxy.
        """
        market_id = market_data['market_id']
        yes_price = market_data.get('yes_price', 0)
        no_price = market_data.get('no_price', 0)
        
        if yes_price == 0 or no_price == 0:
            return None
        
        # Counter trading logic based on trader profile
        confidence = self._calculate_counter_confidence(trader)
        
        # Determine which side the losing trader likely favors
        # (This is simplified - real implementation would track actual positions)
        likely_trader_side = self._predict_trader_position(market_data, trader)
        
        if likely_trader_side == 'yes':
            # Counter trade: bet against YES (buy NO)
            action = 'buy_no'
            price = no_price
        elif likely_trader_side == 'no':
            # Counter trade: bet against NO (buy YES)
            action = 'buy_yes'
            price = yes_price
        else:
            return None
        
        size = min(self.config.get('max_size', 25), market_data.get('volume', 0) * 0.005)
        
        return TradeSignal(
            market_id=market_id,
            action=action,
            price=price,
            size=size,
            reason=f'Counter trading {trader.username} ({trader.recent_win_rate:.0%} win rate, ${trader.recent_pnl:,.0f} recent PnL)',
            confidence=confidence
        )
    
    def _calculate_counter_confidence(self, trader: TraderProfile) -> float:
        """Calculate confidence in counter trading this trader."""
        # Base confidence from win rate (lower win rate = higher confidence)
        win_rate_factor = 1 - trader.recent_win_rate  # 0.73 for 27% win rate
        
        # PnL factor (more negative PnL = higher confidence)
        pnl_factor = min(1.0, abs(trader.recent_pnl) / 50000)  # Scale by $50K recent loss
        
        # Trade frequency factor
        trade_factor = min(1.0, trader.total_trades_recent / 50)  # More trades = more confidence
        
        # Risk score factor
        risk_factor = trader.risk_score
        
        # Combined confidence
        confidence = (win_rate_factor * 0.3 + pnl_factor * 0.3 + trade_factor * 0.2 + risk_factor * 0.2)
        
        return min(1.0, confidence)
    
    def _predict_trader_position(self, market_data: Dict, trader: TraderProfile) -> Optional[str]:
        """
        Predict which side a losing trader would take.
        
        This is a simplified model based on common losing trader patterns.
        In production, this would be based on actual position tracking.
        """
        question = market_data.get('question', '').lower()
        yes_price = market_data.get('yes_price', 0)
        no_price = market_data.get('no_price', 0)
        
        # Different traders have different biases
        if trader.username == 'SSryjh':
            # Sports trader with low win rate - often bets favorites
            if 'favorite' in question or 'underdog' in question:
                return 'yes' if 'favorite' in question else 'no'
            # General bias toward "yes" in sports
            return 'yes'
            
        elif trader.username == 'sonnyf':
            # Politics/sports trader - often contrarian
            if yes_price > 0.6:  # Heavy favorite
                return 'no'  # Bets underdog
            elif yes_price < 0.4:  # Heavy underdog
                return 'yes'  # Fades the underdog
            else:
                return 'yes'  # Slight bias
            
        elif trader.username == 'egas':
            # Crypto trader - momentum follower
            if 'crypto' in question or 'bitcoin' in question or 'token' in question:
                # Often follows hype
                return 'yes' if 'launch' in question or 'new' in question else 'no'
        
        # Default: assume they take the more expensive side (overconfidence)
        return 'yes' if yes_price > no_price else 'no'
    
    def analyze_markets(self, markets_df: pd.DataFrame) -> List[TradeSignal]:
        """Analyze multiple markets."""
        all_signals = []
        for _, market in markets_df.iterrows():
            signals = self.analyze_market(market.to_dict())
            all_signals.extend(signals)
        return all_signals
    
    def update_trader_profiles(self):
        """
        Update trader profiles with latest performance data.
        
        In production, this would scrape Polymarket profiles or use API.
        For now, simulates dynamic discovery.
        """
        now = datetime.now()
        if self.last_update and (now - self.last_update).total_seconds() < self.update_interval_hours * 3600:
            return  # Not time to update yet
        
        logger.info("Updating trader profiles...")
        
        # In production, this would:
        # 1. Query Polymarket API for top traders by volume
        # 2. Scrape profile pages for recent performance
        # 3. Filter for traders with poor recent performance
        
        # For now, simulate discovering new bad traders
        self._discover_new_traders()
        
        self.last_update = now
        logger.info(f"Updated {len(self.tracked_traders)} trader profiles")
    
    def _discover_new_traders(self):
        """
        Discover new traders to track.
        
        In production, this would:
        - Query Polymarket for high-volume traders
        - Check their recent performance
        - Add consistently losing traders to tracking list
        """
        # Simulate discovering 7 more bad traders (to reach top 10)
        simulated_traders = [
            ('traderX', -25000, 0.30, 35, ['politics']),
            ('traderY', -18000, 0.25, 28, ['crypto']),
            ('traderZ', -32000, 0.22, 42, ['sports', 'politics']),
            ('badbet1', -12000, 0.35, 22, ['crypto', 'sports']),
            ('loser99', -28000, 0.28, 38, ['politics']),
            ('downward', -21000, 0.32, 31, ['crypto']),
            ('redink', -35000, 0.20, 45, ['sports', 'crypto'])
        ]
        
        for username, pnl, win_rate, trades, markets in simulated_traders:
            if username not in self.tracked_traders:
                self.tracked_traders[username] = TraderProfile(
                    username=username,
                    profile_url=f'https://polymarket.com/@{username}',
                    recent_pnl=pnl,
                    recent_win_rate=win_rate,
                    total_trades_recent=trades,
                    active_markets=markets,
                    risk_score=self._calculate_risk_score(pnl, win_rate, trades),
                    last_updated=datetime.now()
                )
        
        # Keep only top 10 worst performers
        sorted_traders = sorted(
            self.tracked_traders.items(),
            key=lambda x: (x[1].recent_pnl, x[1].recent_win_rate)  # Sort by PnL then win rate
        )
        
        # Keep top 10 worst (most negative PnL)
        self.tracked_traders = dict(sorted_traders[:self.top_traders_count])
    
    def _calculate_risk_score(self, recent_pnl: float, win_rate: float, trade_count: int) -> float:
        """Calculate risk score for a trader (higher = more suitable for counter trading)."""
        # Risk score based on consistency of poor performance
        pnl_score = min(1.0, abs(recent_pnl) / 50000)  # Scale by $50K
        win_rate_score = 1 - win_rate  # Lower win rate = higher score
        volume_score = min(1.0, trade_count / 50)  # More trades = more reliable signal
        
        return (pnl_score * 0.4 + win_rate_score * 0.4 + volume_score * 0.2)