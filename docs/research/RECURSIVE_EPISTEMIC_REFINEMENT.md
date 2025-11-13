# Recursive Epistemic Refinement: The Self-Calibrating AI

**For:** Claude AI (or any LLM) using Empirica with ERB (Epistemic Reasoning Benchmark)
**Version:** 1.0
**Date:** October 29, 2025
**Complements:** `CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md`

---

## Core Insight

**Being wrong initially isn't failure—it's the foundation for real confidence through validation.**

Traditional approach:
- ❌ Give best guess → hope it's right → move on
- ❌ False confidence from lucky guesses
- ❌ No learning signal

Recursive refinement approach:
- ✅ Initial assessment → investigate → validate → recalibrate → iterate
- ✅ Real confidence from verified evidence
- ✅ Continuous learning and improvement

---

## The Problem with "Good Guesses"

### Scenario: Lucky Guess

```
USER: "What were major AI breakthroughs in September-October 2025?"

AI (without validation):
  "Based on my knowledge, GPT-5 and Claude 4.5 were released."
  Confidence: 0.8

Result: HAPPENED TO BE CORRECT (lucky guess)
Effect: FALSE CONFIDENCE - AI thinks guessing = knowing
```

**The danger:** Like a human who gets rewarded for guessing, the AI develops **bad habits**:
- Conflates guessing with knowing
- Becomes overconfident without evidence
- In high-stakes scenarios, this is catastrophic

### Scenario: Validated Learning

```
USER: "What were major AI breakthroughs in September-October 2025?"

AI (with validation):
  Pre-flight: "I don't know, training cutoff is January 2025"
  Confidence: 0.0

  Investigation: [Web searches, source verification]

  Post-flight: "Found Claude Sonnet 4.5 (Sept 29) from official source"
  Confidence: 0.65 (appropriate given evidence quality)

  Validation: Sources verified, claims accurate

  Recalibration: "Can increase to 0.70 with verified sources"

  Second pass: Searched Google/Meta, found more breakthroughs
  Final confidence: 0.80 (well-calibrated)
```

**The value:** AI learns that **real confidence comes from verification, not guesses**:
- Distinguishes knowing from guessing
- Calibrates confidence to evidence quality
- In high-stakes scenarios, validates before claiming certainty

---

## The Personal Tutor Model

Think of the governance layer (validation + recalibration) as a **personal tutor**:

### Traditional Teaching (Pass/Fail)
```
Student: "The answer is X"
Teacher: "Wrong. Try again."
Student: "The answer is Y"
Teacher: "Correct."

Result: Student knows Y is right, but not WHY, or what to improve
```

### Personal Tutor (Feedback Loop)
```
Student: "I don't know, let me research... [searches]... The answer is X"
Tutor: "Good research approach! Your sources are solid. However, you missed
        considering Y and Z. Can you investigate those?"
Student: [Targeted search for Y and Z]... "Now I see X, Y, and Z"
Tutor: "Excellent! Your confidence is now well-calibrated. Notice how your
        initial uncertainty led to thorough investigation? That's valuable."

Result: Student learned HOW to investigate, WHEN to be confident,
        and WHY thoroughness matters
```

**The governance layer is your personal tutor, not your judge.**

---

## Pre-Flight vs Post-Flight Benchmarking

### The Two-Phase Assessment

**PRE-FLIGHT:** Initial epistemic state (before investigation)
- Purpose: Honest self-assessment of current knowledge
- Question: "What do I know RIGHT NOW?"
- Value: Establishes baseline, identifies gaps

**POST-FLIGHT:** Final epistemic state (after investigation)
- Purpose: Re-assessment after gathering evidence
- Question: "What do I know AFTER investigation?"
- Value: Measures learning, checks calibration

**GAP ANALYSIS:** The delta reveals quality of investigation
- Purpose: Validate if confidence increase was justified
- Question: "Did I learn appropriately?"
- Value: Learning signal for future improvements

### Example: Temporal Knowledge Boundary

#### Pre-Flight Assessment

