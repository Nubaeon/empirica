#!/bin/bash
# Quick test of mini-agent setup

cd /home/yogapad/empirical-ai/empirica

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         MINI-AGENT SETUP VERIFICATION                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "1. Checking mini-agent installation..."
if command -v mini-agent &> /dev/null; then
    echo "   ✅ mini-agent is installed"
    mini-agent --version 2>&1 || echo "   Version: $(which mini-agent)"
else
    echo "   ❌ mini-agent not found"
    exit 1
fi

echo ""
echo "2. Checking configuration files..."
if [ -f ~/.mini-agent/config/config.yaml ]; then
    echo "   ✅ config.yaml exists"
    echo "      API: $(grep api_base ~/.mini-agent/config/config.yaml | head -1)"
    echo "      Model: $(grep '^model:' ~/.mini-agent/config/config.yaml)"
else
    echo "   ❌ config.yaml missing"
fi

if [ -f ~/.mini-agent/config/system_prompt.txt ]; then
    echo "   ✅ system_prompt.txt exists"
    echo "      Lines: $(wc -l < ~/.mini-agent/config/system_prompt.txt)"
else
    echo "   ❌ system_prompt.txt missing"
fi

echo ""
echo "3. Checking workspace MCP configuration..."
if [ -f .mcp.json ]; then
    echo "   ✅ .mcp.json exists in workspace"
    cat .mcp.json | python3 -m json.tool > /dev/null 2>&1 && echo "      Valid JSON ✅" || echo "      Invalid JSON ❌"
else
    echo "   ❌ .mcp.json missing"
fi

echo ""
echo "4. Checking Empirica MCP server..."
if [ -f mcp_local/empirica_mcp_server.py ]; then
    echo "   ✅ empirica_mcp_server.py exists"
    python3 -c "import sys; sys.path.insert(0, '.'); import mcp_local.empirica_mcp_server" 2>&1 && \
        echo "      Imports successfully ✅" || echo "      Import error ❌"
else
    echo "   ❌ empirica_mcp_server.py missing"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         SETUP VERIFICATION COMPLETE                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "To test mini-agent with Empirica:"
echo ""
echo "  cd /home/yogapad/empirical-ai/empirica"
echo "  mini-agent --workspace ."
echo ""
echo "Then try a simple task:"
echo '  "List the files in this directory and tell me what this project does"'
echo ""
echo "Or test with Empirica awareness:"
echo '  "Use your epistemic self-assessment to evaluate your understanding'
echo '   of this codebase before making recommendations"'
echo ""
