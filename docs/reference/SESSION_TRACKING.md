# Session Tracking Reference

**Component:** Auto Tracker (EmpericaTracker)  
**Status:** Production Active  
**Used By:** Bootstraps, Dashboard, Modality Switcher

---

## Overview

Empirica's automatic session tracking provides zero-configuration tracking of CASCADE executions, epistemic assessments, and AI collaboration sessions. It enables dashboards, monitoring, and session replay without manual instrumentation.

**Key Benefit:** Just run your CASCADE - tracking happens automatically.

---

## Architecture

### Core Component

**`EmpericaTracker`** - Automatic session tracking

**Location:** `empirica/auto_tracker.py`

**Purpose:**
- Track CASCADE executions automatically
- Capture epistemic state snapshots
- Enable dashboard monitoring
- Support session replay and analysis

---

## Integration Points

### 1. Bootstraps

**Optimal Metacognitive Bootstrap:**
```python
from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_session
from empirica.auto_tracker import EmpericaTracker

# Tracker initialized automatically
session = bootstrap_session(
    ai_id='claude',
    session_type='production'
)

# Access tracker if needed
tracker = EmpericaTracker.get_instance()
```

**Extended Bootstrap:**
```python
from empirica.bootstraps.extended_metacognitive_bootstrap import bootstrap_with_extensions
from empirica.auto_tracker import EmpericaTracker

session = bootstrap_with_extensions(
    ai_id='minimax',
    enable_tracking=True  # Default
)
```

### 2. Dashboard

**Snapshot Monitor:**
```python
from empirica.dashboard.snapshot_monitor import SnapshotMonitor
from empirica.auto_tracker import EmpericaTracker

# Dashboard uses tracker for real-time monitoring
monitor = SnapshotMonitor()
monitor.start()  # Reads from EmpericaTracker
```

### 3. Modality Switcher

**Snapshot Provider:**
```python
from empirica.plugins.modality_switcher.snapshot_provider import SnapshotProvider
from empirica.auto_tracker import EmpericaTracker

# Modality switcher accesses snapshots for context
provider = SnapshotProvider()
snapshot = provider.get_latest_snapshot()
```

---

## API Reference

### EmpericaTracker

```python
class EmpericaTracker:
    """
    Automatic session and cascade tracking
    
    Singleton pattern - use get_instance()
    """
    
    @classmethod
    def get_instance(cls) -> 'EmpericaTracker':
        """Get singleton tracker instance"""
        pass
    
    def track_session_start(
        self,
        session_id: str,
        ai_id: str,
        context: Optional[Dict] = None
    ) -> None:
        """
        Track session start
        
        Args:
            session_id: Unique session identifier
            ai_id: AI agent identifier
            context: Optional session context
        """
        pass
    
    def track_cascade_start(
        self,
        cascade_id: str,
        task: str,
        context: Optional[Dict] = None
    ) -> None:
        """
        Track CASCADE execution start
        
        Args:
            cascade_id: Unique cascade identifier
            task: Task description
            context: Task context
        """
        pass
    
    def track_assessment(
        self,
        phase: str,
        assessment: 'EpistemicAssessment'
    ) -> None:
        """
        Track epistemic assessment
        
        Args:
            phase: CASCADE phase (preflight, check, postflight)
            assessment: Epistemic assessment snapshot
        """
        pass
    
    def get_session_history(
        self,
        session_id: str
    ) -> List[Dict]:
        """
        Get session history
        
        Returns:
            List of session events in chronological order
        """
        pass
    
    def get_latest_snapshot(self) -> Optional[Dict]:
        """
        Get latest epistemic snapshot
        
        Returns:
            Most recent assessment snapshot or None
        """
        pass
```

---

## Usage Patterns

### Pattern 1: Automatic Tracking (Default)

No code needed - tracking happens automatically:

