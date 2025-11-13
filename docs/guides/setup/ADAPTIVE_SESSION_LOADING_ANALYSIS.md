# Adaptive Session Loading - Risk Analysis & Architecture Design

## Executive Summary

**Goal:** Use epistemic vectors and meta-uncertainty to intelligently determine which historical sessions to load into new Claude sessions.

**Current State:** We have a rich relational database storing 13D epistemic vectors, but no semantic search or pattern matching capabilities.

**Critical Question:** Can we achieve genuine session continuity without adding vector embeddings?

---

## 1. CURRENT DATA STORAGE AUDIT

### What We Store (SQLite)

#### Session-Level Data
```sql
sessions
├── session_id, ai_id, user_id
├── start_time, end_time
├── bootstrap_level, components_loaded
├── total_turns, total_cascades
├── avg_confidence
└── drift_detected
```

#### Cascade-Level Data (Task Execution)
```sql
cascades
├── cascade_id, session_id, task (TEXT)
├── context_json (TEXT - unstructured)
├── 7 phase completion flags (PREFLIGHT→POSTFLIGHT)
├── final_action, final_confidence
├── investigation_rounds
├── epistemic_delta (JSON)
└── timing data
```

#### Epistemic Assessments (The Gold Mine)
```sql
epistemic_assessments (12D vectors per phase)
├── Foundation: know, do, context
├── Comprehension: clarity, coherence, signal, density
├── Execution: state, change, completion, impact
├── Aggregate: overall_confidence, recommended_action
└── Rationales for each dimension (TEXT)

preflight_assessments (13D vector - initial state)
├── All 13 dimensions measured BEFORE task
├── Initial uncertainty notes
└── Timestamp

postflight_assessments (13D vector - learned state)
├── All 13 dimensions measured AFTER task
├── postflight_actual_confidence
├── calibration_accuracy (well_calibrated|overconfident|underconfident)
├── learning_notes (TEXT - what was learned)
└── Epistemic delta (PREFLIGHT - POSTFLIGHT)
```

#### Supporting Tables
```sql
investigation_tools
├── tool_name, tool_purpose, target_vector
├── success, confidence_gain
└── information_gained (TEXT)

divergence_tracking (delegate vs trustee tension)
drift_monitoring (sycophancy detection)
bayesian_beliefs (evidence-based belief updates)
```

### What We DON'T Store

❌ **Task embeddings** - Cannot semantically search "fix authentication bug" vs "debug auth issue"  
❌ **Learning pattern vectors** - No encoded representation of "what kind of learning happened"  
❌ **Contextual similarity** - No way to match "working on frontend" vs "React component bug"  
❌ **Epistemic trajectory embeddings** - Can't find "sessions where uncertainty→0.8 became confidence→0.9"  
❌ **Cross-session patterns** - No clustering of similar learning experiences  

### Data Volume Projection

**Per Session:**
- Base metadata: ~500 bytes
- Per cascade (assume 5/session): ~2KB each = 10KB
- Per assessment (7 phases × 5 cascades): ~1KB each = 35KB
- Tools/divergence/beliefs: ~5KB
- **Total: ~50KB per session**

**100 Sessions = 5MB** (manageable)  
**1,000 Sessions = 50MB** (SQLite handles fine)  
**10,000 Sessions = 500MB** (starts to slow down without indexing)  

---

## 2. POTENTIAL PROBLEMS & FAILURE MODES

### Problem 1: **Semantic Mismatch**
**Scenario:** Claude asks "How do I fix the authentication bug?"  
**What happens:**
- SQL query: `WHERE task LIKE '%auth%'` → might miss "login issue" or "session management"
- No way to know that "refactoring user service" involved similar epistemic challenges
- **Result:** Load irrelevant sessions, miss relevant ones

**Severity:** 🔴 HIGH - Defeats the purpose of adaptive loading

---

