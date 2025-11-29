# System Prompt Optimization Analysis

## Size Reduction Achieved
- **Original:** 1,758 words / 13,964 characters (~1,500 tokens)
- **Minimal:** 489 words / 4,055 characters (~500 tokens)  
- **Reduction:** **72% smaller** while maintaining full functionality

## Static vs Dynamic Separation

### ✅ Kept in Prompt (Static)
1. **Core Role & Purpose** (3 lines)
2. **13 Epistemic Vectors** (concise definitions)
3. **CASCADE Workflow** (basic pattern)
4. **MCO Integration Principle** (key concepts)
5. **Essential Tool Patterns** (critical parameters)
6. **Core Development Principles** (tests, completion, calibration)
7. **Basic Anti-Patterns** (do/don't essentials)

### ❌ Moved External (Dynamic)
1. **Detailed MCO Configurations** (personas, thresholds, bias corrections)
2. **Model-Specific Instructions** (claude_sonnet, gpt4, etc.)
3. **Profile Selection Logic** (auto-selection, manual overrides)
4. **Common Scenarios** (full code examples)
5. **Command Reference** (CLI usage, parameters)
6. **Extensive Tool Documentation** (detailed parameter lists)
7. **Cross-AI Coordination Details** (full workflow examples)
8. **Anti-Pattern Catalog** (comprehensive lists)

## Architecture Benefits

### 1. **Faster Processing**
- 72% less token processing overhead
- Quicker AI startup and context switching

### 2. **Dynamic Configuration**
- MCO loads operational specifics on-demand
- Persona/threshold adjustments without prompt changes
- Model-specific bias corrections externalized

### 3. **Easier Maintenance**
- Configuration changes don't require prompt updates
- Separate concerns (framework vs operations)
- Easier A/B testing of different configurations

### 4. **Personalization Ready**
- Different profiles load different external configs
- Same core prompt works for different AI models
- Role-specific optimizations (developer vs researcher)

## Implementation Strategy

The minimal prompt should be the primary system prompt, with external config loading happening during bootstrap:

```python
# During bootstrap:
1. Load minimal system prompt
2. Load MCO configurations (personas, thresholds, protocols)
3. Apply model-specific bias corrections
4. Set operational parameters based on task type
5. Initialize external command references
```

## Files to Create for Dynamic Loading

1. **`empirica/config/minimal_prompts.yaml`** - Prompt fragments by role
2. **`empirica/config/tool_references.yaml`** - Detailed tool usage
3. **`empirica/config/command_examples.yaml`** - CLI usage examples  
4. **`empirica/config/scenario_patterns.yaml`** - Common workflow patterns

This separation ensures the AI has enough context to function while allowing for dynamic optimization based on the specific task, model type, and operational requirements.
