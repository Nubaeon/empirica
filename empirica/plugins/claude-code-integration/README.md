# Empirica Integration Plugin for Claude Code

**Epistemic Continuity Across Memory Compacting**

This plugin automatically captures and restores epistemic state when Claude Code compacts conversations, preventing metacognitive drift from context loss.

---

## What It Does

When your conversation gets compacted (context window full):

**Before Compact (PreCompact Hook):**
- Automatically saves current epistemic state as ref-doc
- Captures: vectors, reasoning, findings/unknowns counts
- Creates anchor point for drift detection

**After Compact (SessionStart Hook):**
- Loads project bootstrap (ground truth from SQLite + git)
- Loads pre-compact ref-doc
- Presents evidence for reassessment
- Enables drift detection

---

## How It Works

### The Problem
```
Session before compact: 185k tokens, rich context
          ↓ COMPACT ↓
Session after compact: 5k token summary, context loss
          ⚠️ EPISTEMIC DRIFT ⚠️
```

### The Solution
```
PreCompact Hook:
  └─ empirica check-drift --trigger pre_summary
     └─ Saves: .empirica/ref-docs/pre_summary_<timestamp>.json

COMPACT HAPPENS

SessionStart Hook (source=compact):
  └─ empirica check-drift --trigger post_summary
     └─ Loads: Bootstrap + pre-summary ref-doc
     └─ Presents: Evidence for comparison
```

---

## Installation

### Prerequisites
- Empirica installed: `pip install empirica`
- Active Empirica session (created with `empirica session-create`)

### Enable Plugin

The plugin is already installed and enabled in Claude Code settings:
```
~/.claude/plugins/local/empirica-integration/
```

---

## Quick Start

### 1. Create Empirica Session
```bash
# Create session for current work
empirica session-create --ai-id claude-code-verbose-fix --output json
```

### 2. Set Environment Variable (Recommended)
```bash
# Auto-detect and set latest session
source ~/.claude/plugins/local/empirica-integration/hooks/set-session-env.sh

# OR manually set specific session
export EMPIRICA_SESSION_ID=<your-session-id>

# Add to your .bashrc or .zshrc for persistence:
echo 'source ~/.claude/plugins/local/empirica-integration/hooks/set-session-env.sh' >> ~/.bashrc
```

### 3. Use Empirica Workflow

**Run CASCADE to create checkpoints:**
```bash
# Required for hooks to save snapshots
empirica preflight-submit -  # JSON via stdin
empirica check -              # Optional mid-work gate
empirica postflight-submit -  # Final checkpoint
```

**Work normally:**
- Plugin hooks run automatically on `/compact` or auto-compact
- PreCompact saves epistemic snapshot
- SessionStart loads bootstrap + snapshot
- No manual intervention needed

---

## How Auto-Detection Works

**Hooks auto-detect session using this priority:**

1. **Environment variable:** `$EMPIRICA_SESSION_ID` (highest priority)
2. **Session resolver:** Latest active `claude-code*` session via alias system
3. **Fallback:** Exits silently if no session found

**Supported AI ID patterns:**
- `claude-code-verbose-fix` ✅
- `claude-code` ✅
- `claude-code-<anything>` ✅

### Manual Testing

**Test PreCompact hook:**
```bash
# Simulate hook input
echo '{"session_id":"abc123","trigger":"manual"}' | \
  python3 ~/.claude/plugins/local/empirica-integration/hooks/pre-compact.py
```

**Test PostCompact hook:**
```bash
# Simulate hook input
echo '{"session_id":"abc123","source":"compact"}' | \
  python3 ~/.claude/plugins/local/empirica-integration/hooks/post-compact.py
```

---

## Hook Behavior

### PreCompact Hook

**Triggers:**
- `/compact` (manual)
- Auto-compact (context >90% full)

**Actions:**
1. Reads `EMPIRICA_SESSION_ID` env var
2. Runs `empirica check-drift --trigger pre_summary`
3. Saves checkpoint as ref-doc
4. Prints confirmation to stderr (visible to user)

**Output (stdout):**
```json
{
  "ok": true,
  "trigger": "auto",
  "empirica_session_id": "uuid",
  "snapshot_saved": true,
  "snapshot_path": ".empirica/ref-docs/pre_summary_2025-12-25T14-30-00.json"
}
```

### SessionStart Hook (Post-Compact)

**Triggers:**
- SessionStart with `source: "compact"`