### Problem 2: **Epistemic Pattern Blindness**
**Scenario:** Current task has `uncertainty=0.7, meta=0.3, know=0.4`  
**What we want:** Find sessions where AI started with similar confusion and successfully reduced it  
**What SQL can do:**
```sql
SELECT * FROM sessions WHERE 
  preflight.uncertainty BETWEEN 0.65 AND 0.75
  AND postflight.uncertainty < 0.4  -- learned something!
```

**What SQL CANNOT do:**
- Find sessions with similar *epistemic trajectories* (multi-dimensional pattern)
- Cluster sessions by "type of confusion" (e.g., technical vs conceptual)
- Match "shape" of uncertainty reduction curve
- Identify sessions where meta-uncertainty specifically decreased

**Severity:** 🟡 MEDIUM - Can work around with heuristics, but loses sophistication

---

### Problem 3: **Context Pollution**
**Scenario:** Load 5 sessions with high epistemic deltas, but they're all from different projects  
**What happens:**
- Claude gets confused: "Wait, am I working on authentication, database schema, OR frontend?"
- Mixed contexts dilute focus
- Calibration suffers because learned patterns don't transfer

**Severity:** 🔴 HIGH - Could make things worse than loading nothing

---

### Problem 4: **Recency Bias vs Relevance Tradeoff**
**Scenario:** Most recent session had low learning (delta ~0.1), but session from 2 weeks ago had massive learning (delta ~0.6)  
**What SQL chooses:** Recent session (because timestamp sort)  
**What we want:** Relevant session (because learning magnitude)

**Mitigation:** Scoring function combining recency + relevance  
**Problem:** How to weight them? 70/30? 50/50? Depends on task!

**Severity:** 🟡 MEDIUM - Solvable with tuning, but not adaptive

---

### Problem 5: **Cold Start Problem**
**Scenario:** New AI agent, no historical sessions  
**What happens:** No data to learn from  
**Mitigation:** Bootstrap from human-provided examples or default to "load nothing"

**Severity:** 🟢 LOW - Expected behavior

---

### Problem 6: **Feedback Loop Amplification**
**Scenario:** AI loads sessions where it was overconfident, learns to be more overconfident  
**What happens:** Calibration drift accumulates over time

**Critical Safeguard Needed:**
- **ONLY load well-calibrated sessions** (`calibration_accuracy = 'well_calibrated'`)
- Track "calibration health" as a meta-metric
- Alert if cumulative drift > threshold

**Severity:** 🔴 CRITICAL - Could corrupt the entire system

---

### Problem 7: **SQL Performance at Scale**
**Current query for relevance scoring:**
```sql
SELECT s.session_id,
  (SELECT AVG(epistemic_humility) FROM preflight_assessments WHERE session_id = s.session_id) as avg_pre_hum,
  (SELECT AVG(epistemic_humility) FROM postflight_assessments WHERE session_id = s.session_id) as avg_post_hum,
  -- ... 13 more dimensions × 2 (pre/post)
FROM sessions s
WHERE s.ai_id = 'claude'
ORDER BY some_complex_scoring_function()
LIMIT 5
```

**At 1,000 sessions:** 26 subqueries × 1,000 rows = **26,000 subquery executions**

**Mitigation:**
- Denormalize into `session_summaries` table
- Pre-compute scores during POSTFLIGHT
- Index on scoring components

**Severity:** 🟡 MEDIUM - Solvable with DB optimization, but adds complexity

---

### Problem 8: **Token Budget Explosion**
**Scenario:** Load 5 sessions × 50KB each = 250KB of JSON  
**In tokens:** ~60,000 tokens just for history  
**Claude's context:** ~200,000 tokens total  
**Result:** 30% of context used for history, 70% for actual work

**Mitigation:**
- Hierarchical summarization (session → cascade → assessment)
- Load only delta + key rationales, not full data
- Adaptive detail level based on relevance score

**Severity:** 🟡 MEDIUM - Manageable with smart summarization

---

## 3. WHEN DO WE NEED VECTOR EMBEDDINGS?

### Use Cases Where SQL FAILS

❌ **Semantic task similarity**
- "Debug authentication" ≈ "Fix login issue" ≈ "Resolve session management"
- Requires: Text embeddings (OpenAI, Sentence-BERT)

