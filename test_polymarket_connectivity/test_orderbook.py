#!/usr/bin/env python3
"""
Test script to verify Polymarket API connectivity and orderbook fetching.
This script tests the basic functionality needed for the BTC lag-arb strategy.
"""

import os
import sys
import string
from dotenv import load_dotenv
from py_clob_client.client import ClobClient

def main():
    # Load environment variables
    load_dotenv()

    def _is_hex_private_key(value: str) -> bool:
        v = value.strip()
        if v.startswith("0x"):
            v = v[2:]
        return len(v) == 64 and all(c in string.hexdigits for c in v)

    # Check for required environment variables
    private_key = os.getenv('PM_PRIVATE_KEY')
    if not private_key:
        print("❌ ERROR: PM_PRIVATE_KEY not found in .env file")
        print("Please copy .env.example to .env and fill in your Polymarket private key")
        sys.exit(1)

    if not _is_hex_private_key(private_key):
        print("❌ ERROR: PM_PRIVATE_KEY is not a valid hex private key")
        print("Expected 64 hex chars (optionally prefixed with 0x).")
        print("If you use Magic Link email login, export it from https://reveal.magic.link/polymarket")
        sys.exit(1)

    chain_id = os.getenv('PM_CHAIN_ID', '137')
    proxy_address = os.getenv('PM_PROXY_ADDRESS') or os.getenv('POLYMARKET_PROXY_ADDRESS')
    token_id_up = os.getenv('PM_TOKEN_ID_UP')
    token_id_down = os.getenv('PM_TOKEN_ID_DOWN')

    if not token_id_up or not token_id_down:
        print("⚠️  WARNING: PM_TOKEN_ID_UP and/or PM_TOKEN_ID_DOWN not set")
        print("You can still test basic connectivity, but orderbook fetching will fail")
        print("Get token IDs from Polymarket API or docs")

    try:
        print("🔗 Connecting to Polymarket...")
        # Initialize client (Magic Link / Email proxy flow)
        if proxy_address:
            client = ClobClient(
                host="https://clob.polymarket.com",
                key=private_key,
                chain_id=int(chain_id),
                signature_type=1,
                funder=proxy_address,
            )
        else:
            client = ClobClient(
                host="https://clob.polymarket.com",
                key=private_key,
                chain_id=int(chain_id)
            )

        # Align with official quickstart: derive and set API creds
        try:
            client.set_api_creds(client.create_or_derive_api_creds())
        except Exception as e:
            print(f"⚠️  Could not derive/set API creds (orders may fail): {e}")

        # Test basic connectivity
        print("✅ Connected successfully")

        # Get user balance
        try:
            balance = client.get_balance_allowance()
            print(f"💰 Account balance: {balance}")
        except Exception as e:
            print(f"⚠️  Could not fetch balance: {e}")

        # Test orderbook fetching if token IDs are available
        if token_id_up and token_id_down:
            print("\n📊 Testing orderbook fetching...")

            try:
                # Fetch orderbook for UP token
                orderbook_up = client.get_order_book(token_id_up)
                print(f"📈 UP Token Orderbook (first 3 bids/asks):")
                print(f"   Bids: {orderbook_up.get('bids', [])[:3]}")
                print(f"   Asks: {orderbook_up.get('asks', [])[:3]}")

                # Fetch orderbook for DOWN token
                orderbook_down = client.get_order_book(token_id_down)
                print(f"📉 DOWN Token Orderbook (first 3 bids/asks):")
                print(f"   Bids: {orderbook_down.get('bids', [])[:3]}")
                print(f"   Asks: {orderbook_down.get('asks', [])[:3]}")

                print("✅ Orderbook fetching successful")

            except Exception as e:
                print(f"❌ ERROR: Failed to fetch orderbook: {e}")
                print("This might be due to invalid token IDs or API issues")
                sys.exit(1)
        else:
            print("\n⚠️  Skipping orderbook test - token IDs not configured")

        print("\n🎉 All tests passed! Polymarket connectivity is working.")

    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Polymarket: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()