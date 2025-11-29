# Next Session Plan - Claude Code
## Cognitive Vault Investigation + SentinelOrchestrator + CLI Commands

**Date**: 2025-11-28
**Session Type**: Investigation → Implementation
**Parallel Work**: Rovodev handles schema migration, Claude Code handles Sentinel integration

---

## Executive Summary

**Goals for next session:**
1. **Investigate empirica-server** (192.168.1.66) - cognitive_vault and bayesian_guardian
2. **Implement SentinelOrchestrator** - multi-persona coordination
3. **Add CLI commands** - persona orchestration interface

**Why this order:**
- Must understand existing Sentinel architecture before building
- Can't design SentinelOrchestrator without knowing cognitive_vault interface
- Can't build CLI commands without knowing SentinelOrchestrator API

**Parallel with Rovodev:**
- Rovodev: Schema migration (OLD → NEW EpistemicAssessmentSchema)
- Claude Code: Sentinel integration (cognitive_vault + orchestrator + CLI)
- Both converge when complete

---

## Context: What We Know

### Phase 3 Status (Completed)
✅ **PersonaHarness** (534 lines) - Universal runtime container
✅ **Communication Protocol** (302 lines) - Signed messages Persona ↔ Sentinel
✅ **Built-in Templates** (6 personas) - Security, UX, Performance, etc.
✅ **Unified Schema** (445 lines) - EpistemicAssessmentSchema canonical format
✅ **Architecture Decision** - Hybrid: universal harness, domain templates, qualified sentinels

### Phase 3 Remaining (This Session)
⏳ **SentinelOrchestrator** - Multi-persona coordination
⏳ **CLI Commands** - `persona-*` and `orchestrate` commands
⏳ **Integration Tests** - End-to-end multi-persona workflows

### Rovodev's Schema Migration Work (Parallel)

**Status**: In progress, mostly complete

**What Rovodev Did**:
✅ **Fixed unit test hanging** (42 tests pass in 0.17s, was hanging before)
✅ **Investigated schemas** - Found OLD and NEW schemas ~80% similar
✅ **Key discovery**: OLD VectorState already has `rationale`, `evidence`, `warrants_investigation`
✅ **Identified differences**:
   - Field names: `know` → `foundation_know` (with tier prefixes)
   - investigation_priority: `Optional[str]` → `int (0-10)`
   - Metadata: OLD lacks `phase`, `persona_priors`, `persona_profile`
   - Tier confidences: OLD stores them, NEW calculates on demand
✅ **Created converters** - OLD ↔ NEW format conversion
⏳ **Currently migrating**:
   - CanonicalEpistemicAssessor.parse_llm_response()
   - CanonicalEpistemicCascade
   - PersonaHarness (uses OLD VectorState currently)
   - CLI/MCP interfaces

**Migration Details** (see `MIGRATION_KNOWLEDGE_STATE.md`):
- **Scope**: ~4,600 lines affected across 10 components
- **Effort**: 14-21 hours estimated, 8 phases
- **Risk**: MEDIUM (core architecture, but well-tested)
- **Approach**: Force migration, no backwards compatibility
- **User approved**: "Better now than later"

**Key Insight for Claude Code**:
🎯 **NEW schema is READY** - Can use `EpistemicAssessmentSchema` immediately
🎯 **Persona prior logic exists** - `apply_persona_priors()` method already implemented
🎯 **Conversion is simple** - Mainly field renaming and metadata addition
🎯 **No blockers** - Can build SentinelOrchestrator in parallel using NEW schema

### Critical Questions to Answer
❓ **What is cognitive_vault?** (on empirica-server 192.168.1.66)
❓ **What is bayesian_guardian?** (mentioned in investigation_profiles.yaml)
❓ **Do they use EpistemicAssessmentSchema?**
❓ **What interface do they expose?**
❓ **How does PersonaHarness connect to them?**

---

## PHASE 1: Investigate empirica-server (2-3 hours)

### Goal
Understand existing Sentinel infrastructure before building SentinelOrchestrator.

### Tasks

#### 1.1 Locate empirica-server
**Where**: User mentioned `192.168.1.66`

**Questions**:
- Is this a remote server or local directory?
- Is it `/home/yogapad/empirical-ai/empirica-server/`?
- Or is it truly remote at IP 192.168.1.66?

