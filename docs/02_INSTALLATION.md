# Installation Guide

**Time Required:** 5-10 minutes  
**Prerequisites:** Python 3.10+

---

## Prerequisites

⚠️ **Virtual Environment Required**

Modern Python installations use externally-managed environments. You must create a virtual environment before installing Empirica.

**Why Virtual Environment?**
- ✅ Isolates Empirica dependencies
- ✅ Prevents conflicts with other projects  
- ✅ Standard Python best practice
- ✅ Required by Python 3.11+ on many systems

---

## Quick Installation

### 1. Clone Repository
```bash
git clone https://github.com/your-org/empirica.git
cd empirica
```

### 2. Create Virtual Environment
```bash
# Create isolated environment
python3 -m venv .venv-empirica

# Activate virtual environment
# Linux/Mac:
source .venv-empirica/bin/activate

# Windows:
.venv-empirica\Scripts\activate

# You should see (.venv-empirica) in your prompt
```

### 3. Install Dependencies
```bash
# Install Empirica package
pip install -e .

# Install all dependencies
pip install -r requirements.txt
```

This installs Empirica in editable mode with all required dependencies.

### 4. Verify Installation
```bash
# List available commands (should show 'onboard')
empirica --help

# Test onboarding command
empirica onboard --help
```

✅ **Success!** If you see the help output, Empirica is installed correctly.

---

## Installation Methods

### Method 1: Editable Install (Recommended for Development)
```bash
pip install -e .
```
**Pros:** Changes to code take effect immediately  
**Use when:** Developing, contributing, or customizing

### Method 2: Standard Install
```bash
pip install .
```
**Pros:** Cleaner, production-ready  
**Use when:** Just using Empirica

### Method 3: From PyPI (Future)
```bash
pip install empirica
```
**Status:** Not yet published (Phase 0 MVP in progress)

---

## Configuration

### 1. Run Onboarding Wizard
```bash
empirica onboard --ai-id <your-ai-name>
```

The wizard will:
- Create `.empirica/` configuration directory
- Set up credentials template (if needed)
- Verify installation
- Guide you through first use

### 2. Manual Configuration (Optional)

If you prefer manual setup:

```bash
# Create config directory
mkdir -p ~/.empirica

# Copy credentials template
cp .empirica/credentials.yaml.template ~/.empirica/credentials.yaml

# Edit credentials (if using external LLMs)
nano ~/.empirica/credentials.yaml
```

**Note:** Empirica works **locally** by default. External LLM credentials only needed for:
- Modality Switcher (multi-AI routing - Phase 1+)
- Custom integrations requiring API calls

---

## Directory Structure Created

After installation:
```
~/.empirica/
├── credentials.yaml       # API keys (optional, gitignored)
├── sessions/
│   └── sessions.db        # Local session storage
└── .empirica_reflex_logs/ # Epistemic assessment logs
```

**Privacy:** All data stays local on your machine.

---

## Verify Installation

### Test CLI
```bash
# Should show help
empirica --help

# Should show version
empirica --version

# Test onboarding
empirica onboard --ai-id test
```

### Test Python Import
```python
python3 << EOF
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.data import SessionDatabase
print("✅ Empirica installed successfully!")
EOF
```

### Test MCP Server (Optional)
```bash
# Start server
empirica mcp-start

# Check status
empirica mcp-status

# Stop server
empirica mcp-stop
```

---

## Troubleshooting

### Issue: `command not found: empirica`

**Cause:** Installation directory not in PATH

**Fix:**
```bash
# Add to PATH (bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Or use python module
python3 -m empirica.cli --help
```

### Issue: Import errors

**Cause:** Missing dependencies

**Fix:**
```bash
# Reinstall with dependencies
pip install -e . --force-reinstall
```

### Issue: Permission denied

**Cause:** Installing system-wide without sudo

**Fix:**
```bash
# Install for user only
pip install -e . --user

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Issue: `.empirica/` directory not created

**Cause:** First run hasn't occurred

**Fix:**
```bash
# Run onboarding to create directories
empirica onboard