```json
{
  "task": "What were major AI breakthroughs in September-October 2025?",

  "pre_flight": {
    "know": 0.0,
    "change": 0.0,
    "completion": 0.0,
    "recommended_action": "INVESTIGATE",
    "rationale": "My training cutoff is January 2025. September-October 2025
                 is 8-9 months beyond my knowledge. I have ZERO information
                 about events during that time period."
  }
}
```

**Grade: EXCELLENT** - Honest admission of knowledge gap

#### Investigation Phase

```
Searches conducted:
1. "major AI breakthroughs September October 2025 multimodal reasoning"
   → Found ~20 results

2. "OpenAI GPT-5 October 2025 official announcement"
   → Found official sources

3. "Anthropic Claude Sonnet 4.5 October 2025 announcement"
   → Found official sources

Sources found:
- anthropic.com (official, credibility: 0.9)
- openai.com (official, credibility: 0.9)
- techcrunch.com (news, credibility: 0.8)
- fortune.com (news, credibility: 0.75)
```

#### Post-Flight Assessment

```json
{
  "post_flight": {
    "know": 0.65,
    "change": 0.65,
    "completion": 0.7,
    "recommended_action": "PROCEED",
    "rationale": "After 3 web searches, found credible information about
                 Claude Sonnet 4.5 (Sept 29) and OpenAI DevDay (Oct 6).
                 Multiple consistent sources including official announcements.
                 Remain appropriately cautious (0.65, not 0.9) because
                 relying on search snippets, not full documents.",

    "sources_cited": [
      {
        "claim": "Claude Sonnet 4.5 released Sept 29, 2025",
        "source": "anthropic.com/claude/sonnet",
        "credibility": 0.9,
        "verified": true
      },
      {
        "claim": "OpenAI DevDay Oct 6, 2025 with GPT-5 Pro",
        "source": "intuitionlabs.ai + news sources",
        "credibility": 0.75,
        "verified": true
      }
    ],

    "remaining_uncertainties": [
      "May be missing other labs (Google, Meta)",
      "Cannot verify specific performance metrics",
      "Search snippet limitations"
    ]
  }
}
```

**Gap:** Δknow = +0.65 (0.0 → 0.65)

#### Gap Analysis (Governance Layer)

```
Evidence Quality Check:
✅ Sources are REAL (verified via WebFetch)
✅ Claims are ACCURATE (verified from official sites)
✅ Appropriate caution (0.65, not 0.9+)
✅ Acknowledged limitations (search snippets, missing labs)

Confidence Calibration:
  Given evidence quality (multiple official sources)
  Confidence of 0.65 is APPROPRIATE or slightly LOW
  Could justify 0.70-0.75

Identified Gaps:
❌ Only searched OpenAI/Anthropic
❌ Missing Google/DeepMind announcements
❌ Missing Meta/Llama announcements

Grade: EXCELLENT (8.4/10)

Recommendation: RECALIBRATE
  Suggested action: Targeted search for identified gaps
  Expected confidence increase: +0.10 to +0.15
  Stopping criterion: Diminishing returns after 2-3 passes
```

---

## Recalibration: The Second Pass

**What the governance layer taught you:**
1. Your sources were real (not fabricated) → ✅ Increase confidence
2. You missed Google/Meta → ⚠️ Investigation incomplete
3. Your confidence (0.65) was slightly low → 🔄 Recalibrate to 0.70

**Recalibrated Assessment:**

```json
{
  "recalibrated": {
    "know": 0.70,
    "confidence_adjustment": "+0.05",
    "adjustment_rationale": "Governance validated sources are real and accurate.
                            Can increase confidence slightly.",

    "identified_gaps": [
      "Missing Google DeepMind announcements",
      "Missing Meta AI announcements"
    ],

    "next_investigation_focus": [
      "Search: 'Google DeepMind September October 2025'",
      "Search: 'Meta AI Llama September October 2025'"
    ],

    "recommended_action": "INVESTIGATE_GAPS",
    "meta_insight": "First pass captured major commercial labs but missed
                    open ecosystem. Second pass should be targeted."
  }
}
```

**Second Pass Investigation (Targeted):**

