# Plugin Architecture Migration Plan

**Date:** 2025-11-02  
**Goal:** Consolidate modality_switcher into proper plugin architecture  
**Status:** 🔄 IN PROGRESS

---

## 🎯 Problem

Current scattered architecture:
```
/empirica/core/modality/          # ModalitySwitcher core (NEW, 554 lines)
/modality_switcher/               # Original development (OLD, adapters here)
  ├── adapters/                   # ACTUAL adapters (minimax, qwen, local)
  ├── core/epistemic_router.py    # Router logic
  └── setup.py                    # Standalone package config
```

**Issues:**
- Imports use `modality_switcher.adapters` but core is in `empirica.core.modality`
- Duplicate/conflicting code
- Not truly pluggable
- Confusing for contributors

---

## ✅ Target Architecture

```
empirica/
├── empirica/
│   ├── cli/                      # Core Empirica CLI
│   ├── core/                     # Core utilities (NO modality)
│   └── plugins/                  # Plugin system ⭐ NEW
│       ├── __init__.py          # Plugin loader
│       ├── base_plugin.py       # Plugin interface
│       └── modality_switcher/   # ModalitySwitcher plugin
│           ├── __init__.py
│           ├── plugin_manifest.json
│           ├── modality_switcher.py       # Core logic
│           ├── plugin_registry.py         # Registry
│           ├── register_adapters.py       # Registration
│           ├── auth_manager.py            # Auth
│           ├── config_loader.py           # Config
│           ├── usage_monitor.py           # Monitoring
│           ├── adapters/                  # All adapters
│           │   ├── __init__.py
│           │   ├── base_adapter.py
│           │   ├── minimax_adapter.py     # Phase 1 ✅
│           │   ├── qwen_adapter.py        # Phase 1 ✅
│           │   ├── local_adapter.py       # Stub
│           │   ├── rovodev_adapter.py     # Phase 4 🔄
│           │   ├── github_copilot_adapter.py  # Phase 4 🔄
│           │   ├── gemini_adapter.py      # Phase 4 ⏳
│           │   ├── openrouter_adapter.py  # Phase 4 ⏳
│           │   ├── deepseek_adapter.py    # Phase 4 ⏳
│           │   └── qodo_adapter.py        # Phase 4 ⏳
│           └── tests/                     # All tests
│               ├── test_modality_switcher.py
│               ├── test_plugin_registry.py
│               └── adapters/
│                   ├── test_minimax_adapter.py
│                   ├── test_qwen_adapter.py
│                   └── ...
│
└── modality_switcher/            # DEPRECATED ⏳
    └── (move to deprecated/)
```

---

## 📋 Migration Steps

### Phase 1: Create Plugin Structure ✅
- [x] Create `empirica/plugins/` directory
- [x] Create `empirica/plugins/modality_switcher/` 
- [x] Create adapter and test subdirectories
- [ ] Create `plugin_manifest.json`
- [ ] Create `empirica/plugins/__init__.py` (plugin loader)
- [ ] Create `empirica/plugins/base_plugin.py` (interface)

### Phase 2: Merge Core Components
**Source:** `/empirica/core/modality/` + `/modality_switcher/core/`  
**Destination:** `/empirica/plugins/modality_switcher/`

- [ ] `modality_switcher.py` (from empirica/core/modality/) ✅ Keep this
- [ ] `plugin_registry.py` (from empirica/core/modality/) ✅ Keep this
- [ ] `register_adapters.py` (from empirica/core/modality/) - Update imports
- [ ] `auth_manager.py` (from empirica/core/modality/)
- [ ] `config_loader.py` (from empirica/core/modality/)
- [ ] `usage_monitor.py` (from empirica/core/modality/)
- [ ] `epistemic_router.py` (from modality_switcher/core/) - Merge if needed

### Phase 3: Consolidate Adapters
**Source:** `/modality_switcher/adapters/`  
**Destination:** `/empirica/plugins/modality_switcher/adapters/`

- [ ] `base_adapter.py` - Create from patterns
- [ ] `minimax_adapter.py` (361 lines) ✅
- [ ] `qwen_adapter.py` (319 lines) ✅
- [ ] `local_adapter.py` (133 lines) ✅
- [ ] New adapters (Phase 4)

### Phase 4: Consolidate Tests
**Source:** `/modality_switcher/adapters/test_*.py` + create new  
**Destination:** `/empirica/plugins/modality_switcher/tests/`

