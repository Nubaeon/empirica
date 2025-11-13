# Epistemic Snapshot System - Testing & Orchestration Plan

**Date:** 2025-11-03 00:00 UTC
**Objective:** Complete end-to-end testing with tmux dashboard integration
**Orchestration:** From Claude Code (this session)

---

## 🎯 Overview

We'll orchestrate a complete multi-AI snapshot transfer workflow from Claude Code, using:
- **Empirica MCP Server** - Snapshot management
- **Empirica Tmux MCP Server** - Dashboard visualization in tmux
- **Action Hooks** - Real-time dashboard updates
- **ModalitySwitcher** - Cross-AI transfers (Claude → Qwen → MiniMax)

---

## 📋 Testing Phases

### **Phase 0: Setup & Verification** (5 min)
**Goal:** Verify all components are ready

**Tasks:**
1. ✅ Phase 1-4 complete (core system, dashboard, MCP tools, adapters)
2. ⏸️ Phase 5 in progress (domain vectors - Rovodev working)
3. Add snapshot dashboard to tmux MCP server
4. Create snapshot action hooks
5. Test tmux pane orchestration

**Verification:**
```bash
# Check all adapters registered
python3 -c "from empirica.plugins.modality_switcher import get_registry; print(list(get_registry().adapters.keys()))"
# Expected: ['minimax', 'qwen', 'rovodev']

# Check MCP tools available
python3 -c "from empirica.integration.mcp_local.empirica_mcp_server import app; print([t.name for t in app.list_tools() if 'snapshot' in t.name])"
# Expected: ['snapshot_create', 'snapshot_get_latest', 'snapshot_export', 'snapshot_transfer']

# Check dashboard exists
ls empirica/dashboard/snapshot_monitor.py
# Expected: file exists
```

---

### **Phase 1: Tmux Dashboard Integration** (15 min)
**Goal:** Add snapshot dashboard to tmux MCP server with action hooks

#### **Task 1.1: Add Snapshot Action Hook**

**File:** `/empirica/integration/empirica_action_hooks.py`

**Add method:**
```python
@staticmethod
def update_snapshot_status(snapshot: Dict[str, Any]):
    """Update snapshot monitor JSON feed"""
    try:
        snapshot_data = {
            "timestamp": time.time(),
            "snapshot_id": snapshot.get("snapshot_id"),
            "session_id": snapshot.get("session_id"),
            "ai_id": snapshot.get("ai_id"),
            "cascade_phase": snapshot.get("cascade_phase"),
            "vectors": snapshot.get("vectors", {}),
            "delta": snapshot.get("delta", {}),
            "compression": {
                "original_tokens": snapshot.get("original_context_tokens", 0),
                "snapshot_tokens": snapshot.get("snapshot_tokens", 0),
                "ratio": snapshot.get("compression_ratio", 0.0),
                "fidelity": snapshot.get("fidelity_score", 1.0),
                "information_loss": snapshot.get("information_loss_estimate", 0.0)
            },
            "transfer": {
                "count": snapshot.get("transfer_count", 0),
                "reliability": snapshot.get("reliability", 1.0),
                "should_refresh": snapshot.get("should_refresh", False),
                "refresh_reason": snapshot.get("refresh_reason")
            },
            "created_at": snapshot.get("created_at", "")
        }

        output_file = REALTIME_DIR / "snapshot_status.json"
        with open(output_file, 'w') as f:
            json.dump(snapshot_data, f, indent=2)

        # Trigger immediate pane update
        trigger_pane_update('snapshot')

    except Exception as e:
        print(f"Warning: Could not update snapshot monitor feed: {e}")
```

#### **Task 1.2: Add Tmux MCP Tools**

**File:** `/mcp_local/empirica_tmux_mcp_server.py`

**Add to tool groups:**
```python
"snapshot_monitoring": [
    "launch_snapshot_dashboard",
    "snapshot_dashboard_status",
    "update_snapshot_display"
]
```

