#!/usr/bin/env python3
"""
TaskFlow API Server - A mock API for learning API exploration.

Some endpoints are documented, some are not.
Start with: python api_server.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs

# In-memory task storage
tasks = [
    {"id": 1, "title": "Learn Empirica", "status": "in_progress", "priority": "high", "tags": ["learning"]},
    {"id": 2, "title": "Explore API", "status": "pending", "priority": "medium", "tags": ["onboarding"]},
    {"id": 3, "title": "Write tests", "status": "completed", "priority": "low", "tags": ["dev"]},
]
next_id = 4


class TaskHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _parse_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def do_GET(self):
        global tasks
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # DOCUMENTED: GET /tasks - list all tasks
        if path == "/tasks":
            result = tasks
            # UNDOCUMENTED: ?status=X filters by status
            if "status" in query:
                result = [t for t in result if t["status"] == query["status"][0]]
            # UNDOCUMENTED: ?priority=X filters by priority
            if "priority" in query:
                result = [t for t in result if t.get("priority") == query["priority"][0]]
            self._send_json(result)

        # UNDOCUMENTED: GET /tasks/<id> - get single task
        elif path.startswith("/tasks/") and path.count("/") == 2:
            try:
                task_id = int(path.split("/")[2])
                task = next((t for t in tasks if t["id"] == task_id), None)
                if task:
                    self._send_json(task)
                else:
                    self._send_json({"error": "Task not found"}, 404)
            except ValueError:
                self._send_json({"error": "Invalid task ID"}, 400)

        # UNDOCUMENTED: GET /stats - task statistics
        elif path == "/stats":
            stats = {
                "total": len(tasks),
                "by_status": {},
                "by_priority": {}
            }
            for t in tasks:
                s = t["status"]
                p = t.get("priority", "none")
                stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
                stats["by_priority"][p] = stats["by_priority"].get(p, 0) + 1
            self._send_json(stats)

        # UNDOCUMENTED: GET /tags - list all unique tags
        elif path == "/tags":
            all_tags = set()
            for t in tasks:
                all_tags.update(t.get("tags", []))
            self._send_json({"tags": sorted(all_tags)})

        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        global tasks, next_id
        path = urlparse(self.path).path

        # DOCUMENTED: POST /tasks - create task
        if path == "/tasks":
            body = self._parse_body()
            if not body.get("title"):
                self._send_json({"error": "Title required"}, 400)
                return
            task = {
                "id": next_id,
                "title": body["title"],
                "status": "pending",
                "priority": body.get("priority", "medium"),  # UNDOCUMENTED field
                "tags": body.get("tags", [])  # UNDOCUMENTED field
            }
            next_id += 1
            tasks.append(task)
            self._send_json(task, 201)

        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def do_PUT(self):
        global tasks
        path = urlparse(self.path).path

        # UNDOCUMENTED: PUT /tasks/<id> - update task
        if path.startswith("/tasks/") and path.count("/") == 2:
            try:
                task_id = int(path.split("/")[2])
                task = next((t for t in tasks if t["id"] == task_id), None)
                if not task:
                    self._send_json({"error": "Task not found"}, 404)
                    return
                body = self._parse_body()
                for key in ["title", "status", "priority", "tags"]:
                    if key in body:
                        task[key] = body[key]
                self._send_json(task)
            except ValueError:
                self._send_json({"error": "Invalid task ID"}, 400)
        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def do_DELETE(self):
        global tasks
        path = urlparse(self.path).path

        # UNDOCUMENTED: DELETE /tasks/<id> - delete task
        if path.startswith("/tasks/") and path.count("/") == 2:
            try:
                task_id = int(path.split("/")[2])
                idx = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
                if idx is not None:
                    deleted = tasks.pop(idx)
                    self._send_json({"deleted": deleted})
                else:
                    self._send_json({"error": "Task not found"}, 404)
            except ValueError:
                self._send_json({"error": "Invalid task ID"}, 400)
        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[API] {args[0]}")


if __name__ == "__main__":
    PORT = 5050
    print(f"TaskFlow API starting on http://localhost:{PORT}")
    print("Documented endpoints: GET /tasks, POST /tasks")
    print("Hint: There are more endpoints to discover...")
    HTTPServer(("", PORT), TaskHandler).serve_forever()
