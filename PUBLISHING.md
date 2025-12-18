# Publishing Empirica to PyPI

**Complete guide for publishing empirica and empirica-mcp packages**

---

## Prerequisites

```bash
# Install build tools
pip install build twine

# PyPI account
# - Create account: https://pypi.org/account/register/
# - Enable 2FA
# - Create API token: https://pypi.org/manage/account/token/
```

---

## Package 1: empirica (Core)

### Step 1: Verify Package Structure

```bash
cd /path/to/empirica

# Check required files
ls pyproject.toml README.md LICENSE MANIFEST.in

# Verify version in pyproject.toml
grep "version" pyproject.toml
```

### Step 2: Build Package

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Expected output:
# dist/empirica-1.0.0b0-py3-none-any.whl
# dist/empirica-1.0.0b0.tar.gz
```

### Step 3: Validate Package

```bash
# Check package metadata
twine check dist/*

# Should show: PASSED
```

### Step 4: Test Install Locally

```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate  # or test-env\Scripts\activate on Windows

# Install from local wheel
pip install dist/empirica-1.0.0b0-py3-none-any.whl

# Test it works
empirica --help
echo '{"ai_id":"test"}' | empirica session-create -

# Cleanup
deactivate
rm -rf test-env
```

### Step 5: Publish to TestPyPI (Optional)

```bash
# Upload to test.pypi.org first
twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ empirica

# If works, proceed to real PyPI
```

### Step 6: Publish to PyPI

```bash
# Upload to pypi.org
twine upload dist/*

# Enter your PyPI API token when prompted
# Username: __token__
# Password: pypi-xxxx...
```

### Step 7: Verify Publication

```bash
# Check on PyPI
open https://pypi.org/project/empirica/

# Test install from PyPI
pip install empirica

# Verify
empirica --help
```

---

## Package 2: empirica-mcp (MCP Server)

### Step 1: Navigate to MCP Package

```bash
cd empirica-mcp/
```

### Step 2: Build Package

```bash
# Clean
rm -rf dist/ build/ *.egg-info

# Build
python -m build
```

### Step 3: Validate

```bash
twine check dist/*
```

### Step 4: Test Locally

```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate

# Install empirica first (dependency)
pip install empirica

# Install empirica-mcp
pip install dist/empirica_mcp-1.0.0b0-py3-none-any.whl

# Test
empirica-mcp --help 2>&1 | head -10

# Cleanup
deactivate
rm -rf test-env
```

### Step 5: Publish

```bash
# TestPyPI (optional)
twine upload --repository testpypi dist/*

# PyPI
twine upload dist/*
```

---

## Post-Publication Checklist

### Update Documentation

```bash
# Update README.md to show PyPI install
# Already done in iteration 7!

# Verify installation instructions work:
pip install empirica
pip install empirica-mcp
```

### Update Distribution Files

```bash
# Chocolatey (packaging/chocolatey/empirica.nuspec)
# Update version number

# Homebrew (packaging/homebrew/empirica.rb)
# Update version and SHA256

# Docker (Dockerfile)
# Update FROM empirica:1.0.0-beta
```

### Create GitHub Release

```bash
# Tag release
git tag -a v1.0.0-beta -m "Empirica v1.0.0-beta - Production Ready"
git push origin v1.0.0-beta

# Create release on GitHub
# - Upload dist/*.tar.gz as release asset
# - Copy README.md highlights to release notes
```

---

## Troubleshooting

### Build Fails: Missing Dependencies

```bash
# Install build dependencies
pip install setuptools wheel build
```

### Twine Upload Fails: Authentication

```bash
# Use API token, not password
# Username: __token__
# Password: Your full token starting with pypi-

# Or configure ~/.pypirc:
[pypi]
username = __token__
password = pypi-your-token-here
```

### Package Too Large

```bash
# Check size
du -h dist/*

# If > 60MB, check MANIFEST.in excludes:
cat MANIFEST.in

# Common excludes:
exclude tests/*
exclude .git*
exclude *.db
exclude .empirica/*
```

### Import Error After Install

```bash
# Check package structure
tar -tzf dist/empirica-*.tar.gz | head -20

# Verify empirica/ directory is included
# Verify __init__.py exists
```

---

## Version Bumping

### Before Next Release

```bash
# Update pyproject.toml
# version = "1.0.0"  # Remove -beta

# Update README.md badges
# Update CHANGELOG.md

# Rebuild and republish
python -m build
twine upload dist/*
```

---

## Current Status

**As of December 2025:**
- ❌ empirica NOT on PyPI yet (ready to publish)
- ❌ empirica-mcp NOT on PyPI yet (ready to publish)
- ✅ Package structure complete
- ✅ Dependencies verified
- ✅ Documentation ready
- ✅ Security sanitized

**Ready to publish with commands above!**

---

## Quick Reference

```bash
# Complete publishing workflow
cd /path/to/empirica

# 1. Build
python -m build

# 2. Check
twine check dist/*

# 3. Publish
twine upload dist/*

# 4. Verify
pip install --upgrade empirica
empirica --help
```

**That's it!** 🚀
