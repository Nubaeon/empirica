# Memory Retrieval Triggers

## Design Principle

Memory retrieval should be **automatic based on epistemic state**, not manual.
When uncertainty is high, surface relevant knowledge without being asked.

## Trigger Points

### 1. SessionStart (Post-Compact)

**When:** After memory compaction, new session, or resume
**Query:** Active goals → related eidetic facts + episodic work
**Inject:** Into SessionStart hook additionalContext

```python
def post_compact_memory_load(session_id):
    goals = get_active_goals(session_id)

    context = []
    for goal in goals[:3]:  # Top 3 active goals
        facts = search_eidetic(goal.objective, limit=5)
        episodes = search_episodic(goal.objective, limit=2)

        if facts or episodes:
            context.append({
                "goal": goal.objective,
                "relevant_facts": [f.content for f in facts],
                "past_work": [e.narrative[:200] for e in episodes],
            })

    return context
```

### 2. Pre-CHECK Gate

**When:** Before submitting CHECK assessment
**Query:** Action description → similar decisions, mistakes, dead ends
**Inject:** Into CHECK response as memory_context field

```python
def pre_check_memory(action_description, session_id):
    # What have we tried before?
    similar = search_episodic(
        query=action_description,
        types=["decision", "investigation"],
        limit=3
    )

    # What mistakes to avoid?
    mistakes = search_eidetic(
        query=action_description,
        type="mistake",
        min_confidence=0.5
    )

    # What dead ends to avoid?
    dead_ends = search_eidetic(
        query=action_description,
        type="dead_end",
        limit=3
    )

    return {
        "similar_past_work": similar,
        "mistakes_to_avoid": mistakes,
        "dead_ends_to_avoid": dead_ends,
    }
```

### 3. Pre-Unknown-Log

**When:** Before logging a new unknown
**Query:** Unknown text → similar resolved unknowns
**Inject:** Warning if similar was resolved

```python
def check_resolved_unknowns(unknown_text):
    resolved = search_eidetic(
        query=unknown_text,
        type="resolved_unknown",
        similarity_threshold=0.85
    )

    if resolved:
        best = resolved[0]
        return {
            "already_resolved": True,
            "resolution": best.resolved_by,
            "confidence": best.confidence,
            "original_unknown": best.content,
        }

    return {"already_resolved": False}
```

### 4. High-Uncertainty Trigger

**When:** Vectors show uncertainty > 0.5
**Query:** Current task context → any relevant knowledge
**Inject:** Into next tool call response via MCP middleware

```python
class EpistemicMiddleware:
    async def handle_request(self, tool_name, arguments, handler):
        vectors = self.state_machine.get_state()

        if vectors.uncertainty > 0.5:
            # Extract query from tool context
            query = self._extract_query(tool_name, arguments)

            # Search both layers
            facts = await search_eidetic(query, limit=3)
            episodes = await search_episodic(query, limit=2)

            # Inject into response
            memory_hint = self._format_memory_hint(facts, episodes)

        result = await handler(tool_name, arguments)
        return self._enrich_response(result, memory_hint)
```

### 5. Domain-Specific Triggers

**When:** Tool call matches known domain (auth, api, db, etc.)
**Query:** Domain → domain-specific facts and patterns
**Inject:** As context in tool response

```python
DOMAIN_KEYWORDS = {
    "auth": ["login", "jwt", "token", "session", "password"],
    "api": ["endpoint", "request", "response", "http", "rest"],
    "db": ["query", "schema", "table", "migration", "index"],
}

def detect_domain(tool_name, arguments):
    text = f"{tool_name} {json.dumps(arguments)}"

    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in text.lower() for kw in keywords):
            return domain

    return None

def domain_memory_query(domain):
    return search_eidetic(
        query=domain,
        type="pattern",
        min_confidence=0.6,
        limit=5
    )
```

### 6. Pre-Finding-Log Deduplication

**When:** Before logging a new finding
**Query:** Finding text → similar existing facts
**Inject:** Confirmation count boost if similar exists

```python
def check_existing_fact(finding_text):
    similar = search_eidetic(
        query=finding_text,
        similarity_threshold=0.9
    )

    if similar:
        best = similar[0]
        return {
            "existing_fact": True,
            "fact_id": best.id,
            "current_confidence": best.confidence,
            "confirmation_count": best.confirmation_count,
            "action": "boost_confidence"  # Instead of creating new
        }

    return {"existing_fact": False, "action": "create_new"}
```

## Injection Points

### Hook Output (SessionStart)
```json
{
  "hookSpecificOutput": {
    "additionalContext": "## Memory Context\n\n### Relevant Facts\n- JWT uses RS256...\n\n### Past Work\n- Session abc: We solved similar auth issue by..."
  }
}
```

### CLI Response Enrichment
```json
{
  "ok": true,
  "decision": "proceed",
  "memory_context": {
    "relevant_facts": [...],
    "similar_past_decisions": [...],
    "warnings": ["Similar approach failed in session xyz"]
  }
}
```

### MCP Response Enrichment
```json
{
  "result": {...},
  "epistemic_state": {...},
  "memory_hint": {
    "surfaced_because": "uncertainty > 0.5",
    "facts": [...],
    "episodes": [...]
  }
}
```

## Configuration

```yaml
# .empirica/config.yaml
memory:
  auto_retrieval:
    enabled: true
    triggers:
      session_start: true
      pre_check: true
      pre_unknown_log: true
      high_uncertainty: true
      domain_specific: true
    thresholds:
      uncertainty_trigger: 0.5
      similarity_threshold: 0.8
      min_fact_confidence: 0.5
    limits:
      max_facts: 5
      max_episodes: 3
```

## Privacy/Scope

- **Project-scoped by default**: Only search within current project
- **Global opt-in**: Use `--global` flag or config to include cross-project
- **Session filtering**: Can limit to recent N sessions
- **AI filtering**: Can limit to specific AI ID's memories
