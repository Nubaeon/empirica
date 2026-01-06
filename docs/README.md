# Empirica Documentation

**Current Version:** 1.2.3
**Status:** Production Ready

---

## Documentation Split

Documentation is organized by audience:

### 🤖 AI-First Docs (This folder)

Documentation designed for AI context loading - maps directly to code classes.

- **[architecture/](architecture/)** - Core system architecture (Sentinel, EpistemicBus, etc.)
- **[reference/](reference/)** - API reference, database schemas, configuration
- **[guides/](guides/)** - AI workflow guides

### 👤 Human Docs

Documentation for human readers: [human/](human/)

- **[human/end-users/](human/end-users/)** - Getting started, installation, conceptual guides
- **[human/developers/](human/developers/)** - AI integration, system prompts, technical setup

---

## Architecture (AI Limbs)

These docs document actual code classes for AI context loading:

| Doc | Classes Covered |
|-----|-----------------|
| [SENTINEL_ARCHITECTURE.md](architecture/SENTINEL_ARCHITECTURE.md) | Sentinel, GateAction, NoeticFilter, AxiologicGate |
| [EPISTEMIC_BUS.md](architecture/EPISTEMIC_BUS.md) | EpistemicBus, EpistemicEvent, EpistemicObserver |
| [CANONICAL_STORAGE.md](architecture/CANONICAL_STORAGE.md) | GitNotesStorage, CheckpointStorage, SessionSync |
| [SELF_MONITORING.md](architecture/SELF_MONITORING.md) | MirrorDriftMonitor, MemoryGapDetector |
| [HANDOFF_SYSTEM.md](architecture/HANDOFF_SYSTEM.md) | EpistemicHandoffReportGenerator |
| [COMPLETION_TRACKING.md](architecture/COMPLETION_TRACKING.md) | CompletionTracker, GitProgressQuery |
| [ASSESSMENT_AND_SIGNALING.md](architecture/ASSESSMENT_AND_SIGNALING.md) | ComponentAssessor, SignalingState |
| [SUPPORTING_COMPONENTS.md](architecture/SUPPORTING_COMPONENTS.md) | CheckpointSigner, ContextLoadBalancer |

---

## Reference

- **[reference/api/](reference/api/)** - Python API by module
- **[reference/DATABASE_SCHEMA_UNIFIED.md](reference/DATABASE_SCHEMA_UNIFIED.md)** - Database schema
- **[reference/CONFIGURATION_REFERENCE.md](reference/CONFIGURATION_REFERENCE.md)** - Config options
- **[reference/CHANGELOG.md](reference/CHANGELOG.md)** - Version history

---

## Documentation Health

Run `python scripts/doc_health_audit.py` to check:
- Code reference validity (do referenced classes exist?)
- Staleness (how old?)
- Redundancy (covered elsewhere?)

Docs with <30% valid code references go to `human/` or `_archive/`.

---

**System Status:** Production Ready ✅
**AI Doc Coverage:** 86.9%
