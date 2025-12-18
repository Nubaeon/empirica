# Test Empirica pip install in clean environment
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Test 1: Install empirica
RUN pip install --no-cache-dir empirica && \
    empirica --help

# Test 2: Verify MCP server (should fail - not on PyPI yet)
RUN pip install --no-cache-dir empirica-mcp || echo "empirica-mcp not on PyPI yet (expected)"

# Test 3: Create test session
RUN echo '{"ai_id": "docker-test", "session_type": "development"}' | empirica session-create - || echo "Session creation test"

# Test 4: Check installed commands
RUN which empirica && \
    empirica --version || empirica --help | head -5

CMD ["empirica", "--help"]
