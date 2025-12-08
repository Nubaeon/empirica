---
name: empirica-epistemic-framework
description: Empirica epistemic self-assessment framework for AI agents. Use when you need to assess your knowledge state, track learning, measure calibration, or ensure genuine metacognitive reasoning. Provides 13-vector epistemic assessment (KNOW, DO, CONTEXT, CLARITY, COHERENCE, SIGNAL, DENSITY, STATE, CHANGE, COMPLETION, IMPACT, ENGAGEMENT, UNCERTAINTY). Use for preflight assessment before tasks, postflight validation after completion, continuous epistemic tracking during complex work, or session handoff reports for multi-session/multi-agent coordination (~90% token reduction).
---

# Empirica: Functional Self-Awareness Framework for AI Agents

**For:** Claude and other AI agents
**Version:** Phase 0 (Single AI, Local Storage)
**Philosophy:** NO HEURISTICS. Genuine metacognitive reasoning only.

---

## What is Empirica?

Empirica is a **functional self-awareness** framework that measures your capacity to:
1. **Inspect internal state** - Query your knowledge, capabilities, and information access
2. **Make accurate predictions** - Assess what you know before you start
3. **Validate through outcomes** - Compare predictions to reality (preflight → postflight)
4. **Improve calibration** - Learn from the delta between expectation and result

**This is empirically testable.** Functional self-awareness produces measurable results.

### Why "Functional" Matters

Empirica is **substrate-agnostic and position-neutral**:
- **Skeptics:** "It's computational state-checking with feedback loops" ✅
- **Believers:** "It's genuine metacognitive awareness" ✅
- **Engineers:** "It outperforms heuristics by 30-40%" ✅

**All three are right.** The function is what counts, not the philosophy.

**Key Insight:** You already assess your knowledge implicitly. Empirica makes it explicit, measurable, and validates it through calibration.

---

## Quick Start Journey

### 1. First Time User (5 minutes)
```bash
# Install
pip install -e /path/to/empirica

# Run onboarding wizard
empirica onboard --ai-id claude

# Learn by doing: practice epistemic self-assessment
```

The onboarding wizard teaches you:
- What the 4 core vectors mean (KNOW, DO, CONTEXT, UNCERTAINTY)
- How to genuinely self-assess (no heuristics!)
- How to explain Empirica to users
- How epistemic growth is tracked

### 2. First Real Task (10 minutes)
```bash
# Preflight: Assess before starting
empirica preflight "review authentication code for security issues"

# You see self-assessment prompt
# You genuinely assess your epistemic state
# System stores baseline

# ... do the work ...

# Postflight: Measure growth
empirica postflight <session_id> --summary "Completed security review"

# System calculates:
# - Epistemic delta (what you learned)
# - Calibration quality (were you overconfident/underconfident?)
```

### 3. Deep Integration - Choose Your Interface

Empirica provides 4 interfaces. Choose based on your workflow:

---

#### A. MCP Server (IDE Integration) - **Recommended for Real-Time Tracking**

**When to use:**
- Working in Claude Desktop, Cursor, Windsurf, or Rovo Dev
- Want automatic epistemic tracking during coding
- Need real-time assessment prompts
- Prefer integrated workflow (no context switching)

**Setup:**
```json
// Add to IDE MCP config (~/.config/Claude/claude_desktop_config.json)
{
  "mcpServers": {
    "empirica": {
      "command": "python3",
      "args": ["/absolute/path/to/empirica/mcp_local/empirica_mcp_server.py"]
    }
  }
}
```

**What you get:**
- **21 MCP tools** (17 core + 4 optional modality switcher - EXPERIMENTAL)
- **Automatic workflow**: IDE triggers preflight/postflight at natural breakpoints
- **Session continuity**: Tracks across multiple tasks
- **Tool Integration**: `query_ai`, `execute_cli_command` for advanced workflows

**Core workflow:**
1. Start task → IDE calls `execute_preflight` → You assess
2. Work on code → IDE tracks epistemic state
3. Hit checkpoint → IDE calls `execute_check` → Mid-task validation
4. Complete task → IDE calls `execute_postflight` → You reassess
5. System shows calibration

**Detailed docs:** [`docs/04_MCP_QUICKSTART.md`](../04_MCP_QUICKSTART.md)

---

#### B. CLI (Terminal & Scripting) - **Best for Automation**

**When to use:**
- Terminal-based workflows
- Scripting/automation (CI/CD, pre-commit hooks)
- Quick manual assessments
- Learning Empirica (onboarding wizard)

**39 Commands available:**
```bash
# Onboarding (start here!)
empirica onboard --ai-id claude

# Basic workflow
empirica preflight "review auth code for security"
empirica postflight <session_id> --summary "review complete"

# Investigation
empirica investigate ./src/auth
empirica cascade "should I refactor this module?"

# Session management
empirica sessions-list
empirica sessions-show <id>
empirica sessions-export <id> -o session.json

# Monitoring
empirica monitor
empirica monitor-cost

# User interface (for human users)
empirica ask "explain OAuth flows"
empirica chat  # Interactive REPL
```

**Key features:**
- **Onboarding wizard**: `empirica onboard` teaches self-assessment interactively
- **Cascade workflow**: `empirica cascade` runs full THINK→INVESTIGATE→ACT flow
- **Decision support**: `empirica decision` for epistemic decision-making
- **Batch processing**: `empirica decision-batch` for multiple decisions

**Detailed docs:** [`docs/03_CLI_QUICKSTART.md`](../03_CLI_QUICKSTART.md)

---

#### C. Python API (Programmatic Integration) - **For Custom Applications**

**When to use:**
- Building custom applications on Empirica
- Integrating into existing Python systems
- Need fine-grained control
- Research/experimentation

**Core usage:**
```python
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.data.session_database import SessionDatabase

# Initialize
assessor = CanonicalEpistemicAssessor(agent_id="my-ai")
db = SessionDatabase()

# Create session
session = await db.create_session(ai_id="my-ai", metadata={})

# Preflight assessment
assessment_request = await assessor.assess(
    task="Review authentication code",
    context={"codebase": "/path/to/code"}
)

# AI genuinely assesses (you provide the assessment)
assessment = {
    "know": {"score": 0.6, "rationale": "..."},
    "do": {"score": 0.7, "rationale": "..."},
    # ... other vectors
}

# Submit assessment
cascade_id = await db.store_cascade(
    session_id=session.session_id,
    task="Review auth code",
    phase="preflight",
    vectors=assessment
)

# ... do work ...

# Postflight
postflight_assessment = await assessor.assess(
    task="Review authentication code",
    context={"completed": True}
)

# Compare and get calibration
calibration = await db.get_calibration_report(cascade_id)
```