**Actions:**
1. Reads `EMPIRICA_SESSION_ID` env var
2. Runs `empirica check-drift --trigger post_summary`
3. Loads bootstrap + pre-summary ref-doc
4. Prints evidence to stderr (visible to user)

**Output (stdout):**
```json
{
  "ok": true,
  "empirica_session_id": "uuid",
  "pre_summary": {
    "timestamp": "2025-12-25T14-30-00",
    "vectors": {"know": 0.75, "uncertainty": 0.35}
  },
  "bootstrap": {
    "findings_count": 12,
    "unknowns_count": 8,
    "goals_count": 2,
    "incomplete_goals": 1
  },
  "inject_context": true
}
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EMPIRICA_SESSION_ID` | Yes | Active Empirica session UUID |
| `CLAUDE_PLUGIN_ROOT` | Auto | Plugin directory (set by Claude Code) |

**How to set:**
```bash
# At session start
export EMPIRICA_SESSION_ID=$(empirica session-create --ai-id claude-code --output json | jq -r '.session_id')

# Or use existing session
export EMPIRICA_SESSION_ID=$(empirica sessions-list --limit 1 --output json | jq -r '.[0].session_id')
```

---

## What You'll See

### Before Compact
```
📸 Empirica: Pre-compact snapshot saved
   Session: ae16acaf...
   Trigger: auto
   Snapshot: pre_summary_2025-12-25T14-30-00.json
```

### After Compact
```
🔄 Empirica: Post-compact context loaded

📚 Bootstrap Evidence (Ground Truth):
   Findings: 12
   Unknowns: 8
   Goals: 2 (1 incomplete)

📊 Your Pre-Compact State:
   Captured: 2025-12-25T14-30-00
   Vectors: 0.75 KNOW, 0.35 UNCERTAINTY

💡 Recommendation: Run CHECK or PREFLIGHT to reassess based on bootstrap evidence.
   System will compare to detect drift.
```

---

## Troubleshooting

### Plugin Not Running

**Check plugin is loaded:**
```bash
ls -la ~/.claude/plugins/local/empirica-integration/
```

**Check hooks.json syntax:**
```bash
cat ~/.claude/plugins/local/empirica-integration/hooks/hooks.json | jq .
```

### No EMPIRICA_SESSION_ID

**Error:**
```json
{"ok": true, "skipped": true, "reason": "No active Empirica session detected"}
```

**Fix:**
```bash
export EMPIRICA_SESSION_ID=<your-session-id>
```

### Hook Timeout

If hooks take >30s, increase timeout in `hooks.json`:
```json
{
  "type": "command",
  "command": "...",
  "timeout": 60  // Increase to 60s
}
```

---

## Technical Details

### Hook Flow

```
PreCompact (before compact):
├─ Read hook input from stdin (Claude Code provides session_id, trigger)
├─ Check EMPIRICA_SESSION_ID env var
├─ Run: empirica check-drift --session-id $ID --trigger pre_summary
├─ Save checkpoint as: .empirica/ref-docs/pre_summary_<timestamp>.json
└─ Exit 0 (success) or 2 (blocking error)

SessionStart (after compact, source=compact):
├─ Read hook input from stdin (Claude Code provides session_id, source)
├─ Check EMPIRICA_SESSION_ID env var
├─ Run: empirica check-drift --session-id $ID --trigger post_summary
├─ Load: Bootstrap + pre-summary ref-doc
├─ Present evidence in stderr (user-visible)
└─ Exit 0 (success) or 1 (non-blocking error)
```

### Why This Matters

**Without this plugin:**
- Compact → Context loss
- AI forgets findings, unknowns, goals
- Work is repeated, epistemic drift accumulates

**With this plugin:**
- Compact → Anchor captured
- Bootstrap restores ground truth
- Drift detected and corrected
- Epistemic continuity maintained

---

## MIT License

Empirica is MIT licensed. Anyone can use this plugin, even without Empirica.

The hook pattern (PreCompact → SessionStart) is useful for ANY tool that needs:
- State preservation across compacts
- Context restoration
- Drift detection
- Session continuity

---

## Further Reading

- Empirica docs: `~/.empirica/core-docs/`
- check-drift implementation: `empirica/cli/command_handlers/monitor_commands.py`
- Claude Code hooks: Claude Code documentation

---

**Status:** ✅ Active (hooks wire to Empirica check-drift)
**Tested:** Manual simulation (integration test pending)
**Impact:** Solves 5 months of memory compacting issues