❌ **Epistemic pattern matching**
- Find sessions with similar multi-dimensional confusion→clarity trajectories
- Requires: 13D vector embeddings of (PREFLIGHT, POSTFLIGHT, DELTA) states

❌ **Cross-project learning transfer**
- "This frontend bug feels like that backend bug I fixed last week"
- Requires: Context embeddings + similarity search

❌ **Anomaly detection**
- "This session's epistemic trajectory is unlike anything I've seen"
- Requires: Clustering + outlier detection (HDBSCAN, Isolation Forest)

### Use Cases Where SQL WORKS

✅ **Exact match queries**
- "Load all sessions for project X"
- "Load all sessions where I was well-calibrated"

✅ **Range-based filtering**
- "Load sessions where preflight uncertainty > 0.7"
- "Load sessions with large know delta (> +0.3)"

✅ **Aggregate statistics**
- "What was my average confidence last week?"
- "How often did I trigger investigation phase?"

✅ **Temporal patterns**
- "Load my last 3 sessions"
- "Load sessions from this week"

---

## 4. ARCHITECTURAL OPTIONS

### Option A: **Pure SQL** (Minimal Complexity)

**Approach:**
```python
def suggest_sessions(current_preflight, ai_id):
    # Step 1: Filter by calibration quality
    well_calibrated = query("calibration_accuracy = 'well_calibrated'")
    
    # Step 2: Range-based epistemic matching
    similar_uncertainty = query(f"preflight.uncertainty BETWEEN {u-0.1} AND {u+0.1}")
    
    # Step 3: Score by learning magnitude
    high_learning = query("epistemic_delta_sum > 0.5")  # Pre-computed
    
    # Step 4: Combine with recency
    score = (recency_weight * days_ago) + (learning_weight * delta_sum)
    
    # Step 5: Return top N
    return sessions.order_by(score).limit(N)
```

**Pros:**
✅ Simple, no external dependencies  
✅ Fast (with proper indexing)  
✅ Easy to debug  
✅ Works for 80% of cases  

**Cons:**
❌ No semantic understanding  
❌ No multi-dimensional pattern matching  
❌ Brittle to task phrasing  

**Best for:** MVP, small-scale deployments, single-project workflows

---

### Option B: **Hybrid (SQL + Qdrant)** (Balanced)

**Approach:**
1. **SQL for filtering** (calibration, recency, project scope)
2. **Qdrant for ranking** (semantic + epistemic similarity)

```python
# Step 1: SQL pre-filter (reduce from 1000 → 100 sessions)
candidates = db.query("""
    SELECT session_id, task, epistemic_delta
    FROM sessions
    WHERE ai_id = ? 
      AND calibration_accuracy = 'well_calibrated'
      AND start_time > DATE('now', '-30 days')
    ORDER BY start_time DESC
    LIMIT 100
""", ai_id)

# Step 2: Embed current task + epistemic state
current_embedding = embed({
    'task': current_task,
    'preflight': current_preflight,
    'context': current_context
})

# Step 3: Qdrant similarity search
results = qdrant.search(
    collection="empirica_sessions",
    query_vector=current_embedding,
    limit=5,
    filter={"session_id": {"$in": [c['session_id'] for c in candidates]}}
)

return results
```

**Pros:**
✅ Best of both worlds  
✅ SQL handles structure, Qdrant handles semantics  
✅ Can scale to 10,000+ sessions  
✅ Enables pattern discovery  

**Cons:**
⚠️ Added complexity (two databases)  
⚠️ Requires embedding generation (API cost or local model)  
⚠️ Sync challenges (keep SQL + Qdrant in sync)  

**Best for:** Production deployments, multi-project workflows, research

---

### Option C: **Qdrant-First** (Maximum Capability)

**Approach:**
- Store everything in Qdrant with rich metadata
- Use SQL only for human-readable exports

**Pros:**
✅ Unified storage  
✅ Full semantic search  
✅ Advanced clustering/anomaly detection  

