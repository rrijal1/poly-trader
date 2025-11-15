# Copy Trading Strategy

This strategy follows successful traders on Polymarket and replicates their positions with smaller, risk-managed sizes.

## Strategy Overview

The copy trading strategy identifies high-performing traders and copies their positions with conservative position sizing. This approach leverages the expertise of proven traders while maintaining strict risk controls.

## Key Features

- **Selective Trader Following**: Only follows traders with proven track records (high win rates, significant PnL)
- **Risk Management**: Uses small position sizes (3-5% of the trader's position)
- **Dynamic Updates**: Regularly updates trader performance metrics
- **Confidence Scoring**: Adjusts position sizes based on trader consistency and recent performance

## Currently Tracked Traders

### cqs (0xdfe3fedc5c7679be42c3d393e99d4b55247b73c4)
- **Win Rate**: 74.3%
- **Total PnL**: $464,844
- **Total Trades**: 224
- **Specialization**: Political markets
- **Risk Multiplier**: 3% (conservative sizing)
- **Confidence Score**: 0.85

## Configuration

```python
'copy': {
    'max_copy_size': 10,        # Maximum position size to copy
    'risk_multiplier': 0.05,    # 5% of trader's position size
    'min_win_rate': 0.6,        # Minimum 60% win rate
    'min_trades': 50,          # Minimum trades to consider
    'update_interval_hours': 24 # Update trader stats daily
}
```

## How It Works

1. **Trader Selection**: Identifies traders with strong performance metrics
2. **Position Monitoring**: Tracks the trader's current open positions
3. **Signal Generation**: Creates copy signals for profitable or well-positioned trades
4. **Risk Adjustment**: Applies conservative position sizing and confidence scoring
5. **Execution**: Places orders with appropriate risk management

## Risk Management

- Maximum copy size limits exposure to any single trade
- Risk multipliers ensure positions are much smaller than the original trader
- Confidence scoring adjusts for trader consistency and position performance
- Only copies positions that show positive PnL or good entry prices

## Future Enhancements

- Real-time position tracking via Polymarket API
- Dynamic trader discovery based on performance metrics
- Machine learning-based confidence scoring
- Portfolio diversification across multiple traders
- Stop-loss mechanisms for copied positions