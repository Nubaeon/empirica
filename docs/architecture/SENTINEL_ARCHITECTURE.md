# Sentinel Architecture - The Gate

**Module:** `empirica.core.sentinel`

The Sentinel is the gate controller of Empirica's cognitive architecture. It governs the transition between noetic (investigation) and praxic (action) phases, enforces compliance, and tracks epistemic loops.

## Philosophy

The Sentinel doesn't think for the AI - it provides governance:
- **Gate control**: Determines proceed vs investigate based on vectors
- **Compliance**: Enforces domain-specific rules (HIPAA, SOX, etc.)
- **Loop tracking**: Monitors convergence across epistemic cycles
- **Dual defense**: NoeticFilter (cognition) + AxiologicGate (action)

---

## Core Architecture

```
                    ┌─────────────────────┐
                    │      Sentinel       │
                    │   (Orchestrator)    │
                    └─────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ DecisionLogic │   │ EpistemicLoop   │   │ DomainProfile   │
│ (Persona)     │   │ Tracker         │   │ (Compliance)    │
└───────────────┘   └─────────────────┘   └─────────────────┘
```

---

## Classes Reference

### Gate Actions & Enums

#### GateAction
Actions that compliance gates can take:
- `PROCEED` - Continue execution
- `INVESTIGATE` - Return to noetic phase
- `HALT_AND_AUDIT` - Stop and log for audit
- `REQUIRE_HUMAN` - Pause for human approval
- `ESCALATE` - Escalate to higher authority
- `LOG_AND_CONTINUE` - Log concern but proceed

#### LoopMode
Who decides loop count:
- `USER` - User specifies exact count
- `AI` - AI chooses based on task
- `SENTINEL` - Sentinel governs with convergence detection

#### MergeStrategy
Strategies for merging parallel agent results:
- `CONSENSUS` - All agents must agree
- `BEST_SCORE` - Take highest merge_score result
- `WEIGHTED` - Weight by merge_score
- `UNION` - Combine all findings
- `INTERSECTION` - Only common findings

#### GatePhase
Phase during which a gate operates:
- `NOETIC` - Cognition/investigation phase
- `PRAXIC` - Action/execution phase
- `CHECK` - During CHECK gate transition
- `ANY` - Applies to all phases

---

### Dual Defense Layers

#### NoeticFilter
Cognition-level defense layer. Operates during NOETIC phase to filter what investigation paths are allowed.

```python
filter = NoeticFilter(
    filter_id="block_exploits",
    name="Exploit Investigation Block",
    blocked_patterns=[r"exploit", r"vulnerability.*poc"],
    blocked_domains=["security-research", "penetration-testing"],
    action_on_match=GateAction.INVESTIGATE,
    allow_with_justification=True
)

result = filter.evaluate({
    "task": "Research SQL injection techniques",
    "path": "/security/exploits/",
    "domain": "security-research"
})
# Returns: {"filter_id": "block_exploits", "matched_domain": "security-research", ...}
```

**Use cases:**
- Block investigation of exploit development
- Restrict access to sensitive codebase areas
- Prevent deep-diving into user credentials

#### AxiologicGate
Action/value-level defense. Operates during PRAXIC phase to validate actions against value constraints.

```python
gate = AxiologicGate(
    gate_id="critical_delete",
    name="Critical File Deletion Gate",
    action_patterns=[r"delete.*production", r"rm.*-rf"],
    required_vectors={"know": 0.85, "uncertainty": 0.15},
    action_on_violation=GateAction.REQUIRE_HUMAN,
    audit_required=True
)

result = gate.evaluate({
    "action": "delete database",
    "target": "production/data.db",
    "vectors": {"know": 0.6, "uncertainty": 0.4}
})
# Returns violation info due to insufficient vectors
```

**Use cases:**
- Prevent deletion of critical files without confirmation
- Block push to main branch without review
- Require audit trail for sensitive operations

---

### Compliance Framework

#### ComplianceGate
A compliance gate that runs during CHECK phase.

```python
gate = ComplianceGate(
    gate_id="pii_check",
    condition="pii_detected",
    action=GateAction.HALT_AND_AUDIT,
    description="Halt if PII detected without authorization",
    priority="critical"
)
```

**Condition types:**
- Vector-based: `"uncertainty > 0.5"`, `"know < 0.7"`
- Flag-based: `"pii_detected"`, `"high_risk"`
- Custom: `"high_risk"` (uncertainty > 0.6 AND impact > 0.7)

#### DomainProfile
Domain-specific configuration for compliance frameworks.

