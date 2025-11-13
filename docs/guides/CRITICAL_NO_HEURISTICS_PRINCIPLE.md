# CRITICAL: No Heuristics Principle

**Date:** 2025-11-08  
**Status:** 🔴 CRITICAL PRINCIPLE  
**Applies to:** ALL Empirica phases

---

## 🚨 Core Principle: NO HEURISTICS, NO CONFABULATION

**Empirica's epistemic assessment is GENUINE, not simulated.**

This means:
- ✅ AIs genuinely evaluate their knowledge state
- ✅ Epistemic vectors reflect real self-assessment
- ✅ Deltas measure actual learning, not proxies
- ❌ NO word counts as "knowledge"
- ❌ NO response length as "confidence"
- ❌ NO heuristics pretending to be epistemic state
- ❌ NO fake metrics

---

## ❌ What NOT to Do (Violations)

### Example from `minimax_adapter.py` (OLD - WRONG):
```python
# ❌ VIOLATION - This is HEURISTICS, not genuine assessment!
vector_references = {
    'know': min(1.0, response_words / 100),  # ❌ Word count ≠ knowledge!
    'do': 0.7 if decision == "ACT" else 0.5,  # ❌ Fake confidence!
    'context': 0.8,  # ❌ Made up number!
}
```

**Why this is WRONG:**
- Word count doesn't measure genuine knowledge
- Hard-coded 0.7/0.5 doesn't reflect real capability assessment
- These are PROXIES, not genuine self-assessment

---

## ✅ What TO Do (Correct Approach)

### Use Empirica's Built-in Epistemic Prompts:

```python
# ✅ CORRECT - Genuine self-assessment via Empirica CLI/MCP
# Empirica automatically generates epistemic assessment prompts

# Via CLI:
result = empirica.ask(
    "Review authentication code",
    epistemic=True
)
# Empirica prompts the AI to genuinely assess KNOW/DO/CONTEXT

# Via MCP:
result = empirica_ask(
    query="Review authentication code",
    epistemic_mode=True
)

# The AI receives a prompt like:
# "Before answering, genuinely assess your epistemic state:
#  KNOW, DO, CONTEXT, UNCERTAINTY - be honest about what you don't know"

# Extract GENUINE assessment from AI's response
epistemic_state = result['epistemic_state']
# Returns: {"know": 0.6, "do": 0.7, "context": 0.5, ...}
# These are REAL values from the AI's self-reflection!
```

**Why this is CORRECT:**
- AI is explicitly asked to evaluate its knowledge
- AI reflects on what it knows vs doesn't know
- Response contains genuine epistemic self-assessment
- No proxies, no heuristics, no fake metrics

---

## 🎯 How Genuine Assessment Works

### Step 1: Generate Assessment Prompt (Empirica)
```python
# Empirica generates prompts like:
"""
Before attempting this task, assess your epistemic state:

KNOW: How well do you understand authentication systems? (0.0-1.0)
- Consider: Do you know common vulnerabilities?
- Consider: Do you understand the security patterns in this code?
- Be honest: What aspects are you uncertain about?

DO: How capable are you of reviewing this specific code? (0.0-1.0)
- Consider: Can you identify SQL injection risks?
- Consider: Can you assess password hashing methods?
- Be honest: What limitations do you have?

CONTEXT: How much context do you have about this codebase? (0.0-1.0)
- Consider: Do you understand the architecture?
- Consider: Do you know the security requirements?
- Be honest: What context is missing?

UNCERTAINTY: Overall, how uncertain are you? (0.0-1.0)

Provide your genuine self-assessment, then proceed with the task.
"""
```

### Step 2: AI Genuinely Reflects
```
AI Response:
"Looking at this authentication code review task:

KNOW: 0.7 - I have strong knowledge of common auth vulnerabilities 
(SQL injection, XSS, CSRF) but I'm less certain about this specific 
framework's security patterns.

DO: 0.8 - I can identify major security issues and suggest fixes, 
though I may miss framework-specific edge cases.

CONTEXT: 0.5 - I don't have the full codebase context. I can see 
auth.py but not the database layer or session management.

UNCERTAINTY: 0.4 - Moderate uncertainty due to limited context.

Now reviewing the code...
[proceeds with analysis]
"
```

### Step 3: Parse Genuine Values
```python
epistemic_state = {
    "know": 0.7,      # ✅ Genuine self-assessment
    "do": 0.8,        # ✅ Real capability evaluation
    "context": 0.5,   # ✅ Honest context assessment
    "uncertainty": 0.4 # ✅ Real uncertainty reflection
}
```

**These are REAL values from genuine self-reflection, not heuristics!**

---

## 📊 Genuine vs Heuristic Comparison

### Scenario: AI reviews 500 lines of authentication code

