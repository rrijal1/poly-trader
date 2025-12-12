#!/bin/bash
# Verify each strategy is standalone and ready for Railway deployment

echo "🔍 Verifying Railway Deployment Readiness..."
echo ""

STRATEGIES=(
    "strategy_price_arbitrage"
    "strategy_btc_price_prediction"
    "strategy_btc_15m_lag_arb"
)

ALL_PASSED=true

for strategy in "${STRATEGIES[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Checking: $strategy"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check required files exist
    REQUIRED_FILES=("common.py" "main.py" "requirements.txt" ".env.example")
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$strategy/$file" ]; then
            echo "✅ $file exists"
        else
            echo "❌ $file MISSING"
            ALL_PASSED=false
        fi
    done
    
    # Test imports from within the strategy folder
    echo ""
    echo "🧪 Testing imports..."
    cd "$strategy" || exit

    # Prefer uv-managed python when available.
    if command -v uv >/dev/null 2>&1; then
        PYTHON_CMD="uv run python"
    else
        PYTHON_CMD="python3"
    fi
    
    if $PYTHON_CMD -c "from common import get_clob_client, OptimizedClobClient; print('✅ Imports successful')" 2>&1; then
        :
    else
        echo "❌ Import test FAILED"
        ALL_PASSED=false
    fi
    
    cd .. || exit
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$ALL_PASSED" = true ]; then
    echo "✅ ALL CHECKS PASSED - Ready for Railway!"
    echo ""
    echo "Next steps:"
    echo "1. cd into a strategy folder"
    echo "2. Run: railway init"
    echo "3. Deploy: railway up"
else
    echo "❌ SOME CHECKS FAILED - Fix issues above"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
