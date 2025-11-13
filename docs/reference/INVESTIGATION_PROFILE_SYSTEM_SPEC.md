# Investigation Profile System - Implementation Specification

**Version:** 1.0  
**Date:** 2024  
**Status:** Ready for Implementation  
**Purpose:** Complete specification for profile-based investigation system

---

## Executive Summary

This specification documents the complete profile-based investigation system that replaces hardcoded constraints with context-aware, configurable investigation guidance. This document serves as the definitive reference for implementation, handoff, and future maintenance.

### Key Changes:
- **Replace 14 hardcoded constraints** with flexible profile system
- **Add 5 investigation profiles** (high_reasoning, autonomous, critical, exploratory, balanced)
- **Fix database schema bug** (uncertainty columns)
- **Enable context-aware investigation** (AI type + domain)
- **Preserve safety** (universal constraints always enforced)

### Files Created:
- `empirica/config/investigation_profiles.yaml` (418 lines)
- `empirica/config/profile_loader.py` (391 lines)
- `docs/reference/CANONICAL_DIRECTORY_STRUCTURE.md` (600+ lines)
- `docs/reference/ARCHITECTURE_OVERVIEW.md` (650+ lines)

### Implementation Status:
- ✅ Phase 1: Core infrastructure (COMPLETE)
- 🔄 Phase 2-6: Code refactoring (READY TO START)
- 📋 Phase 7-9: Testing, docs, dashboard (PLANNED)

---

## Problem Statement

### Current Issues (14 Anomalies Identified):

**Investigation Constraints:**
1. `max_investigation_rounds = 3` - Hardcoded, prevents deep investigation
2. `action_confidence_threshold = 0.70` - Fixed threshold ignores context
3. Priority filtering - Only 'critical'/'high' gaps trigger investigation

**Action Determination:**
4. `uncertainty > 0.80 → INVESTIGATE` - Magic number
5. `clarity < 0.50 → CLARIFY` - Magic number  
6. `foundation < 0.50 → INVESTIGATE` - Magic number
7. `confidence ≥ 0.70 → PROCEED` - Magic number

**Investigation Strategy:**
8. Keyword-based domain detection - Not genuine reasoning
9. Hardcoded gap→tool mappings - Predetermined
10. Hardcoded tool confidence (0.85, 0.80) - Artificial values

**Fake Learning:**
11. Confidence gain = +0.15 per tool - Simulated
12. POSTFLIGHT boost = rounds × 0.05 - Fake calculation

**Gate Thresholds:**
13. ENGAGEMENT_THRESHOLD = 0.60 - Universal but not configurable
14. CRITICAL_THRESHOLDS - Hardcoded RESET/STOP triggers

### Root Cause:
**Philosophical contradiction** between "no heuristics" principle and hardcoded constraints that force AI into narrow investigation patterns.

---

## Solution Architecture

### Three-Layer Constraint System:

```
┌─────────────────────────────────────────┐
│  Universal Constraints                   │
│  (Sentinel-enforced, always apply)       │
│  - Engagement gate, timeouts, etc.       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Investigation Profile                   │
│  (Context-specific, configurable)        │
│  - Max rounds, confidence thresholds     │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Plugin Suggestions                      │
│  (User-provided, suggestive)             │
│  - Custom tools, domain strategies       │
└─────────────────────────────────────────┘
                  ↓
         AI Makes Final Decision
```

### Design Principles:

1. **Context-Aware:** Different AI types and domains get appropriate constraints
2. **Configurable:** YAML-based profiles, easily customizable
3. **Safe:** Universal constraints always enforced (Sentinel)
4. **Extensible:** Plugin system for custom investigation tools
5. **Transparent:** All constraints visible in profiles, not buried in code

---

## Core Components

### 1. Investigation Profiles (YAML Configuration)

**Location:** `empirica/config/investigation_profiles.yaml`

