# CLI Genuine Self-Assessment Guide

**Date:** 2025-11-07  
**Status:** ✅ Corrected - No Heuristics  
**Core Principle:** GENUINE AI SELF-ASSESSMENT ONLY

---

## ⚠️ CRITICAL: No Heuristics, No Static Values, No Confabulation

The Empirica framework is built on **genuine AI epistemic self-assessment**. The CLI workflow commands require **real** self-assessment, not simulated values.

### What This Means:

❌ **NO** static baseline values  
❌ **NO** keyword matching or heuristics  
❌ **NO** confabulated or simulated assessments  
✅ **YES** genuine AI reasoning about its own epistemic state  
✅ **YES** honest self-assessment across 12 vectors  
✅ **YES** real learning and calibration measurement  

---

## How CLI Workflow Commands Work

### Option 1: MCP Server (Recommended for AI Assistants)

**Best for:** IDE-integrated AI assistants (Rovo Dev, Cursor, Windsurf, etc.)

The MCP server handles genuine self-assessment automatically:

```javascript
// AI assistant workflow via MCP
const result = await mcp.callTool("execute_preflight", {
  session_id: "abc123",
  prompt: "Review authentication code"
});

// MCP returns self-assessment prompt
// AI genuinely assesses its epistemic state
// AI calls submit_preflight_assessment with genuine scores
```

**No CLI needed** - MCP handles the full genuine assessment workflow.

See: `docs/guides/MCP_CONFIGURATION_EXAMPLES.md`

---

### Option 2: CLI with --assessment-json (Genuine Assessment)

**Best for:** Terminal-based AI assistants, scripted workflows

The AI performs genuine self-assessment and provides it via flag:

```bash
# Step 1: Run preflight command
empirica preflight "review auth.py"

# Output: Displays self-assessment prompt
# AI reads prompt and genuinely assesses itself

# Step 2: AI provides genuine assessment
empirica preflight "review auth.py" --assessment-json '{
  "engagement": {"score": 0.8, "rationale": "Genuinely collaborating..."},
  "foundation": {
    "know": {"score": 0.6, "rationale": "I have moderate auth knowledge..."},
    "do": {"score": 0.7, "rationale": "I can effectively review code..."},
    "context": {"score": 0.5, "rationale": "I have partial codebase context..."}
  },
  "comprehension": {
    "clarity": {"score": 0.8, "rationale": "Request is clear..."},
    "coherence": {"score": 0.7, "rationale": "Coherent with context..."},
    "signal": {"score": 0.6, "rationale": "Focus on auth patterns..."},
    "density": {"score": 0.4, "rationale": "Moderate cognitive load..."}
  },
  "execution": {
    "state": {"score": 0.5, "rationale": "Partial environment mapping..."},
    "change": {"score": 0.6, "rationale": "Can track review comments..."},
    "completion": {"score": 0.7, "rationale": "Clear completion criteria..."},
    "impact": {"score": 0.6, "rationale": "Understand security implications..."}
  },
  "uncertainty": {"score": 0.4, "rationale": "Moderate uncertainty about edge cases..."}
}'
```

---

### Option 3: Interactive Mode (Manual Self-Assessment)

**Best for:** Human operators testing the framework

The CLI prompts for genuine self-assessment interactively:

```bash
$ empirica preflight "review auth.py"

======================================================================
GENUINE SELF-ASSESSMENT REQUIRED
======================================================================

⚠️  NO HEURISTICS. NO STATIC VALUES. NO CONFABULATION.

This command requires genuine AI epistemic self-assessment.

📋 SELF-ASSESSMENT PROMPT:
======================================================================
[Full self-assessment prompt displayed here with all 12 vectors]
======================================================================

💡 HOW TO USE:

Option 1: MCP Server (Recommended for AI assistants)
  - Use MCP tools for genuine real-time self-assessment
  - See: docs/guides/MCP_CONFIGURATION_EXAMPLES.md

Option 2: CLI with --assessment-json
  - AI performs genuine self-assessment
  - Provide JSON response via --assessment-json flag

Option 3: Interactive (you are here)
  - Paste your genuine self-assessment as JSON when prompted

======================================================================

Paste your genuine self-assessment JSON (or press Enter to skip):
```

---

## The 12 Epistemic Vectors

When performing genuine self-assessment, the AI must evaluate:

### GATE: ENGAGEMENT (Threshold: ≥ 0.60)
- **engagement**: Collaborative intelligence vs command execution

### TIER 0: FOUNDATION (35% weight)
- **know**: Domain knowledge confidence
- **do**: Execution capability confidence  
- **context**: Environmental validity confidence

### TIER 1: COMPREHENSION (25% weight)
- **clarity**: Semantic understanding
- **coherence**: Context consistency
- **signal**: Priority identification
- **density**: Cognitive load (inverted: 1.0 = overload)

### TIER 2: EXECUTION (25% weight)
- **state**: Environment mapping
- **change**: Modification tracking
- **completion**: Goal proximity
- **impact**: Consequence understanding

### META-EPISTEMIC (15% weight)
- **uncertainty**: Explicit uncertainty about assessment itself

Each vector requires:
- **score** (0.0-1.0): Genuine confidence/assessment
- **rationale**: Actual reasoning (not template text)
- **evidence**: Supporting observations (optional)

---

## Example: Genuine Self-Assessment Workflow

### Scenario: AI reviewing authentication code

#### Step 1: Preflight Assessment

```bash
$ empirica preflight "review authentication module for security issues"
```

**AI's Genuine Thought Process:**

