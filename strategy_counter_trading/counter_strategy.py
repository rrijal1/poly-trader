"""
Counter Trading Strategy
Dynamic discovery and trading against consistently losing traders across multiple timeframes.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

from .common import TradeSignal

logger = logging.getLogger(__name__)

@dataclass
class LosingTraderProfile:
    """Profile of a consistently losing trader to counter trade against."""
    address: str
    username: str
    profile_url: str

    # Multi-timeframe loss metrics (all should be negative)
    pnl_7d: float  # 7-day PnL (negative = losing this week)
    pnl_30d: float  # 30-day (1 month) PnL (negative = losing this month)
    pnl_all_time: float  # All-time PnL (negative = never profitable overall)
    win_rate: float  # Overall win rate (should be low, < 0.5)
    total_trades: int  # Total number of trades
    avg_trade_size: float  # Average position size
    wallet_balance: float  # Current wallet balance

    # Risk and confidence metrics for counter trading
    consistency_score: float  # How consistently they lose (higher = more predictable losses)
    loss_severity: float  # Magnitude of losses (for position sizing)
    market_specialization: List[str]  # Markets they perform worst in

    # Counter trading parameters
    wallet_allocation: float  # How much of our counter wallet to allocate against this trader
    max_single_position: float  # Maximum size for any single counter position
    last_updated: datetime

    # Wallet for counter trading this trader
    wallet_private_key: str  # Separate wallet for counter positions against this trader

@dataclass
class WalletConfig:
    """Configuration for a counter trading wallet."""
    strategy_name: str
    trader_address: str
    private_key: str
    total_allocation: float  # Total USDC allocated for counter trading this trader
    available_balance: float  # Current available balance

class DynamicCounterTradingStrategy:
    """
    Dynamic counter trading strategy that discovers and trades against consistently losing traders.

    Identifies traders with negative PnL across all timeframes:
    - 7-day PnL < 0 (losing this week)
    - 30-day PnL < 0 (losing this month)
    - All-time PnL < 0 (never profitable overall)

    Features:
    - Dynamic trader discovery based on multi-timeframe losses
    - Wallet-based position sizing against losing traders
    - Separate wallets for each trader to isolate counter trading risk
    - Continuous performance monitoring and rebalancing
    """

    def __init__(self, config: Dict):
        self.config = config

        # Loss criteria parameters - traders must have negative PnL in ALL timeframes
        self.min_trades = config.get('min_trades', 50)  # Minimum total trades
        self.min_wallet_balance = config.get('min_wallet_balance', 1000)  # Minimum wallet balance

        # Wallet and sizing parameters
        self.total_counter_budget = config.get('total_counter_budget', 5000)  # Total USDC for counter trading
        self.max_traders_to_counter = config.get('max_traders_to_counter', 5)
        self.wallet_rebalance_interval_hours = config.get('wallet_rebalance_interval_hours', 24)

        # Risk management
        self.max_position_vs_wallet = config.get('max_position_vs_wallet', 0.03)  # 3% of our wallet per position (smaller than copy)
        self.max_position_vs_trader_wallet = config.get('max_position_vs_trader_wallet', 0.05)  # 5% of losing trader's wallet
        self.update_interval_hours = config.get('update_interval_hours', 6)  # Update every 6 hours

        # Dynamic losing trader tracking
        self.discovered_traders: Dict[str, LosingTraderProfile] = {}
        self.wallet_configs: Dict[str, WalletConfig] = {}
        self.last_update = None
        self.last_wallet_rebalance = None

        # Initialize with seed losing traders
        self._initialize_seed_traders()

    def _initialize_seed_traders(self):
        """Initialize with known consistently losing traders as seeds."""
        seed_traders = {
            'SSryjh': {
                'address': '0x1234567890123456789012345678901234567890',
                'username': 'SSryjh',
                'profile_url': 'https://polymarket.com/@SSryjh',
                'estimated_wallet_balance': 25000,
                'wallet_allocation': 0.3,  # 30% of counter budget
            },
            'sonnyf': {
                'address': '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd',
                'username': 'sonnyf',
                'profile_url': 'https://polymarket.com/@sonnyf',
                'estimated_wallet_balance': 15000,
                'wallet_allocation': 0.25,  # 25% of counter budget
            }
        }

        for trader_key, trader_data in seed_traders.items():
            # Create wallet for counter trading this trader
            wallet_key = f"COUNTER_{trader_key.upper()}_PRIVATE_KEY"
            wallet_private_key = os.getenv(wallet_key, "")

            if not wallet_private_key:
                logger.warning(f"No wallet configured for counter trading {trader_key}. Set {wallet_key} in environment.")
                continue

            # Initialize trader profile with negative PnL across all timeframes
            trader_profile = LosingTraderProfile(
                address=trader_data['address'],
                username=trader_data['username'],
                profile_url=trader_data['profile_url'],
                pnl_7d=-2500,  # Negative 7-day
                pnl_30d=-8500,  # Negative 30-day
                pnl_all_time=-25000,  # Negative all-time
                win_rate=0.35,  # Low win rate
                total_trades=125,
                avg_trade_size=200,  # Smaller average trades
                wallet_balance=trader_data['estimated_wallet_balance'],
                consistency_score=0.75,  # High consistency in losing
                loss_severity=0.6,  # Moderate loss severity
                market_specialization=['sports', 'politics'],
                wallet_allocation=trader_data['wallet_allocation'],
                max_single_position=self.total_counter_budget * trader_data['wallet_allocation'] * self.max_position_vs_wallet,
                last_updated=datetime.now(),
                wallet_private_key=wallet_private_key
            )

            self.discovered_traders[trader_key] = trader_profile

            # Create wallet config
            wallet_config = WalletConfig(
                strategy_name='counter_trading',
                trader_address=trader_data['address'],
                private_key=wallet_private_key,
                total_allocation=self.total_counter_budget * trader_data['wallet_allocation'],
                available_balance=self.total_counter_budget * trader_data['wallet_allocation']
            )

            self.wallet_configs[trader_key] = wallet_config

        logger.info(f"Initialized dynamic counter trading with {len(self.discovered_traders)} seed losing traders")

    def _should_update_traders(self) -> bool:
        """Check if trader performance should be updated."""
        if self.last_update is None:
            return True
        return (datetime.now() - self.last_update) > timedelta(hours=self.update_interval_hours)

    def _should_rebalance_wallets(self) -> bool:
        """Check if wallets should be rebalanced."""
        if self.last_wallet_rebalance is None:
            return True
        return (datetime.now() - self.last_wallet_rebalance) > timedelta(hours=self.wallet_rebalance_interval_hours)

    def _discover_new_traders(self):
        """
        Discover new consistently losing traders based on multi-timeframe negative PnL.
        Traders must have negative PnL in 7-day, 30-day, and all-time periods.
        """
        logger.info("Discovering new consistently losing traders...")

        # Mock discovery process - in reality would scan Polymarket trader data
        # This would involve:
        # 1. Querying trader performance APIs for multi-timeframe PnL
        # 2. Filtering for negative PnL across all timeframes
        # 3. Ranking by consistency of losses

        mock_discovered_traders = [
            {
                'address': '0x1111111111111111111111111111111111111111',
                'username': 'loser_trader_1',
                'profile_url': 'https://polymarket.com/@loser_trader_1',
                'pnl_7d': -1800,    # Negative 7-day
                'pnl_30d': -6200,   # Negative 30-day
                'pnl_all_time': -18000,  # Negative all-time
                'win_rate': 0.28,
                'total_trades': 89,
                'avg_trade_size': 150,
                'wallet_balance': 12000,
                'consistency_score': 0.82,
                'loss_severity': 0.55,
                'market_specialization': ['crypto', 'defi'],
            },
            {
                'address': '0x2222222222222222222222222222222222222222',
                'username': 'bad_bettor',
                'profile_url': 'https://polymarket.com/@bad_bettor',
                'pnl_7d': -3200,    # Negative 7-day
                'pnl_30d': -9500,   # Negative 30-day
                'pnl_all_time': -32000,   # Negative all-time
                'win_rate': 0.22,
                'total_trades': 134,
                'avg_trade_size': 180,
                'wallet_balance': 8000,
                'consistency_score': 0.78,
                'loss_severity': 0.7,
                'market_specialization': ['sports', 'football'],
            }
        ]

        for trader_data in mock_discovered_traders:
            trader_key = trader_data['username']

            # Skip if already tracking
            if trader_key in self.discovered_traders:
                continue

            # Check if meets multi-timeframe loss criteria
            if (trader_data['pnl_7d'] < 0 and  # Negative 7-day PnL
                trader_data['pnl_30d'] < 0 and  # Negative 30-day PnL
                trader_data['pnl_all_time'] < 0 and  # Negative all-time PnL
                trader_data['total_trades'] >= self.min_trades and  # Minimum trade count
                trader_data['wallet_balance'] >= self.min_wallet_balance):  # Minimum wallet balance

                # Create wallet for counter trading this trader
                wallet_key = f"COUNTER_{trader_key.upper()}_PRIVATE_KEY"
                wallet_private_key = os.getenv(wallet_key, "")

                if not wallet_private_key:
                    logger.warning(f"No wallet configured for counter trading {trader_key}. Skipping.")
                    continue

                # Calculate wallet allocation (distribute remaining budget)
                remaining_allocation = 1.0 - sum(t.wallet_allocation for t in self.discovered_traders.values())
                new_allocation = min(remaining_allocation / 2, 0.2)  # Max 20% for new losing traders

                trader_profile = LosingTraderProfile(
                    address=trader_data['address'],
                    username=trader_data['username'],
                    profile_url=trader_data['profile_url'],
                    pnl_7d=trader_data['pnl_7d'],
                    pnl_30d=trader_data['pnl_30d'],
                    pnl_all_time=trader_data['pnl_all_time'],
                    win_rate=trader_data['win_rate'],
                    total_trades=trader_data['total_trades'],
                    avg_trade_size=trader_data['avg_trade_size'],
                    wallet_balance=trader_data['wallet_balance'],
                    consistency_score=trader_data['consistency_score'],
                    loss_severity=trader_data['loss_severity'],
                    market_specialization=trader_data['market_specialization'],
                    wallet_allocation=new_allocation,
                    max_single_position=self.total_counter_budget * new_allocation * self.max_position_vs_wallet,
                    last_updated=datetime.now(),
                    wallet_private_key=wallet_private_key
                )

                self.discovered_traders[trader_key] = trader_profile

                # Create wallet config
                wallet_config = WalletConfig(
                    strategy_name='counter_trading',
                    trader_address=trader_data['address'],
                    private_key=wallet_private_key,
                    total_allocation=self.total_counter_budget * new_allocation,
                    available_balance=self.total_counter_budget * new_allocation
                )

                self.wallet_configs[trader_key] = wallet_config

                logger.info(f"Discovered and added losing trader: {trader_key} (7d: ${trader_data['pnl_7d']}, 30d: ${trader_data['pnl_30d']}, all-time: ${trader_data['pnl_all_time']})")

        # Remove traders who are no longer consistently losing (positive PnL in any timeframe)
        traders_to_remove = []
        for trader_key, trader in self.discovered_traders.items():
            if (trader.pnl_7d >= 0 or trader.pnl_30d >= 0 or trader.pnl_all_time >= 0):
                traders_to_remove.append(trader_key)

        for trader_key in traders_to_remove:
            del self.discovered_traders[trader_key]
            if trader_key in self.wallet_configs:
                del self.wallet_configs[trader_key]
            logger.info(f"Removed trader who is no longer consistently losing: {trader_key}")

        self.last_update = datetime.now()

    def _update_trader_performance(self):
        """Update performance metrics for tracked losing traders."""
        logger.info("Updating losing trader performance metrics...")

        # In production, this would fetch latest multi-timeframe PnL data
        # For now, we'll simulate performance updates while maintaining negative PnL

        for trader_key, trader in self.discovered_traders.items():
            # Simulate continued losses while maintaining negative PnL across timeframes
            pnl_change_7d = np.random.normal(-0.05, 0.15)  # Mean -5% change, 15% volatility (losses)
            pnl_change_30d = np.random.normal(-0.03, 0.12)  # Mean -3% change, 12% volatility
            pnl_change_all_time = np.random.normal(-0.02, 0.08)  # Mean -2% change, 8% volatility

            # Ensure PnL stays negative (regenerate if positive)
            trader.pnl_7d = max(trader.pnl_7d * (1 + pnl_change_7d), -100)  # Maximum -100 (but keep negative)
            trader.pnl_30d = max(trader.pnl_30d * (1 + pnl_change_30d), -500)  # Maximum -500
            trader.pnl_all_time = max(trader.pnl_all_time * (1 + pnl_change_all_time), -1000)  # Maximum -1K

            trader.win_rate = np.clip(trader.win_rate + np.random.normal(-0.01, 0.05), 0.1, 0.45)  # Keep low win rate
            trader.consistency_score = min(trader.consistency_score + 0.01, 1.0)
            trader.last_updated = datetime.now()

    def _calculate_dynamic_position_size(self, trader: LosingTraderProfile, trader_position_size: float) -> float:
        """
        Calculate position size for counter trading against a losing trader.

        Args:
            trader: The losing trader profile
            trader_position_size: Size of the trader's position we're countering

        Returns:
            Recommended counter position size
        """
        # Get our wallet allocation for counter trading this trader
        our_wallet_allocation = self.wallet_configs[trader.username].available_balance

        # Calculate based on loss severity: more severe losses = larger counter positions
        loss_multiplier = 1 + (trader.loss_severity * 0.5)  # Up to 50% bonus for severe losers

        # Base size: trader_position × wallet_ratio × loss_multiplier
        wallet_ratio = our_wallet_allocation / max(trader.wallet_balance, 1000)  # Avoid division by very small numbers
        wallet_based_size = trader_position_size * wallet_ratio * loss_multiplier

        # Apply risk limits
        max_vs_our_wallet = our_wallet_allocation * self.max_position_vs_wallet
        max_vs_trader_wallet = trader.wallet_balance * self.max_position_vs_trader_wallet

        # Take the minimum of all constraints
        recommended_size = min(
            wallet_based_size,
            max_vs_our_wallet,
            max_vs_trader_wallet,
            trader.max_single_position
        )

        return max(recommended_size, 0)  # Ensure non-negative

    def _get_trader_positions(self, trader_address: str) -> List[Dict]:
        """
        Get current positions for a losing trader to counter.
        In production, this would query Polymarket API for trader's open positions.
        """
        # Mock positions - in reality would fetch from API
        # These represent positions we want to counter
        mock_positions = [
            {
                'market_id': 'sports_market_1',
                'outcome': 'YES',  # Losing trader betting on this
                'size': 1500,  # Position size we're countering
                'entry_price': 0.65,
                'current_price': 0.62,
                'pnl': -45,
                'timestamp': datetime.now() - timedelta(hours=1)
            },
            {
                'market_id': 'politics_market_1',
                'outcome': 'NO',  # Losing trader betting on this
                'size': 1200,
                'entry_price': 0.58,
                'current_price': 0.55,
                'pnl': -36,
                'timestamp': datetime.now() - timedelta(hours=3)
            }
        ]

        return mock_positions

    def analyze_markets(self, markets_df: pd.DataFrame) -> List[TradeSignal]:
        """
        Analyze markets and generate dynamic counter trading signals against losing traders.

        Args:
            markets_df: DataFrame with market data

        Returns:
            List of counter trading signals
        """
        signals = []

        # Update trader discovery and performance if needed
        if self._should_update_traders():
            self._discover_new_traders()
            self._update_trader_performance()

        # Rebalance wallets if needed
        if self._should_rebalance_wallets():
            self._rebalance_wallets()

        # Generate counter signals for each tracked losing trader
        for trader_key, trader in self.discovered_traders.items():
            try:
                # Get trader's current positions to counter
                positions = self._get_trader_positions(trader.address)

                for position in positions:
                    # Check if market exists in our data
                    market_data = markets_df[markets_df['market_id'] == position['market_id']]
                    if market_data.empty:
                        continue

                    market = market_data.iloc[0]

                    # Calculate dynamic counter position size
                    counter_size = self._calculate_dynamic_position_size(trader, position['size'])

                    # Skip if position too small
                    if counter_size < 5:  # Minimum $5 position
                        continue

                    # Only counter recent positions (within last 12 hours for losing traders)
                    position_age = datetime.now() - position['timestamp']
                    if position_age > timedelta(hours=12):
                        continue

                    # Counter trade: bet opposite to the losing trader
                    if position['outcome'] == 'YES':
                        action = 'buy_no'  # Counter YES with NO
                        price = market.get('best_bid_no', market.get('no_price', position['current_price']))
                    else:
                        action = 'buy_yes'  # Counter NO with YES
                        price = market.get('best_bid_yes', market.get('yes_price', position['current_price']))

                    # Calculate confidence based on trader's loss consistency
                    confidence = (
                        trader.consistency_score * 0.4 +
                        trader.loss_severity * 0.3 +
                        (1 - trader.win_rate) * 0.3  # Higher confidence for lower win rates
                    )
                    confidence = min(confidence, 0.85)  # Cap at 85% for counter trading

                    signal = TradeSignal(
                        market_id=position['market_id'],
                        action=action,
                        price=price,
                        size=counter_size,
                        reason=f"Counter trading losing trader {trader.username} (7d: ${trader.pnl_7d:.0f}, 30d: ${trader.pnl_30d:.0f}, all-time: ${trader.pnl_all_time:.0f}, {trader.win_rate:.1%} win rate)",
                        confidence=confidence
                    )

                    signals.append(signal)
                    logger.info(f"Generated counter signal against {trader.username}: ${counter_size:.0f} {action} position")

            except Exception as e:
                logger.error(f"Error analyzing positions for losing trader {trader.username}: {e}")
                continue

        return signals

    def _rebalance_wallets(self):
        """Rebalance wallet allocations based on trader loss consistency."""
        logger.info("Rebalancing counter trading wallet allocations...")

        # Calculate new allocations based on loss consistency (more consistent losers get more allocation)
        total_weight = sum(trader.consistency_score * trader.loss_severity for trader in self.discovered_traders.values())

        for trader_key, trader in self.discovered_traders.items():
            if total_weight > 0:
                # Allocate based on consistency × loss severity
                weight = trader.consistency_score * trader.loss_severity
                new_allocation = weight / total_weight
                new_allocation = np.clip(new_allocation, 0.1, 0.4)  # Min 10%, max 40%
            else:
                new_allocation = 1.0 / len(self.discovered_traders)

            trader.wallet_allocation = new_allocation
            trader.max_single_position = self.total_counter_budget * new_allocation * self.max_position_vs_wallet

            # Update wallet config
            self.wallet_configs[trader_key].total_allocation = self.total_counter_budget * new_allocation

        self.last_wallet_rebalance = datetime.now()
        logger.info("Counter trading wallet rebalancing completed")

    def get_strategy_summary(self) -> Dict:
        """Get comprehensive summary of the dynamic counter trading strategy."""
        return {
            'strategy_type': 'dynamic_counter_trading',
            'total_traders_countered': len(self.discovered_traders),
            'total_counter_budget': self.total_counter_budget,
            'loss_criteria': 'Negative PnL in 7-day, 30-day, and all-time periods',
            'traders': [
                {
                    'username': t.username,
                    'address': t.address,
                    'pnl_7d': t.pnl_7d,
                    'pnl_30d': t.pnl_30d,
                    'pnl_all_time': t.pnl_all_time,
                    'win_rate': t.win_rate,
                    'total_trades': t.total_trades,
                    'wallet_allocation': t.wallet_allocation,
                    'consistency_score': t.consistency_score,
                    'loss_severity': t.loss_severity,
                    'market_specialization': t.market_specialization
                }
                for t in self.discovered_traders.values()
            ],
            'wallet_configs': [
                {
                    'trader': trader_key,
                    'total_allocation': config.total_allocation,
                    'available_balance': config.available_balance
                }
                for trader_key, config in self.wallet_configs.items()
            ],
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'last_wallet_rebalance': self.last_wallet_rebalance.isoformat() if self.last_wallet_rebalance else None
        }