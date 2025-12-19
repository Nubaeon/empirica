#!/usr/bin/env python3
"""
Automated Release Script for Empirica
Single source of truth: pyproject.toml version

Usage:
    python scripts/release.py --dry-run    # Preview changes
    python scripts/release.py              # Execute release
"""

import argparse
import hashlib
import os
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
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.repo_root = Path(__file__).parent.parent
        self.version: Optional[str] = None
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

    def run_command(self, cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command"""
        cmd_str = " ".join(cmd)
        if self.dry_run:
            info(f"Would run: {cmd_str}")
            return subprocess.CompletedProcess(cmd, 0, "", "")

        info(f"Running: {cmd_str}")
        return subprocess.run(cmd, check=check, capture_output=True, text=True)

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
        self.run_command(["python3", "-m", "build", "--wheel", "--sdist"])
        success("Package built successfully")

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
        """Build and push Docker image"""
        log("\n" + "="*60)
        log("🐳 Building and pushing Docker image")
        log("="*60)

        tags = [
            f"nubaeon/empirica:{self.version}",
            "nubaeon/empirica:latest"
        ]

        # Build
        build_cmd = ["docker", "build", "."]
        for tag in tags:
            build_cmd.extend(["-t", tag])

        self.run_command(build_cmd)
        success("Docker image built")

        # Push
        for tag in tags:
            self.run_command(["docker", "push", tag])
            success(f"Pushed: {tag}")

    def create_github_release(self):
        """Create GitHub release"""
        log("\n" + "="*60)
        log("📝 Creating GitHub release")
        log("="*60)

        tag = f"v{self.version}"
        wheel = f"dist/empirica-{self.version}-py3-none-any.whl"
        tarball = f"dist/empirica-{self.version}.tar.gz"

        notes = f"""## What's in v{self.version}

See CHANGELOG.md for detailed release notes.

### Installation
```bash
pip install empirica=={self.version}
```

### Docker
```bash
docker pull nubaeon/empirica:{self.version}
```
"""

        self.run_command([
            "gh", "release", "create", tag,
            wheel, tarball,
            "--title", f"v{self.version}",
            "--notes", notes
        ])
        success(f"Created GitHub release: {tag}")

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

            # Build package first
            self.build_package()

            # Calculate tarball SHA256
            self.tarball_sha256 = self.calculate_sha256()

            # Update all distribution files
            self.update_homebrew_formula()
            self.update_dockerfile()
            self.update_chocolatey_nuspec()

            # Publish
            self.publish_to_pypi()
            self.create_git_tag()
            self.build_and_push_docker()
            self.create_github_release()

            log("\n╔════════════════════════════════════════════════════════════╗")
            log("║  ✅ Release Complete!                                      ║")
            log("╚════════════════════════════════════════════════════════════╝\n")

            success(f"Released empirica v{self.version}")
            info(f"PyPI: https://pypi.org/project/empirica/{self.version}/")
            info(f"Docker: docker pull nubaeon/empirica:{self.version}")
            info(f"GitHub: https://github.com/Nubaeon/empirica/releases/tag/v{self.version}")

        except Exception as e:
            error(f"Release failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Automated release script for Empirica")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing"
    )
    args = parser.parse_args()

    manager = ReleaseManager(dry_run=args.dry_run)
    manager.run()


if __name__ == "__main__":
    main()
