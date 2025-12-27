# Empirica CLI Reference

**Complete command reference for AI-first CLI**
**Last Updated:** 2025-12-20

---

## Philosophy

This CLI is **AI-first** - designed for AI assistants to use autonomously. All 60+ commands are documented here with examples. No artificial simplification.

**Key principles:**
- Every command has examples
- Dependencies clearly stated
- Related commands cross-referenced
- Common workflows shown

---

## AI-First JSON Stdin Pattern

**Empirica commands accept JSON via stdin for zero shell quoting issues.**

### The Pattern

All Empirica commands that accept complex configuration support a **positional `config` argument** with `nargs='?'`:

```python
# Parser pattern
parser.add_argument('config', nargs='?',
    help='JSON config file path or "-" for stdin (AI-first mode)')

# Handler pattern
def handle_command(args):
    config_data = None

    if hasattr(args, 'config') and args.config:
        if args.config == '-':
            # Read from stdin
            config_data = json.loads(sys.stdin.read())
        else:
            # Read from file
            with open(args.config, 'r') as f:
                config_data = json.loads(f.read())

    # Extract parameters from config or fall back to CLI flags
    session_id = config_data.get('session_id') if config_data else args.session_id
```

### Usage Examples

**Method 1: Stdin (Recommended for AI)**
```bash
# Using echo
echo '{"session_id":"abc","objective":"Implement feature X"}' | empirica goals-create -

# Using cat with heredoc
cat <<'EOF' | empirica handoff-create -
{
  "session_id": "abc123",
  "task_summary": "Implemented OAuth2 with PKCE",
  "key_findings": ["PKCE required", "Tokens in httpOnly cookies"],
  "next_session_context": "Continue with MFA integration"
}
EOF

# Using file
cat /tmp/config.json | empirica preflight-submit -
```

**Method 2: File Path**
```bash
empirica goals-create /tmp/goal-config.json
```

**Method 3: Legacy Flags (Backward Compatible)**
```bash
empirica goals-create --session-id abc --objective "Implement feature X"
```

### Why This Pattern?

**Problem with shell quoting:**
```bash
# ❌ Escaping nightmare
empirica command --json "{\"key\":\"value with 'quotes'\"}"

# ❌ Heredoc with variable expansion issues
cat <<EOF | empirica command
{"key": "$VAR"}  # Variables expand unexpectedly
EOF
```

**Solution with stdin:**
```bash
# ✅ No escaping needed
echo '{"key":"value with 'quotes'"}' | empirica command -

# ✅ Heredoc with single quotes (no expansion)
cat <<'EOF' | empirica command -
{"key": "$VAR"}  # Literal string, no expansion
EOF
```

### Commands Supporting JSON Stdin

**CASCADE Workflow:**
- `preflight-submit -`
- `check-submit -`
- `postflight-submit -`

**Goals & Tasks:**
- `goals-create -`
- `handoff-create -`

**Sessions:**
- `session-create -`

**See individual command documentation for exact JSON schema.**

---

## Quick Start (Your First Session)

```bash
# 1. Create session
empirica session-create --ai-id claude-code

# 2. Assess before work (PREFLIGHT)
cat > /tmp/preflight.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "vectors": {
    "engagement": 0.85, "know": 0.70, "do": 0.90,
    "context": 0.60, "clarity": 0.85, "coherence": 0.80,
    "signal": 0.85, "density": 0.50, "state": 0.30,
    "change": 0.85, "completion": 0.0, "impact": 0.70,
    "uncertainty": 0.60
  },
  "reasoning": "Starting new feature implementation"
}
EOF
empirica preflight-submit /tmp/preflight.json

# 3. Do your work...

# 4. Measure learning (POSTFLIGHT)
cat > /tmp/postflight.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "vectors": {
    "engagement": 0.90, "know": 0.85, "do": 0.95,
    "context": 0.80, "clarity": 0.95, "coherence": 0.90,
    "signal": 0.95, "density": 0.60, "state": 0.90,
    "change": 0.95, "completion": 1.0, "impact": 0.90,
    "uncertainty": 0.25
  },
  "reasoning": "Feature complete. Know +0.15, uncertainty -0.35"
}
EOF
empirica postflight-submit /tmp/postflight.json
```

**That's the core loop.** Everything else builds on this.

---

## Session Management

### session-create

Create new Empirica session.

**Usage:**
```bash
empirica session-create --ai-id <ai-identifier> [--bootstrap-level <0-4>]
```

