# Polymarket Automated Trading Strategies# Polymarket Multi-Strategy Automated Trader

Production-ready automated trading strategies for Polymarket using official `py-clob-client`. Each strategy is a standalone microservice ready for Railway deployment.An automated trading bot for Polymarket prediction markets that exploits multiple alpha sources:

## 🎯 Strategies1. **Price Arbitrage**: Places trades on both sides when YES + NO < $1

2. **BTC Price Prediction**: Detects mispriced Bitcoin markets based on historical volatility patterns

### 1. **Copy Trading** (`strategy_copy_trading/`)3. **Counter Trading**: Bets against consistently losing traders to capture behavioral edges

Copy trades from consistently profitable traders in real-time.4. **Copy Trading**: Dynamic discovery and following of successful traders with wallet-based position sizing

- **Method**: Monitor via `get_trades(TradeParams(maker_address))`

- **Sizing**: Proportional to wallet ratios## Features

- **Criteria**: Positive PnL across 7d, 30d, all-time

- Real-time market data fetching from Polymarket

### 2. **Price Arbitrage** (`strategy_price_arbitrage/`)- Price arbitrage detection (YES + NO < $1)

Profit when YES + NO prices < $1.- BTC market mispricing detection using historical data

- **Method**: Simultaneous market orders on both outcomes- Automated order execution on both sides

- **Execution**: FOK (Fill or Kill) for immediate fills- Risk management and position sizing

- **Threshold**: 1¢ discrepancy (configurable)- Dry-run mode for testing

### 3. **BTC Prediction** (`strategy_btc_price_prediction/`)## Strategies

Trade BTC markets using volatility analysis.

- **Method**: Compare implied vs historical probabilities### 1. Price Arbitrage Strategy

- **Sizing**: Based on mispricing magnitude

- **Threshold**: 5% mispricingPlaces trades on both sides of markets where the combined price of YES and NO outcomes is less than $1, guaranteeing profit.

### 4. **Counter Trading** (`strategy_counter_trading/`)### 2. BTC Price Prediction Strategy

Fade consistently losing traders.

- **Method**: Real-time monitoring, bet oppositeSpecialized strategy for Bitcoin price prediction markets that:

- **Sizing**: Based on loss consistency and severity

- **Criteria**: Negative PnL across 7d, 30d, all-time- Analyzes historical BTC volatility patterns

- Detects when Polymarket prices don't match actual probability distributions

## 🚀 Quick Start- Exploits short-term market inefficiencies (like the 15-minute windows mentioned in X posts)

### 1. Install Dependencies### 3. Counter Trading Strategy

```bash

pip install -r requirements.txtBehavioral strategy that profits from the consistent mistakes of losing traders:

```

- Tracks performance of identified poor-performing traders

### 2. Choose & Configure a Strategy- Bets against their positions when they trade

````bash- Exploits persistent biases and poor decision-making patterns

cd strategy_copy_trading/

cp .env.example .env### 4. Copy Trading Strategy

# Edit .env with your credentials

```Follows successful traders and replicates their positions with conservative risk management:



### 3. Run- Tracks proven traders with high win rates and significant PnL

```bash- Copies their positions with smaller sizes (3-5% of their position)

python main.py- Currently following: **cqs** (74.3% win rate, $464K+ PnL)

```- Risk-managed approach to leverage expert trader insights



## 📁 Architecture## Setup



Each strategy is **completely self-contained**:1. Clone the repository

2. Create virtual environment: `python -m venv poly`

```3. Activate: `source poly/bin/activate` (macOS/Linux)

strategy_name/4. Install dependencies: `pip install -r requirements.txt`

├── common.py           # Self-contained utilities5. Copy `.env.example` to `.env` and fill in your Polymarket API credentials and wallet private key

├── main.py            # Entry point6. Run the bot: `python -m src.main live --dry-run` (for testing)

├── *_strategy.py      # Strategy logic

├── requirements.txt   # All dependencies## Configuration

└── .env.example       # Environment template

```- Set your Polygon wallet private key in `.env`

- Configure Polymarket API credentials

**No parent directory dependencies!** Each folder can be deployed independently.- Strategy parameters are configured in `src/main.py`



## 🌐 Railway Deployment## Usage



### Deploy a Strategy```bash

```bash# Dry run (recommended first)

cd strategy_copy_trading/python -m src.main live --dry-run

railway init

railway link# Live trading (use with caution)

railway uppython -m src.main live

````

### Environment Variables (Set in Railway Dashboard)## Alpha Opportunities

```bash

# Required for all strategiesThe bot is designed to capture alpha from:

POLYGON_WALLET_PRIVATE_KEY=0x...

CLOB_API_KEY=your_key- Pure arbitrage opportunities (YES + NO < $1)

CLOB_SECRET=your_secret- Mispriced BTC markets where implied probabilities don't match historical patterns

CLOB_PASS_PHRASE=your_passphrase- Behavioral edges from counter trading consistently losing traders

- Expert insights by dynamically following top-performing traders

# Strategy-specific (see .env.example in each folder)- Short-term market inefficiencies that get corrected quickly

