# Basic Usage Guide

**Empirica v2.0 - Getting Started**

---

## Hello World - Your First Cascade

The simplest way to use Empirica:

```python
import asyncio
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

async def hello_empirica():
    # Initialize Empirica
    bootstrap = ExtendedMetacognitiveBootstrap(level="2", ai_id="hello_world")
    components = bootstrap.bootstrap()
    
    # Get the cascade
    cascade = components['canonical_cascade']
    
    # Run your first epistemic cascade
    result = await cascade.run_epistemic_cascade(
        task="Explain what Empirica does",
        context={'first_run': True}
    )
    
    # Check the result
    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Overall assessment: {result['phases']['uncertainty']['assessment'].overall_confidence:.2f}")

# Run it
asyncio.run(hello_empirica())
```

**Expected Output:**
```
🔷 TIER 0: CANONICAL FOUNDATION
...
🧠 EPISTEMIC ORCHESTRATOR - Task: 'Explain what Empirica does'
...
Action: proceed
Confidence: 0.75
Overall assessment: 0.75
```

---

## Understanding the Basics

### What Just Happened?

1. **Bootstrap** - Loaded 30 components (Tier 0-2)
2. **THINK** - Generated assessment prompt for self-assessment
3. **UNCERTAINTY** - Measured epistemic state (12 vectors + explicit UNCERTAINTY)
4. **INVESTIGATE** - Checked if investigation needed (skipped if confidence high)
5. **CHECK** - Verified readiness to act
6. **ACT** - Made final decision

### The Result Object

```python
result = {
    'action': 'proceed',              # Action to take
    'confidence': 0.75,               # Overall confidence
    'investigation_rounds': 0,        # How many investigation rounds
    'phases': {
        'think': {...},               # THINK phase results
        'uncertainty': {...},         # 12D assessment
        'investigate': {...},         # Investigation results
        'check': {...},               # Verification results
        'act': {...}                  # Final action
    }
}
```

---

## Common Usage Patterns

### Pattern 1: Simple Task Execution

Run a cascade for a straightforward task:

```python
import asyncio
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

async def simple_task():
    bootstrap = ExtendedMetacognitiveBootstrap(level="2")
    components = bootstrap.bootstrap()
    cascade = components['canonical_cascade']
    
    result = await cascade.run_epistemic_cascade(
        task="Analyze the authentication system for security issues",
        context={
            'cwd': '/path/to/project',
            'files_to_check': ['auth.py', 'login.py'],
            'urgency': 'high'
        }
    )
    
    if result['action'] == 'proceed':
        print("✅ Ready to proceed with analysis")
    elif result['action'] == 'investigate':
        print("⚠️  Need more investigation")
    elif result['action'] == 'clarify':
        print("❓ Need clarification from user")
    
    return result

asyncio.run(simple_task())
```

### Pattern 2: Session Tracking with Database

Track your cascades for analysis:

```python
import asyncio
from empirica.bootstraps import ExtendedMetacognitiveBootstrap
from empirica.data import SessionDatabase, SessionJSONHandler

async def tracked_session():
    # Create database
    db = SessionDatabase()
    json_handler = SessionJSONHandler()
    
    # Start session
    session_id = db.create_session(
        ai_id="my_ai",
        bootstrap_level=2,
        components_loaded=30
    )
    
    # Bootstrap
    bootstrap = ExtendedMetacognitiveBootstrap(level="2")
    components = bootstrap.bootstrap()
    cascade = components['canonical_cascade']
    
    # Run cascade with tracking
    cascade_id = db.create_cascade(session_id, "My task", {'tracked': True})
    
    result = await cascade.run_epistemic_cascade(
        task="Refactor the database layer",
        context={'session_id': session_id}
    )
    
    # Complete tracking
    db.complete_cascade(
        cascade_id,
        final_action=result['action'],
        final_confidence=result['confidence'],
        investigation_rounds=result['investigation_rounds'],
        duration_ms=5000,  # Track time
        engagement_gate_passed=True,
        bayesian_active=True
    )
    
    # Export to JSON for AI reading
    json_handler.export_session(db, session_id)
    
    print(f"✅ Session tracked: {session_id}")
    db.close()

asyncio.run(tracked_session())
```

### Pattern 3: Custom Bootstrap Level

Choose the right initialization level for your needs:

