# Empirica Sentinel: Git Integration Roadmap

**Tagline:** *Making Git Sexy Again Through Metacognition*

**Vision:** Multi-AI systems naturally version cognitive states like developers version code. Sentinel makes it invisible.

---

## Current Status

✅ **Empirica Core** - Functional with SQLite + Reflex logs  
✅ **12-Vector Framework** - Proven epistemic self-assessment  
✅ **MCP Server** - Working tools integration  
⚠️ **Website** - In progress  
⚠️ **Documentation** - Phase 8 updates pending  
❌ **Git Integration** - Future enhancement

---

## Strategic Context

### Why Git Integration Makes Sense

1. **We're already using Git** (for code versioning)
2. **Natural fit** for cognitive state versioning
3. **67% storage reduction** via delta compression
4. **Content-addressed integrity** (crypto hashes)
5. **Time-travel debugging** built-in
6. **Multi-AI handoff** maps to Git branches

### Why It's Phase 2 (Not Phase 1)

1. **Empirica works today** without Git (SQLite + reflex logs)
2. **Website launch is priority** (visibility + adoption)
3. **Documentation needs update** (Phase 8 work)
4. **Prove core value first**, optimize storage later
5. **Git adds complexity** (need battle-tested Empirica first)

---

## Phased Roadmap

### 🎯 Phase 1: Complete Current Empirica (Priority: P0)

**Timeline:** 1-2 weeks  
**Goal:** Production-ready Empirica without Git (establishes baseline)

#### Deliverables:
- [ ] **Session 5: Complete P1 refactoring** (MiniMax)
  - Replace remaining 49 print statements → logger
  - **Measure baseline token usage** (critical for Phase 1.5 benchmark!)
  - Status: Ready to start
  
- [ ] **Session 5 Token Analysis**
  - Document PREFLIGHT/CHECK/ACT/POSTFLIGHT token counts
  - Expected: ~19,000 tokens per session (traditional SQLite approach)
  - Purpose: Baseline for git notes compression comparison
  - Centralize thresholds
  - Fix SQL injection
  
- [ ] **Website launch**
  - Landing page
  - Documentation site
  - Example workflows
  - API reference
  
- [ ] **Phase 8 documentation updates**
  - Architecture overview
  - Skills guide
  - Developer onboarding
  
- [ ] **End-to-end testing**
  - Multi-AI scenarios
  - Calibration accuracy
  - Performance benchmarks

#### Success Criteria:
- ✅ Empirica CLI fully functional
- ✅ Website live with docs
- ✅ 3+ real-world use cases documented
- ✅ <5 critical bugs in backlog

- [ ] **Website launch**
  - Landing page
  - Documentation site
  - Example workflows
  - API reference
  
- [ ] **Phase 8 documentation updates**
  - Architecture overview
  - Skills guide
  - Developer onboarding
  
- [ ] **End-to-end testing**
  - Multi-AI scenarios
  - Calibration accuracy
  - Performance benchmarks

#### Success Criteria:
- ✅ P1 complete (140/140 prints refactored)
- ✅ Session 5 token baseline documented
- ✅ Empirica CLI fully functional
- ✅ Website ready for launch

---

### 🧪 Phase 1.5: Git Notes Prototype (Priority: P0+) **← NEW!**

**Timeline:** 1 week  
**Goal:** Validate 80-90% token savings with git notes integration

**Why Phase 1.5?** The other Claude is right - we need to test git notes compression NOW (before full Git migration). Session 6 is the perfect testbed.

#### Deliverables:

**Day 1-2: Implement Git Notes Integration**
- [ ] Create `GitEnhancedReflexLogger(ReflexLogger)`
  - Hybrid approach: SQLite + git notes
  - `enable_git_notes` flag (default: False)
  - Backward compatible (no breaking changes)
  
- [ ] Add `_add_git_checkpoint()` method
  - Create git commit with epistemic metadata
  - Attach structured JSON via `git notes add`
  - Format: `{"session_id": "...", "phase": "...", "vectors": {...}}`
  