**Add methods:**
```python
async def launch_snapshot_dashboard(self, session_id: str = None, pane_id: str = None) -> Dict[str, Any]:
    """Launch snapshot monitor dashboard in tmux pane"""
    try:
        # Auto-detect session if not provided
        if not session_id:
            result = subprocess.run(['tmux', 'display-message', '-p', '#{session_name}'],
                                  capture_output=True, text=True)
            session_id = result.stdout.strip() if result.returncode == 0 else None

        if not session_id:
            return {"error": "No tmux session found"}

        # If pane not specified, create/use monitoring pane
        if not pane_id:
            # Check if we have a 4-pane layout (from orchestrate_panels)
            # Use upper-right pane (pane 1) for snapshot dashboard
            pane_id = f"{session_id}:0.1"

        # Launch dashboard in specified pane
        dashboard_cmd = f"python3 empirica/dashboard/snapshot_monitor.py {session_id if session_id != 'current' else ''}"

        subprocess.run(['tmux', 'send-keys', '-t', pane_id, dashboard_cmd, 'Enter'], check=True)

        return {
            "dashboard": "launched",
            "session": session_id,
            "pane": pane_id,
            "command": dashboard_cmd,
            "tool_group": "snapshot_monitoring"
        }
    except Exception as e:
        return {"error": f"Failed to launch dashboard: {e}"}

async def snapshot_dashboard_status(self) -> Dict[str, Any]:
    """Check if snapshot dashboard is running"""
    try:
        # Check if JSON feed file exists and is recent
        feed_file = Path("/tmp/empirica_realtime/snapshot_status.json")

        if feed_file.exists():
            mtime = feed_file.stat().st_mtime
            age_seconds = time.time() - mtime

            # Read current state
            with open(feed_file, 'r') as f:
                data = json.load(f)

            return {
                "dashboard": "active" if age_seconds < 5 else "stale",
                "feed_age_seconds": age_seconds,
                "last_snapshot": data.get("snapshot_id"),
                "reliability": data.get("transfer", {}).get("reliability"),
                "tool_group": "snapshot_monitoring"
            }
        else:
            return {
                "dashboard": "not_running",
                "message": "No snapshot feed detected",
                "tool_group": "snapshot_monitoring"
            }
    except Exception as e:
        return {"error": f"Dashboard status check failed: {e}"}
```

#### **Task 1.3: Integrate with Snapshot Provider**

**File:** `/empirica/plugins/modality_switcher/snapshot_provider.py`

**Add action hook calls:**
```python
def save_snapshot(self, snapshot: EpistemicStateSnapshot):
    """Save snapshot to database and trigger action hooks"""
    # ... existing save logic ...

    # NEW: Trigger action hooks for dashboard update
    try:
        from empirica.integration.empirica_action_hooks import EmpiricaActionHooks

        EmpiricaActionHooks.update_snapshot_status({
            "snapshot_id": snapshot.snapshot_id,
            "session_id": snapshot.session_id,
            "ai_id": snapshot.ai_id,
            "cascade_phase": snapshot.cascade_phase,
            "vectors": snapshot.vectors,
            "delta": snapshot.delta,
            "original_context_tokens": snapshot.original_context_tokens,
            "snapshot_tokens": snapshot.snapshot_tokens,
            "compression_ratio": snapshot.compression_ratio,
            "fidelity_score": snapshot.fidelity_score,
            "information_loss_estimate": snapshot.information_loss_estimate,
            "transfer_count": snapshot.transfer_count,
            "reliability": snapshot.estimate_memory_reliability(),
            "should_refresh": snapshot.should_refresh(),
            "refresh_reason": snapshot.get_refresh_reason(),
            "created_at": snapshot.created_at
        })
    except Exception as e:
        print(f"⚠️ Action hook update failed: {e}")

    print(f"📸 Snapshot saved: {snapshot.snapshot_id} (compression: {snapshot.compression_ratio:.1%})")
```