**AI-first JSON mode:**
```bash
cat > /tmp/session.json << 'EOF'
{
  "ai_id": "claude-code",
  "bootstrap_level": 1
}
EOF
empirica session-create /tmp/session.json
```

**Parameters:**
- `--ai-id` (required) - AI identifier (e.g., claude-code, qwen, gemini)
- `--bootstrap-level` (optional) - Context loading: 0=minimal, 1=standard, 2=extended, 3=complete, 4=optimal

**Returns:**
```json
{
  "ok": true,
  "session_id": "uuid",
  "ai_id": "claude-code",
  "project_id": "uuid"
}
```

**See also:** sessions-list, sessions-show, sessions-resume

---

### sessions-list

List all sessions.

**Usage:**
```bash
empirica sessions-list [--limit 10] [--ai-id <filter>] [--output json]
```

**Example:**
```bash
# List last 5 sessions
empirica sessions-list --limit 5 --output json

# Filter by AI
empirica sessions-list --ai-id claude-code --output json
```

**See also:** sessions-show, session-create

---

### sessions-show

Show session details and epistemic state.

**Usage:**
```bash
empirica sessions-show <session-id> [--verbose] [--output json]
```

**Example:**
```bash
# Current session state
empirica sessions-show latest:active:claude-code --output json

# Verbose with full history
empirica sessions-show <uuid> --verbose --output json
```

**Session ID aliases:**
- `latest:active:<ai-id>` - Most recent active session
- `latest:any:<ai-id>` - Most recent session (active or completed)
- `<uuid>` - Specific session

**See also:** session-create, get-calibration-report

---

### sessions-resume

Resume previous session(s).

**Usage:**
```bash
empirica sessions-resume --ai-id <ai-id> [--count 1]
```

**Example:**
```bash
# Resume last session
empirica sessions-resume --ai-id claude-code --count 1
```

**See also:** checkpoint-load (for git-based resumption)

---

### memory-compact

Compact session for epistemic continuity across conversation boundaries. Use when approaching context limits (e.g., >180k tokens) to enable true cross-session continuity.

**Dependencies:** Session must exist with epistemic vectors

**Workflow:**
1. Checkpoints current epistemic state (pre-compact snapshot)
2. Loads project-bootstrap context (ground truth: findings/unknowns/goals)
3. Creates continuation session with lineage linkage
4. Returns formatted context for IDE injection
5. Provides recommended PREFLIGHT vectors for new session

**Usage (AI-first JSON):**
```bash
cat > /tmp/compact.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "create_continuation": true,
  "include_bootstrap": true,
  "checkpoint_current": true,
  "compact_mode": "full"
}
EOF
empirica memory-compact /tmp/compact.json
```

**Parameters:**
- `session_id` (required) - Session to compact (supports aliases like "latest:active:ai-id")
- `create_continuation` (default: true) - Create new continuation session
- `include_bootstrap` (default: true) - Load project-bootstrap context
- `checkpoint_current` (default: true) - Snapshot current epistemic state
- `compact_mode` (default: "full") - Compaction mode:
  - `full` - All features (checkpoint + bootstrap + continuation + IDE injection)
  - `minimal` - Checkpoint only (fast, minimal context)
  - `context_only` - Bootstrap only (no checkpoint or continuation)

**Returns:**
```json
{
  "ok": true,
  "operation": "memory_compact",
  "session_id": "original-session-id",
  "compact_mode": "full",
  "pre_compact_checkpoint": {
    "checkpoint_id": "checkpoint-uuid",
    "vectors": {"engagement": 0.85, "know": 0.80, ...},
    "timestamp": "2025-12-20T..."
  },
  "bootstrap_context": {
    "findings": [...],
    "unknowns": [...],
    "goals": [...]
  },
  "continuation": {
    "new_session_id": "continuation-session-id",
    "parent_session_id": "original-session-id",
    "ai_id": "claude-code"
  },
  "recommended_preflight": {
    "engagement": 0.85,
    "foundation": {"know": 0.80, "do": 0.90, "context": 0.85},
    "uncertainty": 0.35,
    ...
  },
  "ide_injection": "## Empirica Context (Loaded from Ground Truth)\n\n..."
}
```

**Use cases:**
- Approaching IDE context limits (>180k tokens used)
- Switching between long-running investigation sessions
- Measuring epistemic drift (pre-compact vs. post-bootstrap vectors)
- Enabling true cross-session continuity with ground truth anchoring