**Structure:**
```yaml
universal_constraints:      # Always enforced
  engagement_gate: 0.60
  coherence_min: 0.50
  max_tool_calls_per_round: 10
  investigation_timeout_seconds: 3600

profiles:
  high_reasoning_collaborative:
    investigation:
      max_rounds: null           # Unlimited
      confidence_threshold: "dynamic"  # AI decides
    action_thresholds:
      uncertainty_high: 0.75
      override_allowed: true     # AI can override
    tuning:
      confidence_weight: 1.0
      foundation_weight: 1.0
  
  # ... 4 more profiles
```

**5 Profiles:**
1. **high_reasoning_collaborative** - For Claude, GPT-4, o1 (max autonomy)
2. **autonomous_agent** - For smaller models (structured)
3. **critical_domain** - For medical/legal (strict)
4. **exploratory** - For research (max freedom)
5. **balanced** - Default (middle ground)

### 2. Profile Loader (Python Implementation)

**Location:** `empirica/config/profile_loader.py`

**Key Classes:**
- `InvestigationProfile` - Complete profile data
- `ProfileLoader` - Load, validate, select profiles
- `InvestigationConstraints` - Investigation settings
- `ActionThresholds` - Action determination thresholds
- `TuningParameters` - Confidence weight tuning

**Key Functions:**
```python
# Auto-select profile
profile = select_profile(
    ai_model='claude-sonnet',
    domain='medical'
)

# Explicit load
profile = load_profile('high_reasoning_collaborative')

# Get singleton loader
loader = get_profile_loader()
```

**Profile Selection Logic:**
1. Explicit profile (user-specified) → Use it
2. Domain-based (if domain declared) → Select by domain
3. AI capability (from model name) → Select by AI type
4. Default → Use 'balanced' profile

---

## Implementation Phases

### Phase 1: Core Infrastructure ✅ COMPLETE

**Deliverables:**
- [x] `investigation_profiles.yaml` created
- [x] `profile_loader.py` created
- [x] Profile selection logic implemented
- [x] Documentation created

### Phase 2: Refactor Metacognitive Cascade

**Files to Modify:**
- `empirica/core/metacognitive_cascade/metacognitive_cascade.py`

**Changes:**

1. **Update `__init__` signature:**
```python
# OLD (deprecated):
def __init__(
    self,
    max_investigation_rounds: int = 3,
    action_confidence_threshold: float = 0.70,
    ...
):

# NEW:
def __init__(
    self,
    profile_name: Optional[str] = None,
    ai_model: Optional[str] = None,
    domain: Optional[str] = None,
    # Deprecated (backward compat):
    max_investigation_rounds: Optional[int] = None,
    action_confidence_threshold: Optional[float] = None,
    ...
):
    # Load profile
    self.profile = select_profile(
        ai_model=ai_model,
        domain=domain,
        explicit_profile=profile_name
    )
    
    # Backward compat overrides
    if max_investigation_rounds is not None:
        self.profile.investigation.max_rounds = max_investigation_rounds
```

2. **Update investigation loop (Line 536-570):**
```python
# OLD:
while investigation_rounds < self.max_investigation_rounds:
    confidence_low = current_assessment.overall_confidence < self.action_confidence_threshold

# NEW:
max_rounds = self.profile.investigation.max_rounds
while max_rounds is None or investigation_rounds < max_rounds:
    # Dynamic threshold support
    if self.profile.investigation.confidence_threshold_dynamic:
        threshold = self._calculate_dynamic_threshold(current_assessment)
    else:
        threshold = self.profile.investigation.confidence_threshold
    
    confidence_low = current_assessment.overall_confidence < threshold
```

3. **Remove fake learning (Line 866):**
```python
# OLD:
learning_boost = min(0.15, investigation_rounds * 0.05)
know=VectorState(min(0.75, 0.55 + learning_boost), ...)

# NEW:
if self.profile.learning.postflight_mode == PostflightMode.GENUINE_REASSESSMENT:
    # No artificial boost - genuine reassessment only
    pass
```

### Phase 3: Refactor Canonical Assessment

**Files to Modify:**
- `empirica/core/canonical/canonical_epistemic_assessment.py`

