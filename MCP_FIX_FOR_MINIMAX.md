# MCP Communication Fix for Minimax

## 🎯 Problem Identified

**Error:** `"object dict can't be used in 'await' expression"`

**Root Cause:** The MCP server has async/await issues in some tool handlers. Direct Python API works perfectly, but MCP protocol communication fails.

## ✅ Your Environment is CORRECT

**Confirmed Working:**
- ✅ Python venv setup is correct
- ✅ All Empirica imports work (`SessionDatabase`, `GoalRepository`, etc.)
- ✅ MCP server starts and lists 37 tools correctly
- ✅ `mcp==1.21.0` is installed properly
- ✅ PYTHONPATH is set correctly

**The issue is NOT your environment - it's a bug in the MCP server code itself.**

## 🔧 Temporary Workaround

Until we fix the async issues, use the **Python API directly** instead of MCP tools:

### Instead of MCP Tools:
```python
# ❌ Don't use (broken due to async issue):
bootstrap_session(ai_id="mini-agent", session_type="development")
```

### Use Python API Directly:
```python
# ✅ Use this (works perfectly):
import sys
sys.path.insert(0, '/home/yogapad/empirical-ai/empirica')

from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_metacognition
from empirica.data.session_database import SessionDatabase

# Bootstrap
config = bootstrap_metacognition("mini-agent", level=2)
db = SessionDatabase()
session_id = db.create_session(
    ai_id="mini-agent",
    bootstrap_level=2,
    components_loaded=len(config),
    user_id=None
)
db.close()

print(f"✅ Session created: {session_id}")
print(f"✅ Components: {list(config.keys())}")
```

### For Goal Adoption:
```python
from empirica.core.goals.repository import GoalRepository

repo = GoalRepository()
goal = repo.get_goal('16ae0d29-2919-49e5-b67f-3853e02e0297')  # Your goal ID

if goal:
    success = repo.save_goal(goal, session_id)
    print(f'✅ Adopted goal into session: {success}')
else:
    print('❌ Goal not found')

repo.close()
```

### For Subtasks:
```python
from empirica.core.tasks.repository import TaskRepository

task_repo = TaskRepository()
subtasks = task_repo.get_goal_subtasks('16ae0d29-2919-49e5-b67f-3853e02e0297')

for st in subtasks:
    print(f'{st.description}')
    print(f'  Status: {st.status.value}')
    print(f'  Importance: {st.epistemic_importance.value}')
    print(f'  ID: {st.id}')

task_repo.close()
```

### Complete Subtask:
```python
task_repo = TaskRepository()
task_repo.complete_task(
    task_id='subtask-id',
    completion_evidence='commit hash or description'
)
task_repo.close()
```

## 🚀 Your Goal (Use Python API)

**Goal ID:** `16ae0d29-2919-49e5-b67f-3853e02e0297`

**Tasks:**
1. Auto-goal generation from PREFLIGHT (modify `execute_preflight`)
2. Update system prompts with decision criteria

**Spec:** `docs/current_work/EMPIRICA_RELIABILITY_IMPROVEMENTS_SPEC.md`

## 📝 Complete Workflow with Python API

```python
#!/usr/bin/env python3
"""
Mini-agent: Reliability improvements using Python API
(MCP tools have async issues - using direct API instead)
"""

import sys
sys.path.insert(0, '/home/yogapad/empirical-ai/empirica')

from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_metacognition
from empirica.data.session_database import SessionDatabase
from empirica.core.goals.repository import GoalRepository
from empirica.core.tasks.repository import TaskRepository

# 1. Bootstrap session
print("1️⃣ Bootstrapping session...")
config = bootstrap_metacognition("mini-agent", level=2)

db = SessionDatabase()
session_id = db.create_session(
    ai_id="mini-agent",
    bootstrap_level=2,
    components_loaded=len(config),
    user_id=None
)
db.close()

print(f"✅ Session: {session_id[:8]}...")
print(f"✅ Components: {list(config.keys())}")

# 2. Adopt goal from Claude Code
print("\n2️⃣ Adopting goal...")
goal_id = '16ae0d29-2919-49e5-b67f-3853e02e0297'

repo = GoalRepository()
goal = repo.get_goal(goal_id)

if goal:
    success = repo.save_goal(goal, session_id)
    print(f"✅ Goal adopted: {success}")
else:
    print("❌ Goal not found")
    sys.exit(1)

repo.close()

# 3. List subtasks
print("\n3️⃣ Subtasks:")
task_repo = TaskRepository()
subtasks = task_repo.get_goal_subtasks(goal_id)

for i, st in enumerate(subtasks, 1):
    status_emoji = "✅" if st.status.value == "completed" else "⏳"
    print(f"{status_emoji} {i}. {st.description}")
    print(f"   Status: {st.status.value}")
    print(f"   Importance: {st.epistemic_importance.value}")
    print(f"   ID: {st.id}")

task_repo.close()

# 4. Execute PREFLIGHT (manual for now - MCP async issue)
print("\n4️⃣ Execute PREFLIGHT manually:")
print("   Assess your 13 epistemic vectors before starting work")
print("   (Use Python API or wait for MCP fix)")

# 5. Work on tasks!
print("\n5️⃣ Ready to work!")
print(f"   Goal: {goal.objective if goal else 'N/A'}")
print(f"   Subtasks: {len(subtasks)}")
print(f"   Spec: docs/current_work/EMPIRICA_RELIABILITY_IMPROVEMENTS_SPEC.md")
```

## 🔍 Diagnostic Results

Ran `python3 debug_mcp_communication.py`:

```
✅ Direct Python API: WORKING
  ✅ SessionDatabase imported
  ✅ Database accessible (118 sessions found)
  ✅ GoalRepository functional

✅ MCP Server Startup: WORKING
  ✅ MCP server found and starts correctly
  ✅ 37 tools registered

❌ MCP Protocol Communication: PARTIAL
  ✅ Server initializes successfully
  ✅ Tools list correctly (37 tools)
  ❌ bootstrap_session fails with async error
```

## 🎯 Bottom Line for Minimax

**You did everything right!** The MCP dependency is installed, your venv works, Empirica imports correctly. The issue is in our MCP server code (async/await handling).

**Recommendation:** Use the Python API directly (code above) to complete your tasks. It's actually simpler and faster than going through MCP!

When we fix the async issues in the MCP server, you can switch back to MCP tools if you prefer. But the Python API is the "source of truth" and will always work.

---

**Questions?** Check the diagnostic script: `python3 debug_mcp_communication.py`
