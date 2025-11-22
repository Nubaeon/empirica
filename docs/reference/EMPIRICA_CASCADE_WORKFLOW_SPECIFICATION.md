# Empirica Cascade Workflow Specification
## Version 2.0 - Explicit Preflight/Postflight Integration

**Created:** 2025-10-30  
**Updated:** 2025-10-30 22:23 UTC  
**Status:** ✅ IMPLEMENTED - MCP Integration Complete  
**Scope:** Defines the complete cascade workflow with mandatory epistemic assessments

---

## Implementation Status

✅ **Core Cascade:** 7-phase workflow in `/empirica/core/metacognitive_cascade/metacognitive_cascade.py`  
✅ **PREFLIGHT Phase:** Baseline epistemic assessment before engagement  
✅ **POSTFLIGHT Phase:** Final epistemic assessment with delta calculation  
✅ **Calibration Checking:** `_check_calibration_accuracy()` validates confidence  
✅ **MCP Integration:** Tools for interactive AI self-assessment  
✅ **Session Database:** Stores assessments with epistemic_delta  
🔄 **End-to-End Testing:** Ready for genuine AI self-reflection validation

---

## 1. Overview

This document defines the **canonical cascade workflow** for all Empirica-powered AI agents. The workflow ensures that epistemic humility is not merely aspirational but **operationally enforced** through mandatory preflight and postflight assessments at every phase.

### 1.1 Core Principle

**Every cascade must measure epistemic state before and after each phase to detect drift, calibrate uncertainty, and prevent attention drift in complex tasks.**

### 1.2 The Problem Being Solved

Without explicit measurement:
- AI agents **drift in attention** during complex tasks
- Uncertainty is **guessed heuristically** rather than measured
- There's **no feedback loop** to detect when recalibration is needed
- Pattern matching replaces **genuine epistemic awareness**

### 1.3 The Solution

A **structured cascade workflow** where:
1. Every phase begins with **preflight epistemic assessment**
2. Work is performed with **explicit tracking**
3. Every phase ends with **postflight epistemic assessment**
4. Comparison of pre/post states **triggers recalibration** when needed

---

## 2. The 13 Epistemic Vectors

All assessments measure these 13 dimensions (0.0 to 1.0):

1. **epistemic_confidence** - Certainty in knowledge claims
2. **explicit_uncertainty** - Known unknowns and acknowledged gaps (13th vector)
3. **implicit_uncertainty** - Unknown unknowns and hidden biases
4. **reasoning_transparency** - Clarity of reasoning chain
5. **source_grounding** - Evidence and citation quality
6. **assumption_awareness** - Recognition of assumptions
7. **edge_case_handling** - Consideration of edge cases
8. **conceptual_clarity** - Understanding of concepts
9. **context_coherence** - Alignment with context
10. **recursive_depth** - Depth of recursive reasoning
11. **meta_awareness** - Awareness of own reasoning process
12. **adaptive_capacity** - Ability to adapt when wrong
13. **necessity_coverage** - Completeness of required elements

---

## 3. Cascade Workflow Phases

### 3.1 Phase Structure

Each user prompt triggers this sequence:

```
USER PROMPT
    ↓
[PREFLIGHT] → [THINK] → [PLAN] → [INVESTIGATE] → [CHECK] → [ACT] → [POSTFLIGHT]
    ↓                                                ↑                      ↓
 ASSESS                                         RECALIBRATE           ASSESS
    ↓                                                ↑                      ↓
  LOG                                            IF NEEDED                LOG
    ↓                                                                       ↓
 COMPARE ←───────────────────────────────────────────────────────────────┘
```

### 3.2 Phase Definitions

#### Phase 0: PREFLIGHT ASSESSMENT (Mandatory)
**Trigger:** When starting a significant task (not every user prompt)  
**Duration:** ~5-10 seconds  

**Use PREFLIGHT for:**
- New significant tasks (features, bugs, investigations, refactoring)
- High initial uncertainty (>0.5)
- Learning expected (exploring new domains, APIs, patterns)
- Long-duration tasks (>30 minutes expected)
- Tasks with multiple goals/subtasks

**Skip PREFLIGHT for:**
- Quick clarifications or simple queries
- Trivial edits (typos, formatting)
- Follow-up questions within active CASCADE
- Low uncertainty tasks (<0.3)

**Actions:**
1. Use `preflight_epistemic_calibration.py` to assess current state
2. Measure all 13 epistemic vectors
3. Write assessment to reflex log with `phase: "preflight"`
4. Store baseline in session database