```python
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

# Level 0: Minimal (testing only)
bootstrap_minimal = ExtendedMetacognitiveBootstrap(level="0")
components_minimal = bootstrap_minimal.bootstrap()
# 14 components, fast, no drift monitoring

# Level 1: Basic (single-user, no advanced features)
bootstrap_basic = ExtendedMetacognitiveBootstrap(level="1")
components_basic = bootstrap_basic.bootstrap()
# 25 components, no parallel reasoning

# Level 2: Standard (RECOMMENDED - production default)
bootstrap_standard = ExtendedMetacognitiveBootstrap(level="2")
components_standard = bootstrap_standard.bootstrap()
# 30 components, includes Bayesian + drift monitoring

# Level 3: Extended (enterprise features)
bootstrap_extended = ExtendedMetacognitiveBootstrap(level="3")
components_extended = bootstrap_extended.bootstrap()
# ~35 components, all advanced features

# Level 4: Complete (everything)
bootstrap_complete = ExtendedMetacognitiveBootstrap(level="4")
components_complete = bootstrap_complete.bootstrap()
# ~40 components, complete system
```

**Recommendation:** Use **level 2** for production (default).

### Pattern 4: Without LLM (Placeholder Mode)

Empirica works without external LLM using placeholder assessments:

```python
import asyncio
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

async def placeholder_mode():
    # Create cascade directly (no LLM needed)
    cascade = CanonicalEpistemicCascade()
    
    result = await cascade.run_epistemic_cascade(
        task="Simple task",
        context={}
    )
    
    # All vectors will be 0.5 (neutral uncertainty)
    # Recommended action: INVESTIGATE (conservative)
    print(f"Placeholder confidence: {result['confidence']}")

asyncio.run(placeholder_mode())
```

---

## Understanding Epistemic Assessments

### The 12 Vectors

Every cascade measures **12 epistemic vectors**:

#### GATE: ENGAGEMENT (≥0.60 required)
```python
assessment.engagement.score  # 0.0-1.0
assessment.engagement_gate_passed  # True/False
```
**Meaning:** Are you motivated and engaged with this task?

#### TIER 0: FOUNDATION (35% weight)
```python
assessment.know.score      # Domain knowledge
assessment.do.score        # Capability
assessment.context.score   # Situational awareness
```

#### TIER 1: COMPREHENSION (25% weight)
```python
assessment.clarity.score    # Task definition
assessment.coherence.score  # Internal consistency
assessment.signal.score     # Relevance identification
assessment.density.score    # Information load (inverted)
```

#### TIER 2: EXECUTION (25% weight)
```python
assessment.state.score      # Current understanding
assessment.change.score     # Transformation confidence
assessment.completion.score # Success criteria
assessment.impact.score     # Outcome awareness
```

### Checking Vector Scores

```python
result = await cascade.run_epistemic_cascade(task, context)

# Get assessment from UNCERTAINTY phase
assessment = result['phases']['uncertainty']['assessment']

# Check specific vectors
if assessment.know.score < 0.5:  # OLD schema (still works via wrappers)
    print("⚠️  Low domain knowledge")

if assessment.clarity.score < 0.5:  # OLD schema (still works via wrappers)
    print("⚠️  Task unclear")

if not assessment.engagement_gate_passed:
    print("❌ ENGAGEMENT gate failed (< 0.60)")

# Check overall confidence
print(f"Overall: {assessment.overall_confidence:.2f}")
print(f"Foundation: {assessment.foundation_confidence:.2f}")
print(f"Comprehension: {assessment.comprehension_confidence:.2f}")
print(f"Execution: {assessment.execution_confidence:.2f}")
```

---

## Actions and Decision Making

### Possible Actions

Empirica recommends one of these actions:

1. **PROCEED** - Confidence met, ready to act
2. **INVESTIGATE** - Need more information
3. **CLARIFY** - Task unclear, need user input
4. **RESET** - Task incoherent or cognitive overload
5. **STOP** - Cannot proceed (fundamental issue)

### Interpreting Actions

```python
result = await cascade.run_epistemic_cascade(task, context)

action = result['action']

if action == 'proceed':
    # High confidence, execute task
    print(f"✅ Proceeding with confidence {result['confidence']:.2f}")
    execute_task()

elif action == 'investigate':
    # Need investigation to improve confidence
    print(f"🔍 Investigation needed, current confidence: {result['confidence']:.2f}")
    investigation_results = result['phases']['investigate']
    print(f"Ran {investigation_results['rounds']} investigation rounds")
    
elif action == 'clarify':
    # Need user clarification
    print("❓ Task unclear, need clarification:")
    assessment = result['phases']['uncertainty']['assessment']
    print(f"   Clarity: {assessment.clarity.score:.2f}")
    print(f"   Rationale: {assessment.clarity.rationale}")
    
elif action == 'reset':
    # Task has fundamental issues
    print("❌ Cannot proceed - task needs reset:")
    assessment = result['phases']['uncertainty']['assessment']
    if assessment.coherence.score < 0.5:
        print("   Issue: Task incoherent")
    if assessment.density.score > 0.9:
        print("   Issue: Cognitive overload")

elif action == 'stop':
    # Cannot make progress
    print("🛑 Cannot proceed:")
    assessment = result['phases']['uncertainty']['assessment']
    if assessment.change.score < 0.5:
        print("   Issue: Cannot progress toward goal")
```

