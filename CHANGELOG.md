# Changelog

All notable changes to Empirica will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