**Example workflow:**
```bash
# 1. Detect context pressure (e.g., IDE shows >180k tokens)

# 2. Run memory-compact
cat > /tmp/compact.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "compact_mode": "full"
}
EOF
RESULT=$(empirica memory-compact /tmp/compact.json)

# 3. Extract continuation session ID
NEW_SESSION=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['continuation']['new_session_id'])")

# 4. Copy ide_injection to IDE conversation (provides bootstrap context)

# 5. Run PREFLIGHT in new session with recommended vectors
cat > /tmp/preflight.json << EOF
{
  "session_id": "$NEW_SESSION",
  "vectors": $(echo "$RESULT" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin)['recommended_preflight']))"),
  "reasoning": "Post-compact PREFLIGHT with bootstrap-adjusted vectors"
}
EOF
empirica preflight-submit /tmp/preflight.json

# 6. Continue work in new session with full epistemic context
```

**See also:** checkpoint-load, project-bootstrap, sessions-resume

---

## CASCADE Workflow

### preflight-submit

Submit PREFLIGHT epistemic assessment (before work).

**Dependencies:** Session must exist

**Usage (AI-first JSON):**
```bash
cat > /tmp/preflight.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "vectors": {
    "engagement": 0.85,
    "know": 0.70,
    "do": 0.90,
    "context": 0.60,
    "clarity": 0.85,
    "coherence": 0.80,
    "signal": 0.85,
    "density": 0.50,
    "state": 0.30,
    "change": 0.85,
    "completion": 0.0,
    "impact": 0.70,
    "uncertainty": 0.60
  },
  "reasoning": "Starting OAuth implementation. Know OAuth basics but not this codebase. Moderate uncertainty about integration points."
}
EOF

empirica preflight-submit /tmp/preflight.json
```

**13 Epistemic Vectors (0.0-1.0):**
- **Foundation (4):** engagement, know, do, context
- **Comprehension (4):** clarity, coherence, signal, density
- **Execution (4):** state, change, completion, impact
- **Meta (1):** uncertainty

**Returns:**
```json
{
  "ok": true,
  "session_id": "uuid",
  "checkpoint_id": "git-sha",
  "calibration_accuracy": "good",
  "persisted": true
}
```

**See also:** postflight-submit, check

---

### check

Mid-task validation gate. Decide: proceed or investigate more?

**Dependencies:** Session exists, PREFLIGHT submitted

**Usage:**
```bash
cat > /tmp/check.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "findings": ["OAuth endpoints use PKCE", "State parameter required"],
  "unknowns": ["Session management unclear"],
  "confidence": 0.75
}
EOF

empirica check /tmp/check.json
```

**Returns:**
```json
{
  "ok": true,
  "decision": "proceed",
  "confidence": 0.75,
  "readiness_gate": "passed"
}
```

**Decision logic:**
- `confidence >= 0.7` → "proceed"
- `confidence < 0.7` → "investigate"

**See also:** preflight-submit, check-submit

---

### check-submit

Submit CHECK assessment (after investigation cycle).

**Usage:**
```bash
cat > /tmp/check-submit.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "vectors": {
    "engagement": 0.90,
    "know": 0.80,
    "do": 0.90,
    "context": 0.75,
    "clarity": 0.90,
    "coherence": 0.85,
    "signal": 0.90,
    "density": 0.55,
    "state": 0.60,
    "change": 0.85,
    "completion": 0.40,
    "impact": 0.75,
    "uncertainty": 0.35
  },
  "decision": "proceed",
  "reasoning": "Investigation complete. Know increased to 0.80, uncertainty reduced to 0.35. Ready to implement."
}
EOF

empirica check-submit /tmp/check-submit.json
```

**See also:** check, preflight-submit

---

### postflight-submit

Submit POSTFLIGHT assessment (after work complete). Measures learning.

**Dependencies:** Session exists, PREFLIGHT submitted

**Usage:**
```bash
cat > /tmp/postflight.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "vectors": {
    "engagement": 0.90,
    "know": 0.85,
    "do": 0.95,
    "context": 0.80,
    "clarity": 0.95,
    "coherence": 0.90,
    "signal": 0.95,
    "density": 0.60,
    "state": 0.90,
    "change": 0.95,
    "completion": 1.0,
    "impact": 0.90,
    "uncertainty": 0.25
  },
  "reasoning": "OAuth implementation complete. KNOW +0.15 (learned PKCE flow), UNCERTAINTY -0.35 (clear understanding). Tested and working."
}
EOF

empirica postflight-submit /tmp/postflight.json
```