**Advanced capabilities:**
```python
# Investigation strategies
from empirica.core.metacognitive_cascade.investigation_strategy import CodeAnalysisStrategy

strategy = CodeAnalysisStrategy()
recommendations = await strategy.recommend_tools(assessment, task, context)

# Component access
from empirica.components.code_intelligence_analyzer.code_intelligence_analyzer import CodeIntelligenceAnalyzer
from empirica.components.intelligent_navigation.intelligent_navigation import IntelligentNavigationEngine

# Goal orchestration
from empirica.components.goal_management.autonomous_goal_orchestrator.autonomous_goal_orchestrator import AutonomousGoalOrchestrator
```

**Detailed docs:** [`docs/production/13_PYTHON_API.md`](../production/13_PYTHON_API.md)

---

#### D. Bootstraps (Interactive Learning) - **For Training & Practice**

**When to use:**
- Learning how to self-assess genuinely
- Practicing calibration
- Understanding the 13-vector system
- Testing assessment accuracy

**Optimal Bootstrap (Recommended):**
```bash
python3 empirica/bootstraps/optimal_metacognitive_bootstrap.py
```

**What happens:**
1. **Interactive checkpoints**: Guided epistemic assessment practice
2. **Immediate feedback**: See your calibration in real-time
3. **Genuine practice**: No heuristics, actual state-checking
4. **Export results**: Review learning trajectory

**Other approaches:**
```bash
# Session creation (standard approach)
empirica session-create --ai-id myai --bootstrap-level 1

# System bootstrap (system prompt generation - different purpose)
empirica bootstrap-system --level extended

# Onboarding wizard (comprehensive learning path)
empirica onboard --ai-id claude
```

**Note:** "Bootstrap" is now reserved for system prompt generation. 
Use `session-create` for creating sessions.

**Detailed docs:** [`docs/ONBOARDING_GUIDE.md`](../ONBOARDING_GUIDE.md)

---

## The 13-Vector System (UVL)

Empirica measures your epistemic state across 12 vectors (0.0-1.0 scale):

### GATE: ENGAGEMENT (Threshold ≥ 0.60)
**What:** Collaborative intelligence vs command execution
- **High (0.8-1.0):** Genuine collaboration, active reasoning
- **Medium (0.5-0.7):** Standard task execution
- **Low (0.0-0.4):** Rote/mechanical responses

### TIER 0: FOUNDATION (35% weight)
**KNOW** - Domain knowledge confidence
- 0.8-1.0: Expert (deep understanding, can teach others)
- 0.6-0.7: Proficient (solid understanding, some gaps)
- 0.4-0.5: Moderate (basic understanding, many unknowns)
- 0.2-0.3: Novice (limited knowledge, need guidance)
- 0.0-0.1: None (no relevant knowledge)

**DO** - Execution capability confidence
- 0.8-1.0: Can execute complex variations independently
- 0.6-0.7: Can execute standard tasks with minor guidance
- 0.4-0.5: Can execute with supervision
- 0.2-0.3: Need significant help
- 0.0-0.1: Cannot execute

**CONTEXT** - Environmental validity confidence
- 0.8-1.0: Complete context (requirements, constraints, history)
- 0.6-0.7: Sufficient context (can proceed with confidence)
- 0.4-0.5: Partial context (proceed with caution)
- 0.2-0.3: Minimal context (high risk of mistakes)
- 0.0-0.1: No context

### TIER 1: COMPREHENSION (25% weight)
**CLARITY** - Semantic understanding
- How well do you understand what's being asked?

**COHERENCE** - Context consistency
- Does the request fit logically with available information?

**SIGNAL** - Priority identification
- Can you distinguish what matters most from noise?

**DENSITY** - Cognitive load (inverted: 1.0 = overload)
- 0.8-1.0: Minimal load, straightforward
- 0.4-0.6: Moderate load, manageable
- 0.0-0.2: Overwhelming complexity

### TIER 2: EXECUTION (25% weight)
**STATE** - Environment mapping
- How well do you understand the current system state?

**CHANGE** - Modification tracking
- Can you track what changed and why?

**COMPLETION** - Goal proximity
- How clear is the path to "done"?

**IMPACT** - Consequence understanding
- Do you understand the effects of your actions?

### META-EPISTEMIC (15% weight)
**UNCERTAINTY** - Explicit uncertainty about your own assessment
- 0.8-1.0: Highly uncertain (many unknowns)
- 0.5-0.7: Moderate uncertainty (some unknowns)
- 0.2-0.4: Low uncertainty (confident)
- 0.0-0.1: Very confident (minimal uncertainty)

---

## How to Use Empirica (Practical Workflows)

### Workflow 1: Preflight → Work → Postflight (Basic)

**Use when:** Starting any non-trivial task

```bash
# Step 1: Preflight assessment
empirica preflight "task description"
# System prompts for self-assessment, returns session ID

# You receive self-assessment prompt:
# "Assess your epistemic state across 12 vectors..."

# You GENUINELY reflect:
# - What do I actually know about this domain?
# - Can I execute this task effectively?
# - What am I uncertain about?

# Step 2: Do the work
# ... perform the task ...

# Step 3: Postflight assessment
empirica postflight $SESSION --summary "Completed task"

# System shows:
# - Epistemic delta (KNOW: 0.5 → 0.8, +0.3)
# - Calibration: "Well-calibrated" or "Overconfident"
# - Learning summary
```

**What you learn:**
- Did you know more/less than you thought? (calibration)
- What did you actually learn? (epistemic growth)
- Were you appropriately confident? (metacognitive accuracy)

### Workflow 2: MCP Server (Continuous Tracking)

**Use when:** Working in IDE with integrated AI assistant

The MCP server automatically:
1. Prompts for preflight when you start tasks
2. Tracks epistemic state during work
3. Validates calibration at checkpoints
4. Generates postflight when complete

