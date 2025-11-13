# Empirica Tmux Extension - Simplified Architecture

## Overview

The Empirica Tmux Extension has been simplified to its core essence: **2 panels, 2 action hooks**.

## Architecture

### Layout
```
┌──────────────────┬─────────────┐
│                  │   Pane 1    │
│    Pane 0        │   Chain of  │
│  (User working)  │   Thought   │
│                  ├─────────────┤
│                  │   Pane 2    │
│                  │  12-Vector  │
│                  │     UVL     │
└──────────────────┴─────────────┘
     70%                30%
```

### Two Action Hooks

#### Hook 1: Chain of Thought (Pane 1 - Top Right)
**Purpose**: Show AI's decision-making process in real-time

**Triggers**: When AI performs actions like:
- assess
- decide
- cascade
- investigate
- any decision point

**Data Structure**:
```python
{
    "action": "assess_task",
    "decision": "ACT",
    "confidence": 0.85,
    "rationale": "High confidence in approach",
    "status": "complete"  # or "processing", "error"
}
```

**Usage**:
```python
ext.update_chain_of_thought("assess_task", {
    "decision": "ACT",
    "confidence": 0.85,
    "rationale": "High confidence in approach",
    "status": "complete"
})
```

#### Hook 2: Epistemic Humility / 12-Vector UVL (Pane 2 - Bottom Right)
**Purpose**: Show AI's self-awareness state across 12 dimensions

**Triggers**: When AI performs self-assessment

**Data**: TwelveVectorCognitiveState object with:
- Dimension 1: Uncertainty (KNOW, DO, CONTEXT)
- Dimension 2: Comprehension (CLARITY, COHERENCE, DENSITY, SIGNAL)
- Dimension 3: Execution (STATE, CHANGE, COMPLETION, IMPACT)
- Dimension 4: Engagement (THE 12TH VECTOR)

**Usage**:
```python
# With state object
ext.update_epistemic_humility(state)

# Or without (shows placeholder)
ext.update_epistemic_humility()
```

## Key Features

### 1. **Intelligent Pane Detection**
- Checks if panes already exist before creating
- Never creates duplicate panes
- Reuses existing panes in current tmux session

### 2. **Direct Updates (No Temp Files)**
- Sends output directly to panes
- No watch/tail complexity
- Clean, simple, reliable

### 3. **Graceful Degradation**
- Works even if not in tmux (just doesn't display)
- Shows helpful placeholders when no data available
- Error-tolerant

## Usage Examples

### Basic Setup
```python
from tmux_extension.empirica_tmux_simple import launch_empirica_tmux

# Launch extension
ext = launch_empirica_tmux()

# Extension auto-detects tmux session and creates panels
```

### Integration with Empirica CLI

The extension integrates seamlessly with Empirica CLI commands:

```bash
# When you run assess command
empirica assess "task" --verbose

# The extension should:
# 1. Update Chain of Thought with the assessment action
# 2. Update 12-Vector UVL with the resulting state
```

### Integration Points

In Empirica CLI (`empirica_cli.py`), add hooks at decision points:

```python
def handle_assess(self, args):
    # ... existing code ...
    
    # Update chain of thought
    if hasattr(self, 'tmux_ext') and self.tmux_ext:
        self.tmux_ext.update_chain_of_thought("assess", {
            "decision": assessment.recommended_action,
            "confidence": assessment.overall_confidence(),
            "status": "complete"
        })
        
        # Update epistemic humility
        self.tmux_ext.update_epistemic_humility(assessment)
```

## Benefits of Simplification

1. **Clarity**: Only 2 action hooks to understand
2. **Reliability**: No complex temp file management
3. **Maintainability**: ~300 lines vs 800+ lines
4. **Transparency**: Easy to see what's updating where
5. **Portability**: Minimal dependencies

## Files

- `empirica_tmux_simple.py` - Simplified extension (300 lines)
- `empirica_tmux_extension.py` - Original (kept for reference)

## Testing

```bash
# Test the extension standalone
cd /home/yogapad/empirical-ai/semantic_self_aware_kit
python3 tmux_extension/empirica_tmux_simple.py

# Check panes 1 and 2 for updates
```

## Next Steps

1. ✅ Fix assess command (completed - all_vectors attribute issue)
2. ✅ Create simplified tmux extension (completed)
3. ⏭️ Integrate hooks into empirica_cli.py
4. ⏭️ Test with real workflow operations
5. ⏭️ Update MCP server to use simplified hooks

## Summary

The simplified architecture focuses on the essential feedback loop:
- **Chain of Thought** → Shows what the AI is thinking/doing
- **Epistemic Humility** → Shows the AI's self-awareness state

This provides maximum transparency with minimum complexity, enabling effective human-AI collaboration guided by epistemic humility.
