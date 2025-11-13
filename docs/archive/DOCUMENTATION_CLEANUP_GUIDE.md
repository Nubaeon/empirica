# Documentation Cleanup Guide

**Date:** 2025-11-02  
**Purpose:** Clean workspace after plugin architecture migration  
**Action:** Move obsolete phase handoff docs to deprecated/

---

## ✅ Keep (Active Documentation)

### Core Documentation
- `README.md` - Main project README
- `API_DOCUMENTATION.md` - API reference
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - Project license
- `CHANGELOG.md` - Version history
- `QUICK_REFERENCE.md` - Quick start guide

### Current Status
- `CURRENT_STATUS_v2.1.md` - Latest status (should be updated)
- `REMAINING_TASKS.md` - Active task tracking

### New/Updated Docs (Keep These!)
- `docs/PLUGIN_ARCHITECTURE_MIGRATION.md` - Migration plan ✅
- `docs/PLUGIN_MIGRATION_COMPLETE.md` - Migration complete ✅
- `docs/PHASE3_TASK_HANDOFF_QWEN_ROVODEV.md` - Active handoff ✅
- `docs/HOW_TO_RESUME_SESSION.md` - Session resume guide
- `docs/development/STUB_TRACKER.md` - Development tracking

---

## 🗑️ Deprecate (Move to deprecated/phase_handoffs/)

### Old Phase Handoffs (Pre-Migration)
Move these to `/deprecated/phase_handoffs/`:

- `SESSION_HANDOFF_2025_11_01_PHASE2.md` - Outdated (pre-plugin migration)
- `PHASE3_COMPLETE.md` - Outdated (Phase 3 ongoing, not complete)
- `PHASE3_COMPLETE_SUMMARY.md` - Outdated
- `PHASE3_TASK3_COMPLETE.md` - Outdated
- `COMPLETE_SESSION_SUMMARY.txt` - Outdated
- `ARCHITECTURE_ALIGNMENT_SUMMARY.txt` - Pre-migration

### Implementation Plan:
```bash
cd /home/yogapad/empirical-ai/empirica

# Create deprecated directory for handoffs
mkdir -p deprecated/phase_handoffs

# Move old handoff docs
mv SESSION_HANDOFF_2025_11_01_PHASE2.md deprecated/phase_handoffs/
mv PHASE3_COMPLETE.md deprecated/phase_handoffs/
mv PHASE3_COMPLETE_SUMMARY.md deprecated/phase_handoffs/
mv PHASE3_TASK3_COMPLETE.md deprecated/phase_handoffs/
mv COMPLETE_SESSION_SUMMARY.txt deprecated/phase_handoffs/
mv ARCHITECTURE_ALIGNMENT_SUMMARY.txt deprecated/phase_handoffs/

# Create README in deprecated explaining what's there
cat > deprecated/phase_handoffs/README.md << 'EOF'
# Deprecated Phase Handoff Documents

These documents represent historical phase handoffs **before** the plugin architecture migration (2025-11-02).

## Why Deprecated?
On 2025-11-02, we completed a major refactor:
- Moved from `/empirica/core/modality/` to `/empirica/plugins/modality_switcher/`
- Moved from `/modality_switcher/` to `/empirica/plugins/modality_switcher/`
- Updated all imports to use `empirica.plugins.modality_switcher.*`

These old handoff docs reference outdated paths and import patterns.

## Current Documentation
See:
- `/docs/PLUGIN_MIGRATION_COMPLETE.md` - Migration summary
- `/docs/PHASE3_TASK_HANDOFF_QWEN_ROVODEV.md` - Current phase 3 tasks
- `/docs/PLUGIN_ARCHITECTURE_MIGRATION.md` - Architecture details

## Historical Value
Keep these for reference to understand:
1. What Phase 2 accomplished (ModalitySwitcher creation)
2. What Phase 3 Task 1-2 accomplished (CLI + MCP integration)
3. How the architecture evolved
EOF
```

---

## 📝 Update Current Status

**File:** `CURRENT_STATUS_v2.1.md`

Should reflect:
1. ✅ Phase 0-2: Complete (100%)
2. 🔄 Phase 3: In Progress (50% - CLI + MCP done, Qwen tests + Rovodev pending)
3. ⏳ Phase 4: Not started (deployment, additional adapters)

Update to reference new plugin architecture.

---

## 📋 Cleanup Checklist

- [ ] Move 6 old handoff docs to `deprecated/phase_handoffs/`
- [ ] Create `deprecated/phase_handoffs/README.md`
- [ ] Update `CURRENT_STATUS_v2.1.md` with plugin architecture
- [ ] Update `README.md` if it references old paths
- [ ] Verify `docs/` contains only active documentation
- [ ] Verify root contains only essential docs

---

## 🎯 Final Structure

```
/home/yogapad/empirical-ai/empirica/
├── README.md                          # Main README
├── CURRENT_STATUS_v2.1.md             # Updated status
├── REMAINING_TASKS.md                 # Active tasks
├── docs/                              # All documentation
│   ├── HOW_TO_RESUME_SESSION.md       # Session guide
│   ├── PLUGIN_ARCHITECTURE_MIGRATION.md  # Architecture
│   ├── PLUGIN_MIGRATION_COMPLETE.md   # Migration complete
│   ├── PHASE3_TASK_HANDOFF_QWEN_ROVODEV.md  # Active handoff
│   ├── development/
│   │   └── STUB_TRACKER.md
│   └── production/                    # Production docs
│
├── deprecated/                        # Historical/deprecated
│   ├── phase_handoffs/                # Old phase docs ⭐ NEW
│   │   ├── README.md
│   │   ├── SESSION_HANDOFF_2025_11_01_PHASE2.md
│   │   ├── PHASE3_COMPLETE.md
│   │   └── ...
│   └── modality_old/                  # Old code
│       ├── empirica_core_modality/
│       └── modality_switcher_original/
│
└── empirica/
    └── plugins/
        └── modality_switcher/         # ✅ Current code
```

---

## ✅ Benefits

1. **Clean workspace** - Only active docs in root/docs
2. **Clear history** - Deprecated docs preserved with context
3. **No confusion** - Engineers see only current architecture
4. **Easy reference** - Historical docs available if needed

---

**Execute cleanup:**
```bash
bash docs/cleanup_phase_handoffs.sh
```

(Script will be created based on this guide)
