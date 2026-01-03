# Empirica REST API Reference

**Version:** 1.2.3
**Base URL:** `http://localhost:5000/api/v1`
**Generated:** 2026-01-03

---

## Overview

Empirica provides a REST API for integrating epistemic tracking into web applications, dashboards, and external tools. The API follows RESTful conventions with JSON responses.

### Authentication

Currently, the API runs locally without authentication. For production deployments, configure authentication via environment variables or reverse proxy.

### Response Format

All endpoints return JSON with consistent structure:

```json
{
  "ok": true,
  "data": { ... },
  "error": null
}
```

Error responses:
```json
{
  "ok": false,
  "data": null,
  "error": "Error message"
}
```

---

## Endpoints

### Health Check

#### `GET /health`

Check API server health.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.2.3",
  "timestamp": "2026-01-03T12:00:00Z"
}
```

---

## Dashboard

### Get Session Dashboard

#### `GET /api/v1/sessions/<session_id>/dashboard`

Get comprehensive dashboard data for a session including vectors, goals, and activity.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID |

**Response:**
```json
{
  "ok": true,
  "data": {
    "session_id": "abc-123",
    "ai_id": "claude-code",
    "status": "active",
    "vectors": {
      "current": {"know": 0.8, "uncertainty": 0.2},
      "preflight": {"know": 0.5, "uncertainty": 0.5},
      "delta": {"know": 0.3, "uncertainty": -0.3}
    },
    "goals": {
      "active": 2,
      "completed": 5,
      "blocked": 0
    },
    "activity": {
      "findings": 8,
      "unknowns": 3,
      "checks": 2
    },
    "moon_phase": "🌕",
    "health": "excellent"
  }
}
```

---

### Execute Session Command

#### `POST /api/v1/sessions/<session_id>/command`

Execute a command within a session context.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID |

**Request Body:**
```json
{
  "command": "finding-log",
  "args": {
    "finding": "Discovered auth token refresh pattern",
    "impact": 0.7
  }
}
```

**Response:**
```json
{
  "ok": true,
  "data": {
    "command": "finding-log",
    "result": {
      "finding_id": "find-456",
      "status": "logged"
    },
    "execution_time_ms": 45
  }
}
```

**Supported Commands:**
- `finding-log` - Log a finding
- `unknown-log` - Log an unknown
- `check-submit` - Submit CHECK assessment
- `goal-complete` - Complete a goal

---

## Sessions

### List Sessions

#### `GET /api/v1/sessions`

List all sessions with optional filtering and pagination.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ai_id` | string | Filter by AI identifier |
| `project_id` | string | Filter by project UUID |
| `status` | string | Filter by status (active, completed, abandoned) |
| `limit` | int | Max results (default: 50) |
| `offset` | int | Pagination offset |

**Response:**
```json
{
  "ok": true,
  "data": {
    "sessions": [
      {
        "session_id": "abc-123",
        "ai_id": "claude-code",
        "project_id": "proj-456",
        "status": "active",
        "created_at": "2026-01-03T10:00:00Z",
        "last_activity": "2026-01-03T11:30:00Z"
      }
    ],
    "total": 42,
    "limit": 50,
    "offset": 0
  }
}
```

---

### Get Session Details

#### `GET /api/v1/sessions/<session_id>`

Get detailed information for a specific session.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID |

**Response:**
```json
{
  "ok": true,
  "data": {
    "session_id": "abc-123",
    "ai_id": "claude-code",
    "project_id": "proj-456",
    "status": "active",
    "created_at": "2026-01-03T10:00:00Z",
    "vectors": {
      "know": 0.75,
      "uncertainty": 0.25,
      "context": 0.8,
      "do": 0.7
    },
    "cascade_phases": ["PREFLIGHT", "CHECK"],
    "findings_count": 5,
    "unknowns_count": 2
  }
}
```

---

### Get Session Checks

#### `GET /api/v1/sessions/<session_id>/checks`

Get all CHECK gate assessments for a session.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID |

**Response:**
```json
{
  "ok": true,
  "data": {
    "checks": [
      {
        "check_id": "chk-789",
        "timestamp": "2026-01-03T10:30:00Z",
        "decision": "PROCEED",
        "vectors": {
          "know": 0.7,
          "uncertainty": 0.3
        },
        "reasoning": "Sufficient knowledge to proceed"
      }
    ]
  }
}
```

---

## Epistemic Deltas

### Get Session Deltas

#### `GET /api/v1/sessions/<session_id>/deltas`

Get epistemic deltas (learning measurement) between PREFLIGHT and POSTFLIGHT.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID |

