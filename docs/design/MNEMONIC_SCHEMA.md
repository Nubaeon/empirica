# Mnemonic Schema: Eidetic & Episodic Memory Architecture

## Overview

Two-layer memory system for Empirica that serves:
- **Claude Code** (main AI) - context during project-bootstrap, project-search
- **Epistemic Agents** (Scout, Search, FactScorer) - investigation queries
- **External Interfaces** (Discord, Web chat) - response grounding

## Cognitive Memory Types

### Eidetic Memory (What)
Stable, fact-based, declarative knowledge. Timeless truths that persist.

**Characteristics:**
- Facts, patterns, code signatures, API behaviors
- Low decay - knowledge confirmed across sessions increases confidence
- Cross-session: same fact validated multiple times → higher confidence
- Example: "JWT tokens are stored in httpOnly cookies in this codebase"

**Schema:**
```python
EideticEntry = {
    "id": str,                    # UUID
    "type": "fact" | "pattern" | "signature" | "behavior" | "constraint",
    "content": str,               # The knowledge itself
    "content_hash": str,          # For deduplication
    "domain": str,                # Code domain (auth, api, db, etc.)
    "confidence": float,          # 0.0-1.0, increases with confirmation
    "confirmation_count": int,    # How many sessions validated this
    "first_seen": timestamp,
    "last_confirmed": timestamp,
    "source_sessions": list[str], # Sessions that contributed
    "source_findings": list[str], # Finding IDs that support this
    "tags": list[str],
    "vector": list[float],        # Embedding
}
```

**Confidence Evolution:**
```
Initial: 0.5 (first observation)
+0.1 per confirmation from different session
+0.05 per confirmation from same session
Max: 0.95 (never 1.0 - always room for revision)
Decay: -0.01 per month without confirmation
```

### Episodic Memory (When/How)
Contextual, narrative, autobiographical. Stories of how we solved things.

**Characteristics:**
- Session narratives, decision contexts, learning arcs
- Higher decay - recent episodes more relevant than old
- Rich context: who, what, when, why, how
- Example: "In session fc851d91, we debugged the Discord bot auth issue by..."

**Schema:**
```python
EpisodicEntry = {
    "id": str,                    # UUID
    "type": "session_arc" | "decision" | "investigation" | "discovery" | "mistake",
    "narrative": str,             # The story/context
    "session_id": str,
    "ai_id": str,                 # Which AI experienced this
    "goal_id": str | None,
    "timestamp": timestamp,
    "duration_minutes": int,
    "emotional_valence": float,   # -1.0 (frustration) to 1.0 (satisfaction)
    "learning_delta": {           # PREFLIGHT → POSTFLIGHT
        "know": float,
        "uncertainty": float,
        "context": float,
    },
    "actors": list[str],          # AI IDs, human, external systems
    "key_moments": list[str],     # Critical decision points
    "outcome": "success" | "partial" | "failure" | "abandoned",
    "tags": list[str],
    "recency_weight": float,      # Decays over time
    "vector": list[float],
}
```

**Recency Decay:**
```
Initial: 1.0
After 1 day: 0.95
After 1 week: 0.80
After 1 month: 0.50
After 3 months: 0.25
After 1 year: 0.10
Minimum: 0.05 (never fully forgotten)
```

## Collection Structure

### New Qdrant Collections

```
project_{id}_eidetic     # Stable facts (cross-session)
project_{id}_episodic    # Session narratives (time-decayed)
global_eidetic           # Cross-project facts (high-confidence only)
```

### Migration from Current

| Current | New | Notes |
|---------|-----|-------|
| `project_{id}_memory` | Split into eidetic + episodic | Findings → eidetic, session context → episodic |
| `project_{id}_epistemics` | Merge into episodic | Learning trajectories are episodes |
| `global_learnings` | Becomes `global_eidetic` | Only high-confidence facts |

## Query Patterns

### For Claude Code (project-bootstrap)

```python
def load_context(session_id, task_description):
    # 1. Get relevant eidetic facts (stable knowledge)
    eidetic = search_eidetic(
        query=task_description,
        min_confidence=0.6,
        limit=10
    )

    # 2. Get recent episodic context (what we've been doing)
    episodic = search_episodic(
        query=task_description,
        recency_weight=0.7,  # Prioritize recent
        limit=5
    )

    # 3. Merge and format
    return format_context(eidetic, episodic)
```

### For Search Agent

```python
def epistemic_search(query, session_id):
    # Search both layers
    facts = search_eidetic(query, min_confidence=0.5)
    stories = search_episodic(query, include_failures=True)

    return {
        "facts": facts,           # What we know
        "stories": stories,       # How we learned it
        "confidence": aggregate_confidence(facts),
    }
```