**Returns:**
```json
{
  "ok": true,
  "deltas": {
    "know": 0.15,
    "uncertainty": -0.35,
    "state": 0.60,
    "completion": 1.0
  },
  "calibration_accuracy": "good",
  "calibration_issues_detected": 0
}
```

**System calculates:**
- Learning deltas (POSTFLIGHT - PREFLIGHT)
- Calibration accuracy (predicted vs actual learning)
- Confabulation detection (impossible deltas)

**See also:** preflight-submit, get-calibration-report

---

### get-calibration-report

Check calibration accuracy for session.

**Dependencies:** Session with PREFLIGHT + POSTFLIGHT

**Usage:**
```bash
empirica calibration <session-id> --output json
```

**Example:**
```bash
empirica calibration latest:active:claude-code --output json
```

**Returns:**
```json
{
  "ok": true,
  "session_id": "uuid",
  "calibration_accuracy": "good",
  "deltas": {
    "know": 0.15,
    "uncertainty": -0.35
  },
  "issues": []
}
```

**Calibration levels:**
- `"good"` - Well-calibrated, learning as expected
- `"fair"` - Some discrepancies
- `"poor"` - Overconfidence or underconfidence detected

**See also:** postflight-submit

---

## Goal Management

### goals-create

Create structured goal with epistemic scope.

**Dependencies:** Active session

**Usage:**
```bash
cat > /tmp/goal.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "objective": "Implement OAuth2 authentication",
  "scope": {
    "breadth": 0.6,
    "duration": 0.4,
    "coordination": 0.3
  },
  "success_criteria": [
    "PKCE flow implemented",
    "Token refresh working",
    "Tests passing"
  ],
  "estimated_complexity": 0.65
}
EOF

empirica goals-create /tmp/goal.json
```

**Scope vectors (0.0-1.0):**
- `breadth` - How wide (0.0=single function, 1.0=entire codebase)
- `duration` - Expected lifetime (0.0=minutes, 1.0=weeks/months)
- `coordination` - Multi-agent needs (0.0=solo, 1.0=heavy coordination)

**Returns:**
```json
{
  "ok": true,
  "goal_id": "uuid",
  "objective": "Implement OAuth2 authentication"
}
```

**See also:** goals-add-subtask, goals-list

---

### goals-add-subtask

Add subtask to existing goal.

**Dependencies:** Goal exists

**Usage:**
```bash
cat > /tmp/subtask.json << 'EOF'
{
  "goal_id": "<goal-uuid>",
  "description": "Research PKCE flow",
  "importance": "high",
  "estimated_tokens": 2000
}
EOF

empirica goals-add-subtask /tmp/subtask.json
```

**Importance levels:**
- `critical` - Must complete for goal success
- `high` - Important but not blocking
- `medium` - Nice to have
- `low` - Optional

**See also:** goals-complete-subtask, goals-get-subtasks

---

### goals-complete-subtask

Mark subtask as complete.

**Usage:**
```bash
cat > /tmp/complete.json << 'EOF'
{
  "task_id": "<subtask-uuid>",
  "evidence": "Implemented in auth.py:123, tests pass"
}
EOF

empirica goals-complete-subtask /tmp/complete.json
```

**See also:** goals-add-subtask, goals-progress

---

### goals-list

List goals for session.

**Usage:**
```bash
empirica goals-list --session-id latest:active:claude-code --output json
```

**See also:** goals-progress, goals-get-subtasks

---

### goals-progress

Get goal completion progress.

**Usage:**
```bash
empirica goals-progress --goal-id <uuid> --output json
```

**Returns:**
```json
{
  "ok": true,
  "goal_id": "uuid",
  "objective": "Implement OAuth2",
  "completion": 0.75,
  "subtasks": {
    "total": 4,
    "completed": 3,
    "pending": 1
  }
}
```

**See also:** goals-list, goals-get-subtasks

---

### goals-get-subtasks

Get detailed subtask information.

**Usage:**
```bash
empirica goals-get-subtasks --goal-id <uuid> --output json
```

**Returns:**
```json
{
  "ok": true,
  "subtasks": [
    {
      "id": "uuid",
      "description": "Research PKCE",
      "status": "completed",
      "importance": "high"
    }
  ]
}
```

**See also:** goals-add-subtask, goals-progress

---

## Project Setup & Configuration

### project-init

Initialize Empirica in a new project.

**Usage:**
```bash
empirica project-init [--project-name "My Project"] [--description "Description"]
```

