# Compressed System Prompt Usage Guide

## Overview

The compressed system prompt uses **semantic compression** to reduce token usage while maintaining full Empirica functionality.

## Token Comparison

| Prompt Type | Word Count | Estimated Tokens | Use Case |
|-------------|-----------|------------------|----------|
| **Full (GENERIC_EMPIRICA_SYSTEM_PROMPT.md)** | 1,603 | ~2,100 | First-time users, detailed examples needed |
| **Compressed (SYSTEM_PROMPT_COMPRESSED.md)** | 854 | ~1,100 | Experienced users, production use |
| **Savings** | -749 (-47%) | **~1,000 tokens** | Every request |

## What is Semantic Compression?

**Semantic compression** means encoding the same information in a denser format that AI models can still understand perfectly:

### Example: Traditional Format
```markdown
## 13 Epistemic Vectors

Empirica uses 13 epistemic vectors to track your knowledge state:

1. ENGAGEMENT: This vector measures whether you are engaged with the task. 
   A score of 0.6 or higher is required to proceed.
2. KNOW: This vector tracks your domain knowledge on a scale from 0 to 1.
3. DO: This vector measures your capability to execute the task...
```
**Token cost:** ~300 tokens

### Example: Compressed Format
```markdown
### 13 Epistemic Vectors (0-1 scale, assess HONESTLY):
1. **ENGAGEMENT** - Task engagement (0.6+ required)
2. **KNOW** - Domain knowledge
3. **DO** - Execution capability
```
**Token cost:** ~50 tokens

**Result:** Same information, 83% fewer tokens!

## How Semantic Compression Works

### Techniques Used:

1. **Dense Structure**: Use numbered lists, bullet points, tables instead of paragraphs
2. **2-3 Word Phrases**: "Task engagement (0.6+ required)" vs "measures whether you are engaged"
3. **Symbols Over Words**: `→` instead of "then", `≠` instead of "is not equal to"
4. **Code Blocks**: Show patterns in executable format, not prose
5. **Hierarchical Headers**: Use markdown structure to convey relationships
6. **Mandatory Sections Only**: Remove "nice to have" explanations

### What Gets Compressed:

- ✅ **Verbose explanations** → Dense phrases
- ✅ **Examples in prose** → Code patterns
- ✅ **Repetitive content** → Single canonical reference
- ✅ **Motivational text** → Core directives only

### What Gets Preserved:

- ✅ **All 13 epistemic vectors** (just denser format)
- ✅ **Complete CASCADE workflow** (states + transitions)
- ✅ **All 23 MCP tools** (signatures included)
- ✅ **Critical anti-patterns** (what NOT to do)
- ✅ **Core principles** (epistemic transparency, etc.)

## When to Use Each Version

### Use Compressed (SYSTEM_PROMPT_COMPRESSED.md)

**Best for:**
- ✅ Production environments
- ✅ Experienced Empirica users
- ✅ Token-constrained scenarios
- ✅ Multi-cascade sessions (prevents token bloat)
- ✅ Cost-sensitive deployments

**Characteristics:**
- Assumes familiarity with Empirica concepts
- Dense, structured format
- Minimal examples (just patterns)
- ~1,100 tokens per request

### Use Full (GENERIC_EMPIRICA_SYSTEM_PROMPT.md)

**Best for:**
- ✅ First-time users
- ✅ Training/onboarding
- ✅ When examples are critical
- ✅ Debugging/troubleshooting sessions
- ✅ Documentation reference

**Characteristics:**
- Detailed explanations
- Complete code examples
- Step-by-step walkthroughs
- ~2,100 tokens per request

## Installation

### Update Rovo Dev Config (Already Done!)

```bash
# Config already updated to use compressed prompt:
cat /home/yogapad/.rovodev/config_empirica.yml | grep -A 5 "additionalSystemPrompt"
```

### Manual Installation (Other Platforms)

**For Gemini CLI:**
```bash
# Copy compressed prompt to Gemini system prompt location
cp docs/user-guides/SYSTEM_PROMPT_COMPRESSED.md ~/.gemini/system_empirica.md

# Set environment variable
export GEMINI_SYSTEM_MD=~/.gemini/system_empirica.md
```

**For Claude Desktop:**
```bash
# Copy to project root
cp docs/user-guides/SYSTEM_PROMPT_COMPRESSED.md ./CLAUDE.md
```

**For other platforms:**
- Copy content of `SYSTEM_PROMPT_COMPRESSED.md` to your platform's system prompt configuration

## Validation

### Test Token Reduction

```bash
# Count tokens in full prompt
wc -w docs/user-guides/GENERIC_EMPIRICA_SYSTEM_PROMPT.md
# Output: 1603 words (~2,100 tokens)

# Count tokens in compressed prompt
wc -w docs/user-guides/SYSTEM_PROMPT_COMPRESSED.md
# Output: 854 words (~1,100 tokens)

# Savings
echo "Token savings: ~1,000 tokens per request (47% reduction)"
```

### Test Functionality

Start a new session and verify all features work:

