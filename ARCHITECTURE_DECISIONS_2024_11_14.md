# Architecture Decisions - 2025-11-14

**Decision Date:** 2025-11-14  
**Participants:** Human Developer (Lead), Claude (Co-lead Dev)  
**Context:** Bootstrap refactoring and goal orchestrator improvement

---

## Decision 1: Self-Referential Goal Generation Interface

**Question:** How should AI access itself for goal generation?

**Decision:** ✅ **Option A: llm_callback Function**

**Rationale:**
- **Simplest to implement** - Clean function interface
- **Most flexible** - Works with any AI/LLM provider
- **No external dependencies** - Doesn't require MCP or specific services
- **Easy to test** - Can mock the callback for unit tests
- **Clear contract** - Function signature defines expectations

**Implementation:**
```python
def bootstrap_session(
    session_type: str,
    ai_id: str,
    llm_callback: Optional[Callable[[str], str]] = None,
    **kwargs
) -> dict:
    """
    Bootstrap session with optional self-referential goal generation.
    
    Args:
        llm_callback: Function that takes prompt (str) and returns response (str).
                      If provided, enables AI-powered goal generation.
                      If None, uses minimal/placeholder goal generation.
    
    Example:
        def my_llm(prompt: str) -> str:
            return ai_client.reason(prompt)
        
        bootstrap_session(
            session_type="development",
            ai_id="claude-dev",
            llm_callback=my_llm
        )
    """
    pass
```

**Alternatives Considered:**
- Option B (MCP integration): Too complex, adds unnecessary coupling
- Option C (Configuration-based): Less flexible, harder to customize per-session

---

## Decision 2: When to Use Goal Generation

**Question:** Should goal generation be mandatory or optional?

**Decision:** ✅ **Option B: Profile-Based Configuration**

**Rationale:**
- **Flexible** - Different tasks need different approaches
- **Avoids overhead** - Simple tasks don't pay for unnecessary LLM calls
- **User control** - Developers choose when to use sophisticated reasoning
- **Clear semantics** - Profile names indicate expected behavior

**Implementation:**
```yaml
# empirica/config/investigation_profiles.yaml

profiles:
  minimal:
    description: "Fastest - No goal generation, minimal components"
    goal_generation:
      enabled: false
    components:
      - canonical_epistemic_assessment
      - adaptive_uncertainty_calibration
    
  developer:
    description: "Balanced - Optional goal generation, standard components"
    goal_generation:
      enabled: true
      required: false  # Can proceed without llm_callback
      fallback: "placeholder"  # Use threshold-based if no callback
    components:
      - canonical_epistemic_assessment
      - canonical_goal_orchestrator
      - adaptive_uncertainty_calibration
      - twelve_vector_monitor
    
  autonomous_agent:
    description: "Full autonomy - Required goal generation, all components"
    goal_generation:
      enabled: true
      required: true  # Must provide llm_callback
      fallback: null  # Error if no callback provided
    components:
      - all_canonical_components
      - bayesian_beliefs
      - drift_monitor
    
  researcher:
    description: "Deep exploration - Required goal generation, research focus"
    goal_generation:
      enabled: true
      required: true
      strategy: "exploratory"  # Different prompt templates
    components:
      - all_canonical_components
      - advanced_investigation
```

**Usage Examples:**
```python
# Simple task - no goal generation needed
bootstrap_session(
    session_type="testing",
    ai_id="test-agent",
    profile="minimal"
)

# Development - optional goal generation
bootstrap_session(
    session_type="development",
    ai_id="dev-agent",
    profile="developer",
    llm_callback=my_llm  # Optional
)

# Autonomous agent - requires goal generation
bootstrap_session(
    session_type="autonomous",
    ai_id="auto-agent",
    profile="autonomous_agent",
    llm_callback=my_llm  # Required! Will error if missing
)
```

**Alternatives Considered:**
- Option A (Always on): Wasteful for simple tasks, adds overhead
- Option C (On-demand only): Less discoverable, requires manual configuration each time

---

## Decision 3: Implementation Priority

**Question:** What order should we tackle the work?

**Decision:** ✅ **Path 1 → Path 2 (Investigation then Refactor)**

**Phases:**

### Phase 1: System Validation (Claude - NEXT)
**Goal:** Test system in real scenarios, expose goal orchestrator issues

**Tasks:**
1. Create new CASCADE for code quality analysis
2. Test investigation strategies with real scenarios
3. **Exercise goal orchestrator** - See heuristic issues in action
4. Document exact scenarios where heuristics fail
5. Test more MCP tools (10+ remaining untested)
6. Create findings report

