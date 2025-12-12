#!/usr/bin/env python3
"""Runner for BTC 15m lag-arb strategy."""

import os
import time
import logging
from dotenv import load_dotenv

from strategy import BTCLagArb, load_config_from_env

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    load_dotenv()
    cfg = load_config_from_env()

    if not cfg.token_up or not cfg.token_down:
        raise SystemExit("Missing PM_TOKEN_ID_UP / PM_TOKEN_ID_DOWN in .env")

    bot = BTCLagArb(cfg)

    logger.info(
        "Starting BTC 15m lag-arb | DRY_RUN=%s | threshold=%.4f | max_usdc=%.2f",
        cfg.dry_run,
        cfg.btc_move_threshold,
        cfg.max_position_usdc,
    )

    # Simple loop. For real HFT, migrate to asyncio + websockets.
    while True:
        start = time.time()
        bot.step()
        elapsed_ms = (time.time() - start) * 1000

        # Sleep to respect polling budget. Use the slower of the two poll intervals.
        target_ms = max(cfg.hl_poll_ms, cfg.pm_poll_ms)
        sleep_ms = max(0.0, target_ms - elapsed_ms)
        time.sleep(sleep_ms / 1000.0)


if __name__ == "__main__":
    main()
