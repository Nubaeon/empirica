#!/bin/bash
#
# Run Production Tests for Empirica
#
# Tests the production-ready features:
# - Epistemic handoff and knowledge transfer
# - Vector storage (all 13 vectors)
# - Calibration consistency
# - Bayesian Guardian and Drift Monitor

set -e

echo "🧪 Running Empirica Production Tests"
echo "===================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-asyncio pytest-cov
fi

# Run production tests
echo "📊 Running production feature tests..."
pytest tests/production/ -v --tb=short \
    --cov=empirica \
    --cov=mcp_local \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/production

echo ""
echo "✅ Production tests complete!"
echo ""
echo "📈 Coverage report: htmlcov/production/index.html"
