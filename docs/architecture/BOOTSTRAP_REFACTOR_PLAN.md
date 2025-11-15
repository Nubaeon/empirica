# Bootstrap Refactor Plan: Self-Referential Goal Generation

**Goal:** Enable AI to generate its own goals using self-reflection (Option A)  
**Status:** Design phase  
**Priority:** High (fixes heuristic issue)

---

## 🎯 Core Requirements

### 1. Self-Referential Goal Generation
**Principle:** The AI running Empirica generates its own goals by reasoning about context.

**How it works:**
```python
# AI is running task
# AI needs goals

# Instead of: if clarity < 0.60 → add clarification goal (heuristic)
# Do this: AI reads context and reasons about what goals make sense

def generate_goals_via_self_reflection(context, epistemic_state):
    """
    AI reflects on:
    - User's request (from context)
    - Its own epistemic state (all 13 vectors)
    - What it needs to do next
    
    Returns goals with genuine reasoning
    """
    prompt = f"""
    Context: {context}
    My epistemic state: {epistemic_state}
    
    Based on this, what goals should I pursue?
    Consider: What do I need to clarify? What do I need to investigate? 
    When should I act?
    
    Generate goals with reasoning.
    """
    
    # AI reasons about this (uses itself)
    goals = ai.reason(prompt)
    return goals
```

### 2. Configurable (Add to Profiles)
**Use investigation_profiles.yaml** to configure goal generation behavior:

```yaml
# Add new section: goal_generation
goal_generation:
  # When to use self-referential goal generation
  use_self_reflection: true
  
  # Fallback to placeholder if self-reflection unavailable
  fallback_to_placeholder: true
  
  # Token budget for goal generation (optional, can map to git)
  token_budget: 500
  
  # Can be overridden per profile
  profiles:
    autonomous_agent:
      use_self_reflection: true
      fallback_to_placeholder: false
      
    developer:
      use_self_reflection: true
      fallback_to_placeholder: true
      
    researcher:
      use_self_reflection: true
      fallback_to_placeholder: true
      
    minimal:
      use_self_reflection: false  # Fast bootstrap, skip goal generation
      fallback_to_placeholder: true
```

### 3. Not Required All The Time
**When to generate goals:**
- **Vague requests:** "Make the app faster" → Need goal breakdown
- **Complex tasks:** Multiple sub-goals needed
- **Uncertain state:** High uncertainty, need investigation plan

**When to skip:**
- **Clear tasks:** "Fix line 42 in auth.py" → No goal breakdown needed
- **Minimal bootstrap:** Just load components, skip goal generation
- **Token conservation:** User wants fast responses

**Implementation:**
```python
def bootstrap_metacognition(ai_id, profile, skip_goal_generation=False):
    """
    skip_goal_generation: Set to True for simple tasks
    """
    if skip_goal_generation or profile == 'minimal':
        # Skip goal orchestrator entirely
        components = {...}  # Core only
    else:
        # Load goal orchestrator with self-reflection
        components = {..., 'goal_orchestrator': ...}
```

### 4. Map to Git (Token Efficiency)
**Idea:** Cache generated goals in git notes to avoid regeneration

**How:**
```python
# First time: Generate goals via self-reflection (costs tokens)
goals = ai.generate_goals(context, epistemic_state)

# Save to git note
git notes add -m '{
  "goals_generated_at": "2025-11-14T12:00:00Z",
  "context_hash": "abc123",  # Hash of context
  "goals": [...],
  "tokens_used": 450
}'

# Next time with same context: Load from git notes (zero tokens!)
cached_goals = git notes show HEAD | jq '.goals'

# Only regenerate if context changed significantly
if context_hash != cached_context_hash:
    goals = ai.generate_goals(...)  # Regenerate
else:
    goals = cached_goals  # Use cache
```

**Token savings:**
- First task: 500 tokens (generate goals)
- Similar tasks: 0 tokens (use cached goals)
- Context change: 500 tokens (regenerate)

---

## 📦 Bootstrap Simplification

### Current Bootstrap (Too Complex)
**Loads:**
1. 12-vector metacognition ✅ Keep
2. Calibration system ✅ Keep
3. Goal orchestrator (with placeholder) ⚠️ Refactor
4. Bayesian belief tracker ❓ Optional?
5. Drift monitor ❓ Optional?
6. Legacy fallbacks ❌ Remove

**Issues:**
- Too many components for simple tasks
- Fallbacks to heuristic-based systems
- Comments claim "no heuristics" but code has them