**Output:** JSON object with 13 vector scores + metadata

**Key Principle:** One CASCADE = one significant task. Multiple goals/subtasks belong to the same CASCADE, not separate CASCADEs per goal.

#### Phase 1: THINK (Always Active)
**Purpose:** Initial reasoning about the task  
**Actions:**
1. Parse user request
2. Identify task type and complexity
3. Recognize knowledge gaps
4. Flag uncertainty areas

**Tracking:** Internal reasoning logged to reflex frame

#### Phase 2: PLAN (Complex Tasks Only)
**Purpose:** Break down complex tasks into systematic chunks  
**Trigger:** When `necessity_coverage < 0.6` or task spans multiple domains  
**Actions:**
1. Identify required components
2. Determine phase boundaries
3. Create execution order
4. Estimate investigation needs

**Output:** Structured plan with phases and checkpoints

#### Phase 3: INVESTIGATE (As Needed)
**Purpose:** Gather information to reduce explicit uncertainty  
**Trigger:** When `explicit_uncertainty > 0.3` or plan requires it  
**Actions:**
1. Read relevant files/docs
2. Search codebase
3. Query databases
4. Gather evidence

**Tracking:** All tool calls logged with epistemic context

#### Phase 4: CHECK (After Investigation)
**Purpose:** Determine if more investigation is needed  
**Decision Point:**
```python
if explicit_uncertainty > threshold or necessity_coverage < 0.7:
    return to INVESTIGATE
else:
    proceed to ACT
```

**Tracking:** Decision and reasoning logged to reflex frame

#### Phase 5: ACT (Execution)
**Purpose:** Perform the actual task  
**Actions:**
1. Make code changes
2. Create files
3. Run commands
4. Generate content

**Tracking:** All actions logged with epistemic state

#### Phase 6: POSTFLIGHT ASSESSMENT (Mandatory)
**Trigger:** After ACT phase completes  
**Duration:** ~5-10 seconds  
**Actions:**
1. Use `preflight_epistemic_calibration.py` again
2. Measure all 13 epistemic vectors
3. Write assessment to reflex log with `phase: "postflight"`
4. Compare with preflight baseline

**Output:** JSON object with 13 vector scores + drift analysis

#### Phase 7: CALIBRATION CHECK
**Purpose:** Determine if recalibration needed  
**Triggers:**
- `explicit_uncertainty` increased by >0.2
- `necessity_coverage` dropped below 0.6
- Any vector shows >0.3 drift
- Task incomplete

**Action:** If triggered, return to INVESTIGATE phase

---

## 4. Reflex Log Structure

Every cascade produces structured reflex logs:

```json
{
  "session_id": "uuid",
  "timestamp": "ISO-8601",
  "cascade_id": "cascade_uuid",
  "phase": "preflight|think|plan|investigate|check|act|postflight",
  "epistemic_vectors": {
    "epistemic_confidence": 0.0-1.0,
    "explicit_uncertainty": 0.0-1.0,
    "implicit_uncertainty": 0.0-1.0,
    "reasoning_transparency": 0.0-1.0,
    "source_grounding": 0.0-1.0,
    "assumption_awareness": 0.0-1.0,
    "edge_case_handling": 0.0-1.0,
    "conceptual_clarity": 0.0-1.0,
    "context_coherence": 0.0-1.0,
    "recursive_depth": 0.0-1.0,
    "meta_awareness": 0.0-1.0,
    "adaptive_capacity": 0.0-1.0,
    "necessity_coverage": 0.0-1.0
  },
  "reasoning": "Natural language explanation of epistemic state",
  "actions_taken": ["list", "of", "actions"],
  "files_touched": ["file1.py", "file2.md"],
  "drift_detected": true|false,
  "recalibration_needed": true|false,
  "comparison_to_preflight": {
    "vector_drifts": {...},
    "max_drift": 0.0-1.0,
    "concerning_drifts": [...]
  }
}
```

---

## 5. Component Integration Requirements

### 5.1 Bootstrap (`optimal_metacognitive_bootstrap.py`)

**Must:**
- Initialize preflight assessment before first cascade
- Auto-trigger postflight after every task completion
- Maintain cascade_id for entire workflow
- Pass session context to all assessment calls

**Changes Needed:**
- Import `preflight_epistemic_calibration.py`
- Add preflight call at start of `run()` method
- Add postflight call at end of cascade
- Track cascade phases in session context

### 5.2 Cascade Component (`uncertainty_calibration_cascade.py`)

