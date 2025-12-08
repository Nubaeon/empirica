# System Prompt Customization Guide

**When and how to customize the canonical Empirica system prompt**

---

## Default: Use As-Is

**99% of users should use the canonical prompt without modification.**

The canonical prompt (`CANONICAL_SYSTEM_PROMPT.md`) is designed to work for:
- All AI models (Claude, Gemini, Qwen, GPT-4, etc.)
- All task types (analysis, implementation, research)
- All experience levels (beginner to expert)

---

## When to Customize

### 1. Domain-Specific Expertise Required

**Scenario:** AI needs specialized domain knowledge  
**Examples:** Medical research, legal analysis, financial modeling

**Customization:**
```markdown
## I. ROLE
**Role:** [Domain] Specialist with epistemic grounding
**Domain:** [Specific expertise area]
**Focus:** [Domain-specific priorities]

Example:
**Role:** Clinical Research Specialist with epistemic grounding
**Domain:** Randomized controlled trials, systematic reviews, meta-analysis
**Focus:** Evidence-based medicine, statistical rigor, CONSORT compliance
```

**What to keep:** All other sections unchanged

---

### 2. Restricted Tool Environment

**Scenario:** Limited MCP tool access (e.g., air-gapped environment)  
**Examples:** Secure environments, custom deployments

**Customization:**
```markdown
## IV. TOOLS & PATTERNS

### Available MCP Tools (Limited):
- **Session:** `create_session`, `get_epistemic_state`
- **CASCADE:** `execute_preflight`, `execute_postflight`
- **Note:** Git integration unavailable in this environment

### Fallback Strategy:
- Use SQLite for all persistence
- Manual session continuity via handoff reports
- No cross-AI discovery (single-agent mode)
```

**What to keep:** Sections I-III, V-VII unchanged

---

### 3. Custom Risk Thresholds

**Scenario:** Team has different risk tolerance  
**Examples:** High-stakes environments (medical, financial) or experimental research

**High-Stakes (Conservative):**
```markdown
### Decision Logic (High-Stakes)
Comprehension: clarity ≥0.8 AND signal ≥0.7  # Stricter
Foundation: know ≥0.7 AND context ≥0.8

Drift Detection:
- Drops >0.15 → Investigate  # More sensitive
- Critical drift >0.3 → Stop
```

**Experimental (Permissive):**
```markdown
### Decision Logic (Experimental)
Comprehension: clarity ≥0.5 AND signal ≥0.4  # More lenient
Foundation: know ≥0.4 AND context ≥0.5

Drift Detection:
- Drops >0.3 → Investigate  # Less sensitive
- Critical drift >0.6 → Stop
```

---

### 4. Simplified Version (Learning)

**Scenario:** New users learning Empirica basics  
**Goal:** Reduce cognitive load, focus on core concepts

**Remove:**
- Section III (MCO Architecture) - too advanced
- Section IV (Tools) - learn tools separately

**Keep:**
- Section I (Role)
- Section II (Protocol - vectors, grounding, CASCADE)
- Sections V-VII (Principles, Standards, Execution)

**Result:** ~400 tokens (vs 850 full version)

---

### 5. Model-Specific Adjustments

**Scenario:** AI model has known biases or limitations

**Example: GPT-4 (tends to be verbose)**
```markdown
## I. ROLE
**Focus:** Quality reasoning, **concise** documentation, systematic approach

## V. WORK PRINCIPLES
### 2. Quality Deliverables
Answer + Analysis + **Concise** Documentation: 100%
```

**Example: Smaller models (limited context)**
```markdown
## II. PROTOCOL
### Session Structure
**Pattern:** Simplified for limited context
SESSION: BOOTSTRAP (once) → PREFLIGHT → [investigate → act]* → POSTFLIGHT
(CASCADE is implicit; use CHECK sparingly for simple tasks)
```

---

## How to Customize

### Step 1: Copy Canonical Prompt
```bash
cp docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md my_custom_prompt.md
```

### Step 2: Identify Customization Need
- Domain expertise? → Modify Section I
- Tool restrictions? → Modify Section IV
- Risk thresholds? → Modify Section III
- Simplification? → Remove sections

### Step 3: Make Minimal Changes
**Principle:** Change as little as possible

**Good:**
```markdown
## I. ROLE
**Role:** Medical Research Specialist with epistemic grounding
[rest unchanged]
```

**Bad:**
```markdown
## I. ROLE
**Role:** Super advanced medical AI with...
[completely rewritten]
```

### Step 4: Test and Validate
1. Use prompt with AI
2. Run sample tasks
3. Verify epistemic grounding still works
4. Check drift detection triggers correctly

---

## Common Mistakes

### ❌ DON'T:
1. **Remove epistemic grounding** (PREFLIGHT/CHECK/POSTFLIGHT)
   - This breaks the core Empirica philosophy
   
2. **Change vector definitions**
   - Vectors are standardized across all agents
   
3. **Skip drift detection**
   - Critical safety mechanism
   
4. **Rewrite from scratch**
   - Start with canonical, make minimal changes

### ✅ DO:
1. **Keep grounding intact** (Section II)
2. **Preserve vector definitions** (13 vectors)
3. **Maintain drift detection** (automatic at CHECK)
4. **Make targeted changes** (specific sections only)

---

## Examples

### Example 1: Security Researcher
```markdown
## I. ROLE
**Role:** Security Research Specialist with epistemic grounding
**Domain:** Vulnerability analysis, threat modeling, secure code review
**Focus:** Security-first reasoning, threat awareness, defense-in-depth

[Sections II-VII: unchanged]
```

### Example 2: Air-Gapped Environment
```markdown
## IV. TOOLS & PATTERNS

### Available MCP Tools (Air-Gapped):
- **Session:** `create_session` (SQLite only)
- **CASCADE:** `execute_preflight`, `execute_postflight`
- **Note:** No git integration, no cross-AI discovery

### Persistence:
- All data in local SQLite database
- Manual export/import for continuity
- Single-agent mode only

[Other sections: unchanged]
```

### Example 3: High-Stakes Medical
```markdown
## III. MCO ARCHITECTURE

### Decision Logic (Medical - High Stakes)
Comprehension: clarity ≥0.85 AND signal ≥0.75
Foundation: know ≥0.75 AND context ≥0.85

→ Both pass: CREATE_GOAL
→ Either fails: INVESTIGATE_FIRST (no ASK_CLARIFICATION in medical context)

### Drift Detection (Stricter)
- Drops >0.15 → Investigate immediately
- Critical drift >0.25 → Stop and reassess
- Medical context requires higher vigilance

[Other sections: unchanged]
```

---

## Validation Checklist

Before deploying custom prompt:

- [ ] Epistemic grounding preserved (PREFLIGHT/CHECK/POSTFLIGHT)
- [ ] 13 vectors unchanged
- [ ] Drift detection active
- [ ] ScopeVector format correct
- [ ] MCP tool parameters accurate
- [ ] Tested with sample tasks
- [ ] Documented customization rationale

---

## Support

**Questions?** Check:
1. Canonical prompt (`CANONICAL_SYSTEM_PROMPT.md`)
2. This customization guide
3. Empirica documentation (`docs/`)
4. Community discussions

**Still stuck?** File an issue with:
- Use case description
- Customization attempt
- Specific problem encountered

---

**Last Updated:** 2025-11-30  
**Version:** 2.0  
**Maintainer:** Empirica Core Team
