"""Hyperliquid helpers.

This uses the public "info" endpoint to pull a BTC mid/mark-like price.
If you later want true HFT, switch to Hyperliquid websocket market data.
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PriceTick:
    ts_ms: int
    price: float


class HyperliquidClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_btc_price(self, symbol: str = "BTC") -> Optional[PriceTick]:
        """Fetch BTC price from Hyperliquid.

        Uses `POST /info` with type `allMids`.
        """
        try:
            url = f"{self.base_url}/info"
            resp = requests.post(url, json={"type": "allMids"}, timeout=1.5)
            resp.raise_for_status()
            data = resp.json()
            mids = data.get("mids") or {}
            # Some deployments use "BTC"; others use perp symbols. We'll try direct symbol first.
            px = mids.get(symbol)
            if px is None:
                # common perp key is "BTC" on allMids, so if missing, just fail fast.
                return None
            return PriceTick(ts_ms=int(time.time() * 1000), price=float(px))
        except Exception as e:
            logger.error(f"Hyperliquid price fetch failed: {e}")
            return None
