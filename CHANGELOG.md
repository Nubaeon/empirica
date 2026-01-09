# Changelog

All notable changes to Empirica will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-01-09

### Added
- **Multi-Agent Epistemic Investigation** - Spawn parallel investigation agents with different personas to explore codebase corners:
  ```bash
  empirica agent-spawn --session-id <ID> --task "..." --turtle
  ```
  Features:
  - Automatic persona selection with `--turtle` flag
  - Parallel branch execution with POSTFLIGHT aggregation
  - Findings/unknowns automatically logged to parent session

- **Onboarding Projects** - Two complete mini-projects for learning Empirica workflows:
  - `api-explorer/` - Discovery exercise with intentionally incomplete API docs
  - `refactor-decision/` - Decision-making exercise with multiple valid approaches
  - Each includes WALKTHROUGH.md and SOLUTION.md for guided learning

### Changed
- **Documentation Accuracy Audit** - Comprehensive updates via multi-agent investigation:
  - DATABASE_SCHEMA_UNIFIED.md: Updated from 19 to 31 tables (added Session Breadcrumbs, Lessons System, Infrastructure sections)
  - MCP_SERVER_REFERENCE.md: Updated tool count from 40 to 57 tools
  - Added cross-references between Sentinel, CASCADE, and Noetic/Praxic docs
  - Added navigation table to CONFIGURATION_REFERENCE.md for end-users
  - Added cross-references to storage architecture and Qdrant integration docs

### Fixed
- **Version Consistency** - Synchronized version numbers across all package files:
  - pyproject.toml, empirica/__init__.py, empirica-mcp/pyproject.toml, chocolatey/empirica.nuspec

## [1.2.4] - 2026-01-06

### Added
- **project-switch Command** - New command for AI agents to switch between projects with clear context banner and automatic bootstrap loading.
  ```bash
  empirica project-switch <project-name-or-id>
  ```
  Features:
  - Resolves projects by name (case-insensitive) or UUID
  - Shows "you are here" context banner with project details
  - Automatically runs project-bootstrap for context loading
  - Displays project status (sessions, flow state, health)
  - Shows next steps (session-create, goals-ready)
  - JSON output support for programmatic use

### Fixed

1. **check-submit Vector Format Handling** - Added robust vector normalization to handle multiple input formats:
   - Flat dictionary: `{engagement: 0.85, know: 0.75, ...}`
   - Structured dictionary: `{foundation: {know, do, context}, comprehension: {...}, execution: {...}}`
   - Wrapped dictionary: `{vectors: {...}}`
   - JSON string inputs (AI-first mode)
   
   Fixes "Vectors must be a dictionary" errors when using structured CASCADE format.
   
2. **agent-spawn Persona Schema Validation** - Fixed validation errors for persona records:
   - PersonaManager.load_persona() now normalizes public_key to valid Ed25519 format (64 hex chars)
   - Auto-fills missing focus_domains with `['general']` for backward compatibility
   - Default persona in epistemic_agent.py now includes focus_domains
   
   Fixes "public_key 'scout_key_placeholder' invalid" and "focus_domains is required property" errors.
   
3. **Findings/Unknowns/Dead-ends Duplication** - Fixed duplicate breadcrumbs in project-bootstrap output:
   - Changed `UNION ALL` to `UNION` in 8 queries across breadcrumbs.py (get_project_findings, get_project_unknowns, get_project_dead_ends)
   - When scope='both', findings were written to both session_findings and project_findings tables
   - UNION automatically deduplicates while preserving dual-scope architecture

### Changed
- docs/PROJECT_SWITCHING_FOR_AIS.md: Updated status from "CRITICAL" to "IMPLEMENTED" with completed checklist items

### Tests
- Added 4 new tests for project-switch command (all passing)
- Total: 281 tests passing

## [1.2.3] - 2026-01-02

### Added
- **Epistemic Release Agent** (`empirica release-ready`) - Pre-release verification command with epistemic principles:
  - Version sync check across pyproject.toml, __init__.py, CLAUDE.md prompt version
  - Architecture turtle assessment on core/, cli/, data/ directories
  - PyPI package verification for empirica and empirica-mcp
  - Privacy/security scan for secrets, credentials, and dev files
  - Documentation completeness check (README, CHANGELOG, docs/)
  - Git status verification (branch, uncommitted changes, unpushed commits)
  - Respects .gitignore patterns - only flags items NOT covered by gitignore
  - Moon phase indicators (🌕🌔🌓🌒🌑) for visual status
  - JSON output for CI/automation (`--output json`)
  - Quick mode (`--quick`) to skip architecture assessment