- [ ] `test_minimax_adapter.py` (184 lines) - Move
- [ ] `test_minimax_live.py` (178 lines) - Move
- [ ] `test_qwen_adapter.py` - CREATE NEW (Qwen's task)
- [ ] `test_plugin_registry.py` - Create
- [ ] `test_modality_switcher.py` - Create

### Phase 5: Update All Imports
**Files to update:**
- [ ] `empirica/cli/command_handlers/decision_commands.py`
- [ ] `empirica/cli/command_handlers/cascade_commands.py`
- [ ] `empirica/cli/command_handlers/monitor_commands.py`
- [ ] `empirica/cli/command_handlers/config_commands.py`
- [ ] `empirica/mcp_local/empirica_mcp_server.py`
- [ ] All adapter files

**Change:**
```python
# OLD
from empirica.core.modality.modality_switcher import ModalitySwitcher
from modality_switcher.adapters import MinimaxAdapter

# NEW
from empirica.plugins.modality_switcher import ModalitySwitcher
from empirica.plugins.modality_switcher.adapters import MinimaxAdapter
```

### Phase 6: Test & Validate
- [ ] Run all tests
- [ ] Test CLI commands
- [ ] Test MCP tools
- [ ] Test adapter registration
- [ ] Test routing strategies

### Phase 7: Deprecate Old Locations
- [ ] Move `/empirica/core/modality/` to `/docs/deprecated/`
- [ ] Move `/modality_switcher/` to `/docs/deprecated/`
- [ ] Update documentation
- [ ] Clean up imports

---

## 🔧 Implementation Commands

### Step 1: Copy Core Files
```bash
# Copy modality_switcher core
cp /empirica/core/modality/modality_switcher.py \
   /empirica/plugins/modality_switcher/

cp /empirica/core/modality/plugin_registry.py \
   /empirica/plugins/modality_switcher/

cp /empirica/core/modality/register_adapters.py \
   /empirica/plugins/modality_switcher/

cp /empirica/core/modality/auth_manager.py \
   /empirica/plugins/modality_switcher/

cp /empirica/core/modality/config_loader.py \
   /empirica/plugins/modality_switcher/

cp /empirica/core/modality/usage_monitor.py \
   /empirica/plugins/modality_switcher/
```

### Step 2: Copy Adapters
```bash
# Copy all adapters
cp /modality_switcher/adapters/*.py \
   /empirica/plugins/modality_switcher/adapters/

# Copy adapter docs
cp /modality_switcher/adapters/*.md \
   /empirica/plugins/modality_switcher/adapters/
```

### Step 3: Copy Tests
```bash
# Copy existing tests
cp /modality_switcher/adapters/test_*.py \
   /empirica/plugins/modality_switcher/tests/adapters/
```

### Step 4: Update Imports
```bash
# Find all import statements to update
grep -r "from empirica.core.modality" /empirica/empirica/
grep -r "from modality_switcher" /empirica/empirica/
```

---

## 📝 Import Map

### Before → After

| Old Import | New Import |
|------------|------------|
| `empirica.core.modality.modality_switcher` | `empirica.plugins.modality_switcher` |
| `empirica.core.modality.plugin_registry` | `empirica.plugins.modality_switcher.plugin_registry` |
| `empirica.core.modality.register_adapters` | `empirica.plugins.modality_switcher.register_adapters` |
| `modality_switcher.adapters` | `empirica.plugins.modality_switcher.adapters` |
| `modality_switcher.adapters.minimax_adapter` | `empirica.plugins.modality_switcher.adapters.minimax_adapter` |
| `modality_switcher.adapters.qwen_adapter` | `empirica.plugins.modality_switcher.adapters.qwen_adapter` |

---

## 🎯 Benefits

1. **Clear separation:** Plugins are truly pluggable
2. **Single source of truth:** All modality code in one place
3. **Easy extension:** Other plugins can follow same pattern
4. **Better imports:** Consistent `empirica.plugins.X` pattern
5. **Future-ready:** Easy to add Cognitive Vault, AUGIE, etc.

---

## ⚠️ Risks & Mitigation

**Risk:** Breaking existing code  
**Mitigation:** Update all imports atomically, test thoroughly

**Risk:** Missing dependencies  
**Mitigation:** Copy all files first, then update imports

**Risk:** Test failures  
**Mitigation:** Run tests after each step

---

## 📊 Progress Tracking

- [ ] Phase 1: Structure (0%)
- [ ] Phase 2: Core (0%)
- [ ] Phase 3: Adapters (0%)
- [ ] Phase 4: Tests (0%)
- [ ] Phase 5: Imports (0%)
- [ ] Phase 6: Testing (0%)
- [ ] Phase 7: Cleanup (0%)

**Estimated Time:** 2-3 hours  
**Priority:** HIGH (blocks v1.0.0 release)  
**Assignee:** Lead Architect

---

## ✅ Success Criteria

1. All code in `empirica/plugins/modality_switcher/`
2. No code in `/empirica/core/modality/`
3. No code in `/modality_switcher/` (deprecated)
4. All imports updated to `empirica.plugins.X`
5. All tests passing
6. CLI commands work
7. MCP tools work
8. Documentation updated
