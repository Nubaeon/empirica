#!/usr/bin/env python3
"""
Epistemic Release Agent - release-ready command

A thorough pre-release verification that applies epistemic principles:
1. Version Sync - Ensures versions match across pyproject.toml, __init__.py, CLAUDE.md
2. Architecture Assessment - Turtle assess on key directories
3. PyPI Package Check - Verifies empirica and empirica-mcp packages
4. Privacy/Security Scan - Checks for sensitive/private/dev content
5. Documentation Assessment - Verifies docs are current

Usage:
    empirica release-ready                    # Full epistemic release check
    empirica release-ready --quick            # Quick check (skip architecture assess)
    empirica release-ready --output json      # JSON output for automation
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from ..cli_utils import handle_cli_error


class AssessmentStatus(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class CheckResult:
    name: str
    status: AssessmentStatus
    message: str
    details: List[str] = field(default_factory=list)
    moon: str = ""  # Moon phase indicator

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "moon": self.moon
        }


class EpistemicReleaseAgent:
    """
    Epistemic Release Agent - Applies epistemic principles to release readiness.

    Philosophy:
    - "Know what you know" - Version consistency proves understanding
    - "Know what you don't know" - Architecture assess reveals gaps
    - "Protect what shouldn't be known" - Privacy scan guards secrets
    """

    def __init__(self, project_root: Optional[Path] = None, quick: bool = False):
        self.root = project_root or Path.cwd()
        self.quick = quick
        self.results: List[CheckResult] = []
        self.version: Optional[str] = None

    def _score_to_moon(self, score: float) -> str:
        """Convert 0-1 score to moon phase."""
        if score >= 0.85:
            return "🌕"  # Full moon - crystalline
        elif score >= 0.70:
            return "🌔"  # Waxing gibbous - solid
        elif score >= 0.50:
            return "🌓"  # First quarter - emergent
        elif score >= 0.30:
            return "🌒"  # Waxing crescent - forming
        else:
            return "🌑"  # New moon - dark

    def _status_to_moon(self, status: AssessmentStatus) -> str:
        """Convert status to moon phase."""
        return {
            AssessmentStatus.PASS: "🌕",
            AssessmentStatus.WARN: "🌓",
            AssessmentStatus.FAIL: "🌑",
            AssessmentStatus.SKIP: "🌒"
        }.get(status, "🌒")

    # =========================================================================
    # CHECK 1: Version Sync
    # =========================================================================
    def check_version_sync(self) -> CheckResult:
        """Verify version consistency across all files."""
        versions = {}
        details = []

        # pyproject.toml (primary source of truth)
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
            if match:
                versions['pyproject.toml'] = match.group(1)
                self.version = match.group(1)
                details.append(f"pyproject.toml: {match.group(1)}")

        # empirica/__init__.py
        init_file = self.root / "empirica" / "__init__.py"
        if init_file.exists():
            content = init_file.read_text()
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                versions['empirica/__init__.py'] = match.group(1)
                details.append(f"empirica/__init__.py: {match.group(1)}")

        # CLAUDE.md system prompt version (look for "Lean v" pattern)
        claude_md_paths = [
            Path.home() / ".claude" / "CLAUDE.md",
            self.root / "CLAUDE.md",
            self.root / "docs" / "CLAUDE.md"
        ]
        for claude_md in claude_md_paths:
            if claude_md.exists():
                content = claude_md.read_text()
                match = re.search(r'Lean v(\d+\.\d+)', content)
                if match:
                    versions[f'CLAUDE.md ({claude_md})'] = f"prompt-v{match.group(1)}"
                    details.append(f"CLAUDE.md prompt: v{match.group(1)}")
                break

        # Copilot instructions
        copilot_md = self.root / ".github" / "copilot-instructions.md"
        if copilot_md.exists():
            content = copilot_md.read_text()
            match = re.search(r'Lean v(\d+\.\d+)', content)
            if match:
                versions['copilot-instructions.md'] = f"prompt-v{match.group(1)}"
                details.append(f"Copilot prompt: v{match.group(1)}")

        # Check package versions match
        pkg_versions = {k: v for k, v in versions.items()
                       if not k.startswith('CLAUDE') and 'copilot' not in k.lower()}
        unique_pkg_versions = set(pkg_versions.values())

        if len(unique_pkg_versions) == 1:
            status = AssessmentStatus.PASS
            message = f"Package version consistent: {list(unique_pkg_versions)[0]}"
        elif len(unique_pkg_versions) == 0:
            status = AssessmentStatus.FAIL
            message = "No version found in package files"
        else:
            status = AssessmentStatus.FAIL
            message = f"Package version mismatch: {pkg_versions}"

        result = CheckResult(
            name="Version Sync",
            status=status,
            message=message,
            details=details
        )
        result.moon = self._status_to_moon(status)
        return result

    # =========================================================================
    # CHECK 2: Architecture Assessment
    # =========================================================================
    def check_architecture(self) -> CheckResult:
        """Run turtle assessment on architecture."""
        if self.quick:
            return CheckResult(
                name="Architecture Assessment",
                status=AssessmentStatus.SKIP,
                message="Skipped (quick mode)",
                moon="🌒"
            )

        details = []
        scores = []

        # Key directories to assess
        directories = [
            ("empirica/core", "Core modules"),
            ("empirica/cli", "CLI handlers"),
            ("empirica/data", "Data layer"),
        ]

        for dir_path, label in directories:
            full_path = self.root / dir_path
            if not full_path.exists():
                details.append(f"{label}: not found")
                continue

            try:
                result = subprocess.run(
                    ["empirica", "assess-directory", str(full_path), "--output", "json"],
                    capture_output=True, text=True, cwd=self.root, timeout=60
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    avg_health = data.get("average_health", 0)
                    scores.append(avg_health)
                    moon = self._score_to_moon(avg_health)
                    details.append(f"{label}: {moon} {avg_health:.2f}")
                else:
                    details.append(f"{label}: assessment failed")
            except subprocess.TimeoutExpired:
                details.append(f"{label}: timeout")
            except json.JSONDecodeError:
                details.append(f"{label}: invalid JSON output")
            except Exception as e:
                details.append(f"{label}: {str(e)[:50]}")

        if scores:
            avg_score = sum(scores) / len(scores)
            moon = self._score_to_moon(avg_score)

            if avg_score >= 0.70:
                status = AssessmentStatus.PASS
                message = f"Architecture health: {moon} {avg_score:.2f}"
            elif avg_score >= 0.50:
                status = AssessmentStatus.WARN
                message = f"Architecture needs attention: {moon} {avg_score:.2f}"
            else:
                status = AssessmentStatus.FAIL
                message = f"Architecture unhealthy: {moon} {avg_score:.2f}"
        else:
            status = AssessmentStatus.WARN
            message = "Could not assess architecture"
            moon = "🌒"

        result = CheckResult(
            name="Architecture Assessment",
            status=status,
            message=message,
            details=details
        )
        result.moon = moon if scores else "🌒"
        return result

    # =========================================================================
    # CHECK 3: PyPI Package Check
    # =========================================================================
    def check_pypi_packages(self) -> CheckResult:
        """Check empirica and empirica-mcp on PyPI."""
        details = []
        issues = []

        packages = ["empirica", "empirica-mcp"]

        for pkg in packages:
            try:
                result = subprocess.run(
                    ["pip", "index", "versions", pkg],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    # Parse versions from output
                    output = result.stdout + result.stderr
                    match = re.search(rf'{pkg}\s+\(([^)]+)\)', output)
                    if match:
                        latest = match.group(1)
                        details.append(f"{pkg}: latest={latest}")

                        # Compare with local version
                        if self.version and pkg == "empirica":
                            if latest != self.version:
                                details.append(f"  Local: {self.version} (newer)")
                    else:
                        details.append(f"{pkg}: available on PyPI")
                else:
                    # Try alternative method
                    result2 = subprocess.run(
                        ["pip", "show", pkg],
                        capture_output=True, text=True, timeout=30
                    )
                    if result2.returncode == 0:
                        match = re.search(r'Version:\s*(\S+)', result2.stdout)
                        if match:
                            details.append(f"{pkg}: installed={match.group(1)}")
                    else:
                        details.append(f"{pkg}: not found on PyPI")
                        if pkg == "empirica":
                            issues.append(f"{pkg} not on PyPI")
            except subprocess.TimeoutExpired:
                details.append(f"{pkg}: timeout")
            except Exception as e:
                details.append(f"{pkg}: {str(e)[:30]}")

        if issues:
            status = AssessmentStatus.FAIL
            message = f"PyPI issues: {', '.join(issues)}"
        else:
            status = AssessmentStatus.PASS
            message = "PyPI packages verified"

        result = CheckResult(
            name="PyPI Packages",
            status=status,
            message=message,
            details=details
        )
        result.moon = self._status_to_moon(status)
        return result

    def _parse_gitignore(self) -> List[str]:
        """Parse .gitignore and return list of ignored patterns."""
        gitignore = self.root / ".gitignore"
        if not gitignore.exists():
            return []

        patterns = []
        for line in gitignore.read_text().splitlines():
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Normalize pattern
            patterns.append(line.rstrip('/'))
        return patterns

    def _is_gitignored(self, path: Path, gitignore_patterns: List[str]) -> bool:
        """Check if a path matches any gitignore pattern."""
        path_str = str(path.relative_to(self.root)) if path.is_absolute() else str(path)

        for pattern in gitignore_patterns:
            # Direct match
            if pattern in path_str:
                return True
            # Directory match (pattern ends with /)
            if pattern.endswith('/') and pattern.rstrip('/') in path_str:
                return True
            # Glob-style match for simple patterns
            if pattern.startswith('*') and path_str.endswith(pattern[1:]):
                return True
            if pattern.endswith('*') and path_str.startswith(pattern[:-1]):
                return True
        return False

    # =========================================================================
    # CHECK 4: Privacy/Security Scan
    # =========================================================================
    def check_privacy_security(self) -> CheckResult:
        """Scan for sensitive, private, or dev content that shouldn't be released."""
        details = []
        issues = []
        warnings = []

        # Parse .gitignore for exclusions
        gitignore_patterns = self._parse_gitignore()

        # Patterns that should NEVER be in a release (even if gitignored, warn about existence)
        forbidden_patterns = {
            "files": [
                ".env", ".env.local", ".env.production",
                "secrets.json", "credentials.json", "config.secret",
                "*.pem", "*.key", "id_rsa", "id_ed25519",
                ".aws/credentials", ".gcp/credentials",
            ],
            "content": [
                r"sk-[a-zA-Z0-9]{20,}",  # OpenAI API key
                r"ANTHROPIC_API_KEY\s*=\s*['\"][^'\"]+",
                r"password\s*=\s*['\"][^'\"]{8,}",
                r"secret\s*=\s*['\"][^'\"]{8,}",
                r"/home/\w+/",  # Hardcoded home paths
                r"C:\\Users\\\w+\\",  # Windows home paths
            ]
        }

        # Patterns that warn but don't block
        # Note: "temp" excluded because "template" is a valid name pattern
        warn_patterns = {
            "files": [
                "*.draft*", "*.wip*", "*scratch*", "*tmp*",
                "*.bak", "*.backup", "*_old*",
                "research/*", "private/*", "internal/*",
            ],
            "dirs": [
                "notebooks/",  # Research notebooks
            ]
        }

        # Directories to always exclude from scanning (safe or user data)
        exclude_dirs = [".git", ".venv", "venv", ".venv-mcp", "node_modules", "__pycache__",
                        ".empirica", ".beads", ".qdrant_data", "dist", "build", "*.egg-info"]

        # Check for forbidden files (only if NOT gitignored)
        for pattern in forbidden_patterns["files"]:
            found = list(self.root.glob(f"**/{pattern}"))
            for f in found:
                # Skip if in excluded directories
                if any(excl in str(f) for excl in exclude_dirs):
                    continue
                # Skip if gitignored
                if self._is_gitignored(f, gitignore_patterns):
                    continue
                issues.append(f"FORBIDDEN (not gitignored): {f.relative_to(self.root)}")

        # Check for hardcoded secrets in Python files (only in empirica source)
        py_files = list(self.root.glob("empirica/**/*.py"))
        for py_file in py_files[:100]:  # Limit scan
            try:
                content = py_file.read_text()
                for pattern in forbidden_patterns["content"]:
                    if re.search(pattern, content):
                        issues.append(f"SECRET: {py_file.relative_to(self.root)}")
                        break
            except Exception:
                pass

        # Check for warning patterns (only if NOT gitignored)
        for pattern in warn_patterns["files"]:
            found = list(self.root.glob(f"**/{pattern}"))
            for f in found[:2]:
                if any(excl in str(f) for excl in exclude_dirs):
                    continue
                if self._is_gitignored(f, gitignore_patterns):
                    continue
                warnings.append(f"DEV FILE: {f.relative_to(self.root)}")

        # Check for user data directories that are NOT gitignored
        user_data_dirs = [".empirica/sessions", ".qdrant_data", ".beads", "notebooks"]
        for dir_name in user_data_dirs:
            dir_path = self.root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                if not self._is_gitignored(dir_path, gitignore_patterns):
                    warnings.append(f"USER DATA (not gitignored!): {dir_name}")

        # Check .gitignore includes critical security patterns
        gitignore = self.root / ".gitignore"
        if gitignore.exists():
            gitignore_content = gitignore.read_text()
            critical_ignores = [".env", "*.key", "*.pem", ".empirica/"]
            missing = [p for p in critical_ignores if p not in gitignore_content]
            if missing:
                warnings.append(f".gitignore missing: {missing}")
        else:
            issues.append("No .gitignore file found!")

        # Build result
        details.extend(issues)
        details.extend(warnings)

        if issues:
            status = AssessmentStatus.FAIL
            message = f"SECURITY: {len(issues)} forbidden items found"
        elif warnings:
            status = AssessmentStatus.WARN
            message = f"Privacy: {len(warnings)} items to review"
        else:
            status = AssessmentStatus.PASS
            message = "No sensitive content detected"

        result = CheckResult(
            name="Privacy/Security Scan",
            status=status,
            message=message,
            details=details[:10]  # Limit output
        )
        result.moon = self._status_to_moon(status)
        return result

    # =========================================================================
    # CHECK 5: Documentation Assessment
    # =========================================================================
    def check_documentation(self) -> CheckResult:
        """Verify documentation is current."""
        details = []
        issues = []

        # Check key documentation files exist
        required_docs = [
            ("README.md", "Main readme"),
            ("CHANGELOG.md", "Changelog"),
            ("docs/", "Documentation directory"),
        ]

        for path, label in required_docs:
            full_path = self.root / path
            if full_path.exists():
                details.append(f"{label}: exists")
            else:
                issues.append(f"{label}: MISSING")

        # Check CHANGELOG has entry for current version
        changelog = self.root / "CHANGELOG.md"
        if changelog.exists() and self.version:
            content = changelog.read_text()
            if self.version in content:
                details.append(f"CHANGELOG: has v{self.version} entry")
            else:
                issues.append(f"CHANGELOG: missing v{self.version} entry")

        # Check README is not placeholder
        readme = self.root / "README.md"
        if readme.exists():
            content = readme.read_text()
            if len(content) < 500:
                issues.append("README: too short (placeholder?)")
            elif "TODO" in content or "FIXME" in content:
                issues.append("README: contains TODO/FIXME")

        if issues:
            status = AssessmentStatus.WARN
            message = f"Docs need attention: {len(issues)} issues"
        else:
            status = AssessmentStatus.PASS
            message = "Documentation verified"

        result = CheckResult(
            name="Documentation",
            status=status,
            message=message,
            details=details + issues
        )
        result.moon = self._status_to_moon(status)
        return result

    # =========================================================================
    # CHECK 6: Git Status
    # =========================================================================
    def check_git_status(self) -> CheckResult:
        """Check git status and branch."""
        details = []
        issues = []

        try:
            # Current branch
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, cwd=self.root
            )
            branch = result.stdout.strip()
            details.append(f"Branch: {branch}")

            if branch not in ["main", "master", "develop"]:
                issues.append(f"Not on main branch: {branch}")

            # Uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=self.root
            )
            if result.stdout.strip():
                changes = len(result.stdout.strip().split("\n"))
                issues.append(f"Uncommitted changes: {changes} files")
            else:
                details.append("Working tree: clean")

            # Unpushed commits
            result = subprocess.run(
                ["git", "log", "@{u}..", "--oneline"],
                capture_output=True, text=True, cwd=self.root
            )
            if result.stdout.strip():
                commits = len(result.stdout.strip().split("\n"))
                issues.append(f"Unpushed commits: {commits}")
            else:
                details.append("Remote: up to date")

        except Exception as e:
            details.append(f"Git check error: {str(e)[:50]}")

        if issues:
            status = AssessmentStatus.WARN
            message = f"Git issues: {len(issues)}"
        else:
            status = AssessmentStatus.PASS
            message = "Git ready for release"

        result = CheckResult(
            name="Git Status",
            status=status,
            message=message,
            details=details + issues
        )
        result.moon = self._status_to_moon(status)
        return result

    # =========================================================================
    # Main Run
    # =========================================================================
    def run(self) -> Dict[str, Any]:
        """Run all epistemic release checks."""
        checks = [
            self.check_version_sync,
            self.check_architecture,
            self.check_pypi_packages,
            self.check_privacy_security,
            self.check_documentation,
            self.check_git_status,
        ]

        for check in checks:
            try:
                result = check()
                self.results.append(result)
            except Exception as e:
                self.results.append(CheckResult(
                    name=check.__name__.replace("check_", "").replace("_", " ").title(),
                    status=AssessmentStatus.FAIL,
                    message=f"Check failed: {str(e)[:50]}",
                    moon="🌑"
                ))

        # Calculate overall status
        statuses = [r.status for r in self.results]
        if AssessmentStatus.FAIL in statuses:
            overall_status = "NOT READY"
            overall_moon = "🌑"
        elif AssessmentStatus.WARN in statuses:
            overall_status = "READY WITH WARNINGS"
            overall_moon = "🌓"
        else:
            overall_status = "READY"
            overall_moon = "🌕"

        return {
            "ok": overall_status == "READY",
            "status": overall_status,
            "moon": overall_moon,
            "version": self.version,
            "checks": [r.to_dict() for r in self.results],
            "summary": {
                "pass": sum(1 for r in self.results if r.status == AssessmentStatus.PASS),
                "warn": sum(1 for r in self.results if r.status == AssessmentStatus.WARN),
                "fail": sum(1 for r in self.results if r.status == AssessmentStatus.FAIL),
                "skip": sum(1 for r in self.results if r.status == AssessmentStatus.SKIP),
            }
        }


