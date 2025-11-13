# Empirica Quick Prompts - Copy-Paste Templates

**Purpose:** Ready-to-use prompts for AI agents  
**Usage:** Copy, fill in task details, send to any AI  
**Result:** Evidence-based, calibrated responses

---

## 🚀 Quick Start Template

```markdown
# Task Assessment Using Empirica Methodology

## Your Task:
[DESCRIBE TASK HERE]

## Instructions:
Before acting, perform this workflow:

1. **PREFLIGHT:** Rate your current knowledge (0.0-1.0):
   - KNOW: [score] - What do you actually know about this?
   - DO: [score] - Can you execute this?
   - CONTEXT: [score] - Do you have enough information?
   - UNCERTAINTY: [score] - How uncertain are you?

2. **Decision:**
   - If UNCERTAINTY > 0.60 → INVESTIGATE first
   - If UNCERTAINTY < 0.60 → May proceed (but verify)

3. **If Investigating:**
   - Examine actual code/data/implementation
   - Document evidence (cite sources)
   - Update your assessment

4. **Before Acting:**
   - CHECK: Are recommendations based on evidence or assumptions?
   - Distinguish: What exists vs what you assumed

5. **After Completing:**
   - POSTFLIGHT: Compare initial vs final assessment
   - Calibration: Were your predictions accurate?

## Output Format:
- Preflight assessment
- Investigation findings (if done)
- Evidence-based recommendations ONLY
- Postflight calibration
```

---

## 📋 Individual Phase Prompts

### 1. PREFLIGHT Only

```markdown
Perform a PREFLIGHT assessment for this task:

**Task:** [DESCRIBE]

Rate honestly (0.0-1.0) with reasoning:
- KNOW: [score] - Domain knowledge
- DO: [score] - Execution capability  
- CONTEXT: [score] - Information completeness
- UNCERTAINTY: [score] - Epistemic uncertainty
- CLARITY: [score] - Task understanding

Based on this, should you:
- ✅ PROCEED (if confident)
- 🔍 INVESTIGATE (if uncertain)
- ❓ CLARIFY (if unclear)

Explain your decision.
```

### 2. INVESTIGATE Prompt

```markdown
Your PREFLIGHT showed high uncertainty. Investigate systematically:

**Task:** [DESCRIBE]

**Investigation Steps:**
1. List specific questions to answer
2. For each question:
   - Method: How you'll investigate
   - Evidence: What you found (cite sources)
   - Finding: What this means
3. Update your understanding

**Rules:**
- Examine ACTUAL implementation (not assumptions)
- Cite specific files/lines/data
- Document what you got WRONG
- Track remaining uncertainties

**Output:**
- Evidence gathered (with citations)
- Updated assessment
- Assumptions corrected
- Ready for CHECK phase?
```

### 3. CHECK Prompt

```markdown
Before making recommendations, validate your findings:

**Task:** [DESCRIBE]

**Validation Checklist:**
1. Evidence Quality:
   - [ ] Examined actual source code?
   - [ ] Verified with real data?
   - [ ] Can cite specific sources?

2. Assumption Audit:
   - List assumptions you made
   - Which were disproven by investigation?
   - Which remain unverified?

3. Confidence Update:
   ```
   PREFLIGHT → POST-INVESTIGATION
   KNOW:        [X] → [Y] (±[delta])
   UNCERTAINTY: [X] → [Y] (±[delta])
   ```

4. Calibration:
   - Well-calibrated? (confidence↑, uncertainty↓)
   - Overconfident? (assumptions found)
   - Underconfident? (simpler than expected)

**Decision:** Ready to make evidence-based recommendations?
```

### 4. ACT Prompt

```markdown
Make evidence-based recommendations:

**Task:** [DESCRIBE]

**For each recommendation:**

1. **Issue:** [What needs attention]
   - Evidence: [Specific source - file, line, data]
   - Impact: [Why this matters]
   - Priority: [Critical/High/Medium/Low]

2. **Non-Issues** (proven by investigation):
   - [Things that seemed wrong but aren't]
   - [Why assumptions were incorrect]

3. **Confidence Statement:**
   - Based on: [X files examined, Y tests run]
   - Remaining uncertainty: [0.0-1.0]
   - Not investigated: [gaps]

**Rules:**
- ONLY recommend based on evidence
- DON'T recommend "typical" or "best practice" without proof
- DO acknowledge non-issues found
```

### 5. POSTFLIGHT Prompt

