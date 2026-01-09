# TaskFlow API Documentation

**Version:** 1.0 | **Base URL:** http://localhost:5050

## Overview

TaskFlow is a simple task management API. This documentation covers the core endpoints.

---

## Endpoints

### GET /tasks

List all tasks.

**Response:**
```json
[
  {"id": 1, "title": "Example task", "status": "pending"}
]
```

### POST /tasks

Create a new task.

**Body:**
```json
{"title": "My task"}
```

**Response:**
```json
{"id": 2, "title": "My task", "status": "pending"}
```

---

## Notes

- Tasks have `id`, `title`, and `status` fields
- Status can be: `pending`, `in_progress`, `completed`
- More endpoints may exist (documentation in progress)
