#!/usr/bin/env python3
"""
Dynamic Copy Trading Strategy Runner
Real-time trader monitoring and proportional position sizing using Polymarket APIs.
Standalone runner for Railway deployment.
"""

import os
import sys
import logging
import pandas as pd
import time
from dotenv import load_dotenv

from common import TradeSignal, get_clob_client
from copy_strategy import DynamicCopyTradingStrategy

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function to run the dynamic copy trading strategy."""
    logger.info("Starting Dynamic Copy Trading Strategy with Real-time Monitoring")

    config = {
        'total_copy_budget': float(os.getenv('COPY_TOTAL_BUDGET', '10000')),
        'min_trades': int(os.getenv('COPY_MIN_TRADES', '50')),
        'min_wallet_balance': float(os.getenv('COPY_MIN_WALLET', '1000')),
        'max_traders_to_follow': int(os.getenv('COPY_MAX_TRADERS', '5')),
        'max_position_vs_wallet': float(os.getenv('COPY_MAX_POS_WALLET', '0.05')),
        'max_position_vs_trader_wallet': float(os.getenv('COPY_MAX_POS_TRADER', '0.1')),
        'wallet_rebalance_interval_hours': float(os.getenv('COPY_REBALANCE_HOURS', '24')),
        'update_interval_seconds': float(os.getenv('COPY_UPDATE_SECONDS', '30')),  # Real-time monitoring
        'max_copy_wallet_balance': float(os.getenv('COPY_MAX_WALLET_BALANCE', '100'))  # $100 per copy wallet
    }

    strategy = DynamicCopyTradingStrategy(config)

    # Display initial strategy summary
    summary = strategy.get_strategy_summary()
    logger.info(f"Strategy initialized with {summary['total_traders_tracked']} traders")
    logger.info(f"Total copy budget: ${summary['total_copy_budget']}")
    logger.info(f"Max copy wallet balance: ${summary['max_copy_wallet_balance']}")
    logger.info(f"Profitability criteria: {summary['profitability_criteria']}")

    for trader in summary['traders']:
        logger.info(f"Tracking trader {trader['username']}: "
                   f"7d PnL: +${trader['pnl_7d']}, "
                   f"30d PnL: +${trader['pnl_30d']}, "
                   f"Win rate: {trader['win_rate']:.1%}, "
                   f"Copy wallet: ${trader['copy_wallet_balance']}")

    # Mock market data for testing - in production this would come from Polymarket API
    markets_df = pd.DataFrame({
        'market_id': ['politics_market_1', 'crypto_market_1', 'sports_market_1'],
        'best_bid': [0.48, 0.39, 0.55],
        'best_ask': [0.52, 0.41, 0.59]
    })

    logger.info("Starting real-time trader monitoring loop...")

    try:
        while True:
            # Analyze markets and generate signals
            signals = strategy.analyze_markets(markets_df)

            if signals:
                logger.info(f"Generated {len(signals)} proportional copy trading signals")

                for signal in signals:
                    logger.info(f"Signal: {signal.market_id} - {signal.action} "
                               f"${signal.size:.2f} @ ${signal.price:.3f} "
                               f"(confidence: {signal.confidence:.1%})")
                    logger.info(f"Reason: {signal.reason}")
            else:
                logger.debug("No copy trading signals generated this cycle")

            # Wait before next monitoring cycle
            time.sleep(config['update_interval_seconds'])

    except KeyboardInterrupt:
        logger.info("Shutting down dynamic copy trading strategy")
        final_summary = strategy.get_strategy_summary()
        logger.info(f"Final summary: {len(final_summary['traders'])} traders tracked, "
                   f"${final_summary['total_copy_budget']} total budget")

if __name__ == "__main__":
    main()
