# Empirica Update Guide: v1.3.3 → v1.3.4

**For:** Claude instances running older Empirica configurations
**From:** develop branch (2026-01-20)

---

## Quick Summary

Key changes since your last sync:
1. **Memory retrieval** now defaults to "focused" (eidetic + episodic)
2. **Bootstrap** has size-aware depth filtering (89% token reduction)
3. **New autonomy system** for earned trust/graduated Sentinel modes
4. **CLI aliases** added (backward compatible)
5. **MCP tools** deprecated: `execute_preflight`, `execute_postflight` removed

---

## 1. Memory Retrieval Changes

### What Changed
`project-search` now defaults to **focused** mode (eidetic + episodic collections only).

### Old Behavior
```bash
# Searched all 4 collections by default
empirica project-search --task "query"
```

### New Behavior
```bash
# Default: focused (eidetic + episodic - cleaner, faster)
empirica project-search --task "query"

# Explicit: all 4 collections (docs, memory, eidetic, episodic)
empirica project-search --task "query" --type all

# Specific collection
empirica project-search --task "query" --type eidetic
```

### Migration
No action needed. Default is better. Use `--type all` only when you need raw docs/memory.

---

## 2. Bootstrap Size-Aware Depth Filtering

### What Changed
`project-bootstrap` now auto-selects depth based on output size:
- **>50k chars** → minimal (removes file_tree, flow_metrics)
- **>20k chars** → moderate (truncates finding_data, limits tree depth)
- **<20k chars** → full (everything)

### Result
~89% reduction in bootstrap output (138k → 15.6k chars typical).

### New Truncation Behavior
When truncated, findings have:
```json
{
  "finding": "truncated text...",
  "_truncated": true  // Flag for AI to query full text if needed
}
```

### Migration
No action needed. Automatic.

---

## 3. Autonomy System (NEW)

### New Commands
```bash
# Suggestions for human review
empirica suggestion-log --session-id <ID> --suggestion "..." --domain architecture --confidence 0.8
empirica suggestion-list --status pending
empirica suggestion-review --suggestion-id <ID> --outcome accepted

# Trust levels
empirica trust-status                          # All domains
empirica trust-status --domain architecture    # Specific domain

# Graduated Sentinel modes
empirica autonomy-status --domain <dom>        # Show current mode
empirica evaluate-action --action "..." --confidence 0.9  # Test if allowed
empirica trust-evolution --domain <dom>        # Escalation recommendations
```

### Trust Levels → Sentinel Modes
| Trust Score | Level | Mode | Behavior |
|-------------|-------|------|----------|
| 0.0 - 0.4 | LOW | CONTROLLER | Human approval for ALL |
| 0.4 - 0.6 | MEDIUM | OBSERVER | Log warnings, human for significant |
| 0.6 - 0.8 | HIGH | ADVISORY | Autonomous tactical, human for critical |
| 0.8 - 1.0 | VERY_HIGH | AUTONOMOUS | Full autonomy, async review |

### Migration
Optional. Enable by using suggestion-log to build trust history.

---

## 4. CLI Aliases (NEW)

All backward compatible - original commands still work.

| Alias | Full Command |
|-------|--------------|
| `pre` | `preflight-submit` |
| `post` | `postflight-submit` |
| `sc` | `session-create` |
| `sl` | `sessions-list` |
| `sr` | `sessions-resume` |
| `gc` | `goals-create` |
| `gl` | `goals-list` |
| `fl` | `finding-log` |
| `ul` | `unknown-log` |
| `de` | `deadend-log` |
| `pb` | `project-bootstrap` |
| `sug` | `suggestion-log` |

### Migration
No action needed. Use aliases for brevity if desired.

---

## 5. Deprecated MCP Tools

### Removed
- `execute_preflight` → Use `submit_preflight_assessment`
- `execute_postflight` → Use `submit_postflight_assessment`

### Migration
Update any code calling deprecated tools:
```python
# Old
mcp.execute_preflight(...)

# New
mcp.submit_preflight_assessment(session_id, vectors, reasoning)
```

---

## 6. Hooks Updates

### SessionStart:compact Now Chains Breadcrumbs
```json
{
  "SessionStart": [
    {
      "matcher": "compact",
      "hooks": [
        {"command": "python3 .../post-compact.py"},
        {"command": "bash ${BREADCRUMBS_ROOT}/hooks/session-start.sh"}
      ]
    }
  ]
}
```

