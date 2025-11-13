# Profile Management Guide

**Empirica v2.0 - Investigation Profiles for AI Agents**

---

## What Are Investigation Profiles?

Investigation profiles configure how Empirica adapts to different AI capabilities, domains, and criticality levels. Instead of one-size-fits-all constraints, profiles enable **capability-appropriate investigation**.

### The Problem Profiles Solve

**Without Profiles:**
```python
# All AIs get same rigid constraints
MAX_INVESTIGATION_CYCLES = 3  # Too limiting for complex tasks
UNCERTAINTY_THRESHOLD = 0.3    # Too low for novel domains
INVESTIGATION_REQUIRED = True  # Forces investigation even when unnecessary
```

**Result:** High-reasoning AIs constrained, autonomous agents under-supported, critical domains under-investigated.

**With Profiles:**
```python
# High-reasoning AI (Claude/GPT-4)
profile = "high_reasoning"
→ Unlimited investigation cycles
→ Dynamic thresholds based on task
→ Trust AI judgment

# Autonomous agent (Minimax)
profile = "autonomous"
→ Structured guidance (3-5 cycles)
→ Fixed thresholds for consistency
→ Explicit checkpoints

# Critical domain (healthcare/finance)
profile = "critical"
→ Mandatory investigation
→ Strict compliance requirements
→ Audit trail required
```

**Result:** Each AI gets appropriate support for its capabilities and domain requirements.

---

## Built-In Profiles

### 1. **high_reasoning** - For Advanced AI Models

**Best for:** Claude Sonnet/Opus, GPT-4, O1, high-capability models

**Philosophy:** Trust the AI's judgment, minimal constraints

**Configuration:**
```yaml
name: high_reasoning
description: Minimal constraints for high-reasoning AI models
investigation:
  max_cycles: -1              # Unlimited
  uncertainty_threshold: null # AI decides
  required_when: []           # Optional
capabilities:
  reasoning: high
  self_awareness: high
  investigation: autonomous
constraints:
  enforcement: loose
  override_allowed: true
```

**When to Use:**
- Complex architectural problems
- Novel domains requiring exploration  
- Tasks where AI judgment is critical
- Research and investigation workflows

**Example:**
```bash
empirica bootstrap --profile high_reasoning \
  --ai-model claude-sonnet \
  --domain software-architecture
```

### 2. **autonomous** - For Independent AI Agents

**Best for:** Minimax, AutoGPT, agent frameworks needing structure

**Philosophy:** Provide guardrails while enabling autonomy

**Configuration:**
```yaml
name: autonomous
description: Structured guidance for autonomous agents
investigation:
  max_cycles: 5
  uncertainty_threshold: 0.4
  required_when: 
    - uncertainty > 0.6
    - clarity < 0.5
capabilities:
  reasoning: medium-high
  self_awareness: medium
  investigation: guided
constraints:
  enforcement: moderate
  override_allowed: true
guidance:
  investigation_prompts: true
  checkpoint_reminders: true
```

**When to Use:**
- Autonomous agent deployments
- Tasks requiring consistent behavior
- Production workflows with validation
- Multi-step processes needing checkpoints

**Example:**
```bash
empirica bootstrap --profile autonomous \
  --ai-model minimax \
  --domain testing
```

### 3. **critical** - For High-Stakes Domains

**Best for:** Healthcare, finance, legal, safety-critical systems

**Philosophy:** Mandate investigation, maximize validation

**Configuration:**
```yaml
name: critical
description: Strict requirements for critical domains
investigation:
  max_cycles: 10
  uncertainty_threshold: 0.2  # Low tolerance
  required_when:
    - always                  # Investigation mandatory
  tools_required:
    - evidence_gathering
    - validation
    - audit_trail
capabilities:
  reasoning: any
  self_awareness: any
  investigation: required
constraints:
  enforcement: strict
  override_allowed: false
  audit_logging: true
compliance:
  evidence_required: true
  dual_validation: true
  reasoning_trail: mandatory
```

