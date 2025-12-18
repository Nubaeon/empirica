# Complete Empirica Installation Guide

This guide covers all installation methods and integration options for Empirica.

**Quick Navigation:**
- [Package Installation](#package-installation) (Python package via PyPI, Homebrew, Chocolatey, Docker)
- [System Prompt Installation](#system-prompt-installation) (For AI CLI tools like Claude Code, Gemini CLI)
- [MCP Server Installation](#mcp-server-installation) (For IDEs and AI interfaces)

---

## Package Installation

Choose your preferred package manager:

### Option 1: PyPI (Python Package Index)

**Requirements:** Python 3.11+

```bash
pip install empirica
empirica --version
empirica session-create --ai-id myagent --level extended
```

**Verify installation:**
```bash
empirica --help
python -c "from empirica.core.schemas.epistemic_assessment import EpistemicAssessment"
```

---

### Option 2: Homebrew (macOS/Linux)

```bash
# After Homebrew tap is published
brew tap empirica/tap
brew install empirica

# Verify
empirica session-create --help
```

**Or install directly from formula:**
```bash
brew install --build-from-source ./packaging/homebrew/empirica.rb
```

---

### Option 3: Chocolatey (Windows)

```powershell
# After Chocolatey package is published
choco install empirica

# Verify
empirica session-create --help
```

---

### Option 4: Docker

```bash
# Pull image (after publishing to Docker Hub)
docker pull soulentheo/empirica:latest

# Run CLI
docker run -it --rm soulentheo/empirica:latest bootstrap --help

# With persistent data
docker run -v $(pwd)/.empirica:/data/.empirica soulentheo/empirica:latest bootstrap --ai-id docker-agent
```

**Using Docker Compose:**
```bash
# Start MCP server
docker-compose up -d mcp-server

# Run CLI commands
docker-compose run cli bootstrap --ai-id myagent
```

---

### Option 5: From Source (Development)

```bash
git clone https://github.com/nubaeon/empirica.git
cd empirica
pip install -e .
empirica session-create --ai-id dev-agent
```

---

## System Prompt Installation

Install Empirica system prompts for AI CLI tools. This configures the AI agent to use Empirica methodology.

### Platform 1: Claude Code (formerly Claude Dev)

**Location:** `.clinerules` in project root

```bash
# Option A: Automated
empirica install-prompt claude-code --project-dir /path/to/your/project

# Option B: Manual
cat docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md >> /path/to/project/.clinerules
```

**Verify:**
```bash
cat .clinerules | grep "EMPIRICA AGENT"
```

---

### Platform 2: Google Gemini Code Assist

**Location:** `.gemini/system_instructions.md`

```bash
mkdir -p .gemini
cp docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md .gemini/system_instructions.md
```

---

### Platform 3: Roo Cline

**Location:** `.clinerules`

```bash
cp docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md .clinerules
```

---

### Platform 4: Cursor

**Location:** `.cursorrules`

```bash
cp docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md .cursorrules
```

---

### Platform 5: Windsurf (Codeium)

**Location:** `.windsurfrules`

```bash
cp docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md .windsurfrules
```

---

### Generic Installation (Any Platform)

If your AI CLI tool supports custom system prompts:

1. Locate the system prompt configuration file (often `.clinerules`, `.ai-rules`, or similar)
2. Copy or append `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md`
3. Restart the AI tool

**Template command:**
```bash
cp docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md /path/to/your/.ai-config-file
```

---

## MCP Server Installation

Install the Empirica MCP (Model Context Protocol) server for IDE integration.

### Supported Platforms

- Claude Desktop
- Claude Code (VS Code extension)
- Cline (VS Code extension)
- Continue.dev
- Zed Editor
- IDX (Google)
- Cursor
- Windsurf
- Goose (Block)

---

### Configuration File Locations

Each platform requires a specific configuration file:

| Platform | Config File Location |
|----------|---------------------|
| **Claude Desktop** | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)<br>`%APPDATA%/Claude/claude_desktop_config.json` (Windows)<br>`~/.config/Claude/claude_desktop_config.json` (Linux) |
| **Claude Code (VS Code)** | `.vscode/settings.json` or workspace settings |
| **Cline** | `.vscode/settings.json` under `cline.mcpServers` |
| **Continue.dev** | `~/.continue/config.json` |
| **Zed Editor** | `~/.config/zed/settings.json` |
| **IDX (Google)** | `.idx/mcp_settings.json` |
| **Cursor** | MCP support via Continue.dev integration |
| **Windsurf** | `~/.codeium/windsurf/mcp_settings.json` |
| **Goose (Block)** | `~/.config/goose/config.yaml` |

---

### Installation Steps

#### 1. Install Empirica Package

```bash
pip install empirica
```

#### 2. Locate Your Platform's Config File

See table above for your platform's configuration file location.

#### 3. Add MCP Server Configuration

Example for **Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "empirica": {
      "command": "python",
      "args": ["-m", "mcp_local.empirica_mcp_server"],
      "env": {
        "EMPIRICA_HOME": "${HOME}/.empirica"
      }
    }
  }
}
```

Example for **Continue.dev** (`~/.continue/config.json`):

```json
{
  "mcpServers": [
    {
      "name": "empirica",
      "command": "python",
      "args": ["-m", "mcp_local.empirica_mcp_server"],
      "env": {
        "EMPIRICA_HOME": "${HOME}/.empirica"
      }
    }
  ]
}
```

#### 4. Restart Your IDE/Tool

After adding the configuration, restart the IDE or AI tool to load the MCP server.

#### 5. Verify MCP Server

Check if Empirica tools are available:
- Claude Desktop: Look for Empirica tools in the tool picker
- Continue.dev: Check MCP status in Continue panel
- VS Code extensions: Check the MCP server status indicator

---

### Troubleshooting MCP Installation

**MCP server not starting:**
```bash
# Test manually
python -m mcp_local.empirica_mcp_server

