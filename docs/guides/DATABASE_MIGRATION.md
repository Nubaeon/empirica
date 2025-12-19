# Database Migration Guide

**Empirica supports multiple database backends:**
- **SQLite** (default) - Embedded, zero-ops, perfect for single-agent and development
- **PostgreSQL** (optional) - Production-ready, multi-agent concurrent writes, enterprise-scale

---

## When to Migrate to PostgreSQL

### Stay on SQLite if:
- ✅ Working solo or with 2-3 AIs in separate sessions
- ✅ Database < 100MB
- ✅ No concurrent write conflicts
- ✅ Local development/experimentation

### Migrate to PostgreSQL when:
- ⚠️ Getting `database is locked` errors frequently
- ⚠️ Need multiple AIs working on same task simultaneously
- ⚠️ Database > 100MB and queries slowing down
- ⚠️ Enterprise deployment with multiple teams
- ⚠️ Need horizontal scaling or replication

---

## PostgreSQL Setup

### Option 1: Supabase (Easiest)

**Free hosted PostgreSQL with pgvector:**

1. Create account at https://supabase.com
2. Create new project
3. Get connection string from Settings → Database
4. Configure Empirica:

```yaml
# .empirica/config.yaml
database:
  type: postgresql
  postgresql:
    host: db.xxx.supabase.co
    port: 5432
    database: postgres
    user: postgres
    password: ${SUPABASE_PASSWORD}  # Set via environment variable
```

5. Set environment variable:
```bash
export SUPABASE_PASSWORD="your-password-here"
```

### Option 2: Local Docker (Development)

```bash
# Start PostgreSQL with Docker
docker run -d \
  --name empirica-postgres \
  -e POSTGRES_USER=empirica \
  -e POSTGRES_PASSWORD=empirica \
  -e POSTGRES_DB=empirica \
  -p 5432:5432 \
  postgres:16

# Install pgvector extension (optional, for future vector search)
docker exec -it empirica-postgres psql -U empirica -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Configure:
```yaml
# .empirica/config.yaml
database:
  type: postgresql
  postgresql:
    host: localhost
    port: 5432
    database: empirica
    user: empirica
    password: empirica
```

### Option 3: Environment Variables (No Config File)

```bash
export EMPIRICA_DB_TYPE=postgresql
export EMPIRICA_DB_HOST=localhost
export EMPIRICA_DB_PORT=5432
export EMPIRICA_DB_NAME=empirica
export EMPIRICA_DB_USER=empirica
export EMPIRICA_DB_PASSWORD=secret
```

---

## Migration Steps

### 1. Backup Existing Data

```bash
# Backup SQLite database
cp .empirica/sessions/sessions.db .empirica/sessions/sessions.db.backup
```

### 2. Run Migration Script

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Run migration
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite .empirica/sessions/sessions.db \
  --postgres "postgresql://user:pass@localhost/empirica"
```

### 3. Update Configuration

```yaml
# .empirica/config.yaml
database:
  type: postgresql
  postgresql:
    host: localhost
    port: 5432
    database: empirica
    user: empirica
    password: ${POSTGRES_PASSWORD}
```

### 4. Verify Migration

```bash
# Test connection
empirica sessions-list --output json

# Check data integrity
python scripts/verify_migration.py
```

---

## Configuration Reference

### SQLite (Default)

```yaml
database:
  type: sqlite
  sqlite:
    path: ./.empirica/sessions/sessions.db  # Optional, defaults to repo-local
```

### PostgreSQL

```yaml
database:
  type: postgresql
  postgresql:
    host: localhost
    port: 5432
    database: empirica
    user: empirica
    password: ${POSTGRES_PASSWORD}  # Environment variable substitution
    # Optional connection pool settings:
    min_connections: 1
    max_connections: 10
```

---

## Performance Comparison

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| **Setup** | Zero-config | Requires server |
| **Concurrent writes** | Single-writer (locks) | Multi-writer (MVCC) |
| **Database size** | < 100MB ideal | Handles TB+ |
| **Deployment** | Embedded | Client-server |
| **Maintenance** | None | Backups, monitoring |
| **Cost** | Free | Free (self-hosted) or $$ (managed) |

---

## Rollback to SQLite

If you need to roll back from PostgreSQL:

```bash
# 1. Export PostgreSQL data
python scripts/export_postgres_to_sqlite.py \
  --postgres "postgresql://user:pass@localhost/empirica" \
  --sqlite .empirica/sessions/sessions.db

# 2. Update config
# Change: type: postgresql → type: sqlite

# 3. Verify
empirica sessions-list --output json
```

---

## Troubleshooting

### "Module 'psycopg2' not found"
```bash
pip install psycopg2-binary
```

### "Connection refused"
```bash
# Check PostgreSQL is running
docker ps | grep postgres
# or
pg_isready -h localhost -p 5432
```

### "Permission denied for database"
```sql
-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE empirica TO empirica;
```

### "Database is locked" (SQLite)
This means you need PostgreSQL! Multiple processes are trying to write simultaneously.

---

## Architecture Notes

**Qdrant (Vector Store):**
- Empirica already uses Qdrant for semantic vector search
- Stores: Learning deltas, findings, mistakes, unknowns
- This migration only affects *transactional* data (sessions, goals, CASCADE states)
- Qdrant integration is independent and unaffected

**Database Adapter Layer:**
- Clean abstraction pattern
- Zero performance overhead
- Transparent to existing code
- Easy to add new backends (e.g., MySQL, DuckDB) if needed

---

## Next Steps

1. **Now:** Keep using SQLite (it's working!)
2. **When needed:** Follow migration guide above
3. **Enterprise customers:** Contact for managed PostgreSQL setup assistance

Questions? See `empirica/data/db_adapter.py` for implementation details.
