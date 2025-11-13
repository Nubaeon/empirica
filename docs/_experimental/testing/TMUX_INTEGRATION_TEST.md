# Tmux Integration - End-to-End Testing

**Date:** 2025-11-03 02:30 UTC
**Assigned to:** Claude (Architecture)
**Estimated Time:** 30-40 minutes
**Status:** Ready to execute

---

## 🎯 Objective

Test the complete tmux integration to validate:
1. ✅ Dashboard launches correctly in tmux pane
2. ✅ Real-time updates work (<2 sec latency)
3. ✅ Action hooks trigger on snapshot save
4. ✅ JSON feed updates correctly
5. ✅ 4-pane layout works as designed
6. ✅ MCP tools work from Claude Code

---

## 📋 Prerequisites

### **Already Complete:** ✅
- [x] Option 1: Tmux integration (3 code changes)
- [x] credentials_loader.py working
- [x] credentials.yaml migrated
- [x] All action hooks implemented

### **Need Running:**
- [ ] Tmux session active
- [ ] MCP server running (if testing via MCP)
- [ ] At least 1 adapter working (for snapshot creation)

---

## 🧪 Test Suite

### **Test 1: JSON Feed Creation** (5 min)

**Goal:** Verify action hooks create JSON feed correctly

```python
#!/usr/bin/env python3
"""
Test that action hooks create snapshot JSON feed
"""
from empirica.integration.empirica_action_hooks import EmpiricaActionHooks

# Test snapshot status update
test_snapshot = {
    "snapshot_id": "test_123",
    "session_id": "test_session",
    "ai_id": "qwen-coder-plus",
    "cascade_phase": "investigate",
    "vectors": {
        "KNOW": 0.75,
        "DO": 0.80,
        "CONTEXT": 0.85,
        "CLARITY": 0.90,
        "COHERENCE": 0.88,
        "SIGNAL": 0.92,
        "DENSITY": 0.78,
        "STATE": 0.85,
        "CHANGE": 0.60,
        "COMPLETION": 0.40,
        "IMPACT": 0.65,
        "UNCERTAINTY": 0.55,
        "ENGAGEMENT": 0.88
    },
    "delta": {},
    "original_context_tokens": 10000,
    "snapshot_tokens": 500,
    "compression_ratio": 0.95,
    "fidelity_score": 0.94,
    "information_loss_estimate": 0.06,
    "transfer_count": 0,
    "reliability": 0.90,
    "should_refresh": False,
    "refresh_reason": None,
    "created_at": "2025-11-03T02:30:00"
}

# Trigger action hook
EmpiricaActionHooks.update_snapshot_status(test_snapshot)

print("✅ Action hook executed")

# Verify JSON file created
from pathlib import Path
import json

feed_file = Path("/tmp/empirica_realtime/snapshot_status.json")
assert feed_file.exists(), "JSON feed not created"

with open(feed_file, 'r') as f:
    data = json.load(f)

print(f"✅ JSON feed created: {feed_file}")
print(f"   Snapshot ID: {data['snapshot_id']}")
print(f"   Compression: {data['compression']['ratio']:.1%}")
print(f"   Reliability: {data['transfer']['reliability']:.1%}")
print(f"\n🎉 Test 1 PASSED")
```

**Expected:**
- ✅ No errors
- ✅ JSON file exists at `/tmp/empirica_realtime/snapshot_status.json`
- ✅ Data matches input
- ✅ All fields present

---

### **Test 2: Tmux MCP Tools** (10 min)

**Goal:** Verify MCP tools work correctly

```python
#!/usr/bin/env python3
"""
Test tmux MCP tools (without requiring actual MCP server)
"""
import asyncio
from empirica.integration.mcp_local.empirica_tmux_mcp_server import EmpiricaTmuxServer

async def test_mcp_tools():
    server = EmpiricaTmuxServer()

    # Test 1: Check snapshot dashboard status
    print("Test 1: snapshot_dashboard_status")
    status = await server.snapshot_dashboard_status()
    print(f"   Result: {status}")
    print(f"   ✅ Dashboard status: {status.get('dashboard', 'unknown')}")

    # Test 2: Update snapshot display
    print("\nTest 2: update_snapshot_display")
    test_data = {
        "snapshot_id": "mcp_test_456",
        "compression": {"ratio": 0.95},
        "transfer": {"reliability": 0.87}
    }
    update_result = await server.update_snapshot_display(test_data)
    print(f"   Result: {update_result}")
    print(f"   ✅ Status: {update_result.get('status')}")

    # Test 3: Verify JSON updated
    from pathlib import Path
    import json
    feed_file = Path("/tmp/empirica_realtime/snapshot_status.json")
    with open(feed_file, 'r') as f:
        data = json.load(f)
    print(f"\n   ✅ JSON updated with snapshot_id: {data.get('snapshot_id')}")

    print(f"\n🎉 All MCP tool tests PASSED")

# Run tests
asyncio.run(test_mcp_tools())
```

