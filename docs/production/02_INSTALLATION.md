# Installation Guide

**Empirica v2.0 - Metacognitive Reasoning Framework**

---

## Prerequisites

### Required:
- **Python 3.8+** (3.10+ recommended)
- **pip** package manager
- **Git** (for cloning repository)

### Optional:
- **tmux** (for real-time dashboard monitoring)
- **ollama** or OpenAI API (for LLM-powered assessments)
- **SQLite3** (usually pre-installed with Python)

---

## Quick Installation (5 Minutes)

### 1. Clone Repository
```bash
cd /your/workspace/
git clone https://github.com/your-org/empirica.git
cd empirica
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Core Dependencies:**
```
# requirements.txt
watchdog>=3.0.0      # File system monitoring
psutil>=5.9.0        # System resource monitoring
numpy>=1.24.0        # Numerical operations (optional)
```

**No heavy ML dependencies** - Empirica is a reasoning framework, not an ML library.

### 3. Verify Installation
```bash
cd empirica
python3 -c "from empirica.bootstraps import ExtendedMetacognitiveBootstrap; print('✅ Empirica installed')"
```

**Expected Output:**
```
✅ Empirica installed
```

---

## Installation Methods

### Method 1: Development Install (Recommended)

For active development and customization:

```bash
git clone https://github.com/your-org/empirica.git
cd empirica
pip install -e .
```

**Benefits:**
- Changes to code immediately available
- Can modify and extend components
- Full access to all modules

### Method 2: Package Install (Future)

*Coming in v1.1:*
```bash
pip install empirica
```

Currently, use Method 1 (development install).

---

## Configuration

### 1. Database Directory
Empirica stores session data in `.empirica/`:

```bash
# Default location (created automatically)
.empirica/
├── sessions/
│   └── sessions.db       # SQLite database
├── exports/              # JSON exports
└── backups/              # Daily backups
```

**No configuration needed** - directories created on first use.

### 2. LLM Configuration (Optional)

Empirica can use external LLMs for epistemic assessments:

**Option A: Ollama (Local)**
```bash
# Install ollama: https://ollama.ai
ollama pull phi3        # Lightweight model
ollama pull mixtral     # Better reasoning

# Empirica will auto-detect ollama at http://localhost:11434
```

**Option B: OpenAI API**
```bash
export OPENAI_API_KEY="your-api-key"
# Empirica can use OpenAI if configured
```

**Option C: No LLM (Placeholder Mode)**
```python
# Empirica works without LLM using placeholder assessments
# All vectors default to 0.5 (neutral uncertainty)
cascade = CanonicalEpistemicCascade()  # Works immediately
```

### 3. Tmux Dashboard (Optional)

For real-time monitoring:

```bash
# Install tmux
sudo apt install tmux  # Ubuntu/Debian
brew install tmux      # macOS

# Empirica will auto-detect and use tmux if available
```

---

## Verify Installation

### Test 1: Import Core Modules
```python
python3 << 'EOF'
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
from empirica.data import SessionDatabase
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

print("✅ All core modules imported successfully")
EOF
```

### Test 2: Run Bootstrap
```python
python3 << 'EOF'
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

bootstrap = ExtendedMetacognitiveBootstrap(level="2", ai_id="test")
components = bootstrap.bootstrap()

print(f"✅ Bootstrap successful: {len(components)} components loaded")
EOF
```

**Expected Output:**
```
🔷 TIER 0: CANONICAL FOUNDATION
...
✅ Bootstrap successful: 30 components loaded
```

### Test 3: Database Creation
```python
python3 << 'EOF'
from empirica.data import SessionDatabase

db = SessionDatabase()
session_id = db.create_session("test_ai", bootstrap_level=2, components_loaded=30)
print(f"✅ Database working: session {session_id}")
db.close()
EOF
```

---

## Troubleshooting Installation

### Issue: Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'empirica'
```

**Solution:**
```bash
# Ensure you're in the correct directory
cd /path/to/empirica

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Add to PYTHONPATH temporarily
export PYTHONPATH="${PYTHONPATH}:/path/to/empirica"

# Or install in development mode
pip install -e .
```

### Issue: Import Errors from Old Path

**Error:**
```
ImportError: cannot import name 'CanonicalEpistemicCascade' from 'empirica'
```

**Solution:**
```python
# Correct import paths
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
```

### Issue: SQLite Database Errors

**Error:**
```
sqlite3.OperationalError: unable to open database file
```

**Solution:**
```bash
# Ensure .empirica/ directory is writable
mkdir -p .empirica/sessions
chmod 755 .empirica/sessions

# Or specify custom location
from empirica.data import SessionDatabase
db = SessionDatabase("/custom/path/sessions.db")
```

### Issue: Tmux Not Found

**Warning:**
```
⚠️  Tmux dashboard unavailable: tmux not found
```

**Solution:**
```bash
# Install tmux (optional - not required)
sudo apt install tmux  # Linux
brew install tmux      # macOS

# Or disable dashboard
cascade = CanonicalEpistemicCascade(enable_action_hooks=False)
```

---

## Directory Structure After Installation

```
empirica/
├── empirica/                    # Main package
│   ├── core/                   # Core system
│   ├── data/                   # Session database
│   ├── calibration/            # Uncertainty tracking
│   ├── investigation/          # Tool system
│   ├── integration/            # MCP servers
│   ├── bootstraps/             # Initialization
│   └── components/             # Extended modules
│
├── .empirica/                  # Runtime data (created on first use)
│   ├── sessions/
│   ├── exports/
│   └── backups/
│
├── docs/                       # Documentation
│   ├── production/            # User guides
│   └── Core Docs/             # Technical docs
│
└── tests/                      # Test suite
```

---

## Next Steps

After installation:

1. **Read:** [03_BASIC_USAGE.md](03_BASIC_USAGE.md) - Get started
2. **Try:** Run your first cascade
3. **Explore:** [01_QUICK_START.md](01_QUICK_START.md) - 5-minute intro
4. **Learn:** [SYSTEM_ARCHITECTURE_DEEP_DIVE.md](SYSTEM_ARCHITECTURE_DEEP_DIVE.md) - Technical overview

---

## Platform-Specific Notes

### Linux (Ubuntu/Debian)
```bash
# Install all dependencies
sudo apt update
sudo apt install python3 python3-pip git tmux sqlite3

# Clone and install
git clone https://github.com/your-org/empirica.git
cd empirica
pip install -r requirements.txt
```

### macOS
```bash
# Install homebrew if needed: https://brew.sh
brew install python git tmux

# Clone and install
git clone https://github.com/your-org/empirica.git
cd empirica
pip3 install -r requirements.txt
```

### Windows
```powershell
# Install Python from python.org
# Install Git from git-scm.com

# Clone and install
git clone https://github.com/your-org/empirica.git
cd empirica
pip install -r requirements.txt

# Note: Tmux dashboard not available on Windows (optional feature)
```

---

## Uninstallation

To remove Empirica:

```bash
# Remove package
pip uninstall empirica

# Remove data (optional)
rm -rf .empirica/

# Remove source
cd .. && rm -rf empirica/
```

---

## Getting Help

- **Documentation:** `docs/production/`
- **FAQ:** [22_FAQ.md](22_FAQ.md)
- **Troubleshooting:** [21_TROUBLESHOOTING.md](21_TROUBLESHOOTING.md)
- **Issues:** File issues with maintainers (GitHub coming when open-sourced)

---

**Installation Complete!** → Continue to [03_BASIC_USAGE.md](03_BASIC_USAGE.md)
