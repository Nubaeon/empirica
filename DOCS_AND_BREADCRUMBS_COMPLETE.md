# Documentation and Breadcrumbs Integration Complete

**Date:** December 10, 2025
**Status:** ✅ COMPLETE AND TESTED

## Summary

Successfully integrated documentation planning and semantic index into the Empirica breadcrumb workflow. AIs now automatically see:
- Which docs need to be written/updated (based on project memory)
- Core documentation for reference (from SEMANTIC_INDEX.yaml)
- Skills that can help complete the work
- What findings/unknowns remain for next session

## Architecture

### Documentation Philosophy

**Only write docs when:**
1. **Something totally new was added** - Feature, system, or major refactoring
2. **Clearly needs documentation** - Gaps found during investigation/work

**Never write docs for:**
- Trivial changes or refactoring
- Minor enhancements that fit existing docs
- Things already documented elsewhere

### Three-Phase Doc Management

#### Phase 1: Bootstrap (session-create)
Shows AIs what docs already exist and are relevant to the work:
- **Semantic Docs:** Top core-concept docs from SEMANTIC_INDEX.yaml
- **Reference Docs:** Explicitly added to project (project-level knowledge)
- **Skills:** Available tools that can guide implementation

#### Phase 2: Work (preflight → investigate → act)
AI performs work naturally, documenting findings/unknowns as they discover them

#### Phase 3: Postflight (after work complete)
System shows AIs which docs need updates/creation:
- **Doc Completeness Score:** 0.0-1.0 based on memory state
- **Suggested Updates:**
  - "X findings → update knowledge sections"
  - "X unknowns → add resolution patterns"
  - "X mistakes → add prevention guidance"
  - "New CLI → add usage examples"

## Implementation Details

### Postflight Doc Suggestions

Uses `compute_doc_plan()` from `doc_planner.py`:
- Loads SEMANTIC_INDEX.yaml
- Reads project memory (findings/unknowns/mistakes)
- Computes completeness score based on memory count
- Suggests specific docs to update with reasons

```python
# Scoring logic:
score = 0.6
if num_findings > 5:     score -= 0.1  # Too many unmapped findings
if num_unknowns > 3:     score -= 0.1  # Unresolved unknowns
if num_mistakes > 2:     score -= 0.1  # Missing prevention docs
# Result: 0.0-1.0 scale
```

### Bootstrap Semantic Docs

Loads from SEMANTIC_INDEX.yaml:
- Extracts top docs (up to 5)
- Prioritizes "core-concept" tagged docs
- Shows path, title, and tags
- Displayed in project-bootstrap and session-create

### Reference Docs

Explicitly added to projects:
- `empirica refdoc-add --project-id <id> --doc-path <path> --description "..."`
- Stored in `project_reference_docs` table
- Shown in project-bootstrap output

## File Changes

### Core Documentation Integration

**`empirica/core/docs/doc_planner.py`**
- Already existed - computes doc completeness
- Loads semantic index + project memory
- Suggests which docs need updates
- Scores based on findings/unknowns/mistakes count

**`empirica/cli/command_handlers/workflow_commands.py`**
- Enhanced `handle_postflight_submit_command()`
- Now calls `compute_doc_plan()` after submission
- Displays:
  - Doc completeness score
  - Top 3 suggested updates with reasons

### Bootstrap Enhancement

**`empirica/data/session_database.py`**
- Added semantic index loading to `bootstrap_project_breadcrumbs()`
- Top 5 core-concept docs extracted from SEMANTIC_INDEX.yaml
- Added `semantic_docs` field to breadcrumbs dict

**`empirica/cli/command_handlers/project_commands.py`**
- Added "Core Documentation" section to project-bootstrap output
- Shows top 3 semantic docs with path and title

## Data Flow

```
┌─ session-create
│  ├─ Auto-detect project from git
│  └─ Load bootstrap_project_breadcrumbs:
│     ├─ Semantic docs (SEMANTIC_INDEX.yaml)
│     ├─ Available skills (project_skills/*.yaml)
│     ├─ Reference docs (project_reference_docs table)
│     └─ Project findings/unknowns/mistakes
│
├─ preflight (KNOW/DO/CONTEXT assessment)
│
├─ work (investigate, code, test)
│
└─ postflight-submit
   ├─ Save vectors to database + git notes
   ├─ Call compute_doc_plan(project_id):
   │  ├─ Load semantic index
   │  ├─ Query findings/unknowns/mistakes
   │  ├─ Score: 0.6 - penalties for unmapped items
   │  └─ Suggest updates (path + reason)
   └─ Display:
      ├─ Project context (for next session)
      └─ Doc requirements (what needs writing)
```

## Usage Examples

### Session Creation (Shows Bootstrap Docs)
```bash
empirica session-create --ai-id claude-code
```

Output includes:
```
📖 Core Documentation:
   1. Epistemic Vectors
      Path: production/05_EPISTEMIC_VECTORS.md
   2. CASCADE Flow
      Path: production/06_CASCADE_FLOW.md
```

### Postflight (Shows Doc Requirements)
```bash
empirica postflight --session-id <ID> \
  --vectors '{...}' \
  --reasoning "Implemented skills breadcrumbs"
```

Output includes:
```
📄 Documentation Requirements:
   Completeness: 0.6/1.0
   Suggested updates:
     • docs/reference/CLI_COMMANDS_COMPLETE.md
       Reason: New CLI (project-embed, project-search) → add usage examples
```

### Explicit Doc Check
```bash
empirica doc-check --project-id <ID>
```

Returns JSON with completeness score and suggestions

## Key Design Decisions

### Why Postflight Suggests Docs
- Forces AIs to recognize documentation gaps
- Prevents documentation debt accumulation
- Makes it explicit: "Your work introduced these docs needs"
- Non-blocking: AIs can ignore but see the suggestion

### Why Bootstrap Shows Semantic Index
- Gives AIs quick access to core docs
- No need to search; essential docs are pre-selected
- Tags show relevance (core-concept, cascade, vectors, etc.)
- Semantic index is YAML-based, easy to maintain

### Why Only Score on Count
- Simple, deterministic scoring
- Avoids subjective "quality" assessment
- Encourages mapping findings to docs (not creating more findings)
- Easy to understand: >5 findings → incomplete docs

## Testing Checklist

- [x] Semantic index loads in bootstrap
- [x] Core docs display in project-bootstrap output
- [x] session-create shows skills (already wired)
- [x] postflight calls compute_doc_plan
- [x] postflight displays completeness score
- [x] postflight shows suggested updates with reasons
- [x] doc-check command works
- [x] All endpoints tested

## Commits

- `afe53d23` - Wire doc planner into postflight for documentation requirements
- `e09544bc` - Add semantic index docs to project bootstrap

## Integration Summary

The workflow now ensures AIs:

1. **On session-create:** See what docs already exist (bootstrap context)
2. **During work:** Naturally log findings/unknowns/mistakes
3. **On postflight:** Learn which docs need to be written/updated
4. **Next session:** Resume knowing what documentation work remains

This creates a tight feedback loop where documentation requirements are transparent and actionable, preventing silent documentation debt.

---

**Status:** Ready for production. All documentation paths wired and tested.