**Response:**
```json
{
  "ok": true,
  "data": {
    "session_id": "abc-123",
    "preflight": {
      "know": 0.5,
      "uncertainty": 0.6,
      "timestamp": "2026-01-03T10:00:00Z"
    },
    "postflight": {
      "know": 0.8,
      "uncertainty": 0.2,
      "timestamp": "2026-01-03T12:00:00Z"
    },
    "deltas": {
      "know": 0.3,
      "uncertainty": -0.4
    },
    "learning_summary": "Significant knowledge gain with reduced uncertainty"
  }
}
```

---

### Get Commit Epistemic State

#### `GET /api/v1/commits/<commit_sha>/epistemic`

Get epistemic state at a specific git commit.

**Status:** Stub implementation - returns placeholder data

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `commit_sha` | string | Git commit SHA |

**Response:**
```json
{
  "ok": true,
  "data": {
    "commit_sha": "abc123def",
    "epistemic_state": {
      "know": 0.7,
      "uncertainty": 0.3
    },
    "note": "Stub implementation - full git notes integration pending"
  }
}
```

---

## Verification

### Verify Checkpoint Signature

#### `GET /api/v1/checkpoints/<session_id>/<phase>/<round>/verify`

Verify cryptographic signature of an epistemic checkpoint.

**Status:** Stub implementation

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID |
| `phase` | string | CASCADE phase (PREFLIGHT, CHECK, POSTFLIGHT) |
| `round` | int | Round number |

**Response:**
```json
{
  "ok": true,
  "data": {
    "verified": true,
    "signer": "claude-code",
    "timestamp": "2026-01-03T10:00:00Z",
    "note": "Stub implementation"
  }
}
```

---

### List Session Signatures

#### `GET /api/v1/sessions/<session_id>/signatures`

List all cryptographic signatures for a session.

**Status:** Stub implementation

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `session_id` | string | Session UUID |

**Response:**
```json
{
  "ok": true,
  "data": {
    "signatures": [],
    "note": "Stub implementation"
  }
}
```

---

## Heatmaps & Analysis

### Get File Uncertainty

#### `GET /api/v1/files/<filepath>/uncertainty`

Get uncertainty metrics for a specific file.

**Status:** Stub implementation

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `filepath` | string | URL-encoded file path |

**Response:**
```json
{
  "ok": true,
  "data": {
    "filepath": "src/main.py",
    "uncertainty": 0.4,
    "last_assessed": "2026-01-03T10:00:00Z",
    "note": "Stub implementation"
  }
}
```

---

### Get Module Epistemic Map

#### `GET /api/v1/modules/<module_name>/epistemic`

Get epistemic assessment for a code module.

**Status:** Stub implementation

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `module_name` | string | Module name |

**Response:**
```json
{
  "ok": true,
  "data": {
    "module": "empirica.core",
    "know": 0.8,
    "coverage": 0.95,
    "note": "Stub implementation"
  }
}
```

---

## AI Comparison

### Get AI Learning Curve

#### `GET /api/v1/ai/<ai_id>/learning-curve`

Get learning trajectory for a specific AI.

**Status:** Stub implementation

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ai_id` | string | AI identifier |

**Response:**
```json
{
  "ok": true,
  "data": {
    "ai_id": "claude-code",
    "sessions_analyzed": 10,
    "trajectory": [],
    "note": "Stub implementation"
  }
}
```

---

### Compare AIs

#### `GET /api/v1/compare-ais`

Compare epistemic performance across multiple AIs.

**Status:** Stub implementation

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `ai_ids` | string | Comma-separated AI identifiers |

**Response:**
```json
{
  "ok": true,
  "data": {
    "comparison": [],
    "note": "Stub implementation"
  }
}
```

---

## Implementation Status

| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /health` | Functional | Basic health check |
| `GET /sessions` | Functional | Full filtering/pagination |
| `GET /sessions/<id>` | Functional | Full session details |
| `GET /sessions/<id>/checks` | Functional | CHECK assessments |
| `GET /sessions/<id>/deltas` | Functional | Learning measurement |
| `GET /commits/<sha>/epistemic` | Stub | Needs git notes integration |
| `GET /checkpoints/.../verify` | Stub | Needs crypto verification |
| `GET /sessions/<id>/signatures` | Stub | Needs signature tracking |
| `GET /files/<path>/uncertainty` | Stub | Needs file analysis |
| `GET /modules/<name>/epistemic` | Stub | Needs module analysis |
| `GET /ai/<id>/learning-curve` | Stub | Needs trajectory analysis |
| `GET /compare-ais` | Stub | Needs multi-AI comparison |

---

## Running the API Server

```bash
# Start the API server
empirica api --port 5000

# Or with Flask directly
cd empirica && flask run --port 5000
```

---

## See Also

- [CLI Commands Reference](../CLI_COMMANDS_UNIFIED.md)
- [MCP Server Reference](../MCP_SERVER_REFERENCE.md)
- [Database Schema](../DATABASE_SCHEMA_UNIFIED.md)
