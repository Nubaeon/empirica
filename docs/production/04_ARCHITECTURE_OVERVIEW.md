# 🏗️ Architecture Overview

Understanding the Empirica Canonical Epistemic Cascade system.

---

## Philosophy

> "This is about eliminating heuristics and getting AIs to measure and validate without interfering with their internal systems."

**Core Principles:**
1. **Measurement Without Control** - Guide, don't dictate
2. **Evidence-Based Reasoning** - Track real evidence, not assumptions
3. **Behavioral Integrity** - Maintain intellectual honesty
4. **Extensibility** - Adapt to any domain

---

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                  CANONICAL EPISTEMIC CASCADE                 │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Canonical Assessor (LLM-Powered)                  │  │
│  │    • No heuristics                                    │  │
│  │    • Genuine self-assessment                          │  │
│  │    • 12 epistemic vectors                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 2. Investigation System (Approach B)                  │  │
│  │    • Strategic guidance (5 patterns)                  │  │
│  │    • Tool capability mapping                          │  │
│  │    • Investigation necessity logic                    │  │
│  │    • User clarification priority                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 3. Bayesian Guardian (Evidence Tracking)              │  │
│  │    • Real-time belief updates                         │  │
│  │    • Discrepancy detection                            │  │
│  │    • Selective activation                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 4. Drift Monitor (Behavioral Integrity)               │  │
│  │    • Sycophancy detection                             │  │
│  │    • Tension avoidance detection                      │  │
│  │    • Synthesis tracking                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 5. Plugin System (Extensibility)                      │  │
│  │    • Custom tool integration                          │  │
│  │    • Zero core modification                           │  │
│  │    • Automatic LLM explanation                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 6. Action Hooks (Live Monitoring)                     │  │
│  │    • Tmux dashboard updates                           │  │
│  │    • Phase tracking                                   │  │
│  │    • Real-time visualization                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │  Reflex Frame Logger │
              │  (Temporal Separation)│
              └─────────────────────┘
```

---

## Cascade Flow

### Complete 6-Phase Process:

```
1. THINK
   └─> Initial LLM self-assessment
       • No heuristics, genuine reasoning
       • Log to Reflex Frame

2. ENGAGEMENT GATE
   └─> Check 12th dimension (≥ 0.60)
       • Pass → Continue
       • Fail → CLARIFY action

3. UNCERTAINTY
   └─> Measure epistemic state
       • 12D vector assessment
       • Domain classification
       • Bayesian: Initialize beliefs

4. INVESTIGATE (if needed)
   └─> Strategic guidance
       • Assess necessity (skip conditions)
       • Generate strategy (5 patterns)
       • Map tool capabilities (standard + Empirica + plugins)
       • Suggest actions (not execute)
       • LLM decides & reports back
       • Bayesian: Update from evidence

5. CHECK
   └─> Verify readiness
       • Standard checks
       • Bayesian: Discrepancy detection
       • Drift: Behavioral analysis
       • Calibration guidance

6. ACT
   └─> Final decision
       • Action + confidence + rationale
       • Bayesian summary
       • Drift warnings
       • Complete
```

---

## Data Structures

### EpistemicAssessment
```python
@dataclass
class EpistemicAssessment:
    # ENGAGEMENT (Gate)
    engagement: VectorState          # 12th dimension
    engagement_gate_passed: bool     # ≥ 0.60?
    
    # FOUNDATION (35% weight)
    know: VectorState                # Domain knowledge
    do: VectorState                  # Execution capability
    context: VectorState             # Environmental context
    foundation_confidence: float
    
    # COMPREHENSION (25% weight)
    clarity: VectorState             # Request clarity
    coherence: VectorState           # Logical coherence
    signal: VectorState              # Signal vs noise
    density: VectorState             # Information density
    comprehension_confidence: float
    
    # EXECUTION (25% weight)
    state: VectorState               # Current state
    change: VectorState              # Change tracking
    completion: VectorState          # Path to completion
    impact: VectorState              # Consequence prediction
    execution_confidence: float
    
    # OVERALL (with ENGAGEMENT as 15%)
    overall_confidence: float        # Weighted aggregate
    recommended_action: Action       # PROCEED | INVESTIGATE | CLARIFY | PAUSE
```

### VectorState
```python
@dataclass
class VectorState:
    score: float        # 0.0 - 1.0
    rationale: str      # LLM's reasoning
