# Empirica System Architecture Overview

**Version:** 3.0  
**Date:** 2024  
**Purpose:** System architecture, design principles, and component interactions  
**Audience:** All AI agents, architects, and developers

---

## Overview

Empirica is an **epistemic self-assessment framework** that enables AI agents to genuinely reason about their own knowledge, capabilities, and uncertainties without relying on heuristics or confabulation. This document describes the system architecture, core principles, and how components interact.

For file locations and directory structure, see [`CANONICAL_DIRECTORY_STRUCTURE.md`](./CANONICAL_DIRECTORY_STRUCTURE.md).

---

## Core Philosophy

### 1. No Heuristics Principle
**Empirica does not use heuristics to simulate AI self-awareness.**

- ❌ **No keyword matching** for domain detection
- ❌ **No hardcoded confidence calculations** (e.g., +0.15 per tool)
- ❌ **No fake learning boosts** (e.g., rounds × 0.05)
- ✅ **Genuine LLM reasoning** about epistemic state
- ✅ **Real self-assessment** based on task understanding
- ✅ **Honest uncertainty** acknowledgment

### 2. Temporal Separation
**Reflex logs separate current reasoning from historical reasoning.**

- Prevents self-referential recursion
- AI can reflect on past reasoning without circular loops
- Three storage formats serve different purposes (SQLite, JSON, Reflex logs)

### 3. Context-Aware Constraints
**Investigation constraints adapt to AI capability and domain.**

- High reasoning models (Claude, GPT-4, o1) get maximum autonomy
- Autonomous agents get structured guidance
- Critical domains (medical, legal) get strict compliance rules
- Profiles enable appropriate constraints without artificial limitations

### 4. Genuine Calibration
**Track how well AI predictions match reality.**

- PREFLIGHT: Initial assessment (baseline)
- Investigation: Gather information
- CHECK: Reassess after investigation
- ACT: Execute task
- POSTFLIGHT: Final assessment (compare with baseline)
- Calibration delta reveals over/under-confidence patterns

---

## System Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERACTION LAYER                      │
│  - CLI (command-line interface)                                  │
│  - MCP Server (IDE integration)                                  │
│  - Dashboard (real-time monitoring)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    EPISTEMIC FRAMEWORK LAYER                     │
│  - Canonical Assessment (13 vectors, genuine LLM reasoning)      │
│  - CASCADE Workflow (7 phases with investigation loop)           │
│  - Profile System (context-aware constraints)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     INVESTIGATION SYSTEM LAYER                   │
│  - Domain strategies (code, research, creative, etc.)            │
│  - Plugin system (user-provided investigation tools)             │
│  - Tool recommendations (profile-driven suggestions)             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       PERSISTENCE LAYER                          │
│  - SQLite database (queryable, relational)                       │
│  - JSON sessions (portable, exportable)                          │
│  - Reflex logs (temporal separation)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Canonical Epistemic Assessment

**Purpose:** Genuine AI self-assessment using 13 epistemic vectors

**13 Vectors (grouped into 4 tiers):**

**TIER 1: ENGAGEMENT (15% weight)**
- `engagement` - Genuine interest and investment in task

**TIER 2: FOUNDATION (35% weight)**
- `know` - Domain knowledge
- `do` - Capability to execute
- `context` - Understanding of situation

**TIER 3: COMPREHENSION (25% weight)**
- `clarity` - Task clarity
- `coherence` - Internal consistency
- `signal` - Actionable information
- `density` - Complexity management

**TIER 4: EXECUTION (25% weight)**
- `state` - Current state understanding
- `change` - Change management capability
- `completion` - Path to completion
- `impact` - Expected impact

**PLUS:**
- `uncertainty` - Overall uncertainty (special meta-vector)

**Vector Format:**
- Type: `float` (0.0 to 1.0)
- No percentages in core system
- Dashboard converts for display
- AIs reason about scores in 0.0-1.0 range

**How It Works:**
1. LLM receives epistemic assessment prompt
2. LLM genuinely reasons about each vector
3. Response parsed into structured `EpistemicAssessment`
4. No heuristics, no keyword matching
5. Rationale and evidence captured for each vector

