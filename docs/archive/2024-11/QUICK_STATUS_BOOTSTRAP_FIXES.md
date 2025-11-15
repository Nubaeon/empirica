# Quick Status: Bootstrap Fixes Needed

**Date:** 2025-11-14  
**Status:** Analysis complete, ready for implementation

---

## ✅ What We Fixed Today

1. **Import errors** - All relative imports → absolute imports ✅
2. **MCP tool documentation** - All 21 tools documented ✅  
3. **System prompts** - Removed dev-specific content ✅
4. **Production bugs** - db.cursor, bootstrap imports ✅

---

## 🔴 What We Discovered (Critical Issues)

### Issue: Goal Orchestrator Uses Heuristics

**Current Code:**
```python
# empirica/bootstraps/optimal_metacognitive_bootstrap.py line 181
create_goal_orchestrator(use_placeholder=True)  # ← HEURISTIC!

# What placeholder does:
if clarity < 0.60:  # Threshold check = heuristic
    add_clarification_goal()
if know < 0.70:  # Threshold check = heuristic  
    add_investigation_goal()
```

**Your Requirement:**
> "Goals need to be grabbed from context and evaluated by the AI"

**Gap:** Current system uses rule-based logic, NOT AI reasoning.

---

## 🎯 Solution: Self-Referential Goal Generation

**What you want (Option A):**
```python
# AI uses ITSELF to generate goals
orchestrator = CanonicalGoalOrchestrator(
    llm_callback=lambda prompt: ai.reason(prompt),  # AI calls itself!
    use_placeholder=False  # No heuristics
)

# AI reads context and reasons:
# "User wants to make app faster. I should:
#  1. Investigate current performance bottlenecks
#  2. Profile slow endpoints  
#  3. Propose optimizations"
# ← GENUINE REASONING, not template matching
```

---

## 📋 Implementation Tasks

### 1. Simplify Bootstrap (1-2 hours)
**Current:** Too complex, loads unnecessary components, has heuristic fallbacks  
**Target:** Clean, essential components only

**Remove:**
- ❌ Legacy goal orchestrator fallback
- ❌ Heuristic-based placeholder (or make it clear it's fallback)
- ❌ Misleading "no heuristics" comments

**Keep:**
- ✅ 13-vector self-assessment (CORE)
- ✅ Calibration measurement (CORE)
- ✅ Goal orchestrator (make self-reflection primary)

**Structure:**
```python
def bootstrap_metacognition(ai_id, profile, llm_callback=None):
    """
    profile: 'minimal' | 'developer' | 'autonomous_agent' | 'researcher'
    llm_callback: Function for AI to call itself (for goal generation)
    """
    components = {}
    
    # ALWAYS: Core assessment + calibration
    components['assessment'] = load_13_vector_system()
    components['calibration'] = load_calibration_system()
    
    # CONDITIONAL: Goal orchestrator (if llm_callback provided)
    if llm_callback:
        components['goal_orchestrator'] = CanonicalGoalOrchestrator(
            llm_callback=llm_callback,  # Self-reflection!
            use_placeholder=False
        )
    elif profile != 'minimal':
        # Fallback to placeholder (but be honest about it)
        components['goal_orchestrator'] = CanonicalGoalOrchestrator(
            use_placeholder=True  # Threshold-based (not AI reasoning)
        )
    
    # OPTIONAL: Profile-specific components
    if profile == 'researcher':
        components['bayesian_beliefs'] = BayesianBeliefTracker()
    
    if profile == 'autonomous_agent':
        components['drift_monitor'] = DriftMonitor()
    
    return components
```

### 2. Enable Self-Referential Goals (2-3 hours)
**Update:**
- `CanonicalGoalOrchestrator` to accept `llm_callback`
- `_generate_goals_via_llm()` method to use callback
- `investigation_profiles.yaml` to configure goal generation

**Configuration:**
```yaml
# investigation_profiles.yaml (add new section)
goal_generation:
  use_self_reflection: true  # AI generates own goals
  fallback_to_placeholder: true  # If self-reflection unavailable
  cache_in_git: true  # Save generated goals (token efficiency)
  
  profiles:
    minimal:
      use_goal_generation: false  # Skip entirely
    developer:
      use_goal_generation: true
      mode: "self_reflection"
    autonomous_agent:
      use_goal_generation: true
      mode: "self_reflection"
      cache_in_git: true
```

### 3. MCP Integration (Design Decision Needed)
**Problem:** MCP server can't directly call external LLM

**Solution:** Hybrid approach
```python
# MCP bootstrap: Core only (no goals)
bootstrap_session(...)  # Loads assessment + calibration

# Separate MCP tool: Generate goals via meta-prompt  
generate_goals(context, epistemic_state)
→ Returns prompt for AI to reason about
→ AI receives prompt, reasons, returns goals
→ Self-referential without circular dependency!
```

### 4. Git Caching (Optional, 2-3 hours)
**Token Savings:**
- First task: 500 tokens (generate goals)
- Similar task: 0 tokens (load from git cache)
- Changed context: 500 tokens (regenerate)

**Implementation:**
```python
# Save generated goals to git notes
git notes add -m '{
  "goals": [...],
  "context_hash": "abc123",
  "tokens_used": 450
}'

# Load cached goals
cached_goals = git notes show HEAD | jq '.goals'
```

---

## 🤔 Design Decisions Needed

### Q1: Bootstrap Profiles
**Minimal:** 13-vector assessment only (fast, no overhead)  
**Standard:** Assessment + calibration + goals  
**Full:** All components (beliefs, drift monitor, etc.)

**Your preference?**

### Q2: Goal Generation Timing
**Always:** Every task gets goal breakdown (thorough but slow)  
**On-demand:** Only when needed (configurable)  
**Cached:** Use git caching to avoid regeneration

**Your preference?**

### Q3: MCP Self-Reflection
**Option A:** MCP skips goals, use separate `generate_goals` tool  
**Option B:** MCP uses placeholder, Python API uses self-reflection  
**Option C:** Design circular callback mechanism

**Your preference?**

---

## 🚀 Recommended Next Steps

**Immediate (This Session):**
1. Simplify bootstrap (remove legacy components) - 1 hour
2. Update comments to be honest about heuristics - 15 min
3. Test simplified bootstrap - 15 min

**Short-term (Next Session):**
1. Implement llm_callback in CanonicalGoalOrchestrator - 2 hours
2. Add goal_generation config to profiles.yaml - 30 min
3. Test self-referential goal generation - 1 hour

**Long-term:**
1. Git caching for goals
2. Token efficiency measurement
3. Sentinel integration

---

## 📊 Current State

**Bootstrap:**
- ✅ Works (9 components load)
- ⚠️ Uses placeholder (heuristic-based)
- ❌ Comments misleading ("no heuristics")

**Goal Orchestrator:**
- ✅ Architecture sound (LLM-first design)
- ⚠️ Implementation uses placeholder=True
- ❌ Not using genuine AI reasoning

**MCP Server:**
- ✅ Tools defined and working
- ✅ bootstrap_session handler exists (line 1861)
- ⚠️ Client may need restart to see changes

---

**Want me to start with bootstrap simplification? Or discuss design decisions first?**
