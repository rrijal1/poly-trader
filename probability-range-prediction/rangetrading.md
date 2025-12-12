# Range Trading (Long Volatility) — Polymarket

Example market (for context):

- https://polymarket.com/event/bitcoin-price-on-december-19?tid=1765567462403

## What this strategy is

Polymarket "range" or "bracket" markets pay out based on where the reference price settles **at resolution time** (e.g., BTC price at noon ET on Dec 19).

- **YES**: price is inside $[L, U]$ at settlement → *short volatility*
- **NO**: price is outside $[L, U]$ at settlement → *long volatility*

**Key**: The price can leave and re-enter the bracket during the week—only the **terminal settlement price** matters.

The edge you're looking for: cases where **NO is underpriced** relative to your modeled probability of breakout at $T$.

---

## Inputs

- Current spot price $S_0$
- Range bounds: lower $L$, upper $U$
- Time to expiry in days: $T$
- Annualized volatility $\sigma$ (from either IV or realized vol)

---

## Step 1 — Calculate terminal breakout probability (lognormal model)

Under geometric Brownian motion (GBM), the terminal log-return $X = \ln(S_T / S_0)$ is normally distributed:

$$X \sim \mathcal{N}\!\left(-\tfrac{1}{2}\sigma^2 T,\ \sigma^2 T\right)$$

where $\sigma$ is the annualized volatility and $T$ is time in years.

Then the probability that $S_T$ lands **inside** $[L, U]$ is:

$$P(\text{Inside}) = \Phi\!\left(\frac{\ln(U/S_0) + \tfrac{1}{2}\sigma^2 T}{\sigma\sqrt{T}}\right) - \Phi\!\left(\frac{\ln(L/S_0) + \tfrac{1}{2}\sigma^2 T}{\sigma\sqrt{T}}\right)$$

and the **breakout** probability is:

$$P(\text{Breakout}) = 1 - P(\text{Inside})$$

### Where to get $\sigma$

**Option 1: Implied volatility from options**

- Fetch IV for ATM or near-the-money BTC options with expiry $\approx T$.
- Use that IV directly as $\sigma$.

**Option 2: Realized volatility from historical data**

- Compute annualized standard deviation of daily log-returns over the past $N$ days (e.g., $N=30$):

$$\sigma_{\text{realized}} = \text{std}(\ln(S_t / S_{t-1})) \times \sqrt{365}$$

- For crypto, consider upweighting recent volatility or using a shorter lookback (e.g., 14–21 days).

---

## Step 2 — Compare model probability to market-implied probability

The Polymarket orderbook gives you:

- `YES_price` and `NO_price` (should sum close to 1.00)

The market-implied probabilities are:

$$P_{\text{market}}(\text{Inside}) = \text{YES\_price}$$
$$P_{\text{market}}(\text{Breakout}) = \text{NO\_price}$$

### Edge calculation

Your **theoretical edge** on buying NO is:

$$\text{Edge} = P_{\text{model}}(\text{Breakout}) - \text{NO\_ask\_price}$$

Only enter if:

$$\text{Edge} \ge \texttt{EDGE\_THRESHOLD} + \text{costs}$$

where costs include:

- Spread (bid–ask)
- Polymarket fees (~2% on winnings)
- Slippage if orderbook is thin

---

## Step 3 — Adjust for crypto fat tails

The lognormal model assumes normal log-returns, but BTC exhibits:

- **Fatter tails** (larger moves than normal predicts)
- **Skew** and **jump risk** (especially around major news / liquidation cascades)

Practical adjustments:

1. **Vol bump**: Increase your $\sigma$ estimate by 5–15% (e.g., if IV = 0.60, use 0.63–0.69) to account for tail risk.
2. **Realized vol floor**: Even if recent realized vol is low, don't use $\sigma < 0.50$ for weekly BTC.
3. **Skew check**: If the bracket is asymmetric relative to spot (e.g., $S_0$ near lower bound), options deltas or skew can hint at directional bias—adjust accordingly.

---

## Step 4 — Backtest the right event

Your backtest said "price never stayed in a $2k bracket for a week," but that's probably measuring the **intraweek range** (high/low), not the **settlement price at $T$**.

**Correct backtest metric**:

- For each historical week, record $S_T$ (the BTC price at the exact settlement time/index, e.g., noon ET).
- Check if $L \le S_T \le U$.
- Compute empirical $P(\text{settle inside bracket})$ over many weeks.

Compare that empirical frequency to your lognormal model's $P(\text{Inside})$. If the model systematically underestimates breakouts, add a volatility bump or tail adjustment.

---

## Step 5 — Execution checklist

Before entering:

- [ ] You have a current $\sigma$ estimate (IV or realized vol, adjusted for tails)
- [ ] Your $P_{\text{model}}(\text{Breakout})$ exceeds `NO_ask` by at least `EDGE_THRESHOLD` + costs
- [ ] Orderbook liquidity is acceptable (spread < 2–3%, depth sufficient for your size)
- [ ] You know the exact resolution time/index (e.g., Binance BTC/USD 1-min close at noon ET)
- [ ] Backtest confirms your model isn't systematically biased

---

## Minimal automation spec

If you want to automate this:

1. **Choose a market**: Get the token IDs for YES/NO on a specific bracket (e.g., 90–92k for Dec 19).
2. **Fetch inputs**: Current $S_0$, time to expiry $T$, and $\sigma$ (IV or realized).
3. **Compute $P(\text{Breakout})$**: Use the lognormal formula above.
4. **Fetch orderbook**: Get best ask for NO.
5. **Calculate edge**: $\text{Edge} = P(\text{Breakout}) - \text{NO\_ask}$.
6. **Enter conditionally**:

   ```python
   if Edge >= EDGE_THRESHOLD + estimated_costs:
       place_limit_order(token_id=NO_token, side="BUY", size=position_size, price=NO_ask)
   ```

7. **Risk controls**:
   - `MAX_POSITION_USDC` (e.g., $100–500)
   - `COOLDOWN_SECONDS` (don't spam orders)
   - Exit rule: sell NO if edge disappears or close to expiry

Suggested knobs:

- `EDGE_THRESHOLD`: 0.03–0.10 (3–10%)
- `VOL_ADJUSTMENT`: 1.05–1.15 (multiply $\sigma$ by this to be conservative)
- `MAX_POSITION_USDC`
- `COOLDOWN_SECONDS`

If you want a full Python implementation using the repo's existing `poly` venv + Magic Link creds + `uv`, let me know your preferred vol source (IV vs realized) and I'll build it out.
