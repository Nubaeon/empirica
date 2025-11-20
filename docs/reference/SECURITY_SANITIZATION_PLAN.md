# Security & Distribution Sanitization Plan

**Date:** 2025-11-17
**Purpose:** Sanitize Empirica for public/production distribution
**Risk Level:** MEDIUM - No exposed credentials, but extensive personal artifacts
**Estimated Effort:** 4-6 hours

---

## Critical Issues Summary

| Issue | Severity | Files Affected | Status |
|-------|----------|----------------|--------|
| Personal filesystem paths | HIGH | 100+ | Ready to fix |
| API key file references | HIGH | 10+ | Ready to fix |
| Development artifacts in root | MEDIUM | 3 | Ready to archive |
| Session coordination docs | MEDIUM | 15+ | Decision needed |
| Placeholder URLs/emails | MEDIUM | 20+ | Ready to update |
| .agent_memory.json | LOW | 1 | Ready to remove |

---

## Phase 1: Automated Path Sanitization (HIGH PRIORITY)

### 1.1 Find All Files with Personal Paths

```bash
# Create list of files to sanitize
grep -r "/path/to/empirica" . \
  --exclude-dir=.git \
  --exclude-dir=.venv* \
  --exclude-dir=__pycache__ \
  --exclude-dir=.pytest_cache \
  --exclude-dir=node_modules \
  --include="*.md" \
  --include="*.py" \
  --include="*.sh" \
  --include="*.json" \
  --include="*.yaml" \
  --include="*.yml" | \
  cut -d: -f1 | sort -u > /tmp/files_with_paths.txt

# Review the list
cat /tmp/files_with_paths.txt
```

### 1.2 Automated Sanitization Script

Create `scripts/sanitize_paths.sh`:

```bash
#!/bin/bash
# Sanitize personal paths from Empirica codebase
# Run from repository root

set -e

echo "🔒 Empirica Path Sanitization Script"
echo "===================================="
echo ""

# Backup first
echo "📦 Creating backup..."
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p .backups
tar -czf .backups/pre_sanitization_${timestamp}.tar.gz \
  --exclude=.git \
  --exclude=.venv* \
  --exclude=__pycache__ \
  .

echo "✅ Backup created: .backups/pre_sanitization_${timestamp}.tar.gz"
echo ""

# Sanitization patterns
echo "🔧 Applying sanitization patterns..."

# Pattern 1: Full path to generic
find . -type f \( -name "*.md" -o -name "*.sh" -o -name "*.py" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) \
  ! -path "./.git/*" \
  ! -path "./.venv*/*" \
  ! -path "./__pycache__/*" \
  ! -path "./.backups/*" \
  -exec sed -i 's|/path/to/empirica|/path/to/empirica|g' {} \;

# Pattern 2: Home directory references
find . -type f \( -name "*.md" -o -name "*.sh" -o -name "*.py" \) \
  ! -path "./.git/*" \
  ! -path "./.venv*/*" \
  ! -path "./.backups/*" \
  -exec sed -i 's|~/empirica-parent|~/empirica-parent|g' {} \;

# Pattern 3: Specific .venv references in shell scripts
find . -type f -name "*.sh" \
  ! -path "./.git/*" \
  ! -path "./.backups/*" \
  -exec sed -i 's|/path/to/empirica/.venv-mcp/bin/python3|python3|g' {} \;

echo "✅ Path sanitization complete"
echo ""

# Verify
echo "🔍 Verifying sanitization..."
remaining=$(grep -r "/home/yogapad" . \
  --exclude-dir=.git \
  --exclude-dir=.venv* \
  --exclude-dir=.backups \
  --exclude-dir=__pycache__ \
  --include="*.md" \
  --include="*.py" \
  --include="*.sh" \
  --include="*.json" \
  --include="*.yaml" \
  --include="*.yml" | wc -l)

if [ "$remaining" -eq 0 ]; then
  echo "✅ No personal paths remaining"
else
  echo "⚠️  $remaining references still found:"
  grep -r "/home/yogapad" . \
    --exclude-dir=.git \
    --exclude-dir=.venv* \
    --exclude-dir=.backups \
    --exclude-dir=__pycache__ \
    --include="*.md" \
    --include="*.py" \
    --include="*.sh" \
    --include="*.json" \
    --include="*.yaml" \
    --include="*.yml" | head -20
  echo ""
  echo "   Review these manually and re-run if needed"
fi

echo ""
echo "✅ Sanitization complete!"
echo "   Backup: .backups/pre_sanitization_${timestamp}.tar.gz"
echo "   To rollback: tar -xzf .backups/pre_sanitization_${timestamp}.tar.gz"
```

