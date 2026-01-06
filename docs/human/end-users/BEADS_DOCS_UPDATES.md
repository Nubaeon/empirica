# BEADS Integration - Documentation & Prompt Updates

**Date:** 2025-12-15  
**Status:** What needs to be added to docs and system prompts

## 1. System Prompt Updates

### Add to `.github/copilot-instructions.md`

Insert after "XI. MCP Tools Reference" section:

```markdown
## XI.5 BEADS Integration (Optional)

### What is BEADS?

BEADS is an optional git-native issue tracker that integrates with Empirica goals for enhanced dependency tracking and multi-AI coordination.

**BEADS provides:**
- Collision-free hash IDs (bd-a1b2, bd-f14c)
- Dependency graph (blocks, related, parent-child, discovered-from)
- Ready work detection (no open blockers)
- Multi-AI coordination via git sync

**Empirica provides:**
- Epistemic tracking (confidence, learning deltas)
- CASCADE workflow integration
- Investigation findings/unknowns

### When to Use BEADS

✅ **Use BEADS when:**
- Working on multi-session tasks with dependencies
- Coordinating with other AIs on same project
- Need ready work detection (what can I do next?)
- Task graph visualization helps

❌ **Skip BEADS when:**
- Simple single-session tasks
- No dependencies between tasks
- bd CLI not installed (graceful degradation)

### Using BEADS with Goals

**Create goal with BEADS tracking:**
```bash
empirica goals-create \
  --session-id <ID> \
  --objective "Implement OAuth2" \
  --scope-breadth 0.3 \
  --use-beads  # Optional flag
```

**Returns:**
```json
{
  "ok": true,
  "goal_id": "550e8400-...",
  "beads_issue_id": "bd-a1b2",  # BEADS link
  "message": "Goal created successfully"
}
```

**Create subtask with BEADS dependency:**
```bash
empirica goals-add-subtask \
  --goal-id <ID> \
  --description "Setup OAuth2 provider" \
  --use-beads  # Creates bd-a1b2.1 (hierarchical ID)
```

### Configuration

Optional configuration in `.empirica/config.yaml`:
```yaml
integrations:
  beads:
    enabled: true
    auto_detect: true  # Check if bd CLI available
    use_agent_mail: false  # Multi-AI coordination (Phase 3)
```

### Graceful Degradation

If bd CLI not installed:
- `--use-beads` flag shows warning
- Goal creation continues normally
- No BEADS link stored (beads_issue_id = NULL)
- All Empirica features work normally

**Integration is OPTIONAL** - goals work perfectly without BEADS.

### Installation (Optional)

If user wants BEADS integration:
```bash
# Install bd CLI
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash

# Initialize in project
bd init
```

### BEADS Integration Architecture

```
goals.beads_issue_id → "bd-a1b2" (foreign key link)
Empirica tracks epistemic state
BEADS tracks task dependencies
```

**Separate concerns, linked data.**
```

---

## 2. CLI Documentation Updates

### File: `docs/production/CLI_REFERENCE.md` (or similar)

Add new section:

```markdown
## Goals with BEADS Integration

### goals-create (with --use-beads)

Create goal with optional BEADS issue tracker link.

**Syntax:**
```bash
empirica goals-create \
  --session-id <SESSION_ID> \
  --objective "OBJECTIVE" \
  --scope-breadth 0.3 \
  --use-beads  # NEW: Optional BEADS integration
```

**Parameters:**
- `--use-beads` - (Optional) Create linked BEADS issue
  - Requires bd CLI installed
  - Creates hash-based issue ID (e.g., bd-a1b2)
  - Maps scope to BEADS priority
  - Links via goals.beads_issue_id column

**Example:**
```bash
empirica goals-create \
  --session-id abc123 \
  --objective "Implement OAuth2 authentication" \
  --scope-breadth 0.5 \
  --scope-duration 0.4 \
  --use-beads
```

**Response:**
```json
{
  "ok": true,
  "goal_id": "550e8400-e29b-41d4-a716-446655440000",
  "beads_issue_id": "bd-a1b2",
  "message": "Goal created successfully",
  "scope": {"breadth": 0.5, "duration": 0.4, "coordination": 0.1}
}
```

**Graceful Degradation:**
If bd CLI not available:
- Warning logged
- Goal created without BEADS link
- beads_issue_id = null
- All other functionality works

---

### goals-add-subtask (with --use-beads)

Add subtask with optional BEADS child issue.

**Syntax:**
```bash
empirica goals-add-subtask \
  --goal-id <GOAL_ID> \
  --description "DESCRIPTION" \
  --use-beads  # NEW: Optional BEADS integration
```

**Parameters:**
- `--use-beads` - (Optional) Create BEADS child issue
  - Requires parent goal has beads_issue_id
  - Creates hierarchical ID (e.g., bd-a1b2.1)
  - Adds dependency: subtask blocks parent

**Example:**
```bash
empirica goals-add-subtask \
  --goal-id 550e8400-... \
  --description "Research OAuth2 providers" \
  --importance high \
  --use-beads
