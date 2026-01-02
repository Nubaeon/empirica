# Empirica Docker Image
# Includes Python CLI, system prompts, and SKILL.md for AI agent usage
#
# Build: docker build -t empirica:1.2.3 .
# Run:   docker run -it --rm empirica:1.2.3 empirica --help
# Shell: docker run -it --rm empirica:1.2.3 /bin/bash

FROM python:3.11-slim

LABEL maintainer="Empirica Team"
LABEL description="Epistemic self-assessment framework for AI agents"
LABEL version="1.2.3"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY dist/empirica-1.2.3-py3-none-any.whl /tmp/

# Install Empirica
RUN pip install --no-cache-dir /tmp/empirica-1.2.3-py3-none-any.whl \
    && rm /tmp/empirica-1.2.3-py3-none-any.whl \
    && pip install --upgrade pip

# Create directory for user data
RUN mkdir -p /data/.empirica

# Copy documentation to accessible location
COPY docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md /app/docs/CANONICAL_SYSTEM_PROMPT.md
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
LABEL example.bootstrap="docker run -v $(pwd)/.empirica:/data/.empirica empirica:1.2.3 bootstrap --ai-id docker-agent --level extended"
LABEL example.session="docker run -v $(pwd)/.empirica:/data/.empirica empirica:1.2.3 sessions list"
LABEL example.shell="docker run -it -v $(pwd)/.empirica:/data/.empirica empirica:1.2.3 /bin/bash"