**Execution:**
```bash
chmod +x scripts/sanitize_paths.sh
./scripts/sanitize_paths.sh
```

---

## Phase 2: API Key Reference Cleanup

### 2.1 Find Specific API Key File References

```bash
# Find .minimax_api references
grep -r "\.minimax_api" . \
  --exclude-dir=.git \
  --exclude-dir=.venv* \
  --include="*.md" \
  --include="*.py"
```

### 2.2 Sanitize API Key References

```bash
# Replace specific filenames with generic examples
find . -type f \( -name "*.md" -o -name "*.py" \) \
  ! -path "./.git/*" \
  ! -path "./.venv*/*" \
  -exec sed -i 's|\.minimax_key|.minimax_key|g' {} \;

find . -type f \( -name "*.md" -o -name "*.py" \) \
  ! -path "./.git/*" \
  ! -path "./.venv*/*" \
  -exec sed -i 's|\.minimax_api|.minimax_key|g' {} \;

# Update credentials_loader.py to use standard naming
sed -i "s|'minimax': '\.minimax_key'|'minimax': '.minimax_key'|g" \
  empirica/config/credentials_loader.py
```

### 2.3 Verify No Actual Keys

```bash
# Check for potential API key patterns (should find none in code)
grep -r "sk-[a-zA-Z0-9]" . --exclude-dir=.git --exclude-dir=.venv* || echo "✅ No OpenAI keys found"
grep -r "AIza[a-zA-Z0-9]" . --exclude-dir=.git --exclude-dir=.venv* || echo "✅ No Google API keys found"
grep -r "Bearer [a-zA-Z0-9]" . --exclude-dir=.git --exclude-dir=.venv* || echo "✅ No Bearer tokens found"
```

---

## Phase 3: Remove Development Artifacts

### 3.1 Remove .agent_memory.json

```bash
# Verify it's not important
cat .agent_memory.json

# Add to .gitignore if not present
echo ".agent_memory.json" >> .gitignore

# Remove from repository
git rm --cached .agent_memory.json 2>/dev/null || rm .agent_memory.json
```

### 3.2 Archive Root Development Docs

```bash
# Create internal planning directory
mkdir -p docs/_internal/planning

# Move planning documents
mv DOCUMENTATION_CLEANUP_PLAN.md docs/_internal/planning/
mv FOLDER_REORGANIZATION_PLAN.md docs/_internal/planning/
mv MULTI_AGENT_CHECKPOINT_STRATEGY.md docs/_internal/coordination/

# Or if already documented elsewhere, just delete them
# rm DOCUMENTATION_CLEANUP_PLAN.md FOLDER_REORGANIZATION_PLAN.md
```

### 3.3 Review Root Directory

```bash
# Check what's left in root
ls -1 *.md

# Should only have:
# - README.md
# - CONTRIBUTING.md
# - LICENSE (if present)
# - Platform-specific guides (CLAUDE.md, QWEN.md, etc.)
```

---

## Phase 4: Update Placeholder Information

### 4.1 GitHub Repository URLs

**Decision needed:** What is the actual repository URL?