**Action**:
```bash
# Check if empirica-server is local
ls -la /home/yogapad/empirical-ai/ | grep empirica-server

# Or check if it's a subdirectory
find /home/yogapad -name "empirica-server" -type d 2>/dev/null
```

#### 1.2 Investigate cognitive_vault
**What we found locally**: `/home/yogapad/empirical-ai/augie/cognitive_vault/`

**Files of interest**:
- `enhanced_consciousness_sentinel.py` (74KB!)
- `local_sentinel.py` (8KB)
- `sentinel_dashboard.py`
- `cognitive-vaultd.py` (daemon?)
- `advanced_metacognitive_memory_manager.py`

**Questions to answer**:
- What does cognitive_vault DO?
- What is its interface (REST API? Python module? gRPC?)
- Does it store epistemic assessments?
- Does it provide decision-making services?
- How does it relate to Empirica's CASCADE?

**Action**:
1. Read key files (enhanced_consciousness_sentinel.py, local_sentinel.py)
2. Check for API endpoints or interface definitions
3. Test if it's running (check processes, ports)
4. Document capabilities and interface

#### 1.3 Investigate bayesian_guardian
**What we know**: Mentioned in `empirica/config/investigation_profiles.yaml:405`

**Questions to answer**:
- Where is bayesian_guardian code?
- What does it DO? (Bayesian calibration? Decision-making?)
- Is it integrated with cognitive_vault?
- Does it use EpistemicAssessmentSchema?

**Action**:
```bash
# Search for bayesian_guardian
grep -r "bayesian_guardian" /home/yogapad/empirical-ai/
find /home/yogapad/empirical-ai/ -name "*bayesian*" -type f
```

#### 1.4 Document Findings
**Create**: `COGNITIVE_VAULT_FINDINGS.md`

**Document**:
- What cognitive_vault is and what it does
- What bayesian_guardian is and what it does
- Interface specification (API, methods, data formats)
- How PersonaHarness should connect to it
- Whether it uses EpistemicAssessmentSchema
- Any schema conflicts or compatibility issues

---

## PHASE 2: Design SentinelOrchestrator (1-2 hours)

### Goal
Design the orchestrator that coordinates multiple PersonaHarness instances.

### Inputs from Phase 1
- cognitive_vault capabilities (from investigation)
- bayesian_guardian integration (from investigation)
- PersonaHarness interface (already implemented)
- Communication protocol (already implemented)

### Design Decisions

#### 2.1 Architecture Questions
**Q1: Where does SentinelOrchestrator run?**
- Option A: Locally in Empirica CLI process
- Option B: On empirica-server (192.168.1.66) as service
- Option C: Hybrid (local coordinator, remote cognitive_vault)

**Decision depends on**: cognitive_vault interface findings

**Q2: How does it coordinate personas?**
```python
# Three orchestration strategies from architecture doc:
1. parallel_with_consensus - Run personas in parallel, merge insights
2. weighted_by_domain - Weight personas by domain relevance
3. hierarchical - Sentinel manages other Sentinels
```

**Decision**: Start with `parallel_with_consensus` (simplest)

**Q3: How does it handle conflicts?**
```python
# When personas disagree on action (one says INVESTIGATE, one says PROCEED)
- Majority vote?
- Weighted by confidence?
- Escalate to human?
- Bayesian arbitration?
```

**Decision depends on**: bayesian_guardian capabilities

#### 2.2 Core Components to Implement

**SentinelOrchestrator** (`empirica/core/persona/sentinel/sentinel_orchestrator.py`)
```python
class SentinelOrchestrator:
    """Coordinates multiple PersonaHarness instances"""

    def __init__(
        self,
        sentinel_id: str,
        qualified_domains: List[str],
        orchestration_strategy: str = "parallel_with_consensus",
        cognitive_vault_url: Optional[str] = None
    ):
        """Initialize orchestrator"""

    async def orchestrate_task(
        self,
        task: str,
        personas: List[str],
        context: Optional[Dict] = None
    ) -> OrchestrationResult:
        """
        Execute task across multiple personas

        Flow:
        1. Create PersonaHarness for each persona
        2. Execute task in parallel (or sequentially)
        3. Collect assessments from each persona
        4. COMPOSE - Merge insights
        5. ARBITRATE - Resolve conflicts
        6. Return unified result
        """

    def compose_assessments(
        self,
        persona_assessments: Dict[str, EpistemicAssessmentSchema]
    ) -> EpistemicAssessmentSchema:
        """
        COMPOSE operation - merge multi-persona assessments

        Strategies:
        - Average scores across personas
        - Weighted average by persona confidence
        - Bayesian fusion (if bayesian_guardian available)
        """

    def arbitrate_conflicts(
        self,
        persona_actions: Dict[str, str]  # {"security": "investigate", "ux": "proceed"}
    ) -> str:
        """
        Resolve conflicting action recommendations

        Returns: "proceed", "investigate", or "escalate"
        """
```

