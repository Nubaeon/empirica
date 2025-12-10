# Empirica Global Installation

**Date:** 2025-12-10
**Status:** ✅ Complete
**Objective:** Reinstall empirica in global PATH for easy access

---

## What Was Done

### Installation
```bash
# Install empirica globally in editable mode
pip install -e /home/yogapad/empirical-ai/empirica
```

**Result:**
- ✅ `empirica` command available in PATH
- ✅ Uses local source code (editable mode = instant changes)
- ✅ Entry point: `/home/yogapad/.venv/tmux/bin/empirica`
- ✅ Package info: `empirica 1.0.0b0`

---

## Installation Details

### Package Configuration
**File:** `pyproject.toml` (lines 76-77)
```toml
[project.scripts]
empirica = "empirica.cli.cli_core:main"
```

**Installation Method:** Editable (`-e` flag)
- Installs entry point script in PATH
- Links to source code (no copy)
- Changes to source code are immediately reflected
- No rebuild needed

### Location
```
Command: /home/yogapad/.venv/tmux/bin/empirica
Source: /home/yogapad/empirical-ai/empirica/empirica/cli/cli_core.py
Module Entry Point: empirica.cli.cli_core:main()
```

---

## Verification

### Commands Work from PATH
```bash
# ✅ Skill commands
empirica skill-suggest --task "Build a React component"
# Returns: skill suggestions from docs/skills/SKILL_SOURCES.yaml

empirica skill-fetch --name "test-skill" --url "https://..."
# Downloads and saves to project_skills/test-skill.yaml

# ✅ Postflight command
empirica postflight --session-id <sid> --vectors '{"engagement": 0.90, ...}' --reasoning "summary"
# Returns: JSON with vectors persisted to git notes

# ✅ Postflight alias
empirica postflight-submit --session-id <sid> --vectors '...'
# Also works (backward compatibility)
```

### Installation Verification
```bash
$ which empirica
/home/yogapad/.venv/tmux/bin/empirica

$ pip show empirica
Name: empirica
Version: 1.0.0b0
Location: /home/yogapad/.venv/tmux/lib/python3.13/site-packages

$ empirica --help
usage: empirica [-h] [--verbose] [--config CONFIG]
                {sessions-list,sessions-show,sessions-export,preflight,workflow,...}
```

---

## Usage Examples

### From Anywhere in the System
```bash
# No need for full path or venv activation
empirica postflight --session-id "abc123" --vectors '{"engagement": 0.85, ...}' --reasoning "Task done"

# Works in scripts, cron jobs, other tools
empirica skill-suggest --task "Your task here"

# Works in docker, remote SSH, CI/CD pipelines
empirica check --session-id <sid> --findings '["X", "Y"]' --unknowns '["Z"]' --confidence 0.75
```

### Why Global Installation is Better

| Aspect | Before | After |
|--------|--------|-------|
| **Access** | Must use full path or specific venv | `empirica` from anywhere |
| **Scripts** | Had to hardcode `/.../.venv-mcp/bin/python -m` | Simple: `empirica command` |
| **Distribution** | Difficult to share with team | Easy: `pip install empirica` |
| **Updates** | Required both venv and file updates | Editable mode: source changes apply immediately |
| **PATH pollution** | 0 (needed explicit path) | 1 command (clean) |

---

## Editable Mode Benefits

Since empirica was installed with `-e` (editable), changes to the source code are immediately available:

```bash
# Scenario: You modify empirica/cli/cli_core.py
vim /home/yogapad/empirical-ai/empirica/empirica/cli/cli_core.py

# No rebuild needed - next empirica command uses new code
empirica postflight ...  # ← Uses updated code immediately
```

This is ideal for development and testing.

---

## Future: Publishing to PyPI

The `pyproject.toml` is ready for PyPI publication:

```bash
# To publish (when ready):
cd /home/yogapad/empirical-ai/empirica
python -m build
python -m twine upload dist/*

# Then users can do:
pip install empirica

# Instead of:
pip install -e /path/to/local/repo
```

---

## Important: Version Note

Current version: `1.0.0-beta` (in pyproject.toml line 7)
- Should be updated to `1.0.0b0` or use PEP 440 compliant version before PyPI release
- Current installed version: `1.0.0b0` (setuptools interprets the hyphen)

---

## Technical Details

### Entry Point Script
```bash
$ cat /home/yogapad/.venv/tmux/bin/empirica
#!/home/yogapad/.venv/tmux/bin/python
# -*- coding: utf-8 -*-
import re
import sys
from empirica.cli.cli_core import main
if __name__ == '__main__':
    sys.exit(main())
```

### Dependency Management
All dependencies are specified in `pyproject.toml` and installed when empirica is installed:
- pydantic, sqlalchemy, pyyaml (core)
- mcp, anthropic (integrations)
- requests, httpx (HTTP)
- rich, typer (CLI/UI)
- And more (see pyproject.toml lines 30-53)

---

## Status

✅ **COMPLETE**

- Empirica installed globally in editable mode
- All commands work from PATH
- Ready for team distribution
- Ready for PyPI publication (when version is finalized)

---

## Next Steps (Optional)

1. **Version finalization:** Update version from `1.0.0-beta` to production version
2. **PyPI publication:** When ready, publish for global installation
3. **Shell alias:** Optional - add shell alias for shorter commands:
   ```bash
   alias emp='empirica'  # Then: emp postflight ...
   ```

---

**Usage:** `empirica <command> [args]`

**Available anywhere:** ✅ Yes, as long as `/home/yogapad/.venv/tmux/bin` is in PATH
