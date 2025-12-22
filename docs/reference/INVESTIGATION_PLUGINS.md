# Investigation Plugins Module

The `empirica.core.metacognitive_cascade.investigation_plugin` module provides a plugin system for extending Empirica's investigation capabilities. This enables custom tools and integrations without modifying core code.

## Overview

Investigation plugins enable:

- **Custom tool integration** (JIRA, GitHub, databases, etc.)
- **Domain-specific investigations** (code analysis, documentation search, etc.)
- **Confidence-based tool selection** based on epistemic state
- **Automatic capability mapping** presented to LLM during investigation
- **Extensible architecture** for new investigation methods

## Core Components

### InvestigationPlugin

**Module**: `empirica.core.metacognitive_cascade.investigation_plugin`

**Purpose**: Base class for all investigation plugins

**Attributes**:
- `name` (`str`): Unique identifier for the tool
- `description` (`str`): Clear explanation shown to LLM
- `improves_vectors` (`List[str]`): Epistemic vectors this tool helps improve
- `confidence_gain` (`float`): Expected confidence increase (0.0-1.0)
- `tool_type` (`str`): Category (search, analysis, interaction, validation, custom)
- `executor` (`Optional[Callable]`): Function that executes the tool
- `metadata` (`Dict[str, Any]`): Additional plugin-specific data

**Example**:
```python
from empirica.core.metacognitive_cascade.investigation_plugin import InvestigationPlugin

# Create a JIRA search plugin
jira_plugin = InvestigationPlugin(
    name='jira_search',
    description='Search JIRA for related issues and tickets',
    improves_vectors=['know', 'context', 'state'],
    confidence_gain=0.20,
    tool_type='search',
    executor=lambda query, params: {"results": ["JIRA-123", "JIRA-456"]},
    metadata={
        "api_endpoint": "https://jira.example.com/rest/api/2/search",
        "auth_required": True
    }
)
```

**Tool Types**:
- `search`: Information retrieval tools
- `analysis`: Data analysis tools
- `interaction`: Communication tools
- `validation`: Verification tools
- `custom`: Specialized tools

**Related**:
- `PluginRegistry` - Plugin management system
- `EpistemicCascade` - Uses plugins for investigations

---

### PluginRegistry

**Module**: `empirica.core.metacognitive_cascade.investigation_plugin`

**Purpose**: Central registry for managing investigation plugins

**Methods**:

#### `register(plugin: InvestigationPlugin) -> bool`

**Purpose**: Register a new investigation plugin

**Parameters**:
- `plugin` (`InvestigationPlugin`): Plugin instance to register

**Returns**:
- `bool`: True if registration successful

**Example**:
```python
from empirica.core.metacognitive_cascade.investigation_plugin import PluginRegistry

registry = PluginRegistry()

# Register plugins
success = registry.register(jira_plugin)
if success:
    print("✅ Plugin registered successfully")
```

---

#### `get(name: str) -> Optional[InvestigationPlugin]`

**Purpose**: Retrieve a registered plugin by name

**Parameters**:
- `name` (`str`): Plugin name

**Returns**:
- `Optional[InvestigationPlugin]`: Plugin instance or None

**Example**:
```python
# Get a registered plugin
plugin = registry.get('jira_search')
if plugin:
    print(f"Found plugin: {plugin.name}")
```

---

#### `list_plugins() -> List[str]`

**Purpose**: List all registered plugin names

**Returns**:
- `List[str]`: List of plugin names

**Example**:
```python
# List all available plugins
plugins = registry.list_plugins()
print(f"Available plugins: {plugins}")
```

---

#### `get_all_capabilities() -> Dict[str, Dict[str, Any]]`

**Purpose**: Get capabilities of all registered plugins

**Returns**:
- `Dict[str, Dict[str, Any]]`: Plugin capabilities map

**Example**:
```python
# Get plugin capabilities for LLM
capabilities = registry.get_all_capabilities()
print(f"Plugin capabilities: {capabilities}")
```

---

#### `find_by_vector(vector_name: str) -> List[InvestigationPlugin]`

**Purpose**: Find plugins that improve a specific epistemic vector

**Parameters**:
- `vector_name` (`str`): Epistemic vector name (e.g., 'know', 'uncertainty')

**Returns**:
- `List[InvestigationPlugin]`: Plugins that improve the specified vector

**Example**:
```python
# Find plugins that improve 'know' vector
know_plugins = registry.find_by_vector('know')
print(f"Plugins for 'know': {[p.name for p in know_plugins]}")
```

---

#### `create_common_plugins() -> Dict[str, InvestigationPlugin]`

**Purpose**: Create standard investigation plugins

**Returns**:
- `Dict[str, InvestigationPlugin]`: Dictionary of common plugins

**Example**:
```python
# Create standard plugins
common_plugins = registry.create_common_plugins()

# Register them
for name, plugin in common_plugins.items():
    registry.register(plugin)
```

---

## Built-in Plugins

### Common Investigation Plugins

Empirica includes several built-in plugins:

#### `create_jira_plugin()`

**Purpose**: Create JIRA search and issue management plugin