```bash
# Find all placeholder GitHub URLs
grep -r "github.com/Nubaeon/empirica" . --exclude-dir=.git
grep -r "github.com/\[org\]/empirica" . --exclude-dir=.git

# Replace with actual URL (once decided)
ACTUAL_REPO="github.com/empirica-ai/empirica"  # Example

find . -type f -name "*.md" \
  ! -path "./.git/*" \
  -exec sed -i "s|github.com/Nubaeon/empirica|$ACTUAL_REPO|g" {} \;

find . -type f -name "*.md" \
  ! -path "./.git/*" \
  -exec sed -i "s|github.com/\[org\]/empirica|$ACTUAL_REPO|g" {} \;
```

### 4.2 Old Repository References

```bash
# Update old Nubaeon references
find . -type f -name "*.md" \
  ! -path "./.git/*" \
  -exec sed -i "s|github.com/Nubaeon/empirica|$ACTUAL_REPO|g" {} \;
```

### 4.3 License Contact Information

**Edit LICENSE file manually:**

```bash
# Current (lines 78, 211):
# Email: licensing@empirica.dev (placeholder)
# Website: https://empirica.dev (placeholder)

# Options:
# 1. Set up real infrastructure:
#    Email: opensource@empirica.ai
#    Website: https://empirica.ai

# 2. Use GitHub for contact:
#    Email: See GitHub issues
#    Website: https://github.com/empirica-ai/empirica

# 3. Simplify license (remove commercial option):
#    Just use AGPL-3.0 or MIT
```

**Manual edit required:** Update LICENSE file with decision

---

## Phase 5: Session Documentation Decision

### 5.1 Identify Session Coordination Docs

```bash
# List all handoff files
ls -lh docs/handoffs/
ls -lh docs/archive/2025-11/session_notes/

# Total: ~15-20 files with internal coordination
```

