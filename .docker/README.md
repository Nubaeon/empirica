# Empirica - Epistemic Self-Assessment Framework for AI Agents

**Docker Hub:** https://hub.docker.com/r/nubaeon/empirica  
**GitHub:** https://github.com/Nubaeon/empirica  
**PyPI:** https://pypi.org/project/empirica/

## What is Empirica?

Empirica enables AI agents to genuinely assess their knowledge and uncertainty. Instead of false confidence and hallucinations, Empirica provides honest uncertainty tracking, focused investigation, and genuine learning measurement.

**Key Features:**
- 🎯 CASCADE workflow (PREFLIGHT → CHECK → POSTFLIGHT)
- 📊 13-vector epistemic state tracking
- 💾 97.5% token reduction via checkpoint loading
- 🔄 Multi-AI coordination with epistemic handoffs
- 🐙 Git-integrated session management
- 🧠 Genuine metacognitive awareness

## Quick Start

### Pull the Image

```bash
docker pull nubaeon/empirica:1.0.0
# Or use :latest for the latest stable version
docker pull nubaeon/empirica:latest
```

### Run Commands

```bash
# Get help
docker run --rm nubaeon/empirica:1.0.0 empirica --help

# Check version
docker run --rm nubaeon/empirica:1.0.0 empirica --version

# Create a session
docker run --rm nubaeon/empirica:1.0.0 empirica session-create --ai-id docker-agent --output json
```

### Interactive Shell with Persistent Data

```bash
# Run with volume mount for persistent data
docker run -it -v $(pwd)/.empirica:/data/.empirica nubaeon/empirica:1.0.0 /bin/bash

# Inside the container:
empirica session-create --ai-id myagent
empirica preflight-submit preflight.json
# ... your work ...
empirica postflight-submit postflight.json
```

### Example: Complete Workflow

```bash
# 1. Start interactive session
docker run -it -v $(pwd)/.empirica:/data/.empirica nubaeon/empirica:1.0.0 /bin/bash

# 2. Inside container - create session
SESSION_ID=$(empirica session-create --ai-id docker-agent --output json | jq -r '.session_id')

# 3. Submit PREFLIGHT
cat > /tmp/preflight.json << PREFLIGHT
{
  "session_id": "$SESSION_ID",
  "vectors": {
    "engagement": 0.85,
    "foundation": {"know": 0.70, "do": 0.80, "context": 0.60},
    "comprehension": {"clarity": 0.75, "coherence": 0.70, "signal": 0.80, "density": 0.45},
    "execution": {"state": 0.40, "change": 0.60, "completion": 0.30, "impact": 0.70},
    "uncertainty": 0.55
  },
  "reasoning": "Starting Docker-based task"
}
PREFLIGHT

empirica preflight-submit /tmp/preflight.json

# 4. Do your work...

# 5. Submit POSTFLIGHT
cat > /tmp/postflight.json << POSTFLIGHT
{
  "session_id": "$SESSION_ID",
  "vectors": {
    "engagement": 0.85,
    "foundation": {"know": 0.90, "do": 0.85, "context": 0.80},
    "comprehension": {"clarity": 0.90, "coherence": 0.85, "signal": 0.85, "density": 0.50},
    "execution": {"state": 0.90, "change": 0.85, "completion": 0.95, "impact": 0.85},
    "uncertainty": 0.25
  },
  "reasoning": "Task complete. Learned X, Y, Z"
}
POSTFLIGHT

empirica postflight-submit /tmp/postflight.json
```

## Image Tags

- `1.0.0` - Stable release v1.0.0
- `latest` - Latest stable release
- `develop` - Development branch (bleeding edge)

## Environment Variables

- `EMPIRICA_HOME` - Default: `/data/.empirica` - Location for session data
- `PYTHONUNBUFFERED` - Set to `1` for real-time output

## Volumes

Mount `/data` to persist session data between runs:

```bash
docker run -v /path/to/your/data:/data nubaeon/empirica:1.0.0
```

## Image Details

- **Base Image:** `python:3.11-slim`
- **Size:** ~200MB
- **Python Version:** 3.11
- **Includes:** Git, Empirica CLI, all dependencies
- **User:** Non-root user `empirica` (UID 1000)

## Health Check

The image includes a health check that runs `empirica --version`:

```bash
docker inspect nubaeon/empirica:1.0.0 | jq '.[0].Config.Healthcheck'
```

## Use Cases

### CI/CD Integration

```yaml
# .github/workflows/empirica-session.yml
jobs:
  epistemic-test:
    runs-on: ubuntu-latest
    container:
      image: nubaeon/empirica:1.0.0
    steps:
      - name: Run Empirica Session
        run: |
          empirica session-create --ai-id ci-bot
          # ... your CI workflow ...
```

### MCP Server (Model Context Protocol)

```bash
# Run MCP server in Docker
docker run -p 8080:8080 nubaeon/empirica:1.0.0 \
  python -m mcp_local.empirica_mcp_server
```

### Development Environment

```bash
# Use as development environment
docker run -it \
  -v $(pwd):/workspace \
  -v $(pwd)/.empirica:/data/.empirica \
  -w /workspace \
  nubaeon/empirica:1.0.0 \
  /bin/bash
```

## Documentation

- **Installation Guide:** https://github.com/Nubaeon/empirica/blob/main/docs/production/02_INSTALLATION.md
- **Quick Start:** https://github.com/Nubaeon/empirica/blob/main/docs/production/03_BASIC_USAGE.md
- **CASCADE Workflow:** https://github.com/Nubaeon/empirica/blob/main/docs/production/06_CASCADE_FLOW.md
- **Full Docs:** https://github.com/Nubaeon/empirica/tree/main/docs

## Links

- **GitHub Repository:** https://github.com/Nubaeon/empirica
- **PyPI Package:** https://pypi.org/project/empirica/
- **Issues:** https://github.com/Nubaeon/empirica/issues
- **License:** MIT

## Building from Source

```bash
# Clone the repository
git clone https://github.com/Nubaeon/empirica.git
cd empirica

# Build the image
docker build -t empirica:custom .

# Run your custom build
docker run -it empirica:custom empirica --help
```

## Support

- GitHub Issues: https://github.com/Nubaeon/empirica/issues
- Documentation: https://github.com/Nubaeon/empirica/tree/main/docs

---

**License:** MIT  
**Maintainer:** Empirica Team  
**Version:** 1.0.0
