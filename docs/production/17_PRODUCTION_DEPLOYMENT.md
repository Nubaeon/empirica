# Production Deployment Guide

**Empirica v2.0 - Deploying to Production**

---

## Pre-Deployment Checklist

- [ ] Python 3.8+ installed
- [ ] All dependencies tested (`pip install -r requirements.txt`)
- [ ] Bootstrap level selected (recommend: 2)
- [ ] Configuration validated
- [ ] Tests passing
- [ ] Documentation reviewed

---

## Configuration

### Environment Variables

```bash
# .env file
EMPIRICA_BOOTSTRAP_LEVEL=2
EMPIRICA_CONFIDENCE_THRESHOLD=0.75
EMPIRICA_MAX_INVESTIGATION_ROUNDS=3
EMPIRICA_DB_PATH=/var/lib/empirica/sessions.db
EMPIRICA_ENABLE_DASHBOARD=false
EMPIRICA_LOG_LEVEL=INFO

# Optional: LLM config
OLLAMA_URL=http://localhost:11434
OPENAI_API_KEY=your_key_here
```

### Load Configuration

```python
import os
from empirica.bootstraps import ExtendedMetacognitiveBootstrap
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

bootstrap_level = os.getenv('EMPIRICA_BOOTSTRAP_LEVEL', '2')
confidence = float(os.getenv('EMPIRICA_CONFIDENCE_THRESHOLD', '0.70'))
db_path = os.getenv('EMPIRICA_DB_PATH', '.empirica/sessions/sessions.db')

bootstrap = ExtendedMetacognitiveBootstrap(level=bootstrap_level)
components = bootstrap.bootstrap()

cascade = CanonicalEpistemicCascade(
    action_confidence_threshold=confidence,
    enable_action_hooks=False,  # Disable tmux in production
    enable_session_db=True
)
```

---

## Deployment Options

### Option 1: Containerized (Docker)

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Empirica
COPY empirica/ /app/empirica/

# Create data directory
RUN mkdir -p /app/.empirica/sessions

# Environment
ENV PYTHONPATH=/app
ENV EMPIRICA_BOOTSTRAP_LEVEL=2

# Run
CMD ["python3", "your_app.py"]
```

```bash
# Build
docker build -t empirica-app .

# Run
docker run -v empirica_data:/app/.empirica empirica-app
```

### Option 2: Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: empirica-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: empirica
  template:
    metadata:
      labels:
        app: empirica
    spec:
      containers:
      - name: empirica
        image: empirica-app:latest
        env:
        - name: EMPIRICA_BOOTSTRAP_LEVEL
          value: "2"
        - name: EMPIRICA_ENABLE_DASHBOARD
          value: "false"
        volumeMounts:
        - name: empirica-data
          mountPath: /app/.empirica
      volumes:
      - name: empirica-data
        persistentVolumeClaim:
          claimName: empirica-pvc
```

### Option 3: Serverless (AWS Lambda)

```python
# lambda_handler.py
import asyncio
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

# Initialize once (cold start)
bootstrap = ExtendedMetacognitiveBootstrap(level="2")
components = bootstrap.bootstrap()
cascade = components['canonical_cascade']

def lambda_handler(event, context):
    task = event['task']
    cascade_context = event.get('context', {})
    
    result = asyncio.run(
        cascade.run_epistemic_cascade(task, cascade_context)
    )
    
    return {
        'statusCode': 200,
        'body': result
    }
```

---

## Performance Optimization

### 1. Bootstrap Level Selection

```python
# Development: Level 2 (30 components, full features)
bootstrap = ExtendedMetacognitiveBootstrap(level="2")

# Production: Level 2 (recommended)
bootstrap = ExtendedMetacognitiveBootstrap(level="2")

# High-performance: Level 1 (25 components, faster but no parallel reasoning)
# Note: Level 1 has limitations, use with caution
bootstrap = ExtendedMetacognitiveBootstrap(level="1")

# Minimal testing: Level 0 (14 components, fastest)
bootstrap = ExtendedMetacognitiveBootstrap(level="0")
```

**Recommendation:** Use **Level 2** for production (0.17s bootstrap, full features).

### 2. Investigation Limits

```python
cascade = CanonicalEpistemicCascade(
    max_investigation_rounds=2,  # Limit rounds (default: 3)
    action_confidence_threshold=0.70  # Adjust threshold
)
```

### 3. Database Optimization

```python
from empirica.data import SessionDatabase

# Use connection pooling
db = SessionDatabase(db_path='/fast/ssd/sessions.db')

# Batch operations
session_id = db.create_session(...)
cascade_ids = [db.create_cascade(...) for _ in range(10)]

# Close connections
db.close()
```

### 4. Disable Optional Features

```python
cascade = CanonicalEpistemicCascade(
    enable_action_hooks=False,      # No tmux in production
    enable_drift_monitor=False,     # Disable if not needed
    enable_bayesian=True            # Keep for precision-critical
)
```

---

## Monitoring & Observability

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/empirica/app.log'),
        logging.StreamHandler()
    ]
)

# Use in cascade
logger = logging.getLogger('empirica')
logger.info(f"Cascade started: {task}")
```

### Metrics

```python
import time
from prometheus_client import Counter, Histogram

# Define metrics
cascade_count = Counter('empirica_cascades_total', 'Total cascades')
cascade_duration = Histogram('empirica_cascade_duration_seconds', 'Cascade duration')
investigation_rounds = Histogram('empirica_investigation_rounds', 'Investigation rounds')

