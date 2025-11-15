"""
Order Execution Module for Polymarket Trader
Handles placing, managing, and canceling orders on Polymarket.
"""

import logging
from typing import Dict, List, Optional, Any
import time

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, ApiCreds
from py_clob_client.order_builder.constants import BUY, SELL

from strategies.price_arbitrage.arbitrage import TradeSignal
from .data_collector import DataCollector

logger = logging.getLogger(__name__)

class OrderExecutor:
    """Handles order execution on Polymarket."""
    
    def __init__(self, data_collector: DataCollector):
        self.data_collector = data_collector
        self.client = data_collector.client
    
    def execute_signal(self, signal: TradeSignal) -> Optional[str]:
        """
        Execute a trading signal.
        
        Args:
            signal: Trading signal to execute
            
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            # Handle 'buy_both' action (arbitrage)
            if signal.action == 'buy_both':
                return self._execute_arbitrage_orders(signal)
            
            # Get market data to find token_id
            market_data = self.data_collector.get_market_data(signal.market_id)
            if not market_data:
                logger.error(f"Could not get market data for {signal.market_id}")
                return None
            
            # Extract token_id (assuming it's in market data)
            token_id = self._extract_token_id(market_data, signal.action)
            if not token_id:
                logger.error(f"Could not extract token_id for {signal.market_id}")
                return None
            
            # Determine side
            side = BUY if signal.action.endswith('yes') else SELL
            
            # Create order
            order_args = OrderArgs(
                price=signal.price,
                size=signal.size,
                side=side,
                token_id=token_id
            )
            
            # Create and sign order
            signed_order = self.client.create_order(order_args)
            
            # Post order
            response = self.client.post_order(signed_order, orderType='GTC')
            
            if isinstance(response, dict):
                order_id = response.get('orderID') or response.get('id')
            else:
                order_id = str(response) if response else None
            if order_id:
                logger.info(f"Executed order {order_id} for signal {signal}")
                return str(order_id)
            else:
                logger.error(f"Failed to get order ID from response: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing signal {signal}: {e}")
            return None
    
    def _execute_arbitrage_orders(self, signal: TradeSignal) -> Optional[str]:
        """
        Execute arbitrage orders (both YES and NO sides).
        
        Args:
            signal: Arbitrage signal
            
        Returns:
            Combined order ID string or None
        """
        try:
            # Get market data
            market_data = self.data_collector.get_market_data(signal.market_id)
            if not market_data:
                logger.error(f"Could not get market data for arbitrage {signal.market_id}")
                return None
            
            # Extract both token IDs
            yes_token_id = self._extract_token_id(market_data, 'buy_yes')
            no_token_id = self._extract_token_id(market_data, 'buy_no')
            
            if not yes_token_id or not no_token_id:
                logger.error(f"Could not extract token IDs for arbitrage {signal.market_id}")
                return None
            
            order_ids = []
            
            # Place YES order
            yes_order_args = OrderArgs(
                price=market_data.get('yes_price', 0),
                size=signal.size,
                side=BUY,
                token_id=yes_token_id
            )
            yes_signed = self.client.create_order(yes_order_args)
            yes_response = self.client.post_order(yes_signed, orderType=OrderType.GTC)
            if yes_response:
                if isinstance(yes_response, dict):
                    yes_order_id = yes_response.get('orderID') or yes_response.get('id')
                else:
                    yes_order_id = str(yes_response) if yes_response else None
                if yes_order_id:
                    order_ids.append(str(yes_order_id))
            
            # Place NO order
            no_order_args = OrderArgs(
                price=market_data.get('no_price', 0),
                size=signal.size,
                side=BUY,
                token_id=no_token_id
            )
            no_signed = self.client.create_order(no_order_args)
            no_response = self.client.post_order(no_signed, orderType=OrderType.GTC)
            if no_response:
                if isinstance(no_response, dict):
                    no_order_id = no_response.get('orderID') or no_response.get('id')
                else:
                    no_order_id = str(no_response) if no_response else None
                if no_order_id:
                    order_ids.append(str(no_order_id))
            
            if order_ids:
                combined_id = ','.join(order_ids)
                logger.info(f"Executed arbitrage orders {combined_id} for signal {signal}")
                return combined_id
            else:
                logger.error(f"Failed to execute arbitrage orders for {signal}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing arbitrage signal {signal}: {e}")
            return None
    
    def _extract_token_id(self, market_data: Any, action: str) -> Optional[str]:
        """
        Extract token ID from market data.
        
        Args:
            market_data: Market data dict/object
            action: Trading action
            
        Returns:
            Token ID string
        """
        try:
            # Assuming market_data has tokens or condition_id
            if isinstance(market_data, dict):
                # Look for tokens array
                tokens = market_data.get('tokens', [])
                if tokens:
                    # For yes/no markets, tokens[0] is YES, tokens[1] is NO
                    if action.endswith('yes'):
                        return tokens[0].get('token_id') if len(tokens) > 0 else None
                    else:
                        return tokens[1].get('token_id') if len(tokens) > 1 else None
                
                # Fallback to condition_id
                condition_id = market_data.get('condition_id') or market_data.get('id')
                if condition_id:
                    # For binary markets, token_ids are derived from condition_id
                    # YES: condition_id + "0x000...001"
                    # NO: condition_id + "0x000...002"
                    if action.endswith('yes'):
                        return f"{condition_id}0x0000000000000000000000000000000000000000000000000000000000000001"
                    else:
                        return f"{condition_id}0x0000000000000000000000000000000000000000000000000000000000000002"
            
            # If object, try attributes
            elif hasattr(market_data, 'tokens'):
                tokens = market_data.tokens
                if tokens and len(tokens) >= 2:
                    return tokens[0].token_id if action.endswith('yes') else tokens[1].token_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting token_id: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful
        """
        try:
            response = self.client.cancel_orders([order_id])
            logger.info(f"Cancelled order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return False
    
    def cancel_all_orders(self) -> bool:
        """
        Cancel all open orders.
        
        Returns:
            True if successful
        """
        try:
            response = self.client.cancel_all()
            logger.info("Cancelled all orders")
            return True
        except Exception as e:
            logger.error(f"Error canceling all orders: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Any:
        """
        Get status of an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order status dict or None
        """
        try:
            response = self.client.get_order(order_id)
            return response
        except Exception as e:
            logger.error(f"Error getting order status {order_id}: {e}")
            return None
    
    def get_open_orders(self) -> List[Dict]:
        """
        Get all open orders.
        
        Returns:
            List of open orders
        """
        try:
            from py_clob_client.clob_types import OpenOrderParams
            response = self.client.get_orders(OpenOrderParams())
            if isinstance(response, list):
                return response
            elif isinstance(response, dict):
                return response.get('data', [])
            return []
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return []
    
    def execute_signals_batch(self, signals: List[TradeSignal]) -> List[str]:
        """
        Execute multiple signals in batch.
        
        Args:
            signals: List of trading signals
            
        Returns:
            List of order IDs
        """
        order_ids = []
        
        for signal in signals:
            order_id = self.execute_signal(signal)
            if order_id:
                order_ids.append(order_id)
            
            # Rate limiting
            time.sleep(0.1)
        
        return order_ids
    
    def check_order_fill(self, order_id: str) -> Optional[Dict]:
        """
        Check if order was filled and get fill details.
        
        Args:
            order_id: Order ID
            
        Returns:
            Fill details or None
        """
        status = self.get_order_status(order_id)
        if not status:
            return None
        
        # Parse fill status
        # This would depend on the actual response structure
        return {
            'filled': status.get('status') == 'filled',
            'fill_price': status.get('price', 0),
            'fill_size': status.get('size', 0),
            'remaining': status.get('remaining', 0)
        }