# Interactive Epistemic Checklist - TUI Implementation

## Vision: Provider-Agnostic Workflow Enforcement

**Problem:** AIs forget to log epistemic breadcrumbs regardless of provider (Claude, GPT, Qwen, etc.)

**Solution:** TUI dashboard that actively prompts and validates, not passive observation.

---

## Core Concept: "Epistemic Completeness Score"

Dashboard shows real-time completeness of current session across all breadcrumb types:

```
┌─ EPISTEMIC COMPLETENESS ──────────────────────────────┐
│ Session: abc123 | Duration: 00:45:32                  │
│ Overall Score: ████████░░ 75% (GOOD)                  │
├───────────────────────────────────────────────────────┤
│ ✅ PREFLIGHT     Complete (0:00:45 ago)               │
│ ⚠️  Findings      2 logged (last: 15m ago) [+]        │
│ ⚠️  Unknowns      1 logged (last: 20m ago) [+]        │
│ ❌ Mistakes       0 logged                    [+]     │
│ ❌ Dead Ends      0 logged                    [+]     │
│ ⚠️  Sources       1 logged (GitHub URL)       [+]     │
│ ❌ POSTFLIGHT    Not started                  [!]     │
├───────────────────────────────────────────────────────┤
│ 💡 SUGGESTIONS:                                        │
│ • 15+ min since last finding - log discoveries?       │
│ • No mistakes logged - unusual for 45m session        │
│ • POSTFLIGHT required before ending session           │
└───────────────────────────────────────────────────────┘
```

---

## Three-Phase Checklist Integration

### Phase 1: Pre-Work Validation (Session Start)

**When:** AI opens project or starts work
**Goal:** Ensure proper session initialization

```
┌─ SESSION INITIALIZATION CHECKLIST ────────────────────┐
│                                                        │
│ Required Steps:                                        │
│ [✓] 1. Active session exists                          │
│ [✓] 2. Linked to project: empirica                    │
│ [✗] 3. PREFLIGHT assessment submitted                 │
│ [ ] 4. Project context loaded (bootstrap)             │
│                                                        │
│ ⚠️  Step 3 incomplete!                                 │
│                                                        │
│ Options:                                               │
│ [1] Run PREFLIGHT now (guided)                        │
│ [2] Skip (not recommended)                            │
│ [3] Load from previous session                        │
│                                                        │
│ Press [1-3] or [Esc] to dismiss                       │
└────────────────────────────────────────────────────────┘
```