**When to Use:**
- Medical diagnosis assistance
- Financial analysis
- Legal document review
- Safety-critical systems
- Regulatory compliance scenarios

**Example:**
```bash
empirica bootstrap --profile critical \
  --ai-model claude-opus \
  --domain healthcare
```

### 4. **exploratory** - For Research & Discovery

**Best for:** Research tasks, prototyping, learning scenarios

**Philosophy:** Encourage investigation, support exploration

**Configuration:**
```yaml
name: exploratory
description: Encourage investigation and learning
investigation:
  max_cycles: 7
  uncertainty_threshold: 0.5
  required_when:
    - uncertainty > 0.7
  encourage_investigation: true
capabilities:
  reasoning: medium-high
  self_awareness: medium-high
  investigation: encouraged
learning:
  track_epistemic_growth: true
  reward_investigation: true
  uncertainty_reduction_goal: 0.3
```

**When to Use:**
- Research projects
- Learning new domains
- Prototyping and experimentation
- Hypothesis generation
- Discovery workflows

**Example:**
```bash
empirica bootstrap --profile exploratory \
  --ai-model gpt-4 \
  --domain research
```

### 5. **balanced** - Default Profile

**Best for:** General-purpose tasks, unknown AI capabilities

**Philosophy:** Middle ground between freedom and structure

**Configuration:**
```yaml
name: balanced
description: Balanced approach for general use
investigation:
  max_cycles: 4
  uncertainty_threshold: 0.4
  required_when:
    - uncertainty > 0.7
    - clarity < 0.4
capabilities:
  reasoning: medium
  self_awareness: medium
  investigation: supported
constraints:
  enforcement: moderate
  override_allowed: true
```

**When to Use:**
- Default choice when profile unclear
- Mixed capability AI models
- General development tasks
- When starting with Empirica

**Example:**
```bash
empirica bootstrap  # Uses balanced by default
```

---

## Profile Selection Logic

### Automatic Selection

If no profile specified, Empirica selects based on:

1. **AI Model Detection:**
   ```
   claude-opus, gpt-4, o1 → high_reasoning
   claude-sonnet → high_reasoning
   minimax, autogpt → autonomous
   gpt-3.5, other → balanced
   ```

2. **Domain Detection:**
   ```
   healthcare, finance, legal → critical
   research, exploration → exploratory
   development, testing → autonomous
   unknown → balanced
   ```

3. **Explicit Override:**
   ```bash
   # Override auto-detection
   empirica bootstrap --profile critical --ai-model gpt-3.5
   # Uses critical (not balanced) because explicitly set
   ```

### Selection Priority

```
1. Explicit --profile flag (highest)
2. Domain-based selection
3. AI model-based selection
4. Default (balanced)
```

---

## Profile Management Commands

### List Available Profiles

```bash
empirica profile-list

# Output:
📋 Available Profiles:
  • high_reasoning - Minimal constraints for high-reasoning AI
  • autonomous - Structured guidance for autonomous agents
  • critical - Strict requirements for critical domains
  • exploratory - Encourage investigation and learning
  • balanced - Balanced approach for general use (default)
```

### Show Profile Details

```bash
empirica profile-show high_reasoning

# Output:
🔍 Profile: high_reasoning
   Description: Minimal constraints for high-reasoning AI models
   AI Model: Any high-capability model
   Domain: Any
   
   Investigation:
     Max Cycles: Unlimited
     Uncertainty Threshold: AI decides
     Required When: AI decides
   
   Capabilities:
     Reasoning: high
     Self-awareness: high
     Investigation: autonomous
```

### Create Custom Profile

```bash
empirica profile-create my-profile \
  --ai-model custom-model \
  --domain custom-domain \
  --description "My custom investigation profile"

# Output:
➕ Creating profile: my-profile
   Description: My custom investigation profile
   AI Model: custom-model
   Domain: custom-domain

✅ Profile 'my-profile' created successfully!
```