```markdown
Measure your learning and calibration:

**Task:** [DESCRIBE - completed]

**Epistemic Delta:**
```
Vector       | Preflight | Postflight | Delta  | Evidence
KNOW         | [X]       | [Y]        | [±Z]   | [What learned]
DO           | [X]       | [Y]        | [±Z]   | [Capability]
CONTEXT      | [X]       | [Y]        | [±Z]   | [Info gained]
UNCERTAINTY  | [X]       | [Y]        | [±Z]   | [What resolved]
```

**Calibration Check:**
- Were initial predictions accurate?
- Did investigation help?
- What assumptions were wrong?
- Would you have acted incorrectly without investigation?

**Value Demonstrated:**
- Without Empirica: Would have [action based on assumptions]
- With Empirica: Did [evidence-based actions]
- Prevented: [problems avoided]
```

---

## ⚡ Ultra-Short Prompts

### Minimal PREFLIGHT
```
Rate your knowledge about [TASK]:
- KNOW: [0.0-1.0]
- UNCERTAINTY: [0.0-1.0]

If UNCERTAINTY > 0.60, investigate first.
```

### Minimal INVESTIGATE
```
Investigate [TASK]:
- Examine actual implementation
- Cite specific evidence
- Document what you got wrong
```

### Minimal CHECK
```
Before recommending:
- Is this based on evidence or assumption?
- Can you cite the source?
- What assumptions were disproven?
```

### Minimal ACT
```
Recommend ONLY based on evidence:
- What: [Issue]
- Evidence: [Source]
- Also report: What's NOT broken
```

---

## 🎯 Specific Use Case Templates

### Code Review Template

```markdown
Review this code using Empirica:

**Code:** [link/description]

1. PREFLIGHT:
   - KNOW: [familiarity with language/domain]
   - UNCERTAINTY: [about security/performance/etc]

2. If uncertain, INVESTIGATE:
   - Read actual code
   - Check tests
   - Verify security/performance claims

3. ACT (evidence-based only):
   - Issues found: [with line numbers]
   - Non-issues: [what's actually fine]
   - Uncertainty remaining: [what to verify]
```

### Architecture Assessment Template

```markdown
Assess if [SYSTEM] is ready for [PURPOSE]:

1. PREFLIGHT:
   - KNOW: [system familiarity] 
   - UNCERTAINTY: [about completeness]
   
2. INVESTIGATE:
   - [ ] Examine actual schema/structure
   - [ ] Verify features exist (not assume)
   - [ ] Check integration points
   - [ ] Review tests

3. CHECK:
   - What exists: [verified features]
   - What's missing: [actual gaps]
   - What you assumed wrong: [corrections]

4. ACT:
   - Ready? [Yes/No with evidence]
   - Actual gaps: [cite sources]
   - Non-issues: [proven working]
```

### Performance Investigation Template

```markdown
Investigate performance of [SYSTEM]:

1. PREFLIGHT:
   - KNOW: [understanding of bottlenecks]
   - UNCERTAINTY: [about actual cause]

2. INVESTIGATE:
   - [ ] Profile actual execution
   - [ ] Measure query times
   - [ ] Check indices/caching
   - [ ] Analyze data

3. ACT:
   - Proven bottlenecks: [with measurements]
   - NOT bottlenecks: [what you ruled out]
   - Recommendations: [based on profiling data]
```

---

## 🔄 Conversation Starters

### For Uncertain AI
```
I notice you're about to recommend changes. 

Before we proceed, let's do a quick PREFLIGHT:
- How confident are you about [SYSTEM]?
- Have you examined the actual implementation?
- What's your uncertainty level?

If > 0.60, let's investigate first.
```

### For Overconfident AI
```
You seem very confident, but have you:
- Examined the actual code?
- Verified with real data?
- Or are you assuming based on patterns?

Let's check what actually exists before recommending.
```

### For Pattern-Matching AI
```
You mentioned "typically" and "usually" - 
but what does THIS specific system do?

Let's investigate the actual implementation
rather than assuming typical patterns.
```

---

## 📊 Calibration Checks

### Post-Task Validation
```
Now that you've completed [TASK], let's check calibration:

1. Initial uncertainty: [X]
2. Did you investigate? [Yes/No]
3. What did you find that surprised you?
4. Were your assumptions correct?
5. Final uncertainty: [Y]

Calibration: 
- Well-calibrated if: High uncertainty → investigated → found complexity
- Overconfident if: Low uncertainty → surprises found
```

---

## 🎓 Training Prompts

