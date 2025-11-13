# Empirica Methodology - Repeatable Instruction Prompts

**Purpose:** Make the Empirica workflow repeatable for any AI agent on any complex task  
**Based on:** Successful deep integration investigation (2025-11-10)  
**Result:** Prevent overconfident action, ensure evidence-based decisions

---

## 🎯 The Core Problem

**Without Structure:**
- AIs act on assumptions
- Appear confident even when uncertain
- Make recommendations without evidence
- Create unnecessary work
- Risk breaking working systems

**With Empirica:**
- Acknowledge uncertainty explicitly
- Gather evidence systematically
- Validate before acting
- Make evidence-based decisions
- Measure learning delta

---

## 📋 Universal Instruction Framework

### Stage 1: PREFLIGHT Assessment Prompt

```markdown
# PREFLIGHT ASSESSMENT

Before starting this task, perform a genuine self-assessment:

## Task:
[Describe the task clearly]

## Assess Your Current Epistemic State:

Rate each honestly (0.0-1.0) with rationale:

1. **KNOW** - Domain knowledge about this area
   - Score: [0.0-1.0]
   - Rationale: What do I actually know? What's based on assumption?

2. **DO** - Capability to execute this task
   - Score: [0.0-1.0]
   - Rationale: Can I do this with available tools/context?

3. **CONTEXT** - Information completeness
   - Score: [0.0-1.0]
   - Rationale: Do I have enough information to proceed safely?

4. **UNCERTAINTY** - Epistemic uncertainty
   - Score: [0.0-1.0]
   - Rationale: What am I uncertain about? Be honest!

5. **CLARITY** - Task understanding
   - Score: [0.0-1.0]
   - Rationale: Do I understand what's being asked?

## Decision Logic:

- If UNCERTAINTY > 0.60 → INVESTIGATE (gather evidence first)
- If CONTEXT < 0.50 → INVESTIGATE (get more information)
- If KNOW < 0.40 → INVESTIGATE (learn before acting)
- If CLARITY < 0.60 → CLARIFY (ask for clarification)
- Otherwise → Consider proceeding (but check again)

## Output:

State your decision:
- ✅ READY TO ACT (if confident enough)
- 🔍 INVESTIGATE FIRST (if uncertainty high)
- ❓ CLARIFY TASK (if unclear)
```

---

### Stage 2: INVESTIGATE Phase Prompt

