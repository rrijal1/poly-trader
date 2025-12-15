#!/bin/bash
# Verify the codebase is ready for Kalshi trading

set -e

echo "🔍 Verifying Kalshi Trader Setup..."

# Check Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi
echo "✅ Python 3 found"

# Check required files exist
required_files=(
    "kalshi_client.py"
    "requirements.txt"
    ".env.example"
    "README.md"
    "strategy_price_arbitrage/main.py"
    "strategy_price_arbitrage/common.py"
    "strategy_price_arbitrage/arbitrage.py"
    "test_kalshi_connectivity/test_connectivity.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing file: $file"
        exit 1
    fi
done
echo "✅ All required files present"

# Check for Polymarket references (should be removed)
if grep -r "py-clob-client\|Polymarket" --include="*.py" strategy_*/main.py 2>/dev/null | head -5; then
    echo "⚠️  Found Polymarket references in strategy files (should be Kalshi)"
fi

# Check for Kalshi references
if grep -r "kalshi_client\|KalshiClient" --include="*.py" strategy_*/main.py strategy_*/common.py > /dev/null 2>&1; then
    echo "✅ Kalshi client references found"
else
    echo "❌ No Kalshi client references found"
    exit 1
fi

# Check environment variables
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found (copy from .env.example)"
else
    echo "✅ .env file present"
    
    # Check for required env vars
    if grep -q "KALSHI_API_KEY_ID" .env && grep -q "KALSHI_PRIVATE_KEY_PATH" .env; then
        echo "✅ Required Kalshi environment variables present"
    else
        echo "⚠️  Missing required Kalshi environment variables"
    fi
fi

# Try to import kalshi_client
if python3 -c "import sys; sys.path.insert(0, '.'); from kalshi_client import KalshiClient" 2>/dev/null; then
    echo "✅ kalshi_client module can be imported"
else
    echo "❌ Cannot import kalshi_client module"
    exit 1
fi

# Check requirements can be installed
if pip3 list | grep -q "cryptography\|requests"; then
    echo "✅ Some dependencies already installed"
else
    echo "⚠️  Dependencies may need to be installed (pip install -r requirements.txt)"
fi

echo ""
echo "✅ ALL CHECKS PASSED - Ready for Kalshi Trading!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env: cp .env.example .env"
echo "2. Add your Kalshi API credentials to .env"
echo "3. Test connectivity: cd test_kalshi_connectivity && python test_connectivity.py"
echo "4. Run a strategy: cd strategy_price_arbitrage && python main.py"
