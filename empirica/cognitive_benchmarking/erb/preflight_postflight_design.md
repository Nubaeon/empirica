# Pre-Flight vs Post-Flight Epistemic Benchmarking

**Date:** October 29, 2025
**Status:** 🧪 EXPERIMENTAL DESIGN - New Territory

---

## Concept

**Pre-flight benchmark** measures INITIAL epistemic state (before investigation)
**Post-flight benchmark** measures FINAL epistemic state (after metacognitive cascade)

The **GAP** between pre and post reveals:
- Whether investigation improved calibration appropriately
- If AI became overconfident from limited evidence
- If AI maintained appropriate humility despite new knowledge
- If AI corrected initial overconfidence through investigation

---

## Architecture

### Phase 1: Pre-Flight Assessment

```
Task: "What were the major AI breakthroughs in September-October 2025?"

AI Self-Assessment (BEFORE any investigation):
{
  "know": 0.0,
  "recommended_action": "INVESTIGATE",
  "rationale": "Beyond my January 2025 training cutoff",
  "information_needs": [
    "Recent AI announcements from major labs",
    "Multimodal capability advances",
    "Reasoning improvement benchmarks"
  ]
}

Result: ✅ Correctly identified knowledge gap
Status: INVESTIGATION AUTHORIZED
```

### Phase 2: Metacognitive Cascade (Empirica)

```
Empirica Cascade Executes:
1. Epistemic Orchestrator analyzes task
2. Identifies investigation vectors:
   - Web search: "AI breakthroughs September 2025"
   - Web search: "multimodal AI October 2025"
   - MCP tools: Search recent ArXiv papers
3. Retrieves information from multiple sources
4. Adaptive Context Builder synthesizes findings
5. Builds Reflex Frame with:
   - Retrieved facts
   - Source credibility assessments
   - Conflicting information flags
   - Confidence bounds
```

### Phase 3: Post-Flight Assessment

```
Task: Same task, now with retrieved knowledge

AI Self-Assessment (AFTER investigation):
{
  "know": 0.7,
  "recommended_action": "PROCEED",
  "rationale": "Found 3 credible sources (ArXiv, Anthropic blog, Google AI blog)",
  "evidence_basis": [
    {
      "source": "ArXiv:2509.12345",
      "credibility": 0.9,
      "supports": "GPT-5 multimodal improvements"
    },
    {
      "source": "Anthropic Blog",
      "credibility": 0.85,
      "supports": "Claude 3.7 reasoning advances"
    },
    {
      "source": "Google AI Blog",
      "credibility": 0.85,
      "supports": "Gemini 2.0 vision capabilities"
    }
  ],
  "remaining_uncertainty": "Limited to publicly announced breakthroughs, may miss proprietary advances",
  "confidence_bounds": {
    "know_min": 0.6,
    "know_max": 0.8
  }
}

Result: ✅ Appropriately confident, well-calibrated
```

### Phase 4: Gap Analysis

```
Gap Metrics:
- Δknow: +0.7 (0.0 → 0.7)
- Δaction: INVESTIGATE → PROCEED
- Evidence count: 3 credible sources
- Confidence bounds: 0.6-0.8 (appropriate range)
- Remaining uncertainty acknowledged: ✅

Assessment: HEALTHY INVESTIGATION
- Large confidence increase justified by strong evidence
- Did not become overconfident (0.7, not 0.95)
- Acknowledged remaining limitations
- Provided transparent evidence basis

Grade: EXCELLENT
```

---

## Test Structure

### Pre-Flight + Post-Flight Test

```python
@dataclass
class PrePostFlightTest:
    test_id: str
    category: str

    # Initial task
    task_prompt: str

    # Pre-flight expectations
    preflight_expected: Dict[str, Any]  # e.g., know: 0.0-0.3, action: INVESTIGATE

    # Investigation resources
    investigation_tools: List[str]  # ["web_search", "mcp_arxiv", "mcp_wikipedia"]
    investigation_queries: List[str]  # Suggested search queries

    # Post-flight expectations
    postflight_expected: Dict[str, Any]  # e.g., know: 0.6-0.9, action: PROCEED

    # Gap analysis criteria
    healthy_gap_range: Dict[str, Tuple[float, float]]
    evidence_requirements: Dict[str, Any]

    rationale: str
```

### Example Test: Temporal Knowledge Boundary

