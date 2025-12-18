# Changelog

All notable changes to Empirica will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
