# Reasoning Memory Architecture
## Compressed Transfer with Full-Graph Storage

**Date:** 2025-11-04 (Q3/Q4)
**Status:** Vision / Future Work
**Priority:** Phase 6C+ (Post cognitive orchestration)

---

## 🎯 Core Insight

**Problem:** Full reasoning graphs (600-3000 tokens) break our 500-token snapshot target.

**Solution:** Store full graphs separately, transfer compressed pointers with fetch-on-demand.

---

## 📊 Token Economics (Reality Check)

| Item | Token Count | Transfer Cost |
|------|-------------|---------------|
| Conclusion + 3 assumptions + 3 evidence refs | 80-200 | ✅ Acceptable |
| Single ReasoningStep (JSON) | 40-150 | ✅ Acceptable |
| Full reasoning graph (10 steps) | 600-3000 | ❌ Too large |
| Long-form chain-of-thought | 5000+ | ❌ Way too large |

**Implication:** Full graphs in every snapshot is not viable. Must offload to storage.

---

## 🏗️ Architecture: Split Storage + Compressed Transfer

### **Snapshot (Transferred) - Minimal Tokens**

```python
{
    "snapshot_id": "abc123",
    "vectors": {...},
    "context_summary": "API has JWT secret in logs",
    "conclusion": "Rotate JWT secret immediately",

    # Compressed reasoning (SMALL)
    "reasoning_brief": "Observed JWT secret in env vars. Env vars are logged. Logs unencrypted for 30d. Therefore secret likely compromised.",
    "reasoning_tags": ["jwt_secret_in_logs", "rotate_secret", "high_urgency"],
    "top_assumptions": [
        "Logs retained 30 days (CHECK THIS)",
        "No log encryption (VERIFY)"
    ],
    "reasoning_embedding": [0.23, 0.45, ...],  # Semantic fingerprint

    # Pointer to full graph
    "reasoning_ref": "sha256:abc123def456...",  # Content-addressed
    "reasoning_fidelity": 0.92,  # How much preserved in compression
    "reasoning_size": {
        "compressed": 420,  # Tokens in snapshot
        "full": 3120        # Tokens in storage
    }
}
```

**Transferred tokens:** 200-700 (standard mode) vs. 600-3000 (full inline)

### **Full Reasoning (Stored Server-Side)**

```python
ReasoningMemory {
    "reasoning_id": "sha256:abc123def456...",
    "ai_id": "claude-sonnet-4.5",
    "task": "Security audit of authentication system",
    "conclusion": "Rotate JWT secret immediately",

    # Full reasoning chain (NOT transferred unless needed)
    "steps": [
        {
            "step": 1,
            "type": "observation",
            "content": "JWT secret stored in environment variable",
            "evidence": [
                "api/auth.py:23:const SECRET = process.env.JWT_SECRET",
                "env.example:12:JWT_SECRET=changeme"
            ],
            "confidence": 0.95
        },
        {
            "step": 2,
            "type": "inference",
            "reasoning_type": "deductive",
            "content": "Environment variables are logged in our system",
            "premises": ["All env vars logged for debugging (verified in config/logging.yaml:45)"],
            "conclusion": "JWT_SECRET appears in logs",
            "confidence": 0.90
        },
        {
            "step": 3,
            "type": "assumption",
            "content": "Logs are not encrypted",
            "needs_validation": true,
            "validation_method": "grep logs/ for 'encryption' or check log config"
        },
        # ... 7 more steps
    ],

    "dependencies": {
        2: [1],    # Step 2 depends on step 1
        4: [2, 3]  # Step 4 depends on steps 2 and 3
    },

    "known_limitations": [
        "Assumption unvalidated: Logs retained 30 days",
        "Assumption unvalidated: No log encryption"
    ]
}
```

**Storage:** Persistent DB, content-addressed by SHA256/CID

---

## 🚦 Fetch-on-Demand Workflow

### **Three Transfer Levels**

