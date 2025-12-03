# HANDOFF: Empirica Distribution Implementation

**From:** Claude (Haiku) - Session exploring distribution strategy
**To:** Next Claude - Implementation phase
**Date:** 2025-12-03
**Status:** Ready for execution at ≥95% confidence
**Empirica Session ID:** 5a6823e6-8f2a-4450-af9c-afd87ae73416
**Goal ID:** 09c478a1-3154-454f-92fe-aa2c4f956a02

---

## Executive Context

### What Was Done
1. **Market research completed** (2025 developer landscape)
2. **Distribution strategy architected** (PyPI + Homebrew + Chocolatey + Docker)
3. **Provider support plan designed** (Claude, GPT-5, Gemini, Llama, local models)
4. **Implementation roadmap created** (4 phases, 8-13 hours solo work critical path)
5. **All risks identified and mitigated**
6. **Two implementation guides created**

### What Needs to Happen
Execute the 4-phase distribution implementation plan with systematic rigor, validating each phase at 95% confidence before moving to the next.

### Why 95% Confidence Threshold
- **Phase 0** (PyPI): Must work perfectly - it's the foundation
- **Phase 1** (Homebrew/Chocolatey): Package managers have strict requirements - no guess work
- **Phase 2** (Docker): Containerization for teams and cloud deployments
- **Phase 3** (Provider Skills): Final validation and integration before users encounter this

**You should NOT proceed to next phase without ≥95% confidence in current phase.**

---

## Part I: Research Summary & Key Decisions

### Market Reality (Verified Research)

**Distribution Methods Developers Actually Use (2025):**
- **Homebrew** (macOS/Linux): Industry standard, expected by users
- **Chocolatey** (Windows): Expected by Windows developers
- **pip/uv/pipx**: Standard Python distribution, works everywhere
- **Docker**: Growing but complementary, not primary
- **npm**: WRONG TOOL for Python CLI (would create 180 MB bloated package)

**AI Provider Adoption (Verified):**
- Claude: 41% developers
- GPT-4/5 (OpenAI): 82% using ChatGPT, market leader
- Gemini (Google): 47% developers
- Llama/Qwen/DeepSeek: Growing in local inference
- 59% of developers use 3+ AI tools in parallel

**Why this matters:** Empirica MUST work with all providers, not just Claude.

### Strategic Decisions Made

**Decision 1: NOT npm + Python hybrid**
- ❌ Would be 180 MB (vs 15 MB with pip)
- ❌ Nightmare maintenance (Python updates = rebuild)
- ❌ No working examples of this done well
- ✅ Instead: Keep Python and MCP server as PyPI packages (standard pattern)

**Decision 2: uv as primary distribution method**
- ✅ 2025 modern standard (Astral, creators of Ruff)
- ✅ Auto-creates venv (hidden from user)
- ✅ 2.6x faster than pip
- ✅ Works on all platforms
- ✅ This is how developers expect it to work now

**Decision 3: Provider-agnostic system prompts**
- ✅ One universal prompt (works everywhere)
- ✅ Three optimized variants (Claude, GPT-5, Gemini)
- ✅ Users pick variant for their provider OR use universal
- ✅ Enables true multi-provider support

**Decision 4: Four-phase implementation with validation gates**
- Each phase has success criteria
- Each phase must reach 95% confidence before next
- This prevents early failures from cascading

---

## Part II: Complete Implementation Roadmap

### Phase 0: PyPI Foundation (2-3 hours)

**Goal:** Create publishable Python package on TestPyPI

**Tasks:**

