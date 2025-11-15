# Launch Checklist - November 20, 2025

**Status:** 5 days to launch  
**Critical items before going public**

---

## 🚨 CRITICAL: Repository Rename

### Current State
- **Current name:** `semantic_self_aware_kit`
- **Target name:** `empirica`
- **Status:** ❌ NOT DONE YET

### Action Required
```bash
# On GitHub (before launch):
1. Go to repository Settings
2. Repository name: semantic_self_aware_kit → empirica
3. Update description
4. Update topics/tags
5. Verify redirect works (GitHub auto-redirects old URLs)

# Update local remotes:
git remote set-url origin https://github.com/[username]/empirica.git

# Update all documentation references:
grep -r "semantic_self_aware_kit" . --exclude-dir=.git
# Replace with "empirica"
```

### Files That May Reference Old Name
- README.md
- docs/ (various)
- setup.py
- pyproject.toml
- Any install instructions
- Any git clone examples

**Priority:** HIGH - Must do before public launch  
**Owner:** Human lead  
**Deadline:** November 19, 2025 (day before launch)

---

## 📋 Pre-Launch Checklist

### Repository Setup
- [ ] Rename repo: semantic_self_aware_kit → empirica
- [ ] Update all documentation references
- [ ] Verify GitHub Pages URL (if using)
- [ ] Set repository to PUBLIC (currently private)
- [ ] Add repository description
- [ ] Add topics/tags
- [ ] Set license visibility

### Code Quality
- [ ] All E2E tests passing (Claude Code)
- [ ] Code hardening complete (Minimax)
- [ ] Security audit complete (Qwen)
- [ ] Zero critical vulnerabilities
- [ ] Zero duplicate code
- [ ] All dates corrected (2025)

### Documentation
- [ ] README.md updated and accurate
- [ ] CHANGELOG.md created
- [ ] All production docs updated
- [ ] Website deployed (if ready)
- [ ] Installation instructions tested
- [ ] Examples work when copy-pasted

### Testing
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] E2E test complete
- [ ] Performance validated
- [ ] Multi-agent coordination tested

### Legal/Licensing
- [ ] LICENSE file present (AGPL-3.0 dual)
- [ ] CONTRIBUTING.md present
- [ ] Third-party attributions checked
- [ ] No sensitive data in repo

### Communication
- [ ] Announcement draft ready
- [ ] Social media posts prepared
- [ ] Community channels ready
- [ ] Support process defined

---

## 🗓️ Timeline

**November 15 (Today):**
- ✅ Repository made private
- 🔄 E2E tests running
- 🔄 Code hardening in progress
- 🔄 Security audit in progress

**November 16-17:**
- Complete all testing
- Fix all critical issues
- Update all documentation
- Prepare repo rename

**November 18-19:**
- Final QA pass
- **Rename repository**
- Update all references
- Test public access
- Final documentation review

**November 20:**
- Set repository to PUBLIC
- **LAUNCH!** 🚀

---

**Note this down:** Repository rename MUST happen before public launch!