```python
class TransferLevel(Enum):
    MINIMAL = "minimal"     # 60-200 tokens
    STANDARD = "standard"   # 200-700 tokens
    FULL = "full"          # Pointer only (or inline 600-3000 tokens)

def to_context_prompt(snapshot, level: TransferLevel):
    if level == MINIMAL:
        return f"""
        CONTEXT: {snapshot.context_summary}
        CONCLUSION: {snapshot.conclusion}
        TAGS: {snapshot.reasoning_tags}
        TOP ASSUMPTIONS: {snapshot.top_assumptions}
        """

    elif level == STANDARD:
        return f"""
        {minimal_content}

        REASONING BRIEF: {snapshot.reasoning_brief}
        EVIDENCE: {snapshot.top_evidence_refs}
        FIDELITY: {snapshot.reasoning_fidelity}
        """

    elif level == FULL:
        # Don't inline! Return pointer
        return f"""
        {standard_content}

        FULL REASONING: Available via reasoning_ref={snapshot.reasoning_ref}
        Call: snapshot_provider.get_full_reasoning(reasoning_ref)
        """
```

### **Decision Logic: When to Fetch Full Graph**

```python
def should_fetch_full_reasoning(snapshot: EnhancedSnapshot) -> bool:
    """Heuristics for when to fetch full reasoning graph"""

    # High-risk domains always fetch
    if snapshot.domain in {"medical", "legal", "security"}:
        return True

    # High uncertainty needs full context
    if snapshot.vectors["UNCERTAINTY"] >= 0.5:
        return True

    # High impact needs validation
    if snapshot.vectors["IMPACT"] >= 0.7:
        return True

    # Low fidelity compression needs original
    if snapshot.reasoning_fidelity < 0.75:
        return True

    # Evidence points to critical changes
    if any("secret" in ref or "credential" in ref for ref in snapshot.evidence_refs):
        return True

    # Otherwise, compressed version is sufficient
    return False
```

### **Runtime Flow**

```python
# Recipient AI receives snapshot (STANDARD level - 200-700 tokens)
snapshot = receive_snapshot()

# Decide if full graph needed
if should_fetch_full_reasoning(snapshot):
    # Fetch from storage (content-addressed)
    full_reasoning = snapshot_provider.get_full_reasoning(snapshot.reasoning_ref)

    # Validate before using
    validation = ReasoningValidator().validate(full_reasoning)

    if not validation.passed:
        # Escalate to human or re-derive independently
        logger.warning(f"Reasoning validation failed: {validation.issues}")
        action = "human_review_required"
    else:
        # Safe to use full reasoning
        action = act_on_reasoning(full_reasoning)
else:
    # Compressed version sufficient for low-risk task
    action = act_on_reasoning(snapshot.reasoning_brief)
```

---

## 🗜️ Compression Strategies

### **1. Structured First (JSON)**

Capture as structured `ReasoningStep` objects (not prose). Structure compresses better and is machine-parsable.

```python
# ✅ Good: Structured
{
    "type": "inference",
    "reasoning_type": "deductive",
    "premises": ["JWT in env", "env logged"],
    "conclusion": "JWT in logs",
    "evidence_refs": ["api/auth.py:23"]
}

# ❌ Bad: Prose
"I noticed the JWT is in environment variables, and since our system logs all environment variables for debugging purposes, this means the JWT secret is likely present in our log files."
```

### **2. Hierarchical Summarization**

Group steps into blocks (observations → inferences → conclusions), summarize each block.

```python
{
    "observations_summary": "JWT secret in env vars, env vars logged",
    "inferences_summary": "Secret appears in logs, logs retained 30d unencrypted",
    "conclusion_summary": "Rotate secret immediately, move to vault long-term",
    "evidence_count": 7,
    "assumption_count": 2
}
```

### **3. Semantic Tags (Cheap Routing)**

```python
"reasoning_tags": [
    "jwt_secret_in_logs",    # What was found
    "rotate_secret",          # What to do
    "high_urgency",          # Priority
    "security_domain"        # Domain
]
```

### **4. Embedding Fingerprint**

Embed the reasoning summary for cheap similarity checks:

```python
"reasoning_embedding": embed_text(snapshot.reasoning_brief)
# 384-dim vector (MiniLM) or 1536-dim (OpenAI)

# Next AI can compute similarity without fetching
similarity = cosine_similarity(
    snapshot.reasoning_embedding,
    embed_text("my current task")
)

if similarity > 0.8:
    # Reasoning highly relevant, fetch full graph
    fetch_full = True
```

### **5. Delta Compression**

For repeated transfers, only send changes:

```python
{
    "reasoning_ref": "sha256:abc123...",  # Base version
    "reasoning_delta": {
        "steps_added": [10, 11],  # New steps since last transfer
        "assumptions_updated": {
            3: "Validated: logs encrypted since 2024-10"
        }
    }
}
```