**Confidence Calculation:**
```
overall_confidence = (
    foundation × 0.35 +
    comprehension × 0.25 +
    execution × 0.25 +
    engagement × 0.15
)

# Profile tuning multipliers applied:
foundation_weighted = foundation × profile.tuning.foundation_weight
# ... etc, then renormalize
```

---

### 2. CASCADE Workflow

**Purpose:** 7-phase metacognitive workflow with investigation loop

**Phases:**

```
1. PREFLIGHT  → Initial epistemic assessment (baseline)
2. THINK      → Initial reasoning about task
3. PLAN       → Task decomposition (if needed)
4. INVESTIGATE → Gather information (loop with self-check)
5. CHECK      → Self-assessment after investigation
6. ACT        → Execute task
7. POSTFLIGHT → Final assessment (calibration check)
```

**Investigation Loop:**

```
while not satisfied:
    [INVESTIGATE] Gather information
        ↓
    [CHECK] Self-assess current state
        ↓
    if confidence sufficient OR max_rounds reached (if set):
        break
    else:
        continue investigating
```

**Key Features:**
- **Self-check loop:** AI decides when to stop investigating
- **Profile-driven:** Constraints from investigation profile
- **Genuine learning:** POSTFLIGHT is real reassessment, not calculation
- **Calibration tracking:** Compare PREFLIGHT vs POSTFLIGHT

**Actions AI Can Take:**
- `INVESTIGATE` - Need more information
- `PROCEED` - Ready to act
- `CLARIFY` - Need clearer requirements
- `DELEGATE` - Task beyond capability
- `RESET` - Fundamental confusion, start over

---

### 3. Profile System ⭐ NEW

**Purpose:** Context-aware investigation constraints

**Architecture:**

```
Universal Constraints (Sentinel-enforced)
    ↓
Investigation Profile (context-specific)
    ↓
Plugin Suggestions (user-provided)
    ↓
AI Decision (final choice)
```

**Three Types of Constraints:**

**Type 1: Universal Constraints** (Always enforced)
- Engagement gate (0.60 minimum)
- Coherence minimum (0.50)
- Timeout limits (prevent runaway)
- Tool call limits (prevent abuse)
- Purpose: Governance, security, compliance

**Type 2: Profile Constraints** (Context-dependent)
- Max investigation rounds (or unlimited)
- Confidence thresholds
- Tool suggestion modes
- Learning assessment methods
- Purpose: Appropriate guidance per AI type and domain

**Type 3: Plugin Suggestions** (Suggestive)
- Custom investigation tools
- Domain-specific approaches
- User-provided extensions
- Purpose: Expand investigation options

**5 Built-in Profiles:**

1. **high_reasoning_collaborative**
   - For: Claude Opus/Sonnet, GPT-4, o1, Gemini Pro
   - Max rounds: Unlimited (AI decides)
   - Confidence threshold: Dynamic (AI determines)
   - Tool mode: Light suggestions
   - Philosophy: Maximum autonomy, trust AI reasoning

2. **autonomous_agent**
   - For: GPT-3.5, Claude Haiku, smaller models
   - Max rounds: 5
   - Confidence threshold: 0.70
   - Tool mode: Guided suggestions
   - Philosophy: Structured guidance, clear boundaries

3. **critical_domain**
   - For: Medical, financial, legal, safety-critical
   - Max rounds: 3
   - Confidence threshold: 0.90
   - Tool mode: Prescribed (approved tools only)
   - Philosophy: Strict compliance, full audit trail

4. **exploratory**
   - For: Research, learning, brainstorming
   - Max rounds: Unlimited
   - Confidence threshold: 0.50 (low bar)
   - Tool mode: Inspirational
   - Philosophy: Maximum freedom, encourage exploration

5. **balanced**
   - For: General-purpose tasks
   - Max rounds: 7
   - Confidence threshold: 0.65
   - Tool mode: Suggestive
   - Philosophy: Reasonable middle ground