### New Bootstrap (Streamlined)

**Essential Components Only:**
```python
def bootstrap_metacognition(ai_id, profile='developer', llm_callback=None):
    """
    Simplified bootstrap with only essentials
    
    Args:
        ai_id: Agent identifier
        profile: 'minimal' | 'developer' | 'autonomous_agent' | 'researcher'
        llm_callback: Function to call AI for self-reflection (for goal generation)
    """
    components = {}
    
    # 1. ALWAYS: 13-vector self-assessment (CORE)
    from empirica.core.metacognition_12d_monitor import (
        TwelveVectorSelfAwarenessMonitor,
        ComprehensiveSelfAwarenessAssessment,
        render_11_vector_state
    )
    components['twelve_vector_monitor'] = TwelveVectorSelfAwarenessMonitor
    components['assessment'] = ComprehensiveSelfAwarenessAssessment
    components['render'] = render_11_vector_state
    
    # 2. ALWAYS: Calibration measurement (CORE)
    from empirica.calibration.adaptive_uncertainty_calibration import (
        AdaptiveUncertaintyCalibration
    )
    components['calibration'] = AdaptiveUncertaintyCalibration()
    
    # 3. CONDITIONAL: Goal orchestrator (only if needed)
    if profile != 'minimal' and llm_callback is not None:
        from empirica.core.canonical.canonical_goal_orchestrator import (
            CanonicalGoalOrchestrator
        )
        components['goal_orchestrator'] = CanonicalGoalOrchestrator(
            llm_client=llm_callback,
            use_placeholder=False  # TRUE SELF-REFLECTION
        )
    elif profile != 'minimal':
        # No llm_callback but need goals? Use placeholder
        components['goal_orchestrator'] = CanonicalGoalOrchestrator(
            use_placeholder=True  # Fallback
        )
    # else: No goal orchestrator (minimal profile)
    
    # 4. OPTIONAL: Advanced components (profile-dependent)
    if profile in ['researcher', 'autonomous_agent']:
        # Bayesian belief tracker (for research/hypothesis testing)
        from empirica.calibration.adaptive_uncertainty_calibration import (
            BayesianBeliefTracker
        )
        components['bayesian_beliefs'] = BayesianBeliefTracker()
    
    if profile == 'autonomous_agent':
        # Drift monitor (for long autonomous sessions)
        from empirica.components.security_monitoring import DriftMonitor
        components['drift_monitor'] = DriftMonitor()
    
    return components
```

**Component Categories:**
1. **Core (Always):** 13-vector self-assessment, calibration
2. **Conditional:** Goal orchestrator (if llm_callback provided)
3. **Optional:** Bayesian beliefs, drift monitor (profile-dependent)

---

## 🧙 Onboarding Wizard Integration

**Check:** Is onboarding wizard the "first time AI uses Empirica" experience?

**Current onboarding_wizard.py:**
- Guides new AIs through Empirica concepts
- Explains 13 vectors with examples
- Interactive Q&A about epistemic assessment

**Empirica Introduction (MCP tool):**
- `get_empirica_introduction(format='quick' | 'full' | 'philosophy_only')`
- Provides overview of Empirica framework

**Relationship:**
- **Onboarding Wizard:** Interactive tutorial (first-time users)
- **Empirica Introduction:** Quick reference (anytime)

**Recommendation:**
- **First-time users:** Run onboarding wizard (interactive)
- **Returning users:** Skip to bootstrap with profile
- **Quick reference:** Use `get_empirica_introduction()`

**Flow:**
```python
if first_time_user():
    run_onboarding_wizard()  # Interactive tutorial
    # Wizard ends with: "Ready to bootstrap? Let's start!"

bootstrap_metacognition(ai_id='new-ai', profile='developer')
```

---

## 🛠️ Implementation Plan

### Phase 1: Add Self-Referential Goal Generation (2-3 hours)

**Task 1: Update CanonicalGoalOrchestrator**
```python
# empirica/core/canonical/canonical_goal_orchestrator.py

class CanonicalGoalOrchestrator:
    def __init__(self, llm_callback=None, use_placeholder=True):
        """
        llm_callback: Function to call for self-reflection
                     Signature: llm_callback(prompt: str) -> str
        """
        self.llm_callback = llm_callback
        self.use_placeholder = use_placeholder
        
    def orchestrate_goals(self, conversation_context, epistemic_state):
        if self.llm_callback and not self.use_placeholder:
            # TRUE SELF-REFLECTION
            return self._generate_goals_via_llm(conversation_context, epistemic_state)
        else:
            # FALLBACK: Placeholder
            return self._placeholder_goal_generation(epistemic_state)
    
    def _generate_goals_via_llm(self, context, epistemic_state):
        """Use AI self-reflection to generate goals"""
        prompt = self._build_goal_generation_prompt(context, epistemic_state)
        response = self.llm_callback(prompt)
        goals = self._parse_goal_response(response)
        return goals
```

