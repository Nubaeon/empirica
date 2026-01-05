# Dependency Security Documentation

This directory contains comprehensive documentation for managing Empirica's dependency security.

## 📋 Quick Start

**For Local AI Agents:** Start with `DEPENDENCY_UPDATE_QUICK_REF.md` (5-minute summary)

**For Detailed Implementation:** See `DEPENDENCY_SECURITY_SPEC.md` (complete guide)

**For Security Policy:** See `SECURITY.md` (vulnerability reporting, best practices)

## 📁 Files

### Core Documentation

- **`DEPENDENCY_SECURITY_SPEC.md`** - Complete specification with verified CVEs, implementation steps, testing procedures, and rollback plans
- **`DEPENDENCY_UPDATE_QUICK_REF.md`** - Quick reference for immediate action
- **`SECURITY.md`** - Security policy, vulnerability reporting, best practices

### Scripts & Automation

- **`scripts/update_dependencies_security.sh`** - Semi-automated update script
- **`scripts/validate_security_updates.py`** - Post-update validation tool
- **`.github/dependabot.yml`** - Automated dependency monitoring

## 🎯 Current Status (2026-01-05)

### Critical Updates Required

| Package | Current | Target | Severity | Status |
|---------|---------|--------|----------|--------|
| cryptography | 41.0.7 | ≥42.0.4,<43.0 | 🔴 CRITICAL | ⏳ Pending |
| gitpython | 3.1.0 | ≥3.1.43,<4.0 | 🔴 CRITICAL | ⏳ Pending |
| setuptools | 68.1.2 | ≥78.1.1,<79.0 | 🟠 HIGH | ⏳ Pending |
| requests | 2.31.0 | ≥2.32.3,<3.0 | 🟡 MEDIUM | ⏳ Pending |
| pyyaml | 6.0.1 | ≥6.0.2,<7.0 | 🟢 LOW | ⏳ Pending |

### Verified CVEs

- **cryptography:** NULL pointer dereference, timing oracle attack
- **gitpython:** RCE via untrusted search path (Windows)
- **setuptools:** Path traversal, command injection
- **requests:** Credential leak in older versions

All CVEs verified against GitHub Advisory Database.

## 🚀 Implementation Steps

### Option 1: Quick Update (Recommended for AI Agents)

```bash
# 1. Read the quick reference
cat DEPENDENCY_UPDATE_QUICK_REF.md

# 2. Follow the 5-step process:
#    - Backup pyproject.toml
#    - Edit with changes from spec
#    - Reinstall dependencies
#    - Verify versions
#    - Run tests

# 3. Validate
python3 scripts/validate_security_updates.py
```

### Option 2: Semi-Automated

```bash
# Run the update script (requires manual pyproject.toml editing)
bash scripts/update_dependencies_security.sh
```

### Option 3: Manual Update

1. Read `DEPENDENCY_SECURITY_SPEC.md`
2. Apply changes to `pyproject.toml`
3. Test with existing test suite
4. Validate with validation script

## 🧪 Validation

After applying updates:

```bash
# Automated validation
python3 scripts/validate_security_updates.py

# Manual checks
pip list | grep -E "(cryptography|gitpython|pyyaml|requests|setuptools)"
pytest tests/
empirica --version
```

## 📚 Additional Resources

### For Implementation Teams

- **Specification:** `DEPENDENCY_SECURITY_SPEC.md`
  - Complete CVE details
  - Step-by-step instructions
  - Testing requirements
  - Rollback procedures

### For DevOps/CI

- **Automation:** `.github/dependabot.yml`
  - Automatic vulnerability scanning
  - Automated PR creation
  - Version constraint management

### For Security Teams

- **Policy:** `SECURITY.md`
  - Vulnerability reporting process
  - Security best practices
  - Compliance status
  - Update policy

## ⚠️ Important Notes

### YAML Safety

✅ **All YAML loading uses `yaml.safe_load()`** - No unsafe `yaml.load()` found
- Config files are for internal/developer use
- Not exposed to untrusted input
- Secure by design

### Git Notes

⚠️ **Git notes can be pushed to remote repositories**
- Review repository access controls
- Don't store secrets in git notes
- See `SECURITY.md` for details

### Lock Files

🔒 **No lock file currently exists**
- Builds are not reproducible
- Recommended: Generate `requirements-lock.txt`
- See spec for instructions

## 🔄 Ongoing Maintenance

### Automated (via Dependabot)

- Weekly dependency checks
- Automatic security PR creation
- Grouped updates by category

### Manual (Recommended)

- Monthly security review
- Quarterly dependency audit
- Annual policy review

## 📞 Support

- **Security Issues:** Report privately per `SECURITY.md`
- **Implementation Questions:** Open GitHub Discussion
- **Bugs:** Open GitHub Issue

## 📝 Version History

- **2026-01-05:** Initial security audit and specification
  - Identified 5 packages with security issues
  - Created comprehensive update documentation
  - Verified all CVEs against GitHub Advisory Database

---

**Last Updated:** 2026-01-05  
**Status:** Specifications Ready for Implementation  
**Verified By:** GitHub Advisory Database + Manual Code Review
