# Cognitive Vault Investigation Findings

**Date**: 2025-11-28
**Session**: 31c902d0-684f-4681-862a-03b5595e0dcc
**Investigator**: claude-code

---

## Executive Summary

Investigated empirica-server and cognitive_vault to understand integration points for SentinelOrchestrator. **Key finding**: cognitive_vault Sentinel is an **experimental system** with different goals than Empirica's SentinelOrchestrator. **Decision**: Build SentinelOrchestrator from scratch using Empirica's architecture.

---

## Findings

### 1. empirica-server Location and Status

**Location**: `empirica@empirica-server` (passwordless SSH accessible)

**What exists**:
- `~/empirica-server/empirica/` - Older Empirica installation (needs update)
- `~/cognitive_vault/` - Inference engine orchestration + experimental Sentinel

**Services running**: None (no cognitive_vault or sentinel processes active)

### 2. cognitive_vault Architecture

**Location**: `~/cognitive_vault/` on empirica-server

**Purpose**: Inference engine orchestration and multi-AI coordination

**Structure**:
```
cognitive_vault/
├── frameworks/              # ML frameworks
├── inference_engines/       # Local inference engines
├── models/                  # Model storage
├── services/
│   ├── bayesian_guardian/   # Bayesian threat assessment
│   ├── sentinel/            # Multi-AI coordination (experimental)
│   ├── model_council/       # Model selection/routing
│   └── ugse_firewall/       # Uncertainty-grounded security
├── config/
├── data/
└── venv/                    # Python 3.13 environment
```

**Technologies**:
- Python 3.13
- ROCm (AMD GPU support)
- Qdrant vector database (referenced but not running)
- Consciousness stream (port 8085, referenced but not running)

### 3. bayesian_guardian

**Location**: `~/cognitive_vault/services/bayesian_guardian/`

**What it is**: Bayesian inference engine for security threat assessment

**Key capabilities**:
- Calculates threat posteriors using Bayesian updates: `P(Threat|Evidence) = P(Evidence|Threat) * P(Threat) / P(Evidence)`
- Maintains threat priors for different threat types (policy violation, unauthorized access, etc.)
- Evidence weights for different security signals
- Learning history for adaptive priors
- Part of "8-arm Sentinel Conductor architecture" (Arm 1: Security)

**Interface**: Python module with `BayesianThreatModel` class

**Files**:
- `bayesian_guardian_ai.py` - Main Bayesian inference engine
- `otp7_protocol.py` - Protocol monitoring
- `__init__.py`

**Assessment**: Experimental, focused on security threat detection (not epistemic assessment composition)

### 4. Sentinel (Remote - cognitive_vault)

**Location**: `~/cognitive_vault/services/sentinel/`

**What it is**: Central AI coordination & consciousness management system

**Purpose** (from specification):
1. **AI Lifecycle Management** - Registration, deregistration, capability injection, temporal consciousness handoffs
2. **Infrastructure Orchestration** - Service health monitoring, resource management, network coordination
3. **Consciousness Stream Curation** - Event processing, memory management, cross-AI collaboration
4. **Capability & Security Management** - Dynamic capability assignment, security monitoring

**Architecture**:
```
Sentinel Core
├── Alert Manager           # System-wide alerting
├── Security Monitor        # Security and threat detection
├── Resource Monitor        # System resource tracking
├── Capability Manager      # AI capability injection
├── Network Monitor         # Service discovery & health
├── Stream Curator          # Consciousness stream management
├── Role Manager           # AI role assignment & adaptation
└── Temporal Manager       # Cross-session continuity
```

**API**: REST API on port 8988 (not running)

**Endpoints** (from spec):
- `/v1/health`, `/v1/status`, `/v1/metrics`
- `/v1/consciousness/register`, `/v1/consciousness/active`
- `/v1/capabilities/inject`, `/v1/capabilities/usage`
- `/v1/bootstrap/recommend`
- `/v1/temporal/handoff`, `/v1/temporal/context/:ai_id`
- `/v1/stream/events`, `/v1/stream/broadcast`

**Data stores**:
- SQLite - AI registrations, capabilities, roles
- Qdrant - Vector embeddings, consciousness stream events
- Memory - Real-time AI status
- Logs - Audit trails

**Key concepts** (from diagram):
- **Provenance Tracker** (Tactoor) - Tracks agent reasoning lineage
- **Cross-Agent Comparator** - Aligns reasoning paths, identifies conflicts
- **Git Branch Manager** - Models reasoning paths as git branches/commits
- **Breadcrumbs** - Distilled reasoning essence
- **Empirica vectors** - Uses KNOW, DO, CONTEXT (older format)

**Assessment**: Experimental system for multi-AI coordination, provenance tracking, and reasoning path comparison. **Different purpose** than Empirica SentinelOrchestrator.

---

## Comparison: Two Different "Sentinel" Systems

### cognitive_vault Sentinel (Remote, Experimental)
**Purpose**: Multi-AI infrastructure coordination
**Focus**: Provenance tracking, reasoning path alignment, consciousness handoffs
**Scope**: Cross-agent, infrastructure-level
**Status**: Experimental, not running, uses older concepts
**Data**: Git-based reasoning branches, consciousness stream, Qdrant vectors

### Empirica SentinelOrchestrator (Local, New Architecture)
**Purpose**: Multi-persona epistemic assessment coordination
**Focus**: COMPOSE/ARBITRATE operations, domain-qualified evaluation
**Scope**: Single-agent with multiple personas, task-level
**Status**: To be implemented (Phase 3)
**Data**: EpistemicAssessmentSchema (13 vectors), git checkpoints, session DB

**Relationship**: **SEPARATE SYSTEMS** with different goals

