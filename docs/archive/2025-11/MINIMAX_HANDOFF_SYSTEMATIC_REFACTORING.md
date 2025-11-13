# Minimax Handoff: Systematic Profile System Refactoring

**Date:** 2024-11-13  
**From:** Claude (Rovo Dev)  
**To:** Minimax (Autonomous Agent)  
**Task Type:** Systematic find-and-replace refactoring  
**Estimated Time:** 2-3 hours  

---

## Mission

Replace hardcoded investigation constraints with profile-based configuration across the Empirica codebase. This is mechanical refactoring work with clear patterns and validation criteria.

**What's Already Done (by Claude):**
✅ Profile system created (`empirica/config/investigation_profiles.yaml`)
✅ Profile loader implemented (`empirica/config/profile_loader.py`)
✅ Documentation complete
✅ **Critical philosophical fix:** Fake learning heuristics removed from POSTFLIGHT

**What You Need to Do:**
🔄 Replace hardcoded constraints with profile references (Phases 2-4)
🔄 Update method signatures to accept profile parameters
🔄 Remove hardcoded confidence_gain values in tool recommendations
🔄 Update tests

---

## Phase 2: Refactor Metacognitive Cascade

### File: `empirica/core/metacognitive_cascade/metacognitive_cascade.py`

#### Task 2.1: Update `__init__` Method (Lines 168-200)

**Current Code (Lines 170-171):**
```python
action_confidence_threshold: float = 0.70,
max_investigation_rounds: int = 3,
```

**Replace With:**
```python
# NEW: Profile-based configuration
profile_name: Optional[str] = None,
ai_model: Optional[str] = None,
domain: Optional[str] = None,

# DEPRECATED: Keep for backward compatibility
action_confidence_threshold: Optional[float] = None,
max_investigation_rounds: Optional[int] = None,
```

**Then add after line 200 (in __init__ body):**
```python
# Load investigation profile
from empirica.config.profile_loader import select_profile, get_profile_loader

self.profile = select_profile(
    ai_model=ai_model,
    domain=domain,
    explicit_profile=profile_name
)

# Get universal constraints
loader = get_profile_loader()
self.universal_constraints = loader.universal_constraints

# Backward compatibility: override profile if old params provided
if max_investigation_rounds is not None:
    import warnings
    warnings.warn(
        "max_investigation_rounds is deprecated. Use profile_name instead.",
        DeprecationWarning,
        stacklevel=2
    )
    self.profile.investigation.max_rounds = max_investigation_rounds

if action_confidence_threshold is not None:
    import warnings
    warnings.warn(
        "action_confidence_threshold is deprecated. Use profile_name instead.",
        DeprecationWarning,
        stacklevel=2
    )
    self.profile.investigation.confidence_threshold = action_confidence_threshold
```

**Validation:**
```bash
python3 -c "from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade; c = CanonicalEpistemicCascade(profile_name='balanced'); print('✓ Profile initialization works')"
```

---

#### Task 2.2: Update Investigation Loop (Lines 536-570)

**Current Code (Line 540):**
```python
while investigation_rounds < self.max_investigation_rounds:
```

**Replace With:**
```python
max_rounds = self.profile.investigation.max_rounds
while max_rounds is None or investigation_rounds < max_rounds:
```

**Current Code (Line 542):**
```python
confidence_low = current_assessment.overall_confidence < self.action_confidence_threshold
```

**Replace With:**
```python
# Support dynamic thresholds for high reasoning AIs
if self.profile.investigation.confidence_threshold_dynamic:
    # AI determines threshold based on context (future feature)
    threshold = self.profile.investigation.confidence_threshold
else:
    threshold = self.profile.investigation.confidence_threshold

confidence_low = current_assessment.overall_confidence < threshold
```

**Current Code (Line 548):**
```python
print(f"(REQUIRED - confidence {current_assessment.overall_confidence:.2f} < {self.action_confidence_threshold})")
```

**Replace With:**
```python
print(f"(REQUIRED - confidence {current_assessment.overall_confidence:.2f} < {threshold})")
```

**Validation:**
```bash
# Test that investigation loop respects profile max_rounds
python3 -c "
import asyncio
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

async def test():
    cascade = CanonicalEpistemicCascade(
        profile_name='autonomous_agent',  # max 5 rounds
        enable_session_db=False
    )
    # Verify profile loaded
    assert cascade.profile.investigation.max_rounds == 5
    print('✓ Profile max_rounds loaded correctly')

asyncio.run(test())
"
```

---

#### Task 2.3: Remove Hardcoded confidence_gain Values (Lines 1367-1497)

**Pattern to Find:**
```python
'confidence_gain': 0.15
'confidence_gain': 0.20
'confidence_gain': 0.25
# ... etc
```

