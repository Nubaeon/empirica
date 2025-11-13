# 🔌 Plugin System - Extending Empirica

Complete guide to creating custom investigation tools.

---

## Overview

The plugin system allows you to extend Empirica with custom tools **without modifying core code**.

### Key Benefits:
- ✅ Zero core code modification
- ✅ Automatic LLM explanation
- ✅ Domain-specific tool integration
- ✅ Company-specific APIs
- ✅ Industry database connections

---

## Quick Start

```python
from empirica.investigation import InvestigationPlugin
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

# Create plugin
jira_plugin = InvestigationPlugin(
    name='jira_search',
    description='Search JIRA for related issues and tickets',
    improves_vectors=['know', 'context', 'state'],
    confidence_gain=0.20,
    tool_type='search'
)

# Use in cascade
cascade = CanonicalEpistemicCascade(
    investigation_plugins={'jira_search': jira_plugin}
)
```

---

## Creating a Plugin

### Basic Plugin

```python
plugin = InvestigationPlugin(
    name='my_tool',                    # Unique identifier
    description='What this does',      # Shown to LLM
    improves_vectors=['know'],         # Which vectors it helps
    confidence_gain=0.25,              # Expected boost
    tool_type='search'                 # Category
)
```

### Valid Vectors:
`know`, `do`, `context`, `clarity`, `coherence`, `signal`, `density`, `state`, `change`, `completion`, `impact`, `engagement`

### Tool Types:
- `search` - Finding information
- `analysis` - Analyzing data
- `validation` - Checking/testing
- `interaction` - User communication
- `custom` - Other

---

## Example Plugins

### JIRA Integration
```python
def create_jira_plugin():
    return InvestigationPlugin(
        name='jira_search',
        description='Search JIRA for related issues, tickets, and project information',
        improves_vectors=['know', 'context', 'state'],
        confidence_gain=0.20,
        tool_type='search',
        metadata={
            'api_required': True,
            'authentication': 'required',
            'rate_limit': '100 requests/hour'
        }
    )
```

### Confluence Search
```python
confluence_plugin = InvestigationPlugin(
    name='confluence_search',
    description='Search Confluence for documentation and knowledge base articles',
    improves_vectors=['know', 'clarity', 'context'],
    confidence_gain=0.25,
    tool_type='search'
)
```

### Custom Database Query
```python
db_plugin = InvestigationPlugin(
    name='database_query',
    description='Query production database for current state and data validation',
    improves_vectors=['know', 'state', 'context'],
    confidence_gain=0.30,
    tool_type='analysis',
    metadata={
        'requires_permissions': True,
        'safety': 'Read-only queries recommended'
    }
)
```

---

## Plugin Registry

For managing multiple plugins:

```python
from empirica.investigation import PluginRegistry

# Create registry
registry = PluginRegistry()

# Register plugins
registry.register(jira_plugin)
registry.register(confluence_plugin)
registry.register(custom_plugin)

# List all
print(registry.list_plugins())

# Find by vector
know_plugins = registry.find_by_vector('know')

# Use in cascade
cascade = CanonicalEpistemicCascade(
    investigation_plugins=registry.plugins
)
```

---

## What LLM Sees

During investigation, your plugin appears in tool capabilities:

```json
{
  "tool_capabilities": {
    "jira_search": {
      "description": "Search JIRA for related issues and tickets",
      "improves_vectors": ["know", "context", "state"],
      "tool_type": "search",
      "confidence_gain": 0.20,
      "plugin": true,
      "metadata": {
        "api_required": true
      }
    }
  }
}
```

The LLM can then decide to use your tool based on its needs.

---

## Best Practices

### 1. Clear Descriptions
```python
# ❌ Bad
description='Search stuff'

# ✅ Good
description='Search JIRA for related issues, tickets, and project context. Use when investigating bugs or feature requests.'
```

### 2. Accurate Vector Mapping
```python
# Database query improves KNOW and STATE
improves_vectors=['know', 'state']

# User clarification improves CLARITY
improves_vectors=['clarity']
```

### 3. Reasonable Confidence Gains
- 0.10-0.15: Minor help
- 0.15-0.25: Moderate help
- 0.25-0.35: Significant help
- 0.35-0.45: Major help (reserve for user interaction)

### 4. Useful Metadata
```python
metadata={
    'api_url': 'https://api.company.com',
    'rate_limit': '100/hour',
    'requires_auth': True,
    'safety_notes': 'Read-only access recommended'
}
```

---

## Common Use Cases

### Company Tools
- Internal APIs
- Documentation systems
- Project management tools
- Communication platforms

### Industry-Specific
- Medical databases
- Legal research tools
- Financial data sources
- Scientific repositories

### Domain-Specific
- Cloud provider APIs
- Monitoring systems
- CI/CD tools
- Analytics platforms

---

## Next Steps

- See examples: `examples/` directory
- Integration guide: `14_CUSTOM_PLUGINS.md`
- API reference: `19_API_REFERENCE.md`

