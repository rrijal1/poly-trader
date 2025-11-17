"""
Dynamic Copy Trading Strategy
Real-time trader monitoring and proportional position sizing using Polymarket APIs.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import time

from common import TradeSignal, get_clob_client, OptimizedClobClient

logger = logging.getLogger(__name__)

@dataclass
class DynamicTraderProfile:
    """Dynamic profile of a trader discovered through performance analysis."""
    address: str
    username: str
    profile_url: str

    # Performance metrics across multiple timeframes
    pnl_7d: float  # 7-day PnL
    pnl_30d: float  # 30-day (1 month) PnL
    pnl_all_time: float  # All-time PnL
    recent_win_rate: float  # Overall win rate
    total_trades: int  # Total number of trades
    avg_trade_size: float  # Average position size
    wallet_balance: float  # Current wallet balance (USDC)

    # Risk and confidence metrics
    consistency_score: float  # 0-1, how consistent their performance is
    risk_adjusted_return: float  # Sharpe-like ratio for recent performance
    market_specialization: List[str]  # Markets they perform best in

    # Copy trading parameters
    wallet_allocation: float  # How much of our total copy wallet to allocate to this trader
    max_single_position: float  # Maximum size for any single copied position
    last_updated: datetime

    # Wallet for this trader
    wallet_private_key: str  # Separate wallet for this trader's positions

@dataclass
class WalletConfig:
    """Configuration for a strategy-specific wallet."""
    strategy_name: str
    trader_address: str
    private_key: str
    total_allocation: float  # Total USDC allocated to this wallet
    available_balance: float  # Current available balance

@dataclass
class TraderPosition:
    """Represents a trader's active position."""
    trader_address: str
    token_id: str
    side: str  # BUY/SELL
    size: float
    price: float
    timestamp: datetime
    market_id: str  # Polymarket market identifier

