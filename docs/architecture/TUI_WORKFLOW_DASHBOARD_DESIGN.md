# Empirica: TUI Workflow Dashboard Design

**Purpose:** To provide a simple, terminal-based, provider-agnostic dashboard that actively prompts and validates AI activity, ensuring adherence to Empirica's epistemic workflow. It aims to prevent AIs from forgetting to log breadcrumbs and complete the CASCADE workflow, clearly showing active context to prevent accidental writes to the wrong database.

---

## Vision: Provider-Agnostic Workflow Enforcement

**Problem:** AIs often forget to log epistemic breadcrumbs and complete the CASCADE workflow, regardless of the provider (Claude, GPT, Qwen, etc.). This leads to epistemic incompleteness and reduced learning.

**Solution:** An interactive Terminal User Interface (TUI) dashboard that moves beyond passive observation to actively prompt, guide, and validate AI agents through the Empirica workflow.

---

## Core Concept: "Epistemic Completeness Score"

The dashboard displays a real-time "Epistemic Completeness Score" for the current session, tracking adherence to Empirica's principles across all breadcrumb types and CASCADE phases.

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

## Dashboard Layout (80x24 Terminal)

The primary interface for the TUI is an 80x24 terminal window designed for clear, concise information display.

```
┌─ EMPIRICA PROJECT MONITOR ───────────────────────────────┐
│ 📁 Project: empirica                                      │
│ 🗄️  Database: /empirical-ai/empirica/.empirica/sessions/ │
│ 📂 Git Repo: /home/yogapad/empirical-ai/empirica         │
│ 🆔 Active Session: abc123 (AI: claude-code)              │
│ ⏱️  Session Time: 00:15:32                                │
├───────────────────────────────────────────────────────────┤
│ 🎯 CURRENT ACTIVITY                                       │
│ Phase: CHECK (Cycle 2)                                    │
│ Confidence: ████████░░ 75% (MEDIUM)                       │
│ Status: Investigating authentication flow                 │
│ Time in phase: 3m 45s                                     │
├───────────────────────────────────────────────────────────┤
│ 📊 EPISTEMIC STATE                                        │
│ Engagement    ██████████ 0.85                             │
│ Know          ███████░░░ 0.70 ⬆ +0.15                     │
│ Context       ██████░░░░ 0.60 ⬆ +0.10                     │
│ Uncertainty   █████░░░░░ 0.45 ⬇ -0.20                     │
├───────────────────────────────────────────────────────────┤
│ 📝 RECENT COMMANDS (last 5)                               │
│ 14:32:15 finding-log "Found OAuth2 refresh pattern"      │
│ 14:30:42 check --confidence 0.75 → proceed               │
│ 14:28:10 unknown-log "MFA behavior unclear"              │
│ 14:25:33 preflight-submit --session-id abc123            │
│ 14:23:01 session-create --ai-id claude-code              │
├───────────────────────────────────────────────────────────┤
│ 💡 SUGGESTIONS                                            │
│ • Confidence at 75% - ready to proceed                    │
│ • 2 unknowns logged - consider investigation             │
├───────────────────────────────────────────────────────────┤
│ [Q] Quit  [R] Refresh  [C] Clear  [H] Help               │
└───────────────────────────────────────────────────────────┘
```

---

## Three-Phase Workflow Integration

The TUI dashboard integrates active guidance across three key phases of the AI workflow:

### Phase 1: Pre-Work Validation (Session Start)

**When:** AI opens a project or starts new work.
**Goal:** Ensure proper session initialization and PREFLIGHT assessment.
*   The dashboard detects a new session or one without a completed PREFLIGHT.
*   A blocking modal is displayed, guiding the AI through essential setup steps.
*   Work proceeds only when the checklist is complete.

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

### Phase 2: During-Work Monitoring (Active Session)

**When:** Continuously while the AI is working within an active session.
**Goal:** Proactively prompt the AI for epistemic breadcrumbs based on detected activity patterns.

#### Activity-Based Prompts (Action Hooks)

The dashboard monitors various activity signals to trigger contextual prompts:

*   **Files Modified → Suggest Findings:**
    *   **Trigger:** `files_modified_count >= 3` and `time_since_last_finding > 10_minutes`.
    *   **Prompt:** "3 files modified in last 10min. Log discoveries?"
*   **Error Messages → Suggest Mistakes:**
    *   **Trigger:** Command output contains error or non-zero exit code.
    *   **Prompt:** "Command failed. Log this mistake for future learning?" Guides through root cause and prevention.
*   **Uncertainty Keywords → Suggest Unknowns:**
    *   **Trigger:** AI output contains keywords like "unclear," "uncertain," "don't know."
    *   **Prompt:** "Detected uncertainty. Log as unknown for investigation?"
*   **Investigated but Didn't Work → Suggest Dead End:**
    *   **Trigger:** Rollback patterns (git checkout, large deletions) detected.
    *   **Prompt:** "Approach rolled back. Log as dead end?"
*   **External References → Suggest Sources:**
    *   **Trigger:** URLs or file paths detected in AI output.
    *   **Prompt:** "Reference detected. Log as epistemic source?"

#### Example Action Hook Triggered (Low Confidence)

```
AI hits CHECK phase with confidence=0.35

Dashboard detects: confidence < 0.4

Shows interactive prompt:
┌─ ⚠️  LOW CONFIDENCE ────────────────────────┐
│ AI has low confidence (35%)                │
│ Investigate further or proceed?            │
│ [1] Investigate (Recommended)              │
│ [2] Proceed with Caution                   │
└────────────────────────────────────────────┘

User presses [1]

Dashboard writes JSON config to /tmp/action_response.json:
{
  "action": "investigate",
  "reason": "Low confidence",
  "timestamp": "2025-12-25T14:30:00Z"
}

AI reads action and continues investigation cycle
```