**Creates:**
- `.empirica/config.yaml` - Project configuration
- `.empirica/project.yaml` - Project metadata
- `.empirica/sessions/sessions.db` - SQLite database

**Example:**
```bash
cd ~/my-project
empirica project-init --project-name "OAuth Service"
```

**See also:** config, project-bootstrap

---

### config

Manage Empirica configuration.

**Usage:**
```bash
# Show current config
empirica config show

# Set config value
empirica config set <key> <value>

# Get config value
empirica config get <key>
```

**See also:** project-init

---

## Checkpoints & Continuity

### checkpoint-create

Save checkpoint to git notes (compressed).

**Dependencies:** Git repository

**Usage:**
```bash
cat > /tmp/checkpoint.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "phase": "POSTFLIGHT",
  "vectors": {...},
  "metadata": {
    "files_changed": ["auth.py", "test_auth.py"],
    "commits": ["abc123"]
  }
}
EOF

empirica checkpoint-create /tmp/checkpoint.json
```

**Compression:** ~97.5% token reduction vs full context

**See also:** checkpoint-load

---

### checkpoint-load

Load checkpoint from git notes.

**Dependencies:** Git repository with checkpoints

**Usage:**
```bash
# Load latest checkpoint for AI
empirica checkpoint-load latest:active:claude-code --output json

# Load specific session
empirica checkpoint-load <session-uuid> --output json
```

**Returns:**
```json
{
  "ok": true,
  "session_id": "uuid",
  "phase": "POSTFLIGHT",
  "vectors": {...},
  "metadata": {...}
}
```

**Token savings:** ~97.5% reduction vs. manual context reconstruction

**See also:** checkpoint-create, handoff-create

---

## Epistemic Learning (Qdrant Integration)

**Dependencies:** Qdrant running, OpenAI API key for embeddings

### epistemics-search

Search epistemic learning trajectories semantically.

**Usage:**
```bash
empirica epistemics-search \
  --project-id <uuid> \
  --query "OAuth2 authentication learning" \
  --min-learning 0.2 \
  --limit 5 \
  --output json
```

**Parameters:**
- `--query` - Natural language query
- `--min-learning` - Minimum knowledge delta (know Δ ≥ threshold)
- `--limit` - Max results (default: 5)

**Returns:**
```json
{
  "ok": true,
  "results": [
    {
      "score": 0.92,
      "session_id": "uuid",
      "task_description": "Implement OAuth2 with PKCE",
      "deltas": {
        "know": 0.35,
        "uncertainty": -0.40
      },
      "calibration_accuracy": "good"
    }
  ]
}
```

**Use case:** "Show me sessions where we learned about OAuth with high knowledge gain"

**See also:** epistemics-stats, project-bootstrap

---

### epistemics-stats

Aggregate epistemic learning statistics for project.

**Usage:**
```bash
empirica epistemics-stats --project-id <uuid> --output json
```

**Returns:**
```json
{
  "ok": true,
  "stats": {
    "total_sessions": 47,
    "avg_know_delta": 0.18,
    "avg_uncertainty_delta": -0.22,
    "high_learning_sessions": 23,
    "calibration_breakdown": {
      "good": 38,
      "fair": 7,
      "poor": 2
    },
    "investigation_rate": 0.68
  }
}
```

**Use case:** "Is the team learning efficiently? Are calibrations good?"

**See also:** epistemics-search, get-calibration-report

---

### project-bootstrap

Load project context with epistemic breadcrumbs.

**Dependencies:** Project initialized

**Usage:**
```bash
empirica project-bootstrap --project-id <uuid> --output json
```

**Returns:**
```json
{
  "ok": true,
  "breadcrumbs": {
    "findings": ["Found PKCE", "Refresh tokens work"],
    "unknowns": [{"unknown": "MFA flow?", "is_resolved": false}],
    "dead_ends": ["Tried implicit flow - insecure"],
    "mistakes": [...]
  }
}
```

**Uncertainty-driven depth:**
- High uncertainty (>0.7) → Deep context (all findings + unknowns)
- Medium (0.5-0.7) → Moderate (recent findings)
- Low (<0.5) → Minimal (quick overview)

**Token savings:** 80-92% reduction vs. manual git/grep reconstruction

**See also:** epistemics-search, finding-log

---

## Project Tracking (Learning Artifacts)

**Dependencies:** Project initialized

### finding-log

Log what was learned/discovered.