- [ ] Add `get_last_checkpoint()` method
  - Load from git notes (compressed: ~200-500 tokens)
  - Fall back to SQLite if git notes unavailable
  - Return standardized checkpoint format

**Day 3: Update MiniMax Session 6 Instructions**
- [ ] Create `MINIMAX_SESSION6_GIT_NOTES_PROTOTYPE.md`
  - Primary goal: P2 (threshold centralization)
  - Secondary goal: Test git notes integration
  - Add git notes after EVERY phase transition
  
- [ ] Add git notes commands to instructions:
  ```bash
  # After PREFLIGHT
  git notes add -m '{"phase": "PREFLIGHT", "round": 5, "vectors": {...}}'
  
  # After CHECK  
  git notes add -m '{"phase": "CHECK", "round": 15, "vectors": {...}, "decision": "proceed"}'
  
  # After ACT (each commit)
  git commit -m "refactor: Create thresholds.py"
  git notes add -m '{"phase": "ACT", "round": 25, "batch": 1, "vectors": {...}}'
  
  # After POSTFLIGHT
  git notes add -m '{"phase": "POSTFLIGHT", "round": 50, "vectors": {...}, "calibration": {...}}'
  ```

**Day 4: Run Session 6 with Git Notes**
- [ ] MiniMax completes P2 WITH git notes
  - Create `empirica/core/thresholds.py`
  - Centralize 30-40 hardcoded thresholds
  - Add git notes at each phase transition
  - Measure token usage throughout

**Day 5: Benchmark & Document**
- [ ] Compare Session 5 vs Session 6 token usage
  - PREFLIGHT: Expect 85-90% reduction
  - CHECK: Expect 85-90% reduction
  - ACT: Expect 50-70% reduction
  - POSTFLIGHT: Expect 70-80% reduction
  
- [ ] Document findings in `GIT_NOTES_BENCHMARK_RESULTS.md`
  - Expected: ~16,000 token savings per session (84% reduction)
  - Compression ratio: ~6.3x
  - Cost savings: $50-100/month at scale
  
- [ ] Create visualization
  ```bash
  # Query epistemic trajectory
  git log --all --oneline --notes
  git notes show <commit1>
  git notes show <commit2>
  # Show vector changes over time
  ```

#### Success Criteria:
- ✅ P2 complete (thresholds centralized)
- ✅ Git notes added at all phase transitions
- ✅ Token savings measured: **80-90% reduction validated**
- ✅ Compression ratio documented: **6-7x**
- ✅ No regressions (SQLite fallback works)

