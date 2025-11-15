# Dynamic Counter Trading Strategy

## Overview

The Dynamic Counter Trading Strategy automatically identifies and tracks the worst performing traders on Polymarket in recent time windows, then systematically bets against their positions to capture behavioral edges.

## Strategy Logic

### How It Works
- **Dynamic Discovery**: Automatically scans for top traders by volume and filters for poor recent performance
- **Time-Window Analysis**: Focuses on last 30 days performance to avoid outlier contamination
- **Adaptive Tracking**: Updates trader list daily to maintain relevance
- **Counter Bets**: Predicts and bets against losing trader positions

### Winning Logic
- **Recent Performance Focus**: Avoids being misled by old losses that traders have recovered from
- **Statistical Edge**: Dynamically selects from the 10 worst performers for maximum edge
- **Behavioral Exploitation**: Captures persistent biases in real-time trading patterns

## Bot Trading Logic

### Trader Discovery Process
1. **Volume Screening**: Identifies high-volume traders (active participants)
2. **Performance Filtering**: Analyzes last 30 days PnL and win rates
3. **Ranking**: Selects top 10 worst performers based on:
   - Recent PnL (most negative)
   - Win rate (lowest)
   - Trade frequency (consistency)

### Signal Generation
1. **Market Matching**: Monitors markets where tracked traders are active
2. **Position Prediction**: Uses trader-specific patterns to predict their trades:
   - **Sports Traders**: Often bet favorites or follow hype
   - **Politics Traders**: Contrarian tendencies with heavy favorites
   - **Crypto Traders**: Momentum followers, especially with new launches

3. **Counter Signals**: Generates opposite trades with confidence weighting

### Dynamic Updates
- **Daily Refresh**: Updates trader performance data every 24 hours
- **List Rotation**: Replaces improved traders with newly discovered poor performers
- **Risk Adjustment**: Recalculates confidence scores based on latest data

### Configuration
```python
'counter': {
    'max_size': 25,                    # Smaller positions for behavioral strategy
    'lookback_days': 30,              # Analyze last 30 days performance
    'min_trades': 10,                 # Minimum trades to consider trader
    'top_traders_count': 10,          # Track top 10 worst performers
    'update_interval_hours': 24       # Update trader list daily
}
```

## Current Tracked Traders

The system dynamically maintains a list of the 10 worst recent performers. Initial seed traders include:

### Core Traders (Historical Analysis)
- **SSryjh**: Sports-focused, recent -$50K performance
- **sonnyf**: Multi-market, recent -$15K performance  
- **egas**: Crypto-focused, recent -$3K performance

### Dynamic Discovery
System automatically discovers and tracks 7 additional poor performers based on:
- Recent 30-day PnL
- Win rate consistency
- Trading volume

## Advantages
- **Adaptive**: Automatically adjusts to changing market conditions
- **Outlier-Proof**: 30-day window excludes old performance anomalies
- **Systematic**: Data-driven selection of counter trading targets
- **Real-Time**: Daily updates maintain strategy relevance

## Technical Implementation

### Data Sources (Production)
- **Polymarket API**: Trader volume and basic statistics
- **Profile Scraping**: Recent performance data from trader profiles
- **Position Monitoring**: Real-time trade tracking (requires API access)

### Current Simulation
- **Fallback Data**: Uses simulated trader performance for development
- **Pattern Recognition**: Implements behavioral prediction models
- **Confidence Scoring**: Multi-factor risk assessment

## Risk Management
- **Time Windows**: 30-day focus prevents outlier distortion
- **Minimum Volume**: Only tracks traders with sufficient activity
- **Position Limits**: Smaller sizes due to behavioral uncertainty
- **Stop Losses**: Strict loss limits on individual counter trades

## Future Enhancements
- **Real-Time Position Tracking**: WebSocket connections for live trader positions
- **Machine Learning Models**: Predictive models for trader behavior patterns
- **Correlation Analysis**: Avoid counter trading correlated trader groups
- **Market Impact Analysis**: Account for copy trading and front-running effects

## Performance Validation
- **Backtesting Framework**: Historical validation of counter trading effectiveness
- **A/B Testing**: Compare static vs dynamic trader selection
- **Risk Metrics**: Sharpe ratio, maximum drawdown, win rate analysis

## Example Workflow
```
Day 1: Discover top 10 worst 30-day performers
Day 2: Monitor their positions in relevant markets
Day 3: Generate counter signals when they trade
Day 4: Update trader list with latest performance
...continues daily with fresh data
```

This dynamic approach ensures the strategy always targets the most currently relevant poor performers, maximizing the behavioral edge while avoiding outdated information.