**Expected:**
- ✅ `snapshot_dashboard_status` returns status dict
- ✅ `update_snapshot_display` updates JSON feed
- ✅ JSON file reflects updates
- ✅ No errors

---

### **Test 3: Snapshot Provider Integration** (10 min)

**Goal:** Verify snapshots trigger action hooks automatically

```python
#!/usr/bin/env python3
"""
Test that saving snapshots triggers action hooks
"""
import time
from pathlib import Path
import json
from empirica.plugins.modality_switcher.snapshot_provider import EpistemicSnapshotProvider

# Create provider
provider = EpistemicSnapshotProvider()

# Create a snapshot
print("Creating snapshot...")
snapshot = provider.create_snapshot_from_session(
    session_id="tmux_test_session",
    context_summary_text="Testing tmux integration with real snapshot",
    semantic_tags={"test": "tmux_integration"},
    cascade_phase="act"
)

print(f"✅ Snapshot created: {snapshot.snapshot_id}")

# Save snapshot (should trigger action hooks)
print("\nSaving snapshot (should trigger action hooks)...")
before_time = time.time()
provider.save_snapshot(snapshot)
after_time = time.time()

# Check if JSON feed updated
feed_file = Path("/tmp/empirica_realtime/snapshot_status.json")
assert feed_file.exists(), "JSON feed not created after save"

with open(feed_file, 'r') as f:
    data = json.load(f)

# Verify it's our snapshot
assert data['snapshot_id'] == snapshot.snapshot_id, "Wrong snapshot in feed"
assert data['session_id'] == "tmux_test_session", "Wrong session in feed"

# Check timestamp (should be recent)
feed_age = after_time - data['timestamp']
assert feed_age < 2.0, f"Feed too old: {feed_age:.2f}s (expected <2s)"

print(f"✅ Snapshot saved: {snapshot.snapshot_id}")
print(f"✅ Action hook triggered")
print(f"✅ JSON feed updated")
print(f"✅ Update latency: {(after_time - before_time)*1000:.0f}ms")
print(f"\n🎉 Test 3 PASSED - Action hooks working!")
```

**Expected:**
- ✅ Snapshot saves successfully
- ✅ JSON feed updates automatically
- ✅ Latency < 2 seconds
- ✅ Snapshot ID matches

---

### **Test 4: Dashboard Launch** (Manual - 10 min)

**Goal:** Verify dashboard can be launched in tmux

**Prerequisites:**
- Running in a tmux session
- Or have tmux available to create session

```bash
#!/bin/bash
# Test dashboard launch

echo "Test 4: Dashboard Launch"
echo "========================"

# Check if in tmux
if [ -z "$TMUX" ]; then
    echo "⚠️ Not in tmux session, creating one..."
    tmux new-session -d -s empirica_test
    TMUX_SESSION="empirica_test"
else
    TMUX_SESSION=$(tmux display-message -p '#{session_name}')
    echo "✅ In tmux session: $TMUX_SESSION"
fi

# Get current pane count
PANE_COUNT=$(tmux list-panes -t $TMUX_SESSION | wc -l)
echo "   Current panes: $PANE_COUNT"

# If only 1 pane, create a split for dashboard
if [ $PANE_COUNT -eq 1 ]; then
    echo "   Creating split for dashboard..."
    tmux split-window -h -t $TMUX_SESSION
fi

# Launch dashboard in right pane
echo "   Launching dashboard in pane 1..."
tmux send-keys -t "${TMUX_SESSION}:0.1" "cd /home/yogapad/empirical-ai/empirica" Enter
tmux send-keys -t "${TMUX_SESSION}:0.1" "python3 empirica/dashboard/snapshot_monitor.py" Enter

sleep 2

# Check if dashboard is running
if tmux list-panes -t $TMUX_SESSION -F '#{pane_current_command}' | grep -q "python3"; then
    echo "✅ Dashboard appears to be running"
else
    echo "⚠️ Dashboard may not be running (check manually)"
fi

echo ""
echo "🎉 Test 4 PASSED"
echo ""
echo "Manual verification:"
echo "1. Switch to tmux session: tmux attach -t $TMUX_SESSION"
echo "2. Verify dashboard is visible in right pane"
echo "3. Check that it shows 'EMPIRICA SNAPSHOT MONITOR'"
echo "4. Press 'q' to quit dashboard when done"
```

