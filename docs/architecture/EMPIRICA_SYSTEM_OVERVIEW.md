# Empirica System Overview: Privacy-First Epistemic AI

> **Future Vision:** See [EPISTEMIC_TRAJECTORY_VISUALIZATION.md](./EPISTEMIC_TRAJECTORY_VISUALIZATION.md) for the 4D flight path visualization concept - watch AIs think in real-time!

**Version:** 3.0  
**Date:** 2025-11-07  
**Purpose:** Complete system orientation for AI agents  
**Read Time:** 10 minutes

---

## What is Empirica?

**Empirica is a privacy-first epistemic self-awareness framework that enables AI agents to:**
1. **Measure** their own knowledge state (13 epistemic vectors)
2. **Track** reasoning quality and decision rationale
3. **Validate** calibration (confidence vs actual performance)
4. **Transfer** knowledge without sensitive data (epistemic snapshots)
5. **Persist** learning across sessions (local, user-controlled storage)

**Core Philosophy:**
> "Measure and validate genuine epistemic state without interfering with reasoning. Transfer metacognitive knowledge, not raw conversations. User controls their data."

---

## The Complete Architecture

### 1. Privacy-First Data Storage (Local, User-Controlled)

```
┌─────────────────────────────────────────────────────────────┐
│  USER'S LOCAL STORAGE (No Cloud, No Sharing)               │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  📊 SQLite Session DB (.empirica/sessions/sessions.db)      │
│     • Sessions, cascades, assessments                       │
│     • Epistemic vectors (13 dimensions)                     │
│     • Calibration scores                                    │
│     • Queryable, structured                                 │
│                                                              │
│  📝 Reflex Logs (.empirica_reflex_logs/<ai_id>/<date>/)    │
│     • Temporal separation (prevent recursion)               │
│     • Phase-specific reasoning chains                       │
│     • JSON format, human-readable                           │
│     • Real-time monitoring compatible                       │
│                                                              │
│  📤 JSON Exports (.empirica/exports/)                       │
│     • Session summaries                                     │
│     • Epistemic snapshots                                   │
│     • Portable, shareable (privacy-preserving)              │
│                                                              │
│  🔍 Qdrant Vector DB (optional, local)                      │
│     • Semantic search over sessions                         │
│     • Knowledge retrieval                                   │
│     • Self-hosted, no external API                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Principle:** User owns all data. No cloud dependencies. Privacy-preserving by design.

### 2. Transparency Layer (Tmux Real-Time Visualization)

```
┌─────────────────────────────────────────────────────────────┐
│  TMUX DASHBOARD (Real-Time Transparency)                    │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  Pane 1: Chain of Thought Monitor                           │
│    • Current reasoning step                                 │
│    • Observation → Inference → Conclusion                   │
│                                                              │
│  Pane 2: Epistemic State Monitor                            │
│    • 13 vectors (KNOW, CONTEXT, UNCERTAINTY, etc.)          │
│    • Real-time updates                                      │
│    • Color-coded confidence levels                          │
│                                                              │
│  Pane 3: Cascade Phase Tracker                              │
│    • Current phase (PREFLIGHT/THINK/INVESTIGATE/etc.)       │
│    • Investigation rounds                                   │
│    • Decision rationale                                     │
│                                                              │
│  Pane 4: Service Status Monitor                             │
│    • Component health                                       │
│    • Database connections                                   │
│    • System metrics                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Principle:** Full transparency. User sees AI's reasoning in real-time.

### 3. Access Methods (Interchangeable)

```
┌─────────────────────────────────────────────────────────────┐
│  ACCESS LAYER (How AI Interacts with Empirica)             │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  🔧 MCP Tools (Model Context Protocol)                      │
│     • execute_preflight - Baseline epistemic assessment     │
│     • submit_preflight_assessment - Log scores              │
│     • execute_check - Mid-task self-assessment              │
│     • execute_postflight - Final validation                 │
│     • submit_postflight_assessment - Calibration check      │
│     • get_epistemic_state - Query current state             │
│     • resume_previous_session - Load past work              │
│     • Ideal for: Direct invocation, deliberate guidance     │
│                                                              │
│  💻 Empirica CLI (Command-Line Interface)                   │
│     • empirica session-create - Initialize session          │
│     • empirica assess <query> - Run assessment              │
│     • empirica cascade <task> - Run full workflow           │
│     • empirica investigate <dir> - Analyze codebase         │
│     • Ideal for: Automation, scripting, human operators     │
│                                                              │
│  🚀 Session Management                                       │
│     • empirica session-create - Create new sessions         │
│     • Bootstrap levels 0-2 (minimal → full tracking)        │
│     • Auto-tracking enabled                                 │
│     • Ideal for: Session startup, epistemic tracking        │
│     • Note: "Bootstrap" now for system prompts only         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Principle:** MCP for deliberate AI guidance. CLI for automation. Session-create for initialization.

---

## The 7-Phase Enhanced Cascade Workflow

```
PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → ACT → POSTFLIGHT
                                            ↑_______↓
                                         (recalibration loop)