**Replace ALL instances with:**
```python
# Note: confidence_gain is deprecated - genuine reassessment preferred
'confidence_gain': 0.0  # No artificial gain
```

**Or better yet, remove the field entirely if not needed.**

**Locations:**
- Line 1368: `'confidence_gain': 0.15` → `'confidence_gain': 0.0`
- Line 1374: `'confidence_gain': 0.20` → `'confidence_gain': 0.0`
- Line 1380: `'confidence_gain': 0.10` → `'confidence_gain': 0.0`
- Line 1386: `'confidence_gain': 0.25` → `'confidence_gain': 0.0`
- Lines 1417-1497: All `confidence_gain` values → `0.0`

**Validation:**
```bash
grep -n "confidence_gain.*0\.[1-9]" empirica/core/metacognitive_cascade/metacognitive_cascade.py
# Should return no results
```

---

## Phase 3: Refactor Canonical Assessment

### File: `empirica/core/canonical/canonical_epistemic_assessment.py`

#### Task 3.1: Verify `_determine_action` Has Profile Support ✅

**NOTE:** This method is already updated! (Line 786-854)

**Current Signature (Line 786):**
```python
def _determine_action(
    self,
    engagement: VectorState,
    engagement_gate_passed: bool,
    coherence: VectorState,
    density: VectorState,
    change: VectorState,
    clarity: VectorState,
    foundation_confidence: float,
    overall_confidence: float,
    uncertainty: VectorState,
    profile: Optional['InvestigationProfile'] = None
) -> Action:
    """
    Determine recommended action based on epistemic vectors and profile.
    
    If profile.action_thresholds.override_allowed is True, AI can override
    these recommendations with strong rationale.
    
    Args:
        vectors: Epistemic vector scores
        profile: Investigation profile (if None, uses default thresholds)
    """
```

**Already Updated (Lines 830-854):**
```python
# PRIORITY 3: HIGH UNCERTAINTY
if uncertainty.score > thresholds.uncertainty_high:
    action = Action.INVESTIGATE
    if thresholds.override_allowed:
        # Note: AI can override this with strong rationale
        pass
    return action

# PRIORITY 4: COMPREHENSION ISSUES
if clarity.score < thresholds.clarity_low:
    action = Action.CLARIFY
    if thresholds.override_allowed:
        pass
    return action

# PRIORITY 5: FOUNDATION GAPS
if foundation_confidence < thresholds.foundation_low:
    return Action.INVESTIGATE

# PRIORITY 6: OVERALL CONFIDENCE
if overall_confidence >= thresholds.confidence_proceed_min:
    return Action.PROCEED
elif overall_confidence >= (thresholds.confidence_proceed_min - 0.15):
    return Action.INVESTIGATE
else:
    return Action.CLARIFY
```

**Status:** ✅ ALREADY DONE (Claude completed this earlier)
```python
# Use profile thresholds if available, otherwise use defaults
if profile is not None:
    thresholds = profile.action_thresholds
else:
    # Default thresholds (for backward compatibility)
    from empirica.config.profile_loader import load_profile
    thresholds = load_profile('balanced').action_thresholds

# PRIORITY 3: HIGH UNCERTAINTY
if uncertainty.score > thresholds.uncertainty_high:
    action = Action.INVESTIGATE
    if thresholds.override_allowed:
        # Note: AI can override this with strong rationale
        pass
    return action

# PRIORITY 4: COMPREHENSION ISSUES
if clarity.score < thresholds.clarity_low:
    action = Action.CLARIFY
    if thresholds.override_allowed:
        pass
    return action

# PRIORITY 5: FOUNDATION GAPS
if foundation_confidence < thresholds.foundation_low:
    return Action.INVESTIGATE

# PRIORITY 6: OVERALL CONFIDENCE
if overall_confidence >= thresholds.confidence_proceed_min:
    return Action.PROCEED
elif overall_confidence >= (thresholds.confidence_proceed_min - 0.15):
    return Action.INVESTIGATE
else:
    return Action.CLARIFY
```

**Then update all callers to pass profile:**

**Search for:**
```bash
grep -n "_determine_recommended_action" empirica/core/canonical/canonical_epistemic_assessment.py
```

**Update each call site to pass profile parameter.**

**Validation:**
```bash
python3 -c "
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.config.profile_loader import load_profile

assessor = CanonicalEpistemicAssessor()
profile = load_profile('critical_domain')

# Verify critical domain has high thresholds
assert profile.action_thresholds.confidence_proceed_min == 0.90
print('✓ Profile thresholds accessible in canonical assessment')
"
```

---

## Phase 4: Refactor Investigation Strategy

