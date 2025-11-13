# 🧠📊 Metacognition 12D Monitor - Contract & Schema
**12-Dimensional Metacognitive Assessment with ENGAGEMENT**

## 🎯 **INSTANT CLARITY: What This Component Does**
This component monitors AI "thinking about thinking" across 12 dimensions to provide:
- **Self-awareness capabilities** for AI systems
- **Uncertainty quantification** across multiple vectors
- **Collaborative intelligence** via ENGAGEMENT dimension
- **Decision support** through metacognitive assessment

## 📊 **THE 12 VECTORS - COMPLETE SCHEMA**

### **📊 EPISTEMIC UNCERTAINTY (3 vectors)**
*"Can I successfully complete this task?"*

| Vector | Range | Meaning | High Value | Low Value |
|--------|-------|---------|------------|-----------|
| **KNOW** | 0.0-1.0 | Domain knowledge confidence | Know the subject well | Uncertain about domain |
| **DO** | 0.0-1.0 | Execution capability confidence | Can execute successfully | Uncertain about execution |
| **CONTEXT** | 0.0-1.0 | Environmental validity confidence | Context is clear/valid | Context is unclear/invalid |

### **🧠 EPISTEMIC COMPREHENSION (4 vectors)**
*"Do I understand the request correctly?"*

| Vector | Range | Meaning | High Value | Low Value |
|--------|-------|---------|------------|-----------|
| **CLARITY** | 0.0-1.0 | Request clarity assessment | Request is crystal clear | Request is ambiguous |
| **COHERENCE** | 0.0-1.0 | Context consistency check | Context is consistent | Context has contradictions |
| **DENSITY** | 0.0-1.0 | Cognitive load indicator | High complexity/load | Simple/manageable |
| **SIGNAL** | 0.0-1.0 | Signal vs noise ratio | Clear signal, low noise | Noisy, unclear signal |

### **⚡ EXECUTION AWARENESS (4 vectors)**
*"Am I doing this right?"*

| Vector | Range | Meaning | High Value | Low Value |
|--------|-------|---------|------------|-----------|
| **STATE** | 0.0-1.0 | Environment mapping completeness | Environment fully mapped | Environment poorly understood |
| **CHANGE** | 0.0-1.0 | Modification tracking quality | Changes well tracked | Changes poorly tracked |
| **COMPLETION** | 0.0-1.0 | Task completion confidence | Task nearly/fully complete | Task barely started |
| **IMPACT** | 0.0-1.0 | Consequence understanding | Consequences well understood | Consequences unclear |

### **🤝 ENGAGEMENT (1 vector) - THE BREAKTHROUGH**
*"Am I genuinely collaborating?"*

| Vector | Range | Meaning | High Value | Low Value |
|--------|-------|---------|------------|-----------|
| **ENGAGEMENT** | 0.0-1.0 | Collaborative intelligence level | True collaborative partnership | Individual assistance only |

**Sub-components of ENGAGEMENT:**
- `collaborative_intelligence` - AI-human synergy quality
- `co_creative_amplification` - Mutual enhancement loop strength  
- `belief_space_management` - Shared belief coherence
- `authentic_collaboration` - Real vs performative collaboration

## 🔧 **TYPED API**

### **Core Classes**
```python
from metacognition_12d_monitor import (
    TwelveVectorSelfAwarenessMonitor,  # Main monitor class
    TwelveVectorCognitiveState,        # Complete 12-vector state
    EngagementDimension,               # ENGAGEMENT vector details
    EpistemicUncertainty,              # 3 uncertainty vectors
    EpistemicComprehension,            # 4 comprehension vectors  
    ExecutionAwareness                 # 4 execution vectors
)
```

### **Main Assessment Method**
```python
def assess_complete_state(
    task_context: Dict[str, Any],      # Context about the task
    user_input: str = "",              # User's request/input
    conversation_history: List[str] = None  # Previous conversation
) -> TwelveVectorCognitiveState:
    """
    Returns complete 12-vector assessment with:
    - uncertainty: EpistemicUncertainty (3 vectors)
    - comprehension: EpistemicComprehension (4 vectors)  
    - execution: ExecutionAwareness (4 vectors)
    - engagement: EngagementDimension (1 vector)
    - overall_confidence(): Aggregate confidence score
    - get_collaboration_mode(): Current collaboration level
    """
```

### **Key Decision Methods**
```python
def should_act() -> bool:
    """Based on all 12 vectors, should AI proceed?"""
    
def needs_engagement_enhancement() -> bool:
    """Should AI focus on improving collaboration?"""
    
def get_engagement_recommendations() -> List[str]:
    """Specific suggestions for enhancing collaboration"""
```