**Changes:**

1. **Update `_determine_recommended_action` (Line 822-840):**
```python
# OLD:
if uncertainty.score > 0.80:  # Hardcoded
    return Action.INVESTIGATE

# NEW:
def _determine_recommended_action(
    self,
    vectors: Dict[str, Any],
    profile: InvestigationProfile
) -> Action:
    thresholds = profile.action_thresholds
    
    if uncertainty.score > thresholds.uncertainty_high:
        action = Action.INVESTIGATE
        if thresholds.override_allowed:
            action.note = "Suggested (AI can override with rationale)"
        return action
```

2. **Add weighted confidence calculation:**
```python
def _calculate_weighted_confidence(
    self,
    foundation: float,
    comprehension: float,
    execution: float,
    uncertainty: float,
    tuning: TuningParameters
) -> float:
    # Apply profile tuning weights
    base_weights = {
        'foundation': 0.30,
        'comprehension': 0.25,
        'execution': 0.25,
        'uncertainty': 0.20,
    }
    
    tuned_weights = {
        'foundation': base_weights['foundation'] * tuning.foundation_weight,
        'comprehension': base_weights['comprehension'] * tuning.comprehension_weight,
        'execution': base_weights['execution'] * tuning.execution_weight,
        'uncertainty': base_weights['uncertainty'] * tuning.uncertainty_weight,
    }
    
    # Normalize and calculate
    total = sum(tuned_weights.values())
    normalized = {k: v/total for k, v in tuned_weights.items()}
    
    return (
        foundation * normalized['foundation'] +
        comprehension * normalized['comprehension'] +
        execution * normalized['execution'] +
        (1.0 - uncertainty) * normalized['uncertainty']
    ) * tuning.confidence_weight
```

### Phase 4: Refactor Investigation Strategy

**Files to Modify:**
- `empirica/investigation/investigation_strategy.py`

**Changes:**

1. **Remove keyword-based domain detection (Line 423-448):**
```python
# OLD:
def infer_domain(self, task: str, context: Dict[str, Any]) -> Domain:
    task_lower = task.lower()
    if any(kw in task_lower for kw in ['refactor', 'code']):
        return Domain.CODE_ANALYSIS

# NEW:
def infer_domain(
    self,
    task: str,
    context: Dict[str, Any],
    profile: InvestigationProfile
) -> Domain:
    strategy = profile.strategy.domain_detection
    
    if strategy == DomainDetection.DECLARED:
        return Domain[context['domain'].upper()]
    elif strategy == DomainDetection.REASONING:
        return self._ai_infer_domain(task, context)
    elif strategy == DomainDetection.PLUGIN_ASSISTED:
        hints = self._get_plugin_hints(task, context)
        return self._ai_infer_with_hints(task, context, hints)
    else:  # HYBRID
        return self._hybrid_detection(task, context)
```

2. **Make tool recommendations profile-driven (Line 186-241):**
```python
# OLD:
if gap_name == 'know':
    recommendations.append(ToolRecommendation(
        tool_name='codebase_search',
        confidence=0.85,  # Hardcoded
        ...
    ))

# NEW:
def recommend_tools(
    self,
    gaps: List[KnowledgeGap],
    profile: InvestigationProfile
) -> List[ToolRecommendation]:
    mode = profile.investigation.tool_suggestion_mode
    
    if mode == ToolSuggestionMode.PRESCRIBED:
        return self._get_prescribed_tools(gaps, profile)
    elif mode == ToolSuggestionMode.LIGHT:
        return self._get_light_suggestions(gaps)
    else:  # SUGGESTIVE, GUIDED
        suggestions = self._get_standard_suggestions(gaps)
        for tool in suggestions:
            tool.is_suggestion = True
            tool.can_override = profile.investigation.allow_novel_approaches
        return suggestions
```

### Phase 5: Remove Artificial Confidence Calculations

**Files to Modify:**
- `empirica/core/metacognitive_cascade/mcp_aware_investigation.py`

**Changes:**