---

## Investigation System

### When Investigation Happens

Investigation occurs when:
1. Overall confidence < threshold (default: 0.70)
2. ENGAGEMENT gate passed (≥0.60)
3. No critical flags (RESET/STOP not needed)

### Investigation Rounds

```python
result = await cascade.run_epistemic_cascade(
    task="Complex analysis task",
    context={}
)

# Check investigation
invest = result['phases']['investigate']
print(f"Investigation rounds: {invest['rounds']}")
print(f"Tools used: {invest['tools_used']}")

# Investigation updates confidence
initial_conf = result['phases']['uncertainty']['assessment'].overall_confidence
final_conf = result['confidence']
print(f"Confidence: {initial_conf:.2f} → {final_conf:.2f}")
```

### Investigation Recommendations

The system recommends tools strategically:

```python
# Low KNOW → documentation search, codebase analysis
# Low CLARITY → user clarification (highest gain: 0.40-0.45)
# Low CONTEXT → workspace scanning, web research
# Low DO/CHANGE → test simulation, impact analysis
```

---

## Working with Context

### Providing Rich Context

```python
result = await cascade.run_epistemic_cascade(
    task="Refactor authentication module",
    context={
        # Project context
        'cwd': '/path/to/project',
        'project_name': 'MyApp',
        'language': 'Python',
        
        # Available tools
        'available_tools': ['read', 'write', 'edit', 'grep', 'web_search'],
        
        # Domain context
        'domain': 'security',
        'urgency': 'high',
        
        # User context
        'user_expertise': 'senior',
        'time_available': '2 hours',
        
        # Session context
        'session_id': 'abc123',
        'previous_context': {...}  # From previous cascade
    }
)
```

### Context Best Practices

✅ **Do:**
- Provide working directory (`cwd`)
- List available tools
- Include domain information
- Pass session continuity data

❌ **Don't:**
- Include sensitive data (passwords, keys)
- Pass massive data structures (keep concise)
- Assume context carries over automatically

---

## Error Handling

### Graceful Degradation

Empirica handles missing components gracefully:

```python
# If parallel reasoning unavailable
# → Uses placeholder assessments (all vectors = 0.5)

# If Bayesian Guardian unavailable
# → Skips evidence tracking, cascade still works

# If drift monitor unavailable
# → Skips behavioral tracking, cascade still works

# If tmux unavailable
# → Skips dashboard, cascade still works

# Core cascade always works
```

### Common Errors

```python
import asyncio
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

async def with_error_handling():
    try:
        bootstrap = ExtendedMetacognitiveBootstrap(level="2")
        components = bootstrap.bootstrap()
        cascade = components['canonical_cascade']
        
        result = await cascade.run_epistemic_cascade(
            task="My task",
            context={}
        )
        
        return result
        
    except KeyError as e:
        print(f"❌ Component not found: {e}")
        print("   Check bootstrap level")
        
    except AttributeError as e:
        print(f"❌ Attribute error: {e}")
        print("   Check import paths (old vs new)")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("   Check logs for details")

asyncio.run(with_error_handling())
```

---

## Next Steps

Now that you understand basic usage:

1. **Learn Investigation:** [07_INVESTIGATION_SYSTEM.md](07_INVESTIGATION_SYSTEM.md)
2. **Understand Cascade Flow:** [06_CASCADE_FLOW.md](06_CASCADE_FLOW.md)
3. **Track Sessions:** [Session Database](SYSTEM_ARCHITECTURE_DEEP_DIVE.md#session-database)
4. **Troubleshoot Issues:** [21_TROUBLESHOOTING.md](21_TROUBLESHOOTING.md)

---

## Quick Reference

### Minimal Example
```python
import asyncio
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

async def run():
    bootstrap = ExtendedMetacognitiveBootstrap(level="2")
    components = bootstrap.bootstrap()
    cascade = components['canonical_cascade']
    
    result = await cascade.run_epistemic_cascade("Your task", {})
    print(f"{result['action']}: {result['confidence']:.2f}")

asyncio.run(run())
```

### Key Imports
```python
from empirica.bootstraps import ExtendedMetacognitiveBootstrap
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
from empirica.data import SessionDatabase, SessionJSONHandler
from empirica.core.canonical import CanonicalEpistemicAssessor
```

### Bootstrap Levels
- **0:** Minimal (testing)
- **1:** Basic (no parallel reasoning)
- **2:** Standard (RECOMMENDED) ← default
- **3:** Extended (enterprise)
- **4:** Complete (everything)

---

**You're ready to use Empirica!** 🚀