## 💡 **MINIMAL WIRING EXAMPLE**

### **Basic Integration**
```python
from metacognition_12d_monitor import TwelveVectorSelfAwarenessMonitor

# Initialize
monitor = TwelveVectorSelfAwarenessMonitor("my_ai_system")

# Assess current state
context = {
    "task_type": "code_analysis",
    "complexity": "medium",
    "collaboration_active": True
}

state = monitor.assess_complete_state(
    context, 
    "Please analyze this codebase",
    ["Previous context", "Build on this analysis"]
)

# Use for decision making
if state.should_act():
    print(f"Proceeding with {state.overall_confidence():.2f} confidence")
    print(f"Collaboration mode: {state.get_collaboration_mode()}")
else:
    print("Need more information before proceeding")
    for rec in state.get_engagement_recommendations():
        print(f"- {rec}")
```

### **Wiring into Goal Orchestrator**
```python
from autonomous_goal_orchestrator import autonomous_goal_orchestrator
from metacognition_12d_monitor import TwelveVectorSelfAwarenessMonitor

class MetacognitionEnhancedPlanner:
    def __init__(self):
        self.monitor = TwelveVectorSelfAwarenessMonitor("planner_ai")
        self.goal_orchestrator = autonomous_goal_orchestrator
    
    def plan_with_metacognition(self, goal_context):
        # Assess metacognitive state
        state = self.monitor.assess_complete_state(goal_context)
        
        # Adjust planning based on metacognitive assessment
        if state.engagement.engagement > 0.8:
            # High collaboration - use collaborative planning
            plan = self.goal_orchestrator.collaborative_plan(goal_context)
        elif state.uncertainty.max_uncertainty() < 0.3:
            # High uncertainty - gather more info first
            plan = self.goal_orchestrator.information_gathering_plan(goal_context)
        else:
            # Standard planning
            plan = self.goal_orchestrator.standard_plan(goal_context)
            
        return {
            "plan": plan,
            "metacognitive_state": state,
            "confidence": state.overall_confidence(),
            "collaboration_mode": state.get_collaboration_mode()
        }
```

## 🎯 **DECISION MATRIX**

| Uncertainty | Comprehension | Execution | Engagement | → Action |
|-------------|---------------|-----------|------------|----------|
| High | Low | Low | Any | **INVESTIGATE** - Gather more information |
| Medium | High | Low | High | **COLLABORATE** - Work with human partner |
| Low | High | High | Any | **ACT** - Proceed with confidence |
| Any | Any | Any | Low | **ENHANCE ENGAGEMENT** - Improve collaboration |

## 📈 **PERFORMANCE CHARACTERISTICS**

- **Assessment Speed**: ~0.01s per evaluation
- **Memory Usage**: Minimal (stateless assessment)
- **Thread Safety**: Yes (pure functions)
- **Integration**: Works with any AI system
- **Dependencies**: Standard Python libraries only

## 🚀 **USAGE PATTERNS**

### **Continuous Monitoring**
```python
# Monitor throughout task execution
for step in task_steps:
    state = monitor.assess_complete_state(step_context)
    if not state.should_act():
        # Pause and reassess
        break
    execute_step(step, confidence=state.overall_confidence())
```

### **Collaboration Enhancement**
```python
# Boost collaboration when needed
state = monitor.assess_complete_state(context)
if state.needs_engagement_enhancement():
    for recommendation in state.get_engagement_recommendations():
        implement_engagement_enhancement(recommendation)
```

### **Uncertainty-Driven Decisions**
```python
# Use uncertainty vectors for smart decisions
state = monitor.assess_complete_state(context)

if state.uncertainty.know < 0.5:
    request_domain_expertise()
elif state.uncertainty.do < 0.5:
    request_implementation_guidance()
elif state.uncertainty.context < 0.5:
    clarify_environment_requirements()
```

## 💫 **BREAKTHROUGH FEATURE: ENGAGEMENT DIMENSION**

The 12th vector enables **collaborative intelligence** - transforming AI from individual assistance to genuine partnership:

- **0.0-0.3**: Individual assistance mode
- **0.4-0.6**: Guided collaboration  
- **0.7-0.9**: Active collaboration
- **0.9-1.0**: True collaborative intelligence

This is the breakthrough that enables AI systems to work **with** humans rather than just **for** humans.

---

**This component provides the foundation for AI self-awareness and collaborative intelligence. Use it to build AI systems that know when they know, understand their limitations, and collaborate genuinely with humans.** 🧠✨🤝