"""
Global CRM Schema

Database tables for cross-project CRM data.
Lives in ~/.empirica/crm/crm.db (always global, not project-local).

Tables:
- clients: Persistent relationship entities
- engagements: Client-project connections with lifecycle
- client_interactions: Activity log
- client_memory: Semantic memory items (SQLite fallback for Qdrant)
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


CRM_SCHEMA = """
-- Clients: Persistent relationship entities
CREATE TABLE IF NOT EXISTS clients (
    client_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,

    -- Knowledge base links
    notebooklm_url TEXT,
    knowledge_base_urls TEXT,  -- JSON array of additional URLs

    -- Contact information
    contacts TEXT,  -- JSON array: [{name, email, role, notes}]

    -- Classification
    client_type TEXT DEFAULT 'prospect',  -- prospect, active, partner, churned
    industry TEXT,
    tags TEXT,  -- JSON array

    -- Metadata
    created_at REAL NOT NULL,
    updated_at REAL,
    created_by_ai_id TEXT,

    -- Epistemic state (aggregate across engagements)
    relationship_health REAL DEFAULT 0.5,  -- 0.0-1.0
    engagement_frequency REAL DEFAULT 0.0,  -- interactions per week
    knowledge_depth REAL DEFAULT 0.0,  -- how well do I know them

    -- Status
    status TEXT DEFAULT 'active',  -- active, inactive, archived
    last_contact_at REAL,
    next_action TEXT,
    next_action_due REAL
);