### File: `empirica/investigation/investigation_strategy.py`

#### Task 4.1: Remove Keyword-Based Domain Detection (Lines 423-448)

**Current Code:**
```python
def infer_domain(self, task: str, context: Dict[str, Any]) -> Domain:
    """Infer domain from task and context - HEURISTIC-BASED"""
    task_lower = task.lower()
    
    # Code analysis keywords
    if any(kw in task_lower for kw in ['refactor', 'code', 'function', 'class']):
        return Domain.CODE_ANALYSIS
    
    # Research keywords
    if any(kw in task_lower for kw in ['research', 'investigate', 'find', 'search']):
        return Domain.RESEARCH
    
    # ... more keyword matching
```

**Replace With:**
```python
def infer_domain(
    self,
    task: str,
    context: Dict[str, Any],
    profile: Optional['InvestigationProfile'] = None
) -> Domain:
    """
    Infer domain based on profile strategy (NO KEYWORD MATCHING).
    
    Uses profile.strategy.domain_detection to determine approach:
    - DECLARED: Domain must be in context['domain']
    - REASONING: Use genuine AI reasoning (future: call LLM)
    - PLUGIN_ASSISTED: Get hints from plugins, AI decides
    - HYBRID: Mix of reasoning and plugins (current default)
    - EMERGENT: Start generic, let domain emerge
    """
    if profile is None:
        from empirica.config.profile_loader import load_profile
        profile = load_profile('balanced')
    
    strategy = profile.strategy.domain_detection
    
    if strategy.value == 'declared':
        # Domain must be explicitly declared
        domain = context.get('domain')
        if not domain:
            raise ValueError("Domain must be declared for this profile")
        return Domain[domain.upper()]
    
    elif strategy.value == 'reasoning':
        # Future: Call LLM to reason about domain
        # For now, fall through to hybrid
        pass
    
    elif strategy.value == 'emergent':
        # Start generic, let domain emerge through investigation
        return Domain.GENERAL
    
    # HYBRID or fallback: Use context clues (not keywords!)
    # Check for explicit hints in context
    if 'domain_hint' in context:
        try:
            return Domain[context['domain_hint'].upper()]
        except (KeyError, AttributeError):
            pass
    
    # Default to GENERAL
    return Domain.GENERAL
```

**Validation:**
```bash
python3 -c "
from empirica.investigation.investigation_strategy import BaseInvestigationStrategy, Domain
from empirica.config.profile_loader import load_profile

strategy = BaseInvestigationStrategy()
profile = load_profile('high_reasoning_collaborative')

# Test declared domain
context = {'domain': 'code_analysis'}
domain = strategy.infer_domain('test task', context, profile)
print(f'✓ Domain inference works: {domain}')
"
```

---

#### Task 4.2: Update Tool Recommendation Method (Lines 186-241)

**Add profile parameter to method signature:**
```python
def recommend_tools(
    self,
    gaps: List[KnowledgeGap],
    profile: Optional['InvestigationProfile'] = None
) -> List[ToolRecommendation]:
    """
    Recommend tools based on gaps and profile mode.
    
    Profile determines HOW tools are presented:
    - light: Minimal suggestions, AI explores
    - suggestive: Suggestions provided, AI decides
    - guided: Strong guidance, AI should follow
    - prescribed: Specific approved tools only
    """
    if profile is None:
        from empirica.config.profile_loader import load_profile
        profile = load_profile('balanced')
    
    mode = profile.investigation.tool_suggestion_mode
    
    # Get tool recommendations (existing logic)
    recommendations = self._generate_base_recommendations(gaps)
    
    # Annotate based on profile mode
    for rec in recommendations:
        rec.is_required = (mode.value == 'prescribed')
        rec.is_suggestion = (mode.value in ['light', 'suggestive'])
        rec.can_override = profile.investigation.allow_novel_approaches
    
    return recommendations
```

---

## Phase 5: Update MCP Server

### File: `mcp_local/empirica_mcp_server.py`

#### Task 5.1: Update `bootstrap_session` Tool (Around Line 335)

**Add new parameters to tool definition:**
```python
types.Tool(
    name="bootstrap_session",
    description="Initialize new Empirica session with profile support",
    inputSchema={
        "type": "object",
        "properties": {
            "ai_id": {"type": "string"},
            "session_type": {"type": "string"},
            "profile": {"type": "string"},  # NEW
            "ai_model": {"type": "string"},  # NEW
            "domain": {"type": "string"},    # NEW
        },
        "required": ["ai_id", "session_type"]
    }
)
```

**Update implementation to use profile:**
```python
profile = arguments.get("profile")
ai_model = arguments.get("ai_model")
domain = arguments.get("domain")

# Add to session metadata
metadata['profile'] = profile or 'auto-selected'
metadata['ai_model'] = ai_model
metadata['domain'] = domain
```