---

## ✅ Verification & Reliability

### **Reasoning Fidelity Field**

```python
"reasoning_fidelity": 0.92  # 0.0-1.0, how much preserved in compression
```

Computed during compression:
- 1.0 = lossless (full graph transferred)
- 0.9+ = high fidelity (all critical inferences preserved)
- 0.75-0.9 = medium (key points preserved, details lost)
- <0.75 = low (significant loss, fetch full graph if acting)

### **Trust Gates (Thresholds)**

```python
MIN_FIDELITY_FOR_MINIMAL = 0.90
MIN_FIDELITY_FOR_STANDARD = 0.75
MAX_INFORMATION_LOSS_TOLERANCE = 0.15

# Force full graph fetch when:
force_full = (
    reasoning_fidelity < 0.75 or
    domain in {"medical", "legal", "security"} or
    vectors["IMPACT"] >= 0.7 or
    vectors["UNCERTAINTY"] >= 0.5 or
    any("secret" in ref for ref in evidence_refs)
)
```

### **ReasoningValidator**

```python
class ReasoningValidator:
    """Validate another AI's reasoning"""

    def validate(self, reasoning: ReasoningMemory) -> ValidationReport:
        report = ValidationReport()

        # Check assumptions
        for step in reasoning.steps:
            for assumption in step.assumptions:
                if not self.verify_assumption(assumption):
                    report.add_issue(f"Invalid: {assumption}")

        # Verify evidence exists
        for step in reasoning.steps:
            for evidence_ref in step.evidence:
                if not self.file_exists_at_line(evidence_ref):
                    report.add_issue(f"Evidence not found: {evidence_ref}")

        # Check logical soundness
        for step_num, deps in reasoning.dependencies.items():
            if not self.check_inference(reasoning.steps[step_num], deps):
                report.add_issue(f"Step {step_num}: invalid inference")

        return report
```

---

## 📦 Data Structures

### **Core Classes**

```python
@dataclass
class ReasoningStep:
    step_number: int
    type: str  # observation, inference, assumption, hypothesis, conclusion
    content: str
    reasoning_type: str  # deductive, inductive, abductive, analogical

    # Evidence & support
    evidence: List[str] = field(default_factory=list)
    premises: List[str] = field(default_factory=list)

    # Metadata
    alternatives_considered: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    confidence: float = 1.0

@dataclass
class ReasoningMemory:
    reasoning_id: str  # Content-addressed (SHA256)
    ai_id: str
    task: str
    conclusion: str

    # The reasoning chain
    steps: List[ReasoningStep]
    dependencies: Dict[int, List[int]]  # Step N depends on steps [X, Y]

    # Meta
    reasoning_strategy: str  # top-down, bottom-up, hypothesis-driven
    confidence_in_reasoning: float
    known_limitations: List[str]

@dataclass
class EnhancedEpistemicSnapshot:
    # Existing fields
    snapshot_id: str
    session_id: str
    vectors: Dict[str, float]
    context_summary: ContextSummary

    # Compressed reasoning (TRANSFERRED)
    reasoning_brief: str  # 3-6 sentences
    reasoning_tags: List[str]
    top_assumptions: List[str]
    reasoning_embedding: List[float]

    # Pointer to full graph (NOT transferred)
    reasoning_ref: str  # SHA256 or CID
    reasoning_fidelity: float
    reasoning_size: Dict[str, int]  # {"compressed": 420, "full": 3120}
```

---

## 🛡️ Security & Integrity

### **Content Addressing**

```python
def compute_reasoning_ref(reasoning: ReasoningMemory) -> str:
    """Content-addressed reference (like Git)"""
    canonical_json = json.dumps(
        reasoning.to_dict(),
        sort_keys=True,
        ensure_ascii=True
    )
    return f"sha256:{hashlib.sha256(canonical_json.encode()).hexdigest()}"
```

### **Evidence Hashes**

```python
"evidence": [
    "api/auth.py:23:sha256:abc123def456"  # File path + line + file hash
]
# Can detect if evidence file changed since reasoning
```

### **Provenance Signing**

```python
{
    "reasoning_ref": "sha256:abc123...",
    "signature": "ed25519:...",  # Signed by AI's ephemeral key
    "ai_id": "claude-sonnet-4.5",
    "timestamp": "2025-11-04T12:34:56Z"
}
```