### Fixed
- **Issue Resolution Bug** - `issue-resolve` command was filtering by session_id, preventing resolution of issues from different sessions. Removed session_id constraint from WHERE clause.
- **Goal Completion Bug** - `goals-complete` command returned success but never updated goal status in database. Added missing UPDATE statement to set status='completed'.
- **Ollama Auto-Detection** - Embeddings now auto-detect Ollama availability and use semantic embeddings when available, falling back to local hash when not.
- **Sentinel Auto-Enable** - Sentinel now auto-enables with default epistemic evaluator on module load, appearing in CASCADE responses.

### Changed
- Added `.beads/` and `*.pem` to .gitignore for security
- Reorganized .gitignore with "Security-sensitive files" section

## [1.1.3] - 2025-12-29

### Fixed
- **Flow State Display Slice Error** - Fixed TypeError in project-bootstrap command where flow_data was incorrectly treated as a list when it's actually a dictionary. Changed to properly access flow_metrics['flow_scores']. This was causing "slice(None, 5, None)" error messages in bootstrap output.
- **Missing Flow Metrics Components** - Added 'components' and 'recommendations' fields to flow metrics data structure. Components now show weighted breakdown of flow score factors (engagement, capability, clarity, etc.), and recommendations are generated from identify_flow_blockers().

### Added
- **Auto-Capture Logging Hooks** - Implemented true automatic error capture via Python's logging system:
  - Added `AutoCaptureLoggingHandler` class that hooks into logging.ERROR and logging.CRITICAL
  - Added `install_auto_capture_hooks()` function that installs both logging.Handler and sys.excepthook
  - Integrated into session creation - errors are now captured automatically during CLI execution
  - Captures context (logger name, module, function, line number) for better debugging
  - Non-blocking design - capture errors don't break the application
- Auto-capture now truly "auto" - no explicit calls needed, errors logged anywhere in codebase are captured

### Verified
- JSON output working correctly for project-bootstrap and session-snapshot commands
- Cross-project isolation confirmed with 15 projects
- Dynamic context loading via --depth parameter (minimal/moderate/full/auto)
- Session-optional commands working as documented
- Learning delta calculation accurate in session snapshots

## [1.1.2] - 2025-12-29

### Fixed
- **CRITICAL: Schema/API Mismatch in Epistemic Artifacts** - BreadcrumbRepository methods (log_finding, log_unknown, log_dead_end) expected schema columns that were missing from database definitions:
  - Added `subject TEXT` to project_findings table
  - Added `impact REAL DEFAULT 0.5` to project_findings table
  - Added `subject TEXT` to project_unknowns table
  - Added `impact REAL DEFAULT 0.5` to project_unknowns table
  - Added `subject TEXT` to project_dead_ends table
  - Added `impact REAL DEFAULT 0.5` to project_dead_ends table
- Impact: Users following system prompt documentation would get immediate SQLite errors when trying to use epistemic artifact tracking
- Testing: Verified with fresh project initialization - all epistemic tracking APIs now work correctly
- This fix enables proper meta-tracking of complex multi-channel projects (e.g., outreach campaigns)

## [1.1.1] - 2025-12-29

### Fixed
- **CRITICAL: CHECK GATE confidence threshold bug** - The CHECK command was ignoring explicit confidence values provided by AI agents and instead calculating confidence from uncertainty vectors (1.0 - uncertainty). This prevented the proper enforcement of the ≥0.70 confidence threshold for the CASCADE GATE. Fixed by:
  - Extracting `explicit_confidence` from CHECK input config
  - Using explicit confidence in decision logic when provided
  - Making proceed/investigate decision based on confidence ≥ 0.70 threshold as per system design
  - Keeping drift and unknowns as secondary evidence validation
- **Impact**: All users now have a properly functioning CHECK GATE that respects stated confidence while validating against evidence

## [1.1.0] - 2025-12-28

### Added
- **Version 1.1.0 Release** - Fixed version mismatch issue where build artifacts contained old version
- **Build process improvement** - Added step to clean build/ and dist/ directories before building
- **Version consistency** - Updated all documentation and configuration files to reflect 1.1.0

## [1.0.6] - 2025-12-27

### Added
- **Epistemic Vector-Based Functional Self-Awareness Framework** - Updated CLI tagline to better reflect core focus
- **Documentation organization** - Moved development docs to archive, organized guides and reference docs
- **Version alignment** - Updated version across all documentation files

## [1.0.5] - 2025-12-22

