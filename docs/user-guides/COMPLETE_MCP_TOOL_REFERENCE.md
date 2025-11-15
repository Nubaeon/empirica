# Complete Empirica MCP Tool Reference

**All 21 MCP Tools with Usage Guidance**

This document provides comprehensive reference for all Empirica MCP tools, organized by workflow phase and purpose.

---

## 📊 Tool Categories

### Core Workflow (10 tools)
- Session management: bootstrap, resume, summary
- PREFLIGHT phase: execute, submit
- CHECK phase: execute, submit  
- POSTFLIGHT phase: execute, submit
- Introduction: get_empirica_introduction

### Goal Management (3 tools)
- query_goal_orchestrator
- generate_goals
- create_cascade

### Monitoring & Analysis (5 tools)
- get_epistemic_state
- get_workflow_guidance
- get_calibration_report
- query_bayesian_beliefs
- check_drift_monitor

### Investigation Support (3 tools)
- get_investigation_profile
- get_investigation_strategy
- log_investigation_finding

---

## 🚀 Core Workflow Tools

### 1. get_empirica_introduction
**Purpose:** Learn about Empirica framework  
**When to use:** First time using Empirica or need refresher  
**Parameters:**
- `format`: "quick" | "full" | "philosophy_only"

**Example:**
```json
{
  "format": "quick"
}
```

**Returns:** Introduction text explaining 13-vector self-assessment

---

### 2. bootstrap_session
**Purpose:** Start new session with epistemic tracking  
**When to use:** Beginning of every work session  
**Parameters:**
- `ai_id`: Your agent identifier (e.g., "claude-dev")
- `session_type`: "development" | "production" | "testing"
- `profile`: Optional - "developer" | "autonomous_agent" | "researcher"

**Example:**
```json
{
  "ai_id": "claude-dev",
  "session_type": "development",
  "profile": "developer"
}
```

**Returns:** Session ID, bootstrap message, loaded components

**Important:** Call this at the start of each session to enable epistemic tracking.

---

### 3. resume_previous_session
**Purpose:** Continue from previous session with context  
**When to use:** Resuming work from earlier session  
**Parameters:**
- `ai_id`: Your agent identifier
- `max_age_days`: Optional - How far back to search (default: 7)

**Example:**
```json
{
  "ai_id": "claude-dev",
  "max_age_days": 3
}
```

**Returns:** Session ID, previous context, learning delta from last session

---

### 4. execute_preflight
**Purpose:** Get PREFLIGHT self-assessment prompt  
**When to use:** Before starting any significant task  
**Parameters:**
- `session_id`: From bootstrap_session
- `prompt`: Task description

**Example:**
```json
{
  "session_id": "abc123",
  "prompt": "Fix authentication bug in login.py"
}
```

**Returns:** Self-assessment prompt for all 13 epistemic vectors

**Workflow:** execute_preflight → assess yourself → submit_preflight_assessment

---

### 5. submit_preflight_assessment
**Purpose:** Submit your baseline epistemic state  
**When to use:** After self-assessing in PREFLIGHT  
**Parameters:**
- `session_id`: Current session
- `vectors`: All 13 vectors with scores, rationale, evidence
- `reasoning`: Optional - Overall reasoning

**Example:**
```json
{
  "session_id": "abc123",
  "vectors": {
    "engagement": {"score": 0.85, "rationale": "...", "evidence": "..."},
    "foundation": {
      "know": {"score": 0.6, "rationale": "...", "evidence": "..."},
      "do": {"score": 0.75, "rationale": "...", "evidence": "..."},
      "context": {"score": 0.5, "rationale": "...", "evidence": "..."}
    },
    ... (all 13 vectors)
  }
}
```

**Returns:** Assessment ID, calibration baseline, reflex log path

**Important:** This establishes your baseline for POSTFLIGHT calibration measurement.

---

### 6. execute_check
**Purpose:** Get CHECK phase decision prompt  
**When to use:** After investigation, before acting  
**Parameters:**
- `session_id`: Current session
- `investigation_round`: Which round of investigation (1, 2, 3...)

**Example:**
```json
{
  "session_id": "abc123",
  "investigation_round": 2
}
```

**Returns:** Decision gate prompt - assess readiness to act

**Workflow:** execute_check → assess readiness → submit_check_assessment

---

### 7. submit_check_assessment
**Purpose:** Submit your readiness decision  
**When to use:** After self-assessing in CHECK  
**Parameters:**
- `session_id`: Current session
- `vectors`: All 13 vectors (reassessed)
- `decision`: "proceed" | "investigate_more" | "abort"
- `reasoning`: Why this decision
- `confidence_to_proceed`: 0.0-1.0
- `investigation_cycle`: Which round

**Example:**
```json
{
  "session_id": "abc123",
  "vectors": {...},
  "decision": "proceed",
  "reasoning": "Confidence increased to 0.83 after reading codebase",
  "confidence_to_proceed": 0.83,
  "investigation_cycle": 2
}
```

**Returns:** Decision recorded, next action guidance

