# BTC 15m Lag-Arb Strategy

This strategy watches **Hyperliquid BTC price** vs the **Polymarket CLOB top-of-book** for a 15-minute BTC up/down market. If BTC moves fast but the Polymarket best bid/ask hasn’t updated, it attempts to buy the stale best ask (top-of-book only) and exit once the Polymarket price catches up.

## Setup

```bash
cd strategy_btc_15m_lag_arb
uv pip install -r ../requirements.txt
cp .env.example .env
```

Fill in:

- `PM_PRIVATE_KEY` (Magic Link export)
- `PM_PROXY_ADDRESS` (address under your profile picture)
- `PM_TOKEN_ID_UP`
- `PM_TOKEN_ID_DOWN`

(You can fetch token IDs via Gamma API for the market.)

## Run

```bash
python main.py
```

## Safety

- Default is `DRY_RUN=true`.
- Orders are **FOK** at the **best bid/ask only** to avoid sweeping liquidity.
- Use small `MAX_POSITION_SIZE` and a short `MAX_HOLD_SECONDS`.