class DynamicCopyTradingStrategy:
    """
    Dynamic copy trading strategy that discovers and follows successful traders.

    Features:
    - Real-time trader monitoring using Polymarket APIs
    - Proportional position sizing based on wallet ratios
    - Separate wallets for each trader to isolate risk
    - Continuous performance monitoring and rebalancing
    """

    def __init__(self, config: Dict):
        self.config = config

        # Initialize optimized CLOB client
        self.client = get_clob_client()

        # Performance tracking parameters - now based on multi-timeframe profitability
        self.min_trades = config.get('min_trades', 50)  # Minimum total trades
        self.min_wallet_balance = config.get('min_wallet_balance', 1000)  # Minimum wallet balance to consider

        # Wallet and sizing parameters
        self.total_copy_budget = config.get('total_copy_budget', 10000)  # Total USDC for copy trading
        self.max_traders_to_follow = config.get('max_traders_to_follow', 5)
        self.wallet_rebalance_interval_hours = config.get('wallet_rebalance_interval_hours', 24)

        # Risk management
        self.max_position_vs_wallet = config.get('max_position_vs_wallet', 0.05)  # 5% of our wallet per position
        self.max_position_vs_trader_wallet = config.get('max_position_vs_trader_wallet', 0.1)  # 10% of trader's wallet
        self.update_interval_seconds = config.get('update_interval_seconds', 30)  # Check every 30 seconds
        self.max_copy_wallet_balance = config.get('max_copy_wallet_balance', 100)  # $100 per copy wallet

        # Dynamic trader tracking
        self.discovered_traders: Dict[str, DynamicTraderProfile] = {}
        self.wallet_configs: Dict[str, WalletConfig] = {}
        self.active_positions: Dict[str, List[TraderPosition]] = {}  # trader_address -> positions
        self.last_update = None
        self.last_wallet_rebalance = None
        self.last_trade_check = {}  # trader_address -> last_check_timestamp

        # Initialize with seed traders and wallets
        self._initialize_seed_traders()

    def _initialize_seed_traders(self):
        """Initialize with known successful traders as seeds for discovery."""
        seed_traders = {
            'cqs': {
                'address': '0xdfe3fedc5c7679be42c3d393e99d4b55247b73c4',
                'username': 'cqs',
                'profile_url': 'https://polymarket.com/@cqs?via=qwerty',
                'estimated_wallet_balance': 500000,  # Estimated based on PnL
                'wallet_allocation': 0.4,  # 40% of copy budget
            },
            'cigarettes': {
                'address': '0xcigarettes123456789012345678901234567890',
                'username': 'cigarettes',
                'profile_url': 'https://polymarket.com/@cigarettes?via=dominatos',
                'estimated_wallet_balance': 300000,  # Estimated based on performance
                'wallet_allocation': 0.3,  # 30% of copy budget
            }
        }

        for trader_key, trader_data in seed_traders.items():
            # Create wallet for this trader
            wallet_key = f"COPY_{trader_key.upper()}_PRIVATE_KEY"
            wallet_private_key = os.getenv(wallet_key, "")

            if not wallet_private_key:
                logger.warning(f"No wallet configured for trader {trader_key}. Set {wallet_key} in environment.")
                continue

            # Initialize trader profile
            trader_profile = DynamicTraderProfile(
                address=trader_data['address'],
                username=trader_data['username'],
                profile_url=trader_data['profile_url'],
                pnl_7d=15000,  # Estimated 7-day PnL
                pnl_30d=45000,  # Estimated 30-day PnL
                pnl_all_time=464844,  # All-time PnL
                recent_win_rate=0.743,  # Will be updated dynamically
                total_trades=224,
                avg_trade_size=2000,  # Estimated
                wallet_balance=trader_data['estimated_wallet_balance'],
                consistency_score=0.85,
                risk_adjusted_return=2.1,
                market_specialization=['politics', 'elections', 'us-politics'],
                wallet_allocation=trader_data['wallet_allocation'],
                max_single_position=self.total_copy_budget * trader_data['wallet_allocation'] * self.max_position_vs_wallet,
                last_updated=datetime.now(),
                wallet_private_key=wallet_private_key
            )

            self.discovered_traders[trader_key] = trader_profile

            # Create wallet config
            wallet_config = WalletConfig(
                strategy_name='copy_trading',
                trader_address=trader_data['address'],
                private_key=wallet_private_key,
                total_allocation=self.max_copy_wallet_balance,  # $100 per wallet
                available_balance=self.max_copy_wallet_balance  # Assume full balance initially
            )

            self.wallet_configs[trader_key] = wallet_config
            self.active_positions[trader_key] = []
            self.last_trade_check[trader_key] = datetime.now() - timedelta(hours=1)  # Start with 1 hour ago

        logger.info(f"Initialized dynamic copy trading with {len(self.discovered_traders)} seed traders")

    def _should_update_traders(self) -> bool:
        """Check if trader performance should be updated."""
        if self.last_update is None:
            return True
        return (datetime.now() - self.last_update) > timedelta(seconds=self.update_interval_seconds)

    def _should_rebalance_wallets(self) -> bool:
        """Check if wallets should be rebalanced."""
        if self.last_wallet_rebalance is None:
            return True
        return (datetime.now() - self.last_wallet_rebalance) > timedelta(hours=self.wallet_rebalance_interval_hours)

    def _discover_new_traders(self):
        """
        Discover new profitable traders based on multi-timeframe profitability.
        Traders must have positive PnL in 7-day, 30-day, and all-time periods.
        """
        logger.info("Discovering new profitable traders...")

        # Mock discovery process - in reality would scan Polymarket trader data
        # This would involve:
        # 1. Querying trader performance APIs for multi-timeframe PnL
        # 2. Filtering for positive PnL across all timeframes
        # 3. Ranking by consistency and total returns

        mock_discovered_traders = [
            {
                'address': '0x1234567890123456789012345678901234567890',
                'username': 'trader_alpha',
                'profile_url': 'https://polymarket.com/@trader_alpha',
                'pnl_7d': 2500,    # Positive 7-day
                'pnl_30d': 8500,   # Positive 30-day
                'pnl_all_time': 125000,  # Positive all-time
                'win_rate': 0.71,
                'total_trades': 89,
                'avg_trade_size': 1500,
                'wallet_balance': 200000,
                'consistency_score': 0.78,
                'risk_adjusted_return': 1.8,
                'market_specialization': ['crypto', 'defi'],
            },
            {
                'address': '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd',
                'username': 'trader_beta',
                'profile_url': 'https://polymarket.com/@trader_beta',
                'pnl_7d': 1800,    # Positive 7-day
                'pnl_30d': 6200,   # Positive 30-day
                'pnl_all_time': 78000,   # Positive all-time
                'win_rate': 0.68,
                'total_trades': 67,
                'avg_trade_size': 1200,
                'wallet_balance': 150000,
                'consistency_score': 0.82,
                'risk_adjusted_return': 2.1,
                'market_specialization': ['sports', 'football'],
            }
        ]

        for trader_data in mock_discovered_traders:
            trader_key = trader_data['username']

            # Skip if already tracking
            if trader_key in self.discovered_traders:
                continue

            # Check if meets multi-timeframe profitability criteria
            if (trader_data['pnl_7d'] > 0 and  # Positive 7-day PnL
                trader_data['pnl_30d'] > 0 and  # Positive 30-day PnL
                trader_data['pnl_all_time'] > 0 and  # Positive all-time PnL
                trader_data['total_trades'] >= self.min_trades and  # Minimum trade count
                trader_data['wallet_balance'] >= self.min_wallet_balance):  # Minimum wallet balance

                # Create wallet for new trader
                wallet_key = f"COPY_{trader_key.upper()}_PRIVATE_KEY"
                wallet_private_key = os.getenv(wallet_key, "")

                if not wallet_private_key:
                    logger.warning(f"No wallet configured for discovered trader {trader_key}. Skipping.")
                    continue

                # Calculate wallet allocation (distribute remaining budget)
                remaining_allocation = 1.0 - sum(t.wallet_allocation for t in self.discovered_traders.values())
                new_allocation = min(remaining_allocation / 2, 0.15)  # Max 15% for new traders

                trader_profile = DynamicTraderProfile(
                    address=trader_data['address'],
                    username=trader_data['username'],
                    profile_url=trader_data['profile_url'],
                    pnl_7d=trader_data['pnl_7d'],
                    pnl_30d=trader_data['pnl_30d'],
                    pnl_all_time=trader_data['pnl_all_time'],
                    recent_win_rate=trader_data['win_rate'],
                    total_trades=trader_data['total_trades'],
                    avg_trade_size=trader_data['avg_trade_size'],
                    wallet_balance=trader_data['wallet_balance'],
                    consistency_score=trader_data['consistency_score'],
                    risk_adjusted_return=trader_data['risk_adjusted_return'],
                    market_specialization=trader_data['market_specialization'],
                    wallet_allocation=new_allocation,
                    max_single_position=self.total_copy_budget * new_allocation * self.max_position_vs_wallet,
                    last_updated=datetime.now(),
                    wallet_private_key=wallet_private_key
                )

                self.discovered_traders[trader_key] = trader_profile

                # Create wallet config
                wallet_config = WalletConfig(
                    strategy_name='copy_trading',
                    trader_address=trader_data['address'],
                    private_key=wallet_private_key,
                    total_allocation=self.max_copy_wallet_balance,  # $100 per wallet
                    available_balance=self.max_copy_wallet_balance
                )

                self.wallet_configs[trader_key] = wallet_config
                self.active_positions[trader_key] = []
                self.last_trade_check[trader_key] = datetime.now() - timedelta(hours=1)

                logger.info(f"Discovered and added new trader: {trader_key} (7d: +${trader_data['pnl_7d']}, 30d: +${trader_data['pnl_30d']}, all-time: +${trader_data['pnl_all_time']})")

        # Remove underperforming traders (those with negative PnL in any timeframe)
        traders_to_remove = []
        for trader_key, trader in self.discovered_traders.items():
            if (trader.pnl_7d <= 0 or trader.pnl_30d <= 0 or trader.pnl_all_time <= 0):
                traders_to_remove.append(trader_key)

        for trader_key in traders_to_remove:
            del self.discovered_traders[trader_key]
            if trader_key in self.wallet_configs:
                del self.wallet_configs[trader_key]
            if trader_key in self.active_positions:
                del self.active_positions[trader_key]
            if trader_key in self.last_trade_check:
                del self.last_trade_check[trader_key]
            logger.info(f"Removed trader with negative PnL in one or more timeframes: {trader_key}")

        self.last_update = datetime.now()

    def _update_trader_performance(self):
        """Update performance metrics for tracked traders."""
        logger.info("Updating trader performance metrics...")

        # In production, this would fetch latest multi-timeframe PnL data
        # For now, we'll simulate performance updates

        for trader_key, trader in self.discovered_traders.items():
            # Simulate slight performance changes while maintaining positive PnL
            pnl_change_7d = np.random.normal(0.02, 0.1)  # 2% mean change, 10% volatility
            pnl_change_30d = np.random.normal(0.015, 0.08)  # 1.5% mean change, 8% volatility
            pnl_change_all_time = np.random.normal(0.01, 0.05)  # 1% mean change, 5% volatility

            # Ensure PnL stays positive (regenerate if negative)
            trader.pnl_7d = max(trader.pnl_7d * (1 + pnl_change_7d), 100)  # Minimum $100
            trader.pnl_30d = max(trader.pnl_30d * (1 + pnl_change_30d), 500)  # Minimum $500
            trader.pnl_all_time = max(trader.pnl_all_time * (1 + pnl_change_all_time), 1000)  # Minimum $1K

            trader.recent_win_rate = np.clip(trader.recent_win_rate + np.random.normal(0, 0.02), 0.5, 0.95)
            trader.consistency_score = min(trader.consistency_score + 0.01, 1.0)
            trader.last_updated = datetime.now()

    def _monitor_trader_activity(self):
        """
        Monitor real-time trader activity using Polymarket APIs.
        Uses get_trades() with TradeParams(maker_address=trader_address) for real-time monitoring.
        """
        logger.info("Monitoring trader activity with real Polymarket APIs...")

        for trader_key, trader in self.discovered_traders.items():
            try:
                # Get last check time for this trader
                last_check = self.last_trade_check.get(trader_key, datetime.now() - timedelta(hours=1))

                # Get recent trades for this trader using official API
                recent_trades = self.client.get_trader_trades(trader.address, limit=20)

                if not recent_trades:
                    continue

                # Process new trades since last check
                new_positions = []
                for trade in recent_trades:
                    trade_time = datetime.fromisoformat(trade.get('timestamp', '').replace('Z', '+00:00'))

                    # Only process trades since last check
                    if trade_time <= last_check:
                        continue

                    # Convert trade to position
                    position = TraderPosition(
                        trader_address=trader.address,
                        token_id=trade.get('asset_id', ''),
                        side='BUY' if trade.get('side', '').upper() == 'BUY' else 'SELL',
                        size=float(trade.get('size', 0)),
                        price=float(trade.get('price', 0)),
                        timestamp=trade_time,
                        market_id=trade.get('market', '')  # May need to map from condition_id
                    )

                    new_positions.append(position)

                # Add new positions to active positions
                if new_positions:
                    self.active_positions[trader_key].extend(new_positions)
                    logger.info(f"Detected {len(new_positions)} new positions for {trader_key}")

                    # Keep only recent positions (last 24 hours)
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    self.active_positions[trader_key] = [
                        p for p in self.active_positions[trader_key]
                        if p.timestamp > cutoff_time
                    ]

                # Update last check time
                self.last_trade_check[trader_key] = datetime.now()

            except Exception as e:
                logger.error(f"Error monitoring trader {trader_key}: {e}")
                continue

    def _calculate_proportional_position_size(self, trader: DynamicTraderProfile, trader_position_size: float) -> float:
        """
        Calculate position size proportional to wallet ratios.
        Formula: (copy_wallet_balance / trader_wallet_balance) * trader_position_size

        Args:
            trader: The trader profile
            trader_position_size: Size of the trader's position

        Returns:
            Recommended position size for copying
        """
        copy_wallet_balance = self.max_copy_wallet_balance  # $100 per wallet

        # Proportional sizing: (our_wallet / trader_wallet) * trader_position
        wallet_ratio = copy_wallet_balance / trader.wallet_balance
        proportional_size = trader_position_size * wallet_ratio

        # Apply risk limits
        max_vs_our_wallet = copy_wallet_balance * self.max_position_vs_wallet  # 5% of our $100
        max_vs_trader_wallet = trader.wallet_balance * self.max_position_vs_trader_wallet  # 10% of trader's wallet

        # Take the minimum of all constraints
        recommended_size = min(
            proportional_size,
            max_vs_our_wallet,
            max_vs_trader_wallet,
            trader.max_single_position
        )

        return max(recommended_size, 0)  # Ensure non-negative

    def analyze_markets(self, markets_df: pd.DataFrame) -> List[TradeSignal]:
        """
        Analyze markets and generate dynamic copy trading signals.

        Args:
            markets_df: DataFrame with market data

        Returns:
            List of trading signals
        """
        signals = []

        # Update trader discovery and performance if needed
        if self._should_update_traders():
            self._discover_new_traders()
            self._update_trader_performance()
            self._monitor_trader_activity()

        # Rebalance wallets if needed
        if self._should_rebalance_wallets():
            self._rebalance_wallets()

        # Generate signals for each tracked trader's active positions
        for trader_key, trader in self.discovered_traders.items():
            try:
                # Get active positions for this trader
                positions = self.active_positions.get(trader_key, [])

                for position in positions:
                    # Check if market exists in our data
                    market_data = markets_df[markets_df['market_id'] == position.market_id]
                    if market_data.empty:
                        continue

                    market = market_data.iloc[0]

                    # Calculate proportional position size
                    copy_size = self._calculate_proportional_position_size(trader, position.size)

                    # Skip if position too small
                    if copy_size < 1:  # Minimum $1 position
                        continue

                    # Only copy recent positions (within last 24 hours)
                    position_age = datetime.now() - position.timestamp
                    if position_age > timedelta(hours=24):
                        continue

                    # Determine action based on trader's position
                    action = f"buy_{position.side.lower()}"

                    # Get token_id for direct CLOB trading
                    token_id = getattr(market, 'token_id', position.token_id)

                    # Calculate confidence based on trader's recent performance
                    confidence = (
                        trader.recent_win_rate * 0.4 +
                        trader.consistency_score * 0.3 +
                        trader.risk_adjusted_return * 0.3
                    )
                    confidence = min(confidence, 0.95)

                    signal = TradeSignal(
                        market_id=position.market_id,
                        action=action,
                        price=market.get('best_bid', position.price),
                        size=copy_size,
                        reason=f"Proportional copy: {trader.username} (${position.size} → ${copy_size:.2f}, ratio: {self.max_copy_wallet_balance/trader.wallet_balance:.4f})",
                        confidence=confidence,
                        token_id=token_id
                    )

                    signals.append(signal)
                    logger.info(f"Generated proportional copy signal for {trader.username}: ${copy_size:.2f} position (from ${position.size})")

            except Exception as e:
                logger.error(f"Error analyzing positions for trader {trader.username}: {e}")
                continue

        return signals

    def _rebalance_wallets(self):
        """Rebalance wallet allocations based on trader performance."""
        logger.info("Rebalancing wallet allocations...")

        # Calculate new allocations based on recent performance
        total_weight = sum(trader.risk_adjusted_return for trader in self.discovered_traders.values())

        for trader_key, trader in self.discovered_traders.items():
            if total_weight > 0:
                # Allocate based on risk-adjusted return
                new_allocation = trader.risk_adjusted_return / total_weight
                new_allocation = np.clip(new_allocation, 0.05, 0.4)  # Min 5%, max 40%
            else:
                new_allocation = 1.0 / len(self.discovered_traders)

            trader.wallet_allocation = new_allocation
            trader.max_single_position = self.total_copy_budget * new_allocation * self.max_position_vs_wallet

            # Update wallet config (each wallet is still $100)
            if trader_key in self.wallet_configs:
                self.wallet_configs[trader_key].total_allocation = self.max_copy_wallet_balance

        self.last_wallet_rebalance = datetime.now()
        logger.info("Wallet rebalancing completed")

    def get_strategy_summary(self) -> Dict:
        """Get comprehensive summary of the dynamic copy trading strategy."""
        return {
            'strategy_type': 'dynamic_copy_trading',
            'total_traders_tracked': len(self.discovered_traders),
            'total_copy_budget': self.total_copy_budget,
            'max_copy_wallet_balance': self.max_copy_wallet_balance,
            'profitability_criteria': 'Positive PnL in 7-day, 30-day, and all-time periods',
            'traders': [
                {
                    'username': t.username,
                    'address': t.address,
                    'pnl_7d': t.pnl_7d,
                    'pnl_30d': t.pnl_30d,
                    'pnl_all_time': t.pnl_all_time,
                    'win_rate': t.recent_win_rate,
                    'total_trades': t.total_trades,
                    'wallet_balance': t.wallet_balance,
                    'copy_wallet_balance': self.max_copy_wallet_balance,
                    'wallet_allocation': t.wallet_allocation,
                    'consistency_score': t.consistency_score,
                    'market_specialization': t.market_specialization,
                    'active_positions': len(self.active_positions.get(t.username, []))
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