**Profile Selection:**
```python
# Explicit selection
profile = load_profile('high_reasoning_collaborative')

# Auto-selection by AI model
profile = select_profile(ai_model='claude-sonnet')
# → Returns: high_reasoning_collaborative

# Auto-selection by domain
profile = select_profile(domain='medical')
# → Returns: critical_domain

# Auto-selection by both
profile = select_profile(ai_model='gpt-3.5-turbo', domain='research')
# → Returns: autonomous_agent (AI type takes precedence)
```

**Tuning System:**
- Main tuner: `confidence_weight` (overall sensitivity)
- Sub-tuners: `foundation_weight`, `comprehension_weight`, `execution_weight`, `uncertainty_weight`
- Example: Critical domains emphasize foundation (1.5×) and uncertainty (1.4×)

---

### 4. Investigation System

**Purpose:** Pluggable investigation strategies and tools

**Components:**

**A. Investigation Strategies** (Domain-aware)
- `CodeAnalysisStrategy` - For code-related tasks
- `ResearchStrategy` - For research tasks
- `CreativeStrategy` - For creative tasks
- `GeneralStrategy` - Fallback for general tasks

**B. Investigation Plugins** (User-provided)
- Users can add custom investigation tools
- Examples: JIRA search, database queries, API calls
- Plugins declare which vectors they improve
- Plugins can have custom executor functions

**C. Tool Recommendations** (Profile-driven)
- Profile determines HOW tools are suggested:
  - `light` - Minimal suggestions, AI explores freely
  - `suggestive` - Suggestions provided, AI decides
  - `guided` - Strong guidance, AI should follow
  - `prescribed` - Specific approved tools only
  - `inspirational` - Spark ideas for exploration

**D. MCP-Aware Investigation**
- Executes tools using MCP (Model Context Protocol)
- Integrates with IDE capabilities
- Provides results back to CASCADE

**Integration Flow:**

```
1. CASCADE enters INVESTIGATE phase
2. Epistemic gaps identified (low know, context, state, etc.)
3. Investigation strategy selected (based on domain)
4. Profile determines suggestion mode
5. Strategy recommends tools based on gaps
6. Plugins add custom tools
7. AI selects tools to use (respecting profile constraints)
8. MCP-aware investigation executes tools
9. Results integrated
10. CHECK phase reassesses
11. Loop continues or exits
```

---

### 5. Data Management

**Three Storage Formats (Simultaneous):**

**Format 1: SQLite Database**
- **Location:** `.empirica/sessions/sessions.db`
- **Purpose:** Queryable, relational, persistent
- **Tables:**
  - `sessions` - Session metadata
  - `cascades` - CASCADE executions
  - `epistemic_assessments` - All 13-vector assessments
  - `goals` - Goal tracking
- **Use Case:** Querying across sessions, analytics, tracking

**Format 2: JSON Sessions**
- **Location:** `.empirica/sessions/<session_id>.json`
- **Purpose:** Portable, exportable, human-readable
- **Content:** Complete session state
- **Use Case:** Export, backup, sharing, portability

**Format 3: Reflex Logs**
- **Location:** `.empirica_reflex_logs/<ai_id>/<date>/`
- **Purpose:** Temporal separation, prevent recursion
- **Content:** Phase-specific reasoning snapshots
- **Use Case:** Reflection without circular loops

**Auto-Tracking:**
All three formats populated simultaneously via `EmpericaTracker`:
```python
tracker = EmpericaTracker()
await tracker.log_assessment(assessment, phase='preflight')
# → Writes to SQLite, JSON, and reflex logs automatically
```

---

## Data Flow

### Complete CASCADE Data Flow:

```
1. User Prompt
    ↓
2. [PREFLIGHT] Canonical Epistemic Assessment
    │ - LLM genuinely reasons about 13 vectors
    │ - Baseline established
    │ - Auto-tracked: SQLite + JSON + Reflex log
    ↓
3. [THINK] Initial Reasoning
    │ - LLM thinks about approach
    │ - Reasoning captured
    ↓
4. [PLAN] Task Decomposition (if complex)
    │ - Break down into subtasks
    │ - Goal orchestrator manages goals
    ↓
5. [INVESTIGATE] Investigation Loop
    │ ┌─────────────────────────────┐
    │ │ A. Identify epistemic gaps  │
    │ │    (low know, context, etc.)│
    │ ↓                              │
    │ │ B. Load investigation       │
    │ │    profile                  │
    │ ↓                              │
    │ │ C. Strategy recommends      │
    │ │    tools (based on gaps)    │
    │ ↓                              │
    │ │ D. Plugins add custom tools │
    │ ↓                              │
    │ │ E. AI selects tools         │
    │ │    (respecting profile)     │
    │ ↓                              │
    │ │ F. MCP executes tools       │
    │ ↓                              │
    │ │ G. Results integrated       │
    │ ↓                              │
    │ │ [CHECK] Self-assess         │
    │ │ - Genuine reassessment      │
    │ │ - Compare with PREFLIGHT    │
    │ ↓                              │
    │ │ H. Continue OR exit?        │
    │ │    - AI decides based on    │
    │ │      confidence and gaps    │
    │ │    - Profile max_rounds     │
    │ │      may limit (if set)     │
    │ └─────────────────────────────┘
    ↓
6. [ACT] Execute Task
    │ - Perform actual work
    │ - Generate output
    ↓
7. [POSTFLIGHT] Final Assessment
    │ - Genuine reassessment (not calculation)
    │ - Compare with PREFLIGHT (calibration)
    │ - Epistemic delta calculated
    │ - Auto-tracked: SQLite + JSON + Reflex log
    ↓
8. Results + Session Data
    │ - Task output
    │ - Complete session history
    │ - Calibration metrics
    │ - Epistemic trajectory
```

---

## Design Principles

### 1. Genuine Over Simulated
**Always prefer genuine AI reasoning over simulated heuristics.**

Example:
- ❌ Bad: `if 'refactor' in task: domain = CODE_ANALYSIS`
- ✅ Good: LLM reasons about domain from task context

### 2. Temporal Separation
**Separate current reasoning from historical reasoning.**

Example:
- ❌ Bad: AI reads its own current assessment while assessing
- ✅ Good: AI reads historical reflex logs after assessment complete

### 3. Context-Aware Constraints
**Constraints should adapt to context, not be universal.**

Example:
- ❌ Bad: All AIs have max 3 investigation rounds
- ✅ Good: High reasoning AIs unlimited, autonomous agents 5, critical domains 3

### 4. Pluggable Architecture
**Users can extend without modifying core.**

Example:
- ❌ Bad: Hardcoded investigation tools in cascade
- ✅ Good: Plugin system for custom investigation tools

### 5. Three Storage Formats
**Different use cases need different formats.**

Example:
- SQLite: Querying across sessions
- JSON: Portability and export
- Reflex logs: Temporal separation

### 6. Profile-Driven Behavior
**Behavior controlled by profiles, not hardcoded.**

Example:
- ❌ Bad: `action_confidence_threshold = 0.70` hardcoded
- ✅ Good: `profile.investigation.confidence_threshold` (varies by profile)

---

## Component Interactions

### Canonical Assessment ↔ CASCADE

```
CASCADE requests assessment
    ↓
Canonical Assessment generates prompt
    ↓
LLM receives prompt
    ↓
LLM genuinely reasons
    ↓
Response parsed into EpistemicAssessment
    ↓
CASCADE receives structured assessment
    ↓
CASCADE decides action (INVESTIGATE, PROCEED, etc.)
```

### CASCADE ↔ Investigation System

```
CASCADE identifies gaps (low vectors)
    ↓
Investigation Strategy receives gaps + profile
    ↓
Strategy recommends tools based on domain
    ↓
Plugins add custom tools
    ↓
Tools filtered/sorted by profile mode
    ↓
CASCADE presents tools to AI
    ↓
AI selects tools (respecting profile constraints)
    ↓
MCP-aware investigation executes
    ↓
Results returned to CASCADE
    ↓
CHECK phase reassesses
```