1. **Update confidence gain estimation (Line 389-393):**
```python
# OLD:
def _estimate_confidence_gain(self, results):
    successful = sum(1 for r in results if r['success'])
    return min(successful * 0.15, 0.5)  # Fake

# NEW:
def _estimate_confidence_gain(
    self,
    results: List[Dict],
    profile: InvestigationProfile
) -> Optional[float]:
    calc_mode = profile.learning.confidence_gain_calculation
    
    if calc_mode == "none":
        return None  # Genuine reassessment only
    elif calc_mode == "evidence_based":
        evidence_quality = self._assess_evidence(results)
        gap_coverage = self._calculate_coverage(results)
        return evidence_quality * gap_coverage * 0.3
    elif calc_mode == "conservative":
        successful = sum(1 for r in results if r['success'])
        return min(successful * 0.05, 0.15)  # Max +0.15
    else:
        return None
```

### Phase 6: Integration

**Files to Modify:**
- `mcp_local/empirica_mcp_server.py`
- `empirica/cli/cli_core.py`

**Changes:**

**MCP Server:**
```python
async def bootstrap_session(
    ai_id: str,
    session_type: str,
    profile: Optional[str] = None,  # NEW
    ai_model: Optional[str] = None,  # NEW
    domain: Optional[str] = None,   # NEW
) -> dict:
    """Bootstrap with profile support"""
    selected_profile = select_profile(
        ai_model=ai_model,
        domain=domain,
        explicit_profile=profile
    )
    
    # Add to metadata
    metadata['profile'] = selected_profile.name
    metadata['profile_description'] = selected_profile.description
```

**CLI:**
```python
@click.command()
@click.option('--profile', help='Investigation profile')
@click.option('--ai-model', help='AI model for auto-selection')
@click.option('--domain', help='Domain context')
def bootstrap(profile, ai_model, domain):
    """Bootstrap session with profile"""
    # ...

@click.group()
def profile():
    """Manage profiles"""
    pass

@profile.command('list')
def list_profiles():
    """List available profiles"""
    loader = get_profile_loader()
    for name in loader.list_profiles():
        click.echo(f"{name}: {profile.description}")
```

### Phase 7: Testing

**Test Files to Create:**
- `tests/unit/config/test_profile_loader.py`
- `tests/unit/config/test_profile_selection.py`
- `tests/integration/test_profile_cascade.py`

**Key Tests:**
1. Profile loading and parsing
2. Profile selection logic
3. Constraint validation
4. CASCADE with different profiles
5. Profile behavior differences
6. Backward compatibility

### Phase 8: Documentation

**Documents to Create/Update:**
- `docs/guides/INVESTIGATION_PROFILES.md` - User guide
- `docs/production/15_CONFIGURATION.md` - Update with profiles
- `docs/reference/QUICK_REFERENCE.md` - Add profile commands
- Migration guide for users

### Phase 9: Dashboard (Future)

**Features:**
- Profile visualization
- Real-time profile tuning
- Investigation pattern analysis
- A/B testing of profiles

---

## Database Schema Fix

**Issue:** Missing columns in `epistemic_assessments` table

**File:** `empirica/data/session_database.py`

**Fix Applied (Line 198):**
```python
CREATE TABLE IF NOT EXISTS epistemic_assessments (
    ...
    execution_confidence REAL,
    
    uncertainty REAL NOT NULL,              # ADDED
    uncertainty_rationale TEXT,             # ADDED
    uncertainty_evidence TEXT,              # ADDED
    
    overall_confidence REAL NOT NULL,
    ...
)
```

**Status:** ✅ FIXED

---

## Vector Format Specification

### Storage Format:
- **Type:** `float`
- **Range:** 0.0 to 1.0
- **Validation:** Enforced at `VectorState` level
- **No percentages** in core system

### Display Format:
- **Internal:** Always floats
- **Reflex Logs:** JSON with floats
- **Dashboard:** Can convert to percentages or color indicators
- **AI Prompts:** Use floats (0.0-1.0)