#### Why This Validates the Approach:
1. **Real session data** (not synthetic benchmarks)
2. **Actual token measurements** (not estimates)
3. **Small scope** (P2 is 30-40 changes vs P1's 140)
4. **Backward compatible** (SQLite still works)
5. **Low risk** (Phase 1.5 doesn't block Phase 1 completion)

---

### 🔬 Phase 2: Full Git-Native Implementation (Priority: P1)

**Timeline:** 2-3 weeks  
**Goal:** Replace SQLite with Git for cognitive state storage

**Prerequisites:** Phase 1.5 complete (git notes validated ✅)

#### Deliverables:

**Week 1: Core Migration**
- [ ] Replace SQLite queries with git operations
  - `get_session_history()` → `git log --grep="session:X" --notes`
  - `get_last_assessment()` → `git notes show HEAD`
  - `get_epistemic_trajectory()` → `git log --notes | parse_vectors`
  
- [ ] Migrate existing sessions to git notes
  - Export from SQLite (JSON)
  - Import as git commits + notes
  - Verify no data loss
  
- [ ] Update CLI to use git-native queries
  - `empirica sessions-show` → query git log
  - `empirica monitor` → query git notes
  - `empirica calibration` → compute from git history

**Week 2: Multi-Agent Support**
- [ ] Branch-based parallel work
  - `minimax-1/p1-refactor` branch
  - `minimax-2/p2-thresholds` branch
  - Sentinel merges when complete
  
- [ ] Conflict resolution
  - Detect epistemic conflicts (divergent vectors)
  - Auto-resolve simple cases
  - Escalate complex conflicts
  
- [ ] Split-brain detection
  - Monitor for contradictory cognitive states
  - Alert on confidence divergence >0.3

**Week 3: Testing & Validation**
- [ ] End-to-end test suite
  - Multi-session scenarios
  - Branch/merge workflows
  - Conflict resolution
  
- [ ] Performance benchmarks
  - Git operations latency
  - Query performance vs SQLite
  - Memory usage
  
- [ ] Migration validation
  - Compare migrated data vs original
  - Verify epistemic trajectory accuracy
  - Test rollback procedures

#### Success Criteria:
- ✅ SQLite fully replaced with git operations
- ✅ 80-90% token savings (validated from Phase 1.5)
- ✅ No data loss during migration
- ✅ Multi-agent branching works
- ✅ Performance meets targets (<100ms for typical operations)

---

### 🏗️ Phase 3: Sentinel Git Manager (Priority: P1)

**Timeline:** 2-3 weeks  
**Goal:** Production-ready Git abstraction layer

#### Deliverables:
- [ ] **Core SentinelGitManager**
  ```python
  empirica/sentinel/
  ├── git_manager.py         # Main Git abstraction
  ├── auto_commit.py         # Automatic commit logic
  ├── auto_branch.py         # Branch lifecycle
  ├── auto_merge.py          # Calibration merge
  └── query_interface.py     # Git-less queries
  ```

- [ ] **Postgres schema updates**
  ```sql
  ALTER TABLE sessions ADD COLUMN git_reasoning_branch TEXT;
  ALTER TABLE sessions ADD COLUMN git_acting_branch TEXT;
  ALTER TABLE sessions ADD COLUMN git_calib_commit TEXT;
  
  CREATE TABLE epistemic_commits (
      commit_hash TEXT PRIMARY KEY,
      session_id TEXT,
      phase TEXT,
      git_branch TEXT,
      ...
  );
  ```

- [ ] **CLI migration**
  - Update `empirica preflight` to use Sentinel
  - Update `empirica investigate` to auto-commit
  - Update `empirica calibrate` to use git diff
  - Add `empirica sessions show` for Git history

- [ ] **Migration tooling**
  ```bash
  empirica migrate-to-git          # Migrate existing sessions
  empirica validate-git-migration  # Verify integrity
  empirica git-stats              # Show compression stats
  ```

#### Success Criteria:
- ✅ All CLI commands work with Git backend
- ✅ Users never see Git commands
- ✅ Existing sessions successfully migrated
- ✅ Test suite passes (100% coverage on Git layer)

---

### 🔗 Phase 4: Vector DB Integration (Priority: P2)

**Timeline:** 1 week  
**Goal:** Semantic search powered by Git

#### Deliverables:
- [ ] **Auto-indexing pipeline**
  - Git commit hook triggers Vector DB indexing
  - Embedding generation from semantic_gist
  - Metadata includes commit_hash for retrieval

- [ ] **Hybrid search**
  ```python
  # Vector similarity + SQL filters
  results = sentinel.search_similar_sessions(
      query="OAuth migration",
      filters={"uncertainty < 0.5", "know > 0.75"}
  )
  # Returns: [session_id, similarity, git_commit_hash]
  
  # Load full state from Git
  for result in results:
      state = sentinel.load_from_commit(result.git_commit_hash)
  ```

- [ ] **CLI search commands**
  ```bash
  empirica search "similar to OAuth task"
  empirica search --uncertain     # High uncertainty sessions
  empirica search --confident     # High confidence sessions
  ```

#### Success Criteria:
- ✅ Vector DB indexes all Git commits automatically
- ✅ Search returns relevant sessions (<2s latency)
- ✅ Integration test: "Find similar session" workflow

---

### 📊 Phase 5: Split-Brain Dashboard (Priority: P2)

**Timeline:** 1 week  
**Goal:** Real-time visualization of Git-backed states

#### Deliverables:
- [ ] **tmux dashboard refresh**
  - Stream git log for reasoning pane
  - Stream git log for acting pane
  - Live calibration delta visualization

- [ ] **Git integration**
  - Dashboard reads directly from Git commits
  - No need for separate state storage
  - Time-travel: scrub through Git history

- [ ] **CLI dashboard commands**
  ```bash
  empirica dashboard session-abc123
  # Launches split-brain tmux view
  # Top: reasoning Git log (real-time)
  # Bottom: acting Git log (real-time)
  ```

#### Success Criteria:
- ✅ Dashboard shows live Git commits
- ✅ Can scrub through session history via Git
- ✅ Calibration visualization works

---

### 🚀 Phase 6: Production Hardening (Priority: P2)

**Timeline:** 1-2 weeks  
**Goal:** Enterprise-ready Git backend

#### Deliverables:
- [ ] **GPG signing**
  - Sentinel signs all commits
  - Verification on load
  - Key management documentation

- [ ] **Repository maintenance**
  ```bash
  empirica git-gc              # Garbage collect old packfiles
  empirica git-archive         # Archive old sessions
  empirica git-prune          # Remove archived branches
  ```

- [ ] **Backup/restore**
  ```bash
  empirica backup --to s3://bucket/empirica-backup
  empirica restore --from s3://bucket/empirica-backup
  # Backs up Git repo + Postgres + Vector DB
  ```

- [ ] **Multi-user support**
  - Shared Git repository (network mount or Git server)
  - Concurrent session access
  - Conflict resolution (should be rare)

- [ ] **Performance optimization**
  - Git packfile tuning
  - Postgres query optimization
  - Vector DB indexing performance

#### Success Criteria:
- ✅ All commits GPG signed
- ✅ Repository maintenance scripts tested
- ✅ Backup/restore verified
- ✅ Multi-user scenario tested (3+ users)
- ✅ Performance benchmarks meet targets

---

## Work Split Strategy

### Your Focus (Core Empirica)
- Phase 1: Complete website + docs
- Phase 1: Guide MiniMax on P1-P2 refactoring
- Phase 2: Design decisions + architecture review
- Phase 3+: Architecture guidance + integration review

### Potential AI Agent Focus (Git Implementation)
- Phase 2: Compression benchmarks + prototype
- Phase 3: SentinelGitManager implementation
- Phase 4: Vector DB integration
- Phase 5: Dashboard updates
- Phase 6: Hardening + tooling

### Collaborative Work
- Architecture decisions (Phase 2)
- CLI design (Phase 3)
- Testing strategy (all phases)
- Documentation (Phase 6)

---

## Dependencies & Risks

### Dependencies
| Phase | Depends On | Blocker If |
|-------|-----------|-----------|
| Phase 2 | Phase 1 complete | Website not launched |
| Phase 3 | Phase 2 validation | Compression doesn't work |
| Phase 4 | Phase 3 stable | Git abstraction broken |
| Phase 5 | Phase 3 stable | Git backend not working |
| Phase 6 | Phase 3-5 complete | Core features incomplete |

### Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Git performance worse than expected | Medium | High | Phase 2 benchmarks catch early |
| Delta compression <50% | Low | Medium | Still valuable for other Git features |
| Migration breaks existing sessions | Low | High | Extensive testing + rollback plan |
| Users find Git abstraction leaky | Medium | Medium | User testing in Phase 3 |
| Vector DB + Git integration complex | Medium | Low | Phase 4 is optional enhancement |

---

## Decision Points

### After Phase 1:
**Decision:** Proceed with Git integration or optimize current architecture?
- **If Empirica adoption is high:** Proceed (scalability matters)
- **If adoption is low:** Delay (focus on features/marketing)
- **If performance is fine:** Delay (optimization not needed)

### After Phase 2:
**Decision:** Full Git integration or hybrid approach?
- **If compression >60%:** Full integration
- **If compression <40%:** Hybrid (Git for some use cases)
- **If performance issues:** Reconsider architecture

### After Phase 3:
**Decision:** Vector DB integration worth it?
- **If semantic search is requested:** Yes (Phase 4)
- **If SQL queries sufficient:** No (Phase 4 optional)
- **If organizational learning is priority:** Yes (Phase 4 critical)

---

## Success Metrics

### Phase 1 (Current Empirica)
- [ ] Website live with 100+ visits/week
- [ ] 5+ GitHub stars
- [ ] 2+ external contributors
- [ ] 10+ real sessions tracked

### Phase 2 (Research)
- [ ] Compression ratio measured: >60%
- [ ] Git operations <100ms
- [ ] Prototype demonstrates feasibility

### Phase 3 (Sentinel)
- [ ] 100% CLI command parity
- [ ] Zero user-visible Git commands
- [ ] Migration success rate >99%
- [ ] Test coverage >90%

### Phase 4 (Vector DB)
- [ ] Semantic search <2s latency
- [ ] Search relevance >80% (human eval)

### Phase 5 (Dashboard)
- [ ] Real-time Git log streaming works
- [ ] Time-travel feature tested

### Phase 6 (Hardening)
- [ ] 100% commits GPG signed
- [ ] Backup/restore tested (1TB data)
- [ ] Multi-user testing (10+ concurrent)

---

## Documentation Plan

### User-Facing Docs (Phase 1)
- Getting started guide
- CLI reference
- Architecture overview
- Examples / tutorials

### Developer Docs (Phase 3)
- SentinelGitManager API
- Git integration architecture
- Migration guide
- Contributing guide

### Advanced Docs (Phase 6)
- Performance tuning
- Enterprise deployment
- Multi-user setup
- Backup/disaster recovery

---

## Marketing Angle (Post Phase 6)

### Tagline
**"Empirica Sentinel: Making Git Sexy Again Through Metacognition"**

### Value Props
1. **For AI Developers:** "Version cognitive states like you version code"
2. **For Enterprises:** "Cryptographic provenance + 67% storage reduction"
3. **For Researchers:** "Time-travel debugging for AI reasoning"
4. **For Multi-AI Systems:** "Git-native handoff between AI providers"

### Differentiation
| Feature | Empirica Sentinel | LangSmith | MLFlow | W&B |
|---------|-------------------|-----------|--------|-----|
| Epistemic versioning | ✅ Git-native | ❌ | ❌ | ❌ |
| Delta compression | ✅ 67% | ❌ | ❌ | ❌ |
| Multi-AI handoff | ✅ Git branches | ❌ | ❌ | ❌ |
| Time-travel debugging | ✅ git log | ⚠️ traces | ❌ | ❌ |
| Semantic search | ✅ Vector DB | ⚠️ tags | ❌ | ❌ |
| Zero Git knowledge | ✅ Sentinel | N/A | N/A | N/A |

---

## Next Steps (Immediate)

### This Week
1. ✅ Document Git integration vision (this file)
2. ⚠️ Focus on Phase 1 completion
   - Guide MiniMax through P1-P2
   - Complete website content
   - Update Phase 8 docs

### Next Week  
3. Review Phase 1 completion
4. Decision: Start Phase 2 research or continue Phase 1 polish?

### Month 2
5. If Phase 1 solid: Start Phase 2 benchmarks
6. If Phase 1 needs work: Delay Git integration

---

## Appendix: Git Integration Principles

### Design Principles
1. **Invisible by default** - Users never see Git unless they want to
2. **Progressive disclosure** - OSDs can drop down to Git level
3. **Automatic everything** - Sentinel handles commits/branches/merges
4. **Fail gracefully** - If Git breaks, fall back to SQLite
5. **Migration friendly** - Existing sessions migrate cleanly

### Non-Goals
- ❌ Replace Git entirely (it's substrate, not abstraction)
- ❌ Teach users Git (they use Empirica CLI)
- ❌ Support all Git features (just versioning/branching/merging)
- ❌ Distributed remotes (local Git repo only)
- ❌ Complex Git workflows (simple linear commits)

### Architecture Invariants
- Git is implementation detail of storage layer
- Postgres remains source of truth for metadata
- Vector DB remains source of truth for semantic search
- Reflex logs remain human-readable audit trail
- CLI remains simple and semantic

---

**Status:** Draft v1.0  
**Author:** Claude (with David Van Assche)  
**Last Updated:** 2024-11-14  
**Next Review:** After Phase 1 completion

**File stored:** `/home/yogapad/empirical-ai/empirica/GIT_INTEGRATION_ROADMAP.md`
