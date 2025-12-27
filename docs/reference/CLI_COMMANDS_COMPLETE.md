# CLI Commands - Complete Reference

**Empirica v4.0 - All 74 Commands**

**Date:** 2025-12-25
**Status:** Production-ready

---

## Table of Contents

1. [Session Management (7 commands)](#session-management)
2. [CASCADE Workflow (7 commands)](#cascade-workflow)
3. [Goals & Subtasks (8 commands)](#goals--subtasks)
4. [Checkpoints & Git (7 commands)](#checkpoints--git)
5. [Handoff Reports (2 commands)](#handoff-reports)
6. [Identity & Signing (4 commands)](#identity--signing)
7. [Investigation & Actions (3 commands)](#investigation--actions)
8. [Configuration & Profiles (5 commands)](#configuration--profiles)
9. [Monitoring & Performance (2 commands)](#monitoring--performance)
10. [User Interface (3 commands)](#user-interface)
11. [Utility Commands (1 command)](#utility-commands)

**Total: 74 commands**

---

## Session Management

### 1. `session-create`

Create new Empirica session.

```bash
empirica session-create --ai-id myai
empirica session-create --ai-id myai --bootstrap-level 1 --output json
```

**Options:**
- `--ai-id` (required): AI agent identifier
- `--user-id`: User identifier (optional)
- `--bootstrap-level`: Bootstrap level 0-4 (default: 1, legacy parameter)
- `--output`: Output format (default | json)

**Returns:** Session UUID

---

### 2. `sessions-list`

List all sessions.

```bash
empirica sessions-list
empirica sessions-list --limit 10 --output json
```

**Options:**
- `--limit`: Max sessions to show (default: 50)
- `--verbose`: Show detailed info
- `--output`: Output format (text | json)

---

### 3. `sessions-show`

Show detailed session information.

```bash
empirica sessions-show <SESSION_ID>
empirica sessions-show latest
empirica sessions-show latest:myai
empirica sessions-show --session-id <ID> --verbose --output json
```

**Positional:**
- `session_id`: Session ID or alias (latest, latest:active, latest:<ai_id>)

**Options:**
- `--session-id`: Alternative to positional argument
- `--verbose`: Show all vectors and cascades
- `--output`: Output format (text | json)

---

### 4. `sessions-export`

Export session to JSON file.

```bash
empirica sessions-export <SESSION_ID>
empirica sessions-export latest --output session.json
```

**Positional:**
- `session_id`: Session ID or alias

**Options:**
- `--output, -o`: Output file path (default: session_<id>.json)

---

### 5. `sessions-resume`

Resume previous sessions.

```bash
empirica sessions-resume --ai-id myai --count 3
empirica sessions-resume --ai-id myai --detail-level full --output json
```

**Options:**
- `--ai-id`: Filter by AI ID
- `--count`: Number of sessions (default: 1)
- `--detail-level`: summary | detailed | full (default: summary)
- `--output`: Output format (default | json)

---

### 6. `workflow`

Execute full PREFLIGHT→work→POSTFLIGHT workflow.

```bash
empirica workflow "Implement OAuth2 flow"
empirica workflow "Task description" --auto --verbose
```

**Positional:**
- `prompt`: Task description

**Options:**
- `--auto`: Skip manual pause between steps
- `--verbose`: Show detailed workflow steps

---

### 7. `goal-analysis`

Analyze goal feasibility.

```bash
empirica goal-analysis "Implement OAuth2 authorization"
empirica goal-analysis "Task" --context '{"domain": "security"}' --verbose
```

**Positional:**
- `goal`: Goal to analyze

**Options:**
- `--context`: JSON context data
- `--verbose`: Show detailed analysis

---

## CASCADE Workflow

### 8. `preflight`

Execute PREFLIGHT epistemic assessment.

```bash
# Generate self-assessment prompt
empirica preflight "Implement OAuth2 flow" --prompt-only --output json

# Submit assessment (after genuine AI self-assessment)
empirica preflight "Task" --assessment-json '{"vectors": {...}, "reasoning": "..."}'
```

**Positional:**
- `prompt`: Task description

**Options:**
- `--session-id`: Session ID (auto-generated if not provided)
- `--ai-id`: AI identifier (default: empirica_cli)
- `--prompt-only`: Return ONLY self-assessment prompt (for genuine AI assessment)
- `--assessment-json`: Submit genuine AI self-assessment
- `--no-git`: Disable automatic git checkpoint
- `--sign`: Sign assessment with AI keypair (Phase 2)
- `--output`: Output format (default | json)
- `--quiet`: Quiet mode (requires --assessment-json)

---

### 9. `preflight-submit`

Submit PREFLIGHT assessment results.

```bash
empirica preflight-submit \
  --session-id <ID> \
  --vectors '{"engagement":0.8,"know":0.6,...}' \
  --reasoning "Starting with moderate knowledge"
```

**Options:**
- `--session-id` (required): Session ID
- `--vectors` (required): 13 epistemic vectors as JSON
- `--reasoning`: Why you scored yourself this way
- `--output`: Output format (default | json)

---

### 10. `check`

Execute CHECK phase (decision gate).

```bash
empirica check \
  --session-id <ID> \
  --findings '["Found OAuth2 endpoints", "Token TTL is 3600s"]' \
  --unknowns '["Refresh token rotation unclear"]' \
  --confidence 0.85
```

**Options:**
- `--session-id` (required): Session ID
- `--findings` (required): Investigation findings as JSON array
- `--unknowns` (required): Remaining unknowns as JSON array
- `--remaining-unknowns`: Alias for --unknowns
- `--confidence` (required): Confidence score (0.0-1.0)
- `--output`: Output format (default | json)
- `--verbose`: Show detailed analysis

---

### 11. `check-submit`

Submit CHECK assessment results.

```bash
empirica check-submit \
  --session-id <ID> \
  --vectors '{"know":0.75,"uncertainty":0.35,...}' \
  --decision proceed \
  --reasoning "Sufficient understanding to proceed"
```

**Options:**
- `--session-id` (required): Session ID
- `--vectors` (required): 13 epistemic vectors as JSON
- `--decision` (required): proceed | investigate | proceed_with_caution
- `--reasoning`: Why this decision
- `--cycle`: Investigation cycle number
- `--output`: Output format (default | json)

---

### 12. `postflight`

Execute POSTFLIGHT assessment.

```bash
# Generate self-assessment prompt
empirica postflight <SESSION_ID> --prompt-only --output json

# Submit assessment
empirica postflight <SESSION_ID> --assessment-json '{"vectors": {...}, "reasoning": "..."}'
```

**Positional:**
- `session_id`: Session ID from PREFLIGHT

**Options:**
- `--summary`: Task completion summary
- `--ai-id`: AI identifier (should match PREFLIGHT)
- `--prompt-only`: Return ONLY self-assessment prompt
- `--assessment-json`: Submit genuine AI self-assessment
- `--no-git`: Disable automatic git checkpoint
- `--sign`: Sign assessment
- `--output`: Output format (default | json)
- `--quiet`: Quiet mode

---

### 13. `postflight-submit`

Submit POSTFLIGHT assessment results.

```bash
empirica postflight-submit \
  --session-id <ID> \
  --vectors '{"engagement":0.9,"know":0.85,...}' \
  --reasoning "Successfully implemented OAuth2, learned X"
```

**Options:**
- `--session-id` (required): Session ID
- `--vectors` (required): 13 epistemic vectors as JSON
- `--reasoning`: What changed from PREFLIGHT (description of learning)
- `--changes`: Alias for --reasoning (deprecated)
- `--output`: Output format (default | json)

---

### 14. `investigate`

Investigate file/directory/concept.

```bash
empirica investigate src/auth/oauth.py
empirica investigate src/ --type comprehensive
empirica investigate "OAuth2 patterns" --type concept --verbose
```

**Positional:**
- `target`: File, directory, or concept to investigate

**Options:**
- `--type`: auto | file | directory | concept | comprehensive (default: auto)
- `--context`: JSON context data
- `--detailed`: Show detailed investigation
- `--verbose`: Show detailed investigation

**Note:** Use `--type comprehensive` for deep analysis (replaces deprecated `analyze` command).

---

## Goals & Subtasks

### 15. `goals-create`

Create new goal.

```bash
empirica goals-create \
  --session-id <ID> \
  --objective "Investigate OAuth2 implementation" \
  --scope-breadth 0.6 \
  --scope-duration 0.4 \
  --scope-coordination 0.1
```

**Options:**
- `--session-id` (required): Session ID
- `--ai-id`: AI identifier (default: empirica_cli)
- `--objective` (required): Goal objective text
- `--scope-breadth`: Goal breadth (0.0-1.0, default: 0.3)
- `--scope-duration`: Goal duration (0.0-1.0, default: 0.2)
- `--scope-coordination`: Multi-agent coordination (0.0-1.0, default: 0.1)
- `--success-criteria`: Success criteria as JSON array
- `--estimated-complexity`: Complexity estimate (0.0-1.0)
- `--constraints`: Constraints as JSON object
- `--metadata`: Metadata as JSON object
- `--output`: Output format (default | json)

**Scope Vectors:**
- `breadth`: How wide (0.1 = single file, 0.9 = entire system)
- `duration`: Expected lifetime (0.1 = 1 hour, 0.9 = weeks)
- `coordination`: Multi-agent coordination (0.1 = solo, 0.9 = orchestrated)

---

### 16. `goals-add-subtask`

Add subtask to existing goal.

```bash
empirica goals-add-subtask \
  --goal-id <GOAL_ID> \
  --description "Map OAuth2 endpoints" \
  --importance high
```

**Options:**
- `--goal-id` (required): Goal UUID
- `--description` (required): Subtask description
- `--importance`: critical | high | medium | low (default: medium)
- `--dependencies`: Dependencies as JSON array
- `--estimated-tokens`: Estimated token usage
- `--output`: Output format (default | json)

---

### 17. `goals-complete-subtask`

Mark subtask as complete.

```bash
empirica goals-complete-subtask \
  --task-id <SUBTASK_ID> \
  --evidence "Commit abc123: Documented OAuth2 endpoints"
```

**Options:**
- `--task-id` (required): Subtask UUID
- `--evidence`: Completion evidence (commit hash, file path, etc.)
- `--output`: Output format (default | json)

---

### 18. `goals-progress`

Get goal completion progress.

```bash
empirica goals-progress --goal-id <GOAL_ID>
empirica goals-progress --goal-id <ID> --output json
```

**Options:**
- `--goal-id` (required): Goal UUID
- `--output`: Output format (default | json)

---

### 19. `goals-list`

List goals.

```bash
empirica goals-list
empirica goals-list --session-id <ID>
empirica goals-list --scope-breadth-min 0.5 --completed
```

**Options:**
- `--session-id`: Filter by session ID
- `--scope-breadth-min`: Filter by minimum breadth (0.0-1.0)
- `--scope-breadth-max`: Filter by maximum breadth (0.0-1.0)
- `--scope-duration-min`: Filter by minimum duration (0.0-1.0)
- `--scope-duration-max`: Filter by maximum duration (0.0-1.0)
- `--scope-coordination-min`: Filter by minimum coordination (0.0-1.0)
- `--scope-coordination-max`: Filter by maximum coordination (0.0-1.0)
- `--completed`: Filter by completion status
- `--output`: Output format (default | json)

---

### 20. `goals-discover`

Discover goals from other AIs via git.

```bash
empirica goals-discover
empirica goals-discover --from-ai-id otherai --output json
```

**Options:**
- `--from-ai-id`: Filter by AI creator
- `--session-id`: Filter by session
- `--output`: Output format (default | json)

**Use case:** Cross-AI collaboration (Phase 1)

---

### 21. `goals-resume`

Resume another AI's goal.

```bash
empirica goals-resume <GOAL_ID> --ai-id myai
```

**Positional:**
- `goal_id`: Goal ID to resume

**Options:**
- `--ai-id`: Your AI identifier (default: empirica_cli)
- `--output`: Output format (default | json)

**Use case:** Cross-AI goal handoff (Phase 1)

---

### 22. `investigate-log`

Log investigation findings during INVESTIGATE phase.

```bash
empirica investigate-log \
  --session-id <ID> \
  --findings '["Found OAuth2 endpoints", "Token TTL is 3600s"]' \
  --evidence '{"files": ["src/auth/oauth.py"], "lines": [42, 56]}'
```

**Options:**
- `--session-id` (required): Session ID
- `--findings` (required): JSON array of findings
- `--evidence`: JSON object with evidence (file paths, line numbers, etc.)
- `--verbose`: Verbose output

---

## Project Embeddings (Qdrant)

Build semantic vectors for documentation and epistemic memory.

```bash
empirica project-embed \
  --project-id <UUID> \
  [--output json]
```

Options:
- --project-id: Project identifier
- --output: default|json

ENV:
- EMPIRICA_QDRANT_URL: Qdrant service URL (e.g., http://localhost:6333)
- EMPIRICA_EMBEDDINGS_PROVIDER: openai|local (default: local for dev)
- EMPIRICA_EMBEDDINGS_MODEL: embedding model (e.g., text-embedding-3-small)
- OPENAI_API_KEY: required if provider=openai

## Project Semantic Search

Search for relevant docs/memory by task description.

```bash
empirica project-search \
  --project-id <UUID> \
  --task "Implement JWT refresh" \
  [--type all|docs|memory] \
  [--limit 5] \
  [--output json]
```

Options:
- --project-id: Project identifier
- --task: Task description (free text)
- --type: all (default), docs, or memory
- --limit: number of results (default: 5)
- --output: default|json

## Checkpoints & Git

### 23. `checkpoint-create`

Create git checkpoint for session.

```bash
empirica checkpoint-create \
  --session-id <ID> \
  --phase PREFLIGHT \
  --round 1
```

**Options:**
- `--session-id` (required): Session ID
- `--phase` (required): PREFLIGHT | CHECK | ACT | POSTFLIGHT
- `--round` (required): Round number
- `--metadata`: JSON metadata (optional)

---

### 24. `checkpoint-load`

Load latest checkpoint for session.

```bash
empirica checkpoint-load --session-id <ID>
empirica checkpoint-load --session-id <ID> --phase CHECK --output json
```

**Options:**
- `--session-id` (required): Session ID
- `--max-age`: Max age in hours (default: 24)
- `--phase`: Filter by specific phase
- `--output`: Output format (table | json)
- `--format`: Alias for --output (deprecated)

---

### 25. `checkpoint-list`

List checkpoints for session.

```bash
empirica checkpoint-list
empirica checkpoint-list --session-id <ID> --limit 5
```

**Options:**
- `--session-id`: Session ID (lists all if omitted)
- `--limit`: Max checkpoints (default: 10)
- `--phase`: Filter by phase

---

### 26. `checkpoint-diff`

Show vector differences from last checkpoint.

```bash
empirica checkpoint-diff --session-id <ID>
empirica checkpoint-diff --session-id <ID> --threshold 0.2 --output json
```

**Options:**
- `--session-id` (required): Session ID
- `--threshold`: Significance threshold (default: 0.15)
- `--output`: Output format (default | json)

---

### 27. `checkpoint-sign`

Sign checkpoint with AI identity (Phase 2 - Crypto).

```bash
empirica checkpoint-sign \
  --session-id <ID> \
  --phase PREFLIGHT \
  --round 1 \
  --ai-id myai
```

**Options:**
- `--session-id` (required): Session ID
- `--phase` (required): PREFLIGHT | CHECK | ACT | POSTFLIGHT
- `--round` (required): Round number
- `--ai-id` (required): AI identity to sign with
- `--output`: Output format (default | json)

---

### 28. `checkpoint-verify`

Verify signed checkpoint (Phase 2 - Crypto).

```bash
empirica checkpoint-verify \
  --session-id <ID> \
  --phase PREFLIGHT \
  --round 1
```

**Options:**
- `--session-id` (required): Session ID
- `--phase` (required): PREFLIGHT | CHECK | ACT | POSTFLIGHT
- `--round` (required): Round number
- `--ai-id`: AI identity (uses embedded public key if omitted)
- `--public-key`: Public key hex (overrides AI ID)
- `--output`: Output format (default | json)

---

### 29. `checkpoint-signatures`

List all signed checkpoints (Phase 2 - Crypto).

```bash
empirica checkpoint-signatures
empirica checkpoint-signatures --session-id <ID> --output json
```

**Options:**
- `--session-id`: Filter by session ID
- `--ai-id`: AI identity (only if no local identities exist)
- `--output`: Output format (default | json)

---

## Handoff Reports

### 30. `handoff-create`

Create handoff report for session continuity and multi-agent coordination.

**Handoff Types:** Auto-detects type based on CASCADE assessments (investigation/complete/planning). See [`../guides/FLEXIBLE_HANDOFF_GUIDE.md`](../guides/FLEXIBLE_HANDOFF_GUIDE.md) for details.

```bash
# Complete handoff (PREFLIGHT → POSTFLIGHT)
empirica handoff-create \
  --session-id <ID> \
  --task-summary "Implemented OAuth2 flow" \
  --key-findings '["Flow complete", "All edge cases handled"]' \
  --remaining-unknowns '["Rate limiting unclear"]' \
  --next-session-context "Ready to implement rate limiting"

# Investigation handoff (PREFLIGHT → CHECK) for specialist handoff
empirica handoff-create \
  --session-id <ID> \
  --task-summary "Investigated OAuth2 security patterns" \
  --key-findings '["PKCE required", "Token rotation needed"]' \
  --next-session-context "Ready for implementation by specialist"

# Planning handoff (no CASCADE required)
empirica handoff-create \
  --session-id <ID> \
  --task-summary "Planned OAuth2 approach" \
  --key-findings '["Chose PKCE flow"]' \
  --next-session-context "Begin implementation" \
  --planning-only
```

**Options:**
- `--session-id` (required): Session UUID
- `--task-summary` (required): What was accomplished (2-3 sentences)
- `--summary`: Alias for --task-summary
- `--key-findings` (required): JSON array of findings
- `--findings`: Alias for --key-findings
- `--remaining-unknowns`: JSON array of unknowns
- `--unknowns`: Alias for --remaining-unknowns
- `--next-session-context` (required): Critical context for next session
- `--artifacts`: JSON array of files created
- `--planning-only`: Create planning handoff (no CASCADE required)
- `--output`: Output format (text | json)

---

### 31. `handoff-query`

Query handoff reports.

```bash
empirica handoff-query --session-id <ID>
empirica handoff-query --ai-id myai --limit 5 --output json
```

**Options:**
- `--session-id`: Specific session UUID
- `--ai-id`: Filter by AI ID
- `--limit`: Number of results (default: 5)
- `--output`: Output format (text | json)

---

## Identity & Signing

### 32. `identity-create`

Create new AI identity with Ed25519 keypair (Phase 2).

```bash
empirica identity-create --ai-id myai
empirica identity-create --ai-id myai --overwrite
```

**Options:**
- `--ai-id` (required): AI identifier
- `--overwrite`: Overwrite existing identity
- `--output`: Output format (default | json)

---

### 33. `identity-list`

List all AI identities.

```bash
empirica identity-list
empirica identity-list --output json
```

**Options:**
- `--output`: Output format (default | json)

---

### 34. `identity-export`

Export public key for sharing.

```bash
empirica identity-export --ai-id myai
empirica identity-export --ai-id myai --output json
```

**Options:**
- `--ai-id` (required): AI identifier
- `--output`: Output format (default | json)

---

### 35. `identity-verify`

Verify signed session.

```bash
empirica identity-verify <SESSION_ID>
empirica identity-verify <ID> --output json
```

**Positional:**
- `session_id`: Session ID to verify

**Options:**
- `--output`: Output format (default | json)

---

## Investigation & Actions

### 36. `act-log`

Log actions taken during ACT phase.

```bash
empirica act-log \
  --session-id <ID> \
  --actions '["Implemented OAuth2", "Added token validation"]' \
  --artifacts '["src/auth/oauth.py", "tests/test_oauth.py"]' \
  --goal-id <GOAL_ID>
```

**Options:**
- `--session-id` (required): Session ID
- `--actions` (required): JSON array of actions taken
- `--artifacts`: JSON array of files modified/created
- `--goal-id`: Goal UUID being worked on
- `--verbose`: Verbose output

---

### 37. `efficiency-report`

Generate token efficiency report (Phase 1.5/2.0).

```bash
empirica efficiency-report --session-id <ID>
empirica efficiency-report --session-id <ID> --format markdown --output report.md
```

**Options:**
- `--session-id` (required): Session ID
- `--format`: json | markdown | csv (default: markdown)
- `--output, -o`: Save to file (optional)

---

### 38. `performance`

Analyze performance or run benchmarks.

```bash
empirica performance
empirica performance --benchmark --iterations 100
empirica performance --target system --verbose
```

**Options:**
- `--benchmark`: Run performance benchmarks
- `--target`: Performance analysis target (default: system)
- `--type`: Benchmark/analysis type (default: comprehensive)
- `--iterations`: Number of iterations for benchmarks (default: 10)
- `--memory`: Include memory analysis (default: true)
- `--context`: JSON context data
- `--detailed`: Show detailed metrics
- `--verbose`: Show detailed results

---

## Configuration & Profiles

### 39. `config`

Configuration management (unified command).

```bash
# Show all config
empirica config

# Initialize config
empirica config --init

# Validate config
empirica config --validate

# Get specific key
empirica config routing.default_strategy

# Set specific key
empirica config routing.default_strategy epistemic
```

**Positional:**
- `key`: Configuration key (dot notation)
- `value`: Value to set (if key provided)

**Options:**
- `--init`: Initialize configuration
- `--validate`: Validate configuration
- `--section`: Show specific section (routing, adapters, etc.)
- `--format`: Output format (yaml | json, default: yaml)
- `--force`: Overwrite existing config (with --init)
- `--verbose`: Show detailed output

---

### 40. `identity-create`

Create Ed25519 keypair for AI identity.

```bash
empirica identity-create --ai-id myai
empirica identity-create --ai-id myai --overwrite
```

**Options:**
- `--ai-id`: AI agent identifier
- `--overwrite`: Overwrite existing identity

**Output:**
- Public key stored in `.empirica/identities/`
- Private key stored securely

---

### 41. `identity-list`

List all AI identities.

```bash
empirica identity-list
```

**Output:**
- AI identifiers with public key fingerprints

---

### 42. `identity-export`

Export public key for sharing.

```bash
empirica identity-export --ai-id myai
```

**Output:**
- Public key in base64 format

---

### 43. `identity-verify`

Verify signed session.

```bash
empirica identity-verify --session-id <SESSION_ID>
```

**Output:**
- Signature verification result
- Signer identity

---

## Monitoring & Performance

### 44. `monitor`

Monitoring dashboard and statistics.

```bash
# Show dashboard
empirica monitor

# Export data
empirica monitor --export monitor_data.json

# Reset statistics
empirica monitor --reset --yes

# Cost analysis
empirica monitor --cost --project
```

**Options:**
- `--export FILE`: Export data to file
- `--reset`: Reset statistics
- `--cost`: Show cost analysis
- `--history`: Show recent request history
- `--health`: Include adapter health checks
- `--project`: Show cost projections (with --cost)
- `--format`: Export format (json | csv, default: json)
- `--yes, -y`: Skip confirmation (with --reset)
- `--verbose`: Show detailed stats

---

## User Interface

### 45. `onboard`

Interactive introduction to Empirica.

```bash
empirica onboard
```

**No options** - Interactive walkthrough

---

### 46. `ask`

Ask a question (simple query interface).

```bash
empirica ask "What is OAuth2?"
empirica ask "Explain PKCE flow" --adapter qwen --strategy epistemic
```

**Positional:**
- `query`: Question to ask

**Options:**
- `--adapter`: Force specific adapter (qwen, minimax, gemini, etc.)
- `--model`: Force specific model (e.g., qwen-coder-turbo)
- `--strategy`: Routing strategy (epistemic | cost | latency | quality | balanced, default: epistemic)
- `--session`: Session ID for conversation tracking
- `--temperature`: Sampling temperature (0.0-1.0, default: 0.7)
- `--max-tokens`: Maximum response tokens (default: 2000)
- `--no-save`: Don't save to session database
- `--verbose`: Show routing details

---

### 47. `chat`

Interactive chat session (REPL).

```bash
empirica chat
empirica chat --adapter gemini --strategy balanced
empirica chat --resume <SESSION_ID>
```

**Options:**
- `--adapter`: Force specific adapter
- `--model`: Force specific model
- `--strategy`: Routing strategy (default: epistemic)
- `--session`: Session ID (creates new if doesn't exist)
- `--resume`: Resume existing session by ID
- `--no-save`: Don't save conversation
- `--verbose`: Show routing details

---

## Utility Commands

### 48-49. Deprecated/Removed Commands

The following commands have been consolidated or removed:

**Removed:**
- `analyze` → Use `investigate --type comprehensive`
- `benchmark` → Use `performance --benchmark`
- `session-end` → Use `handoff-create`
- `config-init`, `config-show`, `config-validate`, `config-get`, `config-set` → Use unified `config`
- `monitor-export`, `monitor-reset`, `monitor-cost` → Use unified `monitor` with flags
- All MCP server commands (`mcp-start`, `mcp-stop`, etc.) → IDE/CLI manages MCP lifecycle

---

## Command Categories Summary

| Category | Commands |
|----------|----------|
| Session Management | 7 |
| CASCADE Workflow | 7 |
| Goals & Subtasks | 8 |
| Checkpoints & Git | 7 |
| Handoff Reports | 2 |
| Identity & Signing | 4 |
| Investigation & Actions | 3 |
| Configuration & Profiles | 5 |
| Monitoring & Performance | 2 |
| User Interface | 3 |
| **Total** | **49** |

---

## Quick Start Examples

```bash
# 1. Create session
empirica session-create --ai-id myai --output json

# 2. PREFLIGHT
empirica preflight "Implement OAuth2" --prompt-only --output json
# (AI performs genuine self-assessment)
empirica preflight-submit --session-id <ID> --vectors '{...}' --reasoning "..."

# 3. Create goal (if high uncertainty)
empirica goals-create --session-id <ID> --objective "..." --scope-breadth 0.6 --scope-duration 0.4

# 4. CHECK phase
empirica check --session-id <ID> --findings '[...]' --unknowns '[...]' --confidence 0.85
empirica check-submit --session-id <ID> --vectors '{...}' --decision proceed

# 5. ACT phase (do work)
empirica act-log --session-id <ID> --actions '[...]' --artifacts '[...]'

# 6. POSTFLIGHT
empirica postflight <ID> --prompt-only --output json
empirica postflight-submit --session-id <ID> --vectors '{...}' --reasoning "..."

# 7. Handoff
empirica handoff-create --session-id <ID> --task-summary "..." --key-findings '[...]' --next-session-context "..."

# 8. Query handoff
empirica handoff-query --session-id <ID> --output json
```

---

**Generated:** 2025-12-08  
**Version:** Empirica v4.0  
**Documentation Coverage:** 100% (49/49 commands)
