# Custom Plugins Guide

**Empirica v2.0 - Extending Investigation Capabilities**

---

## Overview

The plugin system allows **zero core code modification** - extend Empirica with domain-specific tools without changing the cascade.

**Philosophy:** Universal extensibility through plugins, not by modifying core.

---

## Quick Example

```python
from empirica.investigation import InvestigationPlugin

# Define plugin
jira_plugin = InvestigationPlugin(
    name='jira_search',
    description='Search JIRA for related issues',
    execute_fn=lambda ctx: search_jira(ctx['query']),
    improves_vectors=['know', 'context'],
    confidence_gain=0.25
)

# Use in cascade
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

cascade = CanonicalEpistemicCascade(
    investigation_plugins={'jira_search': jira_plugin}
)
```

---

## InvestigationPlugin Structure

### Required Fields

```python
plugin = InvestigationPlugin(
    name='tool_name',              # Unique identifier
    description='What it does',    # Human-readable description
    execute_fn=callable,           # Function to execute
    improves_vectors=['know'],     # Which vectors it improves
    confidence_gain=0.25           # Expected confidence gain (0.0-1.0)
)
```

### Optional Fields

```python
plugin = InvestigationPlugin(
    name='advanced_tool',
    description='Does advanced stuff',
    execute_fn=my_function,
    improves_vectors=['know', 'context'],
    confidence_gain=0.30,
    
    # Optional
    required_context=['api_key', 'endpoint'],  # Context keys needed
    domain_specific='security',                # Domain restriction
    async_execution=True                       # If execute_fn is async
)
```

---

## Plugin Examples

### Example 1: JIRA Integration

```python
import requests
from empirica.investigation import InvestigationPlugin

def search_jira(context):
    """Search JIRA for issues related to task"""
    query = context.get('query', '')
    api_key = context.get('jira_api_key')
    
    response = requests.get(
        f"https://jira.company.com/rest/api/2/search",
        params={'jql': f'text ~ "{query}"'},
        headers={'Authorization': f'Bearer {api_key}'}
    )
    
    issues = response.json().get('issues', [])
    return {
        'issues_found': len(issues),
        'summaries': [i['fields']['summary'] for i in issues[:5]]
    }

jira_plugin = InvestigationPlugin(
    name='jira_search',
    description='Search JIRA issues for context',
    execute_fn=search_jira,
    improves_vectors=['know', 'context'],
    confidence_gain=0.25,
    required_context=['jira_api_key'],
    domain_specific='code_analysis'
)
```

### Example 2: Confluence Documentation

```python
def search_confluence(context):
    """Search Confluence for documentation"""
    query = context.get('query')
    space = context.get('confluence_space', 'DEV')
    
    # Your Confluence API call
    docs = confluence_client.search(query, space=space)
    
    return {
        'documents_found': len(docs),
        'relevant_pages': [d['title'] for d in docs[:3]]
    }

confluence_plugin = InvestigationPlugin(
    name='confluence_search',
    description='Search Confluence documentation',
    execute_fn=search_confluence,
    improves_vectors=['know', 'clarity'],
    confidence_gain=0.30,
    required_context=['confluence_space']
)
```

### Example 3: Database Schema Analysis

```python
import sqlalchemy

def analyze_database_schema(context):
    """Analyze database schema for context"""
    db_url = context.get('database_url')
    engine = sqlalchemy.create_engine(db_url)
    
    inspector = sqlalchemy.inspect(engine)
    tables = inspector.get_table_names()
    
    schema_info = {}
    for table in tables:
        columns = inspector.get_columns(table)
        schema_info[table] = [c['name'] for c in columns]
    
    return {
        'tables': len(tables),
        'schema': schema_info
    }

db_plugin = InvestigationPlugin(
    name='database_schema_analysis',
    description='Analyze database schema structure',
    execute_fn=analyze_database_schema,
    improves_vectors=['context', 'state'],
    confidence_gain=0.35,
    required_context=['database_url'],
    domain_specific='architecture'
)
```

### Example 4: Async Plugin

```python
import aiohttp

async def async_web_search(context):
    """Async web search"""
    query = context.get('query')
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.search.com/v1/search",
            params={'q': query}
        ) as response:
            results = await response.json()
            return {
                'results_found': len(results),
                'top_result': results[0] if results else None
            }

async_plugin = InvestigationPlugin(
    name='async_web_search',
    description='Async web search engine',
    execute_fn=async_web_search,
    improves_vectors=['know', 'context'],
    confidence_gain=0.20,
    async_execution=True  # Mark as async
)
```

---

## Plugin Registry

Manage multiple plugins:

```python
from empirica.investigation import PluginRegistry

registry = PluginRegistry()

# Register plugins
registry.register(jira_plugin)
registry.register(confluence_plugin)
registry.register(db_plugin)

# Query plugins
know_plugins = registry.get_plugins_by_vector('know')
security_plugins = registry.get_plugins_by_domain('security')

# Validate
is_valid = registry.validate_plugin(jira_plugin)

# Get tool map
tool_map = registry.get_tool_map()
```

---

## Using Plugins in Cascade

### Method 1: Direct Integration