-- Engagements: Client-project connections with lifecycle
CREATE TABLE IF NOT EXISTS engagements (
    engagement_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    project_id TEXT,  -- Links to project in any sessions.db

    -- What is this engagement about
    title TEXT NOT NULL,
    description TEXT,
    engagement_type TEXT DEFAULT 'outreach',  -- outreach, demo, negotiation, support, review

    -- Timeline
    started_at REAL NOT NULL,
    ended_at REAL,
    status TEXT DEFAULT 'active',  -- active, completed, stalled, lost

    -- Outcome tracking
    outcome TEXT,  -- won, lost, deferred, ongoing
    outcome_notes TEXT,

    -- Value tracking (optional)
    estimated_value REAL,
    actual_value REAL,
    currency TEXT DEFAULT 'USD',

    -- Metadata
    created_at REAL NOT NULL,
    created_by_ai_id TEXT,

    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- Client interactions log
CREATE TABLE IF NOT EXISTS client_interactions (
    interaction_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    engagement_id TEXT,
    session_id TEXT,  -- Links to session in any sessions.db

    -- What happened
    interaction_type TEXT NOT NULL,  -- email, call, meeting, demo, document
    summary TEXT NOT NULL,

    -- Who was involved
    contacts_involved TEXT,  -- JSON array of contact names
    ai_id TEXT,

    -- When
    occurred_at REAL NOT NULL,

    -- Sentiment/outcome
    sentiment TEXT,  -- positive, neutral, negative
    follow_up_required INTEGER DEFAULT 0,
    follow_up_notes TEXT,

    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (engagement_id) REFERENCES engagements(engagement_id)
);

-- Client memory: Semantic memory items (SQLite fallback for Qdrant)
CREATE TABLE IF NOT EXISTS client_memory (
    item_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT,  -- MD5 for deduplication
    memory_type TEXT NOT NULL,  -- finding, unknown, pattern, preference, constraint
    engagement_id TEXT,
    session_id TEXT,
    confidence REAL DEFAULT 0.5,
    impact REAL DEFAULT 0.5,
    is_resolved INTEGER DEFAULT 0,
    resolved_by TEXT,
    resolved_at REAL,
    tags TEXT,  -- JSON array
    created_at REAL NOT NULL,
    updated_at REAL,

    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (engagement_id) REFERENCES engagements(engagement_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_clients_status ON clients(status);
CREATE INDEX IF NOT EXISTS idx_clients_type ON clients(client_type);
CREATE INDEX IF NOT EXISTS idx_engagements_client ON engagements(client_id);
CREATE INDEX IF NOT EXISTS idx_engagements_project ON engagements(project_id);
CREATE INDEX IF NOT EXISTS idx_engagements_status ON engagements(status);
CREATE INDEX IF NOT EXISTS idx_interactions_client ON client_interactions(client_id);
CREATE INDEX IF NOT EXISTS idx_interactions_date ON client_interactions(occurred_at);
CREATE INDEX IF NOT EXISTS idx_client_memory_client ON client_memory(client_id);
CREATE INDEX IF NOT EXISTS idx_client_memory_type ON client_memory(memory_type);
CREATE INDEX IF NOT EXISTS idx_client_memory_hash ON client_memory(content_hash);
"""


def get_crm_connection() -> sqlite3.Connection:
    """
    Get connection to global CRM database.

    Creates the database and tables if they don't exist.

    Returns:
        SQLite connection to ~/.empirica/crm/crm.db
    """
    from empirica.config.path_resolver import get_crm_db_path, ensure_crm_structure

    # Ensure directory structure exists
    ensure_crm_structure()

    db_path = get_crm_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # Ensure schema exists
    conn.executescript(CRM_SCHEMA)
    conn.commit()

    logger.debug(f"✅ CRM database connection: {db_path}")
    return conn


def ensure_crm_schema(conn: Optional[sqlite3.Connection] = None) -> bool:
    """
    Ensure CRM tables exist in the database.

    Args:
        conn: Optional connection. If None, uses global CRM DB.

    Returns:
        True if schema was created/verified successfully
    """
    owns_connection = conn is None

    try:
        if conn is None:
            conn = get_crm_connection()

        conn.executescript(CRM_SCHEMA)
        conn.commit()

        logger.info("✅ CRM schema verified/created")
        return True

    except Exception as e:
        logger.error(f"Failed to ensure CRM schema: {e}")
        return False

    finally:
        if owns_connection and conn:
            conn.close()


def migrate_client_data_to_global(source_db_path: Path) -> dict:
    """
    Migrate client data from a project-local DB to global CRM DB.

    Args:
        source_db_path: Path to source sessions.db with client data

    Returns:
        Dict with migration stats: {clients: int, engagements: int, ...}
    """
    from empirica.config.path_resolver import get_crm_db_path

    stats = {"clients": 0, "engagements": 0, "interactions": 0, "memory": 0}

    if not source_db_path.exists():
        logger.warning(f"Source DB not found: {source_db_path}")
        return stats

    try:
        source_conn = sqlite3.connect(str(source_db_path))
        source_conn.row_factory = sqlite3.Row

        target_conn = get_crm_connection()

        # Migrate clients
        try:
            source_clients = source_conn.execute("SELECT * FROM clients").fetchall()
            for client in source_clients:
                try:
                    target_conn.execute("""
                        INSERT OR IGNORE INTO clients
                        (client_id, name, description, notebooklm_url, knowledge_base_urls,
                         contacts, client_type, industry, tags, created_at, updated_at,
                         created_by_ai_id, relationship_health, engagement_frequency,
                         knowledge_depth, status, last_contact_at, next_action, next_action_due)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, tuple(client))
                    stats["clients"] += 1
                except sqlite3.IntegrityError:
                    pass  # Already exists
        except sqlite3.OperationalError:
            pass  # Table doesn't exist in source

        # Migrate engagements
        try:
            source_engagements = source_conn.execute("SELECT * FROM engagements").fetchall()
            for eng in source_engagements:
                try:
                    target_conn.execute("""
                        INSERT OR IGNORE INTO engagements
                        (engagement_id, client_id, project_id, title, description,
                         engagement_type, started_at, ended_at, status, outcome,
                         outcome_notes, estimated_value, actual_value, currency,
                         created_at, created_by_ai_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, tuple(eng))
                    stats["engagements"] += 1
                except sqlite3.IntegrityError:
                    pass
        except sqlite3.OperationalError:
            pass

        # Migrate client_interactions
        try:
            source_interactions = source_conn.execute("SELECT * FROM client_interactions").fetchall()
            for interaction in source_interactions:
                try:
                    target_conn.execute("""
                        INSERT OR IGNORE INTO client_interactions
                        (interaction_id, client_id, engagement_id, session_id,
                         interaction_type, summary, contacts_involved, ai_id,
                         occurred_at, sentiment, follow_up_required, follow_up_notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, tuple(interaction))
                    stats["interactions"] += 1
                except sqlite3.IntegrityError:
                    pass
        except sqlite3.OperationalError:
            pass

        # Migrate client_memory
        try:
            source_memory = source_conn.execute("SELECT * FROM client_memory").fetchall()
            for mem in source_memory:
                try:
                    target_conn.execute("""
                        INSERT OR IGNORE INTO client_memory
                        (item_id, client_id, content, content_hash, memory_type,
                         engagement_id, session_id, confidence, impact, is_resolved,
                         resolved_by, resolved_at, tags, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, tuple(mem))
                    stats["memory"] += 1
                except sqlite3.IntegrityError:
                    pass
        except sqlite3.OperationalError:
            pass

        target_conn.commit()
        source_conn.close()
        target_conn.close()

        logger.info(f"✅ Migrated from {source_db_path}: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return stats
