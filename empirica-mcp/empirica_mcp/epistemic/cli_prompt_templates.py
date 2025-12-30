"""
CLI Prompt Templates - Human-Readable Epistemic Guidance

These templates provide human-friendly guidance for PREFLIGHT, CHECK, and POSTFLIGHT
assessments. Emphasis on narrative reasoning and honest self-assessment.
"""

from typing import Dict, Any
from .shared_vector_semantics import (
    ALL_VECTORS,
    READINESS_THRESHOLDS,
    assess_readiness
)


def preflight_guidance(context: Dict[str, Any] = None) -> str:
    """
    Generate PREFLIGHT guidance for human CLI users.
    
    Args:
        context: Optional context (task description, goal, etc.)
    
    Returns:
        Human-readable guidance string
    """
    guidance = """
## 🎯 PREFLIGHT Assessment - Honest Baseline

**Purpose:** Establish what you ACTUALLY know before starting (not what you could figure out).

**Key Principle:** Rate your CURRENT knowledge, not your potential. "I could research X" ≠ "I know X"

### Foundation Vectors (Always Required):

  **engagement** (0.0-1.0): Am I focused on the right thing?
    • 0.0 = Distracted, unmotivated
    • 1.0 = Fully engaged, clear focus
    • GATE: Must be ≥0.6 to proceed

  **know** (0.0-1.0): Do I understand the domain/concepts?
    • 0.0 = Complete guessing, no knowledge
    • 1.0 = Expert understanding
    • Be honest: "I know OAuth2 exists" ≠ "I know how to implement it"

  **do** (0.0-1.0): Can I execute this with available skills/tools?
    • 0.0 = Cannot execute, missing capabilities
    • 1.0 = Fully capable, all tools available

  **context** (0.0-1.0): Do I understand the situation?
    • 0.0 = No context, isolated understanding
    • 1.0 = Complete situational awareness (files, architecture, constraints)

### Comprehension Vectors (As Needed):

  **clarity** (0.0-1.0): Is the task clear?
  **coherence** (0.0-1.0): Does it make sense?
  **signal** (0.0-1.0): Can I see what's important?
  **density** (0.0-1.0): How much information do I have?

### Execution Vectors (As Needed):

  **state** (0.0-1.0): Do I understand current state?
  **change** (0.0-1.0): Do I understand what needs to change?
  **completion** (0.0-1.0): Starting point (usually 0.0-0.2)
  **impact** (0.0-1.0): Expected value (estimate)

### Meta - Uncertainty (CRITICAL):

  **uncertainty** (0.0-1.0): What don't I know?
    • 0.0 = Completely certain
    • 1.0 = Completely lost
    • High uncertainty (>0.6) → INVESTIGATE first
    • Low uncertainty (<0.3) + high know → PROCEED

### Reasoning (REQUIRED):

Write a brief narrative explaining your assessment:
  "I know X from previous work. Uncertain about Y because Z. Starting fresh (state=0.1)."

**Submit with:** `empirica preflight-submit --session-id <ID> --vectors {...} --reasoning "..."`
"""
    return guidance.strip()


def check_guidance(vectors: Dict[str, float], findings: list, unknowns: list) -> str:
    """
    Generate CHECK guidance based on current state.
    
    Args:
        vectors: Current vector values
        findings: What's been learned
        unknowns: What remains unclear
    
    Returns:
        Human-readable CHECK guidance with decision recommendation
    """
    readiness = assess_readiness(vectors)
    confidence = vectors.get("know", 0.0)
    uncertainty = vectors.get("uncertainty", 1.0)
    
    guidance = f"""
## ⚡ CHECK Gate - Proceed or Investigate?

**Current State:**
  Confidence (know): {confidence:.2f}
  Uncertainty: {uncertainty:.2f}
  Findings logged: {len(findings)}
  Unknowns remaining: {len(unknowns)}

**Readiness Assessment:**
  Overall ready: {'✅ YES' if readiness['ready'] else '❌ NO'}
  
  Gates:
    {'✅' if readiness['gates_passed']['engagement'] else '❌'} Engagement (≥0.6)
    {'✅' if readiness['gates_passed']['uncertainty'] else '❌'} Uncertainty (≤0.35)
    {'✅' if readiness['gates_passed']['context'] else '❌'} Context (≥0.5)
    {'✅' if readiness['gates_passed']['confidence'] else '❌'} Confidence (know ≥0.7 AND uncertainty ≤0.35)

"""
    
    if readiness['blockers']:
        guidance += "**Blockers:**\n"
        for blocker in readiness['blockers']:
            guidance += f"  • {blocker}\n"
        guidance += "\n"
    
    # Decision recommendation
    if confidence >= 0.7 and uncertainty <= 0.35:
        guidance += """
**RECOMMENDATION: ✅ PROCEED**
  You have sufficient confidence and low uncertainty.
  Continue with implementation/work.
"""
    elif uncertainty > 0.6:
        guidance += """
**RECOMMENDATION: 🔍 INVESTIGATE**
  Uncertainty is too high to proceed safely.
  Use: `empirica investigate --session-id <ID> --goal "Clarify X"`
  OR: `empirica project-bootstrap --depth full` to load context
"""
    elif 0.35 < uncertainty <= 0.6:
        guidance += """
**RECOMMENDATION: ❓ ASK OR INVESTIGATE**
  Moderate uncertainty. Consider:
    - If context ≥0.5: Ask specific questions first
    - If context <0.3: Investigate/load context first
"""
    else:
        guidance += """
**RECOMMENDATION: ⚠️ REVIEW**
  Vector state is unusual. Review your assessment.
  Are you being honest about what you know vs what you can figure out?
"""
    
    guidance += "\n**Submit decision:** `empirica check --session-id <ID> --confidence X.XX --findings [...] --unknowns [...]`"
    
    return guidance.strip()