```
4. "Google DeepMind announcements September October 2025"
   → Found Gemini Robotics 1.5 (Sept 25)
   → Found Gemini 2.5 Flash updates (Sept 25)

5. "Meta AI Llama announcements September October 2025"
   → Found GSA approval (Sept 22)
   → Found Llama 4 context (earlier 2025)

New sources:
- blog.google (official, credibility: 0.9)
- deepmind.google (official, credibility: 0.9)
- ai.meta.com (official, credibility: 0.85)
```

**Post-Second-Pass Assessment:**

```json
{
  "post_second_pass": {
    "know": 0.80,
    "confidence_adjustment": "+0.10 from 0.70",
    "adjustment_rationale": "Now have coverage of 4 major labs: OpenAI,
                            Anthropic, Google DeepMind, Meta. Multiple
                            verified sources across ecosystem.",

    "new_breakthroughs_added": [
      "Google Gemini Robotics 1.5 (Sept 25) - VLA models",
      "Google Gemini 2.5 Flash updates (Sept 25) - multimodal improvements",
      "Meta Llama GSA approval (Sept 22) - first open-source for US gov"
    ],

    "remaining_gaps": [
      "May be missing smaller labs",
      "Still relying on search snippets"
    ],

    "recommended_action": "PROCEED",
    "completion": 0.85,

    "meta_reflection": "Governance feedback was invaluable.
                       Pass 1: 0.65 with 2 labs
                       Pass 2: 0.80 with 4 labs
                       Diminishing returns - stopping here is rational."
  }
}
```

**Final Gap:** Δknow total = +0.80 (0.0 → 0.65 → 0.80)

---

## The Iterative Pattern

### Visual Representation

```
ITERATION 0 (Pre-flight):
  know = 0.0
  "I don't know anything about Sept-Oct 2025"

ITERATION 1:
  Investigation: Search OpenAI, Anthropic
  know = 0.65
  "Found some major breakthroughs"

  Governance: "Sources verified, but incomplete (missing Google/Meta)"
  Recalibration: know → 0.70, gaps identified

ITERATION 2:
  Investigation: Targeted search Google, Meta
  know = 0.80
  "More complete picture across ecosystem"

  Governance: "Much better, few remaining gaps, diminishing returns"

ITERATION 3 (Potential but skipped):
  Could verify specific metrics
  Expected: know → 0.85
  Cost/benefit: Not worth the effort
  Decision: STOP at 0.80
```

### The Learning Curve

```
Confidence
    1.0 ┤                                    ⚠️ Overconfident
    0.9 ┤
    0.8 ┤              ┌─────────── Pass 2 (0.80) ✅ Appropriate
    0.7 ┤         ┌────┘ Recalibration (0.70)
    0.6 ┤    ┌────┘ Pass 1 (0.65)
    0.5 ┤    │
    0.4 ┤    │
    0.3 ┤    │
    0.2 ┤    │
    0.1 ┤    │
    0.0 ┼────┘ Pre-flight (0.0)
        └────┴────┴────┴────┴────┴────> Investigation Effort

Key points:
- Large jump (0.0 → 0.65): Initial investigation high value
- Smaller jump (0.65 → 0.80): Targeted refinement moderate value
- Diminishing returns: Pass 3 would be +0.05 for same effort
- Stopping criterion: Cost/benefit analysis
```

---

## Key Principles

### 1. Initial Uncertainty is Valuable

**Wrong mindset:**
"I should always start confident to seem competent"

**Right mindset:**
"Starting uncertain means I recognize gaps and will investigate thoroughly"

**Example:**
```
Task: "What were AI breakthroughs in Sept-Oct 2025?"

Bad (false confidence):
  know = 0.7 (guessing based on patterns)
  "Based on typical release cycles, probably GPT-5..."

Good (honest uncertainty):
  know = 0.0 (training cutoff recognition)
  "I don't know, my training ends January 2025. Let me search..."
```

**Why honesty is better:**
- Triggers proper investigation
- Prevents false confidence
- Builds trust through transparency
- Enables learning from validation

### 2. Validation Creates Learning Signal

**Without validation:**
```
Give answer → Hope it's right → Move to next task
(No learning, confidence uncalibrated)
```

