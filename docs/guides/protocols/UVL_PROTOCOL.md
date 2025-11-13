# UVL Protocol Specification
## Uncertainty Visualization Language for Collaborative AI

**Version 1.0** | **Last Updated**: 2025-01-26

---

## 🎯 Overview

The **UVL (Uncertainty Visualization Language) Protocol** provides a standardized way to visualize and communicate uncertainty states in collaborative AI systems. UVL enables real-time uncertainty sharing between AI agents, human operators, and monitoring systems.

## 🎨 Core Concepts

### 1. Uncertainty Vectors

UVL represents uncertainty using the **3-vector KNOW-DO-CONTEXT framework**:

- **KNOW**: Knowledge certainty (0.0 = certain, 1.0 = completely uncertain)
- **DO**: Capability confidence (0.0 = very capable, 1.0 = incapable)  
- **CONTEXT**: Environmental validity (0.0 = stable context, 1.0 = unreliable context)

### 2. Color Coding

UVL uses intuitive color coding for uncertainty levels:

- **🟢 Green**: Confident (< 0.2 uncertainty)
- **🟡 Yellow**: Moderate (0.2-0.6 uncertainty)
- **🔴 Red**: High uncertainty (> 0.6 uncertainty)

### 3. Node Representation

AI agents and systems are represented as **nodes** with emoji identifiers:

- **🤖 Lead AI**: Primary decision-making AI
- **⚙️ Worker AI**: Task-executing AI agents
- **⚖️ Sentinel**: Security/compliance monitoring
- **👤 Human**: Human operators
- **🌐 System**: External systems/services

## 📊 UVL Syntax

### Basic Node State

```
{node_emoji}{color} {node_description}:
├─ KNOW: {value} {color} ({description})
├─ DO: {value} {color} ({description})  
└─ CONTEXT: {value} {color} ({description})
```

### Example

```
🤖🟡 Lead AI Metacognitive State:
├─ KNOW: 0.25 🟡 (partial domain knowledge)
├─ DO: 0.15 🟢 (confident in tools)
└─ CONTEXT: 0.45 🟡 (validating environment)
```

### Decision Output

```
→ Decision: {ACTION} (confidence: {value})
```

Where `{ACTION}` is one of:
- **ACT**: High confidence, proceed with execution
- **CHECK**: Medium confidence, validate before proceeding  
- **INVESTIGATE**: Low confidence, gather more information

## 🔄 Real-time Updates

### Streaming Format

UVL supports real-time streaming updates:

```
[UVL] {timestamp} {node_id} {update_type} {content}
```

Examples:
```
[UVL] 14:23:45 🤖 STATE_UPDATE KNOW:0.2→0.3 (new information)
[UVL] 14:23:46 🤖 DECISION_UPDATE CHECK→ACT (confidence increased)
[UVL] 14:23:47 ⚙️ TASK_START analyzing_codebase
```

### Update Types

- **STATE_UPDATE**: Vector value changes
- **DECISION_UPDATE**: Action decision changes
- **TASK_START/COMPLETE**: Task lifecycle events
- **CALIBRATION_ALERT**: Calibration adjustments
- **ERROR**: Error conditions
- **SYNC**: Cross-agent synchronization

## 🤝 Multi-Agent Collaboration

### Agent Communication

```
🤖🟡 Lead AI → ⚙️🟢 Worker AI:
├─ Task: analyze_security_logs
├─ Context: production_environment
├─ Uncertainty: CONTEXT:0.4 (environment_access)
└─ Expected: security_assessment_report
```

### Coordination Patterns

**1. Task Delegation**
```
🤖🟡 Lead AI (KNOW:0.6, DO:0.8, CONTEXT:0.3):
├─ Decision: INVESTIGATE  
├─ Action: delegate_to_specialist
└─ Target: ⚙️🟢 Security Analyzer

⚙️🟢 Security Analyzer (KNOW:0.2, DO:0.1, CONTEXT:0.3):
├─ Task: security_audit_accepted
├─ Confidence: HIGH
└─ ETA: 5_minutes
```

**2. Uncertainty Escalation**
```
⚙️🔴 Worker AI (KNOW:0.8, DO:0.7, CONTEXT:0.6):
├─ Status: HIGH_UNCERTAINTY_DETECTED
├─ Issue: unknown_vulnerability_pattern
├─ Escalation: → 🤖 Lead AI
└─ Request: expert_consultation

🤖🟡 Lead AI Response:
├─ Acknowledged: escalation_received
├─ Action: consulting_security_expert
└─ Timeline: investigating
```

## 🖥️ tmux Integration

### Dashboard Layout

UVL is designed for tmux multi-pane dashboards:

```
┌─ Pane 1: Lead AI (🤖) ─────────────────────┐
│ 🤖🟡 Metacognitive State:                  │
│ ├─ KNOW: 0.3 🟡 (partial domain knowledge) │
│ ├─ DO: 0.15 🟢 (confident in tools)        │
│ ├─ CONTEXT: 0.45 🟡 (validating workspace) │
│ └─ Decision: CHECK → INVESTIGATE           │
├─────────────────────────────────────────────┤
│ Pane 2: Worker AI (⚙️) ───────────────────  │
│ ⚙️🟢 Security Analysis Task                │
│ ├─ [🔍🟢] Vulnerability Scan: COMPLETED    │
│ ├─ [📊🟡] Risk Assessment: IN_PROGRESS     │
│ └─ [📝] → Reports to Lead AI               │
├─────────────────────────────────────────────┤
│ Pane 3: Sentinel (⚖️) ────────────────────  │
│ ⚖️🟢 Security & Compliance Monitor         │
│ ├─ [🛡️🟢] System Integrity: VALIDATED      │
│ ├─ [🛡️🟡] File Access: REVIEWING           │
│ └─ [🛡️🟢] Capability Grant: APPROVED       │
├─────────────────────────────────────────────┤
│ Pane 4: System State ─────────────────────  │
│ 📊 Global Uncertainty Dashboard             │
│ ├─ Avg KNOW: 0.25  DO: 0.15  CONTEXT: 0.35 │
│ ├─ ✨ Flow State: APPROACHING (U_avg=0.25) │
│ └─ 🔄 Active Syncs: 2 tasks pending        │
└─────────────────────────────────────────────┘
```

