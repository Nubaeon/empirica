# Empirica Release Process

**Single Source of Truth:** `pyproject.toml` version field

## Automated Release (Recommended)

### 1. Update Version
Edit `pyproject.toml` and update the version:
```toml
[project]
version = "1.0.3"  # Update this
```

### 2. Preview Changes
```bash
python scripts/release.py --dry-run
```

This will show you what would be updated:
- ✅ Homebrew formula (SHA256 + URL)
- ✅ Dockerfile (version label + wheel paths)
- ✅ Chocolatey nuspec (version)
- ✅ PyPI publish
- ✅ Docker build + push
- ✅ Git tag + GitHub release

### 3. Execute Release
```bash
python scripts/release.py
```

That's it! The script will:
1. Build Python package
2. Calculate tarball SHA256
3. Update all distribution files
4. Publish to PyPI
5. Create git tag and push
6. Build and push Docker images
7. Create GitHub release with artifacts

## What Gets Updated Automatically

| File | What Changes |
|------|-------------|
| `packaging/homebrew/empirica.rb` | URL + SHA256 |
| `Dockerfile` | Version label + wheel filename |
| `packaging/chocolatey/empirica.nuspec` | Version number |
| PyPI | Package published |
| Docker Hub | `nubaeon/empirica:VERSION` + `:latest` |
| GitHub | Tag + Release with wheels |

## Manual Steps (If Needed)

### Update MCP Config (For Other Repos)
If using Empirica MCP in another repo (like Antigravity), update the config:

**Old (local file-based):**
```json
{
  "mcpServers": {
    "empirica": {
      "command": "python3",
      "args": ["mcp_local/empirica_mcp_server.py"],
      "cwd": "/path/to/empirica",
      "env": {...}
    }
  }
}
```

**New (package-based):**
```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp"
    }
  }
}
```

### Homebrew Tap Publishing
```bash
# If you have a Homebrew tap
cp packaging/homebrew/empirica.rb /path/to/homebrew-tap/Formula/
cd /path/to/homebrew-tap
git add Formula/empirica.rb
git commit -m "Update empirica to vX.Y.Z"
git push
```

### Chocolatey Publishing (Windows)
```bash
cd packaging/chocolatey
choco pack
choco push empirica.X.Y.Z.nupkg --source https://push.chocolatey.org/ --api-key YOUR_KEY
```

## Version Bumping Guidelines

Follow [Semantic Versioning](https://semver.org/):

- **Patch (1.0.X)**: Bug fixes, no API changes
  - Example: `1.0.2` → `1.0.3`
  - Use case: Fixed MCP dependency, corrected paths

- **Minor (1.X.0)**: New features, backward compatible
  - Example: `1.0.3` → `1.1.0`
  - Use case: Added new CLI command, new optional feature

- **Major (X.0.0)**: Breaking changes
  - Example: `1.3.2` → `2.0.0`
  - Use case: Changed CASCADE workflow, removed deprecated APIs

## Troubleshooting

### "Tarball not found"
Make sure you've built the package first:
```bash
python -m build
```

### "Permission denied" on Docker push
```bash
docker login
```

### "GitHub CLI not found"
Install gh CLI:
```bash
# macOS
brew install gh

# Linux
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
```

Then authenticate:
```bash
gh auth login
```

### Want to skip a step?
Edit `scripts/release.py` and comment out the step in the `run()` method.

## Quick Reference

```bash
# 1. Edit version in pyproject.toml
vim pyproject.toml

# 2. Preview
python scripts/release.py --dry-run

# 3. Release
python scripts/release.py

# Done! ✅
```

## Architecture Notes

The release script:
- **Single source of truth**: Reads version from `pyproject.toml` only
- **Idempotent**: Safe to run multiple times (git operations may fail if already done, but that's OK)
- **Atomic**: Each step is independent, can resume if interrupted
- **Dry-run safe**: Use `--dry-run` to preview all changes

## Migration from Manual Process

Before this script, releases required:
1. ❌ Manually update version in 5+ files
2. ❌ Calculate SHA256 manually
3. ❌ Copy-paste SHA256 to Homebrew formula
4. ❌ Update Dockerfile paths
5. ❌ Build, tag, push Docker separately
6. ❌ Create GitHub release manually

Now:
1. ✅ Update version in `pyproject.toml`
2. ✅ Run `python scripts/release.py`

**Time saved:** ~15 minutes per release → ~30 seconds