# Track metrics
@cascade_duration.time()
async def run_tracked_cascade(task, context):
    cascade_count.inc()
    result = await cascade.run_epistemic_cascade(task, context)
    investigation_rounds.observe(result['investigation_rounds'])
    return result
```

### Health Checks

```python
# health.py
async def health_check():
    try:
        # Test bootstrap
        bootstrap = ExtendedMetacognitiveBootstrap(level="0")
        components = bootstrap.bootstrap()
        
        # Test database
        db = SessionDatabase()
        db.close()
        
        return {'status': 'healthy', 'components': len(components)}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}
```

---

## Security

### 1. Secure Database

```python
# Use encrypted database
db = SessionDatabase('/encrypted/volume/sessions.db')

# Set proper permissions
chmod 600 /encrypted/volume/sessions.db
```

### 2. API Keys

```python
# Never hardcode keys
import os

api_key = os.getenv('API_KEY')  # From environment
# OR
from secrets_manager import get_secret
api_key = get_secret('empirica/api_key')
```

### 3. Input Validation

```python
def validate_input(task: str, context: dict) -> bool:
    # Validate task
    if not task or len(task) > 10000:
        raise ValueError("Invalid task")
    
    # Validate context
    if not isinstance(context, dict):
        raise ValueError("Invalid context")
    
    return True

# Use before cascade
validate_input(task, context)
result = await cascade.run_epistemic_cascade(task, context)
```

---

## Scaling

### Horizontal Scaling

```python
# Stateless cascade instances
# Can scale horizontally without issues
# Database handles concurrency

# Use load balancer
# nginx, ALB, etc.
```

### Database Scaling

```python
# Option 1: Separate read/write
db_write = SessionDatabase('/primary/sessions.db')
db_read = SessionDatabase('/replica/sessions.db')

# Option 2: Partition by session
def get_db_for_session(session_id):
    shard = hash(session_id) % NUM_SHARDS
    return SessionDatabase(f'/data/shard_{shard}/sessions.db')
```

---

## Backup & Recovery

### Database Backup

```bash
# Daily backup
#!/bin/bash
DATE=$(date +%Y%m%d)
sqlite3 .empirica/sessions/sessions.db ".backup '/backups/sessions_${DATE}.db'"

# Retention (keep 30 days)
find /backups -name "sessions_*.db" -mtime +30 -delete
```

### Restore

```bash
# Restore from backup
cp /backups/sessions_20251028.db .empirica/sessions/sessions.db
```

---

## Troubleshooting Production

### High Memory Usage

```python
# Close connections
db.close()

# Limit investigation rounds
cascade = CanonicalEpistemicCascade(max_investigation_rounds=1)

# Use lower bootstrap level
bootstrap = ExtendedMetacognitiveBootstrap(level="1")
```

### Slow Performance

```python
# Add timeout
import asyncio

try:
    result = await asyncio.wait_for(
        cascade.run_epistemic_cascade(task, context),
        timeout=30.0
    )
except asyncio.TimeoutError:
    # Handle timeout
    pass
```

### Database Lock Errors

```python
# Use connection pooling
# Ensure proper closing
try:
    db = SessionDatabase()
    # operations
finally:
    db.close()
```

---

## Production Checklist

### Before Deployment:
- [ ] Tests passing
- [ ] Bootstrap level = 2
- [ ] Dashboard disabled
- [ ] Database path configured
- [ ] Logging configured
- [ ] Health checks working
- [ ] Monitoring enabled

### After Deployment:
- [ ] Health check passes
- [ ] Metrics collecting
- [ ] Logs flowing
- [ ] Database accessible
- [ ] Performance acceptable
- [ ] Error rate acceptable

---

## Example Production Setup

```python
# production_app.py
import os
import asyncio
import logging
from empirica.bootstraps import ExtendedMetacognitiveBootstrap
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
from empirica.data import SessionDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('empirica')

# Load config
CONFIG = {
    'bootstrap_level': os.getenv('EMPIRICA_BOOTSTRAP_LEVEL', '2'),
    'confidence_threshold': float(os.getenv('EMPIRICA_CONFIDENCE_THRESHOLD', '0.70')),
    'max_rounds': int(os.getenv('EMPIRICA_MAX_ROUNDS', '3')),
    'db_path': os.getenv('EMPIRICA_DB_PATH', '.empirica/sessions/sessions.db')
}

# Initialize (once)
logger.info("Initializing Empirica...")
bootstrap = ExtendedMetacognitiveBootstrap(level=CONFIG['bootstrap_level'])
components = bootstrap.bootstrap()

cascade = CanonicalEpistemicCascade(
    action_confidence_threshold=CONFIG['confidence_threshold'],
    max_investigation_rounds=CONFIG['max_rounds'],
    enable_action_hooks=False,
    enable_session_db=True
)

db = SessionDatabase(CONFIG['db_path'])

async def process_task(task: str, context: dict) -> dict:
    """Process task with Empirica"""
    logger.info(f"Processing task: {task[:50]}...")
    
    try:
        result = await cascade.run_epistemic_cascade(task, context)
        logger.info(f"Task completed: {result['action']}, confidence: {result['confidence']:.2f}")
        return result
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise

# Cleanup on shutdown
def shutdown():
    logger.info("Shutting down...")
    db.close()
```

---

## Next Steps

- **Monitoring:** Set up metrics and alerts
- **Scaling:** Add load balancing
- **Security:** Review and harden
- **Documentation:** Keep deployment docs updated

---

**Production-ready deployment with monitoring and security!** 🚀
