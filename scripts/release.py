#!/usr/bin/env python3
"""
Automated Release Script for Empirica
Single source of truth: pyproject.toml version

Usage:
    python scripts/release.py --dry-run                           # Preview full release
    python scripts/release.py                                     # Execute full release
    python scripts/release.py --version-only --old-version 1.5.6  # Update versions only
    python scripts/release.py --old-version 1.5.6                 # Full release with sweep
"""

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def log(msg: str, color: str = RESET):
    print(f"{color}{msg}{RESET}")


def error(msg: str):
    log(f"❌ ERROR: {msg}", RED)
    sys.exit(1)


def warning(msg: str):
    log(f"⚠️  WARNING: {msg}", YELLOW)


def success(msg: str):
    log(f"✅ {msg}", GREEN)


def info(msg: str):
    log(f"ℹ️  {msg}", BLUE)


class ReleaseManager:
    def __init__(self, dry_run: bool = False, old_version: Optional[str] = None):
        self.dry_run = dry_run
        self.repo_root = Path(__file__).parent.parent
        self.version: Optional[str] = None
        self.old_version: Optional[str] = old_version
        self.tarball_sha256: Optional[str] = None

    def read_version(self) -> str:
        """Read version from pyproject.toml"""
        pyproject_path = self.repo_root / "pyproject.toml"
        if not pyproject_path.exists():
            error(f"pyproject.toml not found at {pyproject_path}")

        content = pyproject_path.read_text()
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if not match:
            error("Could not find version in pyproject.toml")

        version = match.group(1)
        info(f"Version from pyproject.toml: {version}")
        return version

    def calculate_sha256(self) -> str:
        """Calculate SHA256 of the tarball"""
        tarball_pattern = f"empirica-{self.version}.tar.gz"
        dist_dir = self.repo_root / "dist"
        tarball = dist_dir / tarball_pattern

        if not tarball.exists():
            if self.dry_run:
                info(f"Tarball not found (dry run): {tarball}")
                return "0" * 64
            error(f"Tarball not found: {tarball}")

        sha256 = hashlib.sha256()
        with open(tarball, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)

        sha256_hex = sha256.hexdigest()
        info(f"Tarball SHA256: {sha256_hex}")
        return sha256_hex

    def update_homebrew_formula(self):
        """Update Homebrew formula with new version and SHA256"""
        formula_path = self.repo_root / "packaging/homebrew/empirica.rb"
        if not formula_path.exists():
            warning(f"Homebrew formula not found: {formula_path}")
            return

        content = formula_path.read_text()

        # Update URL
        url_pattern = r'url "https://github\.com/Nubaeon/empirica/releases/download/v[^/]+/empirica-[^"]+\.tar\.gz"'
        new_url = f'url "https://github.com/Nubaeon/empirica/releases/download/v{self.version}/empirica-{self.version}.tar.gz"'
        content = re.sub(url_pattern, new_url, content)

        # Update SHA256
        sha_pattern = r'sha256 "[a-f0-9]{64}"'
        new_sha = f'sha256 "{self.tarball_sha256}"'
        content = re.sub(sha_pattern, new_sha, content)

        if not self.dry_run:
            formula_path.write_text(content)
            success(f"Updated Homebrew formula: {formula_path}")
        else:
            info(f"Would update Homebrew formula: {formula_path}")

    def update_homebrew_tap(self):
        """Copy updated formula to the Homebrew tap repo and push"""
        log("\n" + "="*60)
        log("🍺 Updating Homebrew tap")
        log("="*60)

        local_formula = self.repo_root / "packaging/homebrew/empirica.rb"
        if not local_formula.exists():
            warning(f"Local formula not found: {local_formula}")
            return

        # Look for tap repo in common locations
        tap_candidates = [
            self.repo_root.parent / "homebrew-tap",          # sibling dir
            Path.home() / "empirical-ai" / "homebrew-tap",   # home dir
        ]

        tap_repo = None
        for candidate in tap_candidates:
            if (candidate / "empirica.rb").exists():
                tap_repo = candidate
                break

        if tap_repo is None:
            warning("Homebrew tap repo not found. Checked:")
            for c in tap_candidates:
                warning(f"  {c}")
            info("Manual step: copy packaging/homebrew/empirica.rb to your tap repo and push")
            return

        tap_formula = tap_repo / "empirica.rb"

        if not self.dry_run:
            import shutil
            shutil.copy2(local_formula, tap_formula)
            success(f"Copied formula to {tap_formula}")

            # Commit and push
            self.run_command(["git", "add", "empirica.rb"], cwd=str(tap_repo))
            self.run_command([
                "git", "commit", "-m",
                f"Update empirica to {self.version}"
            ], cwd=str(tap_repo), check=False)
            self.run_command(["git", "push"], cwd=str(tap_repo))
            success(f"Homebrew tap updated and pushed: {tap_repo}")
        else:
            info(f"Would copy {local_formula} → {tap_formula}")
            info(f"Would commit and push in {tap_repo}")

    def update_dockerfile(self):
        """Update Dockerfile with new version"""
        dockerfile_path = self.repo_root / "Dockerfile"
        if not dockerfile_path.exists():
            warning(f"Dockerfile not found: {dockerfile_path}")
            return

        content = dockerfile_path.read_text()

        # Update version label
        content = re.sub(
            r'LABEL version="[^"]+"',
            f'LABEL version="{self.version}"',
            content
        )

        # Update wheel filename in COPY
        content = re.sub(
            r'COPY dist/empirica-[^-]+-py3-none-any\.whl',
            f'COPY dist/empirica-{self.version}-py3-none-any.whl',
            content
        )

        # Update wheel filename in RUN pip install
        content = re.sub(
            r'/tmp/empirica-[^-]+-py3-none-any\.whl',
            f'/tmp/empirica-{self.version}-py3-none-any.whl',
            content,
            count=2  # Both COPY and RUN lines
        )

        if not self.dry_run:
            dockerfile_path.write_text(content)
            success(f"Updated Dockerfile: {dockerfile_path}")
        else:
            info(f"Would update Dockerfile: {dockerfile_path}")

    def update_chocolatey_nuspec(self):
        """Update Chocolatey nuspec with new version"""
        nuspec_path = self.repo_root / "packaging/chocolatey/empirica.nuspec"
        if not nuspec_path.exists():
            warning(f"Chocolatey nuspec not found: {nuspec_path}")
            return

        content = nuspec_path.read_text()

        # Update version
        content = re.sub(
            r'<version>[^<]+</version>',
            f'<version>{self.version}</version>',
            content
        )

        if not self.dry_run:
            nuspec_path.write_text(content)
            success(f"Updated Chocolatey nuspec: {nuspec_path}")
        else:
            info(f"Would update Chocolatey nuspec: {nuspec_path}")

    def update_version_strings(self):
        """Update version strings in all source files not covered by other methods.

        Covers: __init__.py, empirica-mcp/pyproject.toml, install.py,
        setup_claude_code.py, install.sh (both copies), plugin.json (both copies),
        CLAUDE.md (canonical + both template copies), Dockerfile.alpine.
        """
        version_files = [
            # (path, pattern, replacement)
            (
                self.repo_root / "empirica" / "__init__.py",
                r'__version__\s*=\s*"[^"]+"',
                f'__version__ = "{self.version}"',
            ),
            (
                self.repo_root / "empirica-mcp" / "pyproject.toml",
                r'^version\s*=\s*"[^"]+"',
                f'version = "{self.version}"',
            ),
            (
                self.repo_root / "scripts" / "install.py",
                r'EMPIRICA_VERSION\s*=\s*"[^"]+"',
                f'EMPIRICA_VERSION = "{self.version}"',
            ),
            (
                self.repo_root / "empirica" / "cli" / "command_handlers" / "setup_claude_code.py",
                r'PLUGIN_VERSION\s*=\s*"[^"]+"',
                f'PLUGIN_VERSION = "{self.version}"',
            ),
            (
                self.repo_root / "claude-code-integration" / "install.sh",
                r'PLUGIN_VERSION="[^"]+"',
                f'PLUGIN_VERSION="{self.version}"',
            ),
            (
                self.repo_root / "empirica" / "plugins" / "claude-code-integration" / "install.sh",
                r'PLUGIN_VERSION="[^"]+"',
                f'PLUGIN_VERSION="{self.version}"',
            ),
            (
                self.repo_root / "claude-code-integration" / ".claude-plugin" / "plugin.json",
                r'"version":\s*"[^"]+"',
                f'"version": "{self.version}"',
            ),
            (
                self.repo_root / "empirica" / "plugins" / "claude-code-integration" / ".claude-plugin" / "plugin.json",
                r'"version":\s*"[^"]+"',
                f'"version": "{self.version}"',
            ),
            # __init__.py docstring version
            (
                self.repo_root / "empirica" / "__init__.py",
                r'^Version:\s*[0-9]+\.[0-9]+\.[0-9]+',
                f'Version: {self.version}',
            ),
            # README.md version badge and footer
            (
                self.repo_root / "README.md",
                r'badge/version-[0-9]+\.[0-9]+\.[0-9]+-blue\)\]\(https://github\.com/Nubaeon/empirica/releases/tag/v[0-9]+\.[0-9]+\.[0-9]+\)',
                f'badge/version-{self.version}-blue)](https://github.com/Nubaeon/empirica/releases/tag/v{self.version})',
            ),
            # Chocolatey install script version
            (
                self.repo_root / "packaging" / "chocolatey" / "tools" / "chocolateyinstall.ps1",
                r"\$packageVersion\s*=\s*'[^']+'",
                f"$packageVersion = '{self.version}'",
            ),
            # Canonical Core prompt version header
            (
                self.repo_root / "docs" / "human" / "developers" / "system-prompts" / "CANONICAL_CORE.md",
                r'Canonical Core v[0-9]+\.[0-9]+\.[0-9]+',
                f'Canonical Core v{self.version}',
            ),
            # PROJECT_CONFIG version
            (
                self.repo_root / ".empirica-project" / "PROJECT_CONFIG.yaml",
                r'version:\s*"[^"]+"',
                f'version: "{self.version}"',
            ),
        ]

        # Dockerfile.alpine (same patterns as Dockerfile)
        alpine_path = self.repo_root / "Dockerfile.alpine"
        if alpine_path.exists():
            content = alpine_path.read_text()
            content = re.sub(r'LABEL version="[^"]+"', f'LABEL version="{self.version}"', content)
            content = re.sub(
                r'COPY dist/empirica-[^-]+-py3-none-any\.whl',
                f'COPY dist/empirica-{self.version}-py3-none-any.whl',
                content,
            )
            content = re.sub(
                r'/tmp/empirica-[^-]+-py3-none-any\.whl',
                f'/tmp/empirica-{self.version}-py3-none-any.whl',
                content,
                count=2,
            )
            if not self.dry_run:
                alpine_path.write_text(content)
                success(f"Updated: {alpine_path}")
            else:
                info(f"Would update: {alpine_path}")

        for filepath, pattern, replacement in version_files:
            if not filepath.exists():
                warning(f"Not found: {filepath}")
                continue

            content = filepath.read_text()
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

            if content == new_content:
                info(f"Already up to date: {filepath}")
                continue

            if not self.dry_run:
                filepath.write_text(new_content)
                success(f"Updated: {filepath}")
            else:
                info(f"Would update: {filepath}")

    def sweep_version(self, old_version: str):
        """Broad sweep: replace old_version → self.version in all version-bearing files.

        Catches references that targeted regex patterns miss: Dockerfile comments,
        README docker commands, CLAUDE.md headers, DOCKERHUB_README, etc.
        Skips CHANGELOG files (historical references) and .git directory.
        """
        log("\n" + "=" * 60)
        log(f"🔍 Sweeping {old_version} → {self.version}")
        log("=" * 60)

        sweep_files = []
        skip_names = {"CHANGELOG.md", "release.py"}
        skip_dirs = {".git", ".venv", ".venv-mcp", "dist", "build",
                     ".empirica_reflex_logs", "node_modules", "__pycache__",
                     ".qdrant_data"}
        extensions = {".md", ".py", ".toml", ".yaml", ".yml", ".json", ".rb",
                      ".nuspec", ".ps1", ".sh"}

        for ext in extensions:
            for filepath in self.repo_root.rglob(f"*{ext}"):
                if any(d in filepath.parts for d in skip_dirs):
                    continue
                if filepath.name in skip_names:
                    continue
                if ".egg-info" in str(filepath):
                    continue
                sweep_files.append(filepath)

        # Also include Dockerfiles (no extension)
        for name in ["Dockerfile", "Dockerfile.alpine"]:
            p = self.repo_root / name
            if p.exists():
                sweep_files.append(p)

        updated = 0
        for filepath in sweep_files:
            try:
                content = filepath.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            if old_version not in content:
                continue

            new_content = content.replace(old_version, self.version)
            if not self.dry_run:
                filepath.write_text(new_content)
                success(f"Swept: {filepath.relative_to(self.repo_root)}")
            else:
                info(f"Would sweep: {filepath.relative_to(self.repo_root)}")
            updated += 1

        info(f"Sweep complete: {updated} files updated")

    def run_command(self, cmd: list[str], check: bool = True, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """Run a shell command"""
        cmd_str = " ".join(cmd)
        cwd_info = f" (in {cwd})" if cwd else ""
        if self.dry_run:
            info(f"Would run: {cmd_str}{cwd_info}")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        info(f"Running: {cmd_str}{cwd_info}")
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=cwd)
        if result.returncode != 0:
            if result.stderr:
                warning(f"stderr: {result.stderr.strip()}")
            if check:
                error(f"Command failed (exit {result.returncode}): {cmd_str}")
        return result

    def build_package(self):
        """Build Python package"""
        log("\n" + "="*60)
        log("📦 Building Python package")
        log("="*60)

        # Clean old builds
        for path in ["dist", "build", "empirica.egg-info"]:
            full_path = self.repo_root / path
            if full_path.exists():
                if not self.dry_run:
                    if full_path.is_dir():
                        import shutil
                        shutil.rmtree(full_path)
                    else:
                        full_path.unlink()
                    info(f"Removed {path}")

        # Build
        self.run_command(["python3", "-m", "build", "--wheel", "--sdist"],
                         cwd=str(self.repo_root))
        success("Package built successfully")

    def build_mcp_package(self):
        """Build empirica-mcp package"""
        log("\n" + "="*60)
        log("📦 Building empirica-mcp package")
        log("="*60)

        mcp_dir = self.repo_root / "empirica-mcp"
        if not mcp_dir.exists():
            warning(f"empirica-mcp directory not found: {mcp_dir}")
            return

        # Clean old builds
        for path in ["dist", "build", "empirica_mcp.egg-info"]:
            full_path = mcp_dir / path
            if full_path.exists():
                if not self.dry_run:
                    if full_path.is_dir():
                        import shutil
                        shutil.rmtree(full_path)
                    else:
                        full_path.unlink()
                    info(f"Removed empirica-mcp/{path}")

        # Build
        self.run_command(
            ["python3", "-m", "build", "--wheel", "--sdist"],
            cwd=str(mcp_dir)
        )
        success("empirica-mcp package built successfully")

    def publish_to_pypi(self):
        """Publish to PyPI"""
        log("\n" + "="*60)
        log("📤 Publishing to PyPI")
        log("="*60)

        if self.dry_run:
            info("Would publish to PyPI using twine")
            return

        self.run_command(["python3", "-m", "twine", "upload", f"dist/empirica-{self.version}*"])
        success(f"Published to PyPI: https://pypi.org/project/empirica/{self.version}/")

    def publish_mcp_to_pypi(self):
        """Publish empirica-mcp to PyPI"""
        log("\n" + "="*60)
        log("📤 Publishing empirica-mcp to PyPI")
        log("="*60)

        mcp_dir = self.repo_root / "empirica-mcp"
        if not (mcp_dir / "dist").exists():
            warning("empirica-mcp dist/ not found, skipping MCP publish")
            return

        if self.dry_run:
            info("Would publish empirica-mcp to PyPI using twine")
            return

        self.run_command([
            "python3", "-m", "twine", "upload",
            str(mcp_dir / "dist" / f"empirica_mcp-{self.version}*")
        ])
        success(f"Published empirica-mcp to PyPI: https://pypi.org/project/empirica-mcp/{self.version}/")

    def create_git_tag(self):
        """Create and push git tag"""
        log("\n" + "="*60)
        log("🏷️  Creating Git tag")
        log("="*60)

        tag = f"v{self.version}"

        # Commit distribution updates
        self.run_command(["git", "add", "packaging/", "Dockerfile"])
        self.run_command([
            "git", "commit", "-m",
            f"chore: automated release {self.version}\n\n"
            f"- Updated all distribution channels\n"
            f"- SHA256: {self.tarball_sha256}"
        ], check=False)  # May have no changes

        # Create tag
        self.run_command([
            "git", "tag", "-a", tag,
            "-m", f"Release {self.version}"
        ])

        # Push
        self.run_command(["git", "push", "origin", "main", "--tags"])
        success(f"Created and pushed tag: {tag}")

    def build_and_push_docker(self):
        """Build and push Docker images (Debian + Alpine)"""
        log("\n" + "="*60)
        log("🐳 Building and pushing Docker images")
        log("="*60)

        # Debian image
        debian_tags = [
            f"nubaeon/empirica:{self.version}",
            "nubaeon/empirica:latest"
        ]

        build_cmd = ["docker", "build", "."]
        for tag in debian_tags:
            build_cmd.extend(["-t", tag])

        self.run_command(build_cmd, cwd=str(self.repo_root))
        success("Docker image built (Debian)")

        for tag in debian_tags:
            self.run_command(["docker", "push", tag])
            success(f"Pushed: {tag}")

        # Alpine image
        alpine_dockerfile = self.repo_root / "Dockerfile.alpine"
        if alpine_dockerfile.exists():
            alpine_tags = [
                f"nubaeon/empirica:{self.version}-alpine",
            ]

            build_cmd = ["docker", "build", "-f", "Dockerfile.alpine", "."]
            for tag in alpine_tags:
                build_cmd.extend(["-t", tag])

            self.run_command(build_cmd, cwd=str(self.repo_root))
            success("Docker image built (Alpine)")

            for tag in alpine_tags:
                self.run_command(["docker", "push", tag])
                success(f"Pushed: {tag}")
        else:
            warning("Dockerfile.alpine not found, skipping Alpine build")

    def create_github_release(self):
        """Create GitHub release"""
        log("\n" + "="*60)
        log("📝 Creating GitHub release")
        log("="*60)

        tag = f"v{self.version}"
        wheel = f"dist/empirica-{self.version}-py3-none-any.whl"
        tarball = f"dist/empirica-{self.version}.tar.gz"

        # Include empirica-mcp assets if built
        mcp_wheel = f"empirica-mcp/dist/empirica_mcp-{self.version}-py3-none-any.whl"
        mcp_tarball = f"empirica-mcp/dist/empirica_mcp-{self.version}.tar.gz"
        assets = [wheel, tarball]
        mcp_wheel_path = self.repo_root / mcp_wheel
        mcp_tarball_path = self.repo_root / mcp_tarball
        if mcp_wheel_path.exists():
            assets.append(mcp_wheel)
        if mcp_tarball_path.exists():
            assets.append(mcp_tarball)

        notes = f"""## What's in v{self.version}

See CHANGELOG.md for detailed release notes.

### Installation
```bash
pip install empirica=={self.version}
```

### Docker
```bash
# Security-hardened Alpine (recommended)
docker pull nubaeon/empirica:{self.version}-alpine

# Debian slim
docker pull nubaeon/empirica:{self.version}
```

### Homebrew
```bash
brew tap nubaeon/tap
brew install empirica
```
"""

        self.run_command([
            "gh", "release", "create", tag,
            *assets,
            "--title", f"v{self.version}",
            "--notes", notes
        ])
        success(f"Created GitHub release: {tag}")

    def run_version_update(self):
        """Update version strings only (no build/publish)."""
        log("\n╔════════════════════════════════════════════════════════════╗")
        log("║  Empirica Version Update                                   ║")
        log("╚════════════════════════════════════════════════════════════╝\n")

        if self.dry_run:
            warning("DRY RUN MODE - No changes will be made\n")

        self.version = self.read_version()

        if not self.old_version:
            error("--old-version required for version-only mode")

        # Targeted regex updates (structural patterns)
        self.update_version_strings()
        self.update_dockerfile()
        self.update_chocolatey_nuspec()

        # Broad sweep catches everything else (comments, docker examples, etc.)
        self.sweep_version(self.old_version)

        success(f"All version strings updated to {self.version}")
        info("Homebrew formula SHA256 will be updated during full release.")

    def run(self):
        """Execute full release process"""
        log("\n╔════════════════════════════════════════════════════════════╗")
        log("║  Empirica Automated Release Pipeline                       ║")
        log("╚════════════════════════════════════════════════════════════╝\n")

        if self.dry_run:
            warning("DRY RUN MODE - No changes will be made\n")

        try:
            # Read version from pyproject.toml (single source of truth)
            self.version = self.read_version()

            # Build packages
            self.build_package()
            self.build_mcp_package()

            # Calculate tarball SHA256
            self.tarball_sha256 = self.calculate_sha256()

            # Update all distribution files (targeted + broad sweep)
            self.update_version_strings()
            self.update_homebrew_formula()
            self.update_dockerfile()
            self.update_chocolatey_nuspec()
            if self.old_version:
                self.sweep_version(self.old_version)

            # Publish
            self.publish_to_pypi()
            self.publish_mcp_to_pypi()
            self.create_git_tag()
            self.build_and_push_docker()
            self.create_github_release()
            self.update_homebrew_tap()

            log("\n╔════════════════════════════════════════════════════════════╗")
            log("║  ✅ Release Complete!                                      ║")
            log("╚════════════════════════════════════════════════════════════╝\n")

            success(f"Released empirica v{self.version}")
            info(f"PyPI: https://pypi.org/project/empirica/{self.version}/")
            info(f"PyPI (MCP): https://pypi.org/project/empirica-mcp/{self.version}/")
            info(f"Docker: docker pull nubaeon/empirica:{self.version}")
            info(f"Docker: docker pull nubaeon/empirica:{self.version}-alpine")
            info(f"GitHub: https://github.com/Nubaeon/empirica/releases/tag/v{self.version}")
            info(f"Homebrew: brew upgrade empirica")

        except Exception as e:
            error(f"Release failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Automated release script for Empirica")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing"
    )
    parser.add_argument(
        "--old-version",
        help="Previous version for broad sweep replacement (e.g. 1.5.6)"
    )
    parser.add_argument(
        "--version-only",
        action="store_true",
        help="Update version strings only (no build/publish). Requires --old-version."
    )
    args = parser.parse_args()

    manager = ReleaseManager(dry_run=args.dry_run, old_version=args.old_version)
    if args.version_only:
        manager.run_version_update()
    else:
        manager.run()


if __name__ == "__main__":
    main()