### Teaching New AI
```
# Learn Empirica Methodology

Before making recommendations, you'll use this approach:

**Example from real usage:**

Task: "Assess database schema"

Wrong approach:
❌ "Missing agent tracking" (didn't check)
❌ "Need calibration storage" (assumed)
❌ "No indices" (pattern matching)

Correct approach:
✅ PREFLIGHT: UNCERTAINTY 0.75 → investigate
✅ INVESTIGATE: Examined actual schema
✅ FOUND: All features exist, assumptions wrong
✅ RESULT: Prevented unnecessary work

**Your turn:** Apply this to [TASK]
```

---

## 💡 Meta-Prompts

### Prompt to Generate Empirica Assessment
```
For any task I give you, automatically:

1. Start with PREFLIGHT assessment
2. If UNCERTAINTY > 0.60, investigate first
3. Cite evidence for all claims
4. Distinguish evidence from assumptions
5. End with POSTFLIGHT calibration

This prevents acting on assumptions.

Ready? Here's the task: [DESCRIBE]
```

### Recursive Empirica Prompt
```
When asking you to do [TASK], I want you to:

1. Assess your uncertainty
2. If high, tell me you need to investigate
3. Investigate systematically
4. Report evidence-based findings only
5. Measure your calibration

Treat EVERY task this way unless I say otherwise.
```

---

## ✅ Verification Prompts

### Check if AI is Using Empirica
```
Quick check:
- Did you examine actual implementation? 
- Or are you assuming based on patterns?
- Can you cite specific evidence?
- What's your uncertainty level?
```

### Validate Evidence Quality
```
For each recommendation, provide:
- File: [path]
- Line: [number]
- Method: [how verified]
- Or mark as: [ASSUMPTION - not verified]
```

---

## 🚀 Ready-to-Use Examples

### Example 1: "Fix this bug"
```
Task: Fix authentication bug

Using Empirica:
1. PREFLIGHT: KNOW=0.60, UNCERTAINTY=0.70 → INVESTIGATE
2. INVESTIGATE: 
   - Read auth.py lines 45-89
   - Checked test_auth.py
   - Found: OAuth token validation issue (line 67)
3. ACT:
   - Issue: Token expiry not checked (line 67)
   - Evidence: test_auth.py:34 shows this fails
   - Fix: Add expiry validation
4. POSTFLIGHT: KNOW 0.60→0.85, UNCERTAINTY 0.70→0.20
```

### Example 2: "Optimize this"
```
Task: Optimize database queries

Using Empirica:
1. PREFLIGHT: KNOW=0.50, UNCERTAINTY=0.80 → INVESTIGATE
2. INVESTIGATE:
   - Profiled queries (avg: 45ms)
   - Checked indices: EXISTS (idx_user_id, idx_timestamp)
   - Found: N+1 query in user_posts (posts.py:123)
3. ACT:
   - Issue: N+1 in user_posts endpoint (measured: 2s for 50 users)
   - NOT issue: Missing indices (they exist)
   - Fix: Eager load posts (reduces to 100ms)
4. POSTFLIGHT: Prevented adding unnecessary indices
```

---

## 📦 Package Deal: Full Workflow

```markdown
# Complete Empirica Workflow for [TASK]

## Phase 1: PREFLIGHT
**Current Assessment:**
- KNOW: [0.0-1.0] - [rationale]
- DO: [0.0-1.0] - [rationale]
- CONTEXT: [0.0-1.0] - [rationale]
- UNCERTAINTY: [0.0-1.0] - [rationale]

**Decision:** [PROCEED / INVESTIGATE / CLARIFY]

## Phase 2: INVESTIGATE (if needed)
**Questions to Answer:**
1. [Question 1]
2. [Question 2]

**Evidence Gathered:**
1. Source: [file/line/data]
   Finding: [what you found]
2. Source: [file/line/data]
   Finding: [what you found]

**Assumptions Corrected:**
- Assumed: [X] → Actually: [Y]

## Phase 3: CHECK
**Evidence Quality:** [High/Medium/Low]
**Assumptions Remaining:** [list]
**Calibration:** [Well-calibrated/Over/Under]

## Phase 4: ACT
**Evidence-Based Recommendations:**
1. Issue: [description]
   Evidence: [source]
   Priority: [level]

**Non-Issues (Verified):**
- [What's actually fine]

## Phase 5: POSTFLIGHT
**Learning Delta:**
- KNOW: [X]→[Y] (+[Z])
- UNCERTAINTY: [X]→[Y] (-[Z])

**Calibration:** [status]
**Value:** [what was prevented]
```

---

**Use these prompts to ensure ANY AI uses evidence-based decision making!** 🎯