def handle_release_ready_command(args):
    """Handle release-ready command - Epistemic release assessment."""
    try:
        project_root = Path(getattr(args, 'project_root', None) or os.getcwd())
        quick = getattr(args, 'quick', False)
        output_format = getattr(args, 'output', 'human')

        agent = EpistemicReleaseAgent(project_root=project_root, quick=quick)
        result = agent.run()

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output
            print()
            print("=" * 60)
            print(f"  {result['moon']} EPISTEMIC RELEASE ASSESSMENT")
            print("=" * 60)
            print()

            if result['version']:
                print(f"  Version: {result['version']}")
                print()

            for check in result['checks']:
                status_icon = {
                    "pass": "✅",
                    "warn": "⚠️",
                    "fail": "❌",
                    "skip": "⏭️"
                }.get(check['status'], "?")

                print(f"{check['moon']} {check['name']}")
                print(f"   {status_icon} {check['message']}")

                for detail in check['details'][:5]:
                    print(f"      • {detail}")
                print()

            print("=" * 60)
            summary = result['summary']
            print(f"  Summary: {summary['pass']} pass, {summary['warn']} warn, "
                  f"{summary['fail']} fail, {summary['skip']} skip")
            print()

            if result['status'] == "READY":
                print("  🌕 RELEASE READY")
            elif result['status'] == "READY WITH WARNINGS":
                print("  🌓 RELEASE READY (with warnings)")
            else:
                print("  🌑 NOT READY FOR RELEASE")
            print("=" * 60)
            print()

        return 0 if result['ok'] else 1

    except Exception as e:
        handle_cli_error(e, "release-ready", getattr(args, 'output', 'json'))
        return 1
