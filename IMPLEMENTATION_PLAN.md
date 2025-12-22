# Token Savings Tracker - Implementation Plan

**Investigation Session:** 0554f1d4-88dd-4010-b82a-119535b9bcf8  
**Status:** Investigation complete, ready for implementation  
**Approach:** Minimal, AI-cooperative, avoid complexity creep

---

## 🎯 Core Finding

**Semantic index is ALREADY integrated** in project-bootstrap (line 2655).  
AIs already receive `semantic_docs` breadcrumb showing existing documentation.  
**Missing:** Tracking when AI uses this to avoid redundant work.

---

## 📋 Phase 1: Minimal Implementation (~1 hour)

### 1. Add token_savings Table (5 minutes)

```python
# empirica/data/session_database.py (in _create_tables method)

cursor.execute("""
    CREATE TABLE IF NOT EXISTS token_savings (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        saving_type TEXT NOT NULL,
        tokens_saved INTEGER NOT NULL,
        evidence TEXT,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
""")

cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_savings_session ON token_savings(session_id)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_savings_type ON token_savings(saving_type)")
```

### 2. Add log_token_saving Method (10 minutes)

```python
# empirica/data/session_database.py

def log_token_saving(
    self,
    session_id: str,
    saving_type: str,
    tokens_saved: int,
    evidence: str
) -> str:
    """Log a token saving event
    
    Args:
        session_id: Session identifier
        saving_type: Type of saving ('doc_awareness', 'finding_reuse', 'mistake_prevention', etc.)
        tokens_saved: Estimated tokens saved
        evidence: What was avoided/reused
        
    Returns:
        saving_id: UUID string
    """
    import uuid
    saving_id = str(uuid.uuid4())
    
    cursor = self.conn.cursor()
    cursor.execute("""
        INSERT INTO token_savings (
            id, session_id, saving_type, tokens_saved, evidence
        ) VALUES (?, ?, ?, ?, ?)
    """, (saving_id, session_id, saving_type, tokens_saved, evidence))
    
    self.conn.commit()
    logger.info(f"💰 Token saving logged: {tokens_saved} tokens ({saving_type})")
    
    return saving_id

def get_session_token_savings(self, session_id: str) -> Dict:
    """Get token savings summary for a session"""
    cursor = self.conn.cursor()
    
    cursor.execute("""
        SELECT saving_type, SUM(tokens_saved) as total, COUNT(*) as count
        FROM token_savings
        WHERE session_id = ?
        GROUP BY saving_type
    """, (session_id,))
    
    breakdown = {}
    total = 0
    for row in cursor.fetchall():
        saving_type = row[0]
        tokens = row[1]
        count = row[2]
        breakdown[saving_type] = {'tokens': tokens, 'count': count}
        total += tokens
    
    return {
        'total_tokens_saved': total,
        'cost_saved_usd': round(total * 0.00003, 4),
        'breakdown': breakdown
    }
```

### 3. Add CLI Command (15 minutes)

```python
# empirica/cli/command_handlers/utility_commands.py

def handle_log_token_saving(args):
    """Log a token saving event"""
    from empirica.data.session_database import SessionDatabase
    
    db = SessionDatabase()
    
    saving_id = db.log_token_saving(
        session_id=args.session_id,
        saving_type=args.type,
        tokens_saved=args.tokens,
        evidence=args.evidence
    )
    
    db.close()
    
    if args.output == 'json':
        print(json.dumps({
            'ok': True,
            'saving_id': saving_id,
            'tokens_saved': args.tokens,
            'type': args.type
        }))
    else:
        print(f"✅ Token saving logged: {args.tokens} tokens saved ({args.type})")

# Add to CLI registration (cli_core.py)
parser_log_saving = subparsers.add_parser('log-token-saving',
    help='Log a token saving event')
parser_log_saving.add_argument('--session-id', required=True)
parser_log_saving.add_argument('--type', required=True,
    choices=['doc_awareness', 'finding_reuse', 'mistake_prevention', 'handoff_efficiency'])
parser_log_saving.add_argument('--tokens', type=int, required=True)
parser_log_saving.add_argument('--evidence', required=True)
parser_log_saving.add_argument('--output', choices=['text', 'json'], default='text')
parser_log_saving.set_defaults(func=handle_log_token_saving)
```

### 4. Add Session-End Report (20 minutes)

```python
# Add to session-snapshot or create efficiency-report command

def handle_efficiency_report(args):
    """Show token efficiency report for session"""
    from empirica.data.session_database import SessionDatabase
    
    db = SessionDatabase()
    savings = db.get_session_token_savings(args.session_id)
    
    if args.output == 'json':
        print(json.dumps(savings, indent=2))
    else:
        print("\n📊 Token Efficiency Report")
        print("━" * 60)
        print(f"✅ Tokens Saved This Session:     {savings['total_tokens_saved']:,} tokens")
        print(f"💰 Cost Saved:                    ${savings['cost_saved_usd']:.4f} USD")
        print("\nBreakdown:")
        for saving_type, data in savings['breakdown'].items():
            type_label = saving_type.replace('_', ' ').title()
            print(f"  {type_label:.<30} {data['tokens']:,} tokens ({data['count']}x)")
        print("━" * 60)
    
    db.close()
```

### 5. Update System Prompt (10 minutes)

Add to `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md`:

```markdown
## Token Efficiency Tracking

When you use Empirica features to avoid redundant work, log token savings:

### Documentation Awareness
If you check semantic_docs and link to existing documentation instead of rewriting:

```bash
empirica log-token-saving \
  --session-id <SESSION_ID> \
  --type doc_awareness \
  --tokens 1500 \
  --evidence "Linked to existing docs/auth/OAUTH2.md instead of rewriting OAuth2 guide"
```

### Finding Reuse
If you find an existing project finding that answers your question:

```bash
empirica log-token-saving \
  --session-id <SESSION_ID> \
  --type finding_reuse \
  --tokens 500 \
  --evidence "Reused finding: 'OAuth2 uses /authorize endpoint'"
```

This helps demonstrate Empirica's ROI and proves value to users.
```

---

## 🧪 Testing

```bash
# 1. Create test session
SESSION_ID=$(empirica session-create - <<< '{"ai_id":"test"}' | jq -r .session_id)

# 2. Log a doc awareness saving
empirica log-token-saving \
  --session-id $SESSION_ID \
  --type doc_awareness \
  --tokens 1500 \
  --evidence "Linked to existing CASCADE_WORKFLOW.md"

# 3. Check efficiency report
empirica efficiency-report --session-id $SESSION_ID

# Expected output:
# 📊 Token Efficiency Report
# ✅ Tokens Saved: 1,500 tokens
# 💰 Cost Saved: $0.0450 USD
```

---

## 📦 Deliverables

1. ✅ token_savings table added to session_database.py
2. ✅ log_token_saving() and get_session_token_savings() methods
3. ✅ log-token-saving CLI command
4. ✅ efficiency-report CLI command
5. ✅ Updated system prompt with usage pattern

---

## 🚀 Future Enhancements (Phase 2)

- Automatic bootstrap tracking (log when semantic_docs loaded)
- Finding reuse detection (hook into get_project_findings)
- Mistake prevention detection (hook into get_mistakes)
- Project-lifetime aggregation (total savings across all sessions)
- Dashboard visualization (ASCII art bar charts)

---

**Ready for implementation!** All investigation complete, approach validated, schema minimal.
