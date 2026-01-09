# API Explorer Walkthrough

Discover an API while tracking your epistemic journey.

---

## Step 1: PREFLIGHT - Honest Starting Point

```bash
empirica session-create --ai-id claude-code --output json

empirica preflight-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "task_context": "Integrate with TaskFlow API using incomplete docs",
  "vectors": {
    "know": 0.2,
    "uncertainty": 0.8,
    "context": 0.3,
    "clarity": 0.4
  },
  "reasoning": "Only docs show GET /tasks and POST /tasks. Don't know what other endpoints exist, what query params work, or full data schema."
}
EOF
```

---

## Step 2: Start the Server

```bash
python api_server.py
```

Keep this running in a separate terminal.

---

## Step 3: Explore Documented Endpoints

Test what the docs say works:

```bash
# List tasks
curl http://localhost:5050/tasks

# Create a task
curl -X POST http://localhost:5050/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task"}'
```

Log your findings:

```bash
empirica finding-log --session-id <ID> \
  --finding "GET /tasks returns array with id, title, status fields. Also seeing priority and tags fields not in docs!" \
  --impact 0.4
```

---

## Step 4: Hunt for Hidden Endpoints

Try common REST patterns:

```bash
# Does single-task retrieval work?
curl http://localhost:5050/tasks/1

# What about update?
curl -X PUT http://localhost:5050/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# Delete?
curl -X DELETE http://localhost:5050/tasks/2
```

Log discoveries:

```bash
empirica finding-log --session-id <ID> \
  --finding "Discovered: GET/PUT/DELETE /tasks/<id> all work! Full CRUD support." \
  --impact 0.6

empirica unknown-log --session-id <ID> \
  --unknown "Are there any other top-level endpoints beyond /tasks?"
```

---

## Step 5: Discover Utility Endpoints

Keep exploring:

```bash
# Try common endpoint patterns
curl http://localhost:5050/stats
curl http://localhost:5050/tags
curl http://localhost:5050/health  # This one 404s
```

```bash
empirica finding-log --session-id <ID> \
  --finding "Found /stats endpoint - returns counts by status and priority. Also /tags lists all unique tags." \
  --impact 0.5

empirica unknown-resolve --unknown-id <ID> \
  --resolved-by "Found 2 utility endpoints: /stats and /tags"
```

---

## Step 6: Test Query Parameters

```bash
# Try filtering
curl "http://localhost:5050/tasks?status=pending"
curl "http://localhost:5050/tasks?priority=high"
```

```bash
empirica finding-log --session-id <ID> \
  --finding "GET /tasks supports ?status= and ?priority= query params for filtering" \
  --impact 0.4
```

---

## Step 7: POSTFLIGHT - Measure Learning

```bash
empirica postflight-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "task_context": "Fully mapped TaskFlow API - 5 endpoints discovered",
  "vectors": {
    "know": 0.90,
    "uncertainty": 0.10,
    "context": 0.85,
    "clarity": 0.90
  },
  "reasoning": "Discovered all endpoints: CRUD on /tasks, plus /stats and /tags. Found undocumented query params and fields. Ready to build integration."
}
EOF
```

**Learning delta:** know +0.70, uncertainty -0.70

---

## Key Epistemic Lessons

1. **Docs are often incomplete** - Real APIs frequently have undocumented features
2. **Pattern recognition** - REST conventions help predict endpoints
3. **Incremental discovery** - Each test builds confidence
4. **Log as you go** - Findings capture knowledge for future reference
