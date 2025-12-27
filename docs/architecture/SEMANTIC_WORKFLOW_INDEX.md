# Semantic Workflow Index - Dynamic Context Loading

## Concept

**Problem:** AIs don't know workflow automation exists unless we tell them explicitly
**Solution:** Embed workflow docs in Qdrant → AIs discover via project-bootstrap queries

---

## How It Works

### 1. Index Workflow Docs at Project Init

```python
# When project is created or first bootstrapped
def index_workflow_docs(project_id):
    """Embed workflow automation docs into project's semantic index"""
    from empirica.integrations.qdrant_client import QdrantClient

    client = QdrantClient()

    # Documents to index
    workflow_docs = [
        {
            "path": "docs/architecture/INTERACTIVE_CHECKLIST_TUI.md",
            "type": "workflow_automation",
            "tags": ["checklist", "completeness", "monitoring", "provider-agnostic"],
            "summary": "Interactive TUI checklist for ensuring epistemic completeness. Three-phase validation: pre-work, during-work monitoring, post-work. Covers findings, unknowns, mistakes, dead ends, sources."
        },
        {
            "path": "docs/architecture/AI_WORKFLOW_AUTOMATION.md",
            "type": "workflow_automation",
            "tags": ["automation", "hooks", "statusline", "session-creation"],
            "summary": "8 approaches for automating Empirica workflow. Includes hooks, auto-session creation, wrapper CLI, MCP integration."
        }
    ]

    for doc in workflow_docs:
        # Read full content
        with open(doc["path"], 'r') as f:
            content = f.read()

        # Chunk into sections (for better retrieval)
        sections = chunk_markdown(content, chunk_size=1000)

        # Embed each section
        for i, section in enumerate(sections):
            client.upsert(
                collection_name=f"project_{project_id}",
                points=[{
                    "id": f"{doc['path']}_{i}",
                    "vector": embed_text(section),
                    "payload": {
                        "content": section,
                        "source": doc["path"],
                        "type": doc["type"],
                        "tags": doc["tags"],
                        "chunk_index": i
                    }
                }]
            )
```

---

### 2. Query During Project Bootstrap

```python
# In project-bootstrap command
def get_dynamic_workflow_tips(project_id, session_id):
    """Get workflow suggestions based on session state"""
    from empirica.integrations.qdrant_client import QdrantClient

    client = QdrantClient()
    db = SessionDatabase()

    # Analyze current session state
    session = db.get_session(session_id)
    completeness = calculate_completeness_score(session_id)

    # Build context-aware query
    query_parts = []

    if not db.has_preflight(session_id):
        query_parts.append("how to create PREFLIGHT assessment")

    if completeness['score'] < 0.5:
        query_parts.append("improve epistemic completeness low score")

    if session.duration_minutes > 30 and db.count_findings(session_id) == 0:
        query_parts.append("logging findings discoveries during work")

    query = " ".join(query_parts) or "epistemic workflow best practices"

    # Search semantic index
    results = client.search(
        collection_name=f"project_{project_id}",
        query_vector=embed_text(query),
        limit=3,
        filter={
            "must": [{"key": "type", "match": {"value": "workflow_automation"}}]
        }
    )

    # Return contextual tips
    tips = []
    for result in results:
        tips.append({
            "source": result.payload['source'],
            "content": result.payload['content'][:500],  # First 500 chars
            "relevance": result.score
        })

    return tips
```

**Bootstrap Output with Dynamic Tips:**
```json
{
  "breadcrumbs": {...},
  "workflow_suggestions": [
    {
      "source": "INTERACTIVE_CHECKLIST_TUI.md",
      "tip": "No PREFLIGHT detected. Interactive checklist can guide you through: 1) Assess initial vectors, 2) Load project context, 3) Set investigation scope...",
      "relevance": 0.92
    },
    {
      "source": "INTERACTIVE_CHECKLIST_TUI.md",
      "tip": "Completeness score low (35%). Expected findings: 1 per 15min. Current: 0 in 30min. Suggest logging discoveries as you work...",
      "relevance": 0.87
    }
  ]
}
```

---

### 3. Activity-Based Query Refinement

```python
# Dashboard can query for specific situations
def get_contextual_prompt(activity_type, context):
    """Get workflow prompt based on current activity"""

    queries = {
        "files_modified": "logging findings when code changes detected",
        "error_detected": "logging mistakes when commands fail root cause analysis",
        "uncertainty_detected": "tracking unknowns for investigation planning",
        "rollback_detected": "documenting dead ends failed approaches",
        "url_mentioned": "citing epistemic sources documentation references"
    }

    query = queries.get(activity_type, "epistemic breadcrumb best practices")

    # Add context
    if context.get("project_type"):
        query += f" for {context['project_type']} projects"

    results = qdrant_search(query, top_k=1)

    if results:
        return results[0].payload['content']

    return None
```

**Example - Error Detected:**
```python
# Dashboard detects npm install failure
activity = "error_detected"
context = {
    "command": "npm install",
    "error": "ENOENT package.json",
    "project_type": "nodejs"
}

prompt = get_contextual_prompt(activity, context)

# Returns:
"""
When commands fail, log as mistake with:
1. Root cause (e.g., "Ran npm install in wrong directory")
2. Prevention (e.g., "Always verify pwd before npm commands")
3. Cost estimate (time lost: ~5 minutes)

This builds a mistake library for pattern detection.
"""

# Dashboard shows this as actionable prompt
```

---

## Indexing Strategy

### What to Index

1. **Workflow Automation Docs** (this repo)
   - INTERACTIVE_CHECKLIST_TUI.md
   - AI_WORKFLOW_AUTOMATION.md
   - TUI_DASHBOARD_DESIGN.md

