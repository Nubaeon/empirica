# Dynamic Threshold Configuration - Implementation Plan

**Date:** 2025-01-XX  
**Status:** Ready to implement  
**Estimated:** 8-12 iterations  
**Priority:** HIGH (enables Sentinel orchestration)

---

## 🎯 Objective

Enable Sentinel/Lead AI to dynamically control epistemic thresholds via YAML configuration, allowing:
- Different profiles for different task types (exploration vs production)
- Runtime switching without code changes
- Per-session or per-AI customization
- Intelligent routing based on threshold profiles

---

## 📊 Current vs Proposed

### Current State ❌
```python
# Hardcoded in empirica/core/thresholds.py
ENGAGEMENT_THRESHOLD = 0.60
CRITICAL_THRESHOLDS = {
    'coherence_min': 0.50,
    'density_max': 0.90,
    'change_min': 0.50
}
```

**Problems:**
- Cannot adapt to task context
- Cannot tune for AI capability
- Sentinel has no control
- Requires code changes to adjust

### Proposed State ✅
```yaml
# empirica/config/threshold_profiles.yaml
profiles:
  default: {engagement_threshold: 0.60, ...}
  exploratory: {engagement_threshold: 0.50, ...}  # Lower barriers
  rigorous: {engagement_threshold: 0.70, ...}     # Higher standards
  rapid: {engagement_threshold: 0.50, ...}        # Fast iteration
  expert: {engagement_threshold: 0.70, ...}       # High capability
  novice: {engagement_threshold: 0.50, ...}       # Learning support
```

**Benefits:**
- ✅ Task-specific profiles
- ✅ Runtime switching
- ✅ Sentinel control via MCP
- ✅ No code changes needed

---

## 🏗️ Architecture

### 1. Configuration File
**Location:** `empirica/config/threshold_profiles.yaml`

**Structure:**
```yaml
profiles:
  {profile_name}:
    name: "Display Name"
    description: "When to use this"
    engagement_threshold: 0.60
    critical:
      coherence_min: 0.50
      density_max: 0.90
      change_min: 0.50
    uncertainty:
      low: 0.70
      moderate: 0.30
      high: 0.70
    # ... all thresholds organized by category
```

### 2. Loader Class
**Location:** `empirica/config/threshold_loader.py`

**Responsibilities:**
- Load YAML configuration
- Switch profiles at runtime
- Allow per-session overrides
- Create custom profiles
- Fallback to hardcoded values

**API:**
```python
config = ThresholdConfig()
config.load_profile('exploratory')
threshold = config.get('engagement_threshold')
config.override('uncertainty.high', 0.65)
```

### 3. Updated Core Module
**Location:** `empirica/core/thresholds.py` (modified)

**Changes:**
- Import from threshold_loader
- Convert constants to properties or functions
- Maintain backwards compatibility
- Fallback to hardcoded on failure

### 4. MCP Tools
**Location:** `mcp_local/empirica_mcp_server.py`

**New Tools:**
- `list_threshold_profiles` - Show available profiles
- `load_threshold_profile` - Switch profile
- `override_threshold` - Override specific value
- `create_custom_threshold_profile` - Create custom
- `get_current_threshold_config` - Show current config

---

## 📋 Implementation Tasks

### Phase 1: Configuration File (2 iterations)

#### Task 1.1: Create threshold_profiles.yaml
- [ ] Create `empirica/config/threshold_profiles.yaml`
- [ ] Define 6 profiles: default, exploratory, rigorous, rapid, expert, novice
- [ ] Map all 20+ hardcoded thresholds
- [ ] Add metadata (version, default profile)
- [ ] Document each profile's use case

**Files:**
- `empirica/config/threshold_profiles.yaml` (new)

#### Task 1.2: Create ThresholdConfig class
- [ ] Create `empirica/config/threshold_loader.py`
- [ ] Implement YAML loading
- [ ] Implement profile switching
- [ ] Implement override mechanism
- [ ] Implement custom profile creation
- [ ] Add fallback to hardcoded values
- [ ] Add logging

**Files:**
- `empirica/config/threshold_loader.py` (new)

---

### Phase 2: Core Integration (3 iterations)

#### Task 2.1: Update thresholds.py
- [ ] Import ThresholdConfig
- [ ] Convert constants to dynamic lookups
- [ ] Maintain backwards compatibility
- [ ] Add fallback logic
- [ ] Update docstrings

**Current:**
```python
ENGAGEMENT_THRESHOLD = 0.60
```

