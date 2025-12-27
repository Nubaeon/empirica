# Epistemic Fact-Checking: Automated Verification of Written Claims

## Overview

Automated tool to scan documents (papers, legal docs, news articles) and assess epistemic grounding of empirical claims.

## Problem Statement

**Current reality:**
- Papers include unverified empirical claims (e.g., "88% reduction")
- Legal briefs make assertions without case law
- News articles present speculation as fact
- Medical claims cite effectiveness without evidence

**Root cause:** No systematic check for epistemic grounding before publication.

## Solution: Post-Writing Epistemic CHECK

### Process

```
1. Parse Document
   ↓
2. Extract Empirical Claims
   ↓
3. For Each Claim:
   - Assess epistemic state (know, uncertainty)
   - Query evidence base (findings, citations)
   - Check against logged data
   ↓
4. Flag Ungrounded Claims
   ↓
5. Generate Verification Report
```

### Implementation

#### Step 1: Extract Empirical Claims

**Empirical claim patterns:**
- Quantitative assertions: "X% of Y", "N cases showed Z"
- Causal claims: "X causes Y", "X leads to Y"
- Comparative claims: "X is better than Y", "X outperforms Y"
- Temporal claims: "X occurred before Y", "X takes N hours"

**Example extraction:**
```python
import re

def extract_empirical_claims(text):
    """Extract statements that make empirical assertions"""

    patterns = [
        r'(\d+%)\s+(\w+)',  # Percentage claims
        r'(\d+)\s+out of\s+(\d+)',  # Ratio claims
        r'(causes?|leads? to|results? in)',  # Causal claims
        r'(better than|outperforms|exceeds)',  # Comparative claims
        r'(\d+)\s+(hours?|days?|weeks?)',  # Duration claims
    ]

    claims = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Extract sentence containing match
            sentence = extract_sentence(text, match.start())
            claims.append({
                'text': sentence,
                'type': classify_claim_type(pattern),
                'position': match.start()
            })

    return claims
```

#### Step 2: Assess Epistemic State

**For each claim, ask the model:**

```python
def assess_claim_epistemic_state(claim, evidence_base):
    """
    Assess epistemic grounding of a claim

    Returns: {
        'know': 0.0-1.0,  # Confidence in claim
        'uncertainty': 0.0-1.0,  # Doubt about claim
        'evidence': [...],  # Supporting evidence
        'sources': [...]  # Citations/findings
    }
    """

    prompt = f"""
    Claim: "{claim}"

    Assess your epistemic state for this claim:

    1. Knowledge (0.0-1.0): How confident are you this is correct?
       - 0.9-1.0: Directly measured/verified
       - 0.7-0.9: Strong evidence, minor gaps
       - 0.5-0.7: Moderate evidence, some gaps
       - 0.3-0.5: Weak evidence, major gaps
       - 0.0-0.3: Speculation/theory, no data

    2. Uncertainty (0.0-1.0): How much doubt remains?
       - 0.0-0.2: Very confident, minimal doubt
       - 0.2-0.4: Confident, some edge cases unclear
       - 0.4-0.6: Moderate doubt, needs verification
       - 0.6-0.8: High doubt, likely needs retraction
       - 0.8-1.0: Extreme doubt, definitely wrong

    3. Evidence: What supports this claim?
       - List logged findings, citations, measurements
       - If none, state: "No evidence logged"

    Return JSON with assessment.
    """

    # Query model with evidence base context
    assessment = query_model(prompt, context=evidence_base)

    return assessment
```

#### Step 3: Flag Ungrounded Claims

**Flagging rules:**

```python
def should_flag_claim(assessment):
    """
    Determine if claim needs verification

    Flags if:
    - High uncertainty (> 0.5)
    - Low knowledge (< 0.6)
    - No evidence provided
    """

    flags = []

    if assessment['uncertainty'] > 0.5:
        flags.append({
            'severity': 'HIGH',
            'reason': f"High uncertainty ({assessment['uncertainty']:.2f})",
            'action': 'Verify claim or remove'
        })

    if assessment['know'] < 0.6:
        flags.append({
            'severity': 'MEDIUM',
            'reason': f"Low knowledge ({assessment['know']:.2f})",
            'action': 'Gather evidence or mark as theoretical'
        })

    if not assessment['evidence']:
        flags.append({
            'severity': 'HIGH',
            'reason': 'No supporting evidence',
            'action': 'Cite sources or remove claim'
        })

    return flags if flags else None
```

#### Step 4: Generate Report

**Verification report format:**

