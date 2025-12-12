# Polymarket Trader

Standalone, Railway-ready Polymarket strategies using the official `py-clob-client`.

## Strategies in this repo

- `strategy_price_arbitrage/`: Buys both outcomes when YES + NO is sufficiently below $1.
- `strategy_btc_price_prediction/`: BTC market analysis using volatility/conditional-probability heuristics.
- `strategy_btc_15m_lag_arb/`: Lag-arb scaffold using Hyperliquid BTC price vs Polymarket top-of-book.

## How to run

Each strategy folder is self-contained. Pick one:

```bash
cd strategy_price_arbitrage
uv pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Notes

- This repo does not include copy-trading functionality.
- Trading involves significant risk; test with small sizes first.

## 🔧 Official API Integration

All strategies use official `py-clob-client` patterns:

```python
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import MarketOrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY

# Market order execution
order_args = MarketOrderArgs(token_id=token_id, amount=amount, side=BUY)
signed_order = client.create_market_order(order_args)
result = client.post_order(signed_order, orderType=OrderType.FOK)
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
ls strategy_price_arbitrage/common.py
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