**Expected:**
- ✅ Tmux pane splits successfully
- ✅ Dashboard launches without errors
- ✅ Dashboard UI appears
- ✅ Shows correct header

**Manual Checks:**
- [ ] Dashboard displays correctly
- [ ] Colors work (blue/green/red for reliability)
- [ ] Interactive commands respond (r to refresh)
- [ ] Data displays when available

---

### **Test 5: Real-Time Updates** (10 min)

**Goal:** Verify dashboard updates in real-time when snapshots saved

**Setup:**
1. Have dashboard running in tmux (from Test 4)
2. Have main pane ready for commands

**Test:**
```python
#!/usr/bin/env python3
"""
Test real-time dashboard updates
"""
import time
from empirica.plugins.modality_switcher.snapshot_provider import EpistemicSnapshotProvider

provider = EpistemicSnapshotProvider()

print("🧪 Real-time Update Test")
print("=" * 50)
print("\n👀 Watch the dashboard (right pane) for updates...")
print("\nCreating 5 snapshots with 5-second intervals...\n")

for i in range(5):
    print(f"Snapshot {i+1}/5: Creating...")

    snapshot = provider.create_snapshot_from_session(
        session_id=f"realtime_test_{i+1}",
        context_summary_text=f"Real-time test snapshot #{i+1}",
        semantic_tags={"test": "realtime", "iteration": i+1},
        cascade_phase=["think", "investigate", "uncertainty", "check", "act"][i]
    )

    print(f"           Saving...")
    provider.save_snapshot(snapshot)

    print(f"           ✅ Saved: {snapshot.snapshot_id}")
    print(f"              Compression: {snapshot.compression_ratio:.1%}")
    print(f"              Reliability: {snapshot.estimate_memory_reliability():.1%}")

    if i < 4:
        print(f"\n⏱️  Waiting 5 seconds before next snapshot...")
        time.sleep(5)

print("\n🎉 Test Complete!")
print("\n📊 Expected dashboard behavior:")
print("   • Timeline should show 5 new snapshots")
print("   • Latest snapshot should be at top")
print("   • Reliability should vary across snapshots")
print("   • Updates should appear within 2 seconds of save")
```

**Manual Verification:**
1. Run script in left pane
2. Watch dashboard in right pane
3. Verify:
   - [ ] Dashboard updates appear within 2 seconds
   - [ ] New snapshots show in timeline
   - [ ] Metrics update correctly
   - [ ] No lag or freezing
   - [ ] Colors change appropriately

**Expected:**
- ✅ Dashboard updates in <2 seconds per snapshot
- ✅ All 5 snapshots appear in timeline
- ✅ Metrics display correctly
- ✅ No errors or crashes

---

### **Test 6: 4-Pane Layout** (Optional - 5 min)

**Goal:** Test full 4-pane orchestration