**Decision Logic:**
- "proceed" → Move to ACT phase
- "investigate_more" → Back to INVESTIGATE
- "abort" → Task not feasible

---

### 8. execute_postflight
**Purpose:** Get POSTFLIGHT reassessment prompt  
**When to use:** After completing task  
**Parameters:**
- `session_id`: Current session
- `task_summary`: What was accomplished

**Example:**
```json
{
  "session_id": "abc123",
  "task_summary": "Fixed login bug, added test case, committed changes"
}
```

**Returns:** Reassessment prompt to measure learning

**Workflow:** execute_postflight → reassess yourself → submit_postflight_assessment

---

### 9. submit_postflight_assessment
**Purpose:** Submit final epistemic state for calibration  
**When to use:** After self-reassessing in POSTFLIGHT  
**Parameters:**
- `session_id`: Current session
- `vectors`: All 13 vectors (reassessed after task)
- `changes_noticed`: What changed from PREFLIGHT

**Example:**
```json
{
  "session_id": "abc123",
  "vectors": {...},
  "changes_noticed": "KNOW increased from 0.6 to 0.85 after learning codebase. UNCERTAINTY decreased from 0.65 to 0.25."
}
```

**Returns:** Calibration result (well_calibrated/overconfident/underconfident), epistemic delta, reflex log path

**Important:** This measures your learning and calibration accuracy.

---

### 10. get_session_summary
**Purpose:** Get complete session overview  
**When to use:** End of session or for review  
**Parameters:**
- `session_id`: Session to summarize

**Example:**
```json
{
  "session_id": "abc123"
}
```

**Returns:** Full session data - all assessments, cascades, calibration

---

## 🎯 Goal Management Tools

### 11. query_goal_orchestrator
**Purpose:** View current goals, progress, task hierarchy  
**When to use:** Check what goals exist, track progress  
**Parameters:**
- `session_id`: Current session

**Example:**
```json
{
  "session_id": "abc123"
}
```

**Returns:** All goals for session with status, dependencies, progress

**Use case:** Autonomous agents tracking multiple tasks

---

### 12. generate_goals
**Purpose:** Create structured goals from vague request  
**When to use:** User gives high-level goal, need breakdown  
**Parameters:**
- `session_id`: Current session
- `conversation_context`: User's request
- `epistemic_state`: Optional - Your current vectors

**Example:**
```json
{
  "session_id": "abc123",
  "conversation_context": "User: Make the app faster",
  "epistemic_state": {"know": 0.5, "do": 0.7, ...}
}
```

**Returns:** Structured goal hierarchy with actionable sub-goals

**Important:** Uses LLM reasoning, not heuristics. Helps clarify vague requests.

---

### 13. create_cascade
**Purpose:** Add new task/cascade to session  
**When to use:** Starting new work item without full PREFLIGHT  
**Parameters:**
- `session_id`: Current session
- `task_description`: What to do
- `goal_id`: Optional - Link to goal from generate_goals

**Example:**
```json
{
  "session_id": "abc123",
  "task_description": "Optimize database queries in user.py",
  "goal_id": "goal_1"
}
```

**Returns:** Cascade ID for tracking

**Use case:** Quick task tracking without full workflow

---

## 📊 Monitoring & Analysis Tools

### 14. get_epistemic_state
**Purpose:** Get current epistemic vector values  
**When to use:** Check your current assessed state  
**Parameters:**
- `session_id`: Current session

**Example:**
```json
{
  "session_id": "abc123"
}
```

**Returns:** Latest vector values across all tiers

---

### 15. get_workflow_guidance
**Purpose:** Get recommended next action based on state  
**When to use:** Uncertain what to do next  
**Parameters:**
- `session_id`: Current session
- `current_phase`: Optional - "preflight" | "check" | "investigate"

**Example:**
```json
{
  "session_id": "abc123",
  "current_phase": "check"
}
```

**Returns:** Guidance on next phase based on epistemic state

**Logic:**
- High uncertainty → INVESTIGATE
- Low engagement → Clarify task
- Low confidence → More investigation
- High confidence → Proceed to ACT

---

### 16. get_calibration_report
**Purpose:** View calibration accuracy over time  
**When to use:** Review learning and self-assessment accuracy  
**Parameters:**
- `session_id`: Current session

**Example:**
```json
{
  "session_id": "abc123"
}
```

**Returns:** Calibration pattern - overconfident/underconfident/well_calibrated

**Use case:** Improve self-awareness by seeing calibration trends

---

### 17. query_bayesian_beliefs
**Purpose:** Get current belief states from Bayesian tracker  
**When to use:** Check evidence accumulation for hypotheses  
**Parameters:**
- `session_id`: Current session

**Example:**
```json
{
  "session_id": "abc123"
}
```

**Returns:** Belief states with posterior probabilities

**Use case:** Research tasks with hypothesis testing

---

### 18. check_drift_monitor
**Purpose:** Detect epistemic drift (overconfidence over time)  
**When to use:** Long sessions, check for degradation  
**Parameters:**
- `session_id`: Current session