---

### **Phase 2: Orchestrated Workflow Layout** (10 min)
**Goal:** Set up optimal tmux layout for testing

**Proposed Layout (4 panes):**
```
┌─────────────────────────────────┬──────────────────┐
│                                 │                  │
│  Main Pane (Left 75%)          │  Snapshot        │
│  - Claude Code orchestration    │  Dashboard       │
│  - Test commands                │  (Upper Right    │
│  - Output                       │   25%)           │
│                                 │                  │
│                                 ├──────────────────┤
│                                 │                  │
│                                 │  12D Epistemic   │
│                                 │  Monitor         │
│                                 │  (Middle Right)  │
│                                 │                  │
│                                 ├──────────────────┤
│                                 │  Cascade Status  │
│                                 │  (Lower Right)   │
└─────────────────────────────────┴──────────────────┘
```

**Setup Commands (from Claude Code via MCP):**
```python
# 1. Orchestrate panels (creates 4-pane layout)
await mcp.call_tool("orchestrate_panels", {})

# 2. Launch snapshot dashboard in upper-right pane
await mcp.call_tool("launch_snapshot_dashboard", {
    "pane_id": "0.1"  # Upper-right pane
})

# 3. Verify dashboard running
status = await mcp.call_tool("snapshot_dashboard_status", {})
# Should show: "dashboard": "active"
```

---

### **Phase 3: End-to-End Snapshot Transfer Test** (20 min)
**Goal:** Complete multi-AI workflow with dashboard monitoring

#### **Test Scenario: Security Code Analysis**

**Step 1: Create Initial Snapshot (Claude)**
```python
# Via MCP from Claude Code
snapshot1 = await mcp.call_tool("snapshot_create", {
    "session_id": "claude_session_test",
    "context_summary": "Analyzing JWT authentication implementation for security vulnerabilities",
    "semantic_tags": {
        "domain": "security_analysis",
        "priority": "high",
        "investigation_outcome": "in_progress",
        "confidence": 0.75
    },
    "cascade_phase": "investigate",
    "domain_vectors": {
        "code_analysis": {
            "COMPLEXITY": 0.7,
            "SECURITY_RISK": 0.8,
            "PERFORMANCE": 0.6,
            "MAINTAINABILITY": 0.65
        }
    }
})

# Verify snapshot created
print(f"✅ Snapshot created: {snapshot1['snapshot_id']}")
print(f"   Compression: {snapshot1['compression_ratio']}")
print(f"   Fidelity: {snapshot1['fidelity_score']}")
```

**Expected Dashboard Display:**
```
Session: claude_s...  Model: claude-sonnet-4  Phase: INVESTIGATE
Compression: 95% (10,000 → 500 tokens)
Reliability: 90% 🔵 EXCELLENT
Transfer Count: 0
```

**Step 2: Transfer to Qwen for Deep Analysis**
```python
# Transfer to Qwen via MCP
transfer1 = await mcp.call_tool("snapshot_transfer", {
    "snapshot_id": snapshot1['snapshot_id'],
    "target_adapter": "qwen",
    "prompt": "Continue the security analysis. Focus on JWT token expiration and session management vulnerabilities.",
    "context_level": "standard"
})

print(f"✅ Transferred to Qwen (transfer #{transfer1['transfer_count']})")
print(f"   Reliability after transfer: {transfer1['reliability_after_transfer']}")
print(f"   Context tokens: {transfer1['context_tokens']}")
```

**Expected Dashboard Update:**
```
Session: qwen_ses...  Model: qwen-coder  Phase: INVESTIGATE
Compression: 95% (10,000 → 500 tokens)
Reliability: 87% 🟢 GOOD
Transfer Count: 1
Δ KNOW +0.15 📈 | Δ UNCERTAINTY -0.20 📉
```

