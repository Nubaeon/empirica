#!/bin/bash
# Wrapper script to start Empirica MCP server with clean library paths
# This prevents conflicts with Rovo Dev's bundled OpenSSL libraries

# Unset library paths that might cause conflicts
unset LD_LIBRARY_PATH
unset LD_PRELOAD

# Use the venv Python with clean environment
exec /path/to/empirica/.venv-mcp/bin/python3 \
  /path/to/empirica/mcp_local/empirica_mcp_server.py "$@"