### Rationale:
- Standard ML/probability range
- No confusion between 0.7 and 70%
- Dashboard handles display conversion
- AIs work better with 0.0-1.0

---

## Backward Compatibility

### Deprecated Parameters:
```python
# These still work but emit deprecation warnings:
cascade = CanonicalEpistemicCascade(
    max_investigation_rounds=5,           # Deprecated
    action_confidence_threshold=0.75      # Deprecated
)

# New way:
cascade = CanonicalEpistemicCascade(
    profile_name='balanced',
    ai_model='claude-sonnet'
)
```

### Migration Path:
1. Old code continues to work (with warnings)
2. Update to profiles at convenience
3. Remove deprecated parameters in v4.0

---

## Configuration Examples

### Example 1: High Reasoning AI
```python
cascade = CanonicalEpistemicCascade(
    profile_name='high_reasoning_collaborative',
    ai_model='claude-sonnet',
    enable_session_db=True
)

result = await cascade.run_epistemic_cascade(
    task='Complex research task requiring deep investigation',
    context={'complexity': 'high'}
)

# AI can investigate as long as needed (no max rounds)
# AI determines confidence threshold dynamically
# Light tool suggestions (AI explores freely)
```

### Example 2: Autonomous Agent
```python
cascade = CanonicalEpistemicCascade(
    profile_name='autonomous_agent',
    ai_model='gpt-3.5-turbo',
    enable_session_db=True
)

# Max 5 investigation rounds
# Fixed 0.70 confidence threshold
# Guided tool suggestions (AI should follow)
```

### Example 3: Critical Domain
```python
cascade = CanonicalEpistemicCascade(
    profile_name='critical_domain',
    domain='medical',
    enable_session_db=True
)

# Max 3 rounds
# 0.90 confidence required
# Prescribed tools only (approved list)
# Full audit trail
```

### Example 4: Auto-Selection
```python
cascade = CanonicalEpistemicCascade(
    ai_model='claude-opus',
    domain='research',
    enable_session_db=True
)

# Auto-selects: high_reasoning_collaborative
# (AI capability takes precedence over domain)
```

---

## Testing Strategy

### Unit Tests:

**Profile System:**
- Load profiles from YAML
- Parse profile data correctly
- Validate constraints
- Select profile by AI model
- Select profile by domain
- Export/import profiles

**Cascade Integration:**
- Initialize with profile
- Use profile constraints in investigation loop
- Apply profile thresholds in action determination
- Respect profile learning mode in POSTFLIGHT

### Integration Tests:

**Complete Workflow:**
- PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT
- With different profiles
- Verify different behaviors

**Profile Comparisons:**
```python
async def test_profile_differences():
    task = "Moderate complexity task"
    
    # Test high reasoning (unlimited investigation)
    cascade_hr = CanonicalEpistemicCascade(profile_name='high_reasoning_collaborative')
    result_hr = await cascade_hr.run_epistemic_cascade(task, {})
    
    # Test autonomous (max 5 rounds)
    cascade_auto = CanonicalEpistemicCascade(profile_name='autonomous_agent')
    result_auto = await cascade_auto.run_epistemic_cascade(task, {})
    
    # Verify differences
    assert result_hr['investigation_rounds'] != result_auto['investigation_rounds']
```

### Comparative Tests:

**Verify Profile Behaviors:**
- High reasoning: Can exceed 3 rounds when needed
- Autonomous: Stops at 5 rounds
- Critical: Requires 0.90 confidence
- Exploratory: Accepts 0.50 confidence

---

## Performance Considerations

### Profile Loading:
- YAML parsed once at initialization
- Singleton pattern for `ProfileLoader`
- Cached in memory
- Negligible overhead (~1ms)

### Runtime Impact:
- Profile checks are simple property accesses
- No performance degradation
- Same or better than hardcoded values

### Memory:
- ~5KB per profile in memory
- Total: ~25KB for 5 profiles
- Negligible impact

---

## Security and Validation