**Step 3: Get Latest Snapshot After Qwen Analysis**
```python
# Retrieve updated snapshot
snapshot2 = await mcp.call_tool("snapshot_get_latest", {
    "session_id": "qwen_session_test"
})

# Check quality metrics
reliability = snapshot2['snapshot']['reliability']
should_refresh = snapshot2['snapshot']['should_refresh']

print(f"✅ Snapshot updated after Qwen analysis")
print(f"   Reliability: {reliability:.1%}")
print(f"   Should refresh: {should_refresh}")

if should_refresh:
    print(f"   ⚠️ Refresh reason: {snapshot2['snapshot']['refresh_reason']}")
```

**Step 4: Transfer to MiniMax for Recommendations**
```python
# Create new snapshot from Qwen session
snapshot3 = await mcp.call_tool("snapshot_create", {
    "session_id": "qwen_session_test",
    "context_summary": "Deep security analysis complete. Found 3 critical issues: JWT expiration, session fixation, CSRF token weakness.",
    "semantic_tags": {
        "domain": "security_analysis",
        "priority": "critical",
        "investigation_outcome": "critical_issues_found",
        "confidence": 0.92,
        "issues_found": 3
    },
    "cascade_phase": "act"
})

# Transfer to MiniMax for final recommendations
transfer2 = await mcp.call_tool("snapshot_transfer", {
    "snapshot_id": snapshot3['snapshot_id'],
    "target_adapter": "minimax",
    "prompt": "Based on the security analysis, provide actionable remediation recommendations with priority ordering.",
    "context_level": "full"  # Maximum context for final analysis
})

print(f"✅ Transferred to MiniMax (transfer #{transfer2['transfer_count']})")
print(f"   Multi-hop transfer complete: Claude → Qwen → MiniMax")
print(f"   Total context overhead: ~{transfer2['context_tokens']} tokens")
print(f"   Reliability: {transfer2['reliability_after_transfer']:.1%}")
```

**Expected Final Dashboard:**
```
Session: minimax_...  Model: minimax-m2  Phase: ACT
Compression: 95% (20,000 → 600 tokens across 2 hops)
Reliability: 84% 🟢 GOOD
Transfer Count: 2
Δ COMPLETION +0.40 🎯 | Δ KNOW +0.28 📈

Timeline (3 snapshots):
20:15 INVESTIGATE [Claude] KNOW 0.75 | UNCERTAINTY 0.65
20:22 ACT [Qwen] Δ KNOW +0.15 | Δ UNCERTAINTY -0.20
20:28 ACT [MiniMax] Δ COMPLETION +0.40 | Fidelity 0.92 ✅
```

**Step 5: Export Final Snapshot**
```python
# Export for documentation/review
export_result = await mcp.call_tool("snapshot_export", {
    "snapshot_id": snapshot3['snapshot_id'],
    "filepath": "test_results/security_analysis_snapshot.json"
})

print(f"✅ Snapshot exported: {export_result['filepath']}")
print(f"   File size: {export_result['file_size']} bytes")
print(f"   Compression: {export_result['compression_ratio']}")
```

---

### **Phase 4: Quality Validation** (10 min)
**Goal:** Verify compression, fidelity, and reliability metrics

**Checks:**
1. **Compression Target: 95%** ✅
   - Verify: original_tokens / snapshot_tokens ≥ 0.95
2. **Fidelity Target: >90%** ✅
   - Verify: fidelity_score ≥ 0.90
3. **Information Loss Target: <15%** ✅
   - Verify: information_loss_estimate ≤ 0.15
4. **Reliability Degradation: 3% per hop** ✅
   - Fresh: 90%
   - 1 hop: 87% (3% drop) ✅
   - 2 hops: 84% (6% total drop) ✅
5. **Context Overhead: <150 tokens** ✅
   - Minimal: 105 tokens ✅
   - Standard: 121 tokens ✅
   - Full: 135 tokens ✅