**Usage:**
```bash
cat > /tmp/finding.json << 'EOF'
{
  "project_id": "<uuid>",
  "session_id": "latest:active:claude-code",
  "finding": "PKCE flow requires state parameter for security",
  "goal_id": "<optional-goal-uuid>"
}
EOF

empirica finding-log /tmp/finding.json
```

**Stored in:**
- SQLite (`project_findings` table)
- Qdrant (semantic index for retrieval)

**See also:** unknown-log, project-bootstrap, epistemics-search

---

### unknown-log

Log what's still unclear.

**Usage:**
```bash
cat > /tmp/unknown.json << 'EOF'
{
  "project_id": "<uuid>",
  "session_id": "latest:active:claude-code",
  "unknown": "How does MFA integration work with OAuth flow?"
}
EOF

empirica unknown-log /tmp/unknown.json
```

**Resolution tracking:** Can mark unknown as resolved later

**See also:** finding-log, deadend-log

---

### deadend-log

Log what didn't work (prevent repeat attempts).

**Usage:**
```bash
cat > /tmp/deadend.json << 'EOF'
{
  "project_id": "<uuid>",
  "session_id": "latest:active:claude-code",
  "approach": "Tried implicit OAuth flow",
  "why_failed": "Insecure, no refresh tokens, deprecated"
}
EOF

empirica deadend-log /tmp/deadend.json
```

**Use case:** Before trying an approach, search dead ends to avoid repeating failures

**See also:** mistake-log, finding-log

---

### mistake-log

Log mistake with root cause and prevention.

**Usage:**
```bash
cat > /tmp/mistake.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "mistake": "Hardcoded client secret in code",
  "why_wrong": "Security vulnerability, secret exposed in git history",
  "cost_estimate": "2 hours to fix + security audit",
  "root_cause_vector": "KNOW",
  "prevention": "Use environment variables, add pre-commit hook to detect secrets"
}
EOF

empirica mistake-log /tmp/mistake.json
```

**Root cause vectors:**
- KNOW, DO, CONTEXT, CLARITY, COHERENCE, SIGNAL, DENSITY, STATE, CHANGE, COMPLETION, IMPACT, UNCERTAINTY

**See also:** mistake-query, deadend-log

---

### mistake-query

Query logged mistakes for learning.

**Usage:**
```bash
empirica mistake-query --session-id <uuid> --limit 10 --output json
```

**Filter by:**
- `--session-id` - Specific session
- `--goal-id` - Specific goal
- `--limit` - Max results

**Use case:** "Show mistakes from past OAuth work to avoid repeating"

**See also:** mistake-log

---

## Multi-AI Coordination (Phase 1)

**Dependencies:** Multiple AIs, git notes

### goals-discover

Discover goals from other AIs via git notes.

**Usage:**
```bash
empirica goals-discover --from-ai-id qwen --output json
```

**Returns:**
```json
{
  "ok": true,
  "goals": [
    {
      "goal_id": "uuid",
      "ai_id": "qwen",
      "objective": "Test OAuth implementation",
      "status": "in_progress"
    }
  ]
}
```

**Use case:** "What is Qwen working on? Can I help?"

**See also:** goals-resume, handoff-query

---

### goals-resume

Resume another AI's goal with epistemic handoff.

**Usage:**
```bash
cat > /tmp/resume.json << 'EOF'
{
  "goal_id": "<uuid>",
  "ai_id": "claude-code"
}
EOF

empirica goals-resume /tmp/resume.json
```

**Creates new session** continuing the goal with full epistemic context

**See also:** goals-discover, handoff-create

---

## Handoff Reports

**Dependencies:** Session with work completed

### handoff-create

Create epistemic handoff report (~90% token reduction).

**Usage:**
```bash
cat > /tmp/handoff.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "task_summary": "Implemented OAuth2 with PKCE, refresh tokens working",
  "key_findings": [
    "PKCE flow requires state parameter",
    "Refresh token rotation implemented"
  ],
  "remaining_unknowns": ["MFA integration unclear"],
  "next_session_context": "Next: Implement MFA flow, check TOTP library",
  "artifacts_created": ["auth.py", "test_auth.py"]
}
EOF

empirica handoff-create /tmp/handoff.json
```

**Use case:** Continuity for next session (same AI) or handoff to different AI

**See also:** handoff-query, goals-resume

---

### handoff-query

Query handoff reports.

**Usage:**
```bash
# Latest handoffs by AI
empirica handoff-query --ai-id claude-code --limit 5 --output json

# Specific session
empirica handoff-query --session-id <uuid> --output json
```