**Why First:** Real-world evidence drives better design decisions

**Estimated:** ~2-3 hours, ~15-20 iterations

---

### Phase 2: Bootstrap Refactoring (Claude)
**Goal:** Implement self-referential goal generation

**Tasks:**
1. **Quick Win:** Update misleading comments (15 min)
   - Fix "no heuristics" claims in bootstrap
   - Document actual behavior
   
2. **Core Implementation:** Self-referential goals (2-3 hours)
   - Add `llm_callback` parameter to `bootstrap_session`
   - Update `canonical_goal_orchestrator.py` to use callback
   - Implement profile-based configuration
   - Add validation: require callback for autonomous profile
   
3. **Testing:** (1 hour)
   - Unit tests: mock llm_callback
   - Integration tests: real LLM goal generation
   - Test all profiles (minimal, developer, autonomous, researcher)
   
4. **Documentation:** (30 min)
   - Update bootstrap documentation
   - Add examples for each profile
   - Document llm_callback contract

**Estimated:** ~3-4 hours, ~20-25 iterations

---

### Phase 3: Handoff Work (Copilot Claude & Qwen)
**Goal:** Delegate non-architectural tasks

**For Copilot Claude:**
- Print → logging refactoring (continuation of Minimax work)
- Test coverage expansion
- Documentation updates
- Code style consistency

**For Qwen:**
- Validation of implementations
- Cross-check test coverage
- Performance testing
- Integration testing

**Coordination:**
- Use git commits for progress tracking
- Use epistemic state for confidence checks
- Weekly sync meetings via status documents

---

## Implementation Details

### Change 1: Update optimal_metacognitive_bootstrap.py

**Current (Line 181):**
```python
self.components['canonical_goal_orchestrator'] = create_goal_orchestrator(use_placeholder=True)
```

**New:**
```python
# Load goal orchestrator based on profile
goal_config = self.profile_config.get('goal_generation', {})
if goal_config.get('enabled', False):
    if llm_callback is not None:
        # AI-powered goal generation
        self.components['canonical_goal_orchestrator'] = create_goal_orchestrator(
            use_placeholder=False,
            llm_callback=llm_callback
        )
    elif goal_config.get('required', False):
        # Profile requires callback but none provided
        raise ValueError(
            f"Profile '{self.profile}' requires llm_callback for goal generation. "
            "Please provide llm_callback parameter or switch to 'minimal' profile."
        )
    else:
        # Fallback to placeholder
        self.components['canonical_goal_orchestrator'] = create_goal_orchestrator(
            use_placeholder=True
        )
else:
    # Goal generation disabled for this profile
    self.components['canonical_goal_orchestrator'] = None
```

---

### Change 2: Update canonical_goal_orchestrator.py

**Add to create_goal_orchestrator():**
```python
def create_goal_orchestrator(
    use_placeholder: bool = True,
    llm_callback: Optional[Callable[[str], str]] = None
) -> 'CanonicalGoalOrchestrator':
    """
    Create goal orchestrator with optional AI-powered goal generation.
    
    Args:
        use_placeholder: If True, use threshold-based goal generation (fast).
                        If False, use llm_callback for reasoning (slower, better).
        llm_callback: Function that takes prompt and returns AI response.
                      Required if use_placeholder=False.
    """
    if not use_placeholder and llm_callback is None:
        raise ValueError("llm_callback required when use_placeholder=False")
    
    return CanonicalGoalOrchestrator(
        use_placeholder=use_placeholder,
        llm_callback=llm_callback
    )
```

**Add to CanonicalGoalOrchestrator class:**
```python
def _generate_goals_via_ai(self, context: dict) -> List[dict]:
    """
    Use AI reasoning to generate context-aware goals.
    
    This is the "self-referential" approach where the AI uses itself
    to reason about what goals are needed based on current context.
    """
    prompt = self._create_goal_generation_prompt(context)
    response = self.llm_callback(prompt)
    goals = self._parse_goal_response(response)
    return goals
```

---

### Change 3: Update Comments (Quick Fix)

**File:** `empirica/bootstraps/optimal_metacognitive_bootstrap.py`

**Line 173:**
```python
# OLD:
logger.info("Loading canonical goal orchestrator (LLM-POWERED, NO HEURISTICS)")

# NEW:
logger.info("Loading canonical goal orchestrator (configuration-based)")
```

**Line 186:**
```python
# OLD:
logger.info("Canonical goal orchestrator loaded (LLM-powered, no heuristics)")

# NEW:
if llm_callback is not None:
    logger.info("Canonical goal orchestrator loaded (AI-powered goal generation)")
else:
    logger.info("Canonical goal orchestrator loaded (threshold-based fallback)")
```