**Validation Script:**
```python
def validate_snapshot_quality(snapshot):
    """Comprehensive quality validation"""
    checks = {
        "compression_ratio": snapshot['compression_ratio'] >= 0.90,
        "fidelity_score": snapshot['fidelity_score'] >= 0.90,
        "information_loss": snapshot['information_loss_estimate'] <= 0.15,
        "reliability": snapshot['reliability'] >= 0.75
    }

    passed = sum(checks.values())
    total = len(checks)

    print(f"Quality Validation: {passed}/{total} checks passed")
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")

    return all(checks.values())
```

---

### **Phase 5: Stress Testing** (15 min)
**Goal:** Test limits and degradation patterns

#### **Test 1: Maximum Transfer Chain**
```python
# Create 10-hop transfer chain
# Claude → Qwen → MiniMax → Claude → Qwen → ... (10 transfers)

reliability_history = []
for i in range(10):
    # Transfer snapshot
    # Record reliability
    reliability_history.append(current_reliability)

# Plot degradation curve
# Expected: ~3% per hop, reaches 60% at 10 hops (refresh recommended at 5)
```

#### **Test 2: Large Context Compression**
```python
# Create snapshot from session with massive context (50k tokens)
# Verify: Still achieves 95%+ compression
# Verify: Fidelity remains >90%
```

#### **Test 3: Parallel Transfers**
```python
# Create 3 snapshots simultaneously
# Transfer to 3 different adapters in parallel
# Verify: No race conditions, all transfers successful
```

---

## 🎯 Success Criteria

### **Functional Requirements:**
- [Pending] Snapshot dashboard launches in tmux pane
- [Pending] Real-time updates via action hooks
- [Pending] Multi-AI transfers work (Claude → Qwen → MiniMax)
- [Pending] Dashboard shows correct metrics (compression, reliability, deltas)
- [Pending] Export/import workflow successful

### **Quality Requirements:**
- [Pending] Compression: ≥95% achieved
- [Pending] Fidelity: ≥90% achieved
- [Pending] Information loss: ≤15%
- [Pending] Reliability: Degrades predictably (3% per hop)
- [Pending] Context overhead: <150 tokens

### **Integration Requirements:**
- [Pending] Tmux MCP server integration working
- [Pending] Action hooks triggering correctly
- [Pending] Dashboard updates in real-time (<2 sec latency)
- [Pending] All 4 panes displaying correct info
- [Pending] Orchestration from Claude Code successful

---

## 📝 Test Execution Plan

### **From Claude Code (This Session):**

1. **Setup Phase** (Execute now):
   ```bash
   # 1. Add action hook to empirica_action_hooks.py
   # 2. Add MCP tools to empirica_tmux_mcp_server.py
   # 3. Update snapshot_provider.py with action hook calls
   # 4. Test components individually
   ```

2. **Integration Phase** (After setup):
   ```bash
   # 1. Start tmux session (if not already in one)
   # 2. Call orchestrate_panels MCP tool
   # 3. Launch snapshot dashboard in pane 1
   # 4. Verify dashboard displays
   ```

3. **Testing Phase** (After integration):
   ```bash
   # 1. Run Phase 3 end-to-end test
   # 2. Validate quality metrics (Phase 4)
   # 3. Optional: Run stress tests (Phase 5)
   ```

4. **Documentation Phase** (After testing):
   ```bash
   # 1. Capture test results
   # 2. Document any issues found
   # 3. Update PROJECT_STATUS_FINAL.md
   # 4. Create TESTING_RESULTS.md
   ```

---

## 🚀 Ready to Begin

**Next Steps:**
1. Apply the 3 code changes (action hooks, tmux MCP, snapshot provider)
2. Test tmux integration
3. Run end-to-end workflow
4. Validate quality metrics
5. Document results

**Estimated Total Time:** 60-75 minutes

---

**Status:** Ready to execute
**Orchestrator:** Claude Code (this session)
**Test Environment:** Tmux with 4-pane layout
**Target:** Complete validation of 80% complete system

**Let's do this! 🎉**