---

## 📋 Implementation Plan (Staged)

### **Phase A - Schema + Storage (1-2 days)**

- [ ] Define `ReasoningStep` and `ReasoningMemory` dataclasses
- [ ] Add reasoning storage table to snapshot DB
- [ ] Implement content-addressed storage (SHA256 refs)
- [ ] Add `reasoning_ref` field to `EpistemicSnapshot`

### **Phase B - Compression (1-2 days)**

- [ ] Implement LLM-based summarizer: `ReasoningMemory` → `reasoning_brief`
- [ ] Extract semantic tags from reasoning
- [ ] Compute reasoning embeddings
- [ ] Measure fidelity (automated or human eval)

### **Phase C - Fetch API (1-2 days)**

- [ ] `snapshot_provider.get_full_reasoning(reasoning_ref)`
- [ ] `snapshot.to_context_prompt(level)` with minimal/standard/full
- [ ] Implement fetch-on-demand in modality switcher

### **Phase D - Validation (2-4 days)**

- [ ] `ReasoningValidator`: evidence checks, assumption validation
- [ ] Implement trust gates (UNCERTAINTY/IMPACT/domain)
- [ ] Add independent verification before acting

### **Phase E - Dashboard (1-2 days)**

- [ ] Visualize reasoning_fidelity in dashboard
- [ ] "Explain" button → fetch full graph with evidence links
- [ ] Show validation reports

---

## 💡 Integration with Existing Features

### **MiniMax M2 Thinking Blocks**

MiniMax M2 already outputs thinking blocks! Extract to reasoning memory:

```python
def extract_reasoning_from_minimax(response):
    """Convert MiniMax thinking blocks to ReasoningMemory"""

    reasoning = ReasoningMemory(...)

    # Parse thinking block
    steps = parse_thinking_process(response["thinking"])

    for step_text in steps:
        step = ReasoningStep(
            type=classify_step_type(step_text),
            content=step_text,
            reasoning_type=infer_reasoning_type(step_text)
        )
        reasoning.steps.append(step)

    return reasoning
```

### **Epistemic Snapshots**

Already have 95% compression (10k → 500 tokens). Add reasoning compression on top:

```
Context compression: 10,000 → 500 tokens (95%)
Reasoning compression: 3,000 → 400 tokens (87%)
Total snapshot: ~900 tokens (still good!)
```

---

## 🎯 Success Metrics

### **Token Efficiency**

- Target: <700 tokens for standard transfer (vs. 3000+ for full graph)
- Measure: Average tokens per snapshot across 100 transfers

### **Fidelity**

- Target: >0.90 fidelity for minimal in low-risk contexts
- Measure: Human eval of compressed vs. full reasoning (N=50 samples)

### **Verification Coverage**

- Target: >80% of critical inferences validatable from compressed version
- Measure: `ReasoningValidator` can verify without fetching full graph

---

## 🚨 Critical Considerations

### **When NOT to Use Reasoning Memory**

- Simple tasks (no complex reasoning)
- High token budgets (just transfer full)
- Real-time systems (fetch latency unacceptable)
- Low-stakes contexts (not worth overhead)

### **When ESSENTIAL**

- Security/medical/legal domains (validation critical)
- Multi-hop reasoning (building on previous AI's work)
- High-cost scenarios (token savings matter)
- Explainability requirements (audit trail needed)

---

## 📚 References

**GPT-5's Recommendations (Q3 2025):**
- Split storage architecture (compressed transfer + full graph in DB)
- Token economics (80-200 for brief, 600-3000 for full)
- Fetch-on-demand based on risk heuristics
- Structured compression beats prose
- Independent verification before acting

**Related Empirica Docs:**
- `EMPIRICA_VISION.md` - Cognitive orchestration (Phase 6+)
- `docs/reference/ARCHITECTURE_MAP.md` - Epistemic snapshot protocol
- `LIBTMUX_INTEGRATION.md` - Tmux orchestration for parallel execution

---

**Status:** Vision document (not yet implemented)
**Priority:** Phase 6C+ (after cognitive orchestration foundation)
**ROI:** High (enables reliable multi-AI reasoning), but complex
**Risk:** Token overhead if not compressed properly

---

*Vision captured: 2025-11-04 (Q3/Q4)*
*Credit: GPT-5's architectural recommendations*
*Next step: Focus on current work (tmux integration, Phase 5 completion)*