2. **Best Practices** (discovered from sessions)
   ```python
   # Extract patterns from high-completeness sessions
   high_quality_sessions = db.get_sessions_with_completeness(min_score=0.9)

   for session in high_quality_sessions:
       pattern = analyze_session_workflow(session)
       # e.g., "This session logged findings every 12 min on average"
       index_as_best_practice(pattern)
   ```

3. **Project-Specific Patterns**
   ```python
   # Learn from project history
   project_findings = db.get_all_findings(project_id)
   common_themes = extract_themes(project_findings)
   # e.g., "OAuth authentication is a recurring topic - 45% of findings"

   index_as_project_pattern({
       "theme": "oauth_authentication",
       "frequency": 0.45,
       "suggested_workflow": "Create dedicated goal for OAuth work with subtasks"
   })
   ```

---

## Integration with Project Bootstrap

**Modified bootstrap output:**

```json
{
  "project": {...},
  "breadcrumbs": {
    "findings": [...],
    "unknowns": [...]
  },

  // NEW: Dynamic workflow suggestions
  "workflow_automation": {
    "completeness_score": 0.35,
    "grade": "LOW",
    "suggestions": [
      {
        "priority": "HIGH",
        "action": "Create PREFLIGHT assessment",
        "reason": "No baseline epistemic state recorded",
        "guide": "Interactive checklist can guide you: empirica dashboard → [1] Run PREFLIGHT",
        "source": "INTERACTIVE_CHECKLIST_TUI.md#phase-1"
      },
      {
        "priority": "MEDIUM",
        "action": "Enable activity monitoring",
        "reason": "No findings logged in 30+ min",
        "guide": "Dashboard can prompt for findings based on git changes. Launch: empirica dashboard",
        "source": "INTERACTIVE_CHECKLIST_TUI.md#phase-2"
      }
    ],

    // Learned from project history
    "project_patterns": [
      "OAuth work typically requires 3-5 findings per session",
      "Most mistakes occur in authentication flow (60%)",
      "Average session completeness for this project: 0.72"
    ]
  }
}
```

---

## Semantic Query Examples

### Query 1: "I'm stuck, don't know what to do next"
**Qdrant Search:** `"workflow stuck uncertain next steps investigation"`
**Returns:**
```markdown
From INTERACTIVE_CHECKLIST_TUI.md:

When uncertainty is high:
1. Log unknowns explicitly (empirica unknown-log)
2. Run CHECK phase to evaluate readiness
3. If confidence <40%, system suggests investigation
4. Dashboard shows unknowns with priority ranking
```

### Query 2: "Session has been running for 2 hours"
**Qdrant Search:** `"long session completeness validation postflight"`
**Returns:**
```markdown
From INTERACTIVE_CHECKLIST_TUI.md:

For sessions >2 hours:
- Expected findings: ~8 (1 per 15min)
- Likely mistakes: 1-2 (long sessions hit errors)
- POSTFLIGHT recommended at 2hr mark
- Completeness score should be >70%

Run: empirica dashboard to see checklist
```

### Query 3: "Just made a mistake, command failed"
**Qdrant Search:** `"mistake logging command failure root cause"`
**Returns:**
```markdown
From INTERACTIVE_CHECKLIST_TUI.md:

Log mistakes immediately with:
1. Root cause (why did it fail?)
2. Prevention (how to avoid?)
3. Cost (time lost: estimate)

Command: empirica mistake-log --root-cause "..." --prevention "..."

Dashboard will auto-prompt if error detected in stderr.
```

---

## Implementation Plan

### Phase 1: Index Static Docs (Week 1)
```bash
# Add to project-init command
empirica project-init --with-workflow-index

# Indexes all workflow docs automatically
```

### Phase 2: Dynamic Bootstrap Integration (Week 2)
```python
# Modify project-bootstrap to include workflow suggestions
def handle_project_bootstrap_command(args):
    breadcrumbs = get_breadcrumbs(project_id)

    # NEW: Add workflow tips
    workflow_tips = get_dynamic_workflow_tips(project_id, session_id)
    breadcrumbs['workflow_automation'] = workflow_tips

    return breadcrumbs
```

### Phase 3: Activity-Based Retrieval (Week 3)
```python
# Dashboard queries Qdrant based on detected activity
class ActivityMonitor:
    def on_activity(self, activity_type, context):
        tip = get_contextual_prompt(activity_type, context)
        self.dashboard.show_tip(tip)
```

### Phase 4: Learning Loop (Future)
```python
# Index successful session patterns as new docs
def index_session_pattern(session_id):
    if completeness_score(session_id) >= 0.9:
        pattern = extract_workflow_pattern(session_id)
        qdrant_index(pattern, type="learned_best_practice")
```

---

## Success Metrics

**Before semantic indexing:**
- AIs don't know workflow automation exists: 0% awareness
- Must read CLAUDE.md explicitly: manual
- No contextual suggestions: generic advice

**After semantic indexing:**
- Workflow tips in every project-bootstrap: 100% exposure
- Context-aware suggestions: relevant to current state
- Learning from project history: personalized patterns
- Average completeness score: +30% improvement

---

## Provider-Agnostic Benefits

1. **Works for any AI** - No Claude-specific hooks
2. **Discoverable via standard commands** - project-bootstrap is universal
3. **Self-improving** - Learns from successful sessions
4. **Project-aware** - Patterns specific to each project
5. **Activity-triggered** - Suggestions at the right moment

This makes workflow automation **discoverable and actionable** for any AI provider using Empirica.