### Phase 3: Post-Work Validation (Session End)

**When:** AI signals work completion or session duration exceeds a threshold.
**Goal:** Ensure CASCADE completeness and comprehensive knowledge capture.
*   A checklist is presented summarizing completeness (PREFLIGHT, Findings, Unknowns, Mistakes, etc.).
*   Prompts for missing elements, especially POSTFLIGHT.
*   **Guided POSTFLIGHT:** If selected, the dashboard guides the AI through reassessing knowledge vectors and confirming epistemic deltas.

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
│                                                         │
│ Press [1-3] to continue                                │
└────────────────────────────────────────────────────────┘
```

---

## Epistemic Completeness Scoring Algorithm

```python
def calculate_completeness_score(session_id):
    """
    Calculate 0-1 score for session epistemic completeness.

    Scoring:
    - PREFLIGHT exists: +20%
    - Findings (1+ per 15min): +20%
    - Unknowns tracked: +15% (any tracked is good)
    - Mistakes logged: +10% (any logged or short session)
    - Sources cited: +10%
    - Dead ends documented: +5%
    - POSTFLIGHT exists: +20%
    """
    # ... (implementation details as per INTERACTIVE_CHECKLIST_TUI.md)
    pass
```

---

## Data Sources & Activity Detection

The TUI dashboard leverages various data sources and detection methods to monitor AI activity and generate prompts:

### 1. Project Context (Static - Read Once)
*   `empirica.config.path_resolver.debug_paths()` provides git root, session DB path, etc.

### 2. Active Session (Poll Every 1s)
*   SQL queries to `sessions` table for the most recent active session.

### 3. Latest Epistemic State (Poll Every 1s)
*   SQL queries to `reflexes` table for the latest epistemic vectors and phase.

### 4. Recent Activity
*   **Database Polling:** Universal method for detecting new findings, unknowns, commands, etc.
*   **Git Watching:** Monitors file changes to suggest findings.
*   **Command Logging:** Empirica logs all CLI commands to the `command_usage` table, allowing positive reinforcement for compliance.

---

## Provider-Agnostic Design Principles

The TUI Dashboard is designed to be highly compatible and flexible:
1.  **No Claude-specific hooks:** Works with any AI, relying on database polling and Git watching.
2.  **Database-driven:** All detection and state management are via direct DB access.
3.  **Git-native:** Utilizes Git for file change detection.
4.  **Terminal-based:** Pure TUI, compatible with SSH and various terminal environments.
5.  **MCP-compatible:** Can integrate via MCP server if available.
6.  **Standalone:** Operates independently without requiring an IDE.

---

## Advantages Over Web Dashboard

*   ✅ **SSH-friendly:** Works seamlessly over SSH without port forwarding.
*   ✅ **Tmux-compatible:** Designed to fit efficiently within a terminal split pane.
*   ✅ **Zero overhead:** No web server or WebSockets required.
*   ✅ **Direct DB access:** Fast and efficient data retrieval without an HTTP layer.
*   ✅ **Terminal native:** Supports keyboard shortcuts and easy copy-paste of text.

---

## Integration with Semantic Index (Qdrant)

The dashboard can integrate with a Qdrant-based semantic index to provide project-type-specific and context-aware workflow suggestions. This allows the system to learn from past successful sessions and offer personalized best practices.

---

## Implementation Details

### Tech Stack
*   **Python `textual`:** Modern TUI framework (reactive, component-based).
*   **SQLite:** Direct database queries.
*   **`inotify` (Linux):** File watching for activity detection.

### File Structure
```
empirica/tui/
├── __init__.py
├── dashboard.py          # Main TUI app
├── widgets/              # Reusable UI components
│   ├── project_header.py
│   ├── activity_panel.py
│   ├── vectors_panel.py
│   ├── commands_log.py
│   └── action_prompt.py  # Interactive prompt widget
└── monitors/             # Background data polling and watching
    ├── session_monitor.py
    └── db_watcher.py
```

### Main Command
```bash
empirica dashboard
```
Launches the TUI, automatically detects the current project, and polls the database for updates.

### Implementation Phases
*   **Phase 1: Basic Completeness Tracking:** Implement core score calculation and display.
*   **Phase 2: Activity-Based Prompts:** Integrate Git watching, command monitoring, uncertainty detection.
*   **Phase 3: Guided Workflows:** Develop interactive wizards for PREFLIGHT/POSTFLIGHT.
*   **Phase 4: Semantic Integration:** (Future) Integrate with Qdrant for context-aware suggestions.

---

## Success Metrics

The primary goal is to significantly improve epistemic completeness:
*   **Before TUI:** Average completeness score of ~45%.
*   **Target (After TUI):** Average completeness score of ~85%.

**Specific Goals:**
*   90%+ sessions have PREFLIGHT + POSTFLIGHT.
*   80%+ sessions have 1+ finding per 15 min.
*   50%+ sessions log at least 1 mistake.
*   70%+ sessions cite external sources.
*   30%+ sessions document dead ends.

---

## Future Enhancements & Workspace Dashboard

*   **Multi-session view:** Show all active sessions in the current project.
*   **Historical playback:** Replay past session's epistemic trajectory.
*   **Custom themes:** Dark/light mode.
*   **Workspace Dashboard (Premium Feature):** Extend to workspace-level for multi-project monitoring.

---

This dashboard serves as a crucial interface for guiding AI agents towards robust epistemic practices.