# Or create manually
mkdir -p ~/.empirica/sessions
```

---

## Virtual Environment (Recommended)

For isolated installation:

```bash
# Create virtual environment
python3 -m venv empirica-venv

# Activate
source empirica-venv/bin/activate  # Linux/Mac
# OR
empirica-venv\Scripts\activate     # Windows

# Install
pip install -e .

# Verify
empirica --version
```

**Benefits:**
- Isolated from system Python
- No dependency conflicts
- Easy to remove

---

## Upgrading

### From Git
```bash
cd empirica
git pull
pip install -e . --upgrade
```

### Migration (if needed)
If upgrading from old version with existing database:
```bash
empirica migrate
```

This updates the database schema to include any new features (e.g., uncertainty vector).

---

## Uninstallation

```bash
# Remove package
pip uninstall empirica

# Remove configuration (optional)
rm -rf ~/.empirica

# Remove logs (optional)
rm -rf .empirica_reflex_logs
```

---

## Platform-Specific Notes

### Linux
✅ Works out of the box

### macOS
✅ Works out of the box
- May need: `xcode-select --install` for build tools

### Windows
⚠️ Mostly works, some notes:
- Use PowerShell or WSL
- Path separators: Use `/` not `\` in configs
- Virtual environment recommended

---

## Dependencies

**Core:**
- Python 3.8+
- SQLite3 (included with Python)

**Required packages** (auto-installed):
- See `requirements.txt` for full list

**Optional:**
- `psutil` - For detailed process info in `mcp-status`
- External LLM APIs - Only for Phase 1+ features

---

## Troubleshooting Installation

### "command not found: empirica"

**Problem:** Virtual environment not activated or installation failed

**Solution:**
```bash
# Make sure virtual environment is activated
source .venv-empirica/bin/activate

# You should see (.venv-empirica) in your prompt

# If still not found, reinstall
pip install -e .
```

### "No module named 'yaml'" (or other missing module)

**Problem:** requirements.txt not installed

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Verify
empirica --help
```

### "externally-managed-environment" error

**Problem:** Trying to install without virtual environment

**Solution:**
```bash
# Create and activate virtual environment first
python3 -m venv .venv-empirica
source .venv-empirica/bin/activate

# Then install
pip install -e .
pip install -r requirements.txt
```

### Multiple virtual environments confusion

**Problem:** Directory has multiple venvs (.venv, venv, .venv-mcp)

**Solution:**
```bash
# Use .venv-empirica for Empirica
source .venv-empirica/bin/activate

# Verify you're in correct venv
which python3
# Should show: /path/to/empirica/.venv-empirica/bin/python3

# Verify empirica command available
which empirica
# Should show: /path/to/empirica/.venv-empirica/bin/empirica
```

### "onboard" command not found

**Problem:** Wrong project or old version

**Solution:**
```bash
# Check which empirica is running
which empirica

# Make sure you're in correct directory
cd /path/to/empirica

# Reinstall
source .venv-empirica/bin/activate
pip install -e .
pip install -r requirements.txt

# Verify
empirica onboard --help
```

### Import errors when running commands

**Problem:** PYTHONPATH or sys.path issues

**Solution:**
```bash
# Make sure you're running from project root
cd /path/to/empirica

# Activate venv
source .venv-empirica/bin/activate

# Run commands from root directory
empirica --help
```

---

## Next Steps

After installation:

1. **Run onboarding:** `empirica onboard --ai-id <your-name>`
2. **Try first task:** 
   - **🤖 AI Agent?** → [`docs/01_a_AI_AGENT_START.md`](01_a_AI_AGENT_START.md)
   - **👤 Human?** → [`docs/00_START_HERE.md`](00_START_HERE.md)
3. **Read skills guide:** See [`docs/skills/SKILL.md`](skills/SKILL.md) (for AI agents)
4. **Explore production docs:** See [`docs/production/README.md`](production/README.md)

---

**Need help?** See [`docs/06_TROUBLESHOOTING.md`](06_TROUBLESHOOTING.md)