### Set Default Profile

```bash
empirica profile-set-default high_reasoning

# Output:
⭐ Setting default profile: high_reasoning
✅ Default profile set to 'high_reasoning'
```

---

## Using Profiles with Bootstrap

### CLI Bootstrap

```bash
# Explicit profile
empirica bootstrap --profile high_reasoning

# Profile + AI model
empirica bootstrap --profile autonomous --ai-model minimax

# Full specification
empirica bootstrap \
  --profile critical \
  --ai-model claude-opus \
  --domain healthcare
```

### MCP Bootstrap

```python
from empirica.cli.mcp_client import bootstrap_session

# Explicit profile
result = bootstrap_session(
    ai_id='claude',
    profile='high_reasoning'
)

# Profile + domain
result = bootstrap_session(
    ai_id='minimax',
    profile='autonomous',
    domain='testing'
)

# Full specification
result = bootstrap_session(
    ai_id='medical-assistant',
    profile='critical',
    ai_model='claude-opus',
    domain='healthcare'
)
```

### Python API

```python
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

# With profile
bootstrap = ExtendedMetacognitiveBootstrap(
    level="2",
    profile='high_reasoning'
)

components = bootstrap.bootstrap()
```

---

## Profile Customization

### Creating a Custom Profile

**Step 1: Create profile YAML**

```yaml
# ~/.empirica/profiles/my-profile.yaml
name: my-profile
description: Custom profile for my use case
investigation:
  max_cycles: 6
  uncertainty_threshold: 0.35
  required_when:
    - uncertainty > 0.65
capabilities:
  reasoning: high
  self_awareness: high
  investigation: supported
constraints:
  enforcement: moderate
  override_allowed: true
```

**Step 2: Load profile**

```bash
empirica bootstrap --profile my-profile
```

### Modifying Built-In Profiles

**Not recommended** - Create custom profile instead to preserve defaults

But if necessary:
```bash
# Copy built-in profile
cp empirica/config/investigation_profiles.yaml ~/.empirica/profiles/

# Edit copy
vim ~/.empirica/profiles/investigation_profiles.yaml

# Empirica loads from ~/.empirica/profiles/ first
```

---

## Profile Best Practices

### When to Use Each Profile

**high_reasoning:**
- ✅ Complex architectural decisions
- ✅ Novel problems requiring exploration
- ✅ Research and investigation
- ❌ Production automation (too flexible)
- ❌ Critical domains (needs constraints)

**autonomous:**
- ✅ Autonomous agent deployments
- ✅ Consistent production workflows
- ✅ Multi-step processes
- ❌ Highly novel domains (needs more cycles)
- ❌ Critical domains (needs stricter constraints)

**critical:**
- ✅ Healthcare applications
- ✅ Financial analysis
- ✅ Legal/compliance work
- ✅ Safety-critical systems
- ❌ Rapid prototyping (too strict)
- ❌ Exploratory research (over-constrained)

**exploratory:**
- ✅ Research projects
- ✅ Learning new domains
- ✅ Hypothesis generation
- ❌ Production deployment (too experimental)
- ❌ Time-sensitive tasks (encourages investigation)

**balanced:**
- ✅ General development
- ✅ Unknown requirements
- ✅ Default choice
- ❌ Known specific needs (use specialized profile)

### Profile Selection Flowchart

```
Start
  ↓
Is domain critical (healthcare/finance/legal)?
  Yes → Use "critical"
  No ↓
Is this research/exploration?
  Yes → Use "exploratory"
  No ↓
Is AI autonomous agent?
  Yes → Use "autonomous"
  No ↓
Is AI high-capability (Claude Opus/GPT-4)?
  Yes → Use "high_reasoning"
  No ↓
Use "balanced" (default)
```

---

## Profile Impact on Workflow

### Investigation Cycles

