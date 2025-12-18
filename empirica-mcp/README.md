# Empirica MCP Server

**MCP (Model Context Protocol) server for Empirica epistemic framework**

## Installation

```bash
pip install empirica-mcp
```

## Usage

### As MCP Server

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp"
    }
  }
}
```

### Standalone

```bash
empirica-mcp
```

## Available Tools

The MCP server exposes all Empirica CLI commands as MCP tools:

- `session_create` - Create new session
- `preflight_submit` - Submit PREFLIGHT assessment
- `check` - Execute CHECK gate
- `postflight_submit` - Submit POSTFLIGHT assessment
- `goals_create` - Create goals
- `finding_log` - Log findings
- And 60+ more...

## Requirements

- Python 3.11+
- empirica>=1.0.0-beta
- mcp>=1.0.0

## Docker

```bash
docker pull empirica/mcp:latest
docker run -p 3000:3000 empirica/mcp
```

## Documentation

See main [Empirica documentation](https://github.com/empirical-ai/empirica/tree/main/docs) for details.

## License

Dual-licensed under LGPL-3.0-or-later OR MIT