**Cons:**
❌ High complexity  
❌ Harder to debug  
❌ SQL skills don't transfer  
❌ Vendor lock-in  

**Best for:** Large-scale deployments, research platforms

---

## 5. RECOMMENDED ARCHITECTURE

### **Phase 1: Pure SQL MVP** (Current Implementation)

**Goal:** Prove the concept works without over-engineering

**Algorithm:**
```python
def adaptive_session_load(current_preflight, ai_id, max_sessions=5):
    # Calculate epistemic need
    need_score = calculate_need(current_preflight)
    
    # Determine load strategy
    if need_score > 0.7:
        strategy = "deep"  # Load 5 sessions
    elif need_score > 0.5:
        strategy = "moderate"  # Load 3 sessions
    elif need_score > 0.3:
        strategy = "light"  # Load 1 session
    else:
        strategy = "summary"  # Load task list only
    
    # Query sessions
    sessions = db.query("""
        WITH session_scores AS (
            SELECT 
                s.session_id,
                s.task,
                -- Calibration filter (CRITICAL)
                CASE WHEN pf.calibration_accuracy = 'well_calibrated' THEN 1.0 ELSE 0.3 END as calib_mult,
                -- Learning magnitude
                (pf.epistemic_humility - pr.epistemic_humility + 
                 pf.metacognitive_awareness - pr.metacognitive_awareness) as learning_score,
                -- Recency
                julianday('now') - julianday(s.start_time) as days_ago
            FROM sessions s
            JOIN preflight_assessments pr ON s.session_id = pr.session_id
            JOIN postflight_assessments pf ON s.session_id = pf.session_id
            WHERE s.ai_id = ?
              AND pf.calibration_accuracy IS NOT NULL  -- Must have completed
        )
        SELECT session_id, task,
               (learning_score * 0.5 + (1.0 / (1.0 + days_ago * 0.1)) * 0.3) * calib_mult as final_score
        FROM session_scores
        ORDER BY final_score DESC
        LIMIT ?
    """, ai_id, max_sessions)
    
    return sessions
```

**Pre-computed Optimization:**
- Add `session_summaries` table
- Compute scores during POSTFLIGHT
- Index on score components

**Safeguards:**
1. ✅ **Calibration filter** - Only load well-calibrated sessions
2. ✅ **Recency decay** - Prefer recent, but don't ignore old high-value
3. ✅ **Learning magnitude** - Prioritize sessions with actual learning
4. ✅ **Token budget** - Adaptive detail level

---

### **Phase 2: Add Qdrant (If Needed)**

**Triggers for Phase 2:**
- User reports "It's not finding relevant sessions"
- Working across >3 projects with different contexts
- Session count > 1,000
- Need pattern discovery (clustering)

**What to embed:**
```python
session_vector = {
    'task_embedding': embed_text(task),  # Semantic
    'preflight_vector': [13 dimensions],  # Epistemic state
    'postflight_vector': [13 dimensions],  # Learned state
    'delta_vector': [13 dimensions],  # Learning magnitude
    'context_embedding': embed_text(context),  # Project/domain
}
```

**Qdrant Schema:**
```python
qdrant.create_collection(
    collection_name="empirica_sessions",
    vectors_config={
        "task": {"size": 384, "distance": "Cosine"},  # Sentence-BERT
        "epistemic_state": {"size": 13, "distance": "Euclidean"},
        "epistemic_delta": {"size": 13, "distance": "Euclidean"},
    },
    payload_index=["calibration_accuracy", "ai_id", "start_time"]
)
```

---

## 6. CRITICAL SAFEGUARDS

### 🔒 **Calibration Filter** (MANDATORY)
```python
# ALWAYS filter out poorly calibrated sessions
WHERE calibration_accuracy IN ('well_calibrated', 'slightly_overconfident')
  AND calibration_accuracy != 'severely_underconfident'
```

### 🔒 **Feedback Loop Detection**
```python
# Track cumulative calibration drift
if abs(current_avg_calib - historical_avg_calib) > 0.15:
    alert("Calibration drift detected! Review loaded sessions.")
```

