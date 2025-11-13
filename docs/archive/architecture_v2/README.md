# Architecture Documentation v2.0 - ARCHIVED

**Date Archived:** 2024  
**Reason:** Replaced by v3.0 unified documentation

---

## What Was Archived

This folder contains the previous architecture documentation structure (v2.0) which has been replaced by a cleaner, more unified approach in v3.0.

### Files Archived:

1. **ARCHITECTURE_MAP.md** (679 lines)
   - Previous system architecture document
   - Mixed architecture concepts with directory structure
   - Contained some outdated information

2. **DIRECTORY_STRUCTURE.md** (351 lines)
   - Previous directory structure reference
   - Overlapped with ARCHITECTURE_MAP.md
   - Less comprehensive than v3.0

3. **ARCHITECTURE_ORGANIZATION.md** (608 lines)
   - Previous organization guide
   - Overlapped with both above documents
   - Caused confusion about which doc to reference

---

## What Replaced This

### New v3.0 Documentation:

**1. `docs/reference/CANONICAL_DIRECTORY_STRUCTURE.md`**
- **Purpose:** Single source of truth for directory structure
- **Content:** 
  - Complete folder structure
  - File purposes and descriptions
  - Import path reference
  - Integration points
  - Where to add new functionality
- **Length:** ~600 lines (comprehensive)

**2. `docs/reference/ARCHITECTURE_OVERVIEW.md`**
- **Purpose:** System architecture and design principles
- **Content:**
  - Three-layer architecture
  - Component interactions
  - Data flow diagrams
  - Design principles
  - NO directory structure details (references CANONICAL_DIRECTORY_STRUCTURE.md instead)
- **Length:** ~650 lines (focused)

---

## Why the Change?

### Problems with v2.0:
1. **Overlap:** Three docs describing similar things
2. **Confusion:** Unclear which doc to reference for what
3. **Outdated:** Missing profile system, investigation refactoring
4. **Mixed Concerns:** Architecture mixed with directory structure

### Benefits of v3.0:
1. **Clear Separation:** Architecture vs directory structure (separate docs)
2. **Single Source of Truth:** CANONICAL_DIRECTORY_STRUCTURE.md is definitive
3. **Up to Date:** Includes profile system, investigation plugins, etc.
4. **Better for AIs:** Clear which doc to use for what purpose

---

## Migration Guide

### If You Were Using ARCHITECTURE_MAP.md:
→ Use `ARCHITECTURE_OVERVIEW.md` for system architecture  
→ Use `CANONICAL_DIRECTORY_STRUCTURE.md` for file locations

### If You Were Using DIRECTORY_STRUCTURE.md:
→ Use `CANONICAL_DIRECTORY_STRUCTURE.md` (more comprehensive)

### If You Were Using ARCHITECTURE_ORGANIZATION.md:
→ Content merged into both new documents

---

## Can I Delete This Folder?

**Yes, once you've confirmed:**
1. All references updated to new docs
2. No critical information lost
3. Team aware of new structure

**Keep if:**
- You need to reference old architecture decisions
- Historical documentation is valuable
- Transition period (keep for 1-2 months then delete)

---

## New Documentation Structure

```
docs/
├── reference/
│   ├── CANONICAL_DIRECTORY_STRUCTURE.md   ⭐ USE THIS for file locations
│   ├── ARCHITECTURE_OVERVIEW.md           ⭐ USE THIS for system architecture
│   ├── BOOTSTRAP_QUICK_REFERENCE.md
│   ├── CHANGELOG.md
│   └── ...
│
└── archive/
    └── architecture_v2/                   📦 ARCHIVED (this folder)
        ├── ARCHITECTURE_MAP.md
        ├── DIRECTORY_STRUCTURE.md
        ├── ARCHITECTURE_ORGANIZATION.md
        └── README.md (this file)
```

---

## Questions?

See the new documentation:
- `docs/reference/CANONICAL_DIRECTORY_STRUCTURE.md`
- `docs/reference/ARCHITECTURE_OVERVIEW.md`

For historical context, the archived files remain in this folder.