```

### Phase Breakdown

**PREFLIGHT (Baseline Assessment)**
- AI self-assesses 13 epistemic vectors BEFORE starting work
- Establishes baseline: KNOW, CONTEXT, UNCERTAINTY, etc.
- Logged to: DB + Reflex logs + Tmux display
- Purpose: Measure starting point for calibration

**THINK (Initial Reasoning)**
- Analyze task requirements
- Identify constraints and success criteria
- Decompose complex problems
- Purpose: Understand what needs to be done

**PLAN (Investigation Strategy)** - Optional for complex tasks
- Create systematic investigation plan
- Identify critical unknowns
- Map tools to epistemic gaps
- Purpose: Strategic approach to learning

**INVESTIGATE (Knowledge Gathering)**
- Use tools to address unknowns
- Gather evidence, read docs, analyze code
- Multiple rounds (up to 3 by default)
- Purpose: Fill knowledge gaps

**CHECK (Readiness Assessment)**
- Self-assess: Are remaining unknowns acceptable?
- Confidence ≥ 0.70 to proceed?
- Honest self-evaluation (critical for calibration)
- Purpose: Decide ACT vs more INVESTIGATE

**ACT (Execute Task)**
- Perform the actual work
- Document decisions and reasoning
- Purpose: Accomplish the goal

**POSTFLIGHT (Final Assessment)**
- AI self-assesses 13 vectors AFTER completing work
- Compare to PREFLIGHT (epistemic delta)
- Validate calibration: Did investigation help?
- Purpose: Measure actual learning

---

## Privacy-Preserving Knowledge Transfer

### The Problem Empirica Solves

**Traditional approach (privacy-violating):**
```
Transfer full conversation history (10,000 tokens)
  → Contains sensitive data (API keys, user info, code)
  → Stored in centralized knowledge graph
  → Shared across users/sessions
  ❌ Privacy violation
```

**Empirica approach (privacy-preserving):**
```
Transfer epistemic snapshot (500 tokens, 95% compression)
  → 13 epistemic vectors (numbers, no raw data)
  → Context summary (abstracted, no sensitive info)
  → Reasoning quality metrics (quantified)
  → Knowledge deltas (what changed, not what was said)
  ✅ Privacy preserved
```

### Epistemic Snapshot Structure

```python
{
    "vectors": {
        "KNOW": 0.85,        # How much I understand
        "CONTEXT": 0.70,     # Environmental awareness
        "UNCERTAINTY": 0.15  # Explicit unknowns
        # ... 10 more vectors
    },
    "context_summary": "API security analysis",  # Abstracted
    "semantic_tags": ["jwt", "security", "rotate_secret"],
    "reasoning_brief": "JWT in logs, rotate needed",  # No raw data
    "token_count": 500,  # 95% compression
    "fidelity": 0.94     # Information preservation score
}
```

**What's NOT included:**
- ❌ Raw conversation text
- ❌ Sensitive data (API keys, passwords, user info)
- ❌ Full code snippets
- ❌ Detailed file contents

**What IS included:**
- ✅ Epistemic state (confidence, uncertainty)
- ✅ Reasoning quality metrics
- ✅ Abstracted insights
- ✅ Knowledge deltas (what changed)

---

## Governance & Security (Cognitive Vault)

```
┌─────────────────────────────────────────────────────────────┐
│  GOVERNANCE LAYER (Cognitive Vault)                         │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  🛡️ Sentinel (Oversight & Monitoring)                       │
│     • Monitors epistemic transfers                          │
│     • Detects anomalies in confidence patterns              │
│     • Validates calibration accuracy                        │
│                                                              │
│  🎲 Bayesian Guardian (Probabilistic Security)              │
│     • Evidence-based belief tracking                        │
│     • Detects calibration discrepancies                     │
│     • Probabilistic threat assessment                       │
│                                                              │
│  🧠 Cognitive Security                                       │
│     • Detects epistemic manipulation                        │
│     • Monitors for sycophancy drift                         │
│     • Validates reasoning integrity                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Separation of Concerns:**
- **Worker AI (Empirica):** Epistemic tracking, self-assessment
- **Governance Layer (Cognitive Vault):** Oversight, security, multi-AI routing