```python
from empirica.core.metacognitive_cascade import run_canonical_cascade

# Tracking happens automatically
result = await run_canonical_cascade(
    task="Review security module",
    context={'cwd': '/project'}
)

# Access tracked data
from empirica.auto_tracker import EmpericaTracker
tracker = EmpericaTracker.get_instance()
history = tracker.get_session_history(result.session_id)
```

### Pattern 2: Manual Tracking

For custom workflows:

```python
from empirica.auto_tracker import EmpericaTracker
import uuid

tracker = EmpericaTracker.get_instance()

# Track custom session
session_id = str(uuid.uuid4())
tracker.track_session_start(
    session_id=session_id,
    ai_id='claude',
    context={'workflow': 'custom'}
)

# Track cascade
cascade_id = str(uuid.uuid4())
tracker.track_cascade_start(
    cascade_id=cascade_id,
    task="Custom analysis",
    context={'domain': 'research'}
)

# Track assessments
tracker.track_assessment('preflight', preflight_assessment)
tracker.track_assessment('check', check_assessment)
tracker.track_assessment('postflight', postflight_assessment)
```

### Pattern 3: Snapshot Access

Access real-time snapshots:

```python
from empirica.auto_tracker import EmpericaTracker

tracker = EmpericaTracker.get_instance()

# Get latest snapshot
snapshot = tracker.get_latest_snapshot()
if snapshot:
    print(f"Phase: {snapshot['phase']}")
    print(f"Confidence: {snapshot['overall_confidence']}")
    print(f"Gaps: {snapshot['gaps']}")
```

---

## Tracked Data

### Session Events

```python
{
    'event_type': 'session_start',
    'timestamp': '2025-11-13T20:00:00Z',
    'session_id': 'uuid',
    'ai_id': 'claude',
    'context': {'workflow': 'production'}
}
```

### CASCADE Events

```python
{
    'event_type': 'cascade_start',
    'timestamp': '2025-11-13T20:01:00Z',
    'cascade_id': 'uuid',
    'task': 'Review authentication module',
    'context': {'cwd': '/project', 'domain': 'code_analysis'}
}
```

### Assessment Snapshots

```python
{
    'event_type': 'assessment',
    'timestamp': '2025-11-13T20:02:00Z',
    'phase': 'preflight',
    'assessment': {
        'overall_confidence': 0.75,
        'engagement': 0.85,
        'vectors': {
            'know': {'score': 0.8, 'rationale': '...'},
            'do': {'score': 0.7, 'rationale': '...'},
            # ... all 13 vectors
        },
        'gaps': [
            {'vector': 'context', 'score': 0.6, 'rationale': '...'}
        ]
    }
}
```

---

## Dashboard Integration

### Real-Time Monitoring

The tracker enables real-time dashboard monitoring:

```python
from empirica.dashboard.snapshot_monitor import SnapshotMonitor

monitor = SnapshotMonitor()
monitor.start()  # Monitors EmpericaTracker

# Dashboard shows:
# - Current session status
# - Live epistemic state
# - CASCADE progress
# - Confidence trends
```

### TMUX Integration

```bash
# Start dashboard with auto-tracking
empirica dashboard start --mode tmux

# Dashboard automatically connects to EmpericaTracker
# Shows real-time CASCADE execution
```

---

## Storage

### Default Location

**Tracked Data:** `.empirica/tracking/`

```
.empirica/tracking/
├── sessions.db          # Session metadata
├── cascades.db          # CASCADE executions
└── snapshots/           # Epistemic snapshots
    ├── 2025-11-13/
    │   ├── session_abc.json
    │   └── session_def.json
    └── 2025-11-14/
```

### Custom Storage

```python
from empirica.auto_tracker import EmpericaTracker

tracker = EmpericaTracker.get_instance()
tracker.configure(storage_path='/custom/path/tracking')
```

---

## Query Examples

### Get Session History