**New:**
```python
def get_engagement_threshold():
    return get_threshold_config().get('engagement_threshold', 0.60)
```

**Files:**
- `empirica/core/thresholds.py` (modified)

#### Task 2.2: Update imports across codebase
- [ ] Find all `from empirica.core.thresholds import ENGAGEMENT_THRESHOLD`
- [ ] Convert to function calls if needed
- [ ] Or keep as module-level property
- [ ] Test all imports work

**Files:**
- `empirica/core/canonical/canonical_epistemic_assessment.py`
- `empirica/core/canonical/reflex_frame.py`
- `empirica/core/canonical/__init__.py`
- `empirica/core/metacognitive_cascade/metacognitive_cascade.py`

#### Task 2.3: Add unit tests
- [ ] Test YAML loading
- [ ] Test profile switching
- [ ] Test overrides
- [ ] Test fallback behavior
- [ ] Test custom profiles

**Files:**
- `tests/unit/config/test_threshold_loader.py` (new)

---

### Phase 3: MCP Tools (2 iterations)

#### Task 3.1: Add MCP tool definitions
- [ ] Define 5 new tools in MCP server
- [ ] Add input schemas
- [ ] Map to CLI commands or Python API
- [ ] Add tool descriptions

**Files:**
- `mcp_local/empirica_mcp_server.py` (modified)

#### Task 3.2: Add CLI commands
- [ ] `empirica thresholds-list` - List profiles
- [ ] `empirica thresholds-load <profile>` - Load profile
- [ ] `empirica thresholds-show` - Show current config
- [ ] `empirica thresholds-override <path> <value>` - Override value

**Files:**
- `empirica/cli/command_handlers/config_commands.py` (modified or new)

---

### Phase 4: Testing & Documentation (3 iterations)

#### Task 4.1: Integration testing
- [ ] Test profile switching affects CASCADE behavior
- [ ] Test session-specific overrides
- [ ] Test Sentinel can control via MCP
- [ ] Test fallback when YAML missing
- [ ] Test backwards compatibility

**Files:**
- `tests/integration/test_dynamic_thresholds.py` (new)

#### Task 4.2: Create documentation
- [ ] User guide for threshold profiles
- [ ] Sentinel orchestration examples
- [ ] Profile selection guide
- [ ] Migration guide
- [ ] API reference

**Files:**
- `docs/guides/THRESHOLD_PROFILES_GUIDE.md` (new)
- `docs/guides/SENTINEL_THRESHOLD_CONTROL.md` (new)

#### Task 4.3: Update existing docs
- [ ] Update architecture docs
- [ ] Update MCP tool catalog
- [ ] Update Sentinel orchestration guide
- [ ] Update system prompts if needed

---

## 🎯 Profile Definitions

### Profile: default (Balanced)
```yaml
engagement_threshold: 0.60
uncertainty.high: 0.70
cascade.max_investigation_rounds: 7
check_confidence_to_proceed: 0.70
```
**Use:** General purpose, balanced approach

### Profile: exploratory (Research)
```yaml
engagement_threshold: 0.50  # Lower barrier
uncertainty.high: 0.60      # Investigate sooner
cascade.max_investigation_rounds: 10  # More rounds
check_confidence_to_proceed: 0.60
```
**Use:** Research, prototyping, learning new domains

### Profile: rigorous (Production)
```yaml
engagement_threshold: 0.70  # Higher bar
uncertainty.high: 0.80      # Tolerate less uncertainty
cascade.max_investigation_rounds: 5  # Fewer rounds
check_confidence_to_proceed: 0.85
```
**Use:** Production code, critical systems, high stakes

### Profile: rapid (Fast Iteration)
```yaml
engagement_threshold: 0.50
uncertainty.high: 0.50      # Less investigation
cascade.max_investigation_rounds: 3  # Fast cycles
check_confidence_to_proceed: 0.50
```
**Use:** Prototyping, quick experiments, throwaway code

### Profile: expert (High Capability)
```yaml
engagement_threshold: 0.70
uncertainty.high: 0.85      # High bar for investigation
cascade.max_investigation_rounds: 5
check_confidence_to_proceed: 0.80
```
**Use:** Experienced AIs with high domain knowledge

### Profile: novice (Learning)
```yaml
engagement_threshold: 0.50  # Lower barrier
uncertainty.high: 0.50      # Investigate early
cascade.max_investigation_rounds: 12  # More learning
check_confidence_to_proceed: 0.55
```
**Use:** Learning AIs, unfamiliar domains

---

## 🔧 Technical Decisions