**Example**:
```python
from empirica.core.metacognitive_cascade.investigation_plugin import create_jira_plugin

jira_plugin = create_jira_plugin(
    api_url="https://jira.example.com",
    username="empirica-bot",
    api_token="secret-token"
)
```

**Capabilities**:
- Search JIRA issues
- Get issue details
- Create new issues
- Update existing issues

---

#### `create_github_plugin()`

**Purpose**: Create GitHub repository analysis plugin

**Example**:
```python
from empirica.core.metacognitive_cascade.investigation_plugin import create_github_plugin

github_plugin = create_github_plugin(
    api_url="https://api.github.com",
    token="ghp_secret_token"
)
```

**Capabilities**:
- Search repositories
- Analyze code structure
- Get file contents
- Search issues and pull requests

---

#### `create_slack_plugin()`

**Purpose**: Create Slack communication plugin

**Example**:
```python
from empirica.core.metacognitive_cascade.investigation_plugin import create_slack_plugin

slack_plugin = create_slack_plugin(
    api_token="xoxb-secret",
    default_channel="#empirica-dev"
)
```

**Capabilities**:
- Search messages
- Post messages
- Get channel information
- Search files

---

#### `create_confluence_plugin()`

**Purpose**: Create Confluence documentation plugin

**Example**:
```python
from empirica.core.metacognitive_cascade.investigation_plugin import create_confluence_plugin

confluence_plugin = create_confluence_plugin(
    base_url="https://confluence.example.com",
    username="empirica-bot",
    api_token="secret-token"
)
```

**Capabilities**:
- Search documentation
- Get page content
- Create new pages
- Update existing pages

---

#### `create_database_query_plugin()`

**Purpose**: Create database query plugin

**Example**:
```python
from empirica.core.metacognitive_cascade.investigation_plugin import create_database_query_plugin

db_plugin = create_database_query_plugin(
    connection_string="postgresql://user:pass@localhost:5432/empirica",
    query_timeout=30.0
)
```

**Capabilities**:
- Execute SQL queries
- Get schema information
- Analyze query results
- Validate data

---

## Plugin Development Guide

### Creating Custom Plugins

```python
from empirica.core.metacognitive_cascade.investigation_plugin import InvestigationPlugin

class DocumentationSearchPlugin(InvestigationPlugin):
    """Custom plugin for searching documentation resources"""
    
    def __init__(self, api_key=None, base_url=None):
        super().__init__(
            name='documentation_search',
            description='Search Empirica documentation and examples',
            improves_vectors=['know', 'clarity', 'context'],
            confidence_gain=0.25,
            tool_type='search'
        )
        self.api_key = api_key
        self.base_url = base_url or "https://docs.empirica.ai"
        
    def execute(self, query: str, params: Dict) -> Dict[str, Any]:
        """Execute documentation search"""
        # Implementation would go here
        results = self._perform_search(query, params)
        
        return {
            "results": results,
            "confidence": self._calculate_confidence(results),
            "sources": [f"{self.base_url}/search?q={query}"],
            "metadata": {
                "plugin": self.name,
                "query": query,
                "timestamp": time.time()
            }
        }
    
    def _perform_search(self, query, params):
        """Actual search implementation"""
        # This would call documentation API or search local docs
        return [
            {"title": "Persona Module Documentation", "url": f"{self.base_url}/persona"},
            {"title": "Metacognitive Cascade Guide", "url": f"{self.base_url}/cascade"}
        ]
    
    def _calculate_confidence(self, results):
        """Calculate confidence based on results"""
        return min(0.95, 0.7 + len(results) * 0.05)

# Register the custom plugin
registry = PluginRegistry()
registry.register(DocumentationSearchPlugin(api_key="doc-api-key"))
```

### Plugin Best Practices

1. **Clear Description**: Write descriptions that help LLM understand when to use the plugin
2. **Specific Vectors**: Target specific epistemic vectors the plugin improves
3. **Realistic Confidence**: Set appropriate confidence gain expectations
4. **Error Handling**: Include robust error handling in execute methods
5. **Logging**: Log plugin usage for debugging and monitoring
6. **Metadata**: Include useful metadata for tracking and management

---

## Integration with Metacognitive Cascade

### Plugin Selection Workflow

```mermaid
graph TD
    A[Task Analysis] --> B[Identify Knowledge Gaps]
    B --> C[Find Relevant Plugins]
    C --> D[Select Best Plugin]
    D --> E[Execute Plugin]
    E --> F[Update Epistemic State]
    F --> G[Re-assess Task]
```

### Cascade Integration Example

```python
from empirica.core.metacognitive_cascade.metacognitive_cascade import EpistemicCascade
from empirica.core.metacognitive_cascade.investigation_plugin import PluginRegistry

# Create cascade with plugins
registry = PluginRegistry()
registry.create_common_plugins()  # Add standard plugins

# Add custom plugins
registry.register(DocumentationSearchPlugin())

# Initialize cascade with plugin registry
cascade = EpistemicCascade({
    "plugin_registry": registry
})

# Analyze task with plugin support
task = {
    "task_id": "complex-doc-task",
    "description": "Document advanced cascade features",
    "context": "Need examples and best practices"
}

results = cascade.analyze_single_task(task)

# Check if plugins were used
if "plugins_used" in results:
    print(f"Plugins used: {results['plugins_used']}")
    print(f"Confidence gain: {results['confidence_gain']}")
```

