# Skills Breadcrumb Integration Complete

**Date:** December 10, 2025
**Status:** ✅ COMPLETE AND TESTED

## Summary

Successfully integrated skills into the project bootstrap workflow, enabling automatic context loading when creating new sessions and displaying breadcrumb information after postflight assessments.

### What Was Built

**Phase 1: Skill Architecture Clarification**
- Removed skills from Qdrant vector embedding (they're structured metadata, not semantic vectors)
- Skills remain as source-of-truth YAML files in `project_skills/`
- Memory items (findings, unknowns, mistakes) continue to use Qdrant for semantic search

**Phase 2: skill-suggest Refactoring**
- Updated `handle_skill_suggest_command` to return structured suggestions:
  - `local`: Skills already fetched in `project_skills/*.yaml`
  - `available_to_fetch`: Online candidates from `SKILL_SOURCES.yaml`
- Enables breadcrumb flow: suggest → fetch → yaml → bootstrap

**Phase 3: Project Bootstrap Integration**
- Updated `bootstrap_project_breadcrumbs()` to load skills from `project_skills/*.yaml`
- Skills included in breadcrumbs with: `id`, `title`, `tags`, `source`
- Project bootstrap now shows "Available Skills" section in output

**Phase 4: Session-Create Auto-Loading**
- `session-create` now auto-detects project from git remote URL
- Automatically links session to matching project in database
- Displays project breadcrumbs on session creation:
  - Project name and description
  - Recent findings (last 5)
  - Unresolved unknowns (last 3)
  - Available skills (last 3)

**Phase 5: Postflight Context Display**
- `postflight-submit` now shows project context summary after submission:
  - Count of recent findings
  - Count of unresolved unknowns
  - Count of available skills
- Guides the next AI session with context about what work was just completed

## File Changes

### Core Files Modified

**`empirica/cli/command_handlers/skill_commands.py`**
- Updated `handle_skill_suggest_command()` to split output into `local` and `available_to_fetch`

**`empirica/cli/command_handlers/project_embed.py`**
- Removed skills from Qdrant vector embedding (kept as structured metadata only)

**`empirica/data/session_database.py`**
- Enhanced `bootstrap_project_breadcrumbs()` with:
  - Optional `project_root` parameter (defaults to cwd)
  - Skills loading from `project_skills/*.yaml`
  - Added `available_skills` field to breadcrumbs dict

**`empirica/cli/command_handlers/project_commands.py`**
- Added "Available Skills" section to `handle_project_bootstrap_command` output
- Shows skill title, id, and tags in formatted output

**`empirica/cli/command_handlers/session_create.py`**
- Auto-detects project from git remote URL
- Links session to project in database
- Displays project breadcrumbs on session creation:
  - Project info
  - Recent findings (condensed display)
  - Unresolved unknowns (condensed display)
  - Available skills (condensed display)

**`empirica/cli/command_handlers/workflow_commands.py`**
- Enhanced `handle_postflight_submit_command()` to display project context:
  - Queries session's project_id
  - Shows breadcrumb summary after postflight submission
  - Guides next session with context

## Data Flow

```
┌─ session-create (auto-detect git repo)
│  ├─ Find project by matching repos LIKE git_url
│  ├─ Link session to project_id
│  └─ Display bootstrap_project_breadcrumbs (findings, unknowns, skills)
│
├─ preflight (normal CASCADE flow)
│
├─ work (investigate, implement, etc.)
│
└─ postflight-submit
   ├─ Save assessment to database + git notes
   └─ Display breadcrumb summary (for next session awareness)
```

## Tested Features

✅ Session auto-detection of project from git remote
✅ Auto-loading of project breadcrumbs on session-create
✅ Skills display in bootstrap output
✅ Postflight context summary
✅ 5 skills successfully fetched and stored in project_skills/

### Skills Available

1. **test-skill** - Test fixture
2. **Meta Skill Builder** (meta, skill, builder)
3. **Empirica Epistemic Framework** (empirica, epistemics, framework)
4. **Astro Web Dev** (web, astro, frontend)
5. **Tailwind CSS Basics** (css, tailwind, styling)

## Usage Examples

### Create Session (Auto-loads Project Context)
```bash
empirica session-create --ai-id claude-code
```

Output shows:
- Session ID
- Project name and description
- Recent findings
- Unresolved unknowns
- Available skills

### Run Preflight
```bash
empirica preflight --session-id <SESSION_ID> --prompt "Your task"
```

### Run Postflight (Shows Context for Next Session)
```bash
empirica postflight --session-id <SESSION_ID> \
  --vectors '{...}' \
  --reasoning "Task completed"
```

Output shows:
- Assessment submitted confirmation
- Project context summary (findings, unknowns, skills counts)

## Architecture Notes

### Why Skills Are NOT Vectors

- Skills are **structured metadata** with deterministic properties (id, title, tags)
- Embeddings would be waste of compute for deterministic data
- Qdrant reserved for **memory items** that need semantic search:
  - Findings (what was learned)
  - Unknowns (what needs investigation)
  - Mistakes (what to avoid)
- Skills referenced by **tag-based lookup**, not semantic similarity

### Why Session-Project Linking Matters

- Automatically restricts context to relevant project
- Prevents context overload (avoid showing all 1000+ findings from Ecosystem project)
- Enables multi-project workflows (web AI can switch projects seamlessly)
- Each session knows what project it belongs to via git remote auto-detection

## Integration Points

**Git Remote Detection:**
- Runs `git remote get-url origin` on session creation
- Matches against `projects.repos` LIKE pattern
- Falls back gracefully if not in git repo

**Project Breadcrumbs:**
- Loaded lazily on session-create and postflight
- Mode="session_start" for fast context (recent items only)
- Can switch to mode="live" for full context

**Skill Loading:**
- Scans `project_skills/` directory
- Parses YAML (id, title, tags)
- Shows in bootstrap output with condensed display (max 3)

## Future Enhancements

1. **Uncertainty-Driven Skill Suggestions:** Show different skills based on uncertainty level
2. **Cross-Project Skills:** Access skills from other projects when uncertainty is high
3. **Skill Execution:** Add `empirica skill-run <skill-id>` to execute steps
4. **Skill Version Tracking:** Track which skill versions were used per session
5. **Dynamic Skill Filtering:** Filter available_to_fetch by task keywords

## Commits

- `0be7db82` - Update skill-suggest to show local skills and available candidates
- `02df839b` - Remove skills from Qdrant vector embedding
- `eafbc126` - Wire skills into project-bootstrap breadcrumbs
- `1ff754fb` - Wire project-bootstrap into session-create for auto-loaded context
- `cca721e7` - Add project context display to postflight output

## Testing Checklist

- [x] skill-suggest returns local and available_to_fetch
- [x] project-bootstrap loads skills from project_skills/*.yaml
- [x] session-create auto-detects project from git remote
- [x] session-create displays project breadcrumbs with skills
- [x] postflight-submit shows context summary
- [x] Skills are not embedded in Qdrant (verified by structure)
- [x] 5 skills successfully fetched and stored

---

**Status:** Ready for production. All endpoints wired and tested.