```python
from empirica.auto_tracker import EmpericaTracker

tracker = EmpericaTracker.get_instance()

# Get all events for session
history = tracker.get_session_history('session-123')

# Filter by event type
cascades = [e for e in history if e['event_type'] == 'cascade_start']
assessments = [e for e in history if e['event_type'] == 'assessment']

# Get assessments for specific phase
preflight = [a for a in assessments if a['phase'] == 'preflight']
```

### Analyze Confidence Trends

```python
history = tracker.get_session_history('session-123')
assessments = [e for e in history if e['event_type'] == 'assessment']

# Extract confidence over time
confidence_trend = [
    (e['timestamp'], e['assessment']['overall_confidence'])
    for e in assessments
]

# Plot or analyze
for timestamp, confidence in confidence_trend:
    print(f"{timestamp}: {confidence:.2f}")
```

### Find Problematic Sessions

```python
# Get all sessions with low confidence
tracker = EmpericaTracker.get_instance()
all_sessions = tracker.get_all_sessions()

low_confidence_sessions = []
for session in all_sessions:
    history = tracker.get_session_history(session['session_id'])
    assessments = [e for e in history if e['event_type'] == 'assessment']
    
    if any(a['assessment']['overall_confidence'] < 0.6 for a in assessments):
        low_confidence_sessions.append(session)

print(f"Found {len(low_confidence_sessions)} sessions with low confidence")
```

---

## Performance

### Minimal Overhead

- Tracking is asynchronous (non-blocking)
- Snapshots compressed automatically
- Automatic cleanup of old data (configurable retention)

### Configuration

```python
tracker = EmpericaTracker.get_instance()

# Configure retention
tracker.configure(
    retention_days=30,        # Keep 30 days of history
    snapshot_compression=True, # Compress snapshots
    async_tracking=True       # Non-blocking (default)
)
```

---

## Best Practices

### 1. Let It Track Automatically

```python
# Good - automatic tracking
result = await run_canonical_cascade(task, context)

# Unnecessary - manual tracking for standard CASCADE
tracker.track_cascade_start(...)  # Already done automatically
```

### 2. Use Snapshots for Real-Time Monitoring

```python
# Good - real-time access
snapshot = tracker.get_latest_snapshot()

# Avoid - querying database repeatedly
for i in range(100):
    history = tracker.get_session_history(session_id)  # Expensive
```

### 3. Clean Up Old Data

```python
# Periodic cleanup (run daily/weekly)
tracker.cleanup_old_data(days=30)
```

---

## CLI Commands

### View Tracked Sessions

```bash
# List recent sessions
empirica sessions list --limit 10

# Show session details
empirica sessions show <session-id>

# Export session data
empirica sessions export <session-id> --output session.json
```

### Monitor Live

```bash
# Start monitoring
empirica monitor start

# View latest snapshot
empirica monitor snapshot

# Watch real-time
empirica monitor watch
```

---

## Troubleshooting

### No Data Being Tracked

**Check:**
```python
tracker = EmpericaTracker.get_instance()
is_enabled = tracker.is_enabled()
print(f"Tracking enabled: {is_enabled}")
```

**Solution:**
```python
# Explicitly enable
tracker.enable()
```

### High Disk Usage

**Check storage:**
```bash
du -sh .empirica/tracking/
```

**Solution:**
```python
# Cleanup old data
tracker.cleanup_old_data(days=7)  # Keep only 1 week
```

---

## See Also

- `docs/reference/CASCADE_WORKFLOW.md` - CASCADE documentation
- `docs/reference/DASHBOARD_MONITORING.md` - Dashboard integration
- `empirica/auto_tracker.py` - Source code
- `LEGACY_COMPONENTS_ASSESSMENT.md` - Component analysis

---

**Status:** Production Active ✅  
**Used In:** Bootstraps, Dashboard, Modality Switcher  
**Maintained:** Yes  
**Documented:** 2025-11-13