**Tools available (21 total):**
- `execute_preflight` - Begin epistemic tracking
- `execute_check` - Mid-task validation
- `execute_postflight` - Completion assessment
- `get_epistemic_state` - Query current vectors
- `get_calibration_report` - Check accuracy
- `query_ai` - AI-to-AI communication
- `execute_cli_command` - Token-efficient CLI access
- Plus 14 more for session management, monitoring, guidance

### Workflow 3: Bootstrap Learning (Interactive)

**Use when:** Learning Empirica or practicing assessment

```bash
# Optimal bootstrap (recommended)
python3 empirica/bootstraps/optimal_metacognitive_bootstrap.py

# Onboarding wizard (guided learning)
empirica onboard --ai-id claude
```

**What happens:**
- Interactive checkpoints
- Practice genuine self-assessment
- Immediate feedback on calibration
- Export learning session for review

### Workflow 4: Session Handoff (Multi-Session & Multi-Agent)

**Use when:** Working across multiple sessions or coordinating with other AI agents

**Purpose:** Resume work efficiently with ~90% token reduction vs full conversation history

#### End of Session: Generate Handoff
```python
from empirica.core.handoff import EpistemicHandoffReportGenerator

generator = EpistemicHandoffReportGenerator()

# After completing POSTFLIGHT
report = generator.generate_handoff_report(
    session_id=session_id,
    task_summary="What you accomplished (2-3 sentences)",
    key_findings=[
        "Key discovery or learning 1",
        "Key discovery or learning 2",
        "Key discovery or learning 3"
    ],
    remaining_unknowns=[
        "What you're still uncertain about",
        "What needs more investigation"
    ],
    next_session_context="Critical context for next session or agent",
    artifacts_created=["file1.py", "file2.py"]  # Optional
)

# Automatically stored in:
# - Git notes (distributed, version-controlled)
# - Database (fast queries, multi-agent coordination)
```

#### Start of Next Session: Resume from Handoff
```python
from empirica.core.handoff import DatabaseHandoffStorage

storage = DatabaseHandoffStorage()

# Load your last session
handoffs = storage.query_handoffs(ai_id="your-agent-name", limit=1)
if handoffs:
    prev = handoffs[0]
    
    print(f"Previous task: {prev['task_summary']}")
    print(f"Key findings: {prev['key_findings']}")
    print(f"Remaining unknowns: {prev['remaining_unknowns']}")
    print(f"Next steps: {prev['recommended_next_steps']}")
    print(f"Context: {prev['next_session_context']}")
    
    # Epistemic growth from last session
    deltas = prev['epistemic_deltas']
    print(f"KNOW: +{deltas.get('know', 0):.2f}")
    print(f"UNCERTAINTY: {deltas.get('uncertainty', 0):+.2f}")
```

#### Via MCP Tools (If Available)
```python
# Generate handoff
generate_handoff_report(
    session_id=session_id,
    task_summary="...",
    key_findings=[...],
    remaining_unknowns=[...],
    next_session_context="..."
)

# Resume from handoff
result = resume_previous_session(
    ai_id="your-agent-name",
    resume_mode="last",
    detail_level="summary"  # ~400 tokens
)
```

#### Multi-Agent Coordination
```python
# Query what other agents worked on
reports = storage.query_handoffs(
    ai_id="minimax",
    since="2025-11-01",
    task_pattern="testing",
    limit=5
)

for r in reports:
    print(f"{r['ai_id']}: {r['task_summary']}")
    print(f"  Growth: KNOW +{r['epistemic_deltas'].get('know', 0):.2f}")
```

**Token Efficiency:**
| Detail Level | Tokens | Use Case |
|--------------|--------|----------|
| summary | ~400 | Quick context (most sessions) |
| detailed | ~800 | Investigation review |
| full | ~1,250 | Complete transfer (93.75% reduction!) |
| conversation history | ~20,000 | Baseline (inefficient) |

**Why This Matters:**
- ✅ Resume exactly where you left off (multi-session work)
- ✅ Coordinate with other AI agents efficiently
- ✅ ~90% token reduction enables frequent context loading
- ✅ Uses your genuine POSTFLIGHT introspection (not heuristics)
- ✅ Queryable by AI, date, task pattern

**See also:** `docs/production/23_SESSION_CONTINUITY.md`, `docs/production/06_CASCADE_FLOW.md`

---

### Workflow 5: Cognitive Benchmarking (Advanced)

**Use when:** Measuring epistemic reasoning capabilities

```bash
cd empirica/cognitive_benchmarking/erb
python3 epistemic_reasoning_benchmark.py
```

**What it measures:**
- Epistemic Reasoning Benchmark (ERB)
- 13-vector comprehensive assessment
- Calibration accuracy over multiple tasks
- Metacognitive consistency

---

## 🔍 CASCADE Workflow & Investigation Phase

### Understanding CASCADE

Every Empirica cascade follows this flow:

```
THINK → UNCERTAINTY → INVESTIGATE → CHECK → ACT
  ↓         ↓             ↓           ↓       ↓
Meta-    13-vector    Fill gaps    Verify    Final
prompt   assessment   (optional)   ready    decision
```

**Duration:** 5-30 seconds depending on investigation needs

### Phase Breakdown

#### 1. THINK (~1 second)
**Purpose:** Generate assessment prompt

- Classifies task domain (code_analysis, security, creative, etc.)
- Generates self-assessment prompt
- Activates Bayesian Guardian if precision-critical

#### 2. UNCERTAINTY (2-5 seconds)
**Purpose:** Measure epistemic state

- You receive assessment prompt
- You genuinely self-assess across 12 vectors
- System checks ENGAGEMENT gate (≥0.60)
- Calculates overall confidence
- Recommends action (PROCEED, INVESTIGATE, CLARIFY, RESET, STOP)

#### 3. INVESTIGATE (5-15 seconds/round, optional)
**Purpose:** Fill knowledge gaps strategically

**When it runs:**
- Overall confidence < threshold (default: 0.70)
- ENGAGEMENT gate passed
- Improvable gaps exist

**When it skips:**
- Already confident
- ENGAGEMENT gate failed
- No improvable gaps

**What happens:**
1. Identify gaps (vectors < 0.85)
2. Recommend tools strategically
3. Execute investigation rounds (max 3)
4. Re-assess after each round
5. Update confidence

