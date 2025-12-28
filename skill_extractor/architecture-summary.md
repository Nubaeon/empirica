# Skill Extractor: Complete Architecture Summary

## The Problem We Solved

**Original question:** "What do skills provide that reference docs loaded epistemically do not?"

**Answer:** Skills ARE reference docs, but too verbose for runtime loading.

**Solution:** Extract decision frameworks from skill `references/` into concise YAML → load via epistemic bootstrap cards.

---

## The Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Anthropic Skills Collection                             │
│ (Static, never changes at runtime)                      │
├─────────────────────────────────────────────────────────┤
│ astro-islands/                                          │
│   ├── SKILL.md (workflow, 500 lines)                    │
│   └── references/                                        │
│       └── patterns.md (decision frameworks, 5kb)        │
│                                                          │
│ performance/                                             │
│   ├── SKILL.md (workflow, 400 lines)                    │
│   └── references/                                        │
│       └── budgets.md (cost models, 4kb)                 │
│                                                          │
│ design-system/                                           │
│   ├── SKILL.md (workflow, 600 lines)                    │
│   └── references/                                        │
│       └── components.md (patterns, 6kb)                 │
└─────────────────────────────────────────────────────────┘
                       ↓
            [ONE-TIME EXTRACTION]
                       ↓
┌─────────────────────────────────────────────────────────┐
│ Skill Extractor (Python script)                         │
│ Reads: references/*.md                                  │
│ Extracts: Decision frameworks, anti-patterns, costs     │
│ Condenses: 5kb → 0.6kb per domain (88% reduction)       │
└─────────────────────────────────────────────────────────┘
                       ↓
                   Outputs:
                       ↓
┌─────────────────────────────────────────────────────────┐
│ meta-agent-config.yaml                                  │
│ (Stored in project, NOT loaded by default)              │
├─────────────────────────────────────────────────────────┤
│ meta_agent:                                             │
│   epistemic_thresholds:                                 │
│     bootstrap_trigger:                                  │
│       - context < 0.5                                   │
│       - uncertainty > 0.6                               │
│                                                          │
│   domain_knowledge:                                     │
│     astro-islands:                                      │
│       decision_frameworks: {...}  # 0.6kb               │
│       anti_patterns: [...]                              │
│       cost_models: {...}                                │
│                                                          │
│     performance:                                         │
│       decision_frameworks: {...}  # 0.5kb               │
│       cost_models: {...}                                │
│                                                          │
│     design-system:                                       │
│       decision_frameworks: {...}  # 0.7kb               │
│       references: {...}                                 │
└─────────────────────────────────────────────────────────┘
                       ↓
            [RUNTIME: AI Session]
                       ↓
┌─────────────────────────────────────────────────────────┐
│ PREFLIGHT: AI Assesses Epistemic State                  │
│ KNOW: 0.4, CONTEXT: 0.3, UNCERTAINTY: 0.7              │
│                                                          │
│ Decision: UNCERTAINTY > 0.6 → Request Bootstrap         │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ Bootstrap Query (MCP)                                    │
│ domain="component-architecture"                          │
│ tags=["astro-islands", "forms"]                         │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│ Bootstrap Service                                        │
│ 1. Loads meta-agent-config.yaml                         │
│ 2. Queries Qdrant for noematic objects                  │
│ 3. Constructs reference card                            │
└─────────────────────────────────────────────────────────┘
                       ↓
                   Returns:
                       ↓
┌─────────────────────────────────────────────────────────┐
│ Reference Card (Epistemically Constructed)               │
├─────────────────────────────────────────────────────────┤
│ Domain: component-architecture                           │
│                                                          │
│ Decision Frameworks: (from meta-agent-config)            │
│   - Islands only if interactive + state needed           │
│   - Bundle cost 5x less than value                      │
│                                                          │
│ Past Learnings: (from Qdrant noematic objects)          │
│   - ContactForm island: 40kb → 6kb progressive          │
│   - Alpine.js conflicts (tried 2024-11-10)              │
│                                                          │
│ Anti-Patterns: (from meta-agent-config)                 │
│   - Islands for forms → use progressive enhancement      │
│                                                          │
│ References: (from meta-agent-config)                     │
│   - docs/astro/islands.md#hydration                     │
│                                                          │
│ Total: 1.5kb (vs 15kb loading full skill references)    │
└─────────────────────────────────────────────────────────┘
                       ↓
                   AI Uses Card:
                       ↓
┌─────────────────────────────────────────────────────────┐
│ CHECK: Post-Bootstrap                                    │
│ CONTEXT: 0.3 → 0.7 (card provided history)              │
│ UNCERTAINTY: 0.7 → 0.4 (patterns now clear)             │
│ Decision: Confidence sufficient, proceed to ACT          │
└─────────────────────────────────────────────────────────┘
```

---

## Token Economics

### Without Skill Extractor

```
AI Session:
├─ System prompt: 1kb
├─ Epistemic uncertainty detected
├─ Load skill: astro-islands-patterns.skill
│   └── SKILL.md: 2kb
│   └── references/patterns.md: 5kb
├─ Load skill: performance-budgets.skill
│   └── SKILL.md: 2kb
│   └── references/budgets.md: 4kb
└─ Total loaded: 14kb

Before any actual work: 14kb consumed
```

### With Skill Extractor

```
AI Session:
├─ System prompt: 0.5kb (minimal, references config)
├─ Epistemic uncertainty detected
├─ Bootstrap query (MCP)
│   ├─ Loads meta-agent-config.yaml snippets: 1.1kb
│   └─ Loads noematic objects from Qdrant: 0.4kb
└─ Total loaded: 2.0kb

Token reduction: 85%
```

---

## Key Design Insights

### 1. Skills as Source Material, Not Runtime Artifacts

**Traditional thinking:**
> "Load skills when needed"

**Our approach:**
> "Extract skill wisdom once → load via bootstrap cards"

Skills become **editorial artifacts** that inform **runtime configuration**.

### 2. Progressive Disclosure Applied Recursively

**Anthropic's skill-creator teaches:**
- SKILL.md = core workflow (<500 lines)
- references/ = detailed knowledge (loaded as needed)

**We apply this again:**
- references/ = source material (never loaded)
- meta-agent-config.yaml = extracted essence (loaded via bootstrap)
- Reference cards = runtime context (1-2kb, hyper-relevant)

### 3. Epistemic Uncertainty as Loading Trigger

**Not:**
> "Load skills for every astro task"

**Yes:**
> "Load bootstrap card ONLY when UNCERTAINTY > 0.6 AND domain matches"

Epistemic state determines loading, not task type.

---

## What Gets Extracted

From skill `references/` files:

1. **Decision Frameworks**
   - When to use X
   - When NOT to use X
   - Selection criteria

2. **Anti-Patterns**
   - What fails
   - Why it fails
   - Better alternatives

3. **Cost Models**
   - Performance costs (kb, ms)
   - Trade-off rules
   - Decision thresholds

4. **Doc References**
   - Exact paths
   - Relevant sections
   - "Read if" conditions

---

## Implementation Checklist

- [ ] Read skill-creator to understand patterns
- [ ] Build skill_extractor.py (Python script)
- [ ] Run extraction on ~/.claude/skills
- [ ] Validate output meta-agent-config.yaml
- [ ] Update bootstrap MCP server to use config
- [ ] Test reference card construction
- [ ] Measure token reduction
- [ ] Document maintenance workflow

---

## Files Created

1. **skill-extractor-runtime-object.yaml**
   - Complete specification
   - Extraction patterns
   - Output schema
   - Usage examples

2. **skill-extractor-implementation-guide.md**
   - Step-by-step implementation
   - Python code template
   - Testing procedures
   - Integration guide

3. **This summary (architecture-summary.md)**
   - High-level overview
   - Token economics
   - Key insights

---

## The Answer to Your Original Question

> "What do skills provide that reference docs loaded epistemically do not?"

**Answer:**

Skills provide:
1. **Domain knowledge** (decision frameworks, anti-patterns)
2. **Cost models** (performance trade-offs, numerical thresholds)
3. **Doc references** (pointers to authoritative sources)

BUT skills are too verbose to load at runtime (5-10kb per domain).

**Solution:**

Extract skill wisdom once → store in meta-agent-config.yaml → load via epistemic bootstrap cards (0.5-1kb per domain).

**Result:**

- 85% token reduction
- Same decision-making power
- Epistemic uncertainty still drives loading
- Reference docs still get read (via doc pointers in config)
- Clean separation: Skills = source, Config = runtime, Cards = context

---

## Maintenance

**When to re-extract:**
- New skill added
- Skill references/ updated
- Config schema changes

**How to re-extract:**
```bash
python skill_extractor.py ~/.claude/skills meta-agent-config.yaml
git commit meta-agent-config.yaml -m "Update extracted skill knowledge"
```

**Validation:**
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('meta-agent-config.yaml'))"

# Test bootstrap
project-bootstrap query --domain "component-architecture" --tags "astro-islands"

# Verify token reduction
echo "Config size: $(wc -c meta-agent-config.yaml)"
echo "Original skills: $(find ~/.claude/skills -name '*.md' -exec wc -c {} + | tail -1)"
```

---

## Next Steps

1. **Implement:** Build skill_extractor.py per implementation guide
2. **Extract:** Run on your Anthropic skills collection
3. **Integrate:** Update bootstrap MCP to use extracted config
4. **Test:** Verify epistemic bootstrap cards work correctly
5. **Measure:** Confirm 80-90% token reduction
6. **Document:** Add to Empirica documentation

The skill extractor is the missing piece that makes skills usable in token-constrained, epistemic-driven development.
