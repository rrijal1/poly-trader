# Range Trading (Long Volatility) — Polymarket

Example market (for context):
- https://polymarket.com/event/bitcoin-price-on-december-19?tid=1765567462403

## What this strategy is

Range markets pay out if the underlying stays **inside** a price band until expiry.

- **YES**: price stays inside the band → *short volatility*
- **NO**: price exits the band in either direction → *long volatility*

The edge you’re looking for: cases where **NO is underpriced** relative to a reasonable estimate of breakout probability.

## Inputs

- Spot price $S$
- Range bounds: lower $L$, upper $U$
- Time to expiry in days: $T$
- Either:
  - options deltas at $L$ and $U$, or
  - implied volatility $IV$

## Step 1 — Estimate breakout probability

### Method A: Options delta shortcut

Use deltas as a probability proxy:

- $\Delta_{call}$ at the **upper** strike $U$
- $\Delta_{put}$ at the **lower** strike $L$

Approximation:

$$P(\text{Breakout}) \approx \Delta_{call} + \Delta_{put}$$
$$P(\text{Inside}) \approx 1 - (\Delta_{call} + \Delta_{put})$$

Trade idea:

- If $P(\text{Breakout})$ is meaningfully higher than the Polymarket **NO** price, **NO** is underpriced.

Example: if $\Delta_{call}+\Delta_{put}=0.60$ but NO costs $0.40$, that’s a large theoretical edge.

### Method B: Expected move from implied volatility

Compute 1-sigma expected move:

$$\text{Expected Move} = S \times IV \times \sqrt{\frac{T}{365}}$$

Example:

- $S=100{,}000$
- $IV=0.60$
- $T=7$

$$\text{Expected Move} \approx 100{,}000 \times 0.60 \times \sqrt{7/365} \approx \pm 8{,}300$$

Interpretation:

- If $[L, U]$ is much tighter than $[S-\text{Move},\, S+\text{Move}]$, breakout risk is high → NO tends to be more attractive.

## Step 2 — Adjust for “fat tails” (crypto reality)

A normal model often underestimates extreme moves.

Practical takeaway:

- Treat the delta/IV estimate as a baseline and be conservative about tail risk (i.e., assume breakout is *more* likely than a naive bell curve suggests).

## Step 3 — Execution checklist

Before trading:

- [ ] You have a current IV/delta snapshot (not stale)
- [ ] Your estimated $P(\text{Breakout})$ beats the market-implied probability by a margin
- [ ] Orderbook liquidity is acceptable (spread + depth)

## Minimal automation spec (the “new strategy”)

If you want to try this as a bot, keep it simple:

1) Choose one range market and its YES/NO token IDs
2) On a schedule, compute $P(\text{Breakout})$ (Method A or B)
3) Fetch the best ask for **NO**
4) Enter **only** if:

$$P(\text{Breakout}) - \text{NO\_ask\_price} \ge \texttt{EDGE\_THRESHOLD}$$

5) Size small and enforce a hard cap

Suggested knobs:

- `EDGE_THRESHOLD` (e.g., 0.03–0.10)
- `MAX_POSITION_USDC`
- `COOLDOWN_SECONDS`
- Exit rule: time-based (e.g., don’t hold past a cutoff), or price-based (sell when NO mean-reverts / edge disappears)

If you tell me which probability method you want (delta vs IV) and the expiry horizon you’re targeting (hours/days/weeks), I can tailor this doc into an exact implementation plan matching the repo’s current tooling (Magic Link creds + `uv` + `poly` venv).