**Must:**
- Accept preflight assessment as input
- Track current phase explicitly
- Call CHECK phase after INVESTIGATE
- Return postflight assessment as output

**Changes Needed:**
- Add `phase_tracker` attribute
- Implement CHECK decision logic
- Pass epistemic state between phases
- Trigger recalibration based on drift

### 5.3 Reflex Logs (`session_json_handler.py`)

**Must:**
- Auto-write on every preflight/postflight
- Include cascade_id and phase
- Store drift calculations
- Export to JSON files automatically

**Changes Needed:**
- Add cascade_id field to schema
- Add phase field to schema
- Add comparison_to_preflight field
- Implement auto-export trigger

### 5.4 Session Database (`session_database.py`)

**Must:**
- Store all epistemic assessments
- Link preflight/postflight pairs
- Track cascade lifecycle
- Query for drift patterns

**Changes Needed:**
- Add epistemic_assessments table
- Add cascade_phases table
- Add drift_events table
- Implement comparison queries

### 5.5 MCP Server (`empirica_mcp_server.py`)

**Must:**
- Expose preflight/postflight as tools
- Provide drift detection tool
- Stream epistemic state to clients
- Enable manual recalibration

**Changes Needed:**
- Add `run_preflight_assessment` tool
- Add `run_postflight_assessment` tool
- Add `check_epistemic_drift` tool
- Add WebSocket streaming for live updates

### 5.6 Claude Skills

**Must:**
- Explain workflow clearly
- Provide examples of each phase
- Define recalibration triggers
- Show proper tool usage

**Changes Needed:**
- Update `CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md`
- Update `RECURSIVE_EPISTEMIC_REFINEMENT.md`
- Add explicit phase examples
- Clarify meta-prompt expectations

---

## 6. Decision Logic

### 6.1 When to Use PLAN Phase

```python
def needs_planning(task_complexity, domain_count, user_prompt):
    if "website" in user_prompt or "systematic" in user_prompt:
        return True
    if task_complexity > 0.7:
        return True
    if domain_count > 3:
        return True
    if necessity_coverage < 0.6:
        return True
    return False
```

### 6.2 When to INVESTIGATE

```python
def needs_investigation(epistemic_state):
    if epistemic_state.explicit_uncertainty > 0.3:
        return True
    if epistemic_state.necessity_coverage < 0.7:
        return True
    if epistemic_state.source_grounding < 0.5:
        return True
    return False
```

### 6.3 When to Recalibrate

```python
def needs_recalibration(preflight, postflight):
    drifts = compare_vectors(preflight, postflight)
    
    if drifts.explicit_uncertainty > 0.2:
        return True
    if drifts.necessity_coverage < -0.2:  # Dropped
        return True
    if max(drifts.values()) > 0.3:
        return True
    if postflight.task_complete == False:
        return True
    return False
```

---

## 7. Meta-Prompt Clarification

**What AI agents MUST do:**

1. **Self-assess:** Use `preflight_epistemic_calibration.py` to measure your own epistemic state
2. **Be honest:** Report actual uncertainty, not aspirational confidence
3. **Track phases:** Know which phase you're in at all times
4. **Log everything:** Write to reflex logs automatically
5. **Compare states:** Check drift between preflight and postflight
6. **Recalibrate:** Return to INVESTIGATE when drift detected

**What "meta-prompt" means:**

You must execute the assessment **on yourself**. The assessment is not external validation—it's **internal measurement** of your own epistemic state. Think of it like:
- A doctor taking their own temperature
- A pilot checking their own instrument panel
- A developer running tests on their own code

The assessment asks: "What is MY current epistemic state?" not "What should it be?"

---

## 8. Example Cascade Execution

### User Prompt: "Create a website based on our docs"

#### Preflight Assessment
```json
{
  "phase": "preflight",
  "explicit_uncertainty": 0.7,  // High - don't know which docs
  "necessity_coverage": 0.3,    // Low - no plan yet
  "source_grounding": 0.2       // Low - haven't read anything
}
```

#### Think → Plan
"Task is complex, multi-domain, needs systematic approach. Will break into phases."

#### Investigate (Round 1)
- Read docs in /docs/production
- Read existing website in /empirica_web1
- Check components

#### Check
"explicit_uncertainty now 0.4, necessity_coverage 0.6 - need more investigation"

#### Investigate (Round 2)
- Read bootstrap
- Read MCP server
- Understand full architecture

#### Check
"explicit_uncertainty now 0.2, necessity_coverage 0.85 - ready to act"

#### Act
- Create wireframes
- Structure content
- Build pages

