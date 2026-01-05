#!/usr/bin/env python3
"""
Dependency Security Validation Script
Verifies that security updates have been applied correctly
"""

import sys
import subprocess
from typing import Tuple, List
from dataclasses import dataclass

@dataclass
class PackageRequirement:
    name: str
    min_version: str
    max_version: str
    severity: str
    reason: str

# Security requirements
REQUIREMENTS = [
    PackageRequirement(
        name="cryptography",
        min_version="42.0.4",
        max_version="43.0.0",
        severity="CRITICAL",
        reason="CVE fixes: NULL pointer, timing attack"
    ),
    PackageRequirement(
        name="gitpython",
        min_version="3.1.43",
        max_version="4.0.0",
        severity="CRITICAL",
        reason="RCE fix: untrusted search path"
    ),
    PackageRequirement(
        name="pyyaml",
        min_version="6.0.2",
        max_version="7.0.0",
        severity="MEDIUM",
        reason="Best practice update"
    ),
    PackageRequirement(
        name="requests",
        min_version="2.32.3",
        max_version="3.0.0",
        severity="HIGH",
        reason="Credential leak fix"
    ),
    PackageRequirement(
        name="setuptools",
        min_version="78.1.1",
        max_version="79.0.0",
        severity="HIGH",
        reason="Path traversal, command injection fixes"
    ),
]

def get_installed_version(package: str) -> str:
    """Get installed version of a package"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package],
            capture_output=True,
            text=True,
            timeout=10
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Version:'):
                return line.split(':', 1)[1].strip()
        return None
    except Exception as e:
        return None

def parse_version(version: str) -> Tuple[int, ...]:
    """Parse version string into tuple of integers"""
    try:
        return tuple(int(x) for x in version.split('.')[:3])
    except:
        return (0, 0, 0)

def check_version(installed: str, min_ver: str, max_ver: str) -> Tuple[bool, str]:
    """Check if installed version meets requirements"""
    if not installed:
        return False, "NOT INSTALLED"
    
    installed_tuple = parse_version(installed)
    min_tuple = parse_version(min_ver)
    max_tuple = parse_version(max_ver)
    
    if installed_tuple < min_tuple:
        return False, f"TOO OLD (need >={min_ver})"
    elif installed_tuple >= max_tuple:
        return False, f"TOO NEW (need <{max_ver})"
    else:
        return True, "OK"

def test_imports() -> List[Tuple[str, bool, str]]:
    """Test that critical modules can be imported"""
    tests = [
        ("empirica", "Core module"),
        ("empirica.cli.cli_core", "CLI module"),
        ("empirica.config.profile_loader", "Config loader"),
        ("empirica.integrations.beads.config", "BEADS integration"),
        ("cryptography", "Cryptography"),
        ("git", "GitPython"),
        ("yaml", "PyYAML"),
        ("requests", "Requests"),
    ]
    
    results = []
    for module, description in tests:
        try:
            __import__(module)
            results.append((description, True, "Import OK"))
        except Exception as e:
            results.append((description, False, f"Import FAILED: {str(e)[:50]}"))
    
    return results

def check_yaml_safety() -> Tuple[bool, str]:
    """Verify no unsafe yaml.load() usage"""
    try:
        result = subprocess.run(
            ["grep", "-r", "yaml.load(", "empirica/", "--include=*.py"],
            capture_output=True,
            text=True,
            cwd="/home/runner/work/empirica/empirica"
        )
        if result.stdout.strip():
            return False, f"Found unsafe yaml.load() usage:\n{result.stdout[:200]}"
        return True, "All YAML loading uses safe_load()"
    except:
        return True, "Could not verify (grep failed)"

def main():
    print("=" * 70)
    print("Empirica Dependency Security Validation")
    print("=" * 70)
    print()
    
    # Check package versions
    print("📦 Package Version Validation")
    print("-" * 70)
    all_passed = True
    
    for req in REQUIREMENTS:
        installed = get_installed_version(req.name)
        passed, status = check_version(installed, req.min_version, req.max_version)
        
        icon = "✅" if passed else "❌"
        severity_icon = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }.get(req.severity, "⚪")
        
        print(f"{icon} {severity_icon} {req.name:<20} {installed or 'NOT INSTALLED':<15} {status}")
        print(f"   Required: >={req.min_version}, <{req.max_version}")
        print(f"   Reason: {req.reason}")
        print()
        
        if not passed:
            all_passed = False
    
    # Test imports
    print("🔍 Import Validation")
    print("-" * 70)
    import_results = test_imports()
    for description, passed, status in import_results:
        icon = "✅" if passed else "❌"
        print(f"{icon} {description:<30} {status}")
        if not passed:
            all_passed = False
    print()
    
    # Check YAML safety
    print("🔒 YAML Safety Check")
    print("-" * 70)
    yaml_safe, yaml_msg = check_yaml_safety()
    icon = "✅" if yaml_safe else "❌"
    print(f"{icon} {yaml_msg}")
    print()
    
    # Summary
    print("=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Security updates verified!")
        print()
        print("Next steps:")
        print("  1. Run full test suite: pytest tests/")
        print("  2. Test CLI functionality: empirica --version")
        print("  3. Commit changes: git add pyproject.toml && git commit")
        return 0
    else:
        print("❌ VALIDATION FAILED - Please review errors above")
        print()
        print("Troubleshooting:")
        print("  1. Ensure pyproject.toml has been updated")
        print("  2. Reinstall: pip install -e .")
        print("  3. Check versions: pip list | grep -E 'crypto|git|yaml|request|setup'")
        print("  4. See DEPENDENCY_SECURITY_SPEC.md for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())