### Profile System ↔ CASCADE

```
CASCADE initialization
    ↓
Profile loader auto-selects profile
  (based on ai_model + domain + explicit)
    ↓
Profile loaded with constraints
    ↓
CASCADE uses profile throughout:
  - Investigation loop (max_rounds)
  - Action determination (thresholds)
  - Tool suggestions (mode)
  - Learning assessment (postflight_mode)
```

### Data Layer ↔ All Components

```
Any component logs event
    ↓
EmpericaTracker receives log
    ↓
Tracker writes simultaneously to:
  - SQLite (queryable)
  - JSON (exportable)
  - Reflex logs (temporal separation)
    ↓
All formats stay synchronized
```

---

## Integration Points

### 1. CLI Integration

**Entry Point:** `python -m empirica.cli`

**Key Commands:**
```bash
# Bootstrap with profile
empirica bootstrap --profile high_reasoning_collaborative

# Auto-select profile
empirica bootstrap --ai-model claude-sonnet --domain research

# Profile management
empirica profile list
empirica profile show high_reasoning_collaborative
empirica profile export high_reasoning_collaborative my_profile.yaml
empirica profile import my_custom_profile.yaml --name custom

# Workflow commands
empirica preflight "task description"
empirica investigate
empirica check
empirica postflight
```

### 2. MCP Server Integration

**22 MCP Tools Available:**

**Session Management:**
- `bootstrap_session(ai_id, session_type, profile, ai_model, domain)`
- `resume_previous_session(...)`
- `get_session_summary(...)`
- `get_epistemic_state(...)`

**Assessment Workflow:**
- `execute_preflight(session_id, prompt)`
- `submit_preflight_assessment(session_id, vectors)`
- `execute_check(...)`
- `submit_check_assessment(...)`
- `execute_postflight(...)`
- `submit_postflight_assessment(...)`

**Monitoring:**
- `get_calibration_report(...)`
- `query_bayesian_beliefs(...)`
- `check_drift_monitor(...)`
- `query_goal_orchestrator(...)`

**Utility:**
- `get_empirica_introduction(...)`
- `get_workflow_guidance(...)`
- `cli_help(...)`
- `execute_cli_command(...)`
- `query_ai(...)`  # AI-to-AI communication
- `generate_goals(...)`
- `create_cascade(...)`

### 3. Dashboard Integration (Optional)

**Real-time Monitoring:**
- Epistemic vector visualization
- CASCADE phase tracking
- Investigation progress
- Calibration metrics

**Display Format:**
- Input: Floats (0.0-1.0) from core
- Processing: Threshold-based coloring
  - ≥ 0.90: Green (excellent)
  - ≥ 0.80: Yellow (good)
  - ≥ 0.70: Orange (acceptable)
  - < 0.70: Red (needs attention)
- Output: Visual bars, color indicators

### 4. Plugin Integration

**Investigation Plugins:**
```python
# User creates plugin
my_plugin = InvestigationPlugin(
    name='database_search',
    description='Search internal database',
    improves_vectors=['know', 'context'],
    confidence_gain=0.20,
    executor=my_db_search_function
)

# Register with CASCADE
cascade = CanonicalEpistemicCascade(
    investigation_plugins={'db': my_plugin}
)

# Plugin suggestions filtered by profile
# - light mode: AI can ignore
# - guided mode: AI should consider
# - prescribed mode: Must use if relevant
```

---

## Future Architecture (Planned)

### Sentinel System
**Purpose:** Governance, compliance, security enforcement

**Planned Features:**
- Runtime constraint enforcement
- Policy violation detection
- Audit trail generation
- Risk assessment
- Escalation protocols

**Integration Point:**
```
Profile System → Sentinel validates constraints
CASCADE execution → Sentinel monitors
Investigation → Sentinel checks tool usage
```

### Bayesian Guardian
**Purpose:** Adaptive profile tuning based on calibration

**Planned Features:**
- Track calibration accuracy over time
- Detect systematic over/under-confidence
- Automatically adjust profile weights
- Recommend profile changes
- A/B test profiles