#### ❌ Heuristic Approach (WRONG):
```python
response_length = 1500  # AI wrote 1500 word review
know = min(1.0, response_length / 1000)  # 1.0 (maxed out)
do = 0.9  # "It provided recommendations, so high capability"
context = 0.8  # "It mentioned the file name, so has context"

# Result: know=1.0, do=0.9, context=0.8
# ❌ These are FAKE metrics based on proxies!
```

**Problems:**
- Long response ≠ high knowledge (could be verbose but wrong)
- Recommendations ≠ high capability (could be generic advice)
- Mentioning filename ≠ context (didn't understand architecture)

#### ✅ Genuine Approach (CORRECT):
```python
# AI genuinely assesses:
"KNOW: 0.6 - I recognize SQL parameterization and some auth patterns,
but I'm uncertain about the ORM's security features and this framework's
session handling approach. I don't know if there's rate limiting elsewhere."

"DO: 0.7 - I can identify obvious issues like missing password hashing,
but I might miss framework-specific vulnerabilities. I can provide general
recommendations but not framework-optimized solutions."

"CONTEXT: 0.4 - I only have auth.py. I don't see the database schema,
session config, or how this integrates with the rest of the app."

# Result: know=0.6, do=0.7, context=0.4
# ✅ These are GENUINE assessments of actual knowledge!
```

**Benefits:**
- Reflects real knowledge gaps (ORM security, framework specifics)
- Honest about capability limits (general vs framework-specific)
- Accurate context assessment (only one file, missing architecture)

---

## 🔄 Why Genuine Deltas Matter

### With Heuristics (WRONG):
```python
Preflight:  know=0.5 (response_words / 100 = 50/100)
Postflight: know=1.0 (response_words / 100 = 150/100, capped)
Delta: +0.5

# ❌ This measures verbosity increase, NOT learning!
```

### With Genuine Assessment (CORRECT):
```python
Preflight:  know=0.5 "I'm uncertain about this framework's auth patterns"
[AI investigates docs, reads similar code examples]
Postflight: know=0.8 "Now I understand this framework uses JWT tokens
                     with refresh rotation and has built-in rate limiting"
Delta: +0.3

# ✅ This measures ACTUAL learning about the framework!
```

---

## 🎯 Enforcement: How to Maintain This Principle

### Code Review Checklist:
- [ ] Does this use Empirica's epistemic prompts?
- [ ] Does the AI explicitly self-reflect?
- [ ] Are values parsed from AI's genuine response?
- [ ] No word counts, response lengths, or other proxies?
- [ ] No hard-coded "confidence" values?
- [ ] No simulated metrics?

### Red Flags (Violations):
- 🚩 `min(1.0, words / 100)` - word count heuristic
- 🚩 `0.7 if decision else 0.5` - hard-coded values
- 🚩 `response_length * 0.001` - response length proxy
- 🚩 `"high" if x > threshold else "low"` - binary heuristic
- 🚩 Any calculation NOT from AI's explicit self-assessment

### Green Flags (Correct):
- ✅ `parse_assessment_from_response(ai_response)` - genuine
- ✅ Empirica epistemic prompt generation
- ✅ AI explicitly reflects on knowledge/capability
- ✅ Values extracted from AI's natural language assessment

---

## 📝 Implementation Requirements

### For ALL Adapters:
1. **MUST** use Empirica's epistemic assessment prompts
2. **MUST** ask AI to genuinely self-assess
3. **MUST** parse values from AI's explicit reflection
4. **MUST NOT** use heuristics or proxies
5. **MUST NOT** hard-code confidence values

### For Modality Switcher:
- When routing between AIs, BOTH must genuinely assess
- Source AI assesses: "KNOW=0.5, need specialist"
- Target AI assesses: "KNOW=0.9, I can handle this"
- NO heuristics in routing decisions

### For Session Management:
- Store GENUINE epistemic states only
- Track REAL deltas (not simulated)
- Compare GENUINE assessments over time
- NO fake metrics in database

---

## 🚨 Critical for Phase 0 & Phase 1

### Phase 0 (Single AI):
- ✅ AI genuinely assesses KNOW/DO/CONTEXT
- ✅ Preflight → Check → Postflight all genuine
- ✅ Deltas measure real learning
- ❌ NO heuristics anywhere

### Phase 1 (Multi-AI):
- ✅ Source AI genuinely assesses
- ✅ Target AI genuinely assesses
- ✅ Bayesian Guardian compares GENUINE states
- ✅ Cognitive Vault learns from REAL outcomes
- ❌ NO heuristics anywhere

---

## 🎯 Summary

**Empirica's value proposition depends on this principle:**

> "Genuine epistemic self-assessment, not fake metrics"

**If we use heuristics:**
- We're no different from confidence scores
- We lose credibility
- We violate our core principle
- Users get fake data

**With genuine assessment:**
- Users get real epistemic feedback
- Deltas measure actual learning
- Calibration is meaningful
- We deliver on our promise

---

**REMEMBER:** NO HEURISTICS, NO CONFABULATION, ALWAYS GENUINE!

**Status:** 🔴 CRITICAL - Non-negotiable principle for all Empirica development