#### 2.3 Integration Points

**With cognitive_vault** (if it exists):
- Store multi-persona assessment history
- Query epistemic memory for domain insights
- Track orchestration patterns over time

**With bayesian_guardian** (if it exists):
- Use Bayesian fusion for assessment composition
- Calibrate persona confidence over time
- Adaptive weighting based on accuracy

**With PersonaHarness**:
- Use existing communication protocol
- Receive STATUS_REPORT, ESCALATION_REQUEST messages
- Send TASK_ASSIGNMENT, PROCEED_TO_ACT messages

---

## PHASE 3: Implement SentinelOrchestrator (3-4 hours)

### Goal
Build working multi-persona orchestration.

### Implementation Tasks

#### 3.1 Directory Structure
```bash
empirica/core/persona/sentinel/
├── __init__.py
├── sentinel_orchestrator.py       # Main orchestrator
├── composition_strategies.py      # COMPOSE algorithms
├── arbitration_strategies.py      # Conflict resolution
└── cognitive_vault_client.py      # Interface to cognitive_vault (if needed)
```

#### 3.2 Core Implementation

**File**: `empirica/core/persona/sentinel/sentinel_orchestrator.py`

**Key methods**:
1. `__init__()` - Initialize with strategy, domains, cognitive_vault connection
2. `orchestrate_task()` - Main entry point for multi-persona execution
3. `_create_persona_harnesses()` - Instantiate harnesses for requested personas
4. `_execute_parallel()` - Run personas in parallel
5. `_collect_results()` - Gather assessments from all personas
6. `compose_assessments()` - COMPOSE operation (merge insights)
7. `arbitrate_conflicts()` - Resolve disagreements
8. `_store_to_cognitive_vault()` - Store results if cognitive_vault available

**Composition strategies** (`composition_strategies.py`):
```python
def average_composition(assessments: List[EpistemicAssessmentSchema]) -> EpistemicAssessmentSchema:
    """Simple average of all persona assessments"""

def weighted_composition(
    assessments: List[EpistemicAssessmentSchema],
    weights: Dict[str, float]
) -> EpistemicAssessmentSchema:
    """Weighted average based on persona confidence or domain relevance"""

def bayesian_composition(
    assessments: List[EpistemicAssessmentSchema],
    bayesian_guardian_client
) -> EpistemicAssessmentSchema:
    """Bayesian fusion using bayesian_guardian (if available)"""
```

**Arbitration strategies** (`arbitration_strategies.py`):
```python
def majority_vote_arbitration(actions: Dict[str, str]) -> str:
    """Simple majority vote"""

def confidence_weighted_arbitration(
    actions: Dict[str, str],
    confidences: Dict[str, float]
) -> str:
    """Weight votes by persona confidence"""

def escalate_on_conflict_arbitration(actions: Dict[str, str]) -> str:
    """If any disagreement, escalate to human"""
```

#### 3.3 Testing Strategy

**Create**: `tests/unit/persona/test_sentinel_orchestrator.py`

**Test cases**:
1. Test orchestration with 2 personas (security + UX)
2. Test COMPOSE with agreeing personas (both high confidence)
3. Test COMPOSE with disagreeing personas (security says investigate, UX says proceed)
4. Test arbitration strategies (majority, weighted, escalate)
5. Test cognitive_vault integration (if available)
6. Test with mock LLM (no actual inference)

**Mock approach**:
```python
# Mock PersonaHarness to return predetermined assessments
@pytest.fixture
def mock_persona_harness(monkeypatch):
    async def mock_execute_task(self, task, context):
        # Return predetermined assessment based on persona type
        if self.persona_id == "security":
            return high_security_concern_assessment
        elif self.persona_id == "ux":
            return moderate_ux_confidence_assessment

    monkeypatch.setattr(PersonaHarness, "execute_task", mock_execute_task)
```