### Profile Validation:
- YAML schema validated on load
- Vector scores validated (0.0-1.0 range)
- Profile constraints validated against universal constraints
- Invalid profiles rejected with clear error messages

### Universal Constraints:
- Always enforced (cannot be disabled)
- Sentinel will enforce at runtime (future)
- Prevent runaway processes
- Ensure minimum engagement/coherence

### Plugin Safety:
- Plugins are user-provided (trust model)
- Future: Sandbox plugin execution
- Future: Plugin approval workflow for critical domains

---

## Monitoring and Observability

### Metrics to Track:
- Profile selection distribution
- Investigation rounds by profile
- Confidence thresholds hit/miss
- Tool suggestion acceptance rate
- Profile override frequency

### Logging:
- Profile selection logged at bootstrap
- Profile constraints logged at investigation start
- Threshold comparisons logged at CHECK phase
- Override decisions logged with rationale

### Dashboard (Future):
- Real-time profile usage visualization
- Investigation pattern analysis
- Profile effectiveness comparison
- A/B testing results

---

## Future Enhancements

### Sentinel Integration:
- Runtime constraint enforcement
- Policy violation detection
- Escalation protocols
- Audit trail generation

### Bayesian Guardian Integration:
- Adaptive profile tuning
- Calibration-based weight adjustment
- Profile effectiveness tracking
- Automatic profile recommendations

### Cognitive Vault Integration:
- AI capability assessment
- Optimal profile recommendation
- Capability change tracking
- Persona detection

### Dashboard Features:
- Interactive profile tuning
- Visual constraint editor
- Investigation pattern visualization
- Profile comparison tool

---

## Frequently Asked Questions

### Q: Why not just use one profile for all AIs?
**A:** Different AI types and domains need different constraints. High reasoning AIs need autonomy, autonomous agents need structure, critical domains need strict compliance.

### Q: Can users create custom profiles?
**A:** Yes! Copy an existing profile in the YAML, modify values, and reference it by name.

### Q: What if profile YAML is missing?
**A:** Profile loader falls back to 'balanced' profile with sensible defaults.

### Q: Do plugins work with profiles?
**A:** Yes! Profiles control HOW plugins are suggested (light, guided, prescribed).

### Q: Can AI override profile constraints?
**A:** Depends on profile. `high_reasoning` allows overrides with rationale, `critical_domain` does not.

### Q: How do I tune a profile for my use case?
**A:** Edit `investigation_profiles.yaml` or create custom profile. Main tuner is `confidence_weight`, sub-tuners are `foundation_weight`, etc.

### Q: Will this break existing code?
**A:** No. Old parameters still work (with deprecation warnings). Migrate at your convenience.

---

## References

### Related Documents:
- `CANONICAL_DIRECTORY_STRUCTURE.md` - File locations
- `ARCHITECTURE_OVERVIEW.md` - System architecture
- `investigation_profiles.yaml` - Profile configuration
- `profile_loader.py` - Implementation
- `tmp_rovodev_investigation_anomalies.md` - Original analysis
- `tmp_rovodev_implementation_plan.md` - Detailed implementation plan

### Key Code Locations:
- Profiles: `empirica/config/investigation_profiles.yaml`
- Loader: `empirica/config/profile_loader.py`
- CASCADE: `empirica/core/metacognitive_cascade/metacognitive_cascade.py`
- Assessment: `empirica/core/canonical/canonical_epistemic_assessment.py`
- Strategy: `empirica/investigation/investigation_strategy.py`

---

## Version History

### v1.0 (Current)
- Initial specification
- 5 profiles defined
- Implementation plan documented
- Database schema fix applied

---

## Approval and Sign-off

**Specification Status:** ✅ READY FOR IMPLEMENTATION  
**Review Status:** Awaiting developer review  
**Implementation Start:** Ready to proceed with Phase 2  

**Next Steps:**
1. Review specification
2. Begin Phase 2 implementation (Metacognitive Cascade)
3. Write unit tests alongside implementation
4. Update documentation as implementation progresses

---

**End of Specification**