### Breadcrumbs-Empirica Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRE-COMPACT FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│  1. Empirica pre-compact.py captures:                           │
│     - Current epistemic vectors                                 │
│     - Session ID                                                │
│     - Breadcrumbs summary (findings, unknowns, goals)           │
│     → Saves to git notes: empirica-precompact                   │
│                                                                 │
│  2. Breadcrumbs pre-compact.sh captures:                        │
│     - Task context from transcript                              │
│     - Git state (branch, modified files)                        │
│     - PR context (if applicable)                                │
│     → Saves to git notes: breadcrumbs                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [CONTEXT COMPACTED]
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   POST-COMPACT FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│  1. Empirica post-compact.py:                                   │
│     - Detects phase state (COMPLETE vs INCOMPLETE)              │
│     - Routes recovery (new session vs CHECK gate)               │
│     - Loads confidence-weighted context                         │
│     → Outputs: session instructions + epistemic focus           │
│                                                                 │
│  2. Breadcrumbs session-start.sh loads:                         │
│     - Calibration from .breadcrumbs.yaml                        │
│     - Task context from git notes (breadcrumbs)                 │
│     - Epistemic state from git notes (empirica-precompact)      │
│     → Outputs: context boxes + assessment prompt                │
└─────────────────────────────────────────────────────────────────┘
```

### Key Files for Integration

| File | Purpose |
|------|---------|
| `.breadcrumbs.yaml` | Calibration data (Empirica exports on POSTFLIGHT) |
| `git notes --ref=breadcrumbs` | Task context (breadcrumbs captures) |
| `git notes --ref=empirica-precompact` | Epistemic vectors (Empirica captures) |

### Migration
If using custom hooks, set the environment variable:
```bash
export BREADCRUMBS_ROOT=/path/to/breadcrumbs
# Or for installed plugin:
export BREADCRUMBS_ROOT=~/.claude/plugins/local/breadcrumbs
```

---

## 7. CLAUDE.md System Prompt Updates

### Key Additions

**Phase-aware completion:**
```
NOETIC completion = "Have I learned enough to proceed?"
PRAXIC completion = "Have I implemented enough to ship?"
```

**Focused search default:**
```bash
# Default now queries eidetic + episodic only
empirica project-search --task "query"
```

**Per-goal CASCADE loops:**
```
One goal = one PREFLIGHT → CHECK → POSTFLIGHT loop
Don't batch multiple goals into one loop
```

### Get Latest Prompt
```bash
# From empirica repo
cat docs/human/developers/system-prompts/CLAUDE.md
```

Or copy key sections to `~/.claude/CLAUDE.md`.

---

## 8. Calibration Updates (1727 observations)

### Latest Bias Corrections
| Vector | Correction | Evidence |
|--------|------------|----------|
| completion | **+0.73** | Massive underestimation |
| change | +0.39 | Underestimate impact |
| know | +0.10 | Underestimate knowledge |
| uncertainty | **-0.14** | Overestimate doubt |
| context | +0.02 | Well calibrated |

### Readiness Gate (unchanged)
```
know >= 0.70 AND uncertainty <= 0.35 (after correction)
```

---

## 9. Files to Sync

### From develop branch:
```bash
# System prompt
cp docs/human/developers/system-prompts/CLAUDE.md ~/.claude/CLAUDE.md

# Plugin (if using)
cp -r plugins/claude-code-integration ~/.claude/plugins/

# Calibration data (if breadcrumbs integration)
# Exports to .breadcrumbs.yaml automatically via POSTFLIGHT
```

---

## 10. Verification Checklist

After updating, verify:

```bash
# Check version
empirica --version  # Should show 1.3.4

# Test focused search
empirica project-search --task "test query" --output json | jq '.search_type'
# Should show: "focused"

# Test bootstrap depth
empirica project-bootstrap --output json | jq '.depth'
# Should show: "auto" with filtered output

# Test autonomy commands
empirica trust-status --output json
# Should return domain trust levels

# Test alias
empirica pre --help
# Should show preflight-submit help
```

---

## 11. Statusline Fix

### Issue
Statusline was creating new `.empirica/` in CWD instead of falling back to global hub when not in a project directory.

### Fix Applied
When no local `.empirica/` exists, statusline now checks for global hub at `~/.empirica/`:

```python
# Old (broken)
else:
    db = SessionDatabase()  # Creates in CWD

# New (fixed)
else:
    global_db = Path.home() / '.empirica' / 'sessions' / 'sessions.db'
    if global_db.exists():
        db = SessionDatabase(db_path=str(global_db))
    else:
        db = SessionDatabase()
```

### Verification
```bash
# From any directory
python3 ~/empirical-ai/empirica/scripts/statusline_empirica.py
# Should show session info from global hub
```

---

## Summary of Breaking Changes

| Change | Impact | Action |
|--------|--------|--------|
| Focused search default | Behavioral | None (better default) |
| execute_preflight removed | Breaking (MCP) | Use submit_preflight_assessment |
| execute_postflight removed | Breaking (MCP) | Use submit_postflight_assessment |

**Everything else is additive and backward compatible.**

---

*Generated: 2026-01-20 | Empirica v1.3.4 | develop branch*