**How it works:**
1. Dashboard detects new session or session without PREFLIGHT
2. Shows blocking modal (can't dismiss without action)
3. Guides AI through PREFLIGHT creation
4. Only allows work to proceed when checklist complete

**Implementation:**
```python
def validate_session_start(session_id):
    """Check session initialization completeness"""
    db = SessionDatabase()

    checks = {
        "active_session": db.has_active_session(),
        "linked_to_project": db.get_session_project(session_id) is not None,
        "preflight_done": db.has_preflight(session_id),
        "bootstrap_loaded": check_bootstrap_timestamp()
    }

    incomplete = [k for k, v in checks.items() if not v]

    if incomplete:
        return {
            "complete": False,
            "missing": incomplete,
            "suggestions": generate_fix_suggestions(incomplete)
        }

    return {"complete": True, "score": 1.0}
```

---

### Phase 2: During-Work Monitoring (Active Session)

**When:** Continuously while AI works
**Goal:** Prompt for breadcrumbs based on activity patterns

#### Activity-Based Prompts

**Pattern 1: Files Modified → Suggest Findings**
```python
# Dashboard detects git diff
if files_modified_count >= 3 and time_since_last_finding > 10_minutes:
    show_prompt(
        type="finding",
        message="3 files modified in last 10min. Log discoveries?",
        suggestions=[
            "Modified authentication flow to use JWT tokens",
            "Refactored error handling in API endpoints",
            "Custom input..."
        ]
    )
```

**TUI Display:**
```
┌─ 💡 FINDING SUGGESTION ────────────────────────────────┐
│ Activity detected: 3 files modified (last 10 min)      │
│                                                         │
│ Quick log a finding?                                   │
│ [1] Modified auth flow to use JWT tokens              │
│ [2] Refactored error handling in API                  │
│ [3] Custom message...                                  │
│ [Esc] Remind me later                                 │
└────────────────────────────────────────────────────────┘
```

**Pattern 2: Error Messages → Suggest Mistakes**
```python
# Dashboard monitors command outputs for errors
if stderr_contains_error() or exit_code != 0:
    show_prompt(
        type="mistake",
        message="Command failed. Log as mistake for learning?",
        context={
            "command": last_command,
            "error": stderr_snippet,
            "cost": estimate_time_lost()
        }
    )
```

**TUI Display:**
```
┌─ ⚠️  MISTAKE DETECTED ──────────────────────────────────┐
│ Command failed: npm install                            │
│ Error: ENOENT package.json not found                   │
│ Time lost: ~5 minutes                                  │
│                                                         │
│ Log this mistake for future learning?                  │
│                                                         │
│ Root Cause:                                            │
│ [1] Ran command in wrong directory                    │
│ [2] Package.json was deleted accidentally             │
│ [3] Other (specify)...                                │
│                                                         │
│ Prevention:                                            │
│ [Auto] Always verify pwd before npm commands          │
│                                                         │
│ [L] Log Mistake  [S] Skip  [Esc] Dismiss              │
└────────────────────────────────────────────────────────┘
```

**Pattern 3: Uncertainty Keywords → Suggest Unknowns**
```python
# Dashboard watches for uncertainty signals in AI output
uncertainty_keywords = ["unclear", "uncertain", "don't know", "not sure", "might be", "possibly"]

if ai_output_contains(uncertainty_keywords):
    show_prompt(
        type="unknown",
        message="Detected uncertainty. Log as unknown?",
        extract=extracted_uncertainty_phrase
    )
```

**TUI Display:**
```
┌─ ❓ UNCERTAINTY DETECTED ──────────────────────────────┐
│ AI Output: "Token refresh timing is unclear"          │
│                                                        │
│ Log as unknown for investigation?                     │
│ Unknown: "Token refresh timing unclear"                │
│                                                        │
│ [L] Log Now  [I] Investigate First  [Esc] Skip       │
└────────────────────────────────────────────────────────┘
```

**Pattern 4: Investigated but Didn't Work → Suggest Dead End**
```python
# Dashboard detects rollback patterns (git checkout, ctrl-z, file deletion)
if rollback_detected() or large_deletion():
    show_prompt(
        type="deadend",
        message="Approach rolled back. Log as dead end?",
        context={"approach": what_was_tried, "why_failed": infer_reason}
    )
```

**Pattern 5: External References → Suggest Sources**
```python
# Dashboard watches for URLs or file paths in AI output
if url_detected(ai_output) or file_path_mentioned(ai_output):
    show_prompt(
        type="source",
        message="Reference detected. Log as epistemic source?",
        source_url=extracted_url,
        source_type="url" if is_url else "local"
    )
```

**TUI Display:**
```
┌─ 📚 SOURCE DETECTED ────────────────────────────────────┐
│ Reference: https://oauth.net/2/token-refresh/          │
│                                                         │
│ Log as epistemic source?                               │
│                                                         │
│ Type: [1] Documentation  [2] Tutorial  [3] Example    │
│                                                         │
│ Relevance: [H]igh  [M]edium  [L]ow                    │
│                                                         │
│ [L] Log Source  [Esc] Skip                            │
└─────────────────────────────────────────────────────────┘
```

---

### Phase 3: Post-Work Validation (Session End)

**When:** AI signals work complete or session duration > threshold
**Goal:** Ensure CASCADE completeness and knowledge capture

```
┌─ SESSION COMPLETION CHECKLIST ────────────────────────┐
│ Session: abc123 | Duration: 02:15:32                  │
│                                                        │
│ Before ending session:                                 │
│ [✓] 1. PREFLIGHT completed                            │
│ [✓] 2. Work performed (15 commands)                   │
│ [✓] 3. Findings logged (5)                            │
│ [~] 4. Unknowns logged (2) - any resolved?            │
│ [!] 5. Mistakes logged (0) - unusual!                 │
│ [✗] 6. POSTFLIGHT assessment                          │
│                                                        │
│ ⚠️  Completeness: 70% (MEDIUM)                         │
│                                                        │
│ Missing:                                               │
│ • POSTFLIGHT assessment (required)                    │
│ • No mistakes logged (2hr session - likely missed)    │
│ • 2 unknowns unresolved (mark resolved or carry over) │
│                                                        │
│ Actions:                                               │
│ [1] Complete POSTFLIGHT now (guided, 2 min)           │
│ [2] Review unknowns before ending                     │
│ [3] Force end (creates incomplete session marker)     │
│                                                        │
│ Press [1-3] to continue                                │
└────────────────────────────────────────────────────────┘
```

**Guided POSTFLIGHT:**
If user selects [1], dashboard guides through:
```
┌─ GUIDED POSTFLIGHT ─────────────────────────────────────┐
│ Step 1/3: Reassess Knowledge Vectors                   │
│                                                         │
│ How did your knowledge change from PREFLIGHT?          │
│                                                         │
│ KNOW (was: 0.65)    [████████░░] 0.80 ⬆ +0.15         │
│ CONTEXT (was: 0.55) [███████░░░] 0.75 ⬆ +0.20         │
│ UNCERTAINTY (0.70)  [████░░░░░░] 0.35 ⬇ -0.35         │
│                                                         │
│ Auto-detected from activity:                           │
│ • KNOW +0.15 (5 findings logged)                       │
│ • CONTEXT +0.20 (bootstrap loaded, 15 files changed)   │
│ • UNCERTAINTY -0.35 (2 unknowns → resolved)            │
│                                                         │
│ Accept auto-values? [Y]es [E]dit [C]ancel             │
└─────────────────────────────────────────────────────────┘
```

---

## Completeness Scoring Algorithm

```python
def calculate_completeness_score(session_id):
    """
    Calculate 0-1 score for session epistemic completeness.

    Scoring:
    - PREFLIGHT exists: +20%
    - Findings (1+ per 15min): +20%
    - Unknowns tracked: +15%
    - Mistakes logged: +10%
    - Sources cited: +10%
    - Dead ends documented: +5%
    - POSTFLIGHT exists: +20%
    """
    db = SessionDatabase()
    session = db.get_session(session_id)
    duration_min = session.duration.total_seconds() / 60

    score = 0.0

    # PREFLIGHT (20%)
    if db.has_preflight(session_id):
        score += 0.20

    # Findings (20%)
    findings_count = db.count_findings(session_id)
    expected_findings = max(1, duration_min // 15)  # 1 per 15 min
    findings_score = min(findings_count / expected_findings, 1.0) * 0.20
    score += findings_score

    # Unknowns (15%)
    unknowns_count = db.count_unknowns(session_id)
    if unknowns_count > 0:
        score += 0.15  # Any unknowns tracked = good

    # Mistakes (10%)
    mistakes_count = db.count_mistakes(session_id)
    if mistakes_count > 0 or duration_min < 30:
        score += 0.10  # Either logged mistakes or short session (no mistakes expected)

    # Sources (10%)
    sources_count = db.count_epistemic_sources(session_id)
    if sources_count > 0:
        score += 0.10

    # Dead ends (5%)
    deadends_count = db.count_deadends(session_id)
    if deadends_count > 0:
        score += 0.05

    # POSTFLIGHT (20%)
    if db.has_postflight(session_id):
        score += 0.20

    return {
        "score": score,
        "grade": "EXCELLENT" if score >= 0.9 else "GOOD" if score >= 0.7 else "MEDIUM" if score >= 0.5 else "LOW",
        "breakdown": {
            "preflight": 0.20 if db.has_preflight(session_id) else 0,
            "findings": findings_score,
            "unknowns": 0.15 if unknowns_count > 0 else 0,
            "mistakes": 0.10 if mistakes_count > 0 else 0,
            "sources": 0.10 if sources_count > 0 else 0,
            "deadends": 0.05 if deadends_count > 0 else 0,
            "postflight": 0.20 if db.has_postflight(session_id) else 0
        }
    }
```

---

## Provider-Agnostic Activity Detection

**How does dashboard detect activity without Claude Code hooks?**

### Method 1: Database Polling (Universal)
```python
class ActivityMonitor:
    def __init__(self, session_id):
        self.last_check = datetime.now()
        self.session_id = session_id

    def poll(self):
        """Check for activity every 1s"""
        db = SessionDatabase()

        # Detect new entries since last check
        new_findings = db.count_findings_since(self.session_id, self.last_check)
        new_commands = db.count_commands_since(self.session_id, self.last_check)

        # Detect staleness (no activity for 10+ min)
        if (datetime.now() - self.last_check).seconds > 600:
            return {"alert": "stale_session", "message": "No activity for 10 min"}

        self.last_check = datetime.now()
```

### Method 2: Git Watching (Universal)
```python
import watchdog

class GitWatcher:
    def on_modified(self, event):
        """Triggered when files change"""
        if self.is_significant_change(event):
            suggest_finding(context={
                "files_changed": event.src_path,
                "change_type": "modified"
            })
```

### Method 3: Command Logging (Built-in)
Empirica already logs all commands to `command_usage` table:
```python
# Every empirica command writes to DB
db.log_command_usage(
    command_name="finding-log",
    execution_time_ms=45,
    success=True
)

# Dashboard queries this:
recent_commands = db.get_commands_since(last_check)
for cmd in recent_commands:
    if cmd.name == "finding-log":
        update_completeness_score(+5%)  # Positive reinforcement
```

---

## Smart Suggestions Based on Context

### Context: Project Type Detection
```python
def detect_project_type():
    """Infer project type from files"""
    if exists("package.json"):
        return "nodejs"
    elif exists("requirements.txt"):
        return "python"
    elif exists("go.mod"):
        return "golang"
    # ... etc
```

**Tailored Prompts:**
- **Python project + pytest found** → "Run tests and log results as finding?"
- **Node project + package-lock changed** → "Dependency updated. Log reason as finding?"
- **Any project + .env modified** → "Config changed. Document as source?"

---

## Integration with Semantic Index (Qdrant)

**Store this checklist logic as searchable context:**

```python
# At session start
context_query = f"epistemic workflow automation for {project_type} project"
results = qdrant_search(context_query, top_k=3)

# Results include:
# - This checklist doc
# - Project-specific workflow patterns
# - Common mistakes for this project type

# Dashboard shows personalized suggestions
for result in results:
    show_tip(result.content)
```

**Example tip from semantic index:**
```
💡 TIP: This Python project has high test coverage (95%).
   Suggested workflow:
   1. Modify code
   2. Run pytest
   3. Log test results as finding
   4. If test fails → log as mistake with root cause
```

---

## Implementation Phases

### Phase 1: Basic Completeness Tracking (Week 1)
- [ ] Add completeness score calculation to dashboard
- [ ] Show simple checklist (PREFLIGHT/POSTFLIGHT status)
- [ ] Display counts: findings, unknowns, mistakes

### Phase 2: Activity-Based Prompts (Week 2-3)
- [ ] Git file watcher integration
- [ ] Command output monitoring (errors → mistakes)
- [ ] Uncertainty detection (text analysis)
- [ ] Smart suggestions based on activity

### Phase 3: Guided Workflows (Week 4)
- [ ] Interactive PREFLIGHT wizard
- [ ] Interactive POSTFLIGHT wizard
- [ ] Dead end detection (rollback patterns)
- [ ] Source citation prompts

### Phase 4: Semantic Integration (Future)
- [ ] Index this doc in Qdrant
- [ ] Project-type-specific suggestions
- [ ] Learning from past sessions
- [ ] Automated pattern detection

---

## Success Metrics

Track improvement in epistemic completeness:

```sql
-- Before checklist TUI
SELECT AVG(completeness_score) FROM sessions WHERE created < '2025-01-01';
-- Result: 0.45 (45% average)

-- After checklist TUI
SELECT AVG(completeness_score) FROM sessions WHERE created >= '2025-01-01';
-- Target: 0.85 (85% average)
```

**Goals:**
- 90%+ sessions have PREFLIGHT + POSTFLIGHT
- 80%+ sessions have 1+ finding per 15 min
- 50%+ sessions log at least 1 mistake
- 70%+ sessions cite external sources
- 30%+ sessions document dead ends

---

## Provider-Agnostic Design Principles

1. **No Claude-specific hooks** - Works with any AI via TUI
2. **Database-driven** - All detection via DB polling
3. **Git-native** - Uses git for file change detection
4. **Terminal-based** - TUI works over SSH, any environment
5. **MCP-compatible** - Can integrate via MCP server if available
6. **Standalone** - Dashboard runs independently, no IDE required

This makes Empirica truly provider-agnostic while still ensuring workflow compliance.