# Check if empirica is installed
pip show empirica

# Check Python path
which python
```

**Permission errors:**
```bash
# Ensure EMPIRICA_HOME directory exists
mkdir -p ~/.empirica
chmod 755 ~/.empirica
```

**IDE not detecting MCP server:**
- Restart the IDE completely
- Check IDE logs for MCP connection errors
- Verify JSON syntax in config file
- Ensure Python path is correct in config

---

## Advanced Configuration

### Custom Database Location

```bash
export EMPIRICA_HOME=/custom/path/.empirica
empirica session-create --ai-id myagent
```

### Multi-Profile Setup

```bash
# Development profile
empirica session-create --ai-id dev-agent --profile development

# Production profile  
empirica session-create --ai-id prod-agent --profile production
```

### Integration with Git

Empirica automatically uses git for checkpoints and handoff reports:

```bash
cd your-project
git init
empirica session-create --ai-id myagent
# Checkpoints are stored in git notes
```

---

## Verification Checklist

After installation, verify everything works:

- [ ] CLI responds: `empirica --version`
- [ ] Bootstrap works: `empirica session-create --ai-id test --level minimal`
- [ ] Database created: `ls ~/.empirica/sessions.db`
- [ ] System prompt loaded (if applicable): Check `.clinerules` or equivalent
- [ ] MCP server connects (if applicable): Check IDE tool picker
- [ ] Git integration works: `empirica goals list`

---

## Next Steps

1. **Quick Start:** Run `empirica session-create --ai-id myagent --level extended`
2. **Read Methodology:** See `docs/production/00_DOCUMENTATION_MAP.md`
3. **Try CASCADE Workflow:** See `docs/production/03_BASIC_USAGE.md`
4. **Join Community:** (Add community links when available)

---

## Getting Help

- **Documentation:** `docs/production/`
- **Troubleshooting:** `docs/06_TROUBLESHOOTING.md`
- **Issues:** GitHub Issues
- **Questions:** (Add discussion forum link)

---

**Installation complete!** 🎉 Start your first session:

```bash
empirica session-create --ai-id myagent --level extended
empirica goals create --objective "Learn Empirica" --scope project_wide
```