---

## Advanced Plugin Features

### Dynamic Plugin Loading

```python
# Load plugins from configuration
plugin_configs = [
    {
        "name": "custom_search",
        "type": "search",
        "description": "Custom search tool",
        "improves": ["know", "context"]
    }
]

for config in plugin_configs:
    plugin = create_plugin_from_config(config)
    registry.register(plugin)
```

### Plugin Chaining

```python
# Chain multiple plugins for complex investigations
def chain_plugins(task, plugins):
    results = {}
    confidence = 0.5
    
    for plugin_name in plugins:
        plugin = registry.get(plugin_name)
        if plugin:
            result = plugin.execute(task["description"], {})
            results[plugin_name] = result
            confidence = min(1.0, confidence + plugin.confidence_gain)
    
    return {
        "results": results,
        "final_confidence": confidence
    }

# Use plugin chain
chain_result = chain_plugins(task, ["web_search", "code_analysis", "documentation_search"])
```

### Plugin Monitoring

```python
# Monitor plugin usage and performance
monitor = registry.create_monitor()

# Get plugin statistics
stats = monitor.get_plugin_stats()
print(f"Plugin usage stats: {stats}")

# Get performance metrics
metrics = monitor.get_performance_metrics()
print(f"Performance metrics: {metrics}")
```

---

## Plugin Configuration Management

### Configuration File Example

```yaml
# plugins_config.yaml
plugins:
  - name: "jira_search"
    type: "search"
    description: "Search JIRA for related issues"
    improves_vectors: ["know", "context", "state"]
    confidence_gain: 0.20
    config:
      api_url: "https://jira.example.com"
      username: "empirica-bot"
      timeout: 30

  - name: "github_analysis"
    type: "analysis"
    description: "Analyze GitHub repositories"
    improves_vectors: ["know", "clarity"]
    confidence_gain: 0.25
    config:
      api_url: "https://api.github.com"
      default_repo: "empirical-ai/empirica"

  - name: "documentation_search"
    type: "search"
    description: "Search Empirica documentation"
    improves_vectors: ["know", "clarity", "context"]
    confidence_gain: 0.30
    config:
      base_url: "https://docs.empirica.ai"
      api_key: "doc-api-key"
```

### Loading Configuration

```python
import yaml
from empirica.core.metacognitive_cascade.investigation_plugin import PluginRegistry

def load_plugins_from_config(config_path):
    """Load plugins from YAML configuration"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    registry = PluginRegistry()
    
    for plugin_config in config.get('plugins', []):
        plugin = create_plugin_from_dict(plugin_config)
        if plugin:
            registry.register(plugin)
    
    return registry

# Load and register plugins
registry = load_plugins_from_config("plugins_config.yaml")
```

---

## Security and Best Practices

### Security Guidelines

1. **API Key Management**: Store keys securely, use environment variables
2. **Input Validation**: Validate all plugin inputs
3. **Rate Limiting**: Implement rate limiting for external APIs
4. **Error Handling**: Graceful degradation on failures
5. **Logging**: Log usage without sensitive data
6. **Authentication**: Use proper auth for external services

### Performance Optimization

1. **Caching**: Cache frequent plugin results
2. **Batching**: Batch similar requests
3. **Timeouts**: Set appropriate timeouts
4. **Parallelization**: Execute independent plugins in parallel
5. **Lazy Loading**: Load plugins only when needed

---

## Troubleshooting

### Common Issues

#### Plugin Not Found

**Symptom**: Plugin registered but not found

**Solution**:
```python
# Check registration
plugins = registry.list_plugins()
print(f"Registered plugins: {plugins}")

# Verify plugin name
plugin = registry.get("exact_plugin_name")  # Case sensitive!
```

#### Plugin Execution Failed

**Symptom**: Plugin throws exception during execution

**Solution**:
```python
try:
    result = plugin.execute(query, params)
except Exception as e:
    logger.error(f"Plugin {plugin.name} failed: {e}")
    # Fallback to default behavior
    result = fallback_execution(query, params)
```

#### Low Confidence Results

**Symptom**: Plugin returns low confidence results

**Solution**:
```python
# Check plugin configuration
print(f"Confidence gain: {plugin.confidence_gain}")
print(f"Improves vectors: {plugin.improves_vectors}")

# Adjust configuration or use alternative plugin
if result["confidence"] < 0.6:
    alternative = registry.find_alternative_plugin(plugin.name)
```

---

## Summary

The investigation plugins module provides:

- **🔌 Extensible plugin architecture** for custom tools
- **🤖 LLM-integrated capability mapping** for intelligent tool selection
- **📊 Confidence-based plugin selection** based on epistemic needs
- **🛠️ Built-in plugins** for common integrations
- **🔧 Easy development** of custom plugins

This system enables Empirica to leverage external tools and services intelligently, extending its investigation capabilities while maintaining a clean separation between core logic and tool integrations.