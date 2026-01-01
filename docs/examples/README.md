# Empirica Configuration Examples

This directory contains example configuration files for new Empirica projects.

## Files

### `project.yaml.example`

Example `.empirica/project.yaml` configuration file.

**Purpose:** Per-project settings (metadata, BEADS integration, subjects/workstreams)

**Location:** Copy to `<your-repo>/.empirica/project.yaml`

**Created by:** `empirica project-init` (automatic)

**When to customize:**
- Enable BEADS by default for your team
- Define subjects/workstreams for multi-component projects
- Configure project-specific behavior

**Example usage:**
```bash
cd your-project
cp docs/examples/project.yaml.example .empirica/project.yaml
# Edit to match your project
```

Or just run:
```bash
empirica project-init
# Interactive prompts will guide you
```

## See Also

- [Configuration Architecture](../development/session-summaries/CONFIG_ARCHITECTURE_EXPLAINED.md)
- [Project Init Guide](../development/session-summaries/PROJECT_INIT_ONBOARDING.md)
- [Installation Guide](../02_INSTALLATION.md)