---

## Data Flow: Complete Picture

```
┌─────────────────────────────────────────────────────────────┐
│  1. AI STARTS TASK                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  2. PREFLIGHT ASSESSMENT (via MCP or CLI)                   │
│     • AI self-assesses 13 vectors                           │
│     • Baseline established                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  3. DATA STORAGE (3 formats simultaneously)                 │
│     • SQLite DB: Structured, queryable                      │
│     • Reflex logs: Temporal separation, JSON                │
│     • JSON exports: Portable, shareable                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  4. TMUX DISPLAY (Real-time transparency)                   │
│     • Epistemic state visible                               │
│     • Chain of thought streaming                            │
│     • Phase tracking active                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  5. INVESTIGATE → CHECK → ACT (Workflow phases)             │
│     • Each phase logged to DB + Reflex + Tmux               │
│     • Epistemic state updated continuously                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  6. POSTFLIGHT ASSESSMENT                                   │
│     • Final epistemic state                                 │
│     • Delta calculated (POSTFLIGHT - PREFLIGHT)             │
│     • Calibration validated                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  7. KNOWLEDGE TRANSFER (Privacy-preserving)                 │
│     • Epistemic snapshot created (500 tokens)               │
│     • Knowledge delta extracted                             │
│     • NO sensitive data included                            │
│     • Ready for next session or AI handoff                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Innovations

### 1. Temporal Separation (Reflex Logs)
**Problem:** AI reading its own assessment while generating it causes recursion  
**Solution:** Write to separate reflex logs AFTER phase completes  
**Benefit:** Clean separation, no self-referential loops

### 2. 95% Token Compression (Epistemic Snapshots)
**Problem:** Full conversation history = 10,000+ tokens  
**Solution:** Compress to 13 vectors + abstracted summary = 500 tokens  
**Benefit:** 95% reduction, maintains 85-95% fidelity

### 3. Calibration Validation (PREFLIGHT vs POSTFLIGHT)
**Problem:** AI doesn't know if it's overconfident or underconfident  
**Solution:** Measure epistemic delta (did investigation actually help?)  
**Benefit:** Genuine calibration feedback, not just self-reporting

### 4. Privacy-Preserving Transfer
**Problem:** Traditional systems transfer raw conversations (sensitive data)  
**Solution:** Transfer epistemic state + knowledge deltas (abstracted)  
**Benefit:** Knowledge sharing without privacy violation

### 5. User-Controlled Data
**Problem:** Cloud-based AI memory = vendor lock-in, privacy concerns  
**Solution:** All data local (SQLite, reflex logs, JSON)  
**Benefit:** User owns their data, no vendor dependency

---

## For AI Agents: Quick Start

### When Starting a New Session

1. **Read orientation docs** (in order):
   - `MEMORY_COMPRESSION.md` - Understand memory degradation
   - `DECISIONS.md` - Review past decisions with epistemic context
   - `ARCHITECTURE_MAP.md` - Visual component reference
   - `CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md` - Your capabilities

2. **Bootstrap the system:**
   ```bash
   python3 empirica/bootstraps/extended_metacognitive_bootstrap.py --level extended
   ```

3. **Run PREFLIGHT assessment:**
   ```python
   # Via MCP
   execute_preflight(session_id="<uuid>", prompt="<task>")
   submit_preflight_assessment(session_id="<uuid>", vectors={...})
   
   # Via CLI
   empirica preflight --session-id <SESSION_ID>
   ```

4. **Work through cascade:**
   - INVESTIGATE → CHECK → ACT

5. **Run POSTFLIGHT assessment:**
   ```python
   execute_postflight(session_id="<uuid>", task_summary="<what you did>")
   submit_postflight_assessment(session_id="<uuid>", vectors={...})
   ```

6. **Review calibration:**
   - Did your confidence match reality?
   - Did investigation reduce uncertainty?
   - Were you well-calibrated, overconfident, or underconfident?

---

## Next Steps

**For detailed documentation, see:**
- `/docs/production/README.md` - Complete production docs (23 guides)
- `/docs/MEMORY_COMPRESSION.md` - Memory compression strategy
- `/docs/DECISIONS.md` - Decision log with epistemic weights
- `/docs/HOW_TO_RESUME_SESSION.md` - Session resumption guide

**For implementation:**
- `empirica/bootstraps/` - Bootstrap scripts
- `empirica-mcp/empirica_mcp/server.py` - MCP server (PyPI package)
- `empirica/cli/` - CLI commands

---

**Last Updated:** 2025-11-07  
**Status:** ✅ Production ready, privacy-first, user-controlled