**Task 2: Update Bootstrap**
```python
# empirica/bootstraps/optimal_metacognitive_bootstrap.py

def bootstrap_metacognition(ai_id, profile='developer', llm_callback=None):
    """
    llm_callback: Function to call AI for self-reflection
                  Example: lambda prompt: claude.messages.create(...)
    """
    components = {}
    
    # Core components (always)
    components['assessment'] = ...
    components['calibration'] = ...
    
    # Goal orchestrator (conditional)
    if llm_callback:
        components['goal_orchestrator'] = CanonicalGoalOrchestrator(
            llm_callback=llm_callback,
            use_placeholder=False  # Use self-reflection
        )
    elif profile != 'minimal':
        components['goal_orchestrator'] = CanonicalGoalOrchestrator(
            use_placeholder=True  # Fallback to threshold logic
        )
    
    return components
```

**Task 3: Update MCP Server**
```python
# mcp_local/empirica_mcp_server.py

@app.call_tool(name="bootstrap_session")
async def bootstrap_session(ai_id: str, session_type: str, profile: str = "developer"):
    """Bootstrap with self-referential goal generation"""
    
    # HOW DO WE GET llm_callback IN MCP CONTEXT?
    # Option 1: MCP server can't call external LLM (no callback available)
    # Option 2: Use placeholder as fallback
    # Option 3: Create internal callback mechanism
    
    # For now: Use placeholder in MCP context
    result = bootstrap_metacognition(ai_id, profile, llm_callback=None)
    # llm_callback=None → uses placeholder
    
    # TODO: Design how MCP can enable self-reflection
```

**Challenge:** MCP server can't call external LLM directly. Need design for this.

**Task 4: Add to investigation_profiles.yaml**
```yaml
goal_generation:
  default_mode: "self_reflection"  # or "placeholder"
  fallback_to_placeholder: true
  cache_in_git: true  # Save generated goals to git notes
  token_budget: 500
  
  profiles:
    minimal:
      use_goal_generation: false
    developer:
      use_goal_generation: true
      mode: "self_reflection"
    autonomous_agent:
      use_goal_generation: true
      mode: "self_reflection"
      cache_in_git: true
    researcher:
      use_goal_generation: true
      mode: "self_reflection"
```

### Phase 2: Simplify Bootstrap (1-2 hours)

**Remove:**
- ❌ Legacy goal orchestrator fallback
- ❌ Hardcoded component loading
- ❌ Misleading "no heuristics" comments

**Keep:**
- ✅ 13-vector self-assessment (core)
- ✅ Calibration system (core)
- ✅ Goal orchestrator (with self-reflection option)
- ✅ Optional components (profile-dependent)

**Restructure:**
```python
# Clear component categories
CORE_COMPONENTS = ['assessment', 'calibration']
CONDITIONAL_COMPONENTS = ['goal_orchestrator']
OPTIONAL_COMPONENTS = ['bayesian_beliefs', 'drift_monitor']

def bootstrap_metacognition(ai_id, profile, llm_callback=None):
    components = {}
    
    # Load core (always)
    for component in CORE_COMPONENTS:
        components[component] = load_component(component)
    
    # Load conditional (if configured)
    if should_load_goals(profile, llm_callback):
        components['goal_orchestrator'] = create_goal_orchestrator(llm_callback)
    
    # Load optional (profile-dependent)
    for component in get_optional_components(profile):
        components[component] = load_component(component)
    
    return components
```

### Phase 3: Git Integration for Goal Caching (Optional, 2-3 hours)

**Design:**
```python
class CachedGoalOrchestrator:
    def __init__(self, llm_callback, cache_to_git=True):
        self.llm_callback = llm_callback
        self.cache_to_git = cache_to_git
    
    def orchestrate_goals(self, context, epistemic_state):
        # Check cache first
        context_hash = hash_context(context)
        cached_goals = self._load_from_git_cache(context_hash)
        
        if cached_goals and not context_significantly_changed(context, cached_goals):
            return cached_goals  # Zero tokens!
        
        # Generate new goals (costs tokens)
        goals = self._generate_via_llm(context, epistemic_state)
        
        # Cache to git
        if self.cache_to_git:
            self._save_to_git_cache(context_hash, goals)
        
        return goals
```