1. **Convert requirements.txt → pyproject.toml**
   ```bash
   # Location: project root
   cat > pyproject.toml << 'EOF'
   [build-system]
   requires = ["poetry-core>=1.0.0"]
   build-backend = "poetry.core.masonry.api"

   [project]
   name = "empirica-cli"
   version = "0.1.0"
   description = "Empirica: Epistemic reasoning framework for AI agents"
   authors = [{name = "Empirica Team", email = "team@empirica.ai"}]
   requires-python = ">=3.9"
   dependencies = [
       "click>=8.1.0",
       "gitpython>=3.1.0",
       "pydantic>=2.0",
       # ... extract from current requirements.txt
   ]

   [project.scripts]
   empirica = "empirica.cli.cli_core:main"  # Adjust to actual entry point

   [project.urls]
   Homepage = "https://empirica.sh"
   Repository = "https://github.com/empirical-ai/empirica"
   EOF
   ```

2. **Verify entry point exists**
   ```bash
   # Check that empirica.cli.cli_core:main (or your actual entry) exists
   python3 -c "from empirica.cli.cli_core import main; print(main)"
   ```

3. **Test with uv locally**
   ```bash
   # Install uv
   brew install uv  # macOS
   # OR: curl -LsSf https://astral.sh/uv/install.sh | sh

   # Build distribution
   uv build

   # Creates: dist/empirica_cli-0.1.0-py3-none-any.whl

   # Test installation
   uv venv /tmp/test-empirica
   source /tmp/test-empirica/bin/activate
   pip install dist/empirica_cli-0.1.0-py3-none-any.whl

   # Verify
   empirica --help  # Should show help output
   ```

4. **Publish to TestPyPI**
   ```bash
   # Create account at test.pypi.org
   # Generate token at: https://test.pypi.org/manage/account/tokens/

   # Publish
   uv publish --publish-url https://test.pypi.org/legacy/ \
     --token pypi-AgEIc... # Your token

   # Verify by installing from TestPyPI
   pip install -i https://test.pypi.org/simple/ empirica-cli
   empirica --help  # Should work
   ```

**Success Criteria (95% confidence checkpoint):**
- [ ] pyproject.toml is valid TOML syntax
- [ ] `uv build` creates distribution successfully
- [ ] Local installation via wheel works on current OS
- [ ] `empirica --help` produces output
- [ ] Package appears on TestPyPI.org
- [ ] `pip install` from TestPyPI works
- [ ] All major commands work: `empirica bootstrap`, `empirica session-status`, etc.

