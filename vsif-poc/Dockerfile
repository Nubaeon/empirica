FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /vsif-poc

# Copy scripts
COPY scripts/ /vsif-poc/scripts/
COPY canaries/ /vsif-poc/canaries/

# Create evidence directory
RUN mkdir -p /evidence

# Set permissions
RUN chmod +x /vsif-poc/scripts/*.py

# Default command
CMD ["/bin/bash"]
