# Changelog

All notable changes to Empirica will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - Preparing v1.0.0

### Phase 4 (In Progress)
- Documentation completion
- End-to-end testing
- PyPI package preparation
- Release v1.0.0

---

## [0.9.1] - 2025-12-11 - Critical Bug Fixes

### Fixed
- **Git notes creation failure** (commit daff2801)
  - Problem: Git notes failing with "error: there was a problem with the editor"
  - Root cause: Missing `-F -` flag in subprocess commands
  - Solution: Added `-F -` to tell git to read from stdin
  - Impact: All 3 storage layers (SQLite + Git Notes + JSON) now working correctly
  - Files: `empirica/core/canonical/git_enhanced_reflex_logger.py` (lines 613, 698)

- **Memory gap false positives** (commits 7e39c2e8, 5fa2fbe5, 2a625277)
  - Problem 1: Uncertainty decrease incorrectly flagged as memory loss
  - Reality: Uncertainty decrease = learning, not forgetting (inverse vector)
  - Problem 2: Within-session PREFLIGHT→POSTFLIGHT decreases flagged as "memory gaps"
  - Reality: These are calibration corrections ("I thought I knew, but I don't"), not memory compression
  - Solution: Removed false memory gap detection entirely
  - Note: True memory gap detection requires cross-session comparison (previous POSTFLIGHT → current PREFLIGHT)
  - Files: `empirica/cli/command_handlers/workflow_commands.py`

- **POSTFLIGHT anchoring bias** (commit cb0c15d7)
  - Problem: `execute_postflight` MCP tool showed PREFLIGHT baseline vectors to AI during assessment
  - Risk: Anchoring bias - AI adjusts assessment based on remembered baseline instead of genuine reflection
  - Solution: Removed `preflight_baseline.vectors` from MCP response, kept contextual info only
  - Impact: True pure self-assessment - AI assesses current state without bias, system calculates deltas objectively
  - Philosophy: Genuine self-assessment requires removing cognitive biases
  - Files: `mcp_local/empirica_mcp_server.py`

### Added
- **Artifacts tracking in project-bootstrap** (commit 652db142)
  - Feature: `project-bootstrap` now surfaces recently modified files from handoff reports
  - Returns: `recent_artifacts` with last 10 sessions' file modifications
  - Use case: Systematic documentation auditing - compare modified files vs reference docs vs git history
  - Files: `empirica/data/session_database.py`, `empirica/cli/command_handlers/project_commands.py`

---

## [0.9.0] - 2025-11-01 - Phase 3 Complete

### Added - CLI Integration
- **CLI Commands:**
  - `empirica cascade` - Smart query routing with 5 strategies
  - `empirica decision` - Interactive epistemic decision workflow
  - `empirica monitor` - Usage tracking dashboard
  - `empirica config` - Configuration management (init/show/validate)

- **MCP Tools (4 new, 19 total):**
  - `modality_route_query` - Execute queries through ModalitySwitcher
  - `modality_list_adapters` - List adapters with health status
  - `modality_adapter_health` - Check individual adapter health
  - `modality_decision_assist` - Get routing recommendation

- **Qwen Integration:**
  - Qwen adapter registered in modality system
  - Memory leak fixed (MaxListenersExceededWarning)
  - Full CLI integration with routing

### Changed
- Documentation reorganized (phase_handoffs/, sessions/, archive/)
- STUB_TRACKER updated to reflect Phase 3 completion
- All Phase 0-3 components marked complete

### Fixed
- Qwen adapter memory leak (Node.js EventEmitter warning)
- CLI argument parsing for epistemic vectors
- Routing strategy selection logic

---

## [0.8.0] - 2025-11-01 - Phase 2 Complete

### Added - ModalitySwitcher

- **Intelligent Routing System (520 lines):**
  - EPISTEMIC strategy - Route based on epistemic vectors
  - COST strategy - Minimize cost (prefer free adapters)
  - LATENCY strategy - Minimize latency (prefer fast)
  - QUALITY strategy - Maximize quality (prefer best)
  - BALANCED strategy - Balance all factors with scoring

- **Infrastructure:**
  - `ModalitySwitcher` - Central routing orchestrator
  - `UsageMonitor` - Usage tracking and cost monitoring
  - `AuthManager` - API key management
  - `PluginRegistry` - Dynamic adapter registration

- **MiniMax-M2 Adapter:**
  - API integration via Anthropic SDK
  - 100% test pass rate (10/10 tests)
  - 3s average latency
  - $0.015 per 1k tokens

### Changed
- Plugin registry enhanced with metadata
- Adapter registration centralized

---

## [0.7.0] - 2025-11-01 - Phase 1 Complete

### Added - Adapters

- **Qwen Adapter:**
  - CLI integration with Qwen Code
  - 100% test pass rate (7/7 golden prompts)
  - Proper epistemic reasoning
  - Fixed CLI parameters and stdin handling

- **Local Adapter:**
  - Stub implementation for testing
  - Mock responses with schema compliance

### Changed
- Adapter interface standardized
- Test harness created for golden prompts

---

## [0.6.0] - 2025-10-31 - Phase 0 Complete

### Added - Foundation

- **Plugin Registry:**
  - Dynamic adapter discovery
  - Health check monitoring
  - Adapter lifecycle management

- **Schema Definitions:**
  - `AdapterPayload` - Standard request format
  - `AdapterResponse` - Standard response format (PersonaEnforcer schema)
  - `AdapterError` - Error handling

### Changed
- Project renamed from `empirica` to `empirica`
- Directory structure reorganized (semantic organization)

---

## [0.5.0] - 2025-10-30 - Enhanced Cascade Workflow

### Added
- 7-phase cascade workflow (PREFLIGHT → Think → Plan → Investigate → Check → Act → POSTFLIGHT)
- Preflight/Postflight assessments with Δ vector tracking
- Calibration validation system

### Changed
- Workflow components integrated into cascade
- Reflex frame logging enhanced

---

## [0.4.0] - 2025-10-29 - Core Components

### Added
- 13-vector metacognitive system (11 foundation + ENGAGEMENT + UNCERTAINTY)
- Bayesian Guardian (evidence-based belief tracking)
- Drift Monitor (behavioral integrity tracking)
- Goal Orchestrator (multi-goal coordination)
- Session database (SQLite + JSON exports)

### Changed
- Bootstrap system with 5 levels (0-4)
- Documentation organized into production/ directory

---

## [0.3.0] - 2025-10-28 - Bootstrap & Database

### Added
- Bootstrap system for component initialization
- Session database for tracking
- Auto-tracking (DB + JSON + Reflex logs)

---

## [0.2.0] - 2025-10-27 - MCP Integration

### Added
- MCP server with 15 tools
- Claude Desktop integration
- Tool handlers for cascade, assessment, investigation

---

## [0.1.0] - 2025-10-26 - Initial Release

### Added
- Basic canonical epistemic assessor
- 13-vector system (12 vectors + ENGAGEMENT)
- Simple cascade workflow
- CLI foundation

---

## Version Numbering

- **0.x.x** - Pre-release versions (development)
- **1.0.0** - First stable release (Phase 4 complete)
- **1.x.x** - Minor updates and enhancements
- **2.x.x** - Major feature additions

---

**Current Version:** 0.9.0 (Phase 3 Complete)  
**Next Version:** 1.0.0 (Phase 4 - Production Release)  
**Target Release Date:** November 8-15, 2025
