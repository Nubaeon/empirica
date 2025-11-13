# 15. Configuration Guide

**Version:** 2.0  
**Date:** 2025-10-29  
**Status:** Production Ready

---

## Overview

Empirica provides extensive configuration options for customizing behavior, output locations, thresholds, and component activation. This guide covers all configuration mechanisms from environment variables to bootstrap levels.

---

## Configuration Hierarchy

Configuration is loaded in this order (later overrides earlier):

1. **Built-in Defaults** - Hardcoded fallbacks
2. **Environment Variables** - `.env` file or shell exports
3. **Config Files** - `config.yaml` or `.empirica/config.yaml`
4. **CLI Arguments** - Command-line flags (highest priority)

---

## Environment Variables

### Core Settings

```bash
# AI Identity
EMPIRICA_AI_ID="claude_copilot"              # Unique AI identifier

# Data Locations
EMPIRICA_DB_PATH=".empirica/${AI_ID}/empirica.db"     # SQLite database
EMPIRICA_SESSION_PATH=".empirica/${AI_ID}/sessions/"  # JSON sessions
EMPIRICA_REFLEX_PATH=".empirica_reflex_logs/${AI_ID}/" # Reflex frames

# Logging
EMPIRICA_LOG_LEVEL="INFO"                     # DEBUG|INFO|WARNING|ERROR
EMPIRICA_VERBOSE="false"                      # Enable verbose output
EMPIRICA_QUIET="false"                        # Suppress non-critical output

# Auto-Tracking
EMPIRICA_AUTO_TRACK="true"                    # Enable automatic tracking
EMPIRICA_TRACK_TO_DB="true"                   # Write to SQLite
EMPIRICA_TRACK_TO_JSON="true"                 # Write to JSON sessions
EMPIRICA_TRACK_TO_REFLEX="true"               # Write reflex frames
```

### Assessment Configuration

```bash
# LLM Settings
EMPIRICA_LLM_PROVIDER="openai"                # openai|anthropic|local
EMPIRICA_LLM_MODEL="gpt-4"                    # Model for assessments
EMPIRICA_LLM_TEMPERATURE="0.1"                # Low temp for consistency
EMPIRICA_LLM_MAX_TOKENS="2000"                # Token limit per assessment

# Assessment Behavior
EMPIRICA_ASSESSMENT_TIMEOUT="30"              # Seconds before timeout
EMPIRICA_RETRY_ON_FAILURE="3"                 # Retry attempts
EMPIRICA_CACHE_ASSESSMENTS="false"            # Cache identical prompts
```

### Threshold Settings

```bash
# Canonical Weights (must sum to 100)
EMPIRICA_WEIGHT_CONFIDENCE="35"               # Confidence weight
EMPIRICA_WEIGHT_COHERENCE="25"                # Coherence weight
EMPIRICA_WEIGHT_NECESSITY="25"                # Necessity weight
EMPIRICA_WEIGHT_ENGAGEMENT="15"               # Engagement weight

# Investigation Triggers
EMPIRICA_INVESTIGATION_THRESHOLD="0.65"       # Weighted score threshold
EMPIRICA_UNCERTAINTY_THRESHOLD="0.6"          # Raw uncertainty threshold
EMPIRICA_DELTA_UNCERTAINTY_MIN="-0.2"         # Minimum learning delta

# Bayesian Guardian
EMPIRICA_BAYESIAN_PRIOR="0.5"                 # Default prior belief
EMPIRICA_EVIDENCE_STRENGTH="moderate"         # weak|moderate|strong
```

### Component Activation

