# Dynamic Copy Trading Strategy

This strategy dynamically discovers and follows successful traders on Polymarket, using wallet-based position sizing and separate wallets for risk isolation.

## Strategy Overview

The dynamic copy trading strategy continuously scans for top-performing traders over the last 50 days and automatically allocates capital based on their risk-adjusted performance. Each trader gets their own wallet to isolate risk and enable precise position sizing.

## Key Features

- **Dynamic Trader Discovery**: Automatically finds top performers based on 50-day metrics
- **Wallet-Based Position Sizing**: Position sizes calculated as (our_allocation ÷ trader_wallet) × trader_position
- **Separate Wallets**: Each trader gets an isolated wallet for risk management
- **Performance-Based Allocation**: Capital allocation adjusts based on risk-adjusted returns
- **Continuous Rebalancing**: Daily wallet rebalancing based on performance

## Performance Criteria

Traders are selected based on **strict multi-timeframe profitability requirements**:

- **7-Day PnL**: Must be **positive** (profitable this week)
- **30-Day PnL**: Must be **positive** (profitable this month)
- **All-Time PnL**: Must be **positive** (never lost money overall)
- **Total Trades**: Minimum 50 trades for statistical significance
- **Wallet Balance**: Minimum $1,000 balance to ensure liquidity

**Only traders with positive PnL across ALL timeframes are considered profitable.**

## Wallet Architecture

```
Total Copy Budget: $10,000
├── cqs Wallet: $4,000 (40% allocation)
├── trader_alpha Wallet: $2,500 (25% allocation)
├── trader_beta Wallet: $1,500 (15% allocation)
├── trader_gamma Wallet: $1,000 (10% allocation)
└── trader_delta Wallet: $1,000 (10% allocation)
```

## Position Sizing Logic

For each copied position:
1. **Wallet Ratio**: Calculate our_allocation ÷ trader_wallet_balance
2. **Base Size**: trader_position_size × wallet_ratio
3. **Risk Limits**:
   - Max 5% of our wallet per position
   - Max 10% of trader's wallet
   - Max single position limit per trader
4. **Final Size**: Minimum of all constraints

## Currently Tracked Traders

### cqs (0xdfe3fedc5c7679be42c3d393e99d4b55247b73c4)
- **7-Day PnL**: +$15,000 (positive)
- **30-Day PnL**: +$45,000 (positive)
- **All-Time PnL**: +$464,844 (positive)
- **Win Rate**: 74.3%
- **Total Trades**: 224
- **Wallet Allocation**: 40% ($4,000)
- **Specialization**: Political markets
- **Risk Score**: High consistency

### Dynamic Discovery
The system continuously discovers new traders like:
- trader_alpha (7d: +$2.5K, 30d: +$8.5K, all-time: +$125K)
- trader_beta (7d: +$1.8K, 30d: +$6.2K, all-time: +$78K)

## Configuration

```python
'copy': {
    'total_copy_budget': 10000,        # Total USDC for copy trading
    'min_trades': 50,                  # Minimum total trades
    'min_wallet_balance': 1000,        # Minimum wallet balance ($1K)
    'max_traders_to_follow': 5,        # Maximum traders to track
    'max_position_vs_wallet': 0.05,    # 5% of our wallet limit
    'max_position_vs_trader_wallet': 0.1, # 10% of trader wallet limit
    'wallet_rebalance_interval_hours': 24, # Daily rebalancing
    'update_interval_hours': 6         # Update every 6 hours
}
```

## Environment Variables

Set up separate wallets for each trader:
```bash
COPY_CQS_PRIVATE_KEY=your_cqs_wallet_key
COPY_TRADER_ALPHA_PRIVATE_KEY=your_alpha_wallet_key
# ... etc for each trader
```

## Risk Management

- **Isolated Wallets**: Each trader's positions are in separate wallets
- **Dynamic Allocation**: Capital moves based on performance
- **Position Limits**: Multiple constraints prevent oversized positions
- **Performance Monitoring**: Underperformers are automatically removed
- **Rebalancing**: Regular portfolio rebalancing maintains optimal allocation

## How It Works

1. **Discovery Phase**: Scan for traders meeting performance criteria
2. **Wallet Setup**: Create isolated wallets for each discovered trader
3. **Allocation Phase**: Distribute capital based on risk-adjusted returns
4. **Position Monitoring**: Track trader positions in real-time
5. **Signal Generation**: Create copy signals with wallet-based sizing
6. **Rebalancing**: Adjust allocations based on ongoing performance

## Advantages

- **Dynamic Adaptation**: Automatically finds new successful traders
- **Risk Isolation**: Separate wallets prevent contagion
- **Optimal Sizing**: Wallet ratios ensure appropriate position sizes
- **Performance-Based**: Capital follows success automatically
- **Scalable**: Easy to add new traders and wallets