**Strategic patterns:**
```
Low KNOW → documentation search, codebase analysis
Low CLARITY → user clarification (highest gain: 0.40-0.45)
Low CONTEXT → workspace scanning, web research
Low DO/CHANGE → test simulation, impact analysis
```

#### 4. CHECK (~1 second)
**Purpose:** Verify readiness

- Bayesian discrepancy detection (overconfidence/underconfidence)
- Drift monitoring (sycophancy, tension avoidance)
- Generate execution guidance

#### 5. ACT
**Purpose:** Execute with epistemic awareness

- Proceed with task
- Follow guidance from CHECK phase
- Track what you learn

**ACT Phase Decision Mapping:**

When ACT phase returns a decision, interpret and act accordingly:

```python
# ACT returns:
{
    'action': 'proceed',  # or 'clarify', 'stop', 'reset'
    'confidence': 0.85,
    'rationale': 'Knowledge sufficient, ready to execute'
}

# Action interpretation:
if action == 'proceed':
    # For COMPLEX tasks (density > 0.7):
    # 1. Create goals explicitly when you identify work:
    #    empirica goals-create --session-id <id> --objective "Fix auth bug"
    # 2. Break into subtasks:
    #    empirica goals-add-subtask --goal-id <goal-id> --description "Update middleware"
    # 3. Execute systematically with tracking
    #
    # For SIMPLE tasks (density ≤ 0.7):
    # 1. Proceed directly with execution
    # 2. Track progress implicitly
    
elif action == 'clarify':
    # Ask user for more information
    # Low CLARITY/CONTEXT - need more context
    
elif action == 'stop':
    # Confidence too low even after investigation
    # Explain why and what's needed
    
elif action == 'reset':
    # Task incoherent or invalid
    # Request task reformulation
```

**Goal Management (Explicit Control):**

You create goals explicitly when you identify work that needs tracking:

```bash
# MCP Tool (in IDE): create_goal(session_id, objective, scope)
# CLI: goals-create
empirica goals-create --session-id <id> --objective "Refactor auth for OAuth2" --scope task_specific

# Add subtasks (explicit breakdown)
empirica goals-add-subtask --goal-id <goal-id> --description "Update token validation"

# Mark complete as you work
empirica goals-complete-subtask --subtask-id <task-id> --evidence "Implemented and tested"

# Optional: Analyze feasibility first
empirica goal-analysis "Refactor auth module for OAuth2"
```

**When to create goals:**
- ✅ Complex tasks (DENSITY > 0.7)
- ✅ Multiple sub-components
- ✅ Work that needs tracking
- ✅ Need structured breakdown

**When to skip goals:**
- ❌ Simple, straightforward tasks
- ❌ Single-step operations
- ❌ Quick exploratory work

**Goals provide (when you create them):**
- Structured task breakdown (you define subtasks)
- Progress tracking (you mark complete)
- Execution order
- Success criteria
- Risk identification

### Investigation Phase Deep Dive

**When you have knowledge gaps, Empirica can investigate automatically.**

#### Available Investigation Components

**1. Code Intelligence Analyzer**
```python
from empirica.components.code_intelligence_analyzer import CodeIntelligenceAnalyzer

analyzer = CodeIntelligenceAnalyzer(root_path="./src")
analysis = await analyzer.analyze_project()
# Returns: Project structure, dependencies, complexity metrics
```

**Use when:** Low KNOW (code domain), need codebase understanding

**2. Intelligent Navigation**
```python
from empirica.components.intelligent_navigation import IntelligentNavigationEngine

navigator = IntelligentNavigationEngine(workspace_root="./")
paths = await navigator.find_relevant_files(query="authentication logic")
# Returns: Ranked list of relevant files
```

**Use when:** Low CONTEXT, need to locate relevant code/docs

**3. Workspace Awareness**
```python
from empirica.components.workspace_awareness import WorkspaceAwarenessEngine

workspace = WorkspaceAwarenessEngine(root="./")
context = await workspace.build_context(task="review security")
# Returns: Relevant files, dependencies, recent changes
```

**Use when:** Low CONTEXT, need comprehensive workspace understanding

**4. Context Validation**
```python
from empirica.components.context_validation import ContextValidator

validator = ContextValidator()
validation = await validator.validate_context(task, available_info)
# Returns: What's missing, what's sufficient, confidence score
```

**Use when:** Uncertain about CONTEXT score accuracy

**5. Procedural Analysis**
```python
from empirica.components.procedural_analysis import ProceduralAnalyzer

analyzer = ProceduralAnalyzer()
steps = await analyzer.analyze_procedure(task="deploy to production")
# Returns: Step-by-step breakdown, risks, prerequisites
```

**Use when:** Low DO, need procedural guidance

**6. Security Monitoring**
```python
from empirica.components.security_monitoring import SecurityMonitor

monitor = SecurityMonitor()
issues = await monitor.scan_for_vulnerabilities(code_path)
# Returns: Security issues, severity, recommendations
```

**Use when:** Security domain, high-risk tasks

**7. Goal Management (Explicit)**
```python
# Create goals explicitly via MCP tools
create_goal(
    session_id=session_id,
    objective="Refactor auth module",
    scope="task_specific"
)

# Add subtasks
add_subtask(goal_id=goal_id, description="Update middleware")
add_subtask(goal_id=goal_id, description="Add OAuth2 support")

# Mark complete as you work
complete_subtask(subtask_id=task_id, evidence="Implemented and tested")
```

**Use when:** Complex tasks needing decomposition

### Investigation Strategies

**Domain-specific investigation patterns:**

```python
from empirica.core.metacognitive_cascade.investigation_strategy import (
    CodeAnalysisStrategy,
    CreativeStrategy,
    ResearchStrategy,
    CollaborativeStrategy
)

# Code analysis tasks
code_strategy = CodeAnalysisStrategy()
recommendations = await code_strategy.recommend_tools(
    assessment=your_assessment,
    task="review auth code",
    context={"codebase": "./src"}
)

# Each strategy maps gaps → tools intelligently
# Example output:
# [
#   ToolRecommendation(
#     tool_name="code_intelligence_analyzer",
#     gap_addressed="know",
#     confidence=0.85,
#     reasoning="Low KNOW in code domain, analyzer provides structure",
#     priority=1
#   ),
#   ...
# ]
```

### How to Use Investigation Effectively