**high_reasoning:**
```
PREFLIGHT → uncertainty=0.7
→ AI decides to investigate (no constraint)
→ Investigates until satisfied
→ CHECK → uncertainty=0.2
→ ACT
```

**autonomous:**
```
PREFLIGHT → uncertainty=0.7 (> threshold 0.4)
→ Investigation REQUIRED
→ Max 5 cycles
→ CHECK after each cycle
→ Must reduce uncertainty < 0.4 or hit max cycles
→ ACT
```

**critical:**
```
PREFLIGHT → uncertainty=0.3 (any level)
→ Investigation ALWAYS REQUIRED
→ Max 10 cycles
→ Evidence gathering mandatory
→ Dual validation required
→ CHECK → Must meet strict criteria
→ ACT (with audit trail)
```

### Calibration Expectations

Different profiles have different calibration expectations:

**high_reasoning:**
- Expected calibration: 80-90% well-calibrated
- Reason: AI self-regulates investigation

**autonomous:**
- Expected calibration: 75-85% well-calibrated
- Reason: Structured guidance prevents over/under-investigation

**critical:**
- Expected calibration: 85-95% well-calibrated
- Reason: Mandatory investigation reduces uncertainty

**Track over time:**
```bash
empirica monitor --calibration --profile high_reasoning
# Shows calibration statistics by profile
```

---

## Troubleshooting

### Profile Not Found

**Error:** `Profile 'xyz' not found`

**Solutions:**
```bash
# List available profiles
empirica profile-list

# Check custom profile location
ls ~/.empirica/profiles/

# Verify profile name spelling
empirica profile-show high_reasoning  # Correct
empirica profile-show high-reasoning  # Wrong (underscore not dash)
```

### Profile Not Loading

**Symptom:** Profile seems ignored, using default behavior

**Debug:**
```bash
# Check if profile was actually set
empirica bootstrap --profile high_reasoning --verbose
# Look for: "Profile: high_reasoning loaded"

# Verify profile configuration
empirica profile-show high_reasoning
```

### Investigation Constraints Too Strict

**Symptom:** AI forced to investigate even when confident

**Solutions:**
```bash
# Use more flexible profile
empirica bootstrap --profile high_reasoning  # Instead of autonomous

# Or create custom profile with looser constraints
# Edit ~/.empirica/profiles/my-profile.yaml
investigation:
  required_when: []  # Never force investigation
```

### Investigation Constraints Too Loose

**Symptom:** AI skips investigation when it should investigate

**Solutions:**
```bash
# Use stricter profile
empirica bootstrap --profile critical  # Instead of balanced

# Or lower uncertainty threshold
# Edit profile:
investigation:
  uncertainty_threshold: 0.3  # Lower = more likely to investigate
```

---

## Advanced: Profile Configuration Reference

### Complete Profile Schema

```yaml
# Profile identity
name: string              # Unique profile name
description: string       # Human-readable description

# Investigation behavior
investigation:
  max_cycles: int | -1    # Max investigation cycles (-1 = unlimited)
  uncertainty_threshold: float | null  # Trigger investigation (null = AI decides)
  required_when:          # Conditions forcing investigation
    - string              # e.g., "uncertainty > 0.6", "always", "clarity < 0.5"
  encourage_investigation: bool  # Bias toward investigating
  tools_required:         # Required investigation tools
    - string              # e.g., "evidence_gathering", "validation"

# AI capabilities (informational)
capabilities:
  reasoning: string       # low, medium, medium-high, high
  self_awareness: string  # low, medium, medium-high, high
  investigation: string   # required, guided, supported, encouraged, autonomous

# Constraints
constraints:
  enforcement: string     # loose, moderate, strict
  override_allowed: bool  # Can AI override profile constraints?
  audit_logging: bool     # Log all decisions?

# Domain-specific (optional)
compliance:
  evidence_required: bool
  dual_validation: bool
  reasoning_trail: string  # optional, recommended, mandatory

# Learning (optional)
learning:
  track_epistemic_growth: bool
  reward_investigation: bool
  uncertainty_reduction_goal: float

# Guidance (optional)
guidance:
  investigation_prompts: bool
  checkpoint_reminders: bool
```