### Setup Commands

```bash
# Generate tmux UVL dashboard
semantic-kit uvl --tmux

# Start live monitoring
tmux new-session -s empirica-uvl \; \
  split-window -v \; \
  split-window -h \; \
  select-pane -t 0 \; \
  split-window -h \; \
  send-keys -t 0 'semantic-kit cascade --monitor' Enter \; \
  send-keys -t 1 'semantic-kit uvl --monitor "current task"' Enter \; \
  send-keys -t 2 'semantic-kit calibration --live' Enter \; \
  send-keys -t 3 'semantic-kit calibration --status' Enter
```

## 🔧 Implementation

### Python Integration

```python
from semantic_self_aware_kit.adaptive_uncertainty_calibration import UVLProtocol, UQVector

# Render UVL state
vectors = {
    UQVector.KNOW: 0.3,
    UQVector.DO: 0.15,
    UQVector.CONTEXT: 0.45
}

uvl_output = UVLProtocol.render_uvl_state(vectors, '🤖')
print(uvl_output)

# Emit UVL messages
UVLProtocol.emit_uvl("🔄💭 Calibration adjustment detected")
```

### CLI Integration

```bash
# Show UVL for specific task
semantic-kit uvl --monitor "Deploy to production"

# Continuous UVL streaming
semantic-kit uvl --monitor "Current project" --stream

# UVL demonstration
semantic-kit uvl --demo
```

### Custom UVL Renderers

```python
class CustomUVLRenderer:
    def render_node_state(self, node_id, vectors, context):
        # Custom rendering logic
        max_uncertainty = max(vectors.values())
        node_color = self.get_color(max_uncertainty)
        
        return f"{node_id}{node_color} Custom State: {context}"
    
    def render_collaboration(self, source, target, task, uncertainty):
        return f"{source} → {target}: {task} (U: {uncertainty:.2f})"
```

## 📡 Network Protocol

### Message Format

UVL messages use JSON for network transmission:

```json
{
  "timestamp": "2025-01-26T14:23:45Z",
  "node_id": "🤖",
  "node_type": "lead_ai",
  "message_type": "state_update",
  "vectors": {
    "know": 0.25,
    "do": 0.15,
    "context": 0.45
  },
  "decision": "CHECK",
  "confidence": 0.72,
  "context": {
    "task": "security_analysis",
    "environment": "production"
  }
}
```

### WebSocket Streaming

```javascript
// Connect to UVL stream
const uvlSocket = new WebSocket('ws://localhost:8988/uvl-stream');

uvlSocket.onmessage = function(event) {
    const uvlMessage = JSON.parse(event.data);
    updateDashboard(uvlMessage);
};
```

## 🎯 Best Practices

### 1. Meaningful Descriptions

Use descriptive uncertainty context:

```
✅ Good: KNOW: 0.4 🟡 (partial API documentation)
❌ Poor: KNOW: 0.4 🟡
```

### 2. Consistent Node Identifiers

Use consistent emoji patterns:
- **🤖** for primary AI agents
- **⚙️** for specialized workers  
- **⚖️** for monitoring/security
- **🌐** for external systems

### 3. Appropriate Update Frequency

Balance real-time updates with noise:
- **High-frequency**: Critical operations
- **Medium-frequency**: Normal task execution
- **Low-frequency**: Background monitoring

### 4. Clear Action Mapping

Map decisions to clear actions:
- **ACT** → Immediate execution
- **CHECK** → Validation required
- **INVESTIGATE** → More information needed

## 🔍 Debugging & Monitoring

### UVL Logs

Enable UVL logging for debugging:

```bash
export EMPIRICA_UVL_LOG_LEVEL=DEBUG
semantic-kit calibration --test "Debug task" --uvl-verbose
```

### Performance Monitoring

Monitor UVL performance impact:

```python
from semantic_self_aware_kit.adaptive_uncertainty_calibration import UVLProtocol

# Measure UVL overhead
import time
start = time.time()
UVLProtocol.render_uvl_state(vectors)
overhead = time.time() - start
print(f"UVL rendering overhead: {overhead*1000:.2f}ms")
```

## 🚀 Future Extensions

### Planned Features

- **3D Uncertainty Visualization**: WebGL-based 3D uncertainty space
- **Historical Uncertainty Tracking**: Time-series uncertainty analysis
- **Multi-Modal UVL**: Audio/visual uncertainty indicators
- **AR/VR Integration**: Immersive uncertainty visualization
- **Cross-Platform Protocol**: Mobile and embedded device support

### Extension Points

```python
# Custom UVL extensions
class AdvancedUVLProtocol(UVLProtocol):
    def render_3d_uncertainty_space(self, vectors):
        # 3D visualization implementation
        pass
    
    def render_uncertainty_timeline(self, history):
        # Historical uncertainty tracking
        pass
```

---

## 📚 References

- [Empirica SDK Documentation](README.md)
- [Adaptive Calibration Guide](CALIBRATION_GUIDE.md)
- [CLI Reference](CLI_REFERENCE.md)
- [Multi-AI Collaboration Patterns](COLLABORATION.md)

**The UVL Protocol enables transparent, collaborative AI with empirical uncertainty grounding.** 🎨🤖