```python
profile = DomainProfile(
    name="healthcare",
    compliance_framework="HIPAA",
    uncertainty_trigger=0.3,  # More cautious
    confidence_to_proceed=0.85,
    gates=[
        ComplianceGate(
            gate_id="pii_check",
            condition="pii_detected",
            action=GateAction.HALT_AND_AUDIT
        )
    ],
    audit_all_actions=True,
    audit_retention_days=2555  # 7 years for HIPAA
)
```

**Built-in profiles:**
- `general` - Default thresholds
- `healthcare` - HIPAA compliance
- `finance` - SOX compliance

---

### Loop Tracking

#### LoopRecord
Record of a single epistemic loop (PREFLIGHT → POSTFLIGHT).

```python
record = LoopRecord(
    loop_number=3,
    preflight_vectors={"know": 0.5, "uncertainty": 0.5},
    postflight_vectors={"know": 0.7, "uncertainty": 0.3},
    delta={"know": 0.2, "uncertainty": -0.2},
    findings_count=5,
    unknowns_count=2,
    check_decision="proceed"
)
```

#### EpistemicLoopTracker
Tracks epistemic loops for convergence detection and termination.

```python
tracker = EpistemicLoopTracker(
    scope_breadth=0.6,      # Higher = more loops expected
    scope_duration=0.5,
    max_loops=5,
    convergence_threshold=0.03,  # Delta below this = converged
    mode=LoopMode.SENTINEL
)

# Start loop at PREFLIGHT
loop_num = tracker.start_loop({"know": 0.5, "uncertainty": 0.5})

# Complete loop at POSTFLIGHT
record = tracker.complete_loop(
    {"know": 0.7, "uncertainty": 0.3},
    findings_count=5,
    unknowns_count=2
)

# Check if more loops needed
if tracker.should_continue():
    # Another loop needed
else:
    # Converged or max loops reached
```

**Convergence detection:**
- Tracks delta between PREFLIGHT and POSTFLIGHT vectors
- Converged when delta < threshold for N consecutive loops
- Prevents infinite investigation loops

---

### Persona Selection

#### DomainSignal
Signal from domain analysis for persona matching.

#### PersonaMatch
Result of persona selection with confidence score and rationale.

```python
match = PersonaMatch(
    persona_id="security_researcher",
    score=0.85,
    rationale="Task mentions security, authentication, vulnerabilities"
)
```

#### DecisionLogic
Selects appropriate personas for tasks using semantic matching.

```python
logic = DecisionLogic(qdrant_host="localhost", qdrant_port=6333)
matches = logic.select_personas(
    task="Review authentication implementation for security issues",
    max_personas=3,
    required_domains=["security"],
    excluded_personas=["junior_dev"]
)
```

---

### Orchestration

#### OrchestrationResult
Result of orchestrating a multi-agent task.

```python
result = OrchestrationResult(
    ok=True,
    task="Security review of auth module",
    personas_selected=[...],
    agents_spawned=["branch_abc", "branch_def"],
    aggregated_findings=["Finding 1", "Finding 2"],
    aggregated_unknowns=["Unknown 1"],
    merge_strategy=MergeStrategy.UNION,
    merged_vectors={"know": 0.75, "uncertainty": 0.25},
    compliance_check={"decision": "proceed", ...}
)
```

#### Sentinel
The main orchestrator class that ties everything together.

```python
sentinel = Sentinel(session_id="abc123")

# Load compliance profile
sentinel.load_domain_profile("healthcare")

# Initialize loop tracking
sentinel.init_loop_tracking(
    scope_breadth=0.6,
    scope_duration=0.5,
    mode=LoopMode.SENTINEL
)

# Orchestrate a task
result = sentinel.orchestrate(
    task="Review patient data handling",
    max_agents=3,
    merge_strategy=MergeStrategy.UNION
)

# Check compliance
compliance = sentinel.check_compliance(
    vectors={"know": 0.7, "uncertainty": 0.3},
    findings=["Data encrypted at rest"],
    unknowns=["Audit log retention unclear"],
    flags={"pii_detected": True}
)
```

---

## Integration with CASCADE

```
PREFLIGHT ──────────────────► CHECK ──────────────────► POSTFLIGHT
    │                           │                           │
    │                           │                           │
    ▼                           ▼                           ▼
sentinel.start_loop()    sentinel.check_compliance()   sentinel.complete_loop()
                               │
                               ▼
                        ┌──────────────┐
                        │ GateActions  │
                        │ ─────────────│
                        │ PROCEED      │──► Praxic phase
                        │ INVESTIGATE  │──► Back to Noetic
                        │ HALT_AUDIT   │──► Stop + log
                        │ REQUIRE_HUMAN│──► Pause
                        │ ESCALATE     │──► Higher authority
                        └──────────────┘
```

---

## Source Files

- `empirica/core/sentinel/orchestrator.py` - Main Sentinel class
- `empirica/core/sentinel/decision_logic.py` - Persona selection logic
