"""BTC 15m lag-arb strategy.

Core idea:
- Track Hyperliquid BTC price (fast external reference)
- Track Polymarket orderbook (best bid/ask) for UP/DOWN tokens
- If BTC moves beyond threshold but PM book hasn't moved, hit the stale top-of-book.

This is a scaffold: it intentionally keeps execution conservative:
- Only top-of-book (FOK limit at best ask/bid)
- Small notional per trade
- Short max holding time
"""

from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass
from typing import Optional, Literal

from py_clob_client.order_builder.constants import BUY, SELL

from common import get_clob_client
from hyperliquid import HyperliquidClient

logger = logging.getLogger(__name__)

Side = Literal["UP", "DOWN"]


@dataclass
class Config:
    pm_market_id: str
    token_up: str
    token_down: str

    hl_base_url: str
    hl_symbol: str

    btc_move_threshold: float
    max_position_usdc: float
    top_of_book_only: bool

    max_hold_seconds: float
    cooldown_seconds: float

    hl_poll_ms: int
    pm_poll_ms: int

    dry_run: bool


@dataclass
class Position:
    side: Side
    token_id: str
    entry_price: float
    entry_ts: float
    size_shares: float


class BTCLagArb:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.clob = get_clob_client()
        self.hl = HyperliquidClient(cfg.hl_base_url)

        self.last_hl_price: Optional[float] = None
        self.last_pm_mid_up: Optional[float] = None
        self.last_pm_mid_down: Optional[float] = None

        self.position: Optional[Position] = None
        self.cooldown_until_ts: float = 0.0

    @staticmethod
    def _mid(best_bid: Optional[float], best_ask: Optional[float]) -> Optional[float]:
        if best_bid is None or best_ask is None:
            return None
        return (best_bid + best_ask) / 2

    def _poll_pm_mid(self, token_id: str) -> Optional[float]:
        ob = self.clob.get_orderbook(token_id)
        if not ob:
            return None
        tob = self.clob.top_of_book(ob)
        return self._mid(tob.best_bid, tob.best_ask)

    def _poll_pm_top(self, token_id: str):
        ob = self.clob.get_orderbook(token_id)
        if not ob:
            return None
        return self.clob.top_of_book(ob)

    def _estimate_shares_for_usdc(self, usdc: float, price: float) -> float:
        # shares ~ usdc / price (since price is $ per share)
        if price <= 0:
            return 0.0
        return usdc / price

    def _enter(self, side: Side, token_id: str, best_ask: float, ask_size: float) -> bool:
        # Buy at the best ask only.
        desired_usdc = float(self.cfg.max_position_usdc)
        size_shares = self._estimate_shares_for_usdc(desired_usdc, best_ask)

        # Optionally clamp to top-of-book size so we truly only take the first level.
        if self.cfg.top_of_book_only and ask_size is not None:
            size_shares = min(size_shares, float(ask_size))

        if size_shares <= 0:
            return False

        if self.cfg.dry_run:
            logger.info(f"[DRY_RUN] ENTER {side}: BUY {size_shares:.4f} @ {best_ask:.4f} token={token_id}")
            self.position = Position(side=side, token_id=token_id, entry_price=best_ask, entry_ts=time.time(), size_shares=size_shares)
            return True

        res = self.clob.place_fok_limit_order(token_id=token_id, side=BUY, size=size_shares, price=best_ask)
        if res:
            logger.info(f"ENTER {side}: BUY {size_shares:.4f} @ {best_ask:.4f} token={token_id} res={res}")
            self.position = Position(side=side, token_id=token_id, entry_price=best_ask, entry_ts=time.time(), size_shares=size_shares)
            return True

        logger.info("Entry failed (not filled at top-of-book)")
        return False

    def _exit(self, best_bid: float, bid_size: Optional[float]) -> bool:
        if not self.position:
            return False

        size_shares = self.position.size_shares
        if self.cfg.top_of_book_only and bid_size is not None:
            size_shares = min(size_shares, float(bid_size))

        if size_shares <= 0:
            return False

        if self.cfg.dry_run:
            pnl_per_share = (best_bid - self.position.entry_price)
            logger.info(f"[DRY_RUN] EXIT {self.position.side}: SELL {size_shares:.4f} @ {best_bid:.4f} (pnl/share={pnl_per_share:.4f})")
            self.position = None
            self.cooldown_until_ts = time.time() + self.cfg.cooldown_seconds
            return True

        res = self.clob.place_fok_limit_order(token_id=self.position.token_id, side=SELL, size=size_shares, price=best_bid)
        if res:
            logger.info(f"EXIT {self.position.side}: SELL {size_shares:.4f} @ {best_bid:.4f} res={res}")
            self.position = None
            self.cooldown_until_ts = time.time() + self.cfg.cooldown_seconds
            return True

        logger.info("Exit failed (not filled at top-of-book)")
        return False

    def step(self) -> None:
        now = time.time()

        # Update Hyperliquid price
        tick = self.hl.get_btc_price(self.cfg.hl_symbol)
        if tick:
            if self.last_hl_price is None:
                self.last_hl_price = tick.price
            hl_ret = (tick.price / self.last_hl_price) - 1.0 if self.last_hl_price else 0.0
        else:
            return

        # Update PM mids (coarser)
        up_mid = self._poll_pm_mid(self.cfg.token_up)
        down_mid = self._poll_pm_mid(self.cfg.token_down)
        if up_mid is None or down_mid is None:
            return

        if self.last_pm_mid_up is None:
            self.last_pm_mid_up = up_mid
        if self.last_pm_mid_down is None:
            self.last_pm_mid_down = down_mid

        pm_ret_proxy = ((up_mid - self.last_pm_mid_up) - (down_mid - self.last_pm_mid_down))

        # If holding a position, try to exit when PM has moved in our direction or when timeouts hit.
        if self.position:
            held_for = now - self.position.entry_ts
            if held_for >= self.cfg.max_hold_seconds:
                logger.info(f"Max hold exceeded ({held_for:.1f}s) -> attempting exit")
                tob = self._poll_pm_top(self.position.token_id)
                if tob and tob.best_bid is not None:
                    self._exit(tob.best_bid, tob.best_bid_size)
                return

            # Simple exit condition: PM mid moved favorably relative to entry.
            tob = self._poll_pm_top(self.position.token_id)
            if not tob or tob.best_bid is None or tob.best_ask is None:
                return

            mid_now = self._mid(tob.best_bid, tob.best_ask)
            if mid_now is None:
                return

            if mid_now > self.position.entry_price:
                self._exit(tob.best_bid, tob.best_bid_size)
            return

        # Not in a position: apply cooldown
        if now < self.cooldown_until_ts:
            return

        # Signal: external move but PM has not (using very simple proxies)
        if abs(hl_ret) < self.cfg.btc_move_threshold:
            return

        # If BTC up violently, expect UP token price to rise -> buy UP if its book hasn't moved much.
        if hl_ret > 0:
            tob = self._poll_pm_top(self.cfg.token_up)
            if not tob or tob.best_ask is None or tob.best_ask_size is None:
                return

            pm_drift = abs(up_mid - self.last_pm_mid_up)
            if pm_drift < (self.cfg.btc_move_threshold * 0.25):
                self._enter("UP", self.cfg.token_up, tob.best_ask, tob.best_ask_size)

        # If BTC down violently, expect DOWN token price to rise -> buy DOWN.
        else:
            tob = self._poll_pm_top(self.cfg.token_down)
            if not tob or tob.best_ask is None or tob.best_ask_size is None:
                return

            pm_drift = abs(down_mid - self.last_pm_mid_down)
            if pm_drift < (self.cfg.btc_move_threshold * 0.25):
                self._enter("DOWN", self.cfg.token_down, tob.best_ask, tob.best_ask_size)

        # Update anchors (very simple)
        self.last_hl_price = tick.price
        self.last_pm_mid_up = up_mid
        self.last_pm_mid_down = down_mid


def load_config_from_env() -> Config:
    return Config(
        pm_market_id=os.getenv("PM_MARKET_ID", ""),
        token_up=os.getenv("PM_TOKEN_ID_UP", ""),
        token_down=os.getenv("PM_TOKEN_ID_DOWN", ""),
        hl_base_url=os.getenv("HL_BASE_URL", "https://api.hyperliquid.xyz"),
        hl_symbol=os.getenv("HL_SYMBOL", "BTC"),
        btc_move_threshold=float(os.getenv("BTC_MOVE_THRESHOLD", "0.0010")),
        max_position_usdc=float(os.getenv("MAX_POSITION_SIZE", "25")),
        top_of_book_only=os.getenv("TOP_OF_BOOK_ONLY", "true").lower() in ("1", "true", "yes"),
        max_hold_seconds=float(os.getenv("MAX_HOLD_SECONDS", "30")),
        cooldown_seconds=float(os.getenv("COOLDOWN_SECONDS", "5")),
        hl_poll_ms=int(os.getenv("HL_POLL_MS", "200")),
        pm_poll_ms=int(os.getenv("PM_POLL_MS", "200")),
        dry_run=os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes"),
    )