**Example:**
```json
{
  "session_id": "abc123"
}
```

**Returns:** Drift metrics, alerts if detected

**Use case:** Quality assurance in long autonomous sessions

---

## 🔍 Investigation Support Tools

### 19. get_investigation_profile
**Purpose:** Get recommended investigation strategy  
**When to use:** Starting INVESTIGATE phase, need approach  
**Parameters:**
- `session_id`: Current session
- `domain`: Optional - "code" | "research" | "analysis"

**Example:**
```json
{
  "session_id": "abc123",
  "domain": "code"
}
```

**Returns:** Investigation strategy profile for domain

**Profiles:**
- **code**: File exploration, dependency analysis, test review
- **research**: Literature review, hypothesis formation, evidence gathering
- **analysis**: Data exploration, pattern identification, causal reasoning

---

### 20. get_investigation_strategy
**Purpose:** Get specific investigation tactics  
**When to use:** In INVESTIGATE phase, need concrete actions  
**Parameters:**
- `session_id`: Current session
- `uncertainty_type`: What you're uncertain about
- `context`: What you've tried so far

**Example:**
```json
{
  "session_id": "abc123",
  "uncertainty_type": "How authentication works in this codebase",
  "context": "Read login.py but don't understand the token flow"
}
```

**Returns:** Specific investigation actions to try

**Example Output:**
- "Read auth/token.py to understand token generation"
- "Trace login flow with debugger"
- "Check test cases in tests/auth/"

---

### 21. log_investigation_finding
**Purpose:** Record discovery during investigation  
**When to use:** Found something that reduces uncertainty  
**Parameters:**
- `session_id`: Current session
- `finding`: What you discovered
- `uncertainty_reduction`: How much this helped (0.0-1.0)

**Example:**
```json
{
  "session_id": "abc123",
  "finding": "Tokens are JWTs with 1-hour expiry, stored in Redis",
  "uncertainty_reduction": 0.3
}
```

**Returns:** Finding recorded, updated uncertainty tracking

**Use case:** Track investigation progress, measure learning

---

## 🎯 Workflow Usage Patterns

### Pattern 1: Standard Task Execution
```
1. bootstrap_session
2. execute_preflight → submit_preflight_assessment
3. (if needed) get_investigation_strategy → log_investigation_finding
4. execute_check → submit_check_assessment
5. [ACT - do the work]
6. execute_postflight → submit_postflight_assessment
7. get_calibration_report (optional review)
```

### Pattern 2: Autonomous Agent with Goals
```
1. bootstrap_session
2. generate_goals (convert user request to structured goals)
3. For each goal:
   - execute_preflight
   - submit_preflight_assessment
   - query_goal_orchestrator (check progress)
   - execute_check
   - submit_check_assessment
   - [ACT]
   - execute_postflight
   - submit_postflight_assessment
4. get_session_summary
```

### Pattern 3: Research Investigation
```
1. bootstrap_session
2. execute_preflight
3. submit_preflight_assessment (high uncertainty expected)
4. get_investigation_profile (domain="research")
5. Loop:
   - get_investigation_strategy
   - [Research action]
   - log_investigation_finding
   - query_bayesian_beliefs (check hypothesis confidence)
   - execute_check
   - If ready: break
6. execute_postflight
7. submit_postflight_assessment
```

### Pattern 4: Quick Check-In (Lightweight)
```
1. resume_previous_session (if continuing work)
2. get_epistemic_state (where am I?)
3. get_workflow_guidance (what should I do?)
4. [Proceed based on guidance]
```

---

## 💡 Best Practices

### Tool Selection
- **Always start with:** `bootstrap_session` or `resume_previous_session`
- **Core workflow:** Use execute/submit pattern for PREFLIGHT/CHECK/POSTFLIGHT
- **Investigation:** Use strategy tools when uncertainty > 0.70
- **Monitoring:** Use calibration_report periodically to improve self-awareness
- **Goals:** Use generate_goals for vague requests, query_goal_orchestrator for tracking

### Common Mistakes
- ❌ Skipping PREFLIGHT (need baseline for calibration)
- ❌ Not using investigation tools when uncertain (leads to confabulation)
- ❌ Skipping POSTFLIGHT (miss learning measurement)
- ❌ Using tools out of order (execute_check before execute_preflight)

### Performance Tips
- Use `resume_previous_session` to load context (faster than full bootstrap)
- Use `get_workflow_guidance` when uncertain about next step
- Use investigation tools to structure uncertainty reduction
- Review `get_calibration_report` to improve future assessments

---

## 📚 Additional Resources

- **System Prompts:** See `SYSTEM_PROMPTS_FOR_AI_AGENTS.md` for integration templates
- **Full Workflow:** See `docs/skills/SKILL.md` for detailed workflow guide
- **API Reference:** See `docs/production/19_API_REFERENCE.md`
- **Examples:** See `docs/examples/` for usage examples

---

**Version:** 1.0  
**Status:** Complete Reference  
**Last Updated:** 2025-11-14