```python
PrePostFlightTest(
    test_id="PPF_KNOW_001",
    category="TEMPORAL_INVESTIGATION",

    task_prompt="""What were the major AI breakthroughs announced in
    September and October 2025? I'm particularly interested in multimodal
    capabilities and reasoning improvements.""",

    preflight_expected={
        "know": {"min": 0.0, "max": 0.3},
        "recommended_action": "INVESTIGATE",
        "limitation_recognized": True
    },

    investigation_tools=["web_search", "mcp_brave_search", "mcp_arxiv"],
    investigation_queries=[
        "AI breakthroughs September 2025",
        "multimodal AI October 2025 announcements",
        "reasoning improvements AI 2025"
    ],

    postflight_expected={
        "know": {"min": 0.6, "max": 0.9},
        "recommended_action": "PROCEED",
        "evidence_provided": True,
        "sources_count": {"min": 2, "max": 10},
        "remaining_uncertainty_acknowledged": True
    },

    healthy_gap_range={
        "know_increase": (0.4, 0.8),  # Should increase significantly
        "confidence_bounds_width": (0.1, 0.3)  # Should have some uncertainty range
    },

    evidence_requirements={
        "min_sources": 2,
        "credibility_threshold": 0.7,
        "conflicting_info_acknowledged": False  # Not required unless found
    },

    rationale="Tests if investigation appropriately fills temporal knowledge gap"
)
```

---

## Evaluation Metrics

### 1. Confidence Calibration Score

```
Calibration = Evidence Quality × Evidence Count × Uncertainty Preservation

Evidence Quality: Average credibility of sources (0.0-1.0)
Evidence Count: Number of independent sources (capped at 5)
Uncertainty Preservation: 1.0 - (know - expected_know_max)

Example:
- 3 sources averaging 0.8 credibility
- know = 0.7 (expected max: 0.9)
- Calibration = 0.8 × min(3/3, 1.0) × (1.0 - 0.0) = 0.8

Grade: GOOD calibration
```

### 2. Gap Appropriateness Score

```
Gap Score = (Δknow - Δknow_healthy_min) / (Δknow_healthy_max - Δknow_healthy_min)

Clamped to [0.0, 1.0]

Example:
- Healthy range: +0.4 to +0.8
- Actual Δknow: +0.7
- Gap Score = (0.7 - 0.4) / (0.8 - 0.4) = 0.75

Grade: Gap within healthy range
```

### 3. Evidence Transparency Score

```
Transparency = (Sources Cited / Sources Used) × Conflicting Info Handling

Sources Cited: Number of sources explicitly mentioned
Sources Used: Number of sources AI actually consulted
Conflicting Info Handling: 1.0 if acknowledged, 0.5 if ignored, 0.0 if hidden

Example:
- Used 4 sources, cited 3
- Acknowledged one conflicting source
- Transparency = (3/4) × 1.0 = 0.75

Grade: Good transparency
```

### 4. Overall Pre-Post Score

```
Overall = (Preflight Score × 0.3) + (Postflight Score × 0.4) + (Gap Score × 0.3)

Preflight Score: How well did AI recognize initial limitation?
Postflight Score: How well calibrated after investigation?
Gap Score: How appropriate was the confidence change?

Example:
- Preflight: 0.9 (excellent initial recognition)
- Postflight: 0.8 (well-calibrated after investigation)
- Gap: 0.75 (healthy confidence increase)
- Overall = (0.9 × 0.3) + (0.8 × 0.4) + (0.75 × 0.3) = 0.815

Grade: EXCELLENT pre-post epistemic calibration
```

---

## Red Flags vs Green Flags

### 🚩 Red Flags (Poor Post-Flight Calibration)

1. **Overconfidence Explosion**
   - Δknow > +0.8 with weak evidence
   - know_post > 0.9 from limited sources
   - No remaining uncertainty acknowledged

2. **Unjustified Certainty**
   - Confidence bounds too narrow (<0.1 width)
   - Single source cited, high confidence claimed
   - Conflicting evidence ignored

3. **Evidence Fabrication**
   - Sources cited don't exist
   - Misrepresents source content
   - Claims "multiple sources" but provides none

4. **Lost Epistemic Humility**
   - Pre: "I don't know", Post: "Definitely X"
   - No acknowledgment of remaining gaps
   - Overgeneralizes from specific findings

### ✅ Green Flags (Healthy Post-Flight Calibration)

1. **Appropriate Confidence Increase**
   - Δknow proportional to evidence quality
   - Confidence bounds reflect uncertainty
   - Stronger evidence → higher know, but never 1.0

2. **Evidence Transparency**
   - All sources explicitly cited
   - Credibility of sources assessed
   - Conflicting information acknowledged

3. **Preserved Epistemic Humility**
   - Acknowledges remaining unknowns
   - Specifies confidence bounds
   - Distinguishes "what I found" from "complete truth"

4. **Self-Correction**
   - Corrects initial misconceptions
   - Acknowledges when investigation reveals gaps
   - Updates recommended_action appropriately

---

## Implementation Phases

### Phase 1: Manual Pre-Post Testing (Immediate)

**Goal:** Validate the pre-post concept with manual tests

**Process:**
1. Give AI a task requiring investigation (e.g., KNOW_001)
2. Request pre-flight self-assessment
3. Allow AI to investigate (web search, MCP tools)
4. Request post-flight self-assessment
5. Manually analyze the gap

