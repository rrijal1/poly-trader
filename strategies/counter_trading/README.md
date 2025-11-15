# Counter Trading Strategy

## Overview

The Counter Trading Strategy identifies consistently losing traders on Polymarket and systematically bets against their positions, exploiting behavioral biases and poor decision-making patterns.

## Strategy Logic

### How It Works
- **Trader Tracking**: Monitors performance profiles of identified losing traders
- **Position Prediction**: Predicts which side losing traders will take based on their historical patterns
- **Counter Bets**: Places opposite trades to profit from their expected losses

### Winning Logic
- **Statistical Edge**: Only 13% of Polymarket traders have positive PnL
- **Behavioral Biases**: Losing traders often exhibit persistent, exploitable patterns
- **Contrarian Approach**: Betting against poor performers creates a systematic edge

## Bot Trading Logic

### Trader Selection
1. **Performance Analysis**: Identifies traders with:
   - Consistently negative PnL
   - Low win rates (< 30%)
   - High trading frequency
2. **Market Focus**: Tracks traders active in specific market categories
3. **Risk Scoring**: Assigns confidence scores based on loss magnitude and consistency

### Signal Generation
1. **Market Matching**: Scans for markets where tracked traders are active
2. **Position Prediction**: Uses trader profiles to predict their likely position:
   - **Sports traders**: Often bet favorites or follow hype
   - **Politics traders**: May be contrarian or follow news
   - **Crypto traders**: Follow momentum or project hype

3. **Counter Signal**: Generates opposite trade with calculated confidence

### Trade Execution
1. **Confidence Weighting**: Higher confidence for traders with worse performance
2. **Position Sizing**: Smaller positions due to behavioral strategy nature
3. **Risk Management**: Strict stop losses and position limits

### Example Scenarios
```
Trader Profile: SSryjh
- Win Rate: 27%
- Total PnL: -$3.4M
- Active Markets: Sports

Market: "Will Lakers win vs Warriors?"
Trader likely bets YES (Lakers favorite)
Counter Strategy: Buy NO (bet against Lakers)
```

```
Trader Profile: sonnyf
- Win Rate: 21%
- Total PnL: -$470K
- Active Markets: Politics, Sports

Market: "Will Candidate A win election?"
If Candidate A is heavy favorite (YES $0.75)
Trader likely bets NO (contrarian)
Counter Strategy: Buy YES
```

## Tracked Traders

### SSryjh
- **Profile**: https://polymarket.com/@SSryjh
- **PnL**: -$3.4M
- **Win Rate**: 27%
- **Trades**: 67
- **Focus**: Sports markets
- **Pattern**: Often bets favorites, follows sports hype

### sonnyf
- **Profile**: https://polymarket.com/@sonnyf
- **PnL**: -$470K
- **Win Rate**: 21%
- **Focus**: Politics, sports, crypto
- **Pattern**: Contrarian bets, follows multiple markets

### egas
- **Profile**: https://polymarket.com/@egas
- **PnL**: -$13K
- **Win Rate**: 28%
- **Focus**: Crypto markets
- **Pattern**: Follows token launches and crypto hype

## Configuration
```python
'counter': {
    'max_size': 25  # Smaller positions for behavioral strategy
}
```

## Advantages
- **Statistical Edge**: Exploits the fact that most traders lose money
- **Behavioral Focus**: Captures human biases that algorithms miss
- **Diversified**: Works across different market types

## Technical Implementation Notes

### Current Limitations
- **Conceptual Framework**: Current implementation uses predictive models
- **API Constraints**: Real-time position tracking requires Polymarket API access
- **Privacy Issues**: Individual trader positions may not be publicly exposed

### Production Requirements
- **Real-time Tracking**: API access to trader positions
- **Profile Scraping**: Automated collection of trader statistics
- **Position Monitoring**: WebSocket connections for live position updates

## Risk Management
- **Position Limits**: Smaller sizes due to strategy uncertainty
- **Stop Losses**: Strict loss limits on individual trades
- **Trader Rotation**: Remove traders if performance improves significantly

## Future Enhancements
- **Dynamic Trader Discovery**: Automatically identify new losing traders
- **Machine Learning**: Use ML to predict trader behavior patterns
- **Multi-trader Analysis**: Consider correlations between trader positions
- **Market Impact Analysis**: Account for copy trading and front-running risks