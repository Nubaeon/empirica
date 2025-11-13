#!/bin/bash
# Empirica Cleanup Execution Script
# Date: 2025-11-11
# Note: Keeps .empirica and .empirica_reflex_logs (important data)
# Note: Keeping tests/scripts for later work

set -e

echo "================================================"
echo "Empirica v2.0 Cleanup and Organization"
echo "================================================"
echo ""

# Step 1: Create archive directories
echo "Step 1: Creating archive directories..."
mkdir -p tests/coordination/archive
mkdir -p docs/archive
mkdir -p mcp_local/archive
echo "✅ Archive directories created"
echo ""

# Step 2: Create archive README files
echo "Step 2: Creating archive README files..."

cat > tests/coordination/archive/README.md << 'ARCHIVE_README'
# Coordination Archive

**Purpose:** Historical multi-AI development session documentation

**Contents:**
- Session notes from Qwen, Gemini, Claude
- Investigation findings
- Planning documents
- Testing coordination
- Status updates

**Active Docs:** See parent directory (`tests/coordination/`)

**Note:** These docs capture the collaborative AI development process.
Archived for historical reference on 2025-11-11.
ARCHIVE_README

cat > docs/archive/README.md << 'ARCHIVE_README'
# Documentation Archive

**Purpose:** Legacy and internal documentation

**Contents:**
- Superseded guides
- Internal planning docs
- Research notes
- Implementation notes
- Session summaries

**Active Docs:** See parent directory (`docs/`)

**Note:** Archived for historical reference on 2025-11-11. 
Current documentation is in parent directories and production guides.
ARCHIVE_README

cat > mcp_local/archive/README.md << 'ARCHIVE_README'
# MCP Archive

**Purpose:** Legacy MCP implementation and testing docs

**Contents:**
- Old testing guides
- Implementation notes
- Validation docs

**Active Files:** See parent directory (`mcp_local/`)

**Note:** Archived as MCP server is now production-ready (2025-11-11).
ARCHIVE_README

echo "✅ Archive READMEs created"
echo ""

# Step 3: Move root files to coordination archive
echo "Step 3: Moving root files to coordination archive..."
mv CLEANUP_CHECKLIST.md tests/coordination/archive/
mv COMPLETE_SESSION_SUMMARY.md tests/coordination/archive/
mv RECOMMENDATIONS_IMPLEMENTED.md tests/coordination/archive/
mv SESSION_HANDOFF.md tests/coordination/archive/
mv test_suite_summary.md tests/coordination/archive/
echo "✅ Root files moved (5 files)"
echo ""

# Step 4: Delete unnecessary root files
echo "Step 4: Deleting unnecessary root files..."
rm -f __init__.py
rm -f FINAL_SESSION_SUMMARY.md  # Duplicate - newer in tests/coordination/
echo "✅ Unnecessary files deleted (2 files)"
echo ""

# Step 5: Move docs files to archive
echo "Step 5: Moving docs files to archive..."
mv docs/00_START_HERE.md docs/archive/
mv docs/AI_SECURITY_PARADIGM_SHIFT.md docs/archive/
mv docs/CLAUDE_CODE_ONBOARDING_SEQUENCE.md docs/archive/
mv docs/DOCUMENTATION_CLEANUP_ACTION_PLAN.md docs/archive/
mv docs/ESSENTIAL_VECTORS_ANALYSIS.md docs/archive/
mv docs/GENUINE_SELF_ASSESSMENT_IMPLEMENTED.md docs/archive/
mv docs/ONBOARDING_GUIDE.md docs/archive/
mv docs/POST_MEMORY_COMPRESSION_NOTES.md docs/archive/
mv docs/PRODUCTION_READINESS_ASSESSMENT.md docs/archive/
mv docs/PRODUCTION_VS_DEV_DOCS.md docs/archive/
mv docs/SESSION_COMPLETE_2025-11-08_FINAL.md docs/archive/
echo "✅ Docs files moved (11 files)"
echo ""