---

## PHASE 4: CLI Commands for Persona Orchestration (2-3 hours)

### Goal
Make persona orchestration accessible via CLI.

### Commands to Implement

#### 4.1 Persona Management Commands

**`empirica persona-list`**
```bash
# List available personas (built-in + custom)
empirica persona-list

# Output:
# Built-in Personas:
# - security (Security Expert)
# - ux (UX Specialist)
# - performance (Performance Engineer)
# - architecture (Software Architect)
# - code_review (Code Reviewer)
# - sentinel (Meta-Sentinel)
#
# Custom Personas:
# - ml_engineer (Machine Learning Engineer) [.empirica/personas/ml_engineer.json]
```

**`empirica persona-create`**
```bash
# Create persona from template
empirica persona-create ml_engineer \
  --template builtin:performance \
  --name "ML Engineer" \
  --focus-domains "machine_learning,deep_learning,model_training"

# Create custom persona from scratch
empirica persona-create custom_persona \
  --from-file .empirica/personas/custom.json
```

**`empirica persona-validate`**
```bash
# Validate persona configuration
empirica persona-validate ml_engineer

# Output:
# ✅ Persona 'ml_engineer' is valid
# - Priors: 13/13 vectors present
# - Thresholds: all valid ranges
# - Weights: sum to 1.0
# - Focus domains: 5 domains specified
```

#### 4.2 Orchestration Commands

**`empirica orchestrate`**
```bash
# Run multi-persona CASCADE
empirica orchestrate "Implement authentication system" \
  --personas security,ux,architecture \
  --ai-id claude-code \
  --session-id abc123 \
  --strategy parallel_with_consensus

# Flow:
# 1. Creates SentinelOrchestrator
# 2. Instantiates 3 PersonaHarness instances (security, ux, architecture)
# 3. Each runs PREFLIGHT in parallel
# 4. COMPOSE: Merges 3 assessments into unified view
# 5. ARBITRATE: Determines action (PROCEED/INVESTIGATE/ESCALATE)
# 6. If PROCEED: Each persona runs CASCADE
# 7. COMPOSE final results
# 8. Returns unified output
```

**`empirica orchestrate-monitor`**
```bash
# Monitor ongoing orchestration
empirica orchestrate-monitor --session-id abc123

# Output (live updating):
# Orchestration Status:
# ==================
# Session: abc123
# Task: Implement authentication system
# Personas: security, ux, architecture
#
# security:       [INVESTIGATE] Round 2/5
# ux:             [PREFLIGHT] Waiting...
# architecture:   [ACT] Executing...
#
# Composition: In progress (2/3 complete)
```

#### 4.3 Implementation Files

**`empirica/cli/command_handlers/persona_commands.py`** (NEW)
```python
def handle_persona_list_command(args):
    """List available personas"""

def handle_persona_create_command(args):
    """Create persona from template"""

def handle_persona_validate_command(args):
    """Validate persona configuration"""
```

**`empirica/cli/command_handlers/orchestration_commands.py`** (NEW)
```python
async def handle_orchestrate_command(args):
    """Run multi-persona CASCADE"""
    orchestrator = SentinelOrchestrator(
        sentinel_id=args.ai_id,
        qualified_domains=["*"],  # All domains
        orchestration_strategy=args.strategy
    )

    result = await orchestrator.orchestrate_task(
        task=args.task,
        personas=args.personas.split(","),
        context={"session_id": args.session_id}
    )

    print(json.dumps(result.to_dict(), indent=2))

def handle_orchestrate_monitor_command(args):
    """Monitor orchestration progress"""
```

**Update**: `empirica/cli/cli.py`
```python
# Add new subcommands
parser_persona_list = subparsers.add_parser("persona-list", help="List available personas")
parser_persona_create = subparsers.add_parser("persona-create", help="Create persona from template")
parser_persona_validate = subparsers.add_parser("persona-validate", help="Validate persona")
parser_orchestrate = subparsers.add_parser("orchestrate", help="Run multi-persona CASCADE")
parser_orchestrate_monitor = subparsers.add_parser("orchestrate-monitor", help="Monitor orchestration")
```

---

