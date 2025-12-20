# Repository Organization & Branching Strategy

**Last Updated:** 2025-12-20
**Status:** Active

---

## Overview

The Empirica ecosystem consists of multiple repositories with clear separation of concerns:

- **Core Infrastructure** (MIT, public) - The cognitive OS framework
- **Products & Applications** (Mixed licensing) - Built on top of Empirica
- **Internal** (Private) - Business strategy, security-sensitive content

---

## Repository Structure

### Core Infrastructure (Public, MIT)

#### **empirica** - Main Framework
📍 https://github.com/Nubaeon/empirica

**Purpose:** Cognitive OS for AI systems - epistemic learning, CASCADE workflow, multi-agent coordination

**Contains:**
- Core Python package (`empirica/`)
- CLI tools and commands
- CASCADE workflow implementation
- Epistemic learning system
- Database abstraction (SQLite/PostgreSQL)
- Qdrant integration for semantic learning
- Documentation, examples, tests

**License:** MIT
**Audience:** Developers, researchers, AI engineers
**Install:** `pip install empirica`

**Branching strategy:**
```
main (stable, production-ready)
  ↑
develop (integration, testing)
  ↑
feature/* (work branches)
```

---

#### **empirica-mcp** - MCP Server Integration
📍 Included in `empirica/empirica-mcp/`

**Purpose:** Model Context Protocol server for Claude Code integration

**Contains:**
- MCP server implementation
- Tool definitions for Empirica commands
- Session management via MCP

**License:** MIT
**Audience:** Claude Code users, MCP developers
**Install:** Auto-configured via `empirica` installation

---

### Products & Applications (Mixed Licensing)

#### **empirica-web** - Web Platform
📍 https://github.com/Nubaeon/empirica-web

**Purpose:** Web-based interface for Empirica sessions, visualization, collaboration

**Contains:**
- Frontend (React/Next.js)
- Backend API
- Session visualization
- Multi-user collaboration features

**License:** TBD (likely proprietary for SaaS offering)
**Status:** In development
**Audience:** Teams, enterprises, researchers

---

#### **empirica-chat** - Conversational Interface
📍 Planned repository

**Purpose:** Chat-based interface for Empirica workflows

**Contains:**
- Chat UI for CASCADE workflow
- Natural language session management
- Real-time epistemic feedback

**License:** TBD
**Status:** Concept/early development
**Audience:** Non-technical users, teams

---

#### **empirica-studio** - Management Dashboard
📍 Planned repository

**Purpose:** GUI for managing Empirica projects, teams, AI agents

**Contains:**
- Project management interface
- Team collaboration tools
- AI agent orchestration UI
- Analytics and insights

**License:** Proprietary (Enterprise edition)
**Status:** Planned
**Audience:** Enterprise customers, teams

---

### Extensions & Integrations (Public, MIT)

#### **forgejo-plugin-empirica** - Git Forge Integration
📍 Included in `empirica/forgejo-plugin-empirica/`

**Purpose:** Empirica integration for Forgejo/Gitea

**Contains:**
- Plugin hooks for commit tracking
- Session linking to git operations
- Epistemic metadata in git notes

**License:** MIT
**Audience:** Self-hosted git users
**Status:** Proof of concept

---

### Internal (Private)

#### **empirica-internal** - Business & Security
📍 https://github.com/Nubaeon/empirica-internal (Private)

**Purpose:** Business strategy, internal planning, security-sensitive content

**Contains:**
- Market strategy and analysis
- Internal architecture planning
- Security vulnerability disclosure system (vsif-poc)
- Dev artifacts tracking
- Business roadmap

**License:** Proprietary
**Audience:** Empirica team only
**Access:** Private repository

---

## Branching Strategy

### Main Repository (empirica)

**Philosophy:** Simple, solo-dev friendly, scales to teams

```
main
├── Purpose: Stable, production-ready code
├── Protection: CI must pass, no direct commits
├── Merges from: develop (when tested and stable)
└── Users install from: pip install empirica

develop
├── Purpose: Integration branch for new features
├── Protection: CI must pass
├── Merges from: feature/*, bugfix/*, docs/*
├── Merges to: main (after testing)
└── Dev install: pip install git+https://github.com/Nubaeon/empirica.git@develop

feature/*, bugfix/*, docs/*
├── Purpose: Individual work branches
├── Naming: feature/add-oauth, bugfix/session-leak, docs/api-reference
├── Lifetime: Delete after merge to develop
└── Create from: develop
```

### Branch Workflow