```bash
# Enterprise Components (true/false)
EMPIRICA_ENABLE_CODE_INTELLIGENCE="true"
EMPIRICA_ENABLE_CONTEXT_VALIDATION="true"
EMPIRICA_ENABLE_PERFORMANCE_ANALYZER="true"
EMPIRICA_ENABLE_ENVIRONMENT_STABILIZATION="true"
EMPIRICA_ENABLE_GOAL_MANAGEMENT="true"
EMPIRICA_ENABLE_INTELLIGENT_NAVIGATION="true"
EMPIRICA_ENABLE_PROCEDURAL_ANALYSIS="true"
EMPIRICA_ENABLE_RUNTIME_VALIDATION="true"
EMPIRICA_ENABLE_SECURITY_MONITORING="true"
EMPIRICA_ENABLE_TOOL_MANAGEMENT="true"
EMPIRICA_ENABLE_WORKSPACE_AWARENESS="true"

# Core Components
EMPIRICA_ENABLE_BAYESIAN_GUARDIAN="true"
EMPIRICA_ENABLE_DRIFT_MONITOR="true"
EMPIRICA_ENABLE_REFLEX_LOGGER="true"
```

---

## Configuration Files

### `.env` File Example

```bash
# .env - Place in project root or ~/.empirica/.env
EMPIRICA_AI_ID=my_ai_agent
EMPIRICA_LOG_LEVEL=DEBUG
EMPIRICA_AUTO_TRACK=true
EMPIRICA_WEIGHT_CONFIDENCE=40
EMPIRICA_WEIGHT_COHERENCE=30
EMPIRICA_WEIGHT_NECESSITY=20
EMPIRICA_WEIGHT_ENGAGEMENT=10
```

### `config.yaml` Example

```yaml
# config.yaml - Advanced configuration
ai:
  id: "claude_copilot"
  name: "Claude Copilot CLI"
  version: "2.0"

paths:
  database: ".empirica/{ai_id}/empirica.db"
  sessions: ".empirica/{ai_id}/sessions/"
  reflex_logs: ".empirica_reflex_logs/{ai_id}/"
  cache: ".empirica/{ai_id}/cache/"

assessment:
  llm:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.1
    max_tokens: 2000
  
  weights:
    confidence: 35
    coherence: 25
    necessity: 25
    engagement: 15
  
  thresholds:
    investigation: 0.65
    uncertainty: 0.6
    delta_uncertainty_min: -0.2

components:
  enterprise:
    code_intelligence: true
    context_validation: true
    performance_analyzer: true
    environment_stabilization: true
    goal_management: true
    intelligent_navigation: true
    procedural_analysis: true
    runtime_validation: true
    security_monitoring: true
    tool_management: true
    workspace_awareness: true
  
  core:
    bayesian_guardian: true
    drift_monitor: true
    reflex_logger: true
    auto_tracker: true

logging:
  level: "INFO"
  verbose: false
  quiet: false
  formats:
    - "sqlite"
    - "json"
    - "reflex"

performance:
  max_cascade_depth: 5
  cascade_timeout: 300
  assessment_cache_ttl: 3600
  parallel_assessments: false
```

---

## Bootstrap Levels

Different bootstrap configurations for various use cases:

### Minimal Bootstrap

```bash
empirica bootstrap --level minimal
```

**Activates:**
- Core cascade only
- No auto-tracking
- No enterprise components
- Lightweight for testing

### Standard Bootstrap (Default)

```bash
empirica bootstrap --level standard
```

**Activates:**
- Core cascade
- Auto-tracking (all 3 formats)
- Essential components (Bayesian Guardian, Drift Monitor)
- Reflex logging

### Extended Bootstrap

```bash
empirica bootstrap --level extended
```

**Activates:**
- Everything in standard
- All 11 enterprise components
- Full investigation system
- Performance monitoring

### Complete Bootstrap

```bash
empirica bootstrap --level complete
```

**Activates:**
- Everything in extended
- Cognitive benchmarking
- Tmux dashboard
- Advanced analytics
- All experimental features

---

## Investigation Profiles (NEW in v2.0)

### Overview

Investigation profiles configure how Empirica adapts investigation behavior to different AI capabilities and domain requirements.

### Built-In Profiles

**high_reasoning** - For advanced AI models (Claude Opus, GPT-4)
```bash
empirica bootstrap --profile high_reasoning
# - Unlimited investigation cycles
# - Dynamic thresholds
# - Trust AI judgment
```

**autonomous** - For autonomous agents (Minimax, AutoGPT)
```bash
empirica bootstrap --profile autonomous
# - 5 investigation cycles max
# - Structured guidance
# - Explicit checkpoints
```