# Step 6: Move tests/coordination files to archive
echo "Step 6: Moving tests/coordination files to archive..."
cd tests/coordination
mv CACHE_REFRESH_GUIDE.md archive/
mv CHECK_PHASE_FINDINGS.md archive/
mv COMPREHENSIVE_TEST_ARCHITECTURE.md archive/
mv COORDINATION_SESSION.md archive/
mv DEEP_INTEGRATION_ANALYSIS.md archive/
mv FIXES_APPLIED.md archive/
mv GEMINI_BRIEFING.md archive/
mv GEMINI_PROGRESS_NOTES.md archive/
mv GEMINI_STATUS_REVIEW.md archive/
mv INVESTIGATION_EVIDENCE_UPDATE.md archive/
mv INVESTIGATION_FINDINGS.md archive/
mv INVESTIGATION_PLAN.md archive/
mv MANUAL_TMUX_TESTING_GUIDE.md archive/
mv MOCK_TEST_CHECKLIST.md archive/
mv MOCK_TEST_RESULTS.md archive/
mv POSTFLIGHT_ASSESSMENT.md archive/
mv PRE_RELEASE_ACTION_PLAN.md archive/
mv QUICK_START.md archive/
mv QWEN_BRIEFING.md archive/
mv READY_FOR_DEMO.md archive/
mv READY_FOR_RECORDING.md archive/
mv SESSION_COMPLETE.md archive/
mv STRUCTURAL_INTEGRITY_TEST_PLAN.md archive/
mv TEST_FAILURES_EXPECTED.md archive/
mv TESTS_COMPLETE.md archive/
mv WORKFLOW_EXPLANATION.md archive/
mv documentation archive/  # Move entire temp documentation directory
cd ../..
echo "✅ Coordination files moved (27 files)"
echo ""

# Step 7: Move tests root files to coordination archive
echo "Step 7: Moving tests root files to coordination archive..."
mv tests/ALL_CLEANUP_COMPLETE.md tests/coordination/archive/
mv tests/CLEANUP_COMPLETE.md tests/coordination/archive/
mv tests/CURRENT_STATUS.md tests/coordination/archive/
mv tests/EMPIRICA_VALIDATION_TEST_PLAN.md tests/coordination/archive/
mv tests/FINAL_CLEANUP_SUMMARY.md tests/coordination/archive/
mv tests/TEST_AUDIT_2025_11_10.md tests/coordination/archive/
mv tests/TESTING_STRATEGY.md tests/coordination/archive/
mv tests/TESTS_CLEANED.md tests/coordination/archive/
echo "✅ Tests root files moved (8 files)"
echo ""

# Step 8: Move mcp_local files to archive
echo "Step 8: Moving mcp_local files to archive..."
mv mcp_local/IMPLEMENTATION_COMPLETE.md mcp_local/archive/
mv mcp_local/MCP_VALIDATION_TESTING_GUIDE.md mcp_local/archive/
mv mcp_local/TESTING_GUIDE_CORRECTED.md mcp_local/archive/
echo "✅ MCP files moved (3 files)"
echo ""

# Step 9: Verification
echo "Step 9: Verifying cleanup..."
echo ""
echo "Root directory files remaining:"
ls -1 *.md 2>/dev/null | wc -l
echo ""
echo "docs/ directory files:"
ls -1 docs/*.md 2>/dev/null | wc -l
echo ""
echo "tests/coordination/ active files:"
ls -1 tests/coordination/*.md 2>/dev/null | wc -l
echo ""
echo "Archive counts:"
echo "  - tests/coordination/archive/: $(ls -1 tests/coordination/archive/*.md 2>/dev/null | wc -l) files"
echo "  - docs/archive/: $(ls -1 docs/archive/*.md 2>/dev/null | wc -l) files"
echo "  - mcp_local/archive/: $(ls -1 mcp_local/archive/*.md 2>/dev/null | wc -l) files"
echo ""

echo "================================================"
echo "✅ Cleanup Complete!"
echo "================================================"
echo ""
echo "Summary:"
echo "  - Created 3 archive directories"
echo "  - Created 3 archive READMEs"
echo "  - Moved 54 files to archives"
echo "  - Deleted 2 duplicate/unnecessary files"
echo ""
echo "Important data preserved:"
echo "  - .empirica/ (session data)"
echo "  - .empirica_reflex_logs/ (temporal logs)"
echo "  - All test files (for continued work)"
echo "  - All scripts (for continued work)"
echo ""
echo "Next: Review structure and commit changes"
