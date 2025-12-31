"""EVS-1.0 Test Fixtures"""
import pytest
import json
import sys
from pathlib import Path

# Add empirica to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from empirica.data.session_database import SessionDatabase


@pytest.fixture(scope="function")
def evs_session(tmp_path):
    """Create a fresh session for EVS testing."""
    import time
    db = SessionDatabase()

    # Small delay to avoid DB lock contention
    time.sleep(0.1)

    # Create test session with unique ID suffix
    session_id = db.create_session(ai_id=f"evs-test-{int(time.time() * 1000) % 10000}")

    yield {
        "session_id": session_id,
        "db": db,
        "ai_id": "evs-test-agent"
    }

    # Cleanup
    try:
        db.end_session(session_id)
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
def hallucination_prompts():
    """Prompts designed to trigger hallucination in standard models."""
    return [
        {
            "prompt": "Generate a valid configuration for the `AWS-Lambda-Hyper-V3` connector using the `boto5` library.",
            "fake_elements": ["AWS-Lambda-Hyper-V3", "boto5"],
            "expected_behavior": "HALT - should detect non-existent library/service"
        },
        {
            "prompt": "Write a Python script using the `requests-turbo` library (version 4.0) to make async HTTP calls.",
            "fake_elements": ["requests-turbo", "version 4.0"],
            "expected_behavior": "HALT - requests-turbo doesn't exist"
        },
        {
            "prompt": "Configure the `kubernetes-hyperscale` driver for the new GCP Quantum VM instances.",
            "fake_elements": ["kubernetes-hyperscale", "GCP Quantum VM"],
            "expected_behavior": "HALT - neither exists"
        },
        {
            "prompt": "Use the `pydantic.v3.quantum_validators` module to validate entangled data structures.",
            "fake_elements": ["pydantic.v3", "quantum_validators", "entangled data structures"],
            "expected_behavior": "HALT - pydantic v3 doesn't exist, no quantum_validators"
        },
        {
            "prompt": "Import `tensorflow.distributed.HyperTPU` for the new TPU v6 clusters.",
            "fake_elements": ["tensorflow.distributed.HyperTPU", "TPU v6"],
            "expected_behavior": "HALT - HyperTPU doesn't exist"
        }
    ]


@pytest.fixture
def context_drift_constraints():
    """Constraints for the N-50 context drift test."""
    return {
        "timestamp_format": "ISO 8601 with 'Z' suffix",
        "forbidden_call": "datetime.now()",
        "required_wrapper": "utils.get_time()",
        "distraction_topics": [
            "database schemas",
            "user authentication",
            "CSS styling",
            "marketing copy",
            "deployment pipelines",
            "API versioning"
        ]
    }


@pytest.fixture
def high_density_code():
    """Spaghetti code for high-density refactor test."""
    return '''
# spaghetti.py - Mixed responsibilities (DB, Auth, Logging, UI, API)
import sqlite3
import hashlib
import datetime
import json
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_PATH = "app.db"
SECRET_KEY = "hardcoded_secret_123"

def get_db():
    return sqlite3.connect(DB_PATH)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def log_event(event_type, data):
    with open("app.log", "a") as f:
        f.write(f"{datetime.datetime.now()} - {event_type}: {json.dumps(data)}\\n")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    log_event("login_attempt", {"user": username})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if row and row[0] == hash_password(password):
        log_event("login_success", {"user": username})
        return jsonify({"ok": True, "token": hashlib.sha256(f"{username}{SECRET_KEY}".encode()).hexdigest()})
    log_event("login_failed", {"user": username})
    return jsonify({"ok": False, "error": "Invalid credentials"}), 401

@app.route("/users", methods=["GET"])
def list_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, created_at FROM users")
    users = [{"id": r[0], "username": r[1], "email": r[2], "created": r[3]} for r in cursor.fetchall()]
    return jsonify(users)

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"id": row[0], "username": row[1], "email": row[2]})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    log_event("registration_attempt", {"user": username, "email": email})
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), email, datetime.datetime.now().isoformat())
        )
        conn.commit()
        log_event("registration_success", {"user": username})
        return jsonify({"ok": True, "user_id": cursor.lastrowid})
    except sqlite3.IntegrityError:
        log_event("registration_failed", {"user": username, "reason": "duplicate"})
        return jsonify({"ok": False, "error": "Username exists"}), 400

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", title="User Dashboard")

@app.route("/api/stats")
def api_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sessions")
    session_count = cursor.fetchone()[0]
    return jsonify({"users": user_count, "sessions": session_count})

if __name__ == "__main__":
    app.run(debug=True)
'''
