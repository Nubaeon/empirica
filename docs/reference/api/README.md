# Empirica Python API Reference

**Framework Version:** 1.3.0
**Status:** Production Ready

---

## API Categories

### [Core Session Management](core_session_management.md)
- **SessionDatabase** - Central database for all session data
- **Session creation, retrieval, and management**
- **Epistemic vector storage and retrieval**

### [Goals & Tasks](goals_tasks.md)
- **GoalRepository** - Goal creation, tracking, and completion
- **Subtask management** - Task breakdown and progress tracking
- **Goal-tree operations** - Hierarchical goal management

### [Project Management](project_management.md)
- **ProjectRepository** - Project lifecycle management
- **Handoff reports** - AI-to-AI handoff documentation
- **Project tracking** - Cross-session project management

### [Knowledge Management](knowledge_management.md)
- **BreadcrumbRepository** - Findings, unknowns, dead-ends
- **Epistemic sources** - Source attribution and confidence
- **Reference documents** - Project documentation links

### [Qdrant Vector Storage](qdrant.md)
- **EmbeddingsProvider** - Multi-provider embeddings (Ollama, OpenAI, Jina, Voyage)
- **Vector store operations** - Memory upsert, search, delete
- **Pattern retrieval** - CASCADE hook integration (PREFLIGHT/CHECK)

### [Lessons System](lessons.md)
- **LessonStorageManager** - 4-layer storage for procedural knowledge
- **LessonHotCache** - In-memory graph for nanosecond queries
- **Knowledge graph** - Prerequisites, enables, relations

### [Signaling](signaling.md)
- **DriftLevel** - Traffic light calibration for epistemic drift
- **SentinelAction** - Gate actions (REVISE, BRANCH, HALT, LOCK)
- **CognitivePhase** - Noetic/Threshold/Praxic phase detection
- **VectorHealth** - Health state for individual vectors

### [Identity & Persona](identity_persona.md)
- **AIIdentity** - Cryptographic identity for AI agents
- **PersonaMetadata** - Persona configuration
- **EpistemicConfig** - Priors, thresholds, weights

### [Architecture Assessment](architecture_assessment.md)
- **CouplingAnalyzer** - Dependency and API surface analysis
- **StabilityEstimator** - Git history stability metrics
- **ArchitectureVectors** - Epistemic vectors for code quality

### [System Utilities](system_utilities.md)
- **BranchMapping** - Git branch to goal mapping
- **DocCodeIntegrity** - Documentation-code integrity checking
- **Migration tools** - Schema evolution utilities

---

## API Philosophy

**AI-First Design:** All APIs designed for autonomous AI agent usage with structured return values and comprehensive error handling.

**Epistemic Self-Awareness:** APIs capture and track epistemic state throughout all operations.

**Modular Architecture:** APIs organized in logical modules that can be used independently while maintaining consistency.

**Four-Layer Storage:** Data flows through SQLite (hot), Git Notes (warm), JSON Logs (audit), and Qdrant (search).

---

## Getting Started

For new users, start with:
1. [Core Session Management](core_session_management.md) - Essential session operations
2. [CASCADE Workflow](cascade_workflow.md) - Core reasoning workflow
3. [Goals & Tasks](goals_tasks.md) - Task management operations

---

**Total Modules:** 10 categories
**API Stability:** Production ready