**Line 190:**
```python
# OLD:
logger.info("Falling back to legacy goal orchestrator (heuristic-based)")

# NEW:
logger.info("Goal orchestrator unavailable (minimal profile or load failure)")
```

---

## Testing Strategy

### Unit Tests
```python
def test_bootstrap_with_llm_callback():
    """Test bootstrap with AI-powered goals."""
    def mock_llm(prompt: str) -> str:
        return "Goal 1: Investigate X\nGoal 2: Validate Y"
    
    result = bootstrap_session(
        session_type="test",
        ai_id="test",
        profile="developer",
        llm_callback=mock_llm
    )
    
    assert result['components']['canonical_goal_orchestrator'] is not None
    assert not result['components']['canonical_goal_orchestrator'].use_placeholder

def test_bootstrap_autonomous_requires_callback():
    """Test that autonomous profile requires callback."""
    with pytest.raises(ValueError, match="requires llm_callback"):
        bootstrap_session(
            session_type="test",
            ai_id="test",
            profile="autonomous_agent"
            # Missing llm_callback - should error
        )

def test_bootstrap_minimal_no_goals():
    """Test minimal profile disables goal generation."""
    result = bootstrap_session(
        session_type="test",
        ai_id="test",
        profile="minimal"
    )
    
    assert result['components']['canonical_goal_orchestrator'] is None
```

### Integration Tests
```python
def test_real_llm_goal_generation():
    """Test with real LLM (requires API key)."""
    def real_llm(prompt: str) -> str:
        # Call actual AI service
        return ai_client.complete(prompt)
    
    result = bootstrap_session(
        session_type="development",
        ai_id="integration-test",
        profile="developer",
        llm_callback=real_llm
    )
    
    # Verify goals are generated
    orchestrator = result['components']['canonical_goal_orchestrator']
    goals = orchestrator.generate_goals(context={...})
    
    assert len(goals) > 0
    assert all('reasoning' in g for g in goals)  # AI provides reasoning
```

---

## Success Criteria

### Phase 1 (System Validation) - Complete When:
- ✅ New CASCADE created and tracked
- ✅ Investigation strategies tested in real scenarios
- ✅ Goal orchestrator exercised (document heuristic failures)
- ✅ 10+ additional MCP tools tested
- ✅ Findings report created
- ✅ Recommendations for Phase 2 documented

### Phase 2 (Bootstrap Refactor) - Complete When:
- ✅ Misleading comments fixed
- ✅ llm_callback parameter added to bootstrap
- ✅ Profile-based configuration implemented
- ✅ All 4 profiles working (minimal, developer, autonomous, researcher)
- ✅ Unit tests passing (10+ tests)
- ✅ Integration tests passing (3+ tests)
- ✅ Documentation updated
- ✅ Example code provided for each profile

### Phase 3 (Handoff) - Complete When:
- ✅ Copilot Claude assigned tasks
- ✅ Qwen assigned validation tasks
- ✅ Coordination mechanism established
- ✅ First handoff successful

---

## Risk Mitigation

### Risk 1: Breaking Existing Code
**Mitigation:** 
- Backward compatible: llm_callback is optional
- Default behavior unchanged: use_placeholder=True by default
- Existing code works without changes

### Risk 2: Increased Complexity
**Mitigation:**
- Profile system abstracts complexity
- Simple use cases stay simple (minimal profile)
- Complexity opt-in (autonomous profile)

### Risk 3: LLM Callback Failures
**Mitigation:**
- Graceful fallback to placeholder goals
- Clear error messages when callback required but missing
- Timeout and retry logic in callback wrapper

---

## Documentation Updates Required

1. **Bootstrap Documentation** - Add llm_callback examples
2. **Profile System** - Document all 4 profiles with use cases
3. **Goal Orchestrator** - Explain self-referential approach
4. **Migration Guide** - Show upgrade path from current code
5. **System Prompts** - Update for mini-agents to use callbacks

---

## Timeline

**Phase 1 (System Validation):** 
- Start: Immediately (this session)
- Duration: 2-3 hours
- Completion: Today (2025-11-14)

**Phase 2 (Bootstrap Refactor):**
- Start: After Phase 1 findings
- Duration: 3-4 hours
- Completion: Today or tomorrow (2025-11-14/15)

**Phase 3 (Handoff):**
- Start: After Phase 2 complete
- Duration: Ongoing
- Coordination: Weekly status docs

---

**Status:** ✅ Decisions approved and documented  
**Next:** Begin Phase 1 - System Validation  
**Owner:** Claude (Co-lead Dev)