1. **New work:** Create branch from `develop`
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature
   ```

2. **Develop:** Work in feature branch, commit frequently

3. **Merge to develop:** PR or direct merge when ready
   ```bash
   git checkout develop
   git merge feature/your-feature
   git push origin develop
   ```

4. **Release to main:** When develop is stable
   ```bash
   git checkout main
   git merge develop
   git tag v1.x.x
   git push origin main --tags
   ```

### What Goes Where?

| Content Type | Branch | Notes |
|--------------|--------|-------|
| **Bug fixes** | `develop` | Merge to main for hotfix |
| **New features** | `develop` | Test before main |
| **Experimental work** | `feature/experimental-*` | May not merge |
| **Documentation** | `develop` or `main` | Docs can go direct to main |
| **Infrastructure** | `develop` | Database, Qdrant, etc. |
| **Breaking changes** | `develop` + version bump | Major version change |

---

## Repository Relationships

```
┌─────────────────────────────────────────────────────┐
│  CORE INFRASTRUCTURE (MIT, Public)                  │
│  ┌───────────────────────────────────────────────┐  │
│  │  empirica (main framework)                    │  │
│  │  - CASCADE workflow                           │  │
│  │  - Epistemic learning                         │  │
│  │  - Multi-agent coordination                   │  │
│  │  - Database abstraction                       │  │
│  │  - Qdrant integration                         │  │
│  └───────────────────────────────────────────────┘  │
│                       ▲                              │
│                       │ pip install empirica         │
└───────────────────────┼──────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ empirica-web │ │empirica-chat│ │empirica-studio│
│              │ │             │ │              │
│ Web platform │ │ Chat UI     │ │ Enterprise   │
│ (Mixed)      │ │ (TBD)       │ │ (Proprietary)│
└──────────────┘ └─────────────┘ └──────────────┘

                        ┌───────────────────────┐
                        │  empirica-internal    │
                        │  (Private)            │
                        │  - Business strategy  │
                        │  - Security (vsif-poc)│
                        │  - Internal planning  │
                        └───────────────────────┘
```

---

## Licensing Strategy

### Core = MIT (Infrastructure Level)

**What's MIT:**
- Empirica framework core
- CASCADE workflow
- Epistemic learning system
- Database abstraction
- Qdrant integration
- MCP server
- CLI tools
- Documentation

**Why MIT:**
- Maximum adoption
- Research-friendly
- Enterprise-friendly
- Community contributions
- Open science principles

### Products = Mixed (Built on Top)

**Proprietary candidates:**
- empirica-web (SaaS offering)
- empirica-studio (Enterprise GUI)
- Hosted platform services
- Enterprise support tools

**Open source candidates:**
- empirica-chat (community tool)
- Integrations/plugins
- Example applications

**Decision criteria:**
- Does it compete with SaaS offering? → Proprietary
- Is it infrastructure? → MIT
- Does it drive adoption? → MIT
- Is it enterprise-specific? → Proprietary

---

## Protection Against Accidents

### .gitignore in empirica repo

```gitignore
# Internal business docs (live in empirica-internal repo)
DEV_ARTIFACTS_LOCATION.md
vsif-poc/
docs/MARKET_OPPORTUNITIES.md
docs/MARKET_STRATEGY.md
docs/WHY_BLUE_OCEAN.md
docs/MEETINGS_ADAPTER_DESIGN.md
```

**Prevents:** Accidentally re-adding private content to public repo

---

## Development Workflow

### Solo Developer (Current)

1. Work directly in `develop` for small changes
2. Create feature branches for larger work
3. Merge to `main` when stable
4. Tag releases: `v1.x.x`

### Team Development (Future)

1. All work in feature branches
2. Pull requests to `develop`
3. Code review required
4. CI must pass
5. Release manager merges `develop` → `main`

---

## Migration Path

### Current State (v1.0.x)

- Single developer
- Direct commits to `develop` OK
- Manual testing before `main` merge
- Git Flow light (main ← develop)

### Future State (v2.0+)

- Multiple contributors
- PR-based workflow
- Automated testing (CI/CD)
- Release automation
- Semantic versioning strictly enforced

---

## Repository Checklist

When creating a new repository in the ecosystem:

- [ ] Choose appropriate license (MIT vs. Proprietary)
- [ ] Add to this document
- [ ] Set up CI/CD if applicable
- [ ] Add README with purpose and install instructions
- [ ] Link to main `empirica` repo in docs
- [ ] Add to GitHub org: https://github.com/Nubaeon
- [ ] Configure branch protection rules
- [ ] Add CONTRIBUTING.md if accepting PRs

---

## Questions & Decisions

**Q: When to create a new repo vs. adding to empirica?**
A: New repo if:
- Different licensing (proprietary vs. MIT)
- Different release cycle
- Optional/plugin functionality
- Separate product offering

**Q: What if a feature could be core OR product?**
A: Default to MIT core unless:
- It's a competitive differentiator for SaaS
- It requires proprietary dependencies
- It's enterprise-specific

**Q: How to handle breaking changes?**
A:
- Major version bump (v1.x → v2.0)
- Migration guide in docs
- Deprecation warnings in v1.x
- Support both for transition period

---

## References

- Main repo: https://github.com/Nubaeon/empirica
- Contributing guide: `/CONTRIBUTING.md`
- Release process: `/scripts/RELEASE_PROCESS.md`
- Internal strategy: https://github.com/Nubaeon/empirica-internal (Private)

---

## Updates

| Date | Change | Reason |
|------|--------|--------|
| 2025-12-20 | Initial version | Document repository ecosystem and branching |
| 2025-12-20 | Added empirica-internal | Separate business/security content |
| 2025-12-20 | Database abstraction to develop | Enterprise prep while keeping simple |

---

**Next Steps:**

1. ✅ Document repository structure (this file)
2. [ ] Set up CI/CD for empirica repo
3. [ ] Create empirica-web deployment pipeline
4. [ ] Define empirica-studio licensing
5. [ ] Community contribution guidelines for external PRs
