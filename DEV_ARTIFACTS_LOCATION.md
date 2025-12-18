# Development Artifacts Location

**Date:** 2025-12-18  
**Location Change:** Moved out of workspace to parent directory

## New Location

All development artifacts are now in:
```
/home/yogapad/empirical-ai/empirica-dev/
```

This directory is **outside the workspace** (../empirica-dev relative to project root).

## What Was Moved

### From `./empirica-dev/` → `../empirica-dev/from-workspace/`

**Session Notes** (17 files):
- Phase completion documents (`*COMPLETE*.md`, `*PHASE*.md`)
- Setup/configuration notes (`*SETUP*.md`, `*FIX*.md`)
- Session summaries (`*SESSION*.md`)
- Security incidents (`*INCIDENT*.md`)
- Comparison analyses (`*COMPARISON*.md`)

**Scratch Files** (21 files):
- Temporary Python scripts (`tmp_*.py`)
- Shell scripts (`tmp_*.sh`)
- Session snapshots (`session_*.json`)
- Analysis outputs (`*_categorization.json`)
- Evidence archives (`*.tar.gz`)

**Incident Evidence**:
- `atlassian_incident_evidence/` directory

**Documentation**:
- `README.md` (development artifacts guide)

### From `./docs/archive/` → `../empirica-dev/docs-archive/`

**Old Documentation** (4 items):
- Previous versions of documentation
- Archived reference materials

## Why Move Out of Workspace?

1. **Clean workspace** - Production code only
2. **Separate version control** - Dev artifacts can have own git history
3. **Easier maintenance** - Can clean up without affecting workspace
4. **Clear boundaries** - Obvious separation between prod and dev
5. **No gitignore needed** - Not in workspace tree

## Accessing Dev Artifacts

From project root:
```bash
cd ../empirica-dev/from-workspace/

# Session notes
ls session-notes/

# Scratch files
ls scratch/

# Incident evidence
ls incident-evidence/

# Old docs
cd ../docs-archive/
```

## Workspace Structure Now

```
empirica/                    (production workspace)
├── empirica/               (core package)
├── docs/                   (current documentation)
├── tests/                  (test suite)
├── slides/                 (presentation assets)
├── examples/               (usage examples)
├── scripts/                (production scripts)
└── README.md              (main docs)

../empirica-dev/            (outside workspace)
├── from-workspace/
│   ├── session-notes/     (17 files)
│   ├── scratch/           (21 files)
│   ├── incident-evidence/
│   └── README.md
└── docs-archive/           (4 items)
```

## If You Need to Reference Old Work

Development artifacts are preserved but moved outside workspace:

**Session history:** `../empirica-dev/from-workspace/session-notes/`  
**Temporary files:** `../empirica-dev/from-workspace/scratch/`  
**Old documentation:** `../empirica-dev/docs-archive/`

---

**Note:** This is informational only. No dev artifacts exist in workspace anymore.
If you need them, they're in the parent `empirica-dev` directory.