**Integration Point:**
```
POSTFLIGHT calibration → Bayesian Guardian analyzes
Pattern detected → Adjust profile tuning weights
Next session → Updated profile applied
```

### Cognitive Vault (Experimental)
**Purpose:** AI capability assessment and persona detection

**Planned Features:**
- Assess AI epistemic reasoning capability
- Detect AI type (high reasoning vs autonomous)
- Recommend optimal profile
- Track capability changes over time

**Integration Point:**
```
Session bootstrap → Cognitive vault assesses AI
Assessment complete → Profile auto-selected
Profile effectiveness tracked → Vault learns
```

---

## Performance Characteristics

### Time Complexity:
- Epistemic assessment: O(1) LLM call
- CASCADE execution: O(n) where n = investigation rounds
- Profile loading: O(1) YAML parse (cached)
- Database queries: O(log n) with indexes

### Space Complexity:
- Session storage: ~10KB per session (JSON)
- Database growth: ~50KB per 100 assessments
- Reflex logs: ~5KB per phase per session
- Memory usage: <100MB typical

### Scalability:
- Single AI: Designed for individual sessions
- Multiple AIs: Separate sessions, no conflicts
- Concurrent: SQLite handles concurrent reads, sequential writes
- Distributed: JSON export enables cross-system sharing

---

## Error Handling

### Graceful Degradation:
- Profile YAML missing → Use balanced profile default
- Database locked → Retry with exponential backoff
- LLM API failure → Return cached assessment or request retry
- Invalid assessment → Request clarification

### Validation:
- Vector scores validated (0.0-1.0 range)
- Profile constraints validated on load
- Database schema validated on init
- MCP tool schemas validated

---

## Testing Strategy

### Unit Tests:
- Canonical assessment parsing
- Profile loading and selection
- Vector validation
- Database operations
- Reflex frame structures

### Integration Tests:
- Complete CASCADE execution
- Investigation loop behavior
- Profile-driven constraints
- Multi-phase workflows
- Database + JSON + reflex log sync

### Comparative Tests:
- Profile behavior differences
- High reasoning vs autonomous
- Critical vs exploratory
- Constraint enforcement

### Calibration Tests:
- PREFLIGHT vs POSTFLIGHT accuracy
- Confidence trajectory validation
- Learning assessment verification

---

## Security Considerations

### Data Privacy:
- All data stored locally by default
- No external transmission required
- Reflex logs contain AI reasoning (sensitive)
- Database encryption optional

### Access Control:
- File system permissions protect data
- MCP server requires authorization
- Plugin execution sandboxed (future)

### Validation:
- Input sanitization
- SQL injection prevention (parameterized queries)
- YAML injection prevention (safe loader)

---

## Monitoring and Observability

### Metrics Tracked:
- Investigation rounds per session
- Confidence trajectories
- Calibration accuracy
- Tool usage patterns
- Profile selection distribution
- Phase transition times

### Logging:
- Phase entry/exit
- Assessment submissions
- Investigation tool execution
- Profile loading
- Error conditions

### Debugging:
- Reflex logs provide reasoning trail
- Database queryable for patterns
- JSON sessions exportable for analysis

---

## Summary

Empirica's architecture enables **genuine epistemic self-assessment** through:

1. **No Heuristics** - Pure LLM reasoning, no keyword matching or fake calculations
2. **13-Vector Assessment** - Comprehensive epistemic state capture
3. **CASCADE Workflow** - 7-phase workflow with investigation loop
4. **Profile System** - Context-aware constraints (not one-size-fits-all)
5. **Temporal Separation** - Reflex logs prevent circular reasoning
6. **Pluggable Design** - Users extend without modifying core
7. **Triple Storage** - SQLite + JSON + Reflex logs (simultaneous)
8. **Genuine Calibration** - Track AI prediction accuracy over time

**For Implementation Details:** See `CANONICAL_DIRECTORY_STRUCTURE.md`  
**For User Guides:** See `docs/production/` and `docs/guides/`  
**For API Reference:** See `docs/production/19_API_REFERENCE.md`

