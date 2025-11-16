"""
Risk Management Module for Polymarket Trader
Handles position sizing, stop-losses, and portfolio risk controls.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd

from common import TradeSignal

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """Represents a trading position."""
    market_id: str
    side: str  # 'yes' or 'no'
    size: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @property
    def pnl(self) -> float:
        """Calculate current P&L."""
        if self.side == 'yes':
            return (self.current_price - self.entry_price) * self.size
        else:  # no
            return (self.entry_price - self.current_price) * self.size
    
    @property
    def pnl_percent(self) -> float:
        """Calculate P&L as percentage."""
        if self.entry_price == 0:
            return 0
        return self.pnl / (self.entry_price * self.size)

class RiskManager:
    """Manages trading risk and position sizing."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.positions = {}  # market_id -> Position
        self.portfolio_value = config.get('initial_portfolio', 1000)  # in USDC
        self.max_portfolio_risk = config.get('max_portfolio_risk', 0.1)  # 10%
        self.max_single_position = config.get('max_single_position', 0.05)  # 5%
    
    def calculate_position_size(self, signal: TradeSignal, market_data: Dict) -> float:
        """
        Calculate appropriate position size based on risk management rules.
        
        Args:
            signal: Trading signal
            market_data: Current market data
            
        Returns:
            Position size in USDC
        """
        # Base size from signal
        base_size = signal.size
        
        # Risk per trade
        risk_per_trade = self.config.get('risk_per_trade', 0.01)  # 1% of portfolio
        
        # Adjust for confidence
        confidence_multiplier = signal.confidence
        
        # Maximum position size
        max_size = min(
            self.portfolio_value * self.max_single_position,
            self.portfolio_value * risk_per_trade / confidence_multiplier
        )
        
        # Consider market liquidity
        volume = market_data.get('volume', 0)
        liquidity_limit = volume * 0.01  # 1% of 24h volume
        
        # Final size
        position_size = min(base_size, max_size, liquidity_limit)
        
        # Ensure minimum size
        min_size = self.config.get('min_position_size', 10)
        position_size = max(position_size, min_size)
        
        return position_size
    
    def check_portfolio_limits(self, new_position_size: float) -> bool:
        """
        Check if adding this position would exceed portfolio limits.
        
        Args:
            new_position_size: Size of new position
            
        Returns:
            True if within limits
        """
        current_exposure = sum(pos.size for pos in self.positions.values())
        total_exposure = current_exposure + new_position_size
        
        # Check total exposure
        if total_exposure > self.portfolio_value * self.max_portfolio_risk:
            return False
        
        # Check concentration (no single position > max_single_position)
        if new_position_size > self.portfolio_value * self.max_single_position:
            return False
        
        return True
    
    def set_stop_loss(self, signal: TradeSignal, market_data: Dict) -> Optional[float]:
        """
        Calculate stop loss price.
        
        Args:
            signal: Trading signal
            market_data: Market data
            
        Returns:
            Stop loss price or None
        """
        stop_loss_pct = self.config.get('stop_loss_percent', 0.05)  # 5%
        
        if signal.action.startswith('buy_yes'):
            entry_price = signal.price
            return entry_price * (1 - stop_loss_pct)
        elif signal.action.startswith('buy_no'):
            entry_price = market_data.get('no_price', 0)
            return entry_price * (1 + stop_loss_pct)
        
        return None
    
    def set_take_profit(self, signal: TradeSignal, market_data: Dict) -> Optional[float]:
        """
        Calculate take profit price.
        
        Args:
            signal: Trading signal
            market_data: Market data
            
        Returns:
            Take profit price or None
        """
        take_profit_pct = self.config.get('take_profit_percent', 0.1)  # 10%
        
        if signal.action.startswith('buy_yes'):
            entry_price = signal.price
            return entry_price * (1 + take_profit_pct)
        elif signal.action.startswith('buy_no'):
            entry_price = market_data.get('no_price', 0)
            return entry_price * (1 - take_profit_pct)
        
        return None
    
    def should_close_position(self, position: Position, current_price: float) -> Tuple[bool, str]:
        """
        Check if position should be closed.
        
        Args:
            position: Current position
            current_price: Current market price
            
        Returns:
            (should_close, reason)
        """
        # Update current price
        position.current_price = current_price
        
        # Check stop loss
        if position.stop_loss:
            if position.side == 'yes' and current_price <= position.stop_loss:
                return True, f"Stop loss hit: {current_price} <= {position.stop_loss}"
            elif position.side == 'no' and current_price >= position.stop_loss:
                return True, f"Stop loss hit: {current_price} >= {position.stop_loss}"
        
        # Check take profit
        if position.take_profit:
            if position.side == 'yes' and current_price >= position.take_profit:
                return True, f"Take profit hit: {current_price} >= {position.take_profit}"
            elif position.side == 'no' and current_price <= position.take_profit:
                return True, f"Take profit hit: {current_price} <= {position.take_profit}"
        
        # Check max hold time (if configured)
        max_hold_hours = self.config.get('max_hold_hours', 24)
        # Would need timestamp tracking
        
        # Check P&L thresholds
        max_loss_pct = self.config.get('max_loss_percent', 0.1)  # 10%
        if position.pnl_percent <= -max_loss_pct:
            return True, f"Max loss exceeded: {position.pnl_percent:.1%}"
        
        max_profit_pct = self.config.get('max_profit_percent', 0.2)  # 20%
        if position.pnl_percent >= max_profit_pct:
            return True, f"Max profit reached: {position.pnl_percent:.1%}"
        
        return False, ""
    
    def update_positions(self, markets_df: pd.DataFrame):
        """
        Update all positions with current prices and check for closures.
        
        Args:
            markets_df: Current market data
        """
        positions_to_close = []
        
        for market_id, position in self.positions.items():
            # Find current market data
            market_row = markets_df[markets_df['market_id'] == market_id]
            if market_row.empty:
                continue
            
            market_data = market_row.iloc[0]
            current_price = market_data['yes_price'] if position.side == 'yes' else market_data['no_price']
            
            # Check if should close
            should_close, reason = self.should_close_position(position, current_price)
            if should_close:
                positions_to_close.append((market_id, reason))
        
        # Close positions
        for market_id, reason in positions_to_close:
            self.close_position(market_id, reason)
    
    def open_position(self, signal: TradeSignal, market_data: Dict) -> bool:
        """
        Open a new position.
        
        Args:
            signal: Trading signal
            market_data: Market data
            
        Returns:
            True if position opened
        """
        position_size = self.calculate_position_size(signal, market_data)
        
        if not self.check_portfolio_limits(position_size):
            logger.warning(f"Position size {position_size} exceeds portfolio limits")
            return False
        
        # Determine side and prices
        if signal.action == 'buy_yes':
            side = 'yes'
            entry_price = signal.price
        elif signal.action == 'buy_no':
            side = 'no'
            entry_price = market_data.get('no_price', 0)
        else:
            return False
        
        # Create position
        position = Position(
            market_id=signal.market_id,
            side=side,
            size=position_size,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=self.set_stop_loss(signal, market_data),
            take_profit=self.set_take_profit(signal, market_data)
        )
        
        self.positions[signal.market_id] = position
        
        # Update portfolio value (simplified)
        self.portfolio_value -= position_size  # Assuming we use portfolio value
        
        logger.info(f"Opened position: {position}")
        return True
    
    def close_position(self, market_id: str, reason: str):
        """
        Close a position.
        
        Args:
            market_id: Market ID
            reason: Reason for closing
        """
        if market_id not in self.positions:
            return
        
        position = self.positions[market_id]
        
        # Calculate final P&L
        final_pnl = position.pnl
        
        # Update portfolio value
        self.portfolio_value += position.size + final_pnl  # Return capital + P&L
        
        logger.info(f"Closed position {market_id}: P&L {final_pnl:.2f} USDC, Reason: {reason}")
        
        del self.positions[market_id]
    
    def get_portfolio_status(self) -> Dict:
        """Get current portfolio status."""
        total_exposure = sum(pos.size for pos in self.positions.values())
        total_pnl = sum(pos.pnl for pos in self.positions.values())
        
        return {
            'portfolio_value': self.portfolio_value,
            'total_exposure': total_exposure,
            'total_pnl': total_pnl,
            'num_positions': len(self.positions),
            'positions': [vars(pos) for pos in self.positions.values()]
        }