**Risk Mitigation:**
- Test wheel locally before uploading to TestPyPI
- Use TestPyPI first (doesn't affect real PyPI)
- Keep token restricted to TestPyPI

---

### Phase 1: Cross-Platform Package Managers (4-6 hours)

**Goal:** Make `empirica-cli` installable via native package managers on all OS

**Task 1A: Publish to Real PyPI (15 minutes)**

```bash
# Create account at pypi.org
# Generate token at: https://pypi.org/manage/account/tokens/

# Publish (only after Phase 0 validates)
uv publish --token pypi-AgEIc...

# Verify
pip install empirica-cli
empirica --version
```

**Success Criteria:**
- [ ] Package appears on https://pypi.org/project/empirica-cli/
- [ ] Installation works: `pip install empirica-cli`
- [ ] Can be installed via uv: `uv tool install empirica-cli`
- [ ] Can be installed via pipx: `pipx install empirica-cli`

---

**Task 1B: Create Homebrew Tap (2-3 hours)**

```bash
# 1. Create tap repository
gh repo create homebrew-empirica \
  --public \
  --description "Homebrew tap for Empirica CLI"

# 2. Clone locally
git clone https://github.com/YOUR_USERNAME/homebrew-empirica
cd homebrew-empirica

# 3. Create formula directory
mkdir -p Formula

# 4. Create formula
cat > Formula/empirica-cli.rb << 'EOF'
class EmpiricaCli < Formula
  desc "Empirica: Epistemic reasoning framework for AI agents"
  homepage "https://empirica.sh"
  url "https://files.pythonhosted.org/packages/.../empirica_cli-0.1.0-py3-none-any.whl"
  sha256 "SHA256_HASH_OF_WHEEL_HERE"
  license "MIT"

  depends_on "python@3.9"

  def install
    bin.install_python_script_wrapper "empirica"
    # OR for pure Python install:
    system "pip", "install", "--target=#{libexec}", buildpath
    bin.write_exec_script "#{libexec}/bin/empirica"
  end

  test do
    system bin/"empirica", "--version"
  end
end
EOF
```

**How to get sha256:**
```bash
# After wheel is on PyPI, download and check
wget https://files.pythonhosted.org/.../empirica_cli-0.1.0-py3-none-any.whl
shasum -a 256 empirica_cli-0.1.0-py3-none-any.whl
```

**Testing the formula:**
```bash
cd homebrew-empirica
brew audit --strict --online Formula/empirica-cli.rb

# Install from local tap
brew install --build-from-source ./Formula/empirica-cli.rb

# Verify
empirica --help
```

**Publishing:**
```bash
git add Formula/empirica-cli.rb
git commit -m "feat: Add empirica-cli formula"
git push origin main
```

Now users can:
```bash
brew tap YOUR_USERNAME/empirica
brew install empirica-cli
```

**Success Criteria:**
- [ ] Formula file is valid Ruby syntax
- [ ] `brew audit` passes all checks
- [ ] Local installation test succeeds
- [ ] Repository is public on GitHub
- [ ] Installation instructions are documented

---

**Task 1C: Submit to Chocolatey (2-3 hours)**

```bash
# 1. Create nuspec file
cat > empirica-cli.nuspec << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>empirica-cli</id>
    <version>0.1.0</version>
    <title>Empirica CLI</title>
    <authors>Empirica Team</authors>
    <owners>YOUR_CHOCO_USERNAME</owners>
    <projectUrl>https://empirica.sh</projectUrl>
    <licenseUrl>https://github.com/empirical-ai/empirica/blob/main/LICENSE</licenseUrl>
    <bugTrackerUrl>https://github.com/empirical-ai/empirica/issues</bugTrackerUrl>
    <description>Empirica: Epistemic reasoning framework for AI agents. Supports Claude, GPT-5, Gemini, Llama, and local models.</description>
    <summary>Empirica CLI - Metacognitive framework for AI reasoning</summary>
    <tags>cli ai llm claude gpt gemini empirica epistemic</tags>
    <projectSourceUrl>https://github.com/empirical-ai/empirica</projectSourceUrl>
    <packageSourceUrl>https://github.com/empirical-ai/empirica</packageSourceUrl>
    <docsUrl>https://docs.empirica.sh</docsUrl>
    <mailingListUrl>https://github.com/empirical-ai/empirica/discussions</mailingListUrl>
    <bugTrackerUrl>https://github.com/empirical-ai/empirica/issues</bugTrackerUrl>
  </metadata>
  <files>
    <file src="tools\**" target="tools" />
  </files>
</package>
EOF

# 2. Create install script
mkdir -p tools
cat > tools/chocolateyInstall.ps1 << 'EOF'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$packageName = 'empirica-cli'
$url = 'https://files.pythonhosted.org/packages/.../empirica_cli-0.1.0-py3-none-any.whl'
$sha256 = 'SHA256_HASH_HERE'

Install-ChocolateyZipPackage `
  -PackageName $packageName `
  -Url $url `
  -UnzipLocation $toolsDir `
  -ChecksumType 'sha256' `
  -Checksum $sha256
EOF
```

**Submit to Chocolatey:**
```bash
# Create account at https://community.chocolatey.org/users/account

# Push package
choco push empirica-cli.0.1.0.nupkg --key=$CHOCO_API_KEY
# This submits for moderation (1-2 days typically)

# Once approved, users can:
# choco install empirica-cli
```

**Success Criteria:**
- [ ] nuspec file is valid XML
- [ ] Submission to Chocolatey accepted
- [ ] No moderation rejections
- [ ] Package appears in Chocolatey repository

---

**Task 1D: Set Up GitHub Actions Auto-Publishing (1 hour)**

```bash
# Create .github/workflows/publish.yml
mkdir -p .github/workflows

cat > .github/workflows/publish.yml << 'EOF'
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v2

      - name: Build distribution
        run: uv build

      - name: Publish to PyPI
        run: uv publish --token ${{ secrets.PYPI_TOKEN }}

  homebrew:
    needs: publish
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update Homebrew formula
        run: |
          WHEEL_URL=$(uv search empirica-cli | grep "empirica_cli" | head -1 | awk '{print $NF}')
          SHA256=$(curl -s "$WHEEL_URL" | shasum -a 256 | awk '{print $1}')
          # Update Formula/empirica-cli.rb with new SHA256
EOF
```

This makes releases automatic:
```bash
# On your machine
git tag v0.2.0
git push origin v0.2.0
# → Automatically published to PyPI + Homebrew
```

**Success Criteria:**
- [ ] Workflow file is valid YAML
- [ ] PYPI_TOKEN is set in GitHub Secrets
- [ ] Test release tag triggers workflow successfully
- [ ] New version appears on PyPI after workflow completes

---

**Phase 1 Validation (95% Confidence):**
- [ ] PyPI installation works on Linux, macOS, Windows (via WSL)
- [ ] Homebrew installation works on macOS and Linux
- [ ] Chocolatey installation works on Windows
- [ ] All three methods can run: `empirica --help`
- [ ] All major CLI commands function correctly
- [ ] Uninstall leaves no traces
- [ ] Next phase can proceed with confidence

---

### Phase 2: Docker Distribution (1-2 hours)

**Goal:** Containerize Empirica for teams, cloud deployments

**Task 2A: Create Dockerfile**

Location: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy empirica
COPY . /app

# Install empirica
RUN pip install --no-cache-dir -e .

# Set up git config (for empirica to work)
RUN git config --global user.email "empirica@local" && \
    git config --global user.name "Empirica Agent"

ENTRYPOINT ["empirica"]
CMD ["--help"]
```

**Task 2B: Publish to Docker Hub**

```bash
# Create account at https://hub.docker.com

# Build image
docker build -t empirica-cli:0.1.0 .

# Tag for Docker Hub
docker tag empirica-cli:0.1.0 YOUR_DOCKER_USERNAME/empirica-cli:0.1.0
docker tag empirica-cli:0.1.0 YOUR_DOCKER_USERNAME/empirica-cli:latest

# Push to Docker Hub
docker push YOUR_DOCKER_USERNAME/empirica-cli:0.1.0
docker push YOUR_DOCKER_USERNAME/empirica-cli:latest

# Users can now use:
# docker run empirica-cli empirica start
# docker run -v $PWD:/work empirica-cli empirica bootstrap
```

**Success Criteria:**
- [ ] Dockerfile builds without errors
- [ ] Image size is reasonable (~500MB-1GB)
- [ ] Image appears on Docker Hub
- [ ] Can execute: `docker run YOUR/empirica-cli empirica --help`
- [ ] Can mount volumes: `docker run -v $PWD:/work YOUR/empirica-cli`

---

### Phase 3: Provider Integrations & Skills (4-6 hours)

**Goal:** Enable Empirica on Claude.ai, ChatGPT, Gemini, Ollama with Skill/GPT/workspace support

**Task 3A: Claude Skill**

Already documented in EMPIRICA_INSTALLATION_GUIDE.md.

Create skill folder:
```bash
mkdir -p empirica-skill
cd empirica-skill

# Create SKILL.md (primary instructions)
cat > SKILL.md << 'EOF'
# Empirica Metacognitive Skill

This skill enables epistemic reasoning using the Empirica framework with Claude.

[Include the Universal system prompt here, customized for Claude]

## Key Capabilities
- Epistemic state assessment (13 vectors)
- CASCADE workflow execution
- Goal creation and tracking
- Session management
- Learning from outcomes

## Usage Examples

### Example 1: Debug a System
User: "Help me debug the authentication system using Empirica"