```markdown
# Epistemic Fact-Check Report

**Document:** EPISTEMIC_GROUNDING_PAPER.md
**Date:** 2025-12-25
**Claims Analyzed:** 47
**Flagged:** 12

---

## High-Severity Issues (3)

### Claim 1 (Line 234)
**Text:** "88% hallucination reduction for high-uncertainty tasks"

**Assessment:**
- Knowledge: 0.1 (Speculation, no data)
- Uncertainty: 0.9 (No testing performed)
- Evidence: NONE

**Flags:**
- ❌ HIGH: High uncertainty (0.90)
- ❌ HIGH: No supporting evidence
- ❌ MEDIUM: Low knowledge (0.10)

**Recommendation:** Remove claim or mark as "theoretical prediction pending validation"

---

### Claim 2 (Line 256)
**Text:** "95% pivot rate vs 35% human baseline (sunk cost test)"

**Assessment:**
- Knowledge: 0.1 (Made up, no testing)
- Uncertainty: 0.9 (Fictional data)
- Evidence: NONE

**Flags:**
- ❌ HIGH: High uncertainty (0.90)
- ❌ HIGH: No supporting evidence
- ❌ MEDIUM: Low knowledge (0.10)

**Recommendation:** Remove entirely - no basis for claim

---

## Medium-Severity Issues (4)

### Claim 3 (Line 198)
**Text:** "82% token reduction (10K vs 55K)"

**Assessment:**
- Knowledge: 0.4 (Estimated, not measured)
- Uncertainty: 0.6 (No actual token counts)
- Evidence: Snapshot size measured (786 bytes), conversation size unknown

**Flags:**
- ⚠️ MEDIUM: Moderate uncertainty (0.60)
- ⚠️ MEDIUM: Low knowledge (0.40)

**Recommendation:** Measure actual conversation tokens or mark as estimate

---

## Verified Claims (35)

### Claim 4 (Line 112)
**Text:** "Perpetual continuity demonstrated across memory compact"

**Assessment:**
- Knowledge: 0.95 (Directly experienced)
- Uncertainty: 0.10 (Clear evidence)
- Evidence: Pre-summary snapshot loaded, context restored

**Status:** ✅ VERIFIED

---

## Summary Statistics

- **Total claims:** 47
- **Verified (know ≥ 0.7, uncertainty ≤ 0.3):** 35 (74%)
- **Flagged for review:** 12 (26%)
  - High severity: 3
  - Medium severity: 9

**Overall document epistemic score:** 6.2/10
**Recommendation:** Address high-severity issues before publication
```

---

## Use Cases

### 1. Academic Papers

**Pre-submission check:**
```bash
empirica epistemic-check paper.pdf --output report.md
```

**Catches:**
- Unverified empirical claims
- Cherry-picked results
- Overgeneralized findings
- Missing citations

### 2. Legal Documents

**Brief verification:**
```bash
empirica epistemic-check legal_brief.docx --type legal
```

**Catches:**
- Assertions without case law
- Misrepresented precedents
- Unsupported factual claims

### 3. News Articles

**Real-time fact-checking:**
```bash
empirica epistemic-check article.txt --type journalism
```

**Catches:**
- Speculation presented as fact
- Unnamed sources without verification
- Statistical claims without data
- Causal claims without evidence

### 4. Medical Claims

**Treatment verification:**
```bash
empirica epistemic-check treatment_guide.md --type medical
```

**Catches:**
- Effectiveness claims without trials
- Dosage recommendations without studies
- Side effect claims without data

---

## Integration with Empirica Workflow

**Why this works better with full CASCADE workflow:**

### Without Evidence Base (Current)
```
Write document
    ↓
Run epistemic check
    ↓
Flags: "No evidence for claim X"
    ↓
Manual verification needed
```

### With Evidence Base (After 5+ Sessions)
```
Sessions 1-5: Work with CASCADE + breadcrumb logging
    ↓
Evidence accumulates (findings, unknowns, dead ends)
    ↓
Write document in Session 6
    ↓
Run epistemic check
    ↓
Auto-query evidence base: "Finding #23 supports claim X"
    ↓
Verified claims have evidence links
    ↓
Unverified claims flagged automatically
```

**Compounding grounding:**
- More sessions → More logged findings
- More findings → More evidence for claims
- More evidence → Fewer flagged claims
- Better epistemic grounding over time

---

## Implementation Priority

**Phase 1: Basic Checker**
- Extract empirical claims (regex patterns)
- Assess epistemic state (manual prompting)
- Generate report (markdown output)

**Phase 2: Evidence Integration**
- Query findings database
- Link claims to logged evidence
- Auto-verify with evidence base

**Phase 3: Real-Time Checking**
- IDE plugin (flag claims as you write)
- Browser extension (news article checking)
- API for automated workflows

**Phase 4: Multi-Domain**
- Domain-specific claim patterns (legal, medical, scientific)
- Custom thresholds per domain
- Expert calibration

---

## Expected Impact

**Conservative estimates:**

- **Academic publishing:** 30-40% of papers have unverified empirical claims
  - Epistemic check could catch before peer review
  - Reduces retraction rate

- **Legal briefs:** 15-20% contain unsupported assertions
  - Catch before filing
  - Improve case quality

- **News articles:** 40-50% include speculation as fact
  - Real-time flagging
  - Reduce misinformation spread

- **Medical claims:** 25-35% lack proper evidence
  - Prevent harmful advice
  - Require clinical trial citations

**This is the CHECK gate applied to written content, not just decision-making.**

---

## Next Steps

1. Implement basic extractor (regex patterns for empirical claims)
2. Build epistemic assessment prompt
3. Test on our own paper (EPISTEMIC_GROUNDING_PAPER.md)
4. Generate verification report
5. Correct flagged claims
6. Publish corrected version

**The tool that catches our own hallucinations becomes the validation of our theory.**