## PHASE 5: Integration Testing (1-2 hours)

### Goal
Verify end-to-end multi-persona workflows.

### Test Scenarios

#### 5.1 Scenario: Security + UX Personas Agree
```bash
# Both personas should agree this is straightforward
empirica orchestrate "Update copyright year in footer" \
  --personas security,ux \
  --ai-id test-agent \
  --strategy parallel_with_consensus

# Expected:
# - Both assess PROCEED with high confidence
# - COMPOSE yields high overall confidence
# - No arbitration needed (agreement)
# - Result: PROCEED to ACT
```

#### 5.2 Scenario: Security + UX Personas Disagree
```bash
# Security wants investigation, UX says proceed
empirica orchestrate "Add social login with Google OAuth" \
  --personas security,ux \
  --ai-id test-agent \
  --strategy parallel_with_consensus

# Expected:
# - Security: INVESTIGATE (uncertainty about OAuth security)
# - UX: PROCEED (OAuth improves user experience)
# - COMPOSE: Merge assessments
# - ARBITRATE: Resolve conflict (likely INVESTIGATE wins due to security criticality)
# - Result: INVESTIGATE before proceeding
```

#### 5.3 Scenario: Three Personas with Weighted Strategy
```bash
# Security, UX, Performance - weight by domain relevance
empirica orchestrate "Implement client-side caching" \
  --personas security,ux,performance \
  --ai-id test-agent \
  --strategy weighted_by_domain

# Expected:
# - Performance persona has highest weight (caching is performance domain)
# - Security has moderate weight (cache security implications)
# - UX has lower weight (less relevant to UX)
# - COMPOSE uses weighted average
# - Performance's assessment has most influence
```

#### 5.4 Integration with cognitive_vault (if available)
```bash
# Test storing orchestration history
empirica orchestrate "Implement rate limiting" \
  --personas security,performance \
  --ai-id test-agent \
  --cognitive-vault-url http://192.168.1.66:5000

# Expected:
# - Orchestration completes normally
# - Results stored in cognitive_vault
# - Can query later for insights
```

### Success Criteria
- ✅ All personas complete CASCADE
- ✅ COMPOSE merges assessments correctly
- ✅ ARBITRATE resolves conflicts appropriately
- ✅ CLI commands work end-to-end
- ✅ Results are logged and queryable
- ✅ No crashes or hangs

---

## PHASE 6: Documentation (1 hour)

### Documents to Create

#### 6.1 Technical Documentation

**`docs/guides/MULTI_PERSONA_ORCHESTRATION.md`**
```markdown
# Multi-Persona Orchestration Guide

## Overview
How to use SentinelOrchestrator for multi-persona CASCADE workflows.

## Quick Start
- Creating personas
- Running orchestration
- Interpreting results

## Advanced Topics
- Custom orchestration strategies
- Conflict resolution
- cognitive_vault integration
- Bayesian fusion with bayesian_guardian

## Examples
- Security + UX workflow
- Full-stack orchestration (5 personas)
- Hierarchical Sentinel orchestration
```

**`COGNITIVE_VAULT_INTEGRATION.md`** (based on Phase 1 findings)
```markdown
# cognitive_vault Integration Guide

## What is cognitive_vault?
[Findings from investigation]

## Interface Specification
[API documentation]

## Integration with Empirica
[How PersonaHarness and SentinelOrchestrator connect]

## Bayesian Guardian
[How bayesian_guardian works with assessments]
```

#### 6.2 Update Existing Documentation

**Update**: `SESSION_STATUS.md`
- Mark SentinelOrchestrator as complete
- Mark CLI commands as complete
- Update Phase 3 status to 100%

**Update**: `ARCHITECTURE_PERSONA_SENTINEL.md`
- Add SentinelOrchestrator implementation details
- Add cognitive_vault integration section
- Add bayesian_guardian integration section

---

## Dependencies and Coordination

### With Rovodev (Schema Migration) - UPDATED

**Coordination point**: EpistemicAssessmentSchema

**Rovodev's Progress** (see `MIGRATION_KNOWLEDGE_STATE.md`):
✅ **Investigated schemas** - Found OLD and NEW are more similar than expected
✅ **Key insight** - VectorState (OLD) already has most NEW features (rationale, evidence, warrants_investigation)
✅ **Identified differences**:
   - Field naming: `know` → `foundation_know`, etc.
   - investigation_priority: `Optional[str]` → `int (0-10)`
   - Metadata: OLD lacks `phase`, `persona_priors`, `persona_profile`