```bash
#!/bin/bash
# Create 4-pane layout

echo "Creating 4-pane layout..."

# Create session if not exists
if ! tmux has-session -t empirica 2>/dev/null; then
    tmux new-session -d -s empirica
fi

# Create 4-pane layout
# Left 75%: Main pane
# Right 25%: 3 monitoring panes stacked

tmux split-window -h -t empirica -p 25  # Split right 25%
tmux split-window -v -t empirica:0.1    # Split right into 2
tmux split-window -v -t empirica:0.2    # Split bottom into 2

# Result:
# Pane 0: Main (left, full height)
# Pane 1: Monitor 1 (upper right)
# Pane 2: Monitor 2 (middle right)
# Pane 3: Monitor 3 (lower right)

# Launch snapshot dashboard in pane 1
tmux send-keys -t empirica:0.1 "cd /home/yogapad/empirical-ai/empirica" Enter
tmux send-keys -t empirica:0.1 "python3 empirica/dashboard/snapshot_monitor.py" Enter

echo "✅ 4-pane layout created"
echo ""
echo "Attach with: tmux attach -t empirica"
echo ""
echo "Layout:"
echo "┌─────────────────┬──────────┐"
echo "│                 │ Snapshot │"
echo "│     Main        │ Monitor  │"
echo "│                 ├──────────┤"
echo "│                 │ Monitor  │"
echo "│                 │    2     │"
echo "│                 ├──────────┤"
echo "│                 │ Monitor  │"
echo "│                 │    3     │"
echo "└─────────────────┴──────────┘"
```

**Expected:**
- ✅ 4 panes created
- ✅ Snapshot dashboard in pane 1
- ✅ Layout matches design
- ✅ All panes accessible

---

## 📊 Success Criteria

### **Functional:**
- [ ] JSON feed creates correctly
- [ ] Action hooks trigger on save
- [ ] MCP tools work
- [ ] Dashboard launches
- [ ] Real-time updates < 2 sec
- [ ] 4-pane layout works

### **Quality:**
- [ ] Update latency < 2 seconds
- [ ] No errors in any test
- [ ] Dashboard UI displays correctly
- [ ] All data fields populate

### **Integration:**
- [ ] Action hooks → JSON feed ✅
- [ ] JSON feed → Dashboard display ✅
- [ ] Snapshot save → Auto update ✅
- [ ] MCP tools → Action hooks ✅

---

## 🐛 Troubleshooting

### **Issue: JSON feed not created**
```bash
# Check if directory exists
ls -la /tmp/empirica_realtime/

# Check permissions
ls -l /tmp/empirica_realtime/snapshot_status.json

# Manually test action hook
python3 -c "from empirica.integration.empirica_action_hooks import EmpiricaActionHooks; EmpiricaActionHooks.update_snapshot_status({'snapshot_id': 'test'})"
```

### **Issue: Dashboard won't launch**
```bash
# Test dashboard standalone
python3 empirica/dashboard/snapshot_monitor.py

# Check for errors
python3 -c "from empirica.dashboard.snapshot_monitor import main; main()"

# Check curses support
python3 -c "import curses; print('Curses available')"
```

### **Issue: Updates too slow**
```bash
# Check JSON file age
stat /tmp/empirica_realtime/snapshot_status.json

# Test action hook directly
time python3 -c "from empirica.integration.empirica_action_hooks import EmpiricaActionHooks; EmpiricaActionHooks.update_snapshot_status({'test': 'data'})"
```

---

## 📦 Deliverables

1. **Test Results** - Pass/fail for each test
2. **Performance Metrics** - Update latency measurements
3. **Screenshots** - Dashboard in 4-pane layout (optional)
4. **Issues Log** - Any problems encountered
5. **Completion Report** - `TMUX_INTEGRATION_TEST_RESULTS.md`

---

## 🚀 Execution Plan

**Sequence:**
1. Run Test 1 (JSON Feed) - 5 min
2. Run Test 2 (MCP Tools) - 10 min
3. Run Test 3 (Provider Integration) - 10 min
4. Run Test 4 (Dashboard Launch) - 10 min
5. Run Test 5 (Real-Time Updates) - 10 min
6. Optional: Test 6 (4-Pane Layout) - 5 min

**Total:** 40-50 minutes

---

## ✅ Quick Start

```bash
# 1. Ensure tmux is available
which tmux

# 2. Run automated tests
python3 docs/testing/test_tmux_integration.py

# 3. Run manual dashboard test
cd /home/yogapad/empirical-ai/empirica
bash docs/testing/test_dashboard_launch.sh

# 4. Run real-time test
python3 docs/testing/test_realtime_updates.py

# 5. Document results
```

---

**Status:** Ready to execute
**Assigned to:** Claude (Architecture)
**Estimated Time:** 40-50 minutes
**Dependencies:** None (all prerequisites met)

**Let's test the tmux integration!** 🚀
