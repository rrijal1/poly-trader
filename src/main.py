#!/usr/bin/env python3
"""
Polymarket Automated Trader
Main entry point for the trading bot.
"""

import os
import sys
import logging
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

#!/usr/bin/env python3
"""
Polymarket Price Arbitrage Trader
Main entry point for the arbitrage trading bot.
"""

import os
import sys
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

from .data_collector import DataCollector
from .risk_manager import RiskManager
from .order_executor import OrderExecutor
from strategies.price_arbitrage.arbitrage import PriceArbitrageStrategy
from strategies.btc_price_prediction.btc_strategy import BTCPricePredictionStrategy
from strategies.counter_trading.counter_strategy import CounterTradingStrategy
from strategies.copy_trading.copy_strategy import DynamicCopyTradingStrategy
from strategies.common import TradeSignal

class PolymarketTrader:
    """Main trader class."""
    
    def __init__(self):
        self.config = {
            'initial_portfolio': 1000,
            'max_portfolio_risk': 0.1,
            'max_single_position': 0.05,
            'risk_per_trade': 0.01,
            'stop_loss_percent': 0.05,
            'take_profit_percent': 0.1,
            'arbitrage': {
                'threshold': 0.01,  # 1 cent arbitrage opportunity
                'max_size': 100
            },
            'btc': {
                'mispricing_threshold': 0.05,  # 5% mispricing
                'arbitrage_threshold': 0.01,   # 1 cent arbitrage
                'max_size': 50
            },
                        'counter': {
                'max_size': 25,  # Smaller positions for behavioral strategy
                'lookback_days': 30,  # Analyze last 30 days performance
                'min_trades': 10,  # Minimum trades to consider trader
                'top_traders_count': 10,  # Track top 10 worst performers
                'update_interval_hours': 24  # Update trader list daily
            },
            'copy': {
                'total_copy_budget': 10000,  # Total USDC for copy trading
                'min_trades': 50,  # Minimum total trades to consider
                'min_wallet_balance': 1000,  # Minimum wallet balance ($1K)
                'max_traders_to_follow': 5,  # Maximum traders to track
                'max_position_vs_wallet': 0.05,  # 5% of our wallet per position
                'max_position_vs_trader_wallet': 0.1,  # 10% of trader's wallet
                'wallet_rebalance_interval_hours': 24,  # Daily rebalancing
                'update_interval_hours': 6  # Update every 6 hours
            }
        }
        
        # Initialize components
        self.data_collector = DataCollector()
        self.arbitrage_strategy = PriceArbitrageStrategy(self.config['arbitrage'])
        self.btc_strategy = BTCPricePredictionStrategy(self.config.get('btc', {}))
        self.counter_strategy = CounterTradingStrategy(self.config.get('counter', {}))
        self.copy_strategy = DynamicCopyTradingStrategy(self.config.get('copy', {}))
        self.risk_manager = RiskManager(self.config)
        self.order_executor = OrderExecutor(self.data_collector)
    
    def run_live_trading(self, dry_run: bool = True):
        """
        Run live trading loop.
        
        Args:
            dry_run: If True, don't execute real orders
        """
        logger.info(f"Starting price arbitrage trading (dry_run={dry_run})")
        
        while True:
            try:
                # Collect market data
                markets_df = self.data_collector.collect_market_data(niches=['sports', 'crypto'])
                
                if markets_df.empty:
                    logger.warning("No market data collected")
                    time.sleep(60)
                    continue
                
                # Update existing positions
                self.risk_manager.update_positions(markets_df)
                
                # Generate trading signals from all strategies
                arb_signals = self.arbitrage_strategy.analyze_markets(markets_df)
                btc_signals = self.btc_strategy.analyze_markets(markets_df)
                counter_signals = self.counter_strategy.analyze_markets(markets_df)
                copy_signals = self.copy_strategy.analyze_markets(markets_df)
                signals = arb_signals + btc_signals + counter_signals + copy_signals
                
                if signals:
                    logger.info(f"Generated {len(signals)} arbitrage signals")
                    
                    for signal in signals:
                        logger.info(f"Signal: {signal}")
                        
                        # Check risk - calculate size and check limits
                        position_size = self.risk_manager.calculate_position_size(signal, markets_df[markets_df['market_id'] == signal.market_id].iloc[0].to_dict() if not markets_df[markets_df['market_id'] == signal.market_id].empty else {})
                        if not self.risk_manager.check_portfolio_limits(position_size):
                            logger.info(f"Risk limit reached, skipping signal")
                            continue
                        
                        if not dry_run:
                            # Execute order
                            order_id = self.order_executor.execute_signal(signal)
                            if order_id:
                                logger.info(f"Executed order {order_id} for {signal}")
                                
                                # Open position in risk manager
                                market_data = markets_df[markets_df['market_id'] == signal.market_id]
                                if not market_data.empty:
                                    self.risk_manager.open_position(signal, market_data.iloc[0].to_dict())
                            else:
                                logger.error(f"Failed to execute order for {signal}")
                        else:
                            logger.info(f"Dry run: Would execute {signal}")
                
                # Log portfolio status
                portfolio_status = self.risk_manager.get_portfolio_status()
                logger.info(f"Portfolio: {portfolio_status}")
                
                # Sleep before next cycle
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(60)

def main():
    """Main function to run the trader."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        trader = PolymarketTrader()
        
        if command == 'live':
            dry_run = '--dry-run' in sys.argv
            trader.run_live_trading(dry_run=dry_run)
        else:
            print("Usage: python src/main.py live [--dry-run]")
    else:
        print("Polymarket Price Arbitrage Trader")
        print("Usage: python src/main.py live [--dry-run]")

if __name__ == "__main__":
    main()