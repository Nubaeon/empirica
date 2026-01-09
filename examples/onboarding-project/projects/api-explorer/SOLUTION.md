# Solution - API Explorer

**SPOILERS BELOW**

---

## Complete API Reference

The TaskFlow API has **5 endpoints** (only 2 documented):

| Endpoint | Method | Documented? | Purpose |
|----------|--------|-------------|---------|
| `/tasks` | GET | Yes | List all tasks |
| `/tasks` | POST | Yes | Create task |
| `/tasks/<id>` | GET | No | Get single task |
| `/tasks/<id>` | PUT | No | Update task |
| `/tasks/<id>` | DELETE | No | Delete task |
| `/stats` | GET | No | Task statistics |
| `/tags` | GET | No | List unique tags |

---

## Undocumented Features

### Query Parameters on GET /tasks

```bash
# Filter by status
curl "http://localhost:5050/tasks?status=pending"

# Filter by priority
curl "http://localhost:5050/tasks?priority=high"
```

### Additional Fields

Tasks have more fields than documented:

```json
{
  "id": 1,
  "title": "Example",
  "status": "pending",
  "priority": "high",      // Undocumented
  "tags": ["learning"]     // Undocumented
}
```

### POST /tasks Accepts More

```bash
curl -X POST http://localhost:5050/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "New task", "priority": "high", "tags": ["urgent"]}'
```

---

## Full Endpoint Details

### GET /stats

Returns aggregate statistics:

```json
{
  "total": 3,
  "by_status": {
    "pending": 1,
    "in_progress": 1,
    "completed": 1
  },
  "by_priority": {
    "high": 1,
    "medium": 1,
    "low": 1
  }
}
```

### GET /tags

Returns all unique tags across tasks:

```json
{
  "tags": ["dev", "learning", "onboarding"]
}
```

---

## The Epistemic Journey

| Phase | Know | Uncertainty | What You Discovered |
|-------|------|-------------|---------------------|
| Start | 0.2 | 0.8 | Only 2 documented endpoints |
| After testing docs | 0.4 | 0.6 | Extra fields in responses |
| After CRUD discovery | 0.6 | 0.4 | Full CRUD on /tasks/<id> |
| After utility endpoints | 0.8 | 0.2 | /stats and /tags exist |
| After query params | 0.9 | 0.1 | Filtering support |