---

## Phase 6: Update CLI

### File: `empirica/cli/command_handlers/bootstrap_commands.py`

#### Task 6.1: Add Profile Options

**Add to bootstrap command:**
```python
@click.option('--profile', help='Investigation profile name')
@click.option('--ai-model', help='AI model for auto-selection')
@click.option('--domain', help='Domain context (medical, research, etc.)')
def bootstrap(session_type, profile, ai_model, domain):
    """Bootstrap Empirica session with profile"""
    # Pass to cascade initialization
```

#### Task 6.2: Add Profile Management Commands

**Create new command group:**
```python
@click.group()
def profile():
    """Manage investigation profiles"""
    pass

@profile.command('list')
def list_profiles():
    """List available profiles"""
    from empirica.config.profile_loader import get_profile_loader
    loader = get_profile_loader()
    for name in loader.list_profiles():
        profile_obj = loader.get_profile(name)
        click.echo(f"{name}: {profile_obj.description}")

@profile.command('show')
@click.argument('profile_name')
def show_profile(profile_name):
    """Show profile details"""
    from empirica.config.profile_loader import load_profile
    import json
    profile_obj = load_profile(profile_name)
    click.echo(json.dumps(profile_obj.to_dict(), indent=2))
```

---

## Validation Strategy

### After Each Phase:

1. **Run imports test:**
```bash
python3 -c "from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade; print('✓ Imports work')"
```

2. **Run unit tests:**
```bash
cd /home/yogapad/empirical-ai/empirica
python3 -m pytest tests/unit/ -v -k "cascade or canonical" --tb=short
```

3. **Test profile loading:**
```bash
python3 -c "
from empirica.config.profile_loader import select_profile

# Test each profile loads
for name in ['high_reasoning_collaborative', 'autonomous_agent', 'critical_domain', 'exploratory', 'balanced']:
    p = select_profile(explicit_profile=name)
    print(f'✓ {name}: max_rounds={p.investigation.max_rounds}, threshold={p.investigation.confidence_threshold}')
"
```

4. **Test CASCADE with profile:**
```bash
python3 -c "
import asyncio
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

async def test():
    cascade = CanonicalEpistemicCascade(
        profile_name='balanced',
        enable_session_db=False
    )
    print(f'✓ CASCADE initialized with profile: {cascade.profile.name}')

asyncio.run(test())
"
```

---

## Pattern Summary

### Find and Replace Patterns:

**Pattern 1: Hardcoded max_rounds**
- Find: `self.max_investigation_rounds`
- Replace: `self.profile.investigation.max_rounds`
- Note: Handle `None` case (unlimited rounds)

**Pattern 2: Hardcoded threshold**
- Find: `self.action_confidence_threshold`
- Replace: `self.profile.investigation.confidence_threshold`

**Pattern 3: Magic number thresholds**
- Find: `> 0.80`, `< 0.50`, `>= 0.70`, etc.
- Replace: `> profile.action_thresholds.uncertainty_high`, etc.

**Pattern 4: confidence_gain values**
- Find: `'confidence_gain': 0.XX`
- Replace: `'confidence_gain': 0.0  # No artificial gain`

---

## Success Criteria

✅ All hardcoded constraints replaced with profile references
✅ Backward compatibility maintained (deprecated warnings)
✅ Unit tests pass
✅ Can initialize CASCADE with different profiles
✅ Profile selection logic works (by AI model, domain, explicit)
✅ No `grep` matches for hardcoded magic numbers
✅ Documentation updated

---

## Notes for Minimax

- **This is mechanical work** - clear patterns, well-specified
- **Test after each phase** - don't wait until the end
- **Use grep extensively** - find all instances of patterns
- **Keep backward compatibility** - add deprecation warnings, don't break old code
- **Focus on correctness** - this is refactoring, not new features

---

## Handoff Checklist

Before handing back to Claude:

- [ ] All files modified are listed in commit message
- [ ] All tests pass
- [ ] Validation commands all succeed
- [ ] No hardcoded constraints remain (grep verification)
- [ ] Documentation updated (if needed)
- [ ] Ready for Claude to review and proceed with Phases 7-9

---

## Questions?

If you encounter ambiguity:
1. Check the implementation spec: `docs/reference/INVESTIGATION_PROFILE_SYSTEM_SPEC.md`
2. Check the profile YAML: `empirica/config/investigation_profiles.yaml`
3. Check the profile loader: `empirica/config/profile_loader.py`
4. Default to the `balanced` profile for fallback cases

**Good luck, Minimax! This is well-specified, systematic work. You've got this! 🚀**
