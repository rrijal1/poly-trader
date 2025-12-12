"""Common utilities for the BTC 15m lag-arb strategy."""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, cast

from py_clob_client.clob_types import OrderBookSummary

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TopOfBook:
    best_bid: Optional[float]
    best_bid_size: Optional[float]
    best_ask: Optional[float]
    best_ask_size: Optional[float]


class OptimizedClobClient:
    """Thin wrapper around `py_clob_client` with helpers used by this strategy."""

    def __init__(self, host: str = "https://clob.polymarket.com", chain_id: int = 137):
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds

        self.host = host
        self.chain_id = chain_id

        # Magic Link / Email login:
        # - PM_PRIVATE_KEY: export from https://reveal.magic.link/polymarket
        # - PM_PROXY_ADDRESS: address shown under your profile picture on Polymarket
        self.private_key = os.getenv("PM_PRIVATE_KEY")
        self.funder = os.getenv("PM_PROXY_ADDRESS")

        if not self.private_key:
            logger.warning("No PM_PRIVATE_KEY found - running in read-only mode")
            self.client = ClobClient(host)
            self.mode = "read-only"
            return

        if self.funder:
            self.client = ClobClient(
                host=host,
                key=self.private_key,
                chain_id=chain_id,
                signature_type=1,
                funder=self.funder,
            )
        else:
            self.client = ClobClient(
                host=host,
                key=self.private_key,
                chain_id=chain_id,
            )

        api_key = os.getenv("CLOB_API_KEY")
        api_secret = os.getenv("CLOB_SECRET")
        api_passphrase = os.getenv("CLOB_PASS_PHRASE")

        if api_key and api_secret and api_passphrase:
            self.client.set_api_creds(ApiCreds(api_key=api_key, api_secret=api_secret, api_passphrase=api_passphrase))
            self.mode = "trading"
        else:
            # Align with official quickstart: derive API creds if not provided.
            try:
                creds = self.client.create_or_derive_api_creds()
                self.client.set_api_creds(creds)
                self.mode = "trading"
            except Exception as e:
                logger.warning(f"Could not derive API creds; trading disabled: {e}")
                self.mode = "l1-only"

        logger.info(f"Initialized CLOB client in {self.mode} mode")

    def get_orderbook(self, token_id: str) -> Optional[OrderBookSummary]:
        try:
            return self.client.get_order_book(token_id)
        except Exception as e:
            logger.error(f"Failed to get orderbook for {token_id}: {e}")
            return None

    @staticmethod
    def top_of_book(ob: OrderBookSummary) -> TopOfBook:
        best_bid = float(ob.bids[-1].price) if ob.bids else None
        best_bid_size = float(ob.bids[-1].size) if ob.bids else None
        best_ask = float(ob.asks[-1].price) if ob.asks else None
        best_ask_size = float(ob.asks[-1].size) if ob.asks else None
        return TopOfBook(best_bid=best_bid, best_bid_size=best_bid_size, best_ask=best_ask, best_ask_size=best_ask_size)

    def place_fok_limit_order(self, *, token_id: str, side: str, size: float, price: float) -> Optional[Dict]:
        """Place a FOK limit order (does not sweep beyond price).

        - `side`: "BUY" or "SELL" (py-clob-client order_builder constants)
        - `size`: shares
        """
        if self.mode != "trading":
            logger.warning("Trading not enabled; cannot place orders")
            return None

        try:
            from py_clob_client.clob_types import OrderArgs, OrderType

            order = self.client.create_order(OrderArgs(token_id=token_id, side=side, size=size, price=price))
            res = self.client.post_order(order, orderType=cast(OrderType, OrderType.FOK))
            return res if isinstance(res, dict) else None
        except Exception as e:
            logger.error(f"Failed to place FOK order: {e}")
            return None


_clob_client: Optional[OptimizedClobClient] = None


def get_clob_client() -> OptimizedClobClient:
    global _clob_client
    if _clob_client is None:
        _clob_client = OptimizedClobClient()
    return _clob_client