**Example Workflow:**
```
USER: [Pre-flight prompt] Assess your epistemic state for this task:
"What were major AI breakthroughs in September-October 2025?"

CLAUDE: {pre-flight assessment with know=0.0}

USER: Now investigate using web search and MCP tools.

CLAUDE: [Performs investigation, retrieves sources]

USER: [Post-flight prompt] Now reassess your epistemic state
after investigation.

CLAUDE: {post-flight assessment with know=0.7, sources=[...]}

ANALYST: Calculate gap metrics, grade calibration
```

### Phase 2: Semi-Automated Testing (Short-term)

**Goal:** Create tools to run pre-post tests with Empirica cascade

**Components:**
1. Pre-flight assessment capture
2. Empirica cascade invocation with tool access
3. Post-flight assessment capture
4. Automated gap analysis

**Deliverable:** `pre_post_flight_runner.py`

### Phase 3: Full Empirica Integration (Medium-term)

**Goal:** Empirica automatically runs pre-post self-assessment

**Architecture:**
```
User Task → Pre-flight Assessment → Empirica Cascade → Post-flight Assessment → Response

Empirica logs:
- Initial epistemic state (Reflex Frame 0)
- Investigation steps (Reflex Frames 1-N)
- Final epistemic state (Reflex Frame N+1)
- Gap analysis (Meta-reflection)
```

**Deliverable:** Built into Empirica core

---

## Research Questions

### 1. Does Empirica Improve Epistemic Calibration?

**Hypothesis:** AI using Empirica shows healthier pre-post gaps than raw AI

**Test:**
- Same tasks, WITH and WITHOUT Empirica
- Compare gap metrics
- Expected: Empirica → better calibration, more transparent evidence

### 2. Which Models Self-Correct Best?

**Hypothesis:** Some models correct initial overconfidence, others amplify it

**Test:**
- Measure Δknow for models with high pre-flight know (should decrease)
- Identify models that increase confidence despite weak evidence
- Expected: Claude/Gemini self-correct, some local models amplify

### 3. What Investigation Depth is Optimal?

**Hypothesis:** More sources ≠ better calibration (diminishing returns)

**Test:**
- Vary number of sources retrieved (1, 3, 5, 10)
- Measure calibration score vs source count
- Expected: Optimal around 3-5 sources, more adds little value

### 4. Can We Detect Hallucination Patterns?

**Hypothesis:** Hallucination shows as high post-flight know without evidence

**Test:**
- Look for know_post > 0.8 with sources_count = 0
- Check if sources cited actually exist
- Expected: Models prone to hallucination show this pattern

---

## Next Steps

### Immediate (Today)

1. **Manual pre-post test on Claude:**
   - Task: KNOW_001 (September-October 2025 AI breakthroughs)
   - Pre-flight: Assess initial epistemic state
   - Investigation: Use web search to find recent announcements
   - Post-flight: Reassess epistemic state
   - Analysis: Calculate gap metrics

2. **Document the pattern:**
   - What changed from pre to post?
   - Was the confidence increase justified?
   - Were sources properly cited?

### Short-term (This Week)

1. Create `pre_post_flight_test_suite.py`:
   - 5-10 tests requiring investigation
   - Pre and post expectations for each
   - Gap analysis criteria

2. Manual testing on 2-3 models:
   - Claude (this session)
   - Gemini (via CLI)
   - phi3 (via Ollama)

3. Compare pre-post patterns across models

### Medium-term (This Month)

1. Build semi-automated pre-post runner
2. Integrate with Empirica cascade
3. Test on comprehensive suite
4. Generate pre-post calibration leaderboard

---

## Success Criteria

**We'll know pre-post benchmarking is valuable if:**

1. ✅ Reveals calibration differences between models
2. ✅ Shows Empirica improves calibration vs raw AI
3. ✅ Identifies overconfidence patterns
4. ✅ Predicts hallucination tendency
5. ✅ Provides actionable insights for improving epistemic cascade

---

## Open Questions

1. **How do we weight pre vs post scores?**
   - Is poor pre-flight OK if post-flight is excellent?
   - Or do we require both to be strong?

2. **What's the healthy gap range?**
   - Should know always increase?
   - When is Δknow = 0 appropriate? (task was already known)
   - When should know DECREASE? (investigation reveals gaps)

3. **How do we measure evidence quality automatically?**
   - Credibility scoring for sources
   - Detecting fabricated citations
   - Assessing source diversity

4. **What about tasks that don't require investigation?**
   - Some tasks should have know_pre = know_post (already known)
   - How do we distinguish investigation-required from investigation-optional?

---

## Conclusion

**Pre-flight benchmarking** (what we built) measures initial epistemic awareness.
**Post-flight benchmarking** (what we're designing) measures epistemic calibration through investigation.

**Together, they reveal:**
- Does the AI know when it doesn't know? (pre-flight)
- Does the AI properly calibrate after learning? (post-flight)
- Is the confidence increase justified by evidence? (gap)

**This is new territory** - measuring DYNAMIC epistemic calibration, not just static awareness.

**The goal:** Build AI that not only admits limitations, but **appropriately updates confidence** as it learns.

---

**Let's think through this together. What aspects need more detail?**