### For FactScorer Agent

```python
def verify_claim(claim):
    # Check eidetic memory for supporting facts
    supporting = search_eidetic(claim, similarity_threshold=0.8)

    if not supporting:
        return {"verified": False, "reason": "no_eidetic_support"}

    avg_confidence = mean([f.confidence for f in supporting])

    return {
        "verified": avg_confidence > 0.7,
        "confidence": avg_confidence,
        "sources": [f.id for f in supporting],
    }
```

## Ingestion Pipeline

### Finding → Eidetic

```python
def ingest_finding(finding):
    # Extract factual content
    fact = extract_fact(finding.content)

    # Check for existing similar fact
    existing = find_similar_eidetic(fact, threshold=0.9)

    if existing:
        # Confirm existing fact
        existing.confirmation_count += 1
        existing.confidence = min(0.95, existing.confidence + 0.1)
        existing.last_confirmed = now()
        existing.source_sessions.append(finding.session_id)
        update_eidetic(existing)
    else:
        # Create new eidetic entry
        create_eidetic(EideticEntry(
            type="fact",
            content=fact,
            confidence=0.5,
            confirmation_count=1,
            source_sessions=[finding.session_id],
            source_findings=[finding.id],
        ))
```

### Session → Episodic

```python
def ingest_session_arc(session):
    # Get PREFLIGHT → POSTFLIGHT delta
    preflight = get_preflight(session.id)
    postflight = get_postflight(session.id)

    if not preflight or not postflight:
        return  # Incomplete session

    # Calculate learning delta
    delta = calculate_delta(preflight.vectors, postflight.vectors)

    # Generate narrative from session breadcrumbs
    narrative = generate_narrative(
        findings=get_session_findings(session.id),
        unknowns=get_session_unknowns(session.id),
        delta=delta,
    )

    create_episodic(EpisodicEntry(
        type="session_arc",
        narrative=narrative,
        session_id=session.id,
        ai_id=session.ai_id,
        learning_delta=delta,
        outcome=determine_outcome(delta),
        recency_weight=1.0,
    ))
```

## Semantic Compression

### Eidetic Merging
When multiple facts are highly similar (>0.95 similarity), merge:

```python
def merge_eidetic(facts: list[EideticEntry]) -> EideticEntry:
    # Take highest confidence as base
    base = max(facts, key=lambda f: f.confidence)

    # Aggregate confirmations
    base.confirmation_count = sum(f.confirmation_count for f in facts)
    base.source_sessions = list(set(flatten([f.source_sessions for f in facts])))
    base.confidence = min(0.95, base.confidence + 0.05 * len(facts))

    # Delete merged
    for f in facts:
        if f.id != base.id:
            delete_eidetic(f.id)

    return base
```

### Episodic Summarization
When episodic entries exceed threshold, summarize old episodes:

```python
def summarize_old_episodes(project_id, max_episodes=1000):
    episodes = get_all_episodic(project_id, order_by="timestamp")

    if len(episodes) <= max_episodes:
        return

    # Group old episodes by month
    old_episodes = episodes[:-max_episodes]
    by_month = group_by_month(old_episodes)

    for month, eps in by_month.items():
        # Create summary episode
        summary = create_episodic(EpisodicEntry(
            type="summary",
            narrative=summarize_episodes(eps),
            recency_weight=0.1,  # Old summary
        ))

        # Delete originals
        for ep in eps:
            delete_episodic(ep.id)
```

## Integration Points

### 1. project-bootstrap (CLI)
Loads both eidetic and episodic context for session start.

### 2. project-search (CLI)
Searches both layers with configurable weights.

### 3. Search Agent
Primary consumer - queries both layers for investigation.

### 4. FactScorer Agent
Queries eidetic layer for claim verification.

### 5. Handoff Generation
Extracts key eidetic facts and episodic arc for next session.

### 6. Post-POSTFLIGHT Hook
Triggers episodic ingestion after session completion.

### 7. Finding Log Hook
Triggers eidetic ingestion after finding creation.

## Implementation Priority

1. **Schema definition** - Create dataclasses and Qdrant payloads
2. **Eidetic ingestion** - Wire finding-log to eidetic creation
3. **Episodic ingestion** - Wire postflight to episodic creation
4. **Search functions** - Update project-search to query both layers
5. **Agent integration** - Wire Search and FactScorer to new schema
6. **Decay/merge jobs** - Background tasks for maintenance
7. **Migration** - Convert existing memory to new schema

## Open Questions

1. Should we store embeddings in SQLite as backup, or Qdrant-only?
2. How to handle cross-project eidetic facts (global_eidetic)?
3. Should episodic narratives be LLM-generated or template-based?
4. Decay constants - need calibration from real usage data