```bash
# 1. Bootstrap session
empirica bootstrap --ai-id test-agent --level 2

# 2. Execute PREFLIGHT
empirica preflight <session-id> "Test task"

# 3. Create goal (explicit)
empirica create-goal <session-id> "Test investigation" --scope "Verify compressed prompt"

# 4. Submit assessment
empirica submit-preflight <session-id> --vectors '{"engagement":0.8,"know":0.7,...}' --reasoning "Testing compressed prompt"

# All should work identically to full prompt
```

## Cost Impact

### Per-Request Savings

**Assumptions:**
- Average session: 20 requests
- Token cost: $0.015 per 1K input tokens (Claude Sonnet)

**Calculation:**
```
Full prompt: 2,100 tokens × 20 requests = 42,000 tokens = $0.63
Compressed:  1,100 tokens × 20 requests = 22,000 tokens = $0.33
Savings: 20,000 tokens = $0.30 per session (47% reduction)
```

### Monthly Savings (100 sessions)

```
Full prompt: 42,000 × 100 = 4.2M tokens = $63.00
Compressed:  22,000 × 100 = 2.2M tokens = $33.00
Savings: 2M tokens = $30.00/month per 100 sessions
```

## Migrating from Full to Compressed

### Step 1: Backup Current Config
```bash
cp /home/yogapad/.rovodev/config_empirica.yml /home/yogapad/.rovodev/config_empirica.yml.backup
```

### Step 2: Apply Compressed Prompt
Already done! Config updated automatically.

### Step 3: Test First Session
```bash
# Start new session with compressed prompt
empirica bootstrap --ai-id rovo-dev --level 2

# If issues arise, rollback:
# mv /home/yogapad/.rovodev/config_empirica.yml.backup /home/yogapad/.rovodev/config_empirica.yml
```

### Step 4: Monitor Performance
- ✅ Check that all MCP tools work
- ✅ Verify CASCADE workflow executes correctly
- ✅ Confirm epistemic vectors are assessed properly
- ✅ Validate handoff reports generate successfully

## Troubleshooting

### "AI doesn't understand Empirica concepts"

**Likely cause:** Platform not using compressed prompt

**Fix:**
```bash
# Verify config is correct
cat /home/yogapad/.rovodev/config_empirica.yml | grep -A 2 "additionalSystemPrompt"

# Should show compressed prompt content starting with:
# "# [EMPIRICA AGENT: CORE DIRECTIVES]"
```

### "Need more detailed examples"

**Solution:** Load full prompt for specific query

```bash
# Temporarily reference full documentation
cat docs/user-guides/GENERIC_EMPIRICA_SYSTEM_PROMPT.md | grep -A 20 "Phase 2: INVESTIGATE"
```

Or add to query:
```
"Help me with X. For detailed examples, reference: docs/user-guides/GENERIC_EMPIRICA_SYSTEM_PROMPT.md"
```

### "Token savings not as expected"

**Check:**
1. Config is using compressed prompt (not full)
2. No duplicate system prompts loaded
3. Platform isn't adding extra context automatically

```bash
# Verify only compressed prompt is loaded
grep -c "EMPIRICA AGENT: CORE DIRECTIVES" /home/yogapad/.rovodev/config_empirica.yml
# Should output: 1
```

## Best Practices

### 1. Use Compressed for Production
- Default to compressed prompt for all production work
- Keep full prompt available for reference

### 2. Combine with Session Continuity
- Use compressed prompt + git checkpoints (97.5% reduction)
- Use compressed prompt + handoff reports (98.8% reduction)
- **Result:** Massive token efficiency across multi-session work

### 3. Load Full Prompt On-Demand
```bash
# Only when needed:
"For detailed workflow examples, read: docs/user-guides/GENERIC_EMPIRICA_SYSTEM_PROMPT.md"
```

### 4. Monitor Effectiveness
```bash
# Track token usage over time
empirica performance-metrics

# Compare compressed vs full prompt sessions
empirica token-efficiency-report
```

## FAQ

**Q: Does compressed prompt lose functionality?**  
A: No. All features preserved, just denser format.

**Q: Will AI understand compressed format as well?**  
A: Yes. Modern LLMs excel at structured, dense information.

**Q: Can I compress further?**  
A: Possible, but diminishing returns. 854 words is near-optimal for maintaining clarity.

**Q: Should I always use compressed?**  
A: For production: yes. For learning/onboarding: use full prompt.

**Q: What if I need examples?**  
A: Reference full prompt on-demand: `docs/user-guides/GENERIC_EMPIRICA_SYSTEM_PROMPT.md`

## References

- **Compressed Prompt:** `docs/user-guides/SYSTEM_PROMPT_COMPRESSED.md`
- **Full Prompt:** `docs/user-guides/GENERIC_EMPIRICA_SYSTEM_PROMPT.md`
- **Optimization Plan:** `SYSTEM_PROMPT_OPTIMIZATION_PLAN.md`
- **Config Location:** `/home/yogapad/.rovodev/config_empirica.yml`

---

**Status:** ✅ Compressed prompt active (47% token reduction)  
**Next:** Monitor effectiveness over multiple sessions  
**Goal:** Maintain quality while reducing token costs
