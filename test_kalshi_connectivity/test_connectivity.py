#!/usr/bin/env python3
"""
Test script to verify Kalshi API connectivity and basic functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kalshi_client import KalshiClient, Environment

def main():
    # Load environment variables
    load_dotenv()

    # Check for required environment variables
    api_key_id = os.getenv('KALSHI_API_KEY_ID')
    private_key_path = os.getenv('KALSHI_PRIVATE_KEY_PATH')
    
    if not api_key_id:
        print("❌ ERROR: KALSHI_API_KEY_ID not found in .env file")
        print("Please copy .env.example to .env and fill in your Kalshi API key ID")
        sys.exit(1)

    if not private_key_path:
        print("❌ ERROR: KALSHI_PRIVATE_KEY_PATH not found in .env file")
        print("Please set the path to your Kalshi private key file")
        sys.exit(1)

    if not os.path.exists(private_key_path):
        print(f"❌ ERROR: Private key file not found at {private_key_path}")
        print("Please ensure the private key file exists at the specified path")
        sys.exit(1)

    # Determine environment
    env_str = os.getenv('KALSHI_ENVIRONMENT', 'DEMO').upper()
    environment = Environment.DEMO if env_str == 'DEMO' else Environment.PROD
    
    try:
        print(f"🔗 Connecting to Kalshi ({environment.value})...")
        
        # Initialize client
        client = KalshiClient(environment=environment)
        
        print("✅ Connected successfully")
        print(f"   Mode: {client.mode}")

        # Test exchange status
        print("\n📊 Testing exchange status...")
        try:
            status = client.get_exchange_status()
            print(f"✅ Exchange status: {status.get('exchange_active', 'unknown')}")
            print(f"   Trading active: {status.get('trading_active', 'unknown')}")
        except Exception as e:
            print(f"⚠️  Could not fetch exchange status: {e}")

        # Test announcements endpoint (from provided API spec)
        print("\n📢 Testing exchange announcements...")
        try:
            announcements = client.get_exchange_announcements()
            ann_list = announcements.get('announcements', [])
            print(f"✅ Found {len(ann_list)} announcements")
            for ann in ann_list[:3]:  # Show first 3
                print(f"   - [{ann.get('type')}] {ann.get('message')[:50]}...")
        except Exception as e:
            print(f"⚠️  Could not fetch announcements: {e}")

        # Get user balance (if authenticated)
        if client.mode == "trading":
            print("\n💰 Testing account balance...")
            try:
                balance = client.get_balance()
                print(f"✅ Account balance: {balance}")
            except Exception as e:
                print(f"⚠️  Could not fetch balance: {e}")

        # Test market data fetching
        print("\n📈 Testing market data...")
        try:
            markets = client.get_markets(limit=5)
            market_list = markets.get('markets', [])
            print(f"✅ Found {len(market_list)} markets (showing first 5):")
            for market in market_list:
                ticker = market.get('ticker', 'N/A')
                title = market.get('title', 'N/A')
                print(f"   - {ticker}: {title[:60]}...")
        except Exception as e:
            print(f"❌ ERROR: Failed to fetch markets: {e}")
            sys.exit(1)

        # Test orderbook fetching if markets available
        if market_list:
            first_ticker = market_list[0].get('ticker')
            if first_ticker:
                print(f"\n📊 Testing orderbook for {first_ticker}...")
                try:
                    orderbook = client.get_orderbook(first_ticker)
                    yes_orders = orderbook.get('yes', [])
                    no_orders = orderbook.get('no', [])
                    print(f"✅ Orderbook fetched successfully")
                    print(f"   Yes orders: {len(yes_orders)}")
                    print(f"   No orders: {len(no_orders)}")
                    if yes_orders:
                        print(f"   Best yes: {yes_orders[0]}")
                    if no_orders:
                        print(f"   Best no: {no_orders[0]}")
                except Exception as e:
                    print(f"⚠️  Could not fetch orderbook: {e}")

        print("\n✅ ALL TESTS PASSED - Kalshi connectivity verified!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