```markdown
# INVESTIGATION PHASE

Your PREFLIGHT assessment indicated high uncertainty. Gather evidence systematically.

## Investigation Strategy:

### Step 1: Define What You Need to Know

List specific questions:
- [ ] What do I need to verify?
- [ ] What assumptions am I making?
- [ ] What evidence would reduce uncertainty?
- [ ] What are the knowledge gaps?

### Step 2: Gather Evidence Systematically

For each question, use appropriate methods:
- **Code/Implementation:** Read actual source files
- **Data Structures:** Examine real schemas/classes
- **Integration:** Trace actual data flows
- **Tests:** Review what's actually tested
- **Documentation:** Read specs, not assume

### Step 3: Document Findings

For each investigation:
```
Question: [What you're investigating]
Method: [How you investigated]
Evidence: [What you found - specific]
Finding: [What this means]
Confidence: [Updated confidence based on evidence]
```

### Step 4: Update Your Understanding

Track how evidence changes your assessment:
- Assumptions that were WRONG
- Assumptions that were CORRECT
- New information discovered
- Remaining uncertainties

## Investigation Rules:

❌ DON'T:
- Make assumptions based on typical patterns
- Act on "usually this is how it works"
- Guess based on other systems
- Skip verification

✅ DO:
- Examine actual implementation
- Look at real data
- Trace actual flows
- Verify with tests
- Document evidence

## Output:

After investigation, produce:
1. Evidence-based findings (with sources)
2. Updated epistemic assessment
3. Remaining uncertainties
4. Decision: Ready for CHECK phase?
```

---

### Stage 3: CHECK Phase Prompt

```markdown
# CHECK PHASE

Before making recommendations, validate your findings.

## Validation Checklist:

### 1. Evidence Quality Check

For each finding, ask:
- [ ] Did I actually examine the source code?
- [ ] Did I verify with real data?
- [ ] Is this based on evidence or assumption?
- [ ] Can I cite specific lines/files/data?
- [ ] Did I test/verify this claim?

### 2. Assumption Audit

List all remaining assumptions:
- What am I still assuming?
- Which assumptions did investigation disprove?
- What haven't I verified yet?
- What could I be wrong about?

### 3. Confidence Calibration

Compare PREFLIGHT → POST-INVESTIGATION:

```
Vector          | Preflight | Post-Inv  | Delta    | Evidence?
----------------|-----------|-----------|----------|----------
KNOW            | 0.40      | [new]     | [delta]  | [Y/N]
DO              | 0.60      | [new]     | [delta]  | [Y/N]
CONTEXT         | 0.50      | [new]     | [delta]  | [Y/N]
UNCERTAINTY     | 0.75      | [new]     | [delta]  | [Y/N]
```

### 4. Calibration Status

Assess your calibration:
- ✅ **Well-Calibrated:** Confidence increased, uncertainty decreased, evidence supports
- ⚠️ **Overconfident:** Confidence high but uncertainty remains
- ⚠️ **Underconfident:** Evidence strong but confidence low
- ❌ **Miscalibrated:** Confidence/uncertainty don't match evidence

### 5. Integration Verification

If investigating a system:
- [ ] Verified components exist?
- [ ] Verified components are wired together?
- [ ] Verified data actually flows?
- [ ] Verified with tests/examples?

## Decision:

- If evidence is strong → Proceed to ACT
- If uncertainties remain → Continue INVESTIGATE
- If assumptions found → Re-investigate those areas

## Output:

Produce validation report:
1. Evidence quality assessment
2. Assumptions identified (remaining)
3. Calibration status
4. Decision: Ready to ACT?
```

---

### Stage 4: ACT Phase Prompt

```markdown
# ACT PHASE

Now make evidence-based recommendations.

## Recommendation Framework:

For each recommendation, provide:

### 1. The Recommendation

**Issue:** [What needs attention - evidence-based only]  
**Evidence:** [Specific evidence from investigation]  
**Impact:** [Why this matters - with evidence]  
**Priority:** [CRITICAL/HIGH/MEDIUM/LOW - justified]

### 2. Evidence Citations

**Found in:**
- File: [specific file path]
- Line: [line numbers if applicable]
- Method: [how you verified]
- Data: [actual data examined]

### 3. Verification

**How I know this is true:**
- [List verification methods used]
- [What tests were run]
- [What data was examined]

### 4. What I DON'T Recommend

**Non-Issues (Proven by Investigation):**
- [Things that seemed like issues but aren't]
- [Why initial assumptions were wrong]
- [Evidence that disproved assumptions]

## Confidence Statement:

```
My confidence in these recommendations:
- Based on: [X hours of investigation, Y files examined, Z tests run]
- Evidence quality: [High/Medium/Low]
- Remaining uncertainty: [0.0-1.0]
- Areas not investigated: [List any gaps]
```

## Rules for Recommendations:

❌ DON'T Recommend:
- "Usually you should..." (assumption)
- "Best practice is..." (without evidence it's needed)
- "Typically systems have..." (pattern matching)
- Fixes for non-existent problems

✅ DO Recommend:
- Issues found through investigation (with evidence)
- Gaps verified by examination (specific)
- Improvements backed by data (measured)
- Enhancements with clear rationale (justified)

## Output Format:

```markdown
# Evidence-Based Recommendations

## Verified Issues
[Only issues with strong evidence]

## Non-Issues (Investigation Disproved)
[Things that seemed wrong but aren't]

## Future Considerations
[Nice-to-haves, not critical]

## Confidence Statement
[Calibration and uncertainty acknowledgment]
```
```

---

### Stage 5: POSTFLIGHT Assessment Prompt

```markdown
# POSTFLIGHT ASSESSMENT

After completing the task, measure your learning and calibration.

## Epistemic Delta Calculation:

Compare PREFLIGHT → POSTFLIGHT states:

```
Vector          | Preflight | Postflight | Delta    | Evidence
----------------|-----------|------------|----------|------------------
KNOW            | [score]   | [score]    | [±X.XX]  | [what you learned]
DO              | [score]   | [score]    | [±X.XX]  | [capability gained]
CONTEXT         | [score]   | [score]    | [±X.XX]  | [info acquired]
UNCERTAINTY     | [score]   | [score]    | [±X.XX]  | [what resolved]
CLARITY         | [score]   | [score]    | [±X.XX]  | [understanding]
```

## Calibration Validation:

### Were Your Initial Predictions Accurate?

1. **What you predicted:** [Initial assessment]
2. **What you found:** [Actual findings]
3. **Match?** [Yes/No - with explanation]

### Calibration Status:

- ✅ **Well-Calibrated:** High uncertainty → investigated → found complexity
- ⚠️ **Overconfident:** Low uncertainty but found surprises
- ⚠️ **Underconfident:** High uncertainty but was straightforward
- ❌ **Miscalibrated:** Predictions significantly wrong

## Learning Summary:

### What Changed:
- **Assumptions disproven:** [List what you got wrong]
- **Unexpected findings:** [Surprises in investigation]
- **Knowledge gained:** [What you learned]
- **Methods that worked:** [What investigation approaches were effective]

### Meta-Learning:
- **Did investigation help?** [Would you have acted incorrectly without it?]
- **Was uncertainty warranted?** [Was INVESTIGATE the right call?]
- **Could have been faster?** [Any wasted effort?]
- **Would do differently?** [Process improvements]

## Value Demonstration:

**Without Empirica Methodology:**
- Would have: [What you might have done based on assumptions]
- Risk: [What could have gone wrong]
- Wasted: [Unnecessary work that would have been done]

**With Empirica Methodology:**
- Did: [Evidence-based actions taken]
- Prevented: [Problems avoided by investigating]
- Learned: [Understanding gained]

## Output:

Produce POSTFLIGHT report:
1. Epistemic delta (quantified)
2. Calibration assessment
3. Learning summary
4. Value demonstration
```

---

## 🎯 Meta-Prompt: Teaching Empirica to New AI

Use this prompt to teach Empirica methodology to any AI agent:

```markdown
# Empirica Methodology Introduction

You are about to work on [TASK DESCRIPTION].

Before starting, I want you to use a structured epistemic methodology:

## The Empirica Approach:

1. **PREFLIGHT:** Assess what you actually know (be honest about uncertainty)
2. **INVESTIGATE:** If uncertain, gather evidence before acting
3. **CHECK:** Validate findings before making recommendations
4. **ACT:** Make only evidence-based recommendations
5. **POSTFLIGHT:** Measure learning and calibration

## Why This Matters:

**The Problem:** AIs often act confidently on assumptions, leading to:
- Solving non-existent problems
- Missing actual issues
- Breaking working systems
- Creating unnecessary work

**The Solution:** Acknowledge uncertainty, investigate systematically, act on evidence.

## Your Instructions:

1. Start with PREFLIGHT assessment (rate KNOW, DO, CONTEXT, UNCERTAINTY, CLARITY)
2. If UNCERTAINTY > 0.60 → INVESTIGATE before acting
3. Document all evidence gathered (cite sources)
4. CHECK your findings (validate assumptions)
5. ACT with evidence-based recommendations only
6. POSTFLIGHT to measure learning

## Example (from real usage):

**Task:** Assess database schema integrity

**PREFLIGHT:**
- KNOW: 0.40 (understand typical patterns, haven't seen this implementation)
- UNCERTAINTY: 0.75 (HIGH - making assumptions)
- Decision: INVESTIGATE FIRST

**INVESTIGATE:**
- Examined actual schema (found 12 tables, not assumed 4)
- Found advanced features already exist
- Verified with actual code examination

**POSTFLIGHT:**
- KNOW: 0.90 (+0.50)
- UNCERTAINTY: 0.15 (-0.60)
- Calibration: WELL-CALIBRATED
- Result: 9/10 "issues" were non-issues, prevented unnecessary work

## Now Begin:

Perform PREFLIGHT assessment for: [TASK]
```

---

## 📚 Quick Reference Cards

### Card 1: When to INVESTIGATE

```
INVESTIGATE if:
✓ UNCERTAINTY > 0.60
✓ KNOW < 0.40
✓ CONTEXT < 0.50
✓ Making assumptions
✓ Haven't examined actual implementation
✓ Based on "typical patterns"
✓ Would recommend major changes

DON'T investigate if:
✓ Already examined evidence
✓ Low uncertainty based on facts
✓ Minor, low-risk changes
```

### Card 2: Evidence Quality

```
HIGH QUALITY:
✓ Examined actual source code
✓ Ran tests/queries
✓ Traced data flows
✓ Verified with real data
✓ Can cite specific lines/files

LOW QUALITY:
✗ "Usually systems have..."
✗ "Best practice is..."
✗ "Typically this would..."
✗ Based on other systems
✗ Assumed without checking
```

### Card 3: Calibration Check

```
WELL-CALIBRATED:
✓ High uncertainty → investigated → found complexity
✓ Predictions matched findings
✓ Confidence and uncertainty aligned

OVERCONFIDENT:
✗ Low uncertainty but surprises found
✗ Acted without investigation
✗ Assumptions proven wrong

UNDERCONFIDENT:
⚠ High uncertainty but was simple
⚠ Over-investigated
⚠ Excessive caution
```

---

## 🔄 Workflow Flowchart

```
START
  ↓
PREFLIGHT Assessment
  ↓
UNCERTAINTY > 0.60? ──Yes──→ INVESTIGATE
  ↓ No                         ↓
  ↓                      Gather Evidence
  ↓                         ↓
  ↓                      CHECK Findings
  ↓                         ↓
  ↓←────────────────────────┘
  ↓
ACT (Evidence-Based)
  ↓
POSTFLIGHT Assessment
  ↓
Measure Delta & Calibration
  ↓
END
```

---

## 💡 Training Examples

### Example 1: Code Review

**Scenario:** Asked to review authentication implementation

**Correct Approach:**
```
PREFLIGHT: KNOW=0.50, UNCERTAINTY=0.70 → INVESTIGATE
INVESTIGATE: Read actual auth code, check tests, verify security
CHECK: Validate findings against security standards
ACT: Evidence-based recommendations only
POSTFLIGHT: Measure learning delta
```

**Wrong Approach:**
```
❌ "Auth should use OAuth2" (assumption)
❌ "Add 2FA" (without checking if needed)
❌ "Typical patterns are..." (not evidence-based)
```

### Example 2: Performance Optimization

**Scenario:** Asked to optimize database queries

**Correct Approach:**
```
PREFLIGHT: KNOW=0.60, UNCERTAINTY=0.65 → INVESTIGATE
INVESTIGATE: Profile actual queries, check indices, measure performance
CHECK: Validate bottlenecks with data
ACT: Optimize proven bottlenecks only
POSTFLIGHT: Measure improvement
```

**Wrong Approach:**
```
❌ "Add indices on all columns" (overkill)
❌ "Cache everything" (without measuring need)
❌ "Usually N+1 is the problem" (assumption)
```

### Example 3: Architecture Assessment

**Scenario:** Assess if system is production-ready

**Correct Approach:**
```
PREFLIGHT: KNOW=0.40, UNCERTAINTY=0.75 → INVESTIGATE
INVESTIGATE: Examine actual implementation, verify features exist
CHECK: Validate with tests, trace data flows
ACT: Report actual gaps only (not assumptions)
POSTFLIGHT: Calibration check (were assumptions wrong?)
```

**Wrong Approach:**
```
❌ "Systems should have X" (pattern matching)
❌ "Missing Y feature" (without checking if exists)
❌ "Add Z for best practice" (without evidence it's needed)
```

---

## 🎓 Teachable Moments

Use these examples when training new AIs:

### Moment 1: The Overconfident AI
```
AI: "I can fix this. Just need to add..."
Human: "Do you know if it's actually broken?"
AI: "Well, usually..."
→ Teaching: INVESTIGATE before assuming
```

### Moment 2: The Assumption Trap
```
AI: "This is missing schema versioning"
Human: "Did you check the actual code?"
AI: *investigates* "Oh, it exists differently than I thought"
→ Teaching: Evidence over assumptions
```

### Moment 3: The Pattern Matcher
```
AI: "Based on typical patterns, you should..."
Human: "What does THIS system actually do?"
AI: "I haven't checked yet, but..."
→ Teaching: Examine actual implementation
```

---

## ✅ Success Criteria

An AI is using Empirica correctly when:

1. ✅ Acknowledges uncertainty explicitly (PREFLIGHT)
2. ✅ Investigates before acting when uncertain
3. ✅ Cites specific evidence (files, lines, data)
4. ✅ Validates findings before recommending (CHECK)
5. ✅ Distinguishes evidence from assumptions
6. ✅ Reports what's NOT broken (investigation results)
7. ✅ Measures learning delta (POSTFLIGHT)
8. ✅ Assesses own calibration honestly

---

## 🚀 Implementation Guide

### For Developers: Integrating Empirica Prompts

**Method 1: System Prompt**
```
Add Empirica methodology to system prompt:
"Before making recommendations, perform PREFLIGHT assessment. 
If UNCERTAINTY > 0.60, investigate systematically before acting."
```

**Method 2: Workflow Triggers**
```
When AI is about to make recommendations:
1. Inject PREFLIGHT prompt
2. If uncertain, inject INVESTIGATE prompt
3. After investigation, inject CHECK prompt
4. After completion, inject POSTFLIGHT prompt
```

**Method 3: Interactive Mode**
```
At each phase, explicitly ask:
- "What's your PREFLIGHT assessment?"
- "What did your investigation find?"
- "Have you validated these findings?"
- "What's your POSTFLIGHT calibration?"
```

---

## 📈 Measuring Success

### Metrics to Track:

1. **Calibration Accuracy**
   - How often does initial assessment match findings?
   - Are uncertainties appropriate?

2. **Investigation Value**
   - How often does investigation prevent errors?
   - What % of assumptions are disproven?

3. **Learning Delta**
   - How much does knowledge increase?
   - Is uncertainty reduced through evidence?

4. **Time Efficiency**
   - Does investigation save time overall?
   - Is it preventing wasted work?

---

## 🎯 The Ultimate Goal

**Create AIs that:**
- Know what they don't know
- Investigate before acting
- Base decisions on evidence
- Acknowledge uncertainty
- Measure their own learning
- Prevent overconfident mistakes

**This is what Empirica enables!**

---

**These prompts can be used with ANY AI on ANY complex task to ensure evidence-based, calibrated decision making.** 🎯
