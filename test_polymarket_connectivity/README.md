# Polymarket Connectivity Test

Minimal smoke test to confirm your Magic Link credentials work and that you can fetch an orderbook.

## Quickstart

```bash
cd test_polymarket_connectivity
uv pip install -r ../requirements.txt
cp .env.example .env
python test_orderbook.py
```

## Required `.env`

- `PM_PRIVATE_KEY`: export from https://reveal.magic.link/polymarket
- `PM_PROXY_ADDRESS`: address shown under your profile picture on Polymarket
- `PM_CHAIN_ID`: `137`

Optional (for orderbook fetch):

- `PM_TOKEN_ID_UP`
- `PM_TOKEN_ID_DOWN`