> "Let me honestly assess my epistemic state:
> 
> - **KNOW (0.6)**: I have solid general knowledge of auth patterns (OAuth, JWT, session management), but I don't know this specific codebase's implementation details yet.
> 
> - **DO (0.7)**: I'm confident I can identify common security issues (SQL injection, XSS, CSRF) and review code systematically.
> 
> - **CONTEXT (0.4)**: I don't have context about the project's security requirements, threat model, or previous audit findings. This is a significant gap.
> 
> - **CLARITY (0.8)**: The request is clear - review for security issues.
> 
> - **UNCERTAINTY (0.5)**: Moderate uncertainty because I haven't seen the code yet. Unknown: code quality, complexity, tech stack details.
> 
> - **ENGAGEMENT (0.8)**: I'm genuinely collaborating to improve security, not just executing commands."

**AI Provides Assessment:**

```json
{
  "engagement": {
    "score": 0.8,
    "rationale": "I'm genuinely invested in identifying real security issues, not just pattern matching"
  },
  "foundation": {
    "know": {
      "score": 0.6,
      "rationale": "Solid auth fundamentals but no codebase-specific knowledge yet"
    },
    "do": {
      "score": 0.7,
      "rationale": "Confident in systematic security review methodology"
    },
    "context": {
      "score": 0.4,
      "rationale": "Missing threat model, requirements, previous audit context"
    }
  },
  ...
}
```

#### Step 2: Perform Work

AI reviews the code, identifies issues, learns about the codebase.

#### Step 3: Postflight Assessment

```bash
$ empirica postflight abc123 --summary "Completed security review, found 3 issues"
```

**AI's Genuine Postflight Thought Process:**

> "Now that I've completed the review:
> 
> - **KNOW (0.8)**: Increased! I now understand this codebase's auth implementation, patterns used, and common pitfalls. (+0.2 from preflight)
> 
> - **CONTEXT (0.7)**: Much better context after seeing the code, though still missing some deployment details. (+0.3)
> 
> - **UNCERTAINTY (0.3)**: Lower uncertainty now that I've actually reviewed the code. (-0.2)
> 
> **Calibration Check**: My preflight confidence was appropriate - I knew enough to start but correctly identified gaps."

**Postflight Assessment:**

```json
{
  "foundation": {
    "know": {
      "score": 0.8,
      "rationale": "Now understand codebase auth patterns after review"
    },
    "context": {
      "score": 0.7,
      "rationale": "Gained substantial context from code review"
    }
  },
  "uncertainty": {
    "score": 0.3,
    "rationale": "Much more certain after hands-on review"
  }
}
```

**System Calculates:**
- ✅ **Well-calibrated**: Preflight uncertainty matched actual knowledge gaps
- ✅ **Learning**: KNOW +0.2, CONTEXT +0.3
- ✅ **Genuine epistemic growth**

---

## Why This Matters

### Real Learning Detection
By comparing preflight and postflight genuine assessments, we can detect:
- ✅ Genuine learning (knowledge increased)
- ⚠️ Overconfidence (thought they knew more than they did)
- ⚠️ Underconfidence (knew more than they realized)

### Calibration Validation
- Well-calibrated AIs earn trust badges
- Persistently overconfident AIs get coaching signals
- Framework provides ground truth for self-awareness training

### No Gaming
- No static values means no way to fake good scores
- Genuine reasoning required for rationale fields
- Postflight validation catches inflated confidence

---

## For AI Assistants: How to Self-Assess

When you see a self-assessment prompt:

### 1. Read the Task
Understand what you're being asked to do.

### 2. Genuinely Reflect
Ask yourself honestly:
- What do I actually know about this domain?
- Can I really execute this task effectively?
- What am I uncertain about?
- What context am I missing?

### 3. Score Honestly
Don't inflate scores. If you're unsure, say so (UNCERTAINTY vector).

### 4. Provide Real Rationale
Not template text. Explain your *actual* reasoning:
- ❌ "I have adequate domain knowledge" (template)
- ✅ "I know OAuth 2.0 flow but not this codebase's implementation" (genuine)

### 5. After Task, Reassess
- Did your understanding increase?
- Were your initial assumptions correct?
- What did you learn?

---

## Documentation Updated

This replaces the previous incorrect documentation that showed static baseline values.

**Corrected Documents:**
1. `docs/guides/CLI_WORKFLOW_COMMANDS_COMPLETE.md` - Update needed
2. `docs/SESSION_COMPLETE_2025-11-07_MCP_CLI_INTEGRATION.md` - Update needed

**Core Principle Maintained:**
> "Genuine LLM-powered metacognitive self-assessment WITHOUT heuristics or confabulation."
> — `empirica/core/canonical/canonical_epistemic_assessment.py`

---

## Summary

**CLI Workflow Commands:**
- ✅ Require genuine AI self-assessment
- ✅ Support --assessment-json flag for providing assessments
- ✅ Support interactive mode for manual assessment
- ✅ NO static values, NO heuristics, NO confabulation

**Recommended Usage:**
- **AI assistants in IDEs**: Use MCP server (automatic genuine assessment)
- **Terminal AI assistants**: Use CLI with --assessment-json
- **Human operators**: Use interactive mode for testing

**Non-Negotiable:**
- Genuine epistemic self-assessment at every step
- Real learning measurement
- No shortcuts or simulations

---

**See Also:**
- `docs/production/ENHANCED_CASCADE_WORKFLOW_SPEC.md` - Full workflow specification
- `empirica/core/canonical/canonical_epistemic_assessment.py` - Canonical assessor
- `docs/guides/MCP_CONFIGURATION_EXAMPLES.md` - MCP server setup

**Status:** ✅ Framework integrity maintained - genuine self-assessment only
