# Empirica Docker Image
# Includes Python CLI, system prompts, and SKILL.md for AI agent usage
#
# Build: docker build -t empirica:1.4.2 .
# Run:   docker run -it --rm empirica:1.4.2 empirica --help
# Shell: docker run -it --rm empirica:1.4.2 /bin/bash
#
# For security-hardened Alpine version: docker build -f Dockerfile.alpine -t empirica:1.4.2-alpine .

FROM python:3.11-slim-bookworm

LABEL maintainer="Empirica Team"
LABEL description="Epistemic self-assessment framework for AI agents"
LABEL version="1.4.2"

# Set working directory
WORKDIR /app

# Install system dependencies with version pinning
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Upgrade pip and setuptools first (CVE-2025-47273, CVE-2024-6345)
RUN pip install --no-cache-dir --upgrade pip setuptools

# Copy package files
COPY dist/empirica-1.4.2-py3-none-any.whl /tmp/

# Install Empirica with security flags
RUN pip install --no-cache-dir --no-compile /tmp/empirica-1.4.2-py3-none-any.whl \
    && rm /tmp/empirica-1.4.2-py3-none-any.whl \
    && pip cache purge 2>/dev/null || true

# Create directory for user data
RUN mkdir -p /data/.empirica

# Copy documentation to accessible location (if exists)
COPY README.md /app/README.md

# Set environment variables
ENV EMPIRICA_HOME=/data/.empirica
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 1000 empirica && \
    chown -R empirica:empirica /app /data

USER empirica

# Set volume for persistent data
VOLUME ["/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD empirica --version || exit 1

# Default command
CMD ["empirica", "--help"]

# Usage examples (add as labels for documentation)
LABEL example.bootstrap="docker run -v $(pwd)/.empirica:/data/.empirica empirica:1.4.2 bootstrap --ai-id docker-agent --level extended"
LABEL example.session="docker run -v $(pwd)/.empirica:/data/.empirica empirica:1.4.2 sessions list"
LABEL example.shell="docker run -it -v $(pwd)/.empirica:/data/.empirica empirica:1.4.2 /bin/bash"