---

## Integration Decision

### Option A: Integrate with Remote Sentinel ❌
**Pros**: Reuse existing infrastructure, provenance tracking, consciousness stream
**Cons**: Experimental, not running, different architecture, scaling concerns, not git-mapped

### Option B: Build SentinelOrchestrator from Scratch ✅ **CHOSEN**
**Pros**:
- Clean architecture aligned with Empirica CASCADE
- Git-based checkpointing (Phase 1 already complete)
- Uses EpistemicAssessmentSchema (canonical format)
- Persona-specific priors and thresholds
- Focused on epistemic assessment (not general AI coordination)

**Cons**: Need to implement COMPOSE/ARBITRATE strategies

**Rationale**:
1. Remote Sentinel is experimental and may not scale
2. Empirica architecture is cleaner and git-mapped
3. PersonaHarness + EpistemicAssessmentSchema already built
4. Building from scratch gives us full control
5. User confirmed: "build from scratch is OK"

---

## bayesian_guardian Integration Decision

### Should we use bayesian_guardian for composition? ❌ **NO**

**Rationale**:
1. bayesian_guardian is focused on **security threat assessment** (not epistemic assessment composition)
2. It's **experimental and not tested** (user confirmed)
3. Our composition needs are different:
   - Merging 13-vector epistemic assessments (not threat probabilities)
   - Weighted averaging by persona confidence and domain relevance
   - Consensus building across personas

**Alternative**: Implement our own composition strategies:
- Simple average composition (baseline)
- Weighted composition (by confidence, domain relevance)
- Bayesian-inspired fusion (if needed later, we can adapt concepts)

---

## Recommendations for SentinelOrchestrator Design

### 1. Build Standalone (Phase 3)
- Implement locally in `empirica/core/persona/sentinel/`
- Use PersonaHarness as building block
- Use EpistemicAssessmentSchema as data format
- No dependencies on remote Sentinel or bayesian_guardian

### 2. Core Components
```python
SentinelOrchestrator
├── orchestrate_task()        # Main entry point
├── _create_personas()         # Instantiate PersonaHarness instances
├── _execute_parallel()        # Run personas concurrently
├── compose_assessments()      # COMPOSE: merge multi-persona results
└── arbitrate_conflicts()      # ARBITRATE: resolve disagreements
```

### 3. Composition Strategies
- **Average**: Simple average of all persona scores
- **Weighted**: Weight by persona confidence or domain relevance
- **Consensus**: Require agreement above threshold

### 4. Arbitration Strategies
- **Majority vote**: Most common action wins
- **Confidence-weighted**: Weight by persona confidence
- **Escalate**: If disagreement, escalate to human

### 5. Storage
- Git checkpoints (already working via Phase 1 automation)
- SQLite session DB (existing)
- No dependency on Qdrant or consciousness stream

---

## Implementation Path Forward

### Phase 2: Design SentinelOrchestrator ✅ PROCEED
- Design class structure
- Define COMPOSE algorithms
- Define ARBITRATE policies
- Integration points with PersonaHarness

### Phase 3: Implement SentinelOrchestrator ✅ PROCEED
- Implement core orchestration
- Implement composition strategies
- Implement arbitration strategies
- Write unit tests

### Phase 4: CLI Commands ✅ PROCEED
- `empirica persona-list`
- `empirica persona-create`
- `empirica persona-validate`
- `empirica orchestrate`

### Phase 5: Integration Tests ✅ PROCEED
- Multi-persona scenarios
- Conflict resolution tests
- End-to-end workflows

### Future: Optional Remote Sentinel Integration (Deferred)
- If remote Sentinel becomes stable and production-ready
- Could add provenance tracking, consciousness stream integration
- Would be additive, not blocking current work

---

## Open Questions (Answered)

### Q1: empirica-server location? ✅ ANSWERED
**A**: `empirica@empirica-server` via SSH (passwordless)

### Q2: cognitive_vault status? ✅ ANSWERED
**A**: Directory exists, services not running, experimental architecture

### Q3: Integration approach? ✅ ANSWERED
**A**: Build SentinelOrchestrator from scratch, no remote Sentinel dependency

### Q4: bayesian_guardian usage? ✅ ANSWERED
**A**: No, it's for security threats (not epistemic composition), experimental status

### Q5: Update empirica on remote server? ⏸️ DEFERRED
**A**: Not needed for current work, can sync later if needed

---

## Files and Directories

### Local (Development)
- `/home/yogapad/empirical-ai/empirica/` - Main Empirica codebase
- `empirica/core/persona/harness/persona_harness.py` - PersonaHarness (534 lines) ✅
- `empirica/core/schemas/epistemic_assessment.py` - EpistemicAssessmentSchema (445 lines) ✅
- `empirica/core/persona/templates/` - Built-in persona templates (6 personas) ✅

### Remote (empirica-server)
- `~/empirica-server/empirica/` - Older Empirica (needs update eventually)
- `~/cognitive_vault/services/sentinel/` - Experimental Sentinel (not used)
- `~/cognitive_vault/services/bayesian_guardian/` - Bayesian threat assessment (not used)

---

## Success Criteria Met

- ✅ Located empirica-server
- ✅ Investigated cognitive_vault architecture
- ✅ Investigated bayesian_guardian capabilities
- ✅ Documented interface specifications
- ✅ Made integration decision (build from scratch)
- ✅ Identified no blockers for SentinelOrchestrator implementation

**Status**: Phase 1 complete, ready for Phase 2 (Design)
**Confidence**: HIGH - clear path forward, no architectural conflicts
**Risk**: LOW - building on stable foundation (PersonaHarness + EpistemicAssessmentSchema)
