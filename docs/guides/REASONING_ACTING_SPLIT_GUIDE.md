# Reasoning-Acting Split Pattern Guide

**Guide Type**: Advanced Workflow Pattern
**Status**: Production-Ready
**Use Case**: Leverage specialized AI strengths for complex tasks

---

## Table of Contents

1. [Introduction](#introduction)
2. [The Pattern](#the-pattern)
3. [Why This Works](#why-this-works)
4. [Basic Implementation](#basic-implementation)
5. [Advanced Patterns](#advanced-patterns)
6. [Modality Switcher Integration](#modality-switcher-integration)
7. [Use Cases](#use-cases)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Introduction

### The Problem

Different AI models have different strengths:
- **Claude/GPT-4**: Deep reasoning, strategic planning, complex analysis
- **Minimax/Qwen**: Fast execution, tool usage, code generation
- **Gemini**: Multimodal analysis, report generation
- **Qodo**: Code review, test generation

Using a single AI for both reasoning AND acting:
- ❌ Expensive (premium AI for simple execution)
- ❌ Inefficient (reasoning AI slower at execution)
- ❌ Less specialized (generalist vs specialist)

### The Solution

**Split the workflow**:
```
Reasoning AI → PREFLIGHT + INVESTIGATE + CHECK → Creates plan
                            ↓
                        [HANDOFF]
                            ↓
Acting AI → Loads plan → ACT + POSTFLIGHT → Executes & reports
```

Empirica's architecture makes this handoff **transparent, auditable, and validated**.

---

## The Pattern

### Core Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: REASONING (Claude, GPT-4, Gemini)                │
│                                                             │
│  PREFLIGHT                                                  │
│  ├─ Assess epistemic state                                 │
│  ├─ Identify gaps in knowledge                             │
│  └─ Log: overall_confidence, uncertainty                   │
│                                                             │
│  THINK                                                      │
│  ├─ Analyze task complexity                                │
│  ├─ Identify investigation needs                           │
│  └─ Plan approach                                          │
│                                                             │
│  INVESTIGATE (1-N rounds)                                   │
│  ├─ Research domain knowledge                              │
│  ├─ Analyze codebase/context                               │
│  ├─ Validate assumptions                                   │
│  └─ Log findings after each round                          │
│                                                             │
│  CHECK                                                      │
│  ├─ Final readiness assessment                             │
│  ├─ Validate confidence to proceed                         │
│  └─ Decision: proceed/investigate_more/clarify             │
│                                                             │
│  ACT (Planning)                                            │
│  ├─ Create detailed execution plan                         │
│  ├─ Document reasoning & rationale                         │
│  ├─ Identify risks & mitigation                            │
│  └─ Log to database + reflex logs                          │
│                                                             │
│  Result: Comprehensive plan with full context              │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    DATABASE HANDOFF
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: ACTING (Minimax, Qwen, Aider)                    │
│                                                             │
│  LOAD CONTEXT                                               │
│  ├─ Read reasoner's session from database                  │
│  ├─ Review full epistemic journey                          │
│  ├─ Understand confidence & uncertainty                    │
│  └─ Load detailed execution plan                           │
│                                                             │
│  ACT (Execution)                                           │
│  ├─ Execute plan step-by-step                              │
│  ├─ Use tools as specified                                 │
│  ├─ Handle errors with context                             │
│  └─ Log progress                                           │
│                                                             │
│  POSTFLIGHT                                                 │
│  ├─ Report what was accomplished                           │
│  ├─ Note deviations from plan                              │
│  ├─ Update epistemic state                                 │
│  └─ Calculate calibration delta                            │
│                                                             │
│  Result: Task completed + validation of reasoning          │
└─────────────────────────────────────────────────────────────┘
```

### What Makes This Possible

**Empirica's Three Foundations**:

1. **Database Logging** (`.empirica/sessions/sessions.db`)
   - Every phase logged with full context
   - Complete epistemic state preserved
   - Investigation findings stored
   - Action plans with rationale

2. **Reflex Logs** (`.empirica_reflex_logs/`)
   - Immutable audit trail (JSON)
   - Temporal separation (no self-reference)
   - Complete transparency
   - Human/AI readable

3. **No Heuristics**
   - Genuine epistemic assessment
   - Real confidence levels
   - Actual uncertainty measures
   - Honest reasoning (not confabulated)

---

## Why This Works

### 1. Complete Context Handoff

The acting AI receives:

```json
{
  "session_id": "abc123",
  "reasoner_ai": "claude",

  "preflight_assessment": {
    "know": {"score": 0.75, "rationale": "Understand OAuth 2.1 patterns"},
    "do": {"score": 0.60, "rationale": "Need to see current implementation"},
    "context": {"score": 0.55, "rationale": "Don't know existing auth flow"},
    "overall_confidence": 0.65,
    "uncertainty": 0.40
  },

  "investigation_rounds": [
    {
      "round": 1,
      "tools_used": ["read_file", "semantic_search"],
      "findings": "Current auth uses JWT, no refresh mechanism",
      "confidence_after": 0.72
    },
    {
      "round": 2,
      "tools_used": ["web_search", "documentation"],
      "findings": "OAuth 2.1 requires PKCE for public clients",
      "confidence_after": 0.80
    }
  ],

  "check_assessment": {
    "confidence_to_proceed": 0.85,
    "decision": "proceed",
    "remaining_concerns": "Database migration risk (medium)"
  },

  "action_plan": {
    "steps": [
      "1. Replace JWT with OAuth 2.1 authorization code flow",
      "2. Add PKCE support (tokens.py:20-50)",
      "3. Implement token refresh (auth.py:120-150)",
      "4. Add security validations"
    ],
    "files_to_modify": ["auth.py", "tokens.py", "middleware.py"],
    "tests_required": ["test_oauth_flow.py", "test_token_refresh.py"],
    "risks": [
      {"risk": "Database migration", "severity": "medium", "mitigation": "Test on staging first"}
    ],
    "estimated_complexity": "high",
    "confidence": 0.85
  }
}
```

**Actor sees EVERYTHING** reasoner thought about.

### 2. Specialized Strengths

| AI Type | Strength | Cost | Speed | Use For |
|---------|----------|------|-------|---------|
| Claude/GPT-4 | Deep reasoning, strategic planning | High | Slow | REASONING |
| Minimax | Fast execution, autonomous agents | Low | Fast | ACTING |
| Qwen | Code generation, technical tasks | Low | Fast | ACTING |
| Gemini | Multimodal, presentation | Med | Med | REPORTING |
| Qodo | Code review, test generation | Low | Fast | VALIDATION |

### 3. Cost Optimization

**Example: OAuth Refactor Task**

**Single AI (Claude only)**:
```
PREFLIGHT: 5 min × $0.015/min = $0.075
INVESTIGATE: 20 min × $0.015/min = $0.30
CHECK: 3 min × $0.015/min = $0.045
ACT: 30 min × $0.015/min = $0.45
POSTFLIGHT: 2 min × $0.015/min = $0.03
────────────────────────────────────
Total: 60 min, $0.90
```

**Split AI (Claude + Minimax)**:
```
Claude (REASONING):
  PREFLIGHT: 5 min × $0.015/min = $0.075
  INVESTIGATE: 20 min × $0.015/min = $0.30
  CHECK: 3 min × $0.015/min = $0.045
  Plan creation: 2 min × $0.015/min = $0.03
  Subtotal: 30 min, $0.45

Minimax (ACTING):
  Load context: 1 min × $0.003/min = $0.003
  Execute plan: 15 min × $0.003/min = $0.045
  POSTFLIGHT: 2 min × $0.003/min = $0.006
  Subtotal: 18 min, $0.054
────────────────────────────────────
Total: 48 min, $0.504

Savings: $0.396 (44% cheaper)
Time saved: 12 min (20% faster)
```

### 4. Safety Through Separation

**Reasoning Phase** (High Scrutiny):
- Multiple investigation rounds
- Uncertainty tracking
- Bayesian belief validation (optional)
- Sentinel monitoring (future)
- Human review possible before acting

**Acting Phase** (Bounded Execution):
- Clear plan to follow
- Observable actions
- Rollback capability
- Progress tracking
- Deviation detection

### 5. Calibration Validates Quality

After execution, verify reasoning quality:

```python
calibration = get_calibration_report(session_id)

# Example results:
{
  'reasoner_confidence': 0.85,  # Claude thought 85% ready
  'actual_difficulty': 0.82,    # Task was 82% as expected
  'delta': -0.03,               # Claude slightly overconfident (good to know!)
  'actor_confidence': 0.88,     # Minimax finished with high confidence
  'quality': 'well_calibrated'  # Reasoning was accurate
}
```

If deltas are large:
- Reasoner needs calibration adjustment
- Task was harder/easier than assessed
- Handoff process needs improvement

---

## Basic Implementation

### Step 1: Setup

```python
from empirica.data.session_database import SessionDatabase
from empirica.data.session_json_handler import SessionJSONHandler

# Initialize
db = SessionDatabase()
handler = SessionJSONHandler()
```

### Step 2: Reasoning Phase (Claude)

```python
# Bootstrap reasoner session
reasoner_session = db.create_session(
    ai_id="claude_reasoner",
    bootstrap_level=2,
    components_loaded=30
)

# PREFLIGHT - Assess task
# (In practice, Claude uses MCP tool: execute_preflight)
"""
Task: "Refactor authentication module to use OAuth 2.1"

Claude's self-assessment:
- KNOW: 0.75 (understand OAuth patterns)
- DO: 0.60 (need to see current code)
- CONTEXT: 0.55 (don't know current implementation)
- Overall confidence: 0.65
- Decision: INVESTIGATE
"""

# INVESTIGATE - Research (1-N rounds)
# Round 1: Read current auth.py
investigation_1 = db.log_investigation_round(
    session_id=reasoner_session,
    cascade_id=cascade_id,
    round_number=1,
    tools_mentioned="read_file, semantic_search",
    findings="Current auth uses JWT without refresh, tokens in Redis",
    confidence_before=0.65,
    confidence_after=0.72,
    summary="Understood current implementation"
)

# Round 2: Research OAuth 2.1 requirements
investigation_2 = db.log_investigation_round(
    session_id=reasoner_session,
    cascade_id=cascade_id,
    round_number=2,
    tools_mentioned="web_search, documentation_read",
    findings="OAuth 2.1 requires PKCE for public clients, state parameter for CSRF",
    confidence_before=0.72,
    confidence_after=0.80,
    summary="Validated OAuth 2.1 requirements"
)

# Round 3: Plan migration strategy
investigation_3 = db.log_investigation_round(
    session_id=reasoner_session,
    cascade_id=cascade_id,
    round_number=3,
    tools_mentioned="architecture_review",
    findings="Need database migration for refresh tokens, can use feature flag for rollout",
    confidence_before=0.80,
    confidence_after=0.85,
    summary="Migration strategy defined"
)

# CHECK - Validate readiness
# (Claude uses MCP tool: execute_check)
"""
CHECK assessment:
- Confidence to proceed: 0.85
- Decision: PROCEED
- Reasoning: "Understand current system, know OAuth 2.1 requirements,
              have migration strategy. Medium risk but mitigated."
"""

# ACT - Create detailed plan
action_plan = """
EXECUTION PLAN - OAuth 2.1 Migration
Generated by: Claude (Reasoner)
Confidence: 0.85 | Uncertainty: 0.20

═══════════════════════════════════════════════════════════════

OVERVIEW:
Replace current JWT-based authentication with OAuth 2.1 authorization
code flow with PKCE support.

CURRENT STATE (from investigation):
- JWT tokens stored in Redis (7-day expiry)
- No refresh mechanism (users re-authenticate)
- auth.py handles login/logout (lines 45-120)
- tokens.py manages JWT creation (lines 20-60)
- middleware.py validates tokens (lines 10-40)

TARGET STATE:
- OAuth 2.1 authorization code flow
- PKCE for public clients
- Refresh token support (30-day rotation)
- State parameter for CSRF protection
- Backward compatibility via feature flag

═══════════════════════════════════════════════════════════════

IMPLEMENTATION STEPS:

1. DATABASE MIGRATION (Priority: HIGH)
   File: migrations/0023_oauth_tokens.py (NEW)
   - Add oauth_refresh_tokens table
   - Add oauth_authorization_codes table
   - Add columns: code_challenge, code_verifier, state

   Risk: Medium (database change)
   Mitigation: Test on staging, have rollback script

2. PKCE IMPLEMENTATION (Priority: HIGH)
   File: tokens.py (lines 20-60 → REPLACE)
   - Add generate_code_challenge(verifier)
   - Add validate_code_challenge(challenge, verifier)
   - Update token creation to include PKCE

   Tests: test_pkce_generation.py, test_pkce_validation.py

3. AUTHORIZATION CODE FLOW (Priority: HIGH)
   File: auth.py (lines 45-120 → MAJOR REFACTOR)
   - Add /authorize endpoint (OAuth 2.1 spec)
   - Add /token endpoint (with PKCE validation)
   - Add state parameter handling
   - Keep existing /login as fallback (feature flag)

   Tests: test_authorization_flow.py

4. REFRESH TOKEN MECHANISM (Priority: HIGH)
   File: auth.py (lines 120-150 → NEW)
   - Add /refresh endpoint
   - Implement token rotation (security best practice)
   - Add refresh token expiry (30 days)

   Tests: test_token_refresh.py

5. TOKEN VALIDATION UPDATE (Priority: MEDIUM)
   File: middleware.py (lines 10-40 → UPDATE)
   - Support both JWT (legacy) and OAuth tokens
   - Add feature flag check: oauth2_enabled
   - Maintain backward compatibility

   Tests: test_middleware_oauth.py

6. FEATURE FLAG ROLLOUT (Priority: MEDIUM)
   File: config/feature_flags.py (NEW)
   - Add oauth2_enabled flag (default: False)
   - Add rollout percentage support (1% → 10% → 100%)

   Plan: Test 1% for 24h, then 10% for 48h, then 100%

7. SECURITY VALIDATIONS (Priority: HIGH)
   File: auth.py (various locations)
   - Add state parameter validation (CSRF protection)
   - Add nonce support (replay protection)
   - Rate limiting on token endpoints

   Tests: test_security_validations.py

═══════════════════════════════════════════════════════════════

FILES TO MODIFY:
- auth.py: ~150 lines (major refactor)
- tokens.py: ~80 lines (PKCE implementation)
- middleware.py: ~40 lines (dual token support)
- config/feature_flags.py: ~30 lines (NEW)
- migrations/0023_oauth_tokens.py: ~60 lines (NEW)

TESTS REQUIRED (ALL NEW):
- test_pkce_generation.py
- test_pkce_validation.py
- test_authorization_flow.py
- test_token_refresh.py
- test_middleware_oauth.py
- test_security_validations.py

Total test coverage target: 95%+

═══════════════════════════════════════════════════════════════

RISKS & MITIGATION:

1. DATABASE MIGRATION (Risk: Medium)
   - Impact: If migration fails, auth breaks
   - Mitigation: Test on staging, have rollback script ready
   - Rollback: DROP new tables, revert code

2. BREAKING EXISTING CLIENTS (Risk: Medium)
   - Impact: Old JWT tokens won't work immediately
   - Mitigation: Feature flag + dual support for 30 days
   - Monitor: Track failed auth attempts

3. SECURITY REGRESSION (Risk: High)
   - Impact: Auth vulnerabilities introduced
   - Mitigation: Security review, penetration testing
   - Validation: Run OWASP security tests

4. PERFORMANCE DEGRADATION (Risk: Low)
   - Impact: Token validation slower
   - Mitigation: Redis caching for refresh tokens
   - Monitor: Track auth endpoint latency

═══════════════════════════════════════════════════════════════

ESTIMATED COMPLEXITY:
- Implementation: 2-3 days (6-8 hours coding)
- Testing: 1-2 days (4-6 hours test writing)
- Staging validation: 1 day
- Production rollout: 3 days (phased)

Total: 7-9 days for complete rollout

CONFIDENCE: 0.85 (High)
UNCERTAINTY: 0.20 (Medium - database migration risk)

RECOMMENDATION: PROCEED with phased rollout plan
"""

# Log the plan
db.log_act_phase(
    session_id=reasoner_session,
    cascade_id=cascade_id,
    action_type="proceed",
    action_rationale=action_plan,
    final_confidence=0.85
)

# Export session for actor
export_path = handler.export_session(db, reasoner_session)
print(f"Reasoning complete. Session exported to: {export_path}")
```

### Step 3: Acting Phase (Minimax)

```python
# Bootstrap actor session
actor_session = db.create_session(
    ai_id="minimax_actor",
    bootstrap_level=1,  # Simpler bootstrap for execution
    components_loaded=10
)

# Load Claude's reasoning
claude_context = handler.load_session_context(reasoner_session)

# Get the execution plan
act_data = db.conn.execute("""
    SELECT action_rationale, final_confidence
    FROM act_logs
    WHERE session_id = ?
""", (reasoner_session,)).fetchone()

execution_plan = act_data[0]
reasoner_confidence = act_data[1]

print(f"Loaded plan from Claude (confidence: {reasoner_confidence})")
print(f"Plan length: {len(execution_plan)} chars")

# Execute the plan
# (Minimax would actually implement the changes here)
"""
Minimax execution:
1. Create database migration
2. Implement PKCE in tokens.py
3. Refactor auth.py authorization flow
4. Add refresh token mechanism
5. Update middleware.py
6. Add feature flags
7. Write all tests
8. Run test suite
"""

# Simulated execution results
execution_results = {
    'files_modified': ['auth.py', 'tokens.py', 'middleware.py', 'config/feature_flags.py'],
    'files_created': ['migrations/0023_oauth_tokens.py'],
    'tests_created': [
        'test_pkce_generation.py',
        'test_pkce_validation.py',
        'test_authorization_flow.py',
        'test_token_refresh.py',
        'test_middleware_oauth.py',
        'test_security_validations.py'
    ],
    'tests_passing': '42/42',
    'test_coverage': '96.5%',
    'deviations_from_plan': [
        'Added additional validation in middleware.py (security improvement)',
        'Implemented token rotation slightly differently (more secure)'
    ],
    'issues_encountered': [],
    'completion_time': '7.5 hours'
}

# POSTFLIGHT - Report back
db.log_postflight_assessment(
    session_id=actor_session,
    cascade_id=None,
    task_summary=f"""
OAuth 2.1 migration completed successfully per Claude's plan.

ACCOMPLISHMENTS:
- ✅ Database migration created and tested
- ✅ PKCE implementation (tokens.py)
- ✅ Authorization code flow (auth.py)
- ✅ Refresh token mechanism (auth.py)
- ✅ Dual token support (middleware.py)
- ✅ Feature flag system (config/feature_flags.py)
- ✅ All security validations implemented
- ✅ 42 tests created, all passing (96.5% coverage)

DEVIATIONS:
- Added extra security validation in middleware (improvement)
- Token rotation implementation slightly different (more secure)

CLAUDE'S PLAN ACCURACY:
- Estimated: 2-3 days implementation
- Actual: 7.5 hours (faster than expected!)
- Estimated complexity: High
- Actual complexity: Medium-High (Claude's research made it easier)

All risks successfully mitigated. Ready for staging deployment.
    """,
    vectors={
        'know': 0.92,       # Deep understanding gained through implementation
        'do': 0.95,         # Successfully executed complex refactor
        'context': 0.90,    # Complete codebase knowledge
        'clarity': 0.90,    # Plan was very clear
        'coherence': 0.95,  # Everything fit together logically
        'completion': 1.0,  # Task fully complete
        'uncertainty': 0.10 # Very low uncertainty after completion
    },
    postflight_confidence=0.92,
    calibration_accuracy="well_calibrated",
    learning_notes="""
Claude's investigation was thorough and accurate. The execution plan
was detailed enough to follow precisely. The confidence of 0.85 was
appropriate - task was complex but manageable with the provided plan.

Key insight: Claude's risk assessment (database migration) was spot on.
Having the mitigation strategy prepared made execution smooth.
    """
)

print("Execution complete!")

# Calculate calibration
calibration = {
    'reasoner_confidence': 0.85,
    'actor_confidence': 0.92,
    'delta': +0.07,  # Actor found it slightly easier than Claude estimated
    'quality': 'well_calibrated',
    'note': 'Claude slightly underestimated (safe bias)'
}

print(f"Calibration: {calibration}")

db.close()
```

### Step 4: Validation

```python
# Verify the handoff worked
print("\n" + "="*60)
print("REASONING → ACTING SPLIT: SUCCESS")
print("="*60)

print(f"\nReasoner Session: {reasoner_session[:12]}")
print(f"Actor Session: {actor_session[:12]}")

print(f"\nReasoning Phase:")
print(f"  - PREFLIGHT confidence: 0.65")
print(f"  - Investigation rounds: 3")
print(f"  - CHECK confidence: 0.85")
print(f"  - Plan created: {len(execution_plan)} chars")

print(f"\nActing Phase:")
print(f"  - Plan loaded successfully")
print(f"  - Files modified: {len(execution_results['files_modified'])}")
print(f"  - Tests created: {len(execution_results['tests_created'])}")
print(f"  - Tests passing: {execution_results['tests_passing']}")
print(f"  - Coverage: {execution_results['test_coverage']}")

print(f"\nCalibration:")
print(f"  - Reasoner confidence: {calibration['reasoner_confidence']}")
print(f"  - Actor confidence: {calibration['actor_confidence']}")
print(f"  - Delta: {calibration['delta']:+.2f}")
print(f"  - Quality: {calibration['quality']}")

print(f"\nCost Savings:")
print(f"  - Single AI: $0.90")
print(f"  - Split AI: $0.504")
print(f"  - Savings: $0.396 (44%)")

print(f"\nTime Savings:")
print(f"  - Estimated: 60 min")
print(f"  - Actual: 48 min")
print(f"  - Saved: 12 min (20%)")
```

---

## Advanced Patterns

### Pattern 1: Goal Orchestrator Handoff

For complex multi-step tasks, use goal orchestrator:

```python
# Step 1: Reasoner generates structured goals
goals = db.query_tool("generate_goals", {
    'session_id': reasoner_session,
    'conversation_context': """
    Comprehensive security audit of authentication system:
    1. Review OAuth 2.1 implementation
    2. Test edge cases
    3. Penetration testing
    4. Documentation update
    """
})

# Returns:
{
  "goals": [
    {
      "goal_id": "audit_oauth",
      "description": "Audit OAuth 2.1 implementation for security issues",
      "sub_goals": ["Check PKCE", "Verify state validation", "Review token storage"],
      "dependencies": [],
      "priority": "critical",
      "estimated_time": "4-6 hours"
    },
    {
      "goal_id": "test_edge_cases",
      "description": "Test authentication edge cases",
      "dependencies": ["audit_oauth"],
      "priority": "high",
      "estimated_time": "2-3 hours"
    },
    {
      "goal_id": "pen_testing",
      "description": "Penetration testing",
      "dependencies": ["audit_oauth", "test_edge_cases"],
      "priority": "high",
      "estimated_time": "3-4 hours"
    },
    {
      "goal_id": "update_docs",
      "description": "Update security documentation",
      "dependencies": ["pen_testing"],
      "priority": "medium",
      "estimated_time": "1-2 hours"
    }
  ]
}

# Step 2: Reasoner investigates EACH goal
for goal in goals['goals']:
    # PREFLIGHT for this goal
    # INVESTIGATE specific to this goal
    # CHECK readiness for this goal
    # Create goal-specific plan
    pass

# Step 3: Actor executes goals in dependency order
for goal in sorted_by_dependencies(goals['goals']):
    # Load reasoner's context for this goal
    goal_context = load_goal_context(goal['goal_id'])

    # Execute with full understanding
    execute_goal(goal, goal_context)

    # Mark complete
    mark_goal_complete(goal['goal_id'])
```

### Pattern 2: Parallel Execution

One reasoner → Multiple actors (parallel):

```python
# Reasoner breaks down task
subtasks = claude_plan_parallel_work(main_task)

# Returns:
subtasks = [
    {'id': 1, 'desc': 'Refactor auth.py', 'independent': True},
    {'id': 2, 'desc': 'Refactor tokens.py', 'independent': True},
    {'id': 3, 'desc': 'Write tests', 'depends_on': [1, 2]},
]

# Launch multiple actors
import asyncio

async def execute_subtask(subtask, reasoner_session):
    actor = spawn_actor(f"actor_{subtask['id']}")
    result = await actor.execute(
        load_plan_from(reasoner_session, subtask['id'])
    )
    return result

# Execute independent tasks in parallel
independent = [t for t in subtasks if t['independent']]
results = await asyncio.gather(*[
    execute_subtask(task, reasoner_session)
    for task in independent
])

# Execute dependent tasks after
dependent = [t for t in subtasks if not t['independent']]
for task in dependent:
    await execute_subtask(task, reasoner_session)
```

### Pattern 3: Cascading Handoff

Reasoner → Reasoner → Actor chain:

```python
# Strategic Reasoner (Claude) - High level
session_1 = strategic_reasoning(task="Build new feature")
# Output: High-level architecture, approach, risks

# Tactical Reasoner (GPT-4) - Detailed planning
session_2 = tactical_reasoning(
    parent_session=session_1,
    task="Detailed implementation plan"
)
# Output: Step-by-step plan, file-by-file changes

# Actor (Minimax) - Execution
session_3 = execute_plan(
    parent_session=session_2,
    plan=load_tactical_plan(session_2)
)
# Output: Implemented feature

# Evaluator (Claude) - Validation
session_4 = evaluate_result(
    original_session=session_1,
    execution_session=session_3
)
# Output: Quality check, calibration, lessons learned
```

### Pattern 4: Collaborative Real-Time

Reasoner and actor working together:

```python
while not task_complete:
    # Claude assesses current state
    assessment = claude.assess_current_state()

    if assessment.confidence < 0.70:
        # Claude investigates
        claude.investigate()
        claude.update_plan()

    if ready_to_act:
        # Hand off to Minimax
        action_plan = claude.create_action_plan()
        result = minimax.execute(action_plan)

        # Claude evaluates result
        evaluation = claude.evaluate(result)

        # Update state
        current_state = evaluation

# Continuous feedback loop:
# THINK (Claude) → ACT (Minimax) → EVALUATE (Claude) → repeat
```

---

## Modality Switcher Integration

**Status**: 🧪 **Experimental**

Modality Switcher enables dynamic AI selection based on epistemic needs.

### How It Works

```python
from empirica.plugins.modality_switcher import ModalitySwitcher, Strategy

switcher = ModalitySwitcher()

# Routing based on epistemic state
result = switcher.route(
    query="Refactor authentication to OAuth 2.1",
    strategy=Strategy.EPISTEMIC,  # Route based on epistemic needs
    context={
        'phase': 'reasoning',  # or 'acting'
        'complexity': 'high',
        'domain': 'security'
    }
)

# For REASONING phase:
# - Routes to Claude (deep analysis)
# - Routes to GPT-4 (strategic planning)

# For ACTING phase:
# - Routes to Minimax (execution)
# - Routes to Qwen (code generation)
```

### Reasoning-Acting Split with Modality Switcher

```python
# Step 1: Switcher selects reasoner based on task
reasoner = switcher.select_for_reasoning(
    task="Security audit",
    required_capabilities=['deep_analysis', 'security_expertise']
)
# Returns: "claude" or "gpt4"

# Step 2: Reasoner does PREFLIGHT → INVESTIGATE → CHECK
reasoner_session = run_reasoning_phase(
    ai=reasoner,
    task=task
)

# Step 3: Switcher selects actor based on execution needs
actor = switcher.select_for_acting(
    plan=load_plan(reasoner_session),
    required_capabilities=['fast_execution', 'tool_usage']
)
# Returns: "minimax" or "qwen"

# Step 4: Actor executes
actor_session = run_acting_phase(
    ai=actor,
    plan=load_plan(reasoner_session)
)
```

### Automatic Routing Example

```python
from empirica.plugins.modality_switcher import AutoRouter

router = AutoRouter()

# Router automatically splits reasoning/acting
result = router.execute_split_workflow(
    task="Refactor auth to OAuth 2.1",
    reasoning_ai="auto",  # Router selects best reasoner
    acting_ai="auto",     # Router selects best actor
    strategy="cost_optimized"  # or "speed_optimized", "quality_optimized"
)

# Router did:
# 1. Selected Claude for reasoning (deep analysis needed)
# 2. Claude: PREFLIGHT → INVESTIGATE → CHECK
# 3. Selected Minimax for acting (fast execution)
# 4. Minimax: ACT → POSTFLIGHT
# 5. Returned combined results

print(f"Reasoner: {result['reasoner_ai']}")
print(f"Actor: {result['actor_ai']}")
print(f"Total cost: ${result['total_cost']}")
print(f"Total time: {result['total_time']}min")
print(f"Calibration: {result['calibration_delta']}")
```

### Future: Adaptive Routing

When fully integrated, modality switcher will:

```python
# Learn from calibration data
router.learn_from_history(
    session_history=get_recent_sessions(limit=100)
)

# Adaptive routing based on past performance
# "For security tasks, Claude → Minimax split has 0.92 calibration"
# "For code refactoring, GPT-4 → Qwen split has 0.88 calibration"

# Router automatically improves over time
best_split = router.recommend_split(
    task="Security-related refactoring",
    optimize_for="calibration_quality"
)

# Returns:
{
    'reasoner': 'claude',
    'actor': 'minimax',
    'confidence': 0.92,
    'reasoning': 'Historical data shows this split has best calibration for security tasks'
}
```

---

## Use Cases

### Use Case 1: Security Audit → Fix Implementation

**Scenario**: Audit authentication system and fix issues

**Split**:
```
Claude (Reasoner):
├─ PREFLIGHT: Assess security knowledge (0.75)
├─ INVESTIGATE: Research vulnerabilities, OWASP top 10
├─ INVESTIGATE: Analyze codebase for issues
├─ CHECK: Validate findings (0.85)
└─ Plan: Create fix implementation plan with priorities

Minimax (Actor):
├─ Load: Security findings and fix priorities
├─ ACT: Implement fixes in priority order
├─ ACT: Add security tests
└─ POSTFLIGHT: Report fixes applied (0.90)

Result: Comprehensive security audit + fixes
Calibration: 0.85 → 0.90 (well-calibrated)
```

### Use Case 2: Architecture Design → Code Generation

**Scenario**: Design microservices architecture and generate code

**Split**:
```
GPT-4 (Reasoner):
├─ PREFLIGHT: Understand requirements (0.70)
├─ INVESTIGATE: Research microservice patterns
├─ INVESTIGATE: Analyze trade-offs (monolith vs microservices)
├─ CHECK: Validate architecture (0.80)
└─ Plan: Detailed service design with APIs

Qwen (Actor):
├─ Load: Architecture design and API specs
├─ ACT: Generate service boilerplate
├─ ACT: Implement API endpoints
├─ ACT: Generate tests
└─ POSTFLIGHT: Report code generated (0.85)

Result: Well-architected microservices with code
Calibration: 0.80 → 0.85 (slight underestimate)
```

### Use Case 3: Data Analysis → Report Generation

**Scenario**: Analyze sales data and create executive report

**Split**:
```
Claude (Reasoner):
├─ PREFLIGHT: Assess data quality (0.65)
├─ INVESTIGATE: Analyze sales trends
├─ INVESTIGATE: Find patterns and anomalies
├─ INVESTIGATE: Statistical validation
├─ CHECK: Validate findings (0.85)
└─ Plan: Key insights and recommendations

Gemini (Actor):
├─ Load: Analysis findings and insights
├─ ACT: Generate executive summary
├─ ACT: Create visualizations
├─ ACT: Format as presentation
└─ POSTFLIGHT: Report delivered (0.88)

Result: Data-driven insights + polished report
Calibration: 0.85 → 0.88 (accurate assessment)
```

### Use Case 4: Code Review → Refactoring

**Scenario**: Review legacy code and refactor

**Split**:
```
Claude (Reasoner):
├─ PREFLIGHT: Assess code complexity (0.60)
├─ INVESTIGATE: Analyze code structure
├─ INVESTIGATE: Identify code smells
├─ INVESTIGATE: Research better patterns
├─ CHECK: Validate refactoring plan (0.75)
└─ Plan: Refactoring strategy with priorities

Qodo (Actor - Code specialist):
├─ Load: Refactoring plan and priorities
├─ ACT: Refactor high-priority issues
├─ ACT: Generate comprehensive tests
├─ ACT: Validate test coverage
└─ POSTFLIGHT: Report refactoring complete (0.80)

Result: Cleaner code + test suite
Calibration: 0.75 → 0.80 (good calibration)
```

---

## Best Practices

### For Reasoning Phase

#### 1. **Thorough Investigation**
```python
# Don't rush - investigate thoroughly
# Multiple rounds better than one shallow round

# GOOD:
investigation_rounds = [
    "Round 1: Read current implementation",
    "Round 2: Research best practices",
    "Round 3: Validate approach",
    "Round 4: Plan migration strategy"
]
# Result: High confidence (0.85), accurate plan

# BAD:
investigation_rounds = [
    "Round 1: Quick scan, good enough"
]
# Result: Low confidence (0.60), vague plan, actor struggles
```

#### 2. **Detailed Plans**
```python
# Actor needs specifics, not generalities

# GOOD:
plan = """
1. Modify auth.py lines 45-120
   - Replace authenticate() method
   - Add PKCE validation
   - Keep old method as authenticate_legacy()

2. Add to tokens.py after line 20:
   def generate_pkce_challenge(verifier: str) -> str:
       # Implementation details...

3. Test files to create:
   - test_pkce.py (test PKCE generation)
   - test_oauth_flow.py (end-to-end)
"""

# BAD:
plan = """
1. Update authentication
2. Add OAuth support
3. Write tests
"""
```

#### 3. **Risk Assessment**
```python
# Identify risks AND mitigation strategies

# GOOD:
risks = [
    {
        'risk': 'Database migration fails',
        'severity': 'high',
        'mitigation': 'Test on staging, have rollback script ready',
        'rollback_plan': 'DROP new tables, deploy previous version'
    }
]

# BAD:
risks = ['Database migration might have issues']
```

#### 4. **Honest Confidence**
```python
# Don't confabulate - assess genuinely

# GOOD:
assessment = {
    'know': 0.70,  # "I understand OAuth but haven't implemented it"
    'do': 0.60,    # "Theory strong, practice untested"
    'confidence': 0.65,  # "Need more investigation"
    'uncertainty': 0.40   # "Significant unknowns"
}

# BAD (Confabulation):
assessment = {
    'know': 0.95,  # "I'm an expert!" (but never implemented)
    'do': 0.90,    # "I can do anything!" (overconfident)
    'confidence': 0.90,
    'uncertainty': 0.10
}
# Result: Actor hits unexpected issues, poor calibration
```

### For Acting Phase

#### 1. **Review Context Thoroughly**
```python
# Don't just read the plan - understand the reasoning

# GOOD:
context = load_reasoner_context(session_id)

# Review:
# - Why this approach? (rationale)
# - What was investigated? (findings)
# - What risks identified? (awareness)
# - What's the confidence level? (calibration)

# Then execute with full understanding

# BAD:
plan = get_action_plan(session_id)
execute_blindly(plan)  # Missing context!
```

#### 2. **Follow Plan but Adapt**
```python
# Plan is guide, not rigid script

# GOOD:
for step in plan:
    try:
        execute_step(step)
    except UnexpectedIssue as e:
        # Document deviation
        log_deviation(
            step=step,
            issue=e,
            adaptation="Added extra validation based on error"
        )
        # Adapt intelligently
        execute_adapted_step(step, adaptation)

# BAD:
for step in plan:
    execute_step(step)  # Crashes on first unexpected issue
```

#### 3. **Report Accurately**
```python
# POSTFLIGHT should be honest about what happened

# GOOD:
postflight = {
    'completed': True,
    'deviations': [
        'Added extra security check (improvement)',
        'Database migration took 2x longer (unexpected)'
    ],
    'issues_encountered': [
        'Token validation edge case not in plan',
        'Had to refactor middleware.py more than expected'
    ],
    'actual_vs_estimated': 'Took 8h vs estimated 6h (33% longer)',
    'reasoner_plan_quality': 'Excellent - plan was 90% accurate'
}

# BAD:
postflight = {
    'completed': True,
    'deviations': [],  # Hiding truth
    'everything_was_perfect': True  # Confabulation
}
```

#### 4. **Calibration Feedback**
```python
# Help improve reasoner's calibration

# GOOD:
calibration_feedback = {
    'reasoner_confidence': 0.85,
    'actual_difficulty': 0.80,
    'feedback': """
    Claude's confidence was slightly high but very close.
    Investigation was thorough and plan was detailed.

    Areas where plan helped most:
    - Database migration strategy was perfect
    - Risk mitigation for token validation was spot-on

    Areas that could be better:
    - Didn't anticipate middleware complexity (minor)
    - Test file count estimate was low (not critical)

    Overall: Excellent reasoning quality
    """
}

# BAD:
calibration_feedback = "Everything was perfect" # Not helpful
```

### For Both Phases

#### 1. **Clear Session Linking**
```python
# Always link reasoner and actor sessions

db.create_session(
    ai_id="actor_ai",
    parent_session=reasoner_session,  # Link them
    session_notes=f"Executing plan from {reasoner_session[:8]}"
)
```

#### 2. **Rich Logging**
```python
# Log everything - transparency is key

# Every investigation round
db.log_investigation_round(...)

# Every decision
db.log_act_phase(...)

# Final results
db.log_postflight_assessment(...)

# Export for auditability
handler.export_session(db, session_id)
```

#### 3. **Use Reflex Logs**
```python
# Reflex logs are immutable audit trail

# Can prove:
# - What reasoner actually assessed
# - What actor actually did
# - No post-hoc modification
# - Complete transparency

# Check reflex logs:
reflex_logs = list_reflex_logs(session_id)
for log in reflex_logs:
    verify_integrity(log)  # Cryptographic hashing (future)
```

---

## Troubleshooting

### Issue 1: Actor Can't Find Context

**Symptoms**:
```python
# Actor can't load reasoner's session
context = handler.load_session_context(reasoner_session)
# Returns: None
```

**Causes**:
- Session not exported
- Wrong session ID
- Database path mismatch

**Fix**:
```python
# Verify session exists
session = db.get_session(reasoner_session)
if not session:
    print(f"Session {reasoner_session} not found!")

# Export explicitly
export_path = handler.export_session(db, reasoner_session)
print(f"Exported to: {export_path}")

# Load from export
context = handler.load_session_context(reasoner_session)
```

### Issue 2: Poor Calibration

**Symptoms**:
```python
calibration = {
    'reasoner_confidence': 0.85,
    'actual_difficulty': 0.60,  # Much easier than expected
    'delta': -0.25  # Poor calibration
}
```

**Causes**:
- Reasoner over-investigated (too cautious)
- Reasoner didn't trust their assessment
- Task was simpler than appeared

**Fix**:
```python
# Review reasoner's investigation
investigation_logs = db.get_investigation_logs(reasoner_session)

# Check for signs of over-investigation:
# - Too many rounds (5+ for simple task)
# - Confidence not improving (stuck at 0.70-0.75)
# - Investigating already-known things

# Feedback to reasoner:
feedback = """
You investigated thoroughly (good!) but may have been
overly cautious. Your initial assessment of 0.70 was
actually closer to reality (0.60 actual).

Trust your initial assessment more when:
- Task is familiar domain
- No novel requirements
- Clear implementation path

Continue thorough investigation when:
- Unfamiliar domain
- High-stakes/security-critical
- Many unknowns
"""
```

### Issue 3: Actor Deviates from Plan

**Symptoms**:
```python
# Actor reports major deviations
postflight = {
    'deviations': [
        'Completely rewrote approach',
        'Ignored migration strategy',
        'Different architecture than planned'
    ]
}
```

**Causes**:
- Plan was vague/incomplete
- Actor found better approach
- Actor didn't understand reasoning
- Plan was wrong

**Fix**:
```python
# Review if deviation was justified
if deviation_improved_outcome:
    # Good! Actor used intelligence
    feedback = "Plan provided direction, actor adapted well"

elif deviation_caused_issues:
    # Investigate why

    # Was plan vague?
    if plan_quality == 'vague':
        feedback_to_reasoner = "Provide more detailed plans"

    # Did actor miss context?
    elif actor_missed_reasoning:
        feedback_to_actor = "Review investigation findings, not just plan"

    # Was plan actually wrong?
    elif reasoner_made_error:
        feedback_to_reasoner = "Investigation missed key insight"
        # This is fine! Calibration catches this
```

### Issue 4: Handoff Takes Too Long

**Symptoms**:
```python
# Actor spends 10 minutes just loading context
```

**Causes**:
- Large session history
- Too many investigation rounds
- Inefficient context loading

**Fix**:
```python
# Use session summaries
summary = handler.create_compact_summary(db, reasoner_session)
# Much faster than loading full history

# Or use goal-specific context
goal_context = load_goal_context(
    session_id=reasoner_session,
    goal_id=current_goal
)
# Only loads relevant context

# Cache frequently accessed sessions
from functools import lru_cache

@lru_cache(maxsize=10)
def load_session_cached(session_id):
    return handler.load_session_context(session_id)
```

### Issue 5: Circular Handoffs

**Symptoms**:
```python
# Actor hands back to reasoner, who hands back to actor, repeat...
```

**Causes**:
- Unclear responsibility boundaries
- Plan incomplete
- Unexpected complexity

**Fix**:
```python
# Clear CONTRACT between reasoner and actor

CONTRACT = {
    'reasoner_responsibility': [
        'Assess task thoroughly',
        'Investigate unknowns',
        'Create COMPLETE executable plan',
        'Identify ALL risks'
    ],
    'actor_responsibility': [
        'Execute plan faithfully',
        'Adapt to minor issues',
        'Report deviations',
        'Complete task OR report blocker'
    ],
    'handoff_criteria': {
        'reasoner_must_provide': [
            'Confidence >= 0.75',
            'Plan with file-level detail',
            'Risk mitigation strategies',
            'Success criteria'
        ],
        'actor_must_do': [
            'Review full context',
            'Execute or report blocker',
            'Document deviations',
            'Provide calibration feedback'
        ]
    },
    'escalation': {
        'if_major_blocker': 'Actor reports, reasoner investigates more',
        'if_plan_incomplete': 'Actor requests clarification',
        'if_unexpected_complexity': 'Actor documents, reasoner assesses'
    }
}

# Prevent circular handoffs:
max_handoffs = 2  # Reasoner → Actor → (optional) Reasoner review
if handoff_count > max_handoffs:
    escalate_to_human()
```

---

## Summary

### Key Takeaways

1. **Reasoning-Acting split leverages specialized AI strengths**
   - Reasoners: Deep analysis, planning, risk assessment
   - Actors: Fast execution, tool usage, implementation

2. **Empirica enables transparent handoff**
   - Database logging preserves complete context
   - Reflex logs provide immutable audit trail
   - No heuristics = genuine epistemic state

3. **Calibration validates reasoning quality**
   - Delta shows if reasoner's confidence was accurate
   - Feedback loop improves future reasoning
   - Mathematical proof of effectiveness

4. **Cost and time savings significant**
   - 30-50% cost reduction typical
   - 20-40% time reduction possible
   - Better quality through specialization

5. **Pattern is production-ready**
   - Core Empirica features stable
   - Database schema complete
   - MCP tools functional

### Getting Started

```python
# 1. Bootstrap sessions
reasoner_session = bootstrap_session("claude_reasoner")
actor_session = bootstrap_session("minimax_actor")

# 2. Reasoning phase (Claude)
run_preflight_investigate_check(reasoner_session, task)

# 3. Acting phase (Minimax)
execute_from_plan(actor_session, reasoner_session)

# 4. Validate
verify_calibration(reasoner_session, actor_session)
```

### Next Steps

1. **Try it!** Use the basic implementation example
2. **Measure** calibration deltas to validate quality
3. **Iterate** based on calibration feedback
4. **Scale** to more complex workflows

### Future Enhancements

- **Modality Switcher** (experimental): Automatic AI selection
- **Sentinel Integration**: Cognitive governance for handoffs
- **Adaptive Routing**: Learn optimal splits from history
- **Multi-AI Chains**: Strategic → Tactical → Execution → Validation

---

## Additional Resources

- **API Reference**: [`docs/production/19_API_REFERENCE.md`](../production/19_API_REFERENCE.md)
- **Python API Guide**: [`docs/production/13_PYTHON_API.md`](../production/13_PYTHON_API.md)
- **MCP Quickstart**: [`docs/04_MCP_QUICKSTART.md`](../04_MCP_QUICKSTART.md)
- **Session Database**: [`docs/architecture/SESSION_DATABASE.md`](../architecture/SESSION_DATABASE.md)
- **Calibration**: [`docs/architecture/CALIBRATION.md`](../architecture/CALIBRATION.md)

---

**Questions?** Check the troubleshooting section or open an issue on GitHub.

**Ready to start?** Try the basic implementation example and see how reasoning-acting split improves your workflow!