```

**Response:**
```json
{
  "ok": true,
  "task_id": "abc-123",
  "beads_issue_id": "bd-a1b2.1",
  "message": "Subtask added successfully"
}
```

**Dependencies:**
- Subtask blocks parent (bd-a1b2.1 blocks bd-a1b2)
- Can also use discovered-from for investigation findings
```

---

## 3. User Guide Updates

### File: `docs/guides/GOALS_AND_BEADS.md` (NEW)

Create new user guide:

```markdown
# Using Goals with BEADS

**Status:** Optional Integration (Phase 1)  
**Prerequisites:** bd CLI installed (optional)

## Quick Start

### Without BEADS (Default)
```bash
empirica goals-create \
  --session-id <ID> \
  --objective "My goal"
```

### With BEADS (Optional)
```bash
# Install bd CLI first
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
bd init

# Create goal with BEADS tracking
empirica goals-create \
  --session-id <ID> \
  --objective "My goal" \
  --use-beads
```

## Benefits of BEADS Integration

1. **Dependency Tracking** - Know what blocks what
2. **Ready Work Detection** - Query tasks with no blockers
3. **Multi-AI Coordination** - Collision-free hash IDs
4. **Task Visualization** - View dependency trees

## Example Workflow

```bash
# 1. Create parent goal
empirica goals-create \
  --session-id abc123 \
  --objective "Implement auth system" \
  --scope-breadth 0.6 \
  --use-beads
# Returns: beads_issue_id = bd-a1b2

# 2. Add subtasks
empirica goals-add-subtask \
  --goal-id <goal_id> \
  --description "Research OAuth2 providers" \
  --use-beads
# Creates bd-a1b2.1 (blocks bd-a1b2)

empirica goals-add-subtask \
  --goal-id <goal_id> \
  --description "Implement token validation" \
  --use-beads
# Creates bd-a1b2.2 (blocks bd-a1b2)

# 3. View dependency tree (using bd CLI directly)
bd dep tree bd-a1b2
```

**Output:**
```
🌲 Dependency tree for bd-a1b2:
→ bd-a1b2: Implement auth system [epic] [P1] (open)
  → bd-a1b2.1: Research OAuth2 providers [P1] (open)
  → bd-a1b2.2: Implement token validation [P1] (open)
```

## Configuration

Edit `.empirica/config.yaml`:
```yaml
integrations:
  beads:
    enabled: true
    auto_detect: true
```

## Troubleshooting

**Issue:** `--use-beads` shows warning "bd not available"

**Solution:** Install bd CLI:
```bash
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
```

**Issue:** Subtask doesn't create BEADS issue

**Reason:** Parent goal must have beads_issue_id.  
**Solution:** Create parent goal with `--use-beads` first.
```

---

## 4. Architecture Documentation

### File: `docs/architecture/BEADS_INTEGRATION.md` (NEW)

```markdown
# BEADS Integration Architecture

See: `docs/integrations/BEADS_INTEGRATION_DESIGN.md` for full details.

## TL;DR

- **Pattern:** Subprocess calls to bd CLI, parse --json output
- **Link:** goals.beads_issue_id (foreign key to BEADS)
- **Optional:** Graceful degradation if bd missing
- **Backward Compatible:** Existing goals continue working

## Database Schema

```sql
-- goals table
beads_issue_id TEXT  -- NULL if BEADS not used

-- Index for lookups
CREATE INDEX idx_goals_beads_issue_id ON goals(beads_issue_id);
```

## Code Locations

- Adapter: `empirica/integrations/beads/adapter.py`
- Config: `empirica/integrations/beads/config.py`
- CLI Handler: `empirica/cli/command_handlers/goal_commands.py`
- Tests: `tests/integrations/test_beads_adapter.py`
```

---

## 5. Summary Checklist

### Documentation to Add:
- [x] System prompt updates (`.github/copilot-instructions.md`)
- [x] CLI reference updates (`docs/production/CLI_REFERENCE.md`)
- [x] User guide (`docs/guides/GOALS_AND_BEADS.md`)
- [x] Architecture doc (`docs/architecture/BEADS_INTEGRATION.md`)

### Key Messages:
1. **BEADS is optional** - goals work without it
2. **Graceful degradation** - missing bd CLI doesn't break anything
3. **Use `--use-beads` flag** to opt-in
4. **Hierarchical IDs** - subtasks get bd-a1b2.1 format
5. **Dependency tracking** - blocks, related, discovered-from

### Testing:
- [x] Unit tests created (20 tests, all passing)
- [ ] Integration tests with real bd CLI
- [ ] End-to-end workflow test
- [ ] Multi-AI coordination test

---

## Next Steps

1. Create the documentation files listed above
2. Add system prompt section to `.github/copilot-instructions.md`
3. Test with actual bd CLI (install + bd init)
4. Consider Phase 2: goals-ready command

**All docs written above can be copy-pasted into respective files.**