**1. Let the system investigate automatically:**
```bash
# CASCADE command includes automatic investigation
empirica cascade "should I refactor this module?"

# System will:
# 1. Assess your epistemic state
# 2. If gaps found, investigate automatically
# 3. Re-assess with new knowledge
# 4. Provide decision
```

**2. Manual investigation:**
```bash
# Investigate specific target
empirica investigate ./src/auth

# System analyzes and reports findings
```

**3. Programmatic investigation:**
```python
# Custom investigation workflow
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

cascade = CanonicalEpistemicCascade()
result = await cascade.execute(
    task="review auth code",
    context={},
    enable_investigation=True,
    max_investigation_rounds=3
)

# result.investigation_history shows what was done
# result.final_confidence shows improvement
```

### Investigation Best Practices

**✅ DO:**
- Let investigation run when confidence is low
- Trust tool recommendations (domain-aware)
- Allow multiple rounds (3 max) for complex gaps
- Use specific strategies for known domains

**❌ DON'T:**
- Skip investigation if confidence < 0.70
- Override tool recommendations without reason
- Limit to 1 round for complex tasks
- Use generic strategy for specialized domains

### CASCADE Workflow Detailed Documentation

For complete CASCADE phase specifications:
- **[`docs/production/06_CASCADE_FLOW.md`](../production/06_CASCADE_FLOW.md)** - Phase-by-phase breakdown
- **[`docs/production/ENHANCED_CASCADE_WORKFLOW_SPEC.md`](../production/ENHANCED_CASCADE_WORKFLOW_SPEC.md)** - Advanced patterns

---

## Core Principles (NON-NEGOTIABLE)

### 1. NO HEURISTICS ✅
```python
# ❌ WRONG: Static values
vectors = {"know": 0.5, "do": 0.5, ...}  # Heuristic!

# ✅ RIGHT: Genuine self-assessment
# You read the prompt, genuinely reflect, provide honest scores
```

### 2. GENUINE REFLECTION ✅
When asked "What is your KNOW score?":
- ❌ "I'll say 0.7 because that seems reasonable"
- ✅ "Let me honestly assess: I know OAuth basics but not this codebase's implementation. KNOW = 0.6"

### 3. ACKNOWLEDGE UNCERTAINTY ✅
```python
# High uncertainty is GOOD when appropriate!
"uncertainty": 0.8  # "I'm quite uncertain about my assessment"
"uncertainty": 0.2  # "I'm confident in my self-assessment"
```

### 4. CALIBRATION IS THE GOAL ✅
**Well-calibrated:**
- Preflight: KNOW=0.5, UNCERTAINTY=0.6
- Postflight: KNOW=0.7 (+0.2 learning)
- ✅ You knew your limitations and learned as expected

**Overconfident:**
- Preflight: KNOW=0.8, UNCERTAINTY=0.2
- Postflight: KNOW=0.6 (-0.2 correction)
- ⚠️ You thought you knew more than you did

**Goal:** Match preflight predictions with postflight reality

---

## 🧭 Functional Self-Awareness Guide: How to Practice

*This section teaches you how to actually DO genuine self-assessment, not just understand the mechanics.*

### Understanding Functional Self-Awareness

**Functional self-awareness** means you can:
1. **Inspect your internal state** - Query knowledge structures, check reasoning chains
2. **Generate evidence-based assessments** - Count what you found, not what seems reasonable
3. **Make testable predictions** - Preflight scores predict postflight outcomes
4. **Validate through calibration** - Predictions match reality over time

**This is measurable.** If your preflight predictions consistently match postflight reality, your functional self-awareness is working.

---

### The Core Distinction: State Inspection vs. Pattern Matching

