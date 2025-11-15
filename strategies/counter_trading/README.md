# Dynamic Counter Trading Strategy

This strategy dynamically discovers and trades against consistently losing traders across multiple timeframes, using wallet-based position sizing and separate wallets for risk isolation.

## Strategy Overview

The dynamic counter trading strategy continuously scans for traders with negative PnL across all timeframes and automatically allocates capital to bet against their positions. Each losing trader gets their own wallet to isolate counter trading risk and enable precise position sizing.

## Key Features

- **Multi-Timeframe Loss Criteria**: Traders must have negative PnL in 7-day, 30-day, and all-time periods
- **Dynamic Trader Discovery**: Automatically finds consistently losing traders
- **Wallet-Based Position Sizing**: Position sizes based on our allocation vs losing trader's wallet
- **Separate Wallets**: Each trader gets an isolated wallet for risk management
- **Performance-Based Allocation**: Capital allocation based on loss consistency and severity
- **Continuous Rebalancing**: Daily wallet rebalancing based on ongoing loss patterns

## Loss Criteria

Traders are selected based on **strict multi-timeframe loss requirements**:

- **7-Day PnL**: Must be **negative** (losing money this week)
- **30-Day PnL**: Must be **negative** (losing money this month)
- **All-Time PnL**: Must be **negative** (never profitable overall)

**Only traders with negative PnL across ALL timeframes are considered consistently losing.**

## Wallet Architecture

```
Total Counter Budget: $5,000
├── SSryjh Wallet: $1,500 (30% allocation - sports loser)
├── sonnyf Wallet: $1,250 (25% allocation - multi-market loser)
├── loser_trader_1 Wallet: $1,000 (20% allocation - discovered loser)
├── bad_bettor Wallet: $750 (15% allocation - severe loser)
└── other_losers Wallet: $500 (10% allocation - emerging losers)
```

## Position Sizing Logic

For each counter position:
1. **Loss Multiplier**: More severe losses = larger counter positions (up to 50% bonus)
2. **Wallet Ratio**: Calculate our_allocation ÷ losing_trader_wallet_balance
3. **Base Size**: trader_position_size × wallet_ratio × loss_multiplier
4. **Risk Limits**:
   - Max 3% of our wallet per position (smaller than copy trading)
   - Max 5% of losing trader's wallet
   - Max single position limit per trader
5. **Final Size**: Minimum of all constraints

## Currently Tracked Losing Traders

### SSryjh (0x1234567890123456789012345678901234567890)
- **7-Day PnL**: -$2,500 (losing this week)
- **30-Day PnL**: -$8,500 (losing this month)
- **All-Time PnL**: -$25,000 (never profitable)
- **Win Rate**: 35%
- **Wallet Allocation**: 30% ($1,500)
- **Specialization**: Sports markets
- **Loss Severity**: High consistency

### sonnyf (0xabcdefabcdefabcdefabcdefabcdefabcdefabcd)
- **7-Day PnL**: -$1,200 (losing this week)
- **30-Day PnL**: -$4,500 (losing this month)
- **All-Time PnL**: -$15,000 (never profitable)
- **Win Rate**: 28%
- **Wallet Allocation**: 25% ($1,250)
- **Specialization**: Politics, sports, crypto
- **Loss Severity**: Very consistent

### Dynamic Discovery
The system continuously discovers new consistently losing traders like:
- loser_trader_1 (7d: -$1,800, 30d: -$6,200, all-time: -$18,000)
- bad_bettor (7d: -$3,200, 30d: -$9,500, all-time: -$32,000)

## Configuration

```python
'counter': {
    'total_counter_budget': 5000,      # Total USDC for counter trading
    'min_trades': 50,                  # Minimum total trades
    'min_wallet_balance': 1000,        # Minimum wallet balance ($1K)
    'max_traders_to_counter': 5,       # Maximum losing traders to counter
    'max_position_vs_wallet': 0.03,    # 3% of our wallet per position
    'max_position_vs_trader_wallet': 0.05, # 5% of losing trader's wallet
    'wallet_rebalance_interval_hours': 24, # Daily rebalancing
    'update_interval_hours': 6         # Update every 6 hours
}
```

## Environment Variables

Set up separate wallets for each losing trader:
```bash
COUNTER_SSRYJH_PRIVATE_KEY=your_ssryjh_counter_wallet_key
COUNTER_SONNYF_PRIVATE_KEY=your_sonnyf_counter_wallet_key
COUNTER_LOSER_TRADER_1_PRIVATE_KEY=your_loser_trader_1_counter_wallet_key
# ... etc for each losing trader
```

## Risk Management

- **Isolated Wallets**: Each losing trader's counter positions in separate wallets
- **Conservative Sizing**: Smaller position limits than copy trading (3% vs 5%)
- **Loss Validation**: Only counter traders with proven multi-timeframe losses
- **Automatic Removal**: Traders showing positive PnL in any timeframe are removed
- **Rebalancing**: Regular portfolio rebalancing maintains optimal exposure

## How It Works

1. **Discovery Phase**: Scan for traders with negative PnL in all timeframes
2. **Wallet Setup**: Create isolated wallets for each discovered losing trader
3. **Allocation Phase**: Distribute capital based on loss consistency and severity
4. **Position Monitoring**: Track losing trader positions in real-time
5. **Signal Generation**: Create counter signals betting opposite to their positions
6. **Rebalancing**: Adjust allocations based on ongoing loss patterns

## Advantages

- **Strict Criteria**: Only counters traders with proven multi-timeframe losses
- **Risk Isolation**: Separate wallets prevent contagion from losing traders
- **Dynamic Sizing**: Loss severity determines position size automatically
- **Consistent Edge**: Focuses on persistent poor performance patterns
- **Scalable**: Easy to add new losing traders and wallets

## Counter Trading Edge

The strategy exploits systematic biases in losing traders:

- **Overconfidence**: Losing traders often double down on bad positions
- **Recency Bias**: Recent losses often lead to emotional decision-making
- **Pattern Persistence**: Poor traders tend to repeat losing strategies
- **Market Timing**: Many losing traders follow hype cycles rather than fundamentals

By requiring negative PnL across all timeframes, we ensure we're countering truly consistent underperformance rather than temporary setbacks.