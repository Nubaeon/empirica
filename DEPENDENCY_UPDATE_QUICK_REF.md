# Dependency Security Update - Quick Reference

**⏱️ 5-Minute Summary for Local AI Agents**

---

## TL;DR

Update 5 packages in `pyproject.toml` to fix CRITICAL security vulnerabilities:

```diff
[build-system]
-requires = ["setuptools>=45", "wheel"]
+requires = ["setuptools>=78.1.1,<79.0", "wheel"]

[project]
dependencies = [
-    "cryptography>=41.0",
+    "cryptography>=42.0.4,<43.0",      # CRITICAL: RCE + NULL pointer
    
-    "gitpython>=3.1.0",
+    "gitpython>=3.1.43,<4.0",          # CRITICAL: RCE on Windows
    
-    "requests>=2.31.0",
+    "requests>=2.32.3,<3.0",           # HIGH: Credential leak
    
-    "pyyaml>=6.0",
+    "pyyaml>=6.0.2,<7.0",              # Best practice
    
    # Also add upper bounds to ALL other deps:
    # Pattern: >=X.Y,<(X+1).0
]
```

---

## Verified CVEs

| Package | Current | CVE | Severity | Fix |
|---------|---------|-----|----------|-----|
| cryptography | 41.0.7 | NULL pointer, timing attack | CRITICAL | ≥42.0.4 |
| gitpython | 3.1.0 | RCE via untrusted path | CRITICAL | ≥3.1.43 |
| setuptools | 68.1.2 | Path traversal, command injection | HIGH | ≥78.1.1 |
| requests | 2.31.0 | Credential leak | MEDIUM | ≥2.32.3 |
| pyyaml | 6.0.1 | None (safe_load used) | LOW | ≥6.0.2 |

---

## Implementation (Copy-Paste)

```bash
# 1. Backup
cd /home/runner/work/empirica/empirica
cp pyproject.toml pyproject.toml.backup

# 2. Edit pyproject.toml
#    Apply changes from DEPENDENCY_SECURITY_SPEC.md

# 3. Reinstall
pip uninstall -y cryptography gitpython setuptools requests pyyaml
pip install -e "."

# 4. Verify
pip list | grep -E "(cryptography|gitpython|pyyaml|requests|setuptools)"

# 5. Test
pytest tests/
empirica --version
```

---

## Expected Versions After Update

```
cryptography    ≥42.0.4 (installed: 42.0.4+)
gitpython       ≥3.1.43 (installed: 3.1.43+)
pyyaml          ≥6.0.2  (installed: 6.0.2+)
requests        ≥2.32.3 (installed: 2.32.3+)
setuptools      ≥78.1.1 (installed: 78.1.1+)
```

---

## Test Commands

```bash
# Core imports
python -c "import empirica; print('✅ OK')"

# CLI works
empirica --version

# Config loading (yaml)
python -c "from empirica.config.profile_loader import ProfileLoader; print('✅ OK')"

# Git notes (gitpython)
python -c "from empirica.integrations.beads.config import BeadsConfig; print('✅ OK')"

# Full test suite
pytest tests/
```

---

## Rollback If Needed

```bash
# Quick restore
cp pyproject.toml.backup pyproject.toml
pip install -e "."
```

---

## Full Details

See `DEPENDENCY_SECURITY_SPEC.md` for:
- Complete CVE descriptions
- All version constraints (upper bounds)
- Detailed testing procedures
- Future recommendations (lock files, CI/CD)
- Rollback procedures

---

## Priority

🔴 **DO IMMEDIATELY** - cryptography, gitpython, setuptools  
🟡 **DO SOON** - requests  
🟢 **DO EVENTUALLY** - Add upper bounds, create lock file

---

**Time Required:** 30-60 minutes  
**Risk:** LOW (patch updates only)  
**Impact:** HIGH (fixes critical RCE vulnerabilities)