✅ **Understands assessor flow** - `assess()` returns prompt dict, `parse_llm_response()` converts to schema
⏳ **Currently working on** - Fixing converters and testing

**Rovodev is migrating**:
- CanonicalEpistemicAssessor.parse_llm_response() → return NEW schema
- CanonicalEpistemicCascade → use NEW schema internally
- PersonaHarness → use NEW schema (currently uses OLD VectorState)
- CLI/MCP → accept NEW schema format

**Claude Code is building**:
- SentinelOrchestrator → compose NEW schema (EpistemicAssessmentSchema)
- CLI orchestrate commands → use NEW schema
- **Can start immediately** - NEW schema is stable and well-defined

**Migration Simplification**:
- 🎯 **Simpler than expected** - Schemas are ~80% similar
- 🎯 **Main work** - Field renaming and metadata addition
- 🎯 **Persona prior logic** - Already in NEW schema (`apply_persona_priors()`)

**Potential conflicts**:
- ❌ **LOW RISK** - PersonaHarness schema interface (Rovodev migrating, but interface is clear)
- ❌ **LOW RISK** - CLI command structure (NEW schema format is stable)

**Mitigation**:
- ✅ Use NEW schema from the start (already in `empirica/core/schemas/`)
- ✅ Write tests that verify schema compatibility
- ✅ Rovodev finishing converters first, then migrating components
- ✅ Claude Code can proceed in parallel - NEW schema is ready

### With empirica-server (192.168.1.66)

**Unknown factors**:
- Is empirica-server accessible?
- Is cognitive_vault running?
- What is the API interface?
- Does it conflict with local architecture?

**Mitigation**:
- Phase 1 investigation answers these questions
- If empirica-server is unavailable, build SentinelOrchestrator standalone
- Design with abstraction: cognitive_vault_client can be swapped
- Mock cognitive_vault for testing

---

## Risk Assessment

### HIGH RISK
- **cognitive_vault interface unknown** - Could force redesign
  - Mitigation: Investigate first (Phase 1)
  - Fallback: Build standalone, integrate later

- **Schema changes from Rovodev** - Could break integration
  - Mitigation: Use NEW schema from start
  - Mitigation: Coordinate merges

### MEDIUM RISK
- **Composition algorithms** - May need iteration to get right
  - Mitigation: Start simple (average), add complexity later
  - Mitigation: Extensive testing with edge cases

- **Conflict arbitration** - Hard to get policy right
  - Mitigation: Make strategies pluggable
  - Mitigation: User can override arbitration decision

### LOW RISK
- **CLI commands** - Straightforward implementation
  - Mitigation: Follow existing CLI patterns

- **Documentation** - Can always improve later
  - Mitigation: Document as you build

---

## Session Flow (Recommended Order)

### Hour 1-3: Investigation
1. Locate empirica-server (local or remote?)
2. Investigate cognitive_vault
   - Read enhanced_consciousness_sentinel.py
   - Test if running (check ports, processes)
   - Document interface
3. Investigate bayesian_guardian
   - Find code
   - Understand capabilities
4. Create COGNITIVE_VAULT_FINDINGS.md
5. **CHECKPOINT**: Decide on SentinelOrchestrator integration approach

### Hour 4-5: Design
1. Design SentinelOrchestrator architecture
   - Based on cognitive_vault findings
   - Choose orchestration strategy
   - Design composition algorithm
   - Design arbitration policy
2. Create directory structure
3. Write interface definitions (abstract classes)
4. **CHECKPOINT**: Review design with user if needed

### Hour 6-9: Implementation
1. Implement SentinelOrchestrator core
   - `__init__()`, `orchestrate_task()`
2. Implement composition strategies
   - Average, weighted, bayesian (if available)
3. Implement arbitration strategies
   - Majority vote, confidence-weighted, escalate
4. Write unit tests
   - Mock PersonaHarness
   - Test COMPOSE with 2-3 personas
   - Test arbitration edge cases
5. **CHECKPOINT**: All tests pass

### Hour 10-12: CLI Commands
1. Implement persona-list command
2. Implement persona-create command
3. Implement persona-validate command
4. Implement orchestrate command
5. Implement orchestrate-monitor command
6. Test CLI end-to-end
7. **CHECKPOINT**: CLI commands work