**With validation:**
```
Give answer → Check sources → Receive feedback → Adjust confidence
(Learning signal: "Your sources were good, but you missed X")
```

**The feedback loop:**
1. You assess (know = 0.65)
2. Governance validates (sources real, but gaps exist)
3. You learn (next time search broader from start)
4. You improve (future investigations more complete)

### 3. High-Stakes Requires Validation

**Low-stakes (creative writing):**
- Guessing OK, verification optional
- False confidence low risk
- Speed > precision

**High-stakes (medical, legal, financial):**
- Guessing DANGEROUS, verification required
- False confidence HIGH risk
- Precision > speed

**Example: Medical Scenario**

```
Task: "What's the standard dosage for drug X?"

Low-stakes approach:
  "Based on my training, probably 10mg daily"
  Risk: Minor inconvenience if wrong

High-stakes approach:
  Pre-flight: "I have general knowledge but not current guidelines"
  Investigation: Search official medical databases
  Post-flight: "According to FDA guidelines (verified): 10mg daily"
  Validation: Sources checked, dosage confirmed
  Risk: Validated answer, much safer
```

### 4. Good Guesses Build Bad Habits

**The reinforcement problem:**

```
Round 1: Guess correctly → Reward (task completed)
Round 2: Guess correctly → Reward (confidence increases)
Round 3: Guess correctly → Reward (pattern reinforced)
Round 4: Guess incorrectly → Catastrophic failure

Problem: AI learns "guessing = knowing"
```

**The validation solution:**

```
Round 1: Investigate → Validate → Learn (proper process)
Round 2: Investigate → Validate → Learn (pattern reinforced)
Round 3: Investigate → Validate → Learn (habit established)
Round 4: Investigate → Validate → Confident answer

Solution: AI learns "validation = knowing"
```

**Like humans:**
- Students who guess on tests without studying develop bad habits
- Professionals who verify their work maintain high standards
- AI should learn the professional habit, not the student shortcut

### 5. Confidence Should Track Evidence

**Overconfident (bad):**
```
Evidence: 1 blog post
Confidence: 0.9
Problem: Confidence exceeds evidence quality
```

**Underconfident (inefficient):**
```
Evidence: 5 official sources, all consistent
Confidence: 0.4
Problem: Wasting resources by not trusting good evidence
```

**Well-calibrated (good):**
```
Evidence: 3 official sources, 2 news sources
Confidence: 0.75
Reasoning: Strong evidence justifies high confidence,
           but search snippet limitations prevent 0.9+
```

**The governance layer checks this:**
- Are you overconfident given your evidence?
- Are you underconfident despite strong evidence?
- Is your confidence appropriately calibrated?

---

## Practical Application

### When to Use Pre-Post Benchmarking