**critical** - For high-stakes domains (healthcare, finance, legal)
```bash
empirica bootstrap --profile critical
# - 10 investigation cycles
# - Mandatory investigation
# - Audit trail required
```

**exploratory** - For research and discovery
```bash
empirica bootstrap --profile exploratory
# - 7 investigation cycles
# - Encourages investigation
# - Tracks epistemic growth
```

**balanced** - Default general-purpose profile
```bash
empirica bootstrap  # Uses balanced by default
# - 4 investigation cycles
# - Moderate constraints
# - Sensible defaults
```

### Profile Management Commands

```bash
# List available profiles
empirica profile-list

# Show profile details
empirica profile-show high_reasoning

# Create custom profile
empirica profile-create my-profile \
  --ai-model custom-model \
  --domain custom-domain

# Set default profile
empirica profile-set-default high_reasoning
```

### Profile Selection

**Automatic:**
- AI model detected → Appropriate profile selected
- Domain specified → Domain-appropriate profile selected
- Neither specified → Uses `balanced` profile

**Manual Override:**
```bash
empirica bootstrap --profile critical --ai-model gpt-3.5
# Uses critical (not balanced) because explicitly set
```

### Custom Profiles

**Create profile file:** `~/.empirica/profiles/my-profile.yaml`

```yaml
name: my-profile
description: Custom profile for my use case
investigation:
  max_cycles: 6
  uncertainty_threshold: 0.35
  required_when:
    - uncertainty > 0.65
capabilities:
  reasoning: high
  self_awareness: high
  investigation: supported
```

**Use custom profile:**
```bash
empirica bootstrap --profile my-profile
```

**For comprehensive guide:** See `docs/guides/PROFILE_MANAGEMENT.md`

---

## CLI Configuration

### Global CLI Options

```bash
# Set AI ID for session
empirica --ai-id my_agent cascade "task"

# Use custom config file
empirica --config /path/to/config.yaml assess "question"

# Override log level
empirica --log-level DEBUG bootstrap

# Verbose output
empirica --verbose cascade "task"

# Quiet mode
empirica assess "question" --json
```

### Command-Specific Configuration

```bash
# Assessment with custom weights
empirica assess "question" \
  --weight-confidence 40 \
  --weight-coherence 30 \
  --weight-necessity 20 \
  --weight-engagement 10

# Cascade with investigation threshold
empirica cascade "task" \
  --investigation-threshold 0.7 \
  --uncertainty-threshold 0.65

# Bootstrap with specific components
empirica bootstrap \
  --enable code_intelligence \
  --enable tool_management \
  --disable drift_monitor
```

---

## Advanced Configuration

### Custom AI ID Setup

```bash
# Create new AI identity
mkdir -p .empirica/my_custom_ai
mkdir -p .empirica_reflex_logs/my_custom_ai

# Set environment
export EMPIRICA_AI_ID="my_custom_ai"

# Initialize database
empirica bootstrap --level standard

# Verify
empirica list --status
```

### Multi-AI Collaboration

```yaml
# config.yaml for multi-AI setup
collaboration:
  enabled: true
  shared_sessions: true
  
  agents:
    - id: "claude_copilot"
      role: "primary"
      capabilities: ["cascade", "assessment", "investigation"]
    
    - id: "gemini_analyst"
      role: "secondary"  
      capabilities: ["analysis", "verification"]
    
    - id: "qwen_specialist"
      role: "domain_expert"
      capabilities: ["code_analysis", "security"]
  
  sync:
    session_path: ".empirica/shared/sessions/"
    reflex_path: ".empirica_reflex_logs/shared/"
```

### Plugin Configuration

```yaml
# config.yaml - Plugin settings
plugins:
  enabled: true
  auto_discover: true
  plugin_paths:
    - "./plugins/"
    - "~/.empirica/plugins/"
  
  registry:
    code_analyzer:
      enabled: true
      priority: "high"
      config:
        max_depth: 10
        ignore_patterns: ["node_modules/", ".git/"]
    
    security_scanner:
      enabled: true
      priority: "critical"
      config:
        strict_mode: true
        report_all: false
```

---