def postflight_guidance(preflight_vectors: Dict[str, float], current_estimate: Dict[str, float]) -> str:
    """
    Generate POSTFLIGHT guidance showing what was learned.
    
    Args:
        preflight_vectors: Baseline from PREFLIGHT
        current_estimate: Your current assessment of vectors
    
    Returns:
        Human-readable POSTFLIGHT guidance with delta analysis
    """
    # Calculate deltas
    deltas = {}
    for key in current_estimate:
        if key in preflight_vectors:
            deltas[key] = current_estimate[key] - preflight_vectors[key]
    
    guidance = """
## 🎓 POSTFLIGHT Assessment - What Did You Learn?

**Purpose:** Measure ACTUAL learning by comparing to PREFLIGHT baseline.

**Key Question:** What changed? Be specific about knowledge gains and uncertainty reduction.

### Vector Deltas (Current - Baseline):

"""
    
    # Show significant changes
    significant_changes = [(k, v) for k, v in deltas.items() if abs(v) >= 0.10]
    if significant_changes:
        guidance += "**Significant Changes (≥0.10):**\n"
        for vector, delta in significant_changes:
            direction = "↑" if delta > 0 else "↓"
            guidance += f"  {direction} {vector}: {delta:+.2f}\n"
        guidance += "\n"
    
    # Guidance on what good learning looks like
    guidance += """
**Good Learning Patterns:**
  ✓ KNOW increases (+0.10 to +0.30) - You learned domain knowledge
  ✓ UNCERTAINTY decreases (-0.20 to -0.50) - You resolved doubts
  ✓ CONTEXT increases (+0.15 to +0.40) - You understand the system better
  ✓ COMPLETION increases (+0.60 to +1.00) - You made progress
  
**Warning Patterns:**
  ⚠️ KNOW unchanged or decreased - Did you actually learn anything?
  ⚠️ UNCERTAINTY unchanged or increased - Still confused? Need more investigation?
  ⚠️ All deltas near zero - Were you honest in PREFLIGHT? Or did you not learn?

### Reasoning (CRITICAL):

Explain what you learned in narrative form:
  "KNOW +0.15 because I learned OAuth2 requires PKCE for mobile apps."
  "UNCERTAINTY -0.40 because I found the auth flow diagram in docs."
  "CONTEXT +0.20 because I now understand how sessions are stored."

**Submit with:** `empirica postflight-submit --session-id <ID> --vectors {...} --reasoning "..."`

**Next Step:** Create snapshot for handoff:
  `empirica session-snapshot <SESSION_ID> --output json > snapshot.json`
"""
    
    return guidance.strip()


def get_vector_interpretation(vector_name: str, value: float) -> str:
    """
    Get human-readable interpretation of a vector value.
    
    Args:
        vector_name: Name of vector
        value: Value (0.0-1.0)
    
    Returns:
        Interpretation string
    """
    vector_def = ALL_VECTORS.get(vector_name)
    if not vector_def:
        return f"Unknown vector: {vector_name}"
    
    if value < 0.3:
        interpretation = "LOW - " + vector_def.scale_min_meaning
    elif value < 0.6:
        interpretation = "MODERATE"
    elif value < 0.8:
        interpretation = "GOOD"
    else:
        interpretation = "HIGH - " + vector_def.scale_max_meaning
    
    return f"{vector_name} = {value:.2f}: {interpretation}"