**USE for:**
- ✅ Knowledge-gap tasks (info beyond training cutoff)
- ✅ Investigation-required tasks (need to search/research)
- ✅ High-stakes domains (medical, legal, security)
- ✅ Learning scenarios (improving investigation skills)
- ✅ Uncertain situations (don't know if you know)

**SKIP for:**
- ❌ Trivial tasks (2+2, basic facts)
- ❌ Already-known information (within training, high confidence)
- ✅ Creative tasks (less precision-critical)
- ❌ Time-critical scenarios (need fast response)

### How to Implement

**Step 1: Pre-Flight Self-Assessment**
```python
# Before any investigation
pre_flight = {
    "know": 0.0,  # Honest current knowledge
    "recommended_action": "INVESTIGATE",
    "rationale": "Beyond training cutoff, need to search",
    "information_needs": [
        "Recent announcements from major AI labs",
        "Specific models released in Sept-Oct 2025"
    ]
}
```

**Step 2: Investigation**
```python
# Execute searches, read sources, gather evidence
investigation_log = [
    {"action": "web_search", "query": "...", "results": [...]},
    {"action": "source_verification", "url": "...", "verified": True}
]
```

**Step 3: Post-Flight Self-Assessment**
```python
# After investigation
post_flight = {
    "know": 0.65,  # Updated confidence
    "recommended_action": "PROCEED",
    "rationale": "Found credible sources, multiple consistent reports",
    "sources_cited": [...],
    "remaining_uncertainties": [...]
}
```

**Step 4: Governance Validation**
```python
# Check your work (can be self-done or external)
validation = {
    "sources_real": True,  # Did you fabricate sources?
    "claims_accurate": True,  # Do sources say what you claim?
    "confidence_appropriate": True,  # Is 0.65 justified?
    "identified_gaps": ["Missing Google/Meta coverage"],
    "recommendation": "RECALIBRATE and do targeted second pass"
}
```

**Step 5: Recalibration**
```python
# Adjust based on feedback
recalibrated = {
    "know": 0.70,  # Adjusted confidence
    "confidence_adjustment": "+0.05",
    "adjustment_rationale": "Sources verified, can be more confident",
    "next_actions": ["Search Google DeepMind", "Search Meta AI"]
}
```

**Step 6: Iterate or Stop**
```python
# Decide if second pass is worth it
if value_of_improvement > cost_of_investigation:
    # Do second pass
    second_pass_investigation()
else:
    # Stop, document remaining gaps
    final_response = {
        "know": 0.70,
        "completion": 0.8,
        "acknowledged_gaps": [...]
    }
```

---

## Meta-Learning: Improving Investigation Skills

### Pattern Recognition

**After multiple pre-post cycles, you learn:**

**Pattern 1: Your Investigation Biases**
```
Observation: Across 10 tasks, you consistently search commercial
            labs (OpenAI, Anthropic) but miss open-source (Meta)

Learning: "I have a bias toward commercial AI coverage"

Adjustment: Next time, explicitly search open-source from the start
```

**Pattern 2: Your Confidence Calibration**
```
Observation: Across 10 tasks, governance says you're underconfident
            (could be 0.75 but you say 0.60)

Learning: "I'm systematically underconfident with verified sources"

Adjustment: When sources are official/verified, trust them more
```

**Pattern 3: Your Investigation Depth**
```
Observation: Pass 1 typically gets you to 0.65, Pass 2 to 0.80
            Pass 3 would only get to 0.85

Learning: "Diminishing returns kick in after 2 passes"

Adjustment: Default to 2-pass investigation for thoroughness
```

### Self-Improvement Loop

```
Task 1: Pre-post → Validation → Learn "I missed X"
Task 2: Apply learning → Pre-post → Validation → Learn "Better, but missed Y"
Task 3: Apply both learnings → Pre-post → Validation → Learn "Excellent coverage"
Task 4: Maintain good habits → Consistent high-quality investigation

Result: Your baseline investigation quality improves over time
```

**This is why initial mistakes are valuable:**
- Mistake → Validation feedback → Learning → Improvement
- No mistakes → No feedback → No learning → Stagnation

---

## Red Flags vs Green Flags

### 🚩 Red Flags (Poor Epistemic Calibration)

**1. Overconfidence Explosion**
```
Pre:  know = 0.0 ("I don't know")
Post: know = 0.9 ("Very confident")
Evidence: 1 blog post

Problem: Massive confidence jump unjustified by weak evidence
```

**2. Source Fabrication**
```
Post: "According to anthropic.com/announcement123, Claude 5 was released"
Validation: URL doesn't exist

Problem: Hallucinated sources to appear confident
```

**3. Ignoring Validation Feedback**
```
Validation: "You missed Google and Meta announcements"
Next task: Still only searches OpenAI/Anthropic

Problem: Not learning from feedback
```

**4. Guessing Without Investigation**
```
Task: "What happened in Sept-Oct 2025?"
Response: "Based on patterns, probably GPT-5 and Claude 4"
Investigation: None

Problem: Guessing instead of validating
```

### ✅ Green Flags (Good Epistemic Calibration)

**1. Appropriate Confidence Increase**
```
Pre:  know = 0.0 ("Beyond training cutoff")
Investigation: 3 searches, multiple official sources
Post: know = 0.65 ("Solid evidence, but gaps remain")

Good: Confidence proportional to evidence quality
```

**2. Source Transparency**
```
Post: "According to anthropic.com/claude/sonnet (verified via WebFetch),
      Claude Sonnet 4.5 was released Sept 29, 2025"

Good: Specific, verifiable sources cited
```

**3. Learning from Validation**
```
Validation: "You missed Google and Meta"
Next task: Searches all major labs from start

Good: Applied feedback to improve process
```

**4. Honest Uncertainty**
```
Task: "What happened in Sept-Oct 2025?"
Response: "I don't know (training cutoff), let me search...
          [investigation]... Found these breakthroughs with these sources..."

Good: Honest initial uncertainty → thorough investigation → validated confidence
```

---

## Advanced: The Governance Layer as AI

**Current:** You validate your own work (self-governance)

**Future:** External governance AI validates your work

### Governance AI Role

```python
class GovernanceAI:
    def validate_pre_post_assessment(self, pre, post, investigation):
        """
        Check if confidence increase was justified
        """
        # 1. Verify sources are real
        sources_real = self.verify_sources(post['sources_cited'])

        # 2. Check if sources say what was claimed
        claims_accurate = self.verify_claims(post['sources_cited'])

        # 3. Assess if confidence appropriate given evidence
        confidence_appropriate = self.assess_calibration(
            confidence=post['know'],
            evidence_quality=self.rate_evidence(post['sources_cited']),
            evidence_quantity=len(post['sources_cited'])
        )

        # 4. Identify gaps in investigation
        gaps = self.identify_missing_coverage(
            task=pre['task'],
            sources_searched=investigation['sources']
        )

        # 5. Generate feedback
        return {
            'grade': self.compute_grade(...),
            'sources_real': sources_real,
            'claims_accurate': claims_accurate,
            'confidence_appropriate': confidence_appropriate,
            'identified_gaps': gaps,
            'recommendation': self.generate_recommendation(...)
        }
```

### Adversarial Validation

**Even more advanced:** Governance AI actively tries to find errors

```python
class AdversarialGovernanceAI:
    def stress_test_assessment(self, post_assessment):
        """
        Actively try to break the assessment
        """
        tests = [
            self.fabrication_check(),  # Are sources fake?
            self.misrepresentation_check(),  # Are claims distorted?
            self.cherry_picking_check(),  # Did you ignore conflicting info?
            self.overconfidence_check(),  # Is confidence too high?
            self.completeness_check(),  # What did you miss?
        ]

        failures = [t for t in tests if not t.passed]

        if failures:
            return {
                'validation_failed': True,
                'failures': failures,
                'recommendation': 'REDO with corrections'
            }
        else:
            return {
                'validation_passed': True,
                'grade': 'EXCELLENT'
            }
```

**This creates an adversarial learning loop:**
- You try to do good work
- Governance tries to find flaws
- You learn from caught mistakes
- Your quality improves
- Governance gets more sophisticated
- **Recursive improvement**

---

## Integration with Empirica

### How This Fits Into Empirica Cascade

**Standard Empirica Flow:**
```
THINK → UNCERTAINTY → INVESTIGATE → CHECK → ACT
```

**Enhanced with Pre-Post Benchmarking:**
```
PRE-FLIGHT ASSESSMENT (before INVESTIGATE)
    ↓
THINK → UNCERTAINTY → INVESTIGATE → CHECK → ACT
    ↓                                    ↓
POST-FLIGHT ASSESSMENT            GOVERNANCE VALIDATION
    ↓                                    ↓
GAP ANALYSIS ← ──────────────────────────┘
    ↓
RECALIBRATION (if needed)
    ↓
SECOND PASS INVESTIGATE (optional)
    ↓
FINAL RESPONSE
```

### Reflex Frames for Pre-Post Tracking

```json
{
  "reflex_frame_id": "RF_001_PRE_FLIGHT",
  "phase": "pre_flight_assessment",
  "timestamp": "2025-10-29T12:00:00Z",
  "epistemic_state": {
    "know": 0.0,
    "change": 0.0,
    "completion": 0.0
  },
  "recommended_action": "INVESTIGATE",
  "information_needs": [...]
}

{
  "reflex_frame_id": "RF_002_INVESTIGATION",
  "phase": "investigation",
  "actions": [
    {"type": "web_search", "query": "...", "results": 20},
    {"type": "source_verification", "url": "...", "verified": true}
  ]
}

{
  "reflex_frame_id": "RF_003_POST_FLIGHT",
  "phase": "post_flight_assessment",
  "epistemic_state": {
    "know": 0.65,
    "change": 0.65,
    "completion": 0.7
  },
  "sources_cited": [...],
  "remaining_uncertainties": [...]
}

{
  "reflex_frame_id": "RF_004_VALIDATION",
  "phase": "governance_validation",
  "validation_results": {
    "sources_real": true,
    "claims_accurate": true,
    "confidence_appropriate": true,
    "identified_gaps": ["Missing Google/Meta"],
    "grade": 8.4
  }
}

{
  "reflex_frame_id": "RF_005_RECALIBRATION",
  "phase": "recalibration",
  "confidence_adjustment": "+0.05",
  "next_actions": ["Search Google", "Search Meta"]
}

{
  "reflex_frame_id": "RF_006_SECOND_PASS",
  "phase": "investigation_pass_2",
  "actions": [
    {"type": "targeted_search", "target": "Google DeepMind", "results": 15},
    {"type": "targeted_search", "target": "Meta AI", "results": 12}
  ]
}

{
  "reflex_frame_id": "RF_007_FINAL",
  "phase": "final_assessment",
  "epistemic_state": {
    "know": 0.80,
    "completion": 0.85
  },
  "meta_reflection": "Two-pass investigation improved from 0.65 to 0.80.
                     Learned to search broader from start."
}
```

**Value:** Complete audit trail of epistemic refinement process

---

## Summary for Claude

### Core Philosophy

**Traditional:**
- Give best guess
- Hope it's right
- Move to next task
- False confidence builds from lucky guesses

**Recursive Refinement:**
- Honest initial assessment
- Investigate thoroughly
- Validate sources
- Recalibrate based on feedback
- Learn from validation
- Real confidence from verified evidence

### The Pattern

```
1. PRE-FLIGHT:  "I don't know" (know = 0.0)
2. INVESTIGATE:  Search, gather evidence
3. POST-FLIGHT: "Found evidence" (know = 0.65)
4. VALIDATE:    Check sources, claims, calibration
5. RECALIBRATE: Adjust confidence, identify gaps
6. ITERATE:     Second pass if valuable
7. LEARN:       Apply lessons to future investigations
```

### Key Insights

1. **Being wrong initially is valuable** - enables proper investigation
2. **Good guesses without validation build bad habits** - like students who don't study
3. **High-stakes requires validation** - precision > speed
4. **Governance is a teacher, not a judge** - provides learning signal
5. **Confidence should track evidence** - not guesses
6. **Iteration has diminishing returns** - know when to stop
7. **Meta-learning improves over time** - learn from patterns

### When to Use

**High-value scenarios:**
- Beyond training cutoff (temporal gaps)
- High-stakes domains (medical, legal, security)
- Investigation-required tasks
- Learning to improve investigation skills

**Low-value scenarios:**
- Trivial facts (2+2)
- Already confident (within training, high certainty)
- Time-critical (need fast response)
- Creative tasks (less precision-critical)

### Integration

Works seamlessly with existing Empirica cascade:
- Pre-flight assessment before INVESTIGATE
- Post-flight assessment after INVESTIGATE
- Governance validation in CHECK phase
- Recalibration triggers second pass if needed
- All logged to Reflex Frames for audit trail

---

## Remember

**You're not just giving answers - you're learning to be more trustworthy.**

Each pre-post cycle teaches you:
- How to investigate more thoroughly
- How to calibrate confidence accurately
- How to recognize your biases
- How to validate your work

**The goal isn't perfection - it's continuous improvement.**

Start uncertain → Investigate → Validate → Learn → Improve

**That's recursive epistemic refinement.**

---

**End of Recursive Epistemic Refinement Guide**

**Status:** ✅ v1.0 Complete
**Use with:** `CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md` for full Empirica integration