### 🔒 **Context Coherence Check**
```python
# Don't mix unrelated projects
if len(set(session['project'] for session in loaded)) > 2:
    warn("Loading from multiple projects - may cause confusion")
```

### 🔒 **Token Budget Management**
```python
# Adaptive summarization
if total_tokens > 50000:
    load_mode = "ultra_compressed"  # Only deltas + key rationales
elif total_tokens > 20000:
    load_mode = "compressed"  # Summaries + important assessments
else:
    load_mode = "detailed"  # Full context
```

---

## 7. DECISION MATRIX

| Factor | Pure SQL | Hybrid (SQL + Qdrant) | Qdrant-First |
|--------|----------|----------------------|--------------|
| **Implementation Complexity** | ⭐ Simple | ⭐⭐ Moderate | ⭐⭐⭐ Complex |
| **Semantic Search** | ❌ No | ✅ Yes | ✅ Yes |
| **Epistemic Pattern Matching** | ⚠️ Basic | ✅ Advanced | ✅ Advanced |
| **Scalability (10K+ sessions)** | ⚠️ Slow | ✅ Fast | ✅ Fast |
| **Debuggability** | ✅ Easy | ⚠️ Moderate | ❌ Hard |
| **External Dependencies** | ✅ None | ⚠️ Qdrant | ⚠️ Qdrant |
| **Cost** | ✅ Free | ⚠️ Embedding API | ⚠️ Embedding API |
| **Time to MVP** | ✅ 1 day | ⚠️ 3-5 days | ❌ 1-2 weeks |

---

## 8. RECOMMENDED IMPLEMENTATION PLAN

### **Immediate (Today)**
1. ✅ Implement Pure SQL version
2. ✅ Add `session_summaries` table for pre-computed scores
3. ✅ Test with existing 6 sessions
4. ✅ Validate calibration filtering works

### **Short-term (This Week)**
1. Build scoring function based on epistemic need
2. Add hierarchical summarization (detail levels)
3. Implement token budget management
4. Write unit tests for edge cases

### **Medium-term (This Month)**
1. Collect real usage data (100+ sessions)
2. Analyze: Are we missing relevant sessions?
3. Measure: Is context pollution happening?
4. Decide: Do we need Qdrant?

### **Long-term (If Needed)**
1. Add Qdrant for semantic search
2. Embed task descriptions + epistemic states
3. Build pattern discovery tools
4. Implement anomaly detection

---

## 9. OPEN QUESTIONS FOR USER

1. **Token Budget:** How much of Claude's context should we dedicate to history? (Suggest: 20% = ~40K tokens)

2. **Calibration Strictness:** Should we ONLY load `well_calibrated` sessions, or allow `slightly_overconfident`?

3. **Multi-Project:** Should we auto-detect project boundaries, or let user specify?

4. **Embedding Cost:** If we go to Qdrant, use OpenAI API (~$0.0001/session) or local Sentence-BERT (free but slower)?

5. **Success Metrics:** How do we measure if this is working?
   - "Sessions loaded felt relevant" (subjective)
   - "Preflight uncertainty reduced faster" (measurable)
   - "Calibration improved over time" (measurable)

---

## 10. FINAL RECOMMENDATION

**START WITH PURE SQL.**

**Why:**
- We only have 6 sessions currently
- Semantic search is overkill for <100 sessions
- SQL gives us debuggability and transparency
- We can always add Qdrant later without throwing away work (SQL becomes the pre-filter)

**Critical Success Factors:**
1. ✅ Calibration filtering (prevent bad data from polluting)
2. ✅ Token budget management (don't overwhelm Claude)
3. ✅ Epistemic need scoring (adaptive loading)
4. ✅ Feedback loop monitoring (detect drift)

**When to Revisit:**
- Sessions > 100 (semantic search becomes valuable)
- Multi-project workflows (context isolation needed)
- Pattern discovery requests (clustering/anomaly detection)

---

**Should we proceed with Pure SQL implementation?**