MAX_POSITION_SIZE=100- Multi-wallet risk isolation for strategy-specific capital allocation

```

## Disclaimer

### Railway Architecture

```Trading involves significant risk. Use at your own risk. This is for educational purposes. Always test with small amounts first.

Railway Project
├── Service: Copy Trading      → deploys strategy_copy_trading/
├── Service: Price Arbitrage   → deploys strategy_price_arbitrage/
├── Service: BTC Prediction    → deploys strategy_btc_price_prediction/
└── Service: Counter Trading   → deploys strategy_counter_trading/
```

Each service runs independently with its own environment, logs, and scaling.

## ⚡ Performance Optimizations

### Fee Minimization

- ✅ **Market orders only** - No limit order maker fees
- ✅ **FOK execution** - Fill or Kill for immediate execution
- ✅ **No waiting** - Instant fills or cancellation

### Latency Reduction

- ✅ **Direct CLOB integration** - Official `py-clob-client`
- ✅ **Efficient caching** - Minimize redundant API calls
- ✅ **Gamma API** - Fast metadata retrieval

### Code Quality

- ✅ **Mirrors official docs** - Pure `py-clob-client` patterns
- ✅ **Minimal dependencies** - Only what's needed
- ✅ **No bloat** - Clean, production-ready code

## 🔧 Official API Integration

All strategies use official `py-clob-client` patterns:

```python
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import MarketOrderArgs, OrderType, TradeParams

# Market order execution
order_args = MarketOrderArgs(token_id=token_id, amount=amount, side=BUY)
signed_order = client.create_market_order(order_args)
result = client.post_order(signed_order, orderType=OrderType.FOK)

# Real-time trader monitoring
params = TradeParams(maker_address=trader_address)
trades = client.get_trades(params)
```

## 🧪 Verification

Run the verification script to ensure everything is ready:

```bash
./verify_railway_ready.sh
```

Expected output:

```
✅ ALL CHECKS PASSED - Ready for Railway!
```

## 📊 Monitoring

Each strategy logs:

- Trade signals generated
- Orders executed
- API errors
- Wallet balances
- Performance metrics

```bash
# View logs locally
python main.py

# View logs on Railway
railway logs --follow
```

## 🛡️ Security

- ✅ **Agent Wallets**: Trading-only wallets that cannot withdraw funds
- ✅ **Funder Wallets**: Secure wallets holding actual funds
- ✅ **Separate wallets per strategy** - Risk isolation
- ✅ **Never commit .env** - Use Railway secrets
- ✅ **Start small** - Test with minimal capital first
- ✅ **Monitor closely** - Set up alerts

### Agent Wallet Setup

See [`AGENT_WALLET_SETUP.md`](AGENT_WALLET_SETUP.md) for complete trading-only agent wallet configuration.

## 📈 Scaling

1. **Test locally** - Verify with paper trading
2. **Deploy one strategy** - Start with smallest positions
3. **Monitor 24 hours** - Watch logs and P&L
4. **Scale gradually** - Increase positions as confidence grows
5. **Add strategies** - Deploy additional strategies independently

## 🐛 Troubleshooting

### Import Error

```
ModuleNotFoundError: No module named 'common'
```

**Fix**: Ensure `common.py` exists in strategy folder

```bash
ls strategy_copy_trading/common.py  # Should exist
```

### Missing Environment Variables

```
No POLYGON_WALLET_PRIVATE_KEY found
```

**Fix**: Check `.env` file or Railway dashboard variables

### CLOB Connection Error

```
Failed to create API credentials
```

**Fix**:

1. Verify all 4 CLOB variables are set
2. Check wallet has USDC balance
3. Verify API keys are correct

## 📚 Documentation

- **Official py-clob-client**: https://github.com/Polymarket/py-clob-client
- **Polymarket API**: https://docs.polymarket.com
- **Railway Docs**: https://docs.railway.app

## 🎯 Production Checklist

- [ ] All `.env` files configured with real credentials
- [ ] Wallet funded with USDC on Polygon
- [ ] CLOB API keys created and working
- [ ] Token approvals set for trading
- [ ] Railway deployment configured
- [ ] Monitoring and alerts set up
- [ ] Test trades executed successfully
- [ ] Verification script passes

## ⚙️ Railway Commands

```bash
railway init          # Initialize Railway
railway link          # Link to project
railway up            # Deploy
railway logs          # View logs
railway logs --follow # Follow logs
railway variables     # Manage environment variables
railway restart       # Restart service
railway open          # Open dashboard
```

## 💰 Cost Estimation

- **Hobby Plan**: $5/month per service
- **Pro Plan**: $20/month + usage
- **4 Strategies**: ~$20-80/month depending on plan

## 📞 Support

- Railway: https://railway.app/help
- Issues: Open a GitHub issue
- Questions: See documentation links above

## ⚠️ Disclaimer

Trading involves significant risk. This software is for educational purposes only. Use at your own risk. Always:

- Test with small amounts first
- Monitor positions closely
- Set appropriate risk limits
- Never invest more than you can afford to lose

## 📄 License

MIT

---

**Ready to deploy?** Pick a strategy, configure `.env`, and run `python main.py`! 🚀