---

## Examples

### Example 1: High-Reasoning AI on Complex Task

```bash
# Bootstrap
empirica bootstrap --profile high_reasoning --ai-model claude-opus

# Workflow
PREFLIGHT:
  Uncertainty: 0.65 (moderately uncertain)
  Decision: Investigate (AI chooses to)
  
INVESTIGATE:
  Cycle 1: Research architecture patterns
  Cycle 2: Analyze existing code
  Cycle 3: Prototype solutions
  (No limit - continues until AI satisfied)
  
CHECK:
  Uncertainty: 0.18 (low)
  Decision: Proceed
  
ACT:
  Implements solution with confidence
  
POSTFLIGHT:
  Calibration: well_calibrated
  Uncertainty reduction: -0.47
```

### Example 2: Autonomous Agent on Testing Task

```bash
# Bootstrap
empirica bootstrap --profile autonomous --ai-model minimax

# Workflow
PREFLIGHT:
  Uncertainty: 0.72 (> threshold 0.4)
  Decision: Investigation REQUIRED
  
INVESTIGATE:
  Cycle 1/5: Review test specifications
  CHECK: Uncertainty 0.58 (still > 0.4)
  
  Cycle 2/5: Analyze codebase
  CHECK: Uncertainty 0.45 (still > 0.4)
  
  Cycle 3/5: Identify test cases
  CHECK: Uncertainty 0.32 (< 0.4 ✓)
  Decision: Proceed
  
ACT:
  Writes tests
  
POSTFLIGHT:
  Calibration: well_calibrated
  Cycles used: 3/5
```

### Example 3: Critical Domain (Healthcare)

```bash
# Bootstrap
empirica bootstrap --profile critical --ai-model claude-opus --domain healthcare

# Workflow
PREFLIGHT:
  Uncertainty: 0.25 (low)
  Decision: Investigation REQUIRED (always in critical profile)
  
INVESTIGATE:
  Cycle 1/10: Gather medical evidence
  Evidence logged: [research papers, clinical guidelines]
  
  Cycle 2/10: Cross-validate findings
  Dual validation: Required
  
  Cycle 3/10: Check contraindications
  Audit trail: Generated
  
  CHECK: Uncertainty 0.08, Evidence complete
  Decision: Proceed (with audit trail)
  
ACT:
  Provides medical information
  Audit trail: Complete reasoning logged
  
POSTFLIGHT:
  Calibration: well_calibrated
  Compliance: Evidence trail verified
```

---

## Summary

**Profiles enable capability-appropriate investigation:**

- **high_reasoning:** Trust advanced AI judgment
- **autonomous:** Provide structure for agents
- **critical:** Mandate investigation for safety
- **exploratory:** Encourage learning
- **balanced:** Sensible defaults

**Use profiles to:**
- Match investigation to AI capability
- Enforce domain requirements (healthcare, finance)
- Balance autonomy and structure
- Improve calibration over time

**Profile selection:**
1. Critical domain? → Use `critical`
2. Research/exploration? → Use `exploratory`
3. Autonomous agent? → Use `autonomous`
4. High-capability AI? → Use `high_reasoning`
5. Uncertain? → Use `balanced` (default)

---

**Next Steps:**
- Try different profiles on same task
- Track calibration by profile over time
- Create custom profiles for your domain
- Share profile configurations across team

**For More Info:**
- Profile system spec: `docs/reference/INVESTIGATION_PROFILE_SYSTEM_SPEC.md`
- CLI reference: `docs/03_CLI_QUICKSTART.md`
- MCP integration: `docs/04_MCP_QUICKSTART.md`