**See also:** handoff-create, checkpoint-load

---

## Cryptographic Trust (Phase 2)

**Dependencies:** Ed25519 keypair generation

### identity-create

Create AI identity with Ed25519 keypair.

**Usage:**
```bash
empirica identity-create --ai-id claude-code [--overwrite]
```

**Creates:**
- `.empirica/identity/claude-code.key` (private key, gitignored)
- Public key stored in database

**See also:** identity-list, identity-export

---

### identity-list

List all AI identities.

**Usage:**
```bash
empirica identity-list --output json
```

**See also:** identity-create

---

### identity-export

Export public key for sharing.

**Usage:**
```bash
empirica identity-export --ai-id claude-code --output json
```

**Returns:**
```json
{
  "ok": true,
  "ai_id": "claude-code",
  "public_key": "ed25519:abc123..."
}
```

**See also:** identity-verify

---

### identity-verify

Verify signed session.

**Usage:**
```bash
empirica identity-verify --session-id <uuid> --output json
```

**Returns:**
```json
{
  "ok": true,
  "verified": true,
  "ai_id": "claude-code",
  "signature": "valid"
}
```

**See also:** identity-create

---

## Vision Analysis

**Dependencies:** Vision model access (optional)

### vision-analyze

Analyze image(s) and extract metadata.

**Usage:**
```bash
# Single image
empirica vision-analyze --image "screenshot.png" --session-id <uuid>

# Pattern
empirica vision-analyze --pattern "slides/*.png" --session-id <uuid>
```

**Returns:**
```json
{
  "ok": true,
  "images": [
    {
      "path": "screenshot.png",
      "size": "1920x1080",
      "format": "PNG",
      "aspect_ratio": "16:9"
    }
  ]
}
```

**Optionally logs findings to session**

**See also:** vision-log

---

### vision-log

Manually log visual observation to session.

**Usage:**
```bash
cat > /tmp/vision.json << 'EOF'
{
  "session_id": "latest:active:claude-code",
  "observation": "Screenshot shows OAuth consent screen with proper PKCE parameters"
}
EOF

empirica vision-log /tmp/vision.json
```

**See also:** vision-analyze

---

## Skills System

**Dependencies:** Skills defined

### skill-suggest

Suggest skills for a task.

**Usage:**
```bash
empirica skill-suggest --task "Implement REST API" --output json
```

**Returns:**
```json
{
  "ok": true,
  "suggestions": [
    {
      "skill": "api-design",
      "relevance": 0.95,
      "description": "REST API design patterns"
    }
  ]
}
```

**See also:** skill-fetch

---

### skill-fetch

Fetch and normalize skill.

**Usage:**
```bash
# From URL
empirica skill-fetch --name "api-design" --url "https://..." --output json

# From file
empirica skill-fetch --name "api-design" --file "api-design.skill" --output json
```

**See also:** skill-suggest

---

## Documentation Tools

**Dependencies:** Semantic index

### ask

Query Empirica documentation semantically.

**Usage:**
```bash
empirica ask "How do I use CHECK gates?"
```

**Returns relevant documentation**

**See also:** onboard, project-search

---

### onboard

Interactive onboarding for new users.

**Usage:**
```bash
empirica onboard
```

**Walks through:**
- Session creation
- PREFLIGHT/POSTFLIGHT
- Goal management
- Project setup

**See also:** ask

---

### project-embed

Embed project documentation for semantic search.

**Usage:**
```bash
empirica project-embed --project-id <uuid>
```

**Creates embeddings** in Qdrant for semantic doc search

**See also:** project-search, ask

---

### project-search

Search project documentation.

**Usage:**
```bash
empirica project-search --project-id <uuid> --query "authentication" --output json
```

**See also:** project-embed, ask

---

## Advanced Workflow

### workflow

Execute full preflight→work→postflight workflow.

**Usage:**
```bash
empirica workflow --auto [--verbose]
```

**See also:** preflight-submit, postflight-submit

---

### investigate

Investigation workflow helper.

**Usage:**
```bash
empirica investigate --type auto --context '{"topic": "OAuth"}' --detailed
```

**See also:** check

---

### decision

Decision point tracking.

**Usage:**
```bash
empirica decision <command> [options]
```

**See also:** check

---

## Developer/Debug Tools

### performance

Performance analysis or benchmarks.

**Usage:**
```bash
# Run benchmarks
empirica performance --benchmark --iterations 10

# Analyze performance
empirica performance --target system --detailed
```