### Added
- **workspace-overview command** - Epistemic project management dashboard
  - Shows epistemic health of all projects in workspace
  - Health scoring algorithm: `(know * 0.6) + ((1 - uncertainty) * 0.4) - (dead_end_ratio * 0.2)`
  - Color-coded health tiers: 🟢 high (≥0.7), 🟡 medium (0.5-0.7), 🔴 low (<0.5)
  - Sorting options: activity, knowledge, uncertainty, name
  - Filtering by project status: active, inactive, complete
  - JSON and dashboard output formats
  
- **workspace-map command** - Git repository discovery
  - Scans parent directory for git repositories
  - Shows which repos are tracked in Empirica
  - Displays epistemic health metrics for tracked projects
  - Suggests commands to track untracked repositories
  - Enables workspace-wide epistemic visibility

### Database
- `get_workspace_overview()` - Aggregates epistemic state across all projects
- `_get_workspace_stats()` - Calculates workspace-level statistics
- Health metrics include: know, uncertainty, findings, unknowns, dead ends

### Dogfooding
- Successfully used Empirica's full CASCADE workflow to build these features
- PREFLIGHT → CHECK → POSTFLIGHT assessments captured
- Learning deltas: know +0.13, completion +0.75, uncertainty -0.20
- BEADS integration tested with 3 issues tracked and closed

---

## [1.0.4] - 2025-12-22

### Added
- **Improved goals-list UX** - Shows helpful preview of 5 most recent goals when no session ID provided
- Preview includes goal ID, objective, session ID, completion percentage, and progress
- Better guidance for creating sessions and querying goals properly

### Changed
- **goals-list** command now provides more helpful error messages and previews instead of failing silently
- Goal/subtask query workflow improved with contextual hints

### Fixed
- Goal completion command now uses correct repository methods
- Project embed command properly handles goal/subtask metadata

### Refactored
- Moved `forgejo-plugin-empirica/` (125MB) to separate `empirica-dashboards` repo
- Moved `slides/` (72MB) to separate `empirica-web` repo  
- Moved `archive/` folder to `empirica-web` repo
- Reduced main package size by ~200MB for cleaner distribution

---

## [1.0.3] - 2025-12-19

### Added
- **`empirica project-init` command** - Interactive onboarding for new repositories
- **Per-project SEMANTIC_INDEX.yaml** - Each repo can have its own semantic documentation index
- **Project-level BEADS defaults** - Configure BEADS behavior per-project
- **CLI hints for BEADS** - Helpful tips after goal creation
- **Better error messages** - Install instructions when BEADS CLI not found
- **Configuration examples** - Added docs/examples/project.yaml.example

### Fixed
- **Database fragmentation (AI Amnesia)** - MCP server now uses repo-local database
- **refdoc-add UnboundLocalError** - Fixed variable usage before assignment
- **MCP server postflight regression** - Added missing resolve_session_id import
- **goals-ready schema bug** - Fixed vectors_json → individual columns
- **Project auto-detection** - Made --project-id optional with git remote URL auto-detection

### Changed
- **Project-session linking** - Added explicit --project-id flag to session-create
- **Project bootstrap** - Now auto-detects project from git remote
- **Documentation organization** - Moved session summaries to docs/development/

### Investigated
- **BEADS default behavior** - Kept opt-in (matches industry standards: Git LFS, npm, Python)
- Evidence: 5 major tools analyzed, high confidence decision (know=0.9, uncertainty=0.15)


## [1.0.0] - 2025-12-18

### Summary
First stable release of Empirica - genuine AI epistemic self-assessment framework.

### Added
- **MCO (Model-Centric Operations)**: Persona-aware configuration system
  - AI model profiles with bias corrections
  - Persona definitions (implementer, architect, researcher)
  - Cascade style configurations
- **CASCADE Workflow**: Complete epistemic assessment framework
  - PREFLIGHT: Initial epistemic state assessment
  - CHECK: Decision gate (proceed vs investigate)
  - POSTFLIGHT: Learning measurement and calibration
- **Unified Storage**: GitEnhancedReflexLogger for atomic writes
  - SQLite reflexes table integration
  - Git notes synchronization
  - JSON checkpoint export
- **Session Management**: Fast session create/resume
  - 97.5% token reduction via checkpoint loading
  - Uncertainty-driven bootstrap (scales with AI uncertainty)
- **Project Bootstrap**: Dynamic context loading
  - Recent findings, unknowns, mistakes
  - Dead ends (avoid repeated failures)
  - Qdrant semantic search integration
- **Multi-AI Coordination**: Epistemic handoffs between agents
- **CLI Commands**:
  - `empirica session-create` - Start new session
  - `empirica preflight-submit` - Submit initial assessment
  - `empirica check` - Decision gate
  - `empirica postflight-submit` - Submit final assessment
  - `empirica checkpoint-load` - Resume session
  - `empirica project-bootstrap` - Load project context