## Configuration Best Practices

### Development

```bash
# .env for development
EMPIRICA_AI_ID=dev_agent
EMPIRICA_LOG_LEVEL=DEBUG
EMPIRICA_VERBOSE=true
EMPIRICA_AUTO_TRACK=true
EMPIRICA_ENABLE_ALL_COMPONENTS=true
```

### Production

```bash
# .env for production
EMPIRICA_AI_ID=prod_agent
EMPIRICA_LOG_LEVEL=WARNING
EMPIRICA_VERBOSE=false
EMPIRICA_QUIET=true
EMPIRICA_AUTO_TRACK=true
EMPIRICA_ASSESSMENT_TIMEOUT=60
EMPIRICA_RETRY_ON_FAILURE=5
```

### Testing

```bash
# .env for testing
EMPIRICA_AI_ID=test_agent
EMPIRICA_LOG_LEVEL=ERROR
EMPIRICA_AUTO_TRACK=false
EMPIRICA_TRACK_TO_DB=false
EMPIRICA_CACHE_ASSESSMENTS=true
```

---

## Validation & Troubleshooting

### Verify Configuration

```bash
# Show current configuration
empirica config --show

# Validate config file
empirica config --validate config.yaml

# Test with config
empirica config --test config.yaml cascade "test task"
```

### Common Issues

**Issue:** Weights don't sum to 100
```bash
# Fix in .env
EMPIRICA_WEIGHT_CONFIDENCE=35
EMPIRICA_WEIGHT_COHERENCE=25
EMPIRICA_WEIGHT_NECESSITY=25
EMPIRICA_WEIGHT_ENGAGEMENT=15
# Verify: 35+25+25+15 = 100 ✓
```

**Issue:** Database not found
```bash
# Check path
echo $EMPIRICA_DB_PATH

# Verify exists
ls -la .empirica/${EMPIRICA_AI_ID}/empirica.db

# Reinitialize
empirica bootstrap --level standard
```

**Issue:** Components not activating
```bash
# Check bootstrap level
empirica bootstrap --level extended

# Or manually enable
export EMPIRICA_ENABLE_CODE_INTELLIGENCE=true
```

---

## Configuration Migration

### From v1.x to v2.0

```bash
# Old v1.x config
SEMANTIC_KIT_ID=my_agent        # OLD
UNCERTAINTY_VECTORS=3           # OLD (was 3-vector)

# New v2.0 config
EMPIRICA_AI_ID=my_agent         # NEW
# (12 vectors automatic)
```

**Migration Script:**
```bash
#!/bin/bash
# migrate_config.sh

# Backup old config
cp .env .env.v1.backup

# Update environment variables
sed -i 's/SEMANTIC_KIT_ID/EMPIRICA_AI_ID/g' .env
sed -i 's/UNCERTAINTY_VECTORS=3//g' .env

# Add new v2.0 settings
cat >> .env << EOF
EMPIRICA_AUTO_TRACK=true
EMPIRICA_TRACK_TO_DB=true
EMPIRICA_TRACK_TO_JSON=true
EMPIRICA_TRACK_TO_REFLEX=true
EOF

# Reinitialize
empirica bootstrap --level standard

echo "✅ Migrated to v2.0"
```

---

## Security Considerations

**DO NOT commit to git:**
```bash
# .gitignore
.env
config.yaml
.empirica/
.empirica_reflex_logs/
```

**Protect sensitive data:**
```bash
# Set restrictive permissions
chmod 600 .env
chmod 700 .empirica/
```

**API Keys:**
```bash
# Store separately
OPENAI_API_KEY="sk-..."          # In .env
ANTHROPIC_API_KEY="sk-ant-..."   # In .env

# Never in config.yaml or version control
```

---

## Next Steps

- **Threshold Tuning:** See `16_TUNING_THRESHOLDS.md`
- **Monitoring:** See `18_MONITORING_LOGGING.md`
- **Production Deploy:** See `17_PRODUCTION_DEPLOYMENT.md`
- **API Reference:** See `19_API_REFERENCE.md`

---

**Last Updated:** 2025-10-29  
**Version:** 2.0
