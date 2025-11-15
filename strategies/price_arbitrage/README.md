# Price Arbitrage Strategy

## Overview

The Price Arbitrage Strategy identifies and exploits pure arbitrage opportunities in Polymarket prediction markets where the combined price of YES and NO outcomes is less than $1.

## Strategy Logic

### How It Works

- **Market Efficiency**: In efficient markets, YES + NO prices should equal $1
- **Arbitrage Opportunity**: When YES + NO < $1, there's a guaranteed profit opportunity
- **Risk-Free Profit**: By buying both outcomes, you lock in profit regardless of the actual outcome

### Winning Logic

- **Guaranteed Profit**: The strategy profits from market inefficiencies, not from predicting outcomes
- **No Market Risk**: Profit is locked in at the time of trade execution
- **Self-Correcting**: As more traders exploit this, prices adjust back to efficient levels

## Bot Trading Logic

### Signal Generation

1. **Market Scanning**: Bot continuously monitors all active Polymarket prediction markets
2. **Price Analysis**: Calculates YES + NO prices for each market
3. **Threshold Check**: Identifies markets where combined price < $1 (minus small threshold for fees)

### Trade Execution

1. **Position Sizing**: Calculates appropriate position size based on:
   - Available arbitrage profit
   - Portfolio risk limits
   - Market liquidity
2. **Dual Orders**: Places simultaneous orders on both YES and NO sides
3. **Profit Capture**: Locks in the price difference as profit

### Example

```
Market: "Will it rain tomorrow?"
YES price: $0.45
NO price: $0.52
Combined: $0.97

Arbitrage: Buy both sides for $0.97, guaranteed $0.03 profit
```

### Risk Management

- **Portfolio Limits**: Respects maximum exposure limits
- **Position Sizing**: Scales positions based on arbitrage opportunity size
- **Liquidity Checks**: Only trades markets with sufficient volume

### Configuration

```python
'arbitrage': {
    'threshold': 0.01,  # Minimum arbitrage opportunity (1 cent)
    'max_size': 100     # Maximum position size per trade
}
```

## Advantages

- **Risk-Free**: Profit guaranteed at time of execution
- **Market Neutral**: Profits regardless of outcome
- **Automated**: Continuously scans for opportunities 24/7

## Limitations

- **Rare Opportunities**: True arbitrage is uncommon in efficient markets
- **Competition**: Opportunities get arbitraged away quickly
- **Transaction Costs**: Fees can reduce or eliminate small arbitrage profits