### Decision 1: Backwards Compatibility
**Approach:** Keep hardcoded values as fallbacks

**Rationale:**
- If YAML fails to load, system still works
- Existing code doesn't break
- Gradual migration possible

**Implementation:**
```python
def get_threshold(key, default_value):
    try:
        return config.get(key)
    except:
        return default_value
```

### Decision 2: Import Style
**Approach:** Functions instead of constants

**Rationale:**
- Dynamic lookup at runtime
- No import-time dependencies
- Easy to test

**Implementation:**
```python
# OLD
from empirica.core.thresholds import ENGAGEMENT_THRESHOLD

# NEW
from empirica.core.thresholds import get_engagement_threshold
threshold = get_engagement_threshold()
```

### Decision 3: Override Scope
**Approach:** Session-specific overrides

**Rationale:**
- Multiple AIs can have different configs
- Changes don't affect other sessions
- Scoped to session lifecycle

**Implementation:**
```python
config.override('uncertainty.high', 0.65, session_id='abc-123')
```

---

## 📊 Success Metrics

### Functionality
- [ ] All 6 profiles load correctly
- [ ] Profile switching works at runtime
- [ ] Overrides apply correctly
- [ ] MCP tools functional
- [ ] Backwards compat maintained

### Performance
- [ ] Config load time < 10ms
- [ ] Threshold lookup < 1ms
- [ ] No performance regression

### Usability
- [ ] Sentinel can switch profiles via MCP
- [ ] Clear documentation
- [ ] Easy to add new profiles

---

## 🚀 Usage Examples

### Example 1: Sentinel Routes by Task Type
```python
# Via MCP
load_threshold_profile(
    profile_name="exploratory",
    session_id="research-task-123"
)

# AI runs CASCADE with exploratory thresholds
# - Lower engagement barrier (0.50)
# - More investigation rounds (10)
# - Higher uncertainty tolerance
```

### Example 2: Project Phase Transition
```python
# Phase 1: Prototyping
load_threshold_profile("rapid")

# Phase 2: Development
load_threshold_profile("default")

# Phase 3: Production
load_threshold_profile("rigorous")
```

### Example 3: AI-Specific Configuration
```python
# Expert AI
load_threshold_profile("expert", session_id="expert-ai")

# Novice AI
load_threshold_profile("novice", session_id="novice-ai")
```

### Example 4: Fine-Tuned Control
```python
# Start with default
load_threshold_profile("default")

# Override specific threshold for this task
override_threshold(
    threshold_path="uncertainty.high",
    value=0.60,
    session_id="task-123"
)
```

---

## 📝 Files to Create/Modify

### New Files (3)
1. `empirica/config/threshold_profiles.yaml` (~300 lines)
2. `empirica/config/threshold_loader.py` (~400 lines)
3. `tests/unit/config/test_threshold_loader.py` (~200 lines)
4. `tests/integration/test_dynamic_thresholds.py` (~150 lines)
5. `docs/guides/THRESHOLD_PROFILES_GUIDE.md` (~400 lines)
6. `docs/guides/SENTINEL_THRESHOLD_CONTROL.md` (~300 lines)

### Modified Files (4)
1. `empirica/core/thresholds.py` (~100 line changes)
2. `mcp_local/empirica_mcp_server.py` (+50 lines for tools)
3. `empirica/cli/command_handlers/config_commands.py` (+100 lines)
4. Various imports in canonical/cascade files (~20 files, minor changes)

---

## ⚠️ Risks & Mitigation

### Risk 1: Config File Corruption
**Mitigation:** Fallback to hardcoded values, YAML validation

### Risk 2: Import Breaking Changes
**Mitigation:** Maintain backwards compat, gradual migration

### Risk 3: Performance Impact
**Mitigation:** Lazy loading, caching, minimal overhead

### Risk 4: Complexity
**Mitigation:** Clear documentation, sensible defaults

---

## 🎯 Next Steps

**Ready to implement?**

1. **Review this plan** - Any adjustments needed?
2. **Start Phase 1** - Create YAML and loader
3. **Test incrementally** - Verify each phase
4. **Document thoroughly** - Enable Sentinel usage

**Estimated:** 8-12 iterations total  
**Breaking Changes:** None (backwards compatible)  
**Impact:** HIGH (enables dynamic Sentinel orchestration)

---

**Status:** ✅ Plan ready for implementation  
**Approval Needed:** Confirm approach before starting  
**Questions:** Any concerns or alternative approaches?

---

*"Dynamic configuration is the bridge between rigid code and flexible intelligence."* ✨