```python
cascade = CanonicalEpistemicCascade(
    investigation_plugins={
        'jira_search': jira_plugin,
        'confluence_search': confluence_plugin,
        'db_analysis': db_plugin
    }
)

result = await cascade.run_epistemic_cascade(task, context)
```

### Method 2: Registry Integration

```python
registry = PluginRegistry()
registry.register(jira_plugin)
registry.register(confluence_plugin)

cascade = CanonicalEpistemicCascade(
    investigation_plugins=registry.get_all_plugins()
)
```

---

## Plugin Execution

### Context Passing

Plugins receive context dict with:
- Task information
- User-provided context
- Investigation state
- Required context keys

```python
def my_plugin_fn(context):
    # Standard context
    task = context.get('task')
    cwd = context.get('cwd')
    
    # Plugin-specific context
    api_key = context.get('my_api_key')
    
    # Investigation state
    current_round = context.get('investigation_round')
    
    return {'result': 'data'}
```

### Return Format

Plugins should return dict with:
- Results/data found
- Metadata about execution
- Any errors encountered

```python
return {
    'success': True,
    'data': {...},
    'items_found': 5,
    'duration_ms': 123,
    'error': None  # or error message if failed
}
```

---

## Error Handling

### Plugin-Level Errors

```python
def robust_plugin(context):
    try:
        # Your logic
        result = do_something()
        return {'success': True, 'data': result}
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'data': None
        }
```

### Cascade-Level Handling

Cascade handles plugin failures gracefully:
- Failed plugin → skip to next recommendation
- All plugins fail → exit investigation round
- Investigation failure → confidence not improved

---

## Best Practices

### Do:
✅ Return dict with consistent structure
✅ Handle errors internally
✅ Set realistic confidence_gain values
✅ Specify required_context clearly
✅ Keep execute_fn focused (single purpose)
✅ Add logging for debugging

### Don't:
❌ Modify core cascade code
❌ Assume context keys exist (check first)
❌ Make blocking calls without timeout
❌ Return huge data structures (keep concise)
❌ Throw unhandled exceptions

---

## Example Plugin Library

```python
# plugin_library.py
from empirica.investigation import InvestigationPlugin

class PluginLibrary:
    """Collection of reusable plugins"""
    
    @staticmethod
    def jira_plugin(api_key):
        return InvestigationPlugin(
            name='jira_search',
            description='Search JIRA issues',
            execute_fn=lambda ctx: search_jira(ctx, api_key),
            improves_vectors=['know', 'context'],
            confidence_gain=0.25
        )
    
    @staticmethod
    def github_plugin(token):
        return InvestigationPlugin(
            name='github_search',
            description='Search GitHub code',
            execute_fn=lambda ctx: search_github(ctx, token),
            improves_vectors=['know'],
            confidence_gain=0.30
        )
    
    @staticmethod
    def slack_plugin(workspace, token):
        return InvestigationPlugin(
            name='slack_search',
            description='Search Slack messages',
            execute_fn=lambda ctx: search_slack(ctx, workspace, token),
            improves_vectors=['context'],
            confidence_gain=0.20
        )

# Usage
library = PluginLibrary()
cascade = CanonicalEpistemicCascade(
    investigation_plugins={
        'jira': library.jira_plugin(api_key='xxx'),
        'github': library.github_plugin(token='yyy'),
        'slack': library.slack_plugin('workspace', 'zzz')
    }
)
```

---

## Testing Plugins

```python
import pytest
from empirica.investigation import InvestigationPlugin

def test_jira_plugin():
    plugin = jira_plugin
    
    # Test validation
    assert plugin.name == 'jira_search'
    assert 'know' in plugin.improves_vectors
    
    # Test execution
    context = {
        'query': 'authentication',
        'jira_api_key': 'test_key'
    }
    result = plugin.execute_fn(context)
    
    assert 'issues_found' in result
    assert isinstance(result['issues_found'], int)

def test_plugin_with_missing_context():
    context = {}  # Missing required keys
    
    result = jira_plugin.execute_fn(context)
    
    # Should handle gracefully
    assert result is not None
    assert 'error' in result or 'success' in result
```

---

## Domain-Specific Plugins

### Security Domain
```python
security_plugins = {
    'vulnerability_scan': vulnerability_plugin,
    'security_audit': audit_plugin,
    'dependency_check': dependency_plugin
}

cascade = CanonicalEpistemicCascade(
    investigation_plugins=security_plugins
)
```

### Architecture Domain
```python
architecture_plugins = {
    'component_map': component_plugin,
    'dependency_graph': dependency_plugin,
    'service_discovery': discovery_plugin
}
```

### Data Domain
```python
data_plugins = {
    'schema_analysis': schema_plugin,
    'data_quality': quality_plugin,
    'migration_planning': migration_plugin
}
```

---

## Next Steps

- **Investigation System:** [07_INVESTIGATION_SYSTEM.md](07_INVESTIGATION_SYSTEM.md)
- **Python API:** [13_PYTHON_API.md](13_PYTHON_API.md)
- **Examples:** See `examples/` directory (coming soon)

---

**Extend Empirica's capabilities without touching core code!** 🔌