**See also:** monitor

---

### component

Component analysis.

**Usage:**
```bash
empirica component <command> [options]
```

**Developer tool** for analyzing Empirica components

---

### monitor

Real-time monitoring (experimental).

**Usage:**
```bash
empirica monitor [options]
```

**Status:** Experimental

---

## Common Workflows

### Workflow 1: First Session (Minimal)

```bash
# 1. Create session
SESSION_ID=$(empirica session-create /tmp/session.json | jq -r '.session_id')

# 2. PREFLIGHT
empirica preflight-submit /tmp/preflight.json

# 3. Work...

# 4. POSTFLIGHT
empirica postflight-submit /tmp/postflight.json
```

### Workflow 2: With Goals

```bash
# 1. Create session + PREFLIGHT
SESSION_ID=$(empirica session-create /tmp/session.json | jq -r '.session_id')
empirica preflight-submit /tmp/preflight.json

# 2. Create goal
GOAL_ID=$(empirica goals-create /tmp/goal.json | jq -r '.goal_id')

# 3. Add subtasks
empirica goals-add-subtask /tmp/subtask1.json
empirica goals-add-subtask /tmp/subtask2.json

# 4. Work on subtasks, log findings
empirica finding-log /tmp/finding1.json
empirica finding-log /tmp/finding2.json

# 5. Complete subtasks
empirica goals-complete-subtask /tmp/complete1.json
empirica goals-complete-subtask /tmp/complete2.json

# 6. CHECK (if uncertain)
empirica check /tmp/check.json

# 7. POSTFLIGHT
empirica postflight-submit /tmp/postflight.json
```

### Workflow 3: With Epistemic Learning (Qdrant)

```bash
# Before starting new work, search past learning
empirica epistemics-search \
  --project-id <uuid> \
  --query "OAuth2 implementation" \
  --min-learning 0.2 \
  --output json

# Bootstrap project context
empirica project-bootstrap --project-id <uuid> --output json

# Do your work...

# Log findings for future semantic search
empirica finding-log /tmp/finding.json

# After POSTFLIGHT, trajectory is auto-indexed in Qdrant
```

### Workflow 4: Multi-AI Handoff

```bash
# AI 1 (Claude): Finish work
empirica handoff-create /tmp/handoff.json

# AI 2 (Qwen): Discover and resume
empirica goals-discover --from-ai-id claude-code --output json
empirica goals-resume /tmp/resume.json
```

---

## Session ID Aliases

**For convenience, use aliases instead of UUIDs:**

- `latest:active:<ai-id>` - Most recent active session
- `latest:any:<ai-id>` - Most recent session (any status)
- `<uuid>` - Specific session UUID

**Example:**
```bash
empirica sessions-show latest:active:claude-code
```

---

## Output Formats

**All commands support `--output json` for programmatic use:**

```bash
empirica <command> --output json | jq '.result'
```

**Human-readable output available** with `--output human` (default for some commands)

---

## Configuration

**AI-first JSON mode:** All commands accept JSON config files to avoid shell quoting issues.

**Pattern:**
```bash
cat > /tmp/config.json << 'EOF'
{
  "parameter": "value",
  "nested": {"key": "value"}
}
EOF

empirica <command> /tmp/config.json
```

**Environment variables:**
- `EMPIRICA_DB_TYPE` - Database type (sqlite, postgresql)
- `EMPIRICA_DB_HOST` - PostgreSQL host
- `QDRANT_URL` - Qdrant server URL
- `OPENAI_API_KEY` - For embeddings

**See also:** config, project-init

---

## Dependencies Summary

| Command Category | Dependencies |
|------------------|--------------|
| **Core workflow** | SQLite only (zero deps) |
| **Epistemic learning** | Qdrant + OpenAI API |
| **Multi-AI** | Git notes |
| **Cryptographic trust** | Ed25519 keypair |
| **Vision** | Vision model (optional) |
| **Skills** | Skills defined |
| **PostgreSQL** | PostgreSQL server (optional) |

---

## See Also

- **Architecture:** `docs/architecture/QDRANT_EPISTEMIC_INTEGRATION.md`
- **Database:** `docs/guides/DATABASE_MIGRATION.md`
- **MCP Tools:** `docs/reference/MCP_CLI_MAPPING.md`
- **Python API:** `docs/reference/PYTHON_API.md`

---

**Questions?** Use `empirica ask "your question"` to query this documentation semantically.