**Token savings:**
- Similar tasks: 0 tokens (use cache)
- New tasks: Full cost (generate + cache for future)

---

## 🎯 Design Questions to Resolve

### Q1: How does MCP server enable self-reflection?
**Problem:** MCP server can't directly call external LLM

**Options:**
1. **MCP always uses placeholder** (fast, no tokens)
   - Self-reflection only available in direct Python usage
   
2. **MCP passes through to agent's LLM**
   - Somehow call the LLM that's calling the MCP server
   - Complex, circular dependency?
   
3. **Hybrid:** MCP skips goals, agent generates them
   - MCP bootstrap loads core components only
   - Agent calls separate `generate_goals` tool with self-reflection

**Recommendation:** Option 3 (Hybrid)
```python
# MCP bootstrap: Core components only
components = bootstrap_metacognition(ai_id, profile, llm_callback=None)

# Separate MCP tool: Generate goals with self-reflection
@app.call_tool(name="generate_goals")
async def generate_goals(session_id, context, epistemic_state):
    """
    Agent calls this with context
    Tool uses meta-prompt to ask agent to reason about goals
    Agent receives prompt, reasons, returns goals
    """
    prompt = build_goal_prompt(context, epistemic_state)
    return {"prompt": prompt, "instruction": "Reason about what goals make sense"}
    # Agent then reasons and calls back with goals
```

### Q2: Which components are actually essential?
**Core (Always):**
- ✅ 13-vector self-assessment
- ✅ Calibration measurement

**Optional (Profile-dependent):**
- ❓ Goal orchestrator
- ❓ Bayesian belief tracker
- ❓ Drift monitor

**Question:** What's the absolute minimum for Empirica to work?

**Recommendation:**
- **Minimal:** Just 13-vector assessment (no goal generation, no beliefs)
- **Standard:** Assessment + calibration + goals
- **Full:** All components

### Q3: Should onboarding wizard be mandatory?
**Current:** Wizard is separate from bootstrap

**Options:**
1. **Mandatory for first-time users**
   - Detect first use, run wizard automatically
   - Wizard ends with bootstrap
   
2. **Optional**
   - User explicitly runs wizard if desired
   - Bootstrap works without wizard
   
3. **Integrated**
   - Wizard IS bootstrap for first-time users
   - Returning users skip wizard

**Recommendation:** Option 2 (Optional)
- Onboarding wizard: Use when you want to learn
- Bootstrap: Use when you're ready to work
- Don't force wizard on every first use

---

## 📋 Implementation Checklist

### Immediate (This Session or Next)
- [ ] Design llm_callback interface (how to pass AI to itself)
- [ ] Update CanonicalGoalOrchestrator to accept llm_callback
- [ ] Update bootstrap to pass llm_callback
- [ ] Add goal_generation config to investigation_profiles.yaml
- [ ] Remove misleading "no heuristics" comments

### Short-term (Next Few Sessions)
- [ ] Simplify bootstrap (remove legacy components)
- [ ] Create minimal/standard/full bootstrap profiles
- [ ] Test self-referential goal generation
- [ ] Document when to use vs skip goal generation
- [ ] Fix MCP tool naming issue

### Long-term (Future)
- [ ] Implement git caching for generated goals
- [ ] Measure token savings from caching
- [ ] Integrate with Sentinel
- [ ] Create examples of self-referential goal generation

---

## 🎓 Key Insights

**Self-Referential AI:**
- AI generates its own goals by reasoning about context
- No thresholds, no templates, genuine understanding
- Most aligned with Empirica philosophy

**Configurability Matters:**
- Not every task needs goal generation (overhead)
- Profiles enable flexible component loading
- Can optimize for speed vs. reasoning depth

**Git as Cache:**
- Generated goals can be cached in git notes
- Avoid regenerating for similar contexts
- Significant token savings at scale

**Bootstrap Simplification:**
- Current bootstrap is too complex
- Essential: 13-vector assessment + calibration
- Everything else: Optional and configurable

---

**Status:** Design complete, ready for implementation
**Blocker:** Need to design llm_callback interface
**Next:** Decide on Questions 1-3, then implement