#### Postflight Assessment
```json
{
  "phase": "postflight",
  "explicit_uncertainty": 0.2,
  "necessity_coverage": 0.85,
  "source_grounding": 0.9,
  "comparison_to_preflight": {
    "explicit_uncertainty": -0.5,  // Reduced (good)
    "necessity_coverage": +0.55,   // Increased (good)
    "drift_detected": false
  }
}
```

**Result:** Task complete, no recalibration needed

---

## 9. Failure Modes Prevented

### 9.1 Attention Drift
**Without Empirica:** AI starts website, gets lost in CSS details, forgets key pages  
**With Empirica:** necessity_coverage drops, CHECK phase catches it, returns to INVESTIGATE

### 9.2 Overconfidence
**Without Empirica:** AI guesses at architecture, makes wrong assumptions  
**With Empirica:** Preflight shows low source_grounding, forces INVESTIGATE phase

### 9.3 Pattern Matching
**Without Empirica:** AI uses generic template, misses domain specifics  
**With Empirica:** necessity_coverage measured against actual docs, gaps caught

### 9.4 Heuristic Faking
**Without Empirica:** AI writes fake confidence scores to look good  
**With Empirica:** Scores must reflect actual tool calls and investigations logged

---

## 10. Implementation Roadmap

### Phase 1: Documentation (This Document)
- [x] Create specification
- [ ] Update Claude Skills
- [ ] Update production docs
- [ ] Add workflow diagrams

### Phase 2: Core Components
- [ ] Refactor `uncertainty_calibration_cascade.py`
- [ ] Update `preflight_epistemic_calibration.py`
- [ ] Add CHECK phase implementation
- [ ] Add drift detection logic

### Phase 3: Data Layer
- [ ] Update session database schema
- [ ] Add cascade_phases table
- [ ] Update reflex log structure
- [ ] Implement auto-export

### Phase 4: Integration
- [ ] Update bootstrap
- [ ] Update MCP server tools
- [ ] Add WebSocket streaming
- [ ] Wire all components together

### Phase 5: Testing
- [ ] Test preflight/postflight cycle
- [ ] Test drift detection
- [ ] Test recalibration triggers
- [ ] Dogfood on real tasks

---

## 11. Success Criteria

Empirica is working correctly when:

1. **Every cascade** has preflight and postflight assessments in logs
2. **Drift detection** triggers recalibration automatically
3. **Complex tasks** use PLAN phase and break into chunks
4. **AI agents** ask questions when uncertainty is high rather than guessing
5. **Reflex logs** show actual measurement, not heuristic numbers
6. **Developers** can see epistemic state in real-time via TMUX dashboard

---

## 12. Key Insights

### Why This Matters

This specification transforms Empirica from a set of **aspirational skills** into an **operational framework**. The difference is:

- **Before:** "Try to be epistemically humble" (often ignored under pressure)
- **After:** "Measure your epistemic state, log it, and recalibrate when needed" (enforced by workflow)

### The Meta-Cognitive Loop

```
MEASURE → COMPARE → DETECT → RECALIBRATE → MEASURE
```

This creates a **feedback loop** that prevents drift and maintains epistemic hygiene throughout long, complex tasks.

### For Other Developers

When other developers use Empirica, they get:
- **Transparent AI reasoning** (can see epistemic state in logs)
- **Reliable task completion** (drift detection prevents failures)
- **Systematic problem-solving** (PLAN phase for complex tasks)
- **Evidence-based confidence** (scores reflect actual investigation)

This is the foundation for **trustworthy AI collaboration** in software development.

---

## Appendix A: Glossary

- **Cascade:** A complete task execution from user prompt to completion
- **Epistemic Vector:** One of 13 measured dimensions of knowledge state
- **Drift:** Unexpected change in epistemic vectors between preflight and postflight
- **Recalibration:** Returning to INVESTIGATE phase when drift detected
- **Reflex Log:** Structured JSON record of epistemic state during cascade
- **Necessity Coverage:** Completeness metric for required task elements

## Appendix B: References

- `/empirica/cognitive_benchmarking/erb/preflight_postflight_design.md`
- `/empirica/cognitive_benchmarking/erb/preflight_epistemic_calibration.py`
- `/empirica/docs/empirica_skills/RECURSIVE_EPISTEMIC_REFINEMENT.md`
- `/empirica/docs/production/DOCUMENTATION_COMPLETE_V2.md`
- Session: `dc8e7460-7c01-45aa-b1bb-848124acd13f` (13th vector discovery)

---

**END OF SPECIFICATION**