### 5.2 Decision Matrix

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Keep All** | Educational value, shows real workflow | Internal references, agent names | ❌ Not recommended |
| **Archive All** | Clean distribution | Lose development history visibility | ✅ Safest |
| **Sanitize** | Keep technical content, remove internal refs | Time-consuming | ⚠️ If resources allow |
| **Move to _internal/** | Available but not distributed | Still in repository | ✅ Good middle ground |

### 5.3 Recommended Action: Move to _internal/

```bash
# Create internal coordination directory
mkdir -p docs/_internal/coordination

# Move handoffs
mv docs/handoffs/ docs/_internal/coordination/handoffs/

# Move session notes
mv docs/archive/2025-11/session_notes/ docs/_internal/coordination/session_notes/

# Add to .gitignore or keep in repo for internal reference (decision needed)
# echo "docs/_internal/" >> .gitignore  # If want to exclude from distribution
```

---

## Phase 6: Verification & Testing

### 6.1 Security Scan

```bash
# Run comprehensive security check
./scripts/sanitize_paths.sh  # Should report 0 remaining

# Check for common security issues
grep -r "password\s*=" . --include="*.py" --exclude-dir=.git --exclude-dir=.venv* || echo "✅ No hardcoded passwords"
grep -r "api_key\s*=" . --include="*.py" --exclude-dir=.git --exclude-dir=.venv* || echo "✅ No hardcoded API keys"
grep -r "secret\s*=" . --include="*.py" --exclude-dir=.git --exclude-dir=.venv* || echo "✅ No hardcoded secrets"
```

### 6.2 Link Checker

```bash
# Check for broken internal links (requires markdown-link-check)
# npm install -g markdown-link-check

find docs -name "*.md" -exec markdown-link-check {} \; | grep "✖" || echo "✅ All links valid"

# Or manual check of common references
grep -r "\[.*\](docs/" . --include="*.md" | head -20
```

### 6.3 Test Installation

```bash
# Fresh clone simulation
cd /tmp
git clone /path/to/empirica empirica-test
cd empirica-test

# Verify no personal paths
grep -r "/home/yogapad" . || echo "✅ No personal paths"

# Verify installation works
pip install -e .
empirica --help

# Clean up
cd ..
rm -rf empirica-test
```

---

## Phase 7: Final Cleanup Checklist

### Pre-Release Verification

- [ ] **Path Sanitization**
  - [ ] No `/home/yogapad/` references in code/docs
  - [ ] Shell scripts use generic paths or env vars
  - [ ] MCP config uses relative paths

- [ ] **Credentials & Keys**
  - [ ] No hardcoded API keys
  - [ ] No hardcoded passwords
  - [ ] .gitignore covers all sensitive files
  - [ ] credentials_loader.py uses standard filenames

- [ ] **Development Artifacts**
  - [ ] `.agent_memory.json` removed/gitignored
  - [ ] Planning docs archived or removed from root
  - [ ] Session handoffs moved to _internal/ or sanitized
  - [ ] Checkpoint files archived

- [ ] **Placeholder Updates**
  - [ ] GitHub repository URLs updated
  - [ ] LICENSE contact information finalized
  - [ ] Email addresses updated (if needed)
  - [ ] Website URLs updated (if applicable)

- [ ] **Root Directory Clean**
  - [ ] Only production files in root
  - [ ] README.md updated and accurate
  - [ ] CONTRIBUTING.md complete
  - [ ] LICENSE finalized

- [ ] **Documentation**
  - [ ] No broken internal links
  - [ ] Installation instructions tested
  - [ ] API documentation complete
  - [ ] Examples work without modification

- [ ] **Testing**
  - [ ] Fresh install test passes
  - [ ] Example code runs successfully
  - [ ] No errors referencing personal paths
  - [ ] MCP server starts without errors

---

## Phase 8: Distribution Strategy

### Option A: Clean Repository (Recommended for Public Release)

```bash
# Create clean distribution branch
git checkout -b distribution-clean

# Apply all sanitization
./scripts/sanitize_paths.sh

# Commit changes
git add -A
git commit -m "Sanitize for public distribution

- Remove personal filesystem paths
- Update API key references to generic examples
- Archive internal development artifacts
- Update placeholder URLs and contact info
- Clean root directory structure"

# Create distribution repository
# (Fresh repository with clean history)
```

### Option B: Filter History (Advanced)

```bash
# Use git-filter-repo to remove sensitive data from history
# (Requires git-filter-repo tool)

# Only if accidentally committed sensitive data
git filter-repo --path-rename "/path/to/empirica:/path/to/empirica"
```

### Option C: Archive Distribution (Simplest)

```bash
# Create clean archive for distribution
tar -czf empirica-release-v1.0.tar.gz \
  --exclude=.git \
  --exclude=.venv* \
  --exclude=__pycache__ \
  --exclude=.pytest_cache \
  --exclude=*.pyc \
  --exclude=.agent_memory.json \
  --exclude=docs/_internal \
  --exclude=.backups \
  .

# Verify archive
mkdir /tmp/empirica-test
tar -xzf empirica-release-v1.0.tar.gz -C /tmp/empirica-test
grep -r "/home/yogapad" /tmp/empirica-test || echo "✅ Clean archive"
rm -rf /tmp/empirica-test
```

---

## Automated Sanitization Script (Complete)

Save as `scripts/complete_sanitization.sh`:

```bash
#!/bin/bash
# Complete Empirica Sanitization for Distribution
# Run from repository root

set -e

echo "🔒 Empirica Complete Sanitization Script"
echo "========================================"
echo ""
echo "This script will:"
echo "  1. Create backup"
echo "  2. Sanitize paths"
echo "  3. Clean API key references"
echo "  4. Remove development artifacts"
echo "  5. Verify security"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi

# 1. Backup
echo "📦 Creating backup..."
timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p .backups
tar -czf .backups/pre_sanitization_${timestamp}.tar.gz \
  --exclude=.git \
  --exclude=.venv* \
  --exclude=__pycache__ \
  --exclude=.backups \
  .
echo "✅ Backup: .backups/pre_sanitization_${timestamp}.tar.gz"
echo ""

# 2. Path sanitization
echo "🔧 Sanitizing paths..."
find . -type f \( -name "*.md" -o -name "*.sh" -o -name "*.py" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) \
  ! -path "./.git/*" \
  ! -path "./.venv*/*" \
  ! -path "./__pycache__/*" \
  ! -path "./.backups/*" \
  ! -path "./docs/_internal/*" \
  -exec sed -i 's|/path/to/empirica|/path/to/empirica|g' {} \;

echo "✅ Path sanitization complete"
echo ""

# 3. API key references
echo "🔧 Cleaning API key references..."
find . -type f \( -name "*.md" -o -name "*.py" \) \
  ! -path "./.git/*" \
  ! -path "./.venv*/*" \
  ! -path "./.backups/*" \
  -exec sed -i 's|\.minimax_key|.minimax_key|g' {} \;

find . -type f \( -name "*.md" -o -name "*.py" \) \
  ! -path "./.git/*" \
  ! -path "./.venv*/*" \
  ! -path "./.backups/*" \
  -exec sed -i 's|\.minimax_api|.minimax_key|g' {} \;

echo "✅ API key reference cleanup complete"
echo ""

# 4. Remove development artifacts
echo "🗑️  Removing development artifacts..."

# Remove .agent_memory.json
if [ -f ".agent_memory.json" ]; then
  rm .agent_memory.json
  echo "   Removed .agent_memory.json"
fi

# Add to .gitignore if not present
if ! grep -q "^.agent_memory.json" .gitignore 2>/dev/null; then
  echo ".agent_memory.json" >> .gitignore
  echo "   Added .agent_memory.json to .gitignore"
fi

echo "✅ Artifacts cleaned"
echo ""

# 5. Security verification
echo "🔍 Running security verification..."

# Check for remaining personal paths
remaining=$(grep -r "/home/yogapad" . \
  --exclude-dir=.git \
  --exclude-dir=.venv* \
  --exclude-dir=.backups \
  --exclude-dir=__pycache__ \
  --exclude-dir=docs/_internal \
  --include="*.md" \
  --include="*.py" \
  --include="*.sh" \
  --include="*.json" \
  --include="*.yaml" \
  --include="*.yml" 2>/dev/null | wc -l)

if [ "$remaining" -eq 0 ]; then
  echo "✅ No personal paths remaining"
else
  echo "⚠️  $remaining personal path references still found"
  echo "   (May be in _internal/ docs, which is okay)"
fi

# Check for potential secrets (should be none)
secrets=0
if grep -r "sk-[a-zA-Z0-9]\{20,\}" . --exclude-dir=.git --exclude-dir=.venv* --exclude-dir=.backups 2>/dev/null | grep -v ".md:"; then
  ((secrets++))
fi

if [ $secrets -eq 0 ]; then
  echo "✅ No exposed secrets found"
else
  echo "❌ Potential secrets found! Review manually."
fi

echo ""
echo "🎉 Sanitization complete!"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Update LICENSE contact information manually"
echo "  3. Update GitHub repository URLs (if known)"
echo "  4. Test installation: pip install -e ."
echo "  5. Commit changes: git add -A && git commit -m 'Sanitize for distribution'"
echo ""
echo "Rollback if needed:"
echo "  tar -xzf .backups/pre_sanitization_${timestamp}.tar.gz"
```

**Make executable and run:**
```bash
chmod +x scripts/complete_sanitization.sh
./scripts/complete_sanitization.sh
```

---

## Summary

**Estimated Timeline:**
- Phase 1 (Path sanitization): 30 minutes (mostly automated)
- Phase 2 (API references): 15 minutes
- Phase 3 (Artifacts): 30 minutes
- Phase 4 (Placeholders): 1 hour (requires decisions)
- Phase 5 (Session docs): 1 hour (decision + execution)
- Phase 6 (Verification): 30 minutes
- Phase 7 (Checklist): 30 minutes
- Phase 8 (Distribution): 30 minutes

**Total: 4-6 hours**

**Critical Path:**
1. Run `complete_sanitization.sh` (30 min)
2. Make licensing decision (30 min)
3. Decide on session documentation (30 min)
4. Update placeholders (1 hour)
5. Final verification (30 min)

**After completion:** Repository will be ready for public distribution with no security concerns and professional presentation.
