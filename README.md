# Kalshi Trader

Standalone, Railway-ready Kalshi trading strategies using the official Kalshi API.

## Strategies in this repo

- `strategy_price_arbitrage/`: Buys both outcomes when YES + NO is sufficiently below $1.
- `strategy_btc_price_prediction/`: BTC market analysis (simplified for Kalshi).
- `strategy_btc_15m_lag_arb/`: Lag-arb scaffold for monitoring external BTC price vs Kalshi markets.

## How to run

Each strategy folder is self-contained. Pick one:

```bash
cd strategy_price_arbitrage
pip install -r ../requirements.txt
cp ../.env.example .env
# Edit .env with your Kalshi credentials
python main.py
```

## Notes

- This repo does not include copy-trading functionality.
- Trading involves significant risk; test with small sizes first.
- Start with DEMO environment before moving to PROD.

## 🔧 Official API Integration

All strategies use the official Kalshi API patterns:

```python
from kalshi_client import KalshiClient, Environment

# Initialize client
client = KalshiClient(environment=Environment.DEMO)

# Market order execution
result = client.execute_market_order(
    ticker="TICKER",
    side="yes",  # or "no"
    count=10,
    action="buy"
)
```

## 🧪 Verification

Run the test script to ensure everything is set up correctly:

```bash
cd test_kalshi_connectivity
python test_connectivity.py
```

Expected output:

```
✅ ALL TESTS PASSED - Kalshi connectivity verified!
```

## 📊 Monitoring

Each strategy logs:

- Trade signals generated
- Orders executed
- API errors
- Account balances
- Performance metrics

```bash
# View logs locally
python main.py

# View logs on Railway
railway logs --follow
```

## 🛡️ Security

- ✅ **API Keys**: Use dedicated trading API keys with appropriate permissions
- ✅ **Private Keys**: Store RSA private keys securely, never commit to git
- ✅ **Separate keys per strategy** - Risk isolation
- ✅ **Never commit .env** - Use Railway secrets or environment variables
- ✅ **Start small** - Test with minimal capital first
- ✅ **Monitor closely** - Set up alerts
- ✅ **Use DEMO first** - Test thoroughly before using PROD

### Credentials

This repo uses Kalshi API authentication:

- `KALSHI_API_KEY_ID`: Your API key ID from Kalshi
- `KALSHI_PRIVATE_KEY_PATH`: Path to your RSA private key file
- `KALSHI_ENVIRONMENT`: Either "DEMO" or "PROD"

To get your API credentials:

1. Log in to [Kalshi](https://kalshi.com) (or [demo.kalshi.co](https://demo.kalshi.co) for demo)
2. Go to Settings → API Keys
3. Generate a new API key
4. Download the private key file and save it securely
5. Copy the API key ID

## 📈 Scaling

1. **Test locally** - Verify with DEMO environment
2. **Deploy one strategy** - Start with smallest positions
3. **Monitor 24 hours** - Watch logs and P&L
4. **Scale gradually** - Increase positions as confidence grows
5. **Add strategies** - Deploy additional strategies independently

## 🐛 Troubleshooting

### Authentication Error

Check that:

- Your `KALSHI_API_KEY_ID` is correct
- Your private key file exists at `KALSHI_PRIVATE_KEY_PATH`
- The private key format is correct (PEM format)

### Connection Error

- Verify your internet connection
- Check if Kalshi API is accessible
- Ensure you're using the correct environment (DEMO vs PROD)

### Order Execution Issues

- Check account balance
- Verify market is open and tradeable
- Ensure your API key has trading permissions
- Check order size meets market minimums

## 📚 Documentation

- **Kalshi API**: https://trading-api.readme.io/reference/getting-started
- **Kalshi Demo**: https://demo-api.kalshi.co
- **Railway Docs**: https://docs.railway.app

## 🎯 Production Checklist

- [ ] All `.env` files configured with Kalshi credentials
- [ ] API key created and private key downloaded
- [ ] Account funded (if using PROD)
- [ ] Test connectivity script passes
- [ ] Railway deployment configured
- [ ] Monitoring and alerts set up
- [ ] Test trades executed successfully in DEMO

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
- **Multiple Strategies**: ~$20-80/month depending on plan

## 📞 Support

- Railway: https://railway.app/help
- Kalshi: https://kalshi.com/support
- Issues: Open a GitHub issue

## ⚠️ Disclaimer

Trading involves significant risk. This software is for educational purposes only. Use at your own risk. Always:

- Test with DEMO environment first
- Test with small amounts
- Monitor positions closely
- Set appropriate risk limits
- Never invest more than you can afford to lose

## 📄 License

MIT

MIT

---

**Ready to deploy?** Pick a strategy, configure `.env`, and run `python main.py`! 🚀