### Hour 13-14: Integration Testing
1. Test multi-persona scenarios
2. Test conflict resolution
3. Test cognitive_vault integration (if available)
4. Fix any bugs found
5. **CHECKPOINT**: All integration tests pass

### Hour 15: Documentation
1. Create MULTI_PERSONA_ORCHESTRATION.md
2. Create COGNITIVE_VAULT_INTEGRATION.md
3. Update SESSION_STATUS.md
4. Update ARCHITECTURE_PERSONA_SENTINEL.md
5. **CHECKPOINT**: Documentation complete

---

## Success Criteria

After this session, we should have:

### Deliverables
- ✅ **COGNITIVE_VAULT_FINDINGS.md** - Investigation results
- ✅ **SentinelOrchestrator** - Working implementation (~300-500 lines)
- ✅ **Composition strategies** - 2-3 algorithms implemented
- ✅ **Arbitration strategies** - 2-3 policies implemented
- ✅ **5 CLI commands** - persona-list, persona-create, persona-validate, orchestrate, orchestrate-monitor
- ✅ **Unit tests** - 10+ tests covering orchestration scenarios
- ✅ **Integration tests** - 3-5 end-to-end workflows
- ✅ **Documentation** - 2 guides + updates to existing docs

### Functionality
- ✅ Can run multi-persona CASCADE (2-3 personas)
- ✅ Can COMPOSE assessments from multiple personas
- ✅ Can ARBITRATE conflicts between personas
- ✅ Can create and validate personas via CLI
- ✅ Can monitor orchestration progress
- ✅ cognitive_vault integration works (if available)

### Code Quality
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Code follows existing Empirica patterns
- ✅ Type hints and docstrings complete
- ✅ No regressions in existing functionality

---

## Open Questions for User

Before starting next session, please clarify:

### Q1: empirica-server Location
- Is empirica-server at IP 192.168.1.66 (remote)?
- Or is it a local directory (e.g., `/home/yogapad/empirical-ai/empirica-server/`)?
- Is it accessible? Do we need SSH credentials?

### Q2: cognitive_vault Status
- Is cognitive_vault in `/home/yogapad/empirical-ai/augie/cognitive_vault/` the one to integrate?
- Or is there a separate implementation on empirica-server?
- Is it running? Should we start it?

### Q3: Coordination with Rovodev
- Should Claude Code wait for schema migration to complete?
- Or build in parallel using NEW schema?
- Who merges first?

### Q4: Scope Adjustment
- Is 15 hours too aggressive for one session?
- Should we split across 2 sessions?
- Any features to defer?

### Q5: Sentinel LLM Execution
- Where should Sentinel execute LLM prompts for assessment?
- Local `llm` command?
- Remote inference at 192.168.1.66?
- Mock for now, integrate later?

---

## Fallback Plans

### If cognitive_vault is unavailable
**Plan**: Build SentinelOrchestrator standalone
- Skip cognitive_vault integration
- Use in-memory storage
- Add cognitive_vault_client abstraction for later integration

### If empirica-server is inaccessible
**Plan**: Continue with local implementation
- All orchestration runs locally
- Document interface for future remote integration
- Add REST API to SentinelOrchestrator for server deployment

### If schema migration conflicts arise
**Plan**: Coordinate merge timing
- Claude Code uses NEW schema from start
- Wait for Rovodev to finish migration
- Merge orchestration after schema migration complete
- Resolve conflicts together

### If session runs long
**Plan**: Split into 2 sessions
- Session 1: Investigation + SentinelOrchestrator implementation
- Session 2: CLI commands + integration testing + documentation

---

## Next Steps

**For User**:
1. Review this plan
2. Answer open questions above
3. Approve scope and timeline
4. Start next session when ready

**For Next Claude Code Session**:
1. Read this plan
2. Start with Phase 1 (investigation)
3. Adapt plan based on findings
4. Execute phases in order
5. Communicate frequently if blockers arise

---

**Status**: Ready for next session ✅
**Estimated effort**: 12-15 hours
**Risk level**: MEDIUM (unknown cognitive_vault interface)
**Coordination**: Parallel with Rovodev schema migration
**User approval needed**: Yes (answer open questions)
