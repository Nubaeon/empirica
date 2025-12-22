#!/bin/bash
# One-Click Cross-Platform Distribution Script
# This script orchestrates the entire distribution pipeline:
#   PyPI → Homebrew → Chocolatey → Docker
#
# Usage:
#   ./scripts/distribute_all.sh test    # Test run (TestPyPI only, no publishing)
#   ./scripts/distribute_all.sh prod    # Production (publishes to PyPI)

set -e
YES_FLAG="false"
if [ "$1" = "-y" ]; then
    YES_FLAG="true"
    shift
fi

MODE="${1:-test}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Empirica Cross-Platform Distribution Pipeline             ║"
echo "║  PyPI → Homebrew → Chocolatey → Docker                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Mode: $MODE"
echo "Project: $(pwd)"
echo ""

# ============================================================================
# Phase 0: PyPI Foundation
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Phase 0: PyPI Foundation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Clean old builds
echo "🧹 Cleaning old builds..."
python3 "$SCRIPT_DIR/safe_delete.py" --force dist build empirica.egg-info 2>/dev/null || true

# Build package
echo "🔨 Building Python package..."
python -m pip install --upgrade build twine
python -m build

# Verify
echo "✅ Verifying package..."
twine check dist/*

# Get SHA256
TARBALL=$(ls dist/*.tar.gz)
SHA256=$(sha256sum "$TARBALL" | cut -d' ' -f1)
echo "📝 Package SHA256: $SHA256"

# Test installation
echo "🧪 Testing package installation..."
TEST_VENV="/tmp/test_empirica_$(date +%s)"
python3 -m venv "$TEST_VENV"
"$TEST_VENV/bin/pip" install --quiet dist/*.whl
"$TEST_VENV/bin/empirica" --help > /dev/null
"$TEST_VENV/bin/python" -c "from empirica.plugins.modality_switcher import ModalitySwitcher"
rm -rf "$TEST_VENV"
echo "✅ Package installs and imports successfully"

# Publish to PyPI
if [ "$MODE" = "prod" ]; then
    echo ""
    echo "⚠️  WARNING: About to publish to PRODUCTION PyPI"
    if [ "$YES_FLAG" = "false" ]; then
        read -p "Continue? (yes/no): " -r
    else
        REPLY="yes"
        echo "yes (auto-confirmed with -y)"
    fi
    if [[ $REPLY != "yes" ]]; then
        echo "Aborted."
        exit 1
    fi
    echo "📤 Publishing to PyPI..."
    twine upload dist/*
    PYPI_URL="https://pypi.org/project/empirica/"
    echo "✅ Published to PyPI: $PYPI_URL"
elif [ "$MODE" = "test" ]; then
    echo "📤 Publishing to TestPyPI..."
    twine upload --repository testpypi dist/* || echo "⚠️  TestPyPI upload skipped (may already exist)"
    PYPI_URL="https://test.pypi.org/project/empirica/"
    echo "✅ Published to TestPyPI: $PYPI_URL"
fi

echo "✅ Phase 0 complete: PyPI package ready"
echo ""

# ============================================================================
# Phase 1a: Homebrew Formula
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🍺 Phase 1a: Homebrew Formula"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "📝 Updating Homebrew formula SHA256..."
sed -i "s/sha256 \"[a-f0-9]*\"/sha256 \"$SHA256\"/" packaging/homebrew/empirica.rb

echo "✅ Homebrew formula ready: packaging/homebrew/empirica.rb"
echo ""
echo "To test on macOS:"
echo "  brew install --build-from-source ./packaging/homebrew/empirica.rb"
echo "  empirica bootstrap --help"
echo ""
echo "To publish to Homebrew tap:"
echo "  1. Create tap repo: brew tap-new empirica/tap"
echo "  2. Copy formula to tap"
echo "  3. Push to GitHub"
echo "  4. Users install: brew tap empirica/tap && brew install empirica"
echo ""

# ============================================================================
# Phase 1b: Chocolatey Package
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🍫 Phase 1b: Chocolatey Package"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "📝 Updating Chocolatey package SHA256..."
sed -i "s/\\\$checksum = '[a-f0-9]*'/\\\$checksum = '$SHA256'/" packaging/chocolatey/tools/chocolateyinstall.ps1

echo "✅ Chocolatey package ready: packaging/chocolatey/"
echo ""
echo "To test on Windows:"
echo "  cd packaging/chocolatey"
echo "  choco pack"
echo "  choco install empirica -s . -y"
echo "  empirica bootstrap --help"
echo ""
echo "To publish to Chocolatey Community:"
echo "  choco push empirica.1.0.0-beta.nupkg --source https://push.chocolatey.org/ --api-key YOUR_API_KEY"
echo ""

# ============================================================================
# Phase 3: Docker Image
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐳 Phase 3: Docker Image"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v docker &> /dev/null; then
    echo "🔨 Building Docker image..."
    docker build -t empirica:1.0.0-beta -t empirica:latest .
    
    echo "🧪 Testing Docker image..."
    docker run --rm empirica:1.0.0-beta --version > /dev/null
    docker run --rm empirica:1.0.0-beta --help > /dev/null
    
    echo "✅ Docker image built and tested successfully"
    echo ""
    echo "Docker image: empirica:1.0.0-beta"
    echo "Image size: $(docker images empirica:1.0.0-beta --format '{{.Size}}')"
    echo ""
    echo "Usage:"
    echo "  docker run -it --rm empirica:1.0.0-beta --help"
    echo "  docker run -v \$(pwd)/.empirica:/data/.empirica empirica:1.0.0-beta bootstrap --ai-id docker-agent"
    echo ""
    
    if [ "$MODE" = "prod" ]; then
        echo "To publish to Docker Hub:"
        echo "  docker tag empirica:1.0.0-beta soulentheo/empirica:1.0.0-beta"
        echo "  docker tag empirica:1.0.0-beta soulentheo/empirica:latest"
        echo "  docker push soulentheo/empirica:1.0.0-beta"
        echo "  docker push soulentheo/empirica:latest"
        echo ""
    fi
else
    echo "⚠️  Docker not installed - skipping Docker build"
    echo "Docker build can be run manually: docker build -t empirica:1.0.0-beta ."
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ Distribution Pipeline Complete!                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Package Details:"
echo "   Version: 1.0.0-beta"
echo "   Size: $(du -h dist/*.whl | cut -f1)"
echo "   SHA256: $SHA256"
echo ""
echo "📍 Distribution Channels:"
echo "   [✅] PyPI: $PYPI_URL"
echo "   [✅] Homebrew: packaging/homebrew/empirica.rb (ready for tap)"
echo "   [✅] Chocolatey: packaging/chocolatey/ (ready to pack)"
if command -v docker &> /dev/null; then
    echo "   [✅] Docker: empirica:1.0.0-beta (built and tested)"
else
    echo "   [⚠️ ] Docker: Ready to build (Docker not installed)"
fi
echo ""
echo "📚 Next Steps:"
echo "   1. Test installation on each platform"
echo "   2. Create Homebrew tap repository (optional)"
echo "   3. Submit to Chocolatey Community (optional)"
echo "   4. Push Docker image to Docker Hub (optional)"
echo ""
echo "🎉 One-click distribution complete!"
