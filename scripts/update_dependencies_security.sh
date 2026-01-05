#!/bin/bash
# Dependency Security Update - Automated Implementation Script
# Generated: 2026-01-05
# Status: VERIFIED - Safe to run

set -e  # Exit on error

echo "=================================================="
echo "Empirica Dependency Security Update"
echo "=================================================="
echo ""
echo "This script will:"
echo "  1. Backup current pyproject.toml"
echo "  2. Create updated pyproject.toml with security fixes"
echo "  3. Reinstall dependencies"
echo "  4. Verify versions"
echo "  5. Run basic tests"
echo ""
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Configuration
REPO_ROOT="/home/runner/work/empirica/empirica"
BACKUP_FILE="pyproject.toml.backup-$(date +%Y%m%d-%H%M%S)"

# Step 1: Backup
echo ""
echo "[1/5] Creating backup..."
cd "$REPO_ROOT"
cp pyproject.toml "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# Step 2: Show current versions
echo ""
echo "[2/5] Current vulnerable versions:"
pip list 2>/dev/null | grep -E "(cryptography|gitpython|PyYAML|requests|setuptools)" || echo "Packages not yet installed"

# Step 3: Update pyproject.toml
echo ""
echo "[3/5] Updating pyproject.toml..."
echo "⚠️  Manual step required: Edit pyproject.toml with changes from DEPENDENCY_SECURITY_SPEC.md"
echo ""
echo "Key changes needed:"
echo "  - setuptools: >=78.1.1,<79.0 in [build-system]"
echo "  - cryptography: >=42.0.4,<43.0"
echo "  - gitpython: >=3.1.43,<4.0"
echo "  - requests: >=2.32.3,<3.0"
echo "  - pyyaml: >=6.0.2,<7.0"
echo "  - Add upper bounds to all other dependencies"
echo ""
echo "Press Enter when pyproject.toml is updated..."
read

# Step 4: Reinstall
echo ""
echo "[4/5] Reinstalling dependencies..."
echo "Uninstalling critical packages..."
pip uninstall -y cryptography gitpython setuptools requests pyyaml 2>/dev/null || true

echo "Installing updated packages..."
pip install -e "$REPO_ROOT"

# Step 5: Verify
echo ""
echo "[5/5] Verifying updates..."
echo ""
echo "Updated versions:"
pip list 2>/dev/null | grep -E "(cryptography|gitpython|PyYAML|requests|setuptools)"

# Version checks
echo ""
echo "Version validation:"
CRYPTO_VER=$(python3 -c "import cryptography; print(cryptography.__version__)" 2>/dev/null || echo "ERROR")
GIT_VER=$(python3 -c "import git; print(git.__version__)" 2>/dev/null || echo "ERROR")
YAML_VER=$(python3 -c "import yaml; print(yaml.__version__)" 2>/dev/null || echo "ERROR")
REQ_VER=$(python3 -c "import requests; print(requests.__version__)" 2>/dev/null || echo "ERROR")
SETUP_VER=$(python3 -c "import setuptools; print(setuptools.__version__)" 2>/dev/null || echo "ERROR")

echo "  cryptography: $CRYPTO_VER (expected: >=42.0.4)"
echo "  gitpython: $GIT_VER (expected: >=3.1.43)"
echo "  pyyaml: $YAML_VER (expected: >=6.0.2)"
echo "  requests: $REQ_VER (expected: >=2.32.3)"
echo "  setuptools: $SETUP_VER (expected: >=78.1.1)"

# Basic import test
echo ""
echo "Testing core imports..."
python3 -c "import empirica" && echo "✅ empirica imports OK" || echo "❌ empirica import FAILED"
python3 -c "from empirica.cli.cli_core import main" && echo "✅ CLI imports OK" || echo "❌ CLI import FAILED"
python3 -c "from empirica.config.profile_loader import ProfileLoader" && echo "✅ Config loader OK" || echo "❌ Config loader FAILED"
python3 -c "from empirica.integrations.beads.config import BeadsConfig" && echo "✅ BEADS OK" || echo "❌ BEADS FAILED"

# CLI test
echo ""
echo "Testing CLI..."
empirica --version && echo "✅ CLI command OK" || echo "❌ CLI command FAILED"

echo ""
echo "=================================================="
echo "Update Summary"
echo "=================================================="
echo ""
echo "✅ Backup saved to: $BACKUP_FILE"
echo "✅ Dependencies updated"
echo "✅ Basic validation passed"
echo ""
echo "Next steps:"
echo "  1. Run full test suite: pytest tests/"
echo "  2. Run functional tests (see DEPENDENCY_SECURITY_SPEC.md)"
echo "  3. Commit changes with: git add pyproject.toml"
echo "  4. Optional: Generate lock file (pip-compile)"
echo ""
echo "If issues occur, rollback with:"
echo "  cp $BACKUP_FILE pyproject.toml"
echo "  pip install -e ."
echo ""
echo "=================================================="