```

---

## Key Innovations

### 1. No Heuristics
**Before:** Count vague terms, keyword matching  
**After:** LLM-powered genuine reasoning

### 2. Approach B (Investigation)
**Before:** Execute tools automatically  
**After:** Suggest tools, LLM decides

### 3. Bayesian Guardian
**Real-time evidence tracking:**
- Initialize from assessment
- Update from tool execution
- Detect discrepancies
- Guide calibration

### 4. Drift Monitor
**Behavioral integrity:**
- Track synthesis decisions
- Detect sycophancy patterns
- Detect tension avoidance
- Maintain honesty

### 5. Plugin System
**Universal extensibility:**
- Any tool can be added
- No core modification
- Automatic explanation
- Domain-specific tools

---

## Canonical Weights

```python
CANONICAL_WEIGHTS = {
    'foundation': 0.35,      # KNOW + DO + CONTEXT
    'comprehension': 0.25,   # CLARITY + COHERENCE + SIGNAL + DENSITY
    'execution': 0.25,       # STATE + CHANGE + COMPLETION + IMPACT
    'engagement': 0.15       # ENGAGEMENT (12th dimension)
}
```

**Why these weights?**
- Foundation (35%): Most critical - what you know and can do
- Comprehension (25%): Understanding the task correctly
- Execution (25%): Ability to execute successfully
- Engagement (15%): Collaborative intelligence (when applicable)

---

## Decision Logic

### Investigation Necessity
**Skip when:**
1. No significant gaps (all near threshold)
2. Simple, well-understood tasks
3. Creative tasks with good engagement
4. Acceptable confidence with minimal gaps

**Investigate when:**
1. Critical gaps (severity > 0.25)
2. Low clarity in complex domains
3. Multiple moderate gaps
4. Low knowledge in specialized tasks

### Strategic Patterns
1. **User Clarification** (clarity < 0.60)
2. **Complex Domain Info** (medical/legal + low knowledge)
3. **External Search** (knowledge gap)
4. **Environmental Scan** (context/state gap)
5. **Layered Investigation** (multiple gaps - one at a time)

### Bayesian Activation
**Active for:**
- Precision-critical domains (security, medical, legal)
- Low clarity situations
- After multiple discrepancies

**Dormant for:**
- Creative tasks
- High confidence
- Simple tasks

---

## Tool Ecosystem

### Standard Tools (4)
- `grep` - Search files
- `read_file` - Read contents
- `bash` - Execute commands
- `workspace_scan` - Map environment

### Empirica Tools (10+)
- `monitor_assess_12d` - Full assessment
- `calibration_assess` - Adaptive calibration
- `web_search` - External knowledge
- `semantic_search_qdrant` - Vector search
- `session_manager_search` - History
- `user_clarification` - Ask user (HIGHEST priority)
- `user_information_gathering` - Systematic info
- `goals_create` - Structure goals
- `goals_orchestrate` - Multi-step workflows

### User Plugins (Unlimited)
- JIRA, Confluence, Slack
- Domain-specific APIs
- Company-specific tools
- Industry databases

---

## Logging & Monitoring

### Reflex Frame Logging
```
.empirica_reflex_logs/cascade/
├── reflex_frame_20251027_143022.json
├── reflex_frame_20251027_143156.json
└── ...
```

**Each frame contains:**
- Timestamp
- Phase name
- Complete assessment
- Context data
- Phase-specific metadata

### Dashboard Updates
Via action hooks:
- `log_thought()` - Chain of thought
- `log_12d_state()` - Vector visualization
- `log_cascade_phase()` - Phase metadata

---

## Integration Points

### Python API
```python
cascade = CanonicalEpistemicCascade(...)
result = await cascade.run_epistemic_cascade(task, context)
```

### MCP Protocol
```json
{
  "tool": "cascade_run_full",
  "arguments": { "question": "...", "enable_dashboard": true }
}
```

### Tmux Dashboard
Real-time visualization of cascade progress

---

## Performance Characteristics

**Investigation Skip Rate:** ~40% (simple tasks)  
**Bayesian Activation:** ~30% (precision domains)  
**Average Cascade Time:** 2-5 seconds (no investigation), 10-30 seconds (with investigation)  
**Tool Count:** 16+ (standard + Empirica + plugins)

---

## Security & Safety

### Built-in Safeguards:
1. **No Auto-Execution** - Investigation suggests, never executes
2. **User Priority** - User clarification has highest gain (0.40-0.45)
3. **Drift Detection** - Catches sycophancy and tension avoidance
4. **Evidence Tracking** - Bayesian catches overconfidence
5. **Temporal Separation** - Reflex logging prevents recursion

### Recommended Practices:
- Use Bayesian for high-stakes decisions
- Enable drift monitoring for long sessions
- Monitor dashboard in production
- Review Reflex Frame logs regularly
- Set appropriate confidence thresholds

---

## Next Reading

- **Understanding vectors:** `05_EPISTEMIC_VECTORS.md`
- **Investigation details:** `07_INVESTIGATION_SYSTEM.md`
- **API usage:** `13_PYTHON_API.md`
- **Production deploy:** `17_PRODUCTION_DEPLOYMENT.md`

---

**Architecture Questions?** → `22_FAQ.md`