- **MCP Server**: Full integration with Claude Code and other MCP clients
- **Documentation**: Comprehensive production docs
  - Installation guides (all platforms)
  - Quickstart tutorials
  - Architecture documentation
  - API reference

### Changed
- Centralized decision logic in `decision_utils.py`
- Removed heuristic drift detection (replaced with epistemic pattern analysis)
- Cleaned documentation structure (removed future visions from public repo)

### Fixed
- Session ID mismatch in goal tracking
- Bootstrap goal progress tracking
- JSON output format in project-bootstrap
- MCP server configuration

### Security
- API key handling in config validation
- Checkpoint signature verification
- Git notes integrity checks

## [Unreleased]

### Planned
- Enhanced Qdrant integration for semantic search
- Real-time epistemic drift detection
- Advanced calibration metrics
- Web dashboard for session visualization

---

## Version Guidelines

- **MAJOR** (x.0.0): Breaking changes, incompatible API changes
- **MINOR** (1.x.0): New features, backwards-compatible
- **PATCH** (1.0.x): Bug fixes, backwards-compatible

## Links

- [GitHub Repository](https://github.com/Nubaeon/empirica)
- [Documentation](https://github.com/Nubaeon/empirica/tree/main/docs)
- [Issue Tracker](https://github.com/Nubaeon/empirica/issues)

## [Unreleased] - 2025-12-24

### Added - Major Feature Release
- **Epistemic Environmental Awareness System**: Complete spatial understanding for AIs
  - Active work context (sessions, goals, AI activity, epistemic artifacts)
  - File tree structure (3-level depth, .gitignore filtering, 60s caching)
  - Database schema summary (key tables, row counts, orthogonal view)
  - Project structure health (pattern detection, conformance scoring)
  - Flow state metrics (6-component productivity measurement)
  
- **Flow State Metrics System**: Empirically validated productivity measurement
  - 6 components: CASCADE (25%), Bootstrap (15%), Goals (15%), Learning (20%), CHECK (15%), Continuity (10%)
  - Displays recent session flow scores in bootstrap (⭐ 🟢 🟡 🔴)
  - Provides actionable recommendations for improvement
  - Tracked empirically: File tree session scored 1.00 (perfect flow)

- **Smart CHECK Prompts**: Context-aware recommendations for high-scope work
  - Triggers when scope breadth ≥0.6 or duration ≥0.5
  - Shows in goals-create JSON output as check_recommendation
  - Includes suggested timing and ready-to-use command

- **CLI Command Telemetry**: Usage-based legacy detection
  - Tracks command usage, execution time, success/failure
  - Analytics detect rarely-used (<5/90d), abandoned (>180d), broken (<50% success)
  - All local tracking, no external telemetry
  - Integrated into CLI entry point (automatic tracking)

- **AI Naming Convention**: Standardized format for cross-session discovery
  - Format: `<model>-<workstream>` (e.g., claude-bootstrap-enhancement)
  - Documented in system prompts and bootstrap tips
  - Enables session filtering and handoff clarity

- **Static/Dynamic Context Separation**: Clear knowledge architecture
  - STATIC (system prompts): How Empirica works, universal knowledge
  - DYNAMIC (bootstrap): Project-specific reality, current state
  - Documented in CANONICAL_SYSTEM_PROMPT.md sections VIII & IX

### Fixed
- goals-complete: Fixed AttributeError with sqlite3.Row objects (dict-style access)
- Flow metrics: Added helpful message when no completed sessions exist
- CLI audit: Removed 16 empty command stubs (assess, decision, profile, component commands)

### Improved
- Bootstrap output: Now shows 6 major sections (active work, flow metrics, DB schema, structure health, file tree, artifacts)
- System prompts: Enhanced with static context (DB schema, flow factors, project patterns)
- Test strategy: Documented unit vs integration testing philosophy (TESTING_STRATEGY.md)

### Performance
- File tree generation: 3ms average, instant cache hits
- Bootstrap loading: ~200ms with all new features
- Flow metrics calculation: <100ms for 5 sessions

### Documentation
- Added comprehensive static context to CANONICAL_SYSTEM_PROMPT.md
- Created TESTING_STRATEGY.md with testing philosophy
- Updated system prompts in docs/system-prompts/ directory
- Enhanced rovodev config.yml with latest patterns

### Technical Details
- New tables: command_usage (CLI telemetry)
- New modules: empirica/metrics/flow_state.py, empirica/utils/structure_health.py
- Enhanced: SessionDatabase with telemetry and flow metrics methods
- 10 sessions, ~2600+ lines changed, 12 commits
- Average flow score: 0.89 (exceptional productivity day)

