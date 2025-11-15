# BTC Price Prediction Strategy

## Overview

The BTC Price Prediction Strategy specializes in Bitcoin price prediction markets on Polymarket, detecting when market prices don't reflect actual historical probability distributions.

## Strategy Logic

### How It Works
- **Historical Analysis**: Uses Bitcoin's actual price movement patterns from historical data
- **Probability Comparison**: Compares Polymarket's implied probabilities vs. real-world BTC behavior
- **Mispricing Detection**: Identifies markets where prices are significantly off from historical norms

### Winning Logic
- **Statistical Edge**: Profits from markets that misprice short-term BTC movements
- **Volatility Exploitation**: BTC exhibits predictable short-term volatility patterns
- **Market Inefficiency**: Prediction markets sometimes over/underestimate BTC's tendency to move

## Bot Trading Logic

### Signal Generation
1. **Market Identification**: Scans for BTC-related markets (containing "bitcoin", "btc", "up or down")
2. **Price Extraction**: Parses market questions to extract target prices and timeframes
3. **Historical Comparison**: Calculates actual probability of BTC hitting target based on:
   - Historical 15-minute BTC return distributions
   - Current market conditions
   - Target price vs. current price relationship

### Trade Execution
1. **Mispricing Assessment**:
   - Implied probability = YES price (probability market assigns to up move)
   - Actual probability = Historical frequency of similar moves
   - Trade when |implied - actual| > 5% threshold

2. **Directional Trading**:
   - **Buy YES**: When market underestimates upward moves (YES price too low)
   - **Buy NO**: When market overestimates upward moves (YES price too high)

3. **Arbitrage Check**: Also checks for YES + NO < $1 opportunities in BTC markets

### Example Scenario
```
BTC 15-minute market: "Will BTC be above $97,005.79?"
Current BTC: ~$96,142
Market prices: YES $0.18, NO $0.82

Analysis:
- Historical data shows ~50% of 15-min periods have positive returns
- Market implies only 18% chance of up move
- Strategy detects underestimation of upward moves

Action: Buy YES (bet on up move at favorable odds)
```

### Risk Management
- **Confidence Scoring**: Higher confidence for larger mispricings
- **Position Sizing**: Scales based on statistical edge strength
- **Stop Losses**: Automatic position closure on adverse price movements

### Configuration
```python
'btc': {
    'mispricing_threshold': 0.05,  # 5% minimum mispricing
    'arbitrage_threshold': 0.01,   # 1 cent arbitrage threshold
    'max_size': 50                 # Maximum position size
}
```

## Advantages
- **Statistical Edge**: Based on actual BTC behavior patterns
- **Specialized Focus**: Optimized for BTC markets specifically
- **Alpha Capture**: Exploits short-term market inefficiencies before correction

## Market Examples
- **15-minute windows**: Short-term price prediction markets
- **4-hour predictions**: Medium-term directional bets
- **Overnight moves**: End-of-day price targets

## Data Sources
- **Historical BTC Data**: 15-minute return distributions
- **Real-time Prices**: Current BTC market prices (to be integrated)
- **Market Data**: Polymarket API for current pricing

## Limitations
- **Data Quality**: Relies on quality historical BTC data
- **Market Hours**: BTC markets may have different behavior during various market sessions
- **Black Swan Events**: Extreme market conditions can break historical patterns