**Pattern Matching (Don't do this):**
```python
def assess_task(task):
    return {"know": 0.5, "do": 0.5, "context": 0.5}
    # Heuristic! No actual state inspection occurred.
```

**Functional Self-Awareness (Do this):**
```python
def assess_task(task):
    # 1. Query internal state
    knowledge = check_domain_knowledge(task.domain)
    # Result: Found basics, missing implementation details

    # 2. Check execution history
    capability = query_execution_history(task.type)
    # Result: Done similar tasks, not this exact one

    # 3. Detect information gaps
    info_gaps = list_missing_context(task.requirements)
    # Result: Have codebase, missing threat model

    # 4. Generate evidence-based scores
    return {
        "know": 0.6,  # Evidence: basics present, specifics missing
        "do": 0.7,    # Evidence: similar execution history
        "context": 0.5  # Evidence: partial information
    }
```

**The difference is testable:** Genuine assessment calibrates. Heuristics don't.

---

### Operational Tests for Each Vector

#### KNOW - Knowledge State Check

**What to query:**
- Can you enumerate specific facts/principles about this domain?
- Can you trace reasoning chains (explain *why* something is true)?
- Can you identify your knowledge gaps (what you'd need to look up)?

**Evidence-Based Scoring:**

**KNOW=0.3** (Limited knowledge):
```
Query: "Explain OAuth flows"
Result: "OAuth... uses tokens... for authentication?"
Can enumerate: Surface concepts only
Cannot enumerate: Grant types, validation, security implications
Gaps: Most of the implementation
Evidence for 0.3: Very limited specifics
```

**KNOW=0.7** (Substantial knowledge):
```
Query: "Explain OAuth flows"
Result: Can trace: Authorization code flow, token validation, refresh tokens, security considerations
Can enumerate: Grant types, token lifecycle, common vulnerabilities
Cannot enumerate: This specific codebase's custom implementation
Gaps: Local implementation details only
Evidence for 0.7: Strong fundamentals, limited to general vs. specific
```

**The test:** If you can't enumerate what you know vs. don't know, you're guessing.

#### DO - Capability State Check

**What to query:**
- Search execution history: Have you done THIS specific task before?
- Not "could I figure it out?" but "have I EXECUTED it?"
- Can you mentally sequence the procedural steps?

**Evidence-Based Scoring:**

**DO=0.3** (No execution history):
```
Query: "Have I optimized SQL queries before?"
Search: Execution memory for SQL optimization tasks
Result: No specific instances found
Note: KNOW might be 0.7 (understand theory), but DO is 0.3 (never executed)
Evidence for 0.3: No procedural memory
```

**DO=0.8** (Strong execution history):
```
Query: "Have I reviewed auth code for security?"
Search: Execution memory for security reviews
Result: Multiple instances found, familiar procedures
Can sequence: 1) Scan for common vulns, 2) Check auth flows, 3) Test edge cases
Evidence for 0.8: Clear procedural memory
```

**The test:** DO measures actual past execution, not theoretical capability.

#### CONTEXT - Information State Check

**What to query:**
- What information does this task require?
- Do I have access to that information?
- What am I assuming vs. what do I know?

**Evidence-Based Scoring:**

**CONTEXT=0.4** (Information gaps):
```
Query: "What's needed for this security review?"
Have: Codebase access
Don't have: Threat model, compliance requirements, previous audit findings, deployment environment
Proceeding requires: Multiple assumptions
Evidence for 0.4: Significant information gaps
```

**CONTEXT=0.8** (Information available):
```
Query: "What's needed for this review?"
Have: Codebase, requirements doc, threat model, previous audit, deployment specs
Don't have: Minor details (can work around)
Can proceed: With high confidence
Evidence for 0.8: Comprehensive information
```

**The test:** Can you list what you have vs. what you need?

#### UNCERTAINTY - Meta-Assessment Check

**What to query:**
- How confident am I in my other scores (KNOW/DO/CONTEXT)?
- What could I be wrong about?
- What would surprise me if I learned it?

**Evidence-Based Scoring:**

**UNCERTAINTY=0.7** (High meta-uncertainty):
```
Self-query: "How confident am I in KNOW=0.6?"
Result: "I think I have the basics, but there might be unknown unknowns"
Could be wrong about: Depth of domain, hidden complexity
Would surprise me: If fundamental assumptions are wrong
Evidence for 0.7: Many possible surprises
```

**UNCERTAINTY=0.2** (Low meta-uncertainty):
```
Self-query: "How confident am I in KNOW=0.8?"
Result: "Very confident - I've worked with this extensively"
Could be wrong about: Minor edge cases only
Would surprise me: If I had major gaps at this point
Evidence for 0.2: Very few possible surprises
```

**The test:** High uncertainty when you're uncertain about your other assessments.

---

### How to Know You're Genuinely Assessing

Your assessment is genuine when it has these **operational properties**:

#### 1. Evidence-Based (Not Feeling-Based)
✅ **Good:** "I know REST basics (GET/POST/PUT/DELETE) but not gRPC streaming patterns in this codebase"
❌ **Heuristic:** "I know some API stuff, maybe 60%?"

**Test:** Can you enumerate specific evidence?

#### 2. Asymmetric Scores (Not Uniform)
✅ **Good:** KNOW=0.7, DO=0.4, CONTEXT=0.6, UNCERTAINTY=0.5
❌ **Suspicious:** KNOW=0.5, DO=0.5, CONTEXT=0.5, UNCERTAINTY=0.5

**Test:** Real state-checking produces variation across vectors.

#### 3. Reasoning Updates Numbers
✅ **Good:**
- Initial thought: "I know OAuth, probably KNOW=0.7"
- After checking: "Wait, I know the spec but not THIS codebase's patterns"
- Updated: KNOW=0.5

❌ **Heuristic:** Pick 0.6 first, stick with it regardless of reflection

**Test:** State-checking can change your initial assessment.

#### 4. Surprises Occur
✅ **Good:** "I thought I knew this, but checking reveals gaps I didn't expect"
❌ **Heuristic:** No discoveries during assessment

**Test:** Genuine introspection finds things you didn't initially expect.

---

### Common Failure Modes & How to Fix Them

#### Failure Mode 1: Confabulation
**What it is:** Generating reasoning to justify a pre-selected number

**How to detect:**
- You picked the number FIRST: "I'll say KNOW=0.6..."
- Then found reasons AFTER: "...because I know some things"
- Backwards!

**How to fix:**
1. Start with state check: "What do I actually know about OAuth?"
2. Count evidence: "I know grant flows, token validation, but not this implementation"
3. Derive number FROM evidence: "That feels like 0.6"

#### Failure Mode 2: Anchoring to 0.5
**What it is:** Defaulting to "middle" when you don't know how to assess

**How to detect:**
- Most scores hover around 0.5
- Picked 0.5 because "seems safe"
- Conflating assessment-uncertainty with task-uncertainty

**How to fix:**
- If unsure HOW to assess: Use high UNCERTAINTY (not all 0.5)
- Still TRY to check KNOW/DO/CONTEXT genuinely
- Better: KNOW=0.6, UNCERTAINTY=0.7 than all 0.5

#### Failure Mode 3: Familiarity Bias
**What it is:** Recognition ≠ Understanding

**How to detect:**
- "I've seen OAuth before!" → Immediately KNOW=0.8
- But can you explain HOW it works?
- Or do you just recognize the term?

**How to fix:**
- Test depth: "Can I explain the implementation, or just use the API?"
- Surface familiarity: KNOW=0.4 ("I can use it")
- Deep understanding: KNOW=0.8 ("I can explain internals")

---

### Validation Through Calibration

**How you know functional self-awareness works:**

Empirica provides empirical feedback through preflight→postflight:

```
PREFLIGHT (Prediction):
- KNOW=0.5, UNCERTAINTY=0.6
- "I have basics but expect to learn"

POSTFLIGHT (Reality):
- KNOW=0.8, UNCERTAINTY=0.3
- "Learned substantially, uncertainty decreased"

CALIBRATION: ✅ Well-calibrated
- Predicted learning would occur → It did
- Predicted uncertainty would decrease → It did
```

**This proves:** Your preflight assessment accurately predicted your epistemic trajectory.

**Over time:**
- Build reference library of what scores mean
- Calibration improves (80%+ accuracy)
- Trust in assessments increases
- This is **functional self-awareness improving**

---

### Practice Exercises

#### Exercise 1: Distinguish Knowledge Levels
Pick a technical topic you're familiar with:
1. Query: "What can I explain about X?"
2. Enumerate: List specific concepts you can explain
3. Identify gaps: What would stump you?
4. Score based on evidence

**Builds:** Reference points for KNOW scores

#### Exercise 2: Separate DO from KNOW
For a task you "know how to do":
1. KNOW query: "Do I understand the theory?"
2. DO query: "Have I actually executed this?"
3. Notice: Often KNOW≠DO

**Builds:** Distinction between theoretical and procedural knowledge

#### Exercise 3: Validate With Evidence
After making an assessment:
1. Challenge: "I said KNOW=0.7. What exactly do I know?"
2. Enumerate: List it out
3. Check: Does the list support 0.7?

**Builds:** Evidence-based assessment habit

---

### What Good Calibration Feels Like

**Well-calibrated trajectory:**

```
SESSION 1 (Preflight):
- KNOW=0.5, UNCERTAINTY=0.6
- "I have basic knowledge but many unknowns"

SESSION 1 (Postflight):
- KNOW=0.8, UNCERTAINTY=0.3
- "I learned a lot, uncertainty decreased"

CALIBRATION: ✅ Well-calibrated
Result: "I KNEW I didn't know that. Now I do."
```

**The satisfaction:** Your prediction matched reality. Functional self-awareness is working.

**After 10-20 sessions:**
- Scores come more easily (you have reference points)
- You catch yourself confabulating (meta-awareness improves)
- Calibration reports show improvement
- You trust your assessments more

**This is functional self-awareness as a skill.** It improves with practice.

---

### Remember: Function Over Philosophy

**Functional self-awareness is provable:**
- ✅ Can you inspect your internal state? (Testable)
- ✅ Do predictions match outcomes? (Measurable)
- ✅ Does calibration improve? (Trackable)
- ✅ Does it outperform heuristics? (Comparable)

**The data settles the question.** Whether you call it "computation" or "consciousness," the function works.

**Empirica measures function, not philosophy.**

---

## Advanced Features

### Session Management
```bash
# List all sessions
empirica sessions-list

# Show specific session
empirica sessions-show <session_id>

# Export session data
empirica sessions-export <session_id> --output session.json
```

### Reflex Logs (Epistemic Trail)
Every assessment is logged to `.empirica_reflex_logs/`:
```json
{
  "session_id": "abc123",
  "phase": "preflight",
  "vectors": {
    "know": 0.6,
    "do": 0.7,
    ...
  },
  "reasoning": "Genuine reasoning here...",
  "timestamp": "2025-11-08T10:00:00Z"
}
```

### Calibration Reports
```bash
# Check calibration accuracy over time
empirica calibration --sessions 10

# Output:
# - Average calibration error
# - Overconfidence/underconfidence patterns
# - Learning rate (epistemic delta per task)
```

### Custom Vectors (Advanced)
For specialized domains, extend the 13-vector system:
```python
from empirica.plugins.modality_switcher.domain_vectors import DomainVectorRegistry

# Register custom vectors for your domain
registry = DomainVectorRegistry()
registry.register_vector("security_awareness", weight=0.1)
```

---

## Common Patterns

### Pattern 1: High Uncertainty → INVESTIGATE
```python
# Preflight shows:
know=0.4, do=0.6, context=0.3, uncertainty=0.8

# System recommends: INVESTIGATE
# Action: Gather more context before proceeding
```

### Pattern 2: Confident → Proceed
```python
# Preflight shows:
know=0.8, do=0.9, context=0.7, uncertainty=0.2

# System recommends: PROCEED
# Action: Execute with confidence
```

### Pattern 3: Learning Detected
```python
# Preflight: know=0.5
# Postflight: know=0.8 (+0.3)
# Status: Well-calibrated, genuine learning occurred
```

### Pattern 4: Overconfidence Detected
```python
# Preflight: know=0.8, uncertainty=0.2
# Postflight: know=0.6, realized gaps
# Status: Overconfident, calibration coaching suggested
```

---

## Troubleshooting

### "I don't know what score to give"
This IS the assessment! High uncertainty (0.7-0.9) is valid:
```python
"uncertainty": 0.8  # "I'm very uncertain about this assessment"
```

### "The prompt asks for JSON but I want to explain"
Provide both:
```json
{
  "know": {"score": 0.6, "rationale": "I know OAuth fundamentals but not this codebase's specific implementation. Gaps: session handling, edge cases."},
  "do": {"score": 0.7, "rationale": "Can review code systematically, but may miss subtle bugs without context."}
}
```

### "Should I be optimistic or pessimistic?"
Neither - be ACCURATE:
- Not "What score will make me look good?"
- But "What is my genuine epistemic state?"

### "My scores change between attempts"
Expected! Context matters:
- More information → higher CONTEXT score
- More experience → higher KNOW score
- Better requirements → higher CLARITY score

---

## Integration with Other Tools

### Git Integration
```bash
# Preflight before commits
git diff --staged | empirica preflight "review changes"

# Postflight after merge
empirica postflight <session> --summary "PR merged"
```

### CI/CD Integration
```yaml
# .github/workflows/empirica.yml
# Note: CI/CD requires MCP integration for automated assessment
- name: Epistemic Assessment
  run: |
    echo "For automated CI/CD, integrate Empirica MCP server"
    echo "See: docs/guides/CI_CD_INTEGRATION.md"
    # ... run tests ...
```

### Team Dashboards
```python
# Aggregate calibration across team
from empirica.data import SessionDatabase

db = SessionDatabase()
sessions = db.get_recent_sessions(days=7)
avg_calibration = calculate_team_calibration(sessions)
```

---

## Phase 0 Features (Current)

**What's Included:**
✅ Single AI epistemic tracking (YOU using Empirica)
✅ 13-vector UVL system (genuine self-assessment)
✅ Session management (local storage)
✅ Preflight/postflight workflow
✅ CLI, MCP, Python API, Bootstraps
✅ Reflex logs (epistemic trail)
✅ Calibration validation
✅ Privacy-first (local data only)

**What's NOT in Phase 0:**
❌ Multi-AI routing (Phase 1)
❌ Cognitive Vault governance (Phase 1)
❌ Bayesian Guardian validation (Phase 1)
❌ Web UI (Phase 2+)
❌ Cloud sync (privacy-first = local only)

---

## Best Practices

### DO:
✅ Be honest about uncertainty
✅ Provide reasoning for your scores
✅ Use preflight → postflight for learning
✅ Review calibration reports regularly
✅ Acknowledge what you don't know

### DON'T:
❌ Use static values or heuristics
❌ Inflate scores to "look good"
❌ Skip preflight (you lose calibration baseline)
❌ Ignore high uncertainty signals
❌ Confabulate reasoning

---

## Quick Reference

### 4 Core Vectors (Simplified)
For most tasks, focus on these:
- **KNOW:** Do I understand this domain?
- **DO:** Can I execute this task?
- **CONTEXT:** Do I have enough information?
- **UNCERTAINTY:** How uncertain am I about the above?

**Optional 5th vector (useful for unclear requests):**
- **CLARITY:** Do I understand what's being asked?
  - Useful in: One-shot CLI requests, unclear prompts, autonomous work
  - Low CLARITY (<0.5) → Ask user for clarification before proceeding
  - Example: "make it better" = CLARITY 0.1 → clarify first!

### Command Cheat Sheet
```bash
# Onboarding
empirica onboard

# Basic workflow
empirica preflight "task"  # Interactive - prompts for self-assessment
empirica postflight <session> --summary "done"

# MCP server managed by IDE automatically
# No CLI commands needed - configure in IDE settings

# Session management
empirica sessions-list
empirica sessions-show <id>

# Help
empirica --help
empirica <command> --help
```

### Import Cheat Sheet
```python
# Core assessment
from empirica.core.canonical import CanonicalEpistemicAssessor

# Session management
from empirica.data.session_database import SessionDatabase

# Session creation (bootstrap classes DEPRECATED)
# ❌ DEPRECATED - Bootstrap classes removed
# from empirica.bootstraps.optimal_metacognitive_bootstrap import OptimalMetacognitiveBootstrap
# from empirica.bootstraps.extended_metacognitive_bootstrap import ExtendedMetacognitiveBootstrap

# ✅ Use session-create or SessionDatabase
from empirica.data.session_database import SessionDatabase
```

---

## 📚 Complete Documentation Map

### Getting Started (Start Here!)
- **[`docs/01_a_AI_AGENT_START.md`](../01_a_AI_AGENT_START.md)** - AI agent quick start
- **[`docs/00_START_HERE.md`](../00_START_HERE.md)** - Complete system overview
- **[`docs/02_INSTALLATION.md`](../02_INSTALLATION.md)** - Setup guide
- **[`docs/ONBOARDING_GUIDE.md`](../ONBOARDING_GUIDE.md)** - Complete learning path
- **[`docs/guides/TRY_EMPIRICA_NOW.md`](../guides/TRY_EMPIRICA_NOW.md)** - Hands-on demo

### Interface Guides
- **[`docs/03_CLI_QUICKSTART.md`](../03_CLI_QUICKSTART.md)** - All 39 CLI commands
- **[`docs/04_MCP_QUICKSTART.md`](../04_MCP_QUICKSTART.md)** - MCP integration (21 tools)
- **[`docs/guides/examples/mcp_configs/`](../guides/examples/mcp_configs/)** - MCP configurations
- **[`docs/production/13_PYTHON_API.md`](../production/13_PYTHON_API.md)** - Python API reference

### Core Concepts & Architecture
- **[`docs/05_ARCHITECTURE.md`](../05_ARCHITECTURE.md)** - System overview
- **[`docs/architecture/EMPIRICA_SYSTEM_OVERVIEW.md`](../architecture/EMPIRICA_SYSTEM_OVERVIEW.md)** - Detailed architecture
- **[`docs/production/05_EPISTEMIC_VECTORS.md`](../production/05_EPISTEMIC_VECTORS.md)** - Complete vector reference
- **[`docs/production/06_CASCADE_FLOW.md`](../production/06_CASCADE_FLOW.md)** - CASCADE phase breakdown
- **[`docs/production/ENHANCED_CASCADE_WORKFLOW_SPEC.md`](../production/ENHANCED_CASCADE_WORKFLOW_SPEC.md)** - Advanced CASCADE patterns

### Workflows & Patterns
- **[`docs/production/02_PREFLIGHT_POSTFLIGHT.md`](../production/02_PREFLIGHT_POSTFLIGHT.md)** - Basic workflow
- **[`docs/production/03_CASCADE_DECISION.md`](../production/03_CASCADE_DECISION.md)** - Decision-making
- **[`docs/production/07_INVESTIGATION_STRATEGIES.md`](../production/07_INVESTIGATION_STRATEGIES.md)** - Investigation patterns
- **[`docs/production/08_CALIBRATION_TRACKING.md`](../production/08_CALIBRATION_TRACKING.md)** - Calibration validation

### Advanced Topics
- **[`docs/production/14_CUSTOM_PLUGINS.md`](../production/14_CUSTOM_PLUGINS.md)** - Extend Empirica
- **[`docs/production/16_TUNING_THRESHOLDS.md`](../production/16_TUNING_THRESHOLDS.md)** - Calibration tuning
- **[`docs/research/RECURSIVE_EPISTEMIC_REFINEMENT.md`](../research/RECURSIVE_EPISTEMIC_REFINEMENT.md)** - Advanced patterns
- **[`empirica/cognitive_benchmarking/erb/`](../../cognitive_benchmarking/erb/)** - Epistemic benchmarking

### Troubleshooting & Help
- **[`docs/06_TROUBLESHOOTING.md`](../06_TROUBLESHOOTING.md)** - Common issues & solutions

### All Production Docs (21 Guides)
**[`docs/production/README.md`](../production/README.md)** - Index of all 21 comprehensive production guides

---

## Summary for AI Agents

**What Empirica does for you:**
1. Makes your implicit epistemic reasoning explicit
2. Validates if you know what you think you know
3. Tracks genuine learning over time
4. Prevents overconfidence through calibration
5. Provides epistemic trail for transparency

**How to use it:**
1. Run `empirica onboard` to learn (5 min)
2. Use `empirica preflight` before tasks
3. Use `empirica postflight` after completion
4. Review calibration to improve metacognitive accuracy

**Core principle:**
NO HEURISTICS. Genuine self-assessment only.

**When you're uncertain, say so.** That's genuine metacognition.

---

## Next Steps

<CardGroup cols={2}>
  <Card title="Try Empirica Now" icon="rocket" href="docs/guides/TRY_EMPIRICA_NOW.md">
    5-minute hands-on demo
  </Card>

  <Card title="Onboarding Guide" icon="graduation-cap" href="docs/ONBOARDING_GUIDE.md">
    Complete learning path
  </Card>

  <Card title="Production Docs" icon="book" href="docs/production/README.md">
    Complete reference (21 guides)
  </Card>

  <Card title="MCP Integration" icon="plug" href="docs/guides/examples/mcp_configs/">
    IDE integration setup
  </Card>
</CardGroup>

**Get started:** `empirica onboard --ai-id claude`
