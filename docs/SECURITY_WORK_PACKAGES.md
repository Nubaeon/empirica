# 🔒 Empirica Security Work Packages

**Version:** 1.0.0  
**Status:** Active  
**Last Updated:** 2026-01-05  

This document provides actionable work packages for implementing the security controls defined in [SECURITY_SPECIFICATION.md](./SECURITY_SPECIFICATION.md).

---

## Overview

Each work package is:
- **Self-contained**: Can be completed independently
- **Testable**: Has clear acceptance criteria
- **Scoped**: 1-5 days of effort
- **Prioritized**: CRITICAL → HIGH → MEDIUM → LOW

---

## Work Package Index

### Phase 1: Critical Security Foundations (Weeks 1-2)
- [WP-001: Prompt Injection Detector](#wp-001-prompt-injection-detector) - CRITICAL - 3 days
- [WP-002: SQL Injection Prevention Audit](#wp-002-sql-injection-prevention-audit) - HIGH - 2 days
- [WP-003: Secure Session Management](#wp-003-secure-session-management) - CRITICAL - 3 days
- [WP-004: RBAC Authorization Model](#wp-004-rbac-authorization-model) - HIGH - 5 days
- [WP-005: Secret Scanning Pipeline](#wp-005-secret-scanning-pipeline) - HIGH - 2 days

### Phase 2: Web Application Security (Weeks 3-4)
- [WP-006: XSS Prevention](#wp-006-xss-prevention) - HIGH - 3 days
- [WP-007: CSRF Protection](#wp-007-csrf-protection) - HIGH - 2 days
- [WP-008: API Token Management](#wp-008-api-token-management) - HIGH - 3 days
- [WP-009: Rate Limiting](#wp-009-rate-limiting) - MEDIUM - 3 days

### Phase 3: Advanced Security (Weeks 5-6)
- [WP-010: Command Injection Prevention](#wp-010-command-injection-prevention) - CRITICAL - 3 days
- [WP-011: Path Traversal Protection](#wp-011-path-traversal-protection) - HIGH - 2 days
- [WP-012: NoSQL Injection Prevention](#wp-012-nosql-injection-prevention) - MEDIUM - 2 days
- [WP-013: Security Audit Logger](#wp-013-security-audit-logger) - HIGH - 3 days
- [WP-014: Anomaly Detection](#wp-014-anomaly-detection) - MEDIUM - 5 days

### Phase 4: Testing & Compliance (Weeks 7-8)
- [WP-015: Security Test Suite](#wp-015-security-test-suite) - HIGH - 5 days
- [WP-016: Automated Security Scanning](#wp-016-automated-security-scanning) - MEDIUM - 2 days
- [WP-017: HIPAA Compliance Enhancement](#wp-017-hipaa-compliance-enhancement) - MEDIUM - 3 days
- [WP-018: Security Documentation](#wp-018-security-documentation) - MEDIUM - 3 days

---

## Phase 1: Critical Security Foundations

### WP-001: Prompt Injection Detector

**Control ID:** SEC-001  
**Priority:** CRITICAL  
**Effort:** 3 days  
**Dependencies:** None

#### Objectives
Implement prompt injection detection to protect against malicious prompt manipulation, integrating with the existing MCP Sentinel.

#### Tasks

**Day 1: Core Detection Logic**
1. Create `empirica/core/sentinel/injection_detector.py`
   ```python
   from dataclasses import dataclass
   from typing import List, Optional
   import re
   
   @dataclass
   class InjectionPattern:
       pattern: str
       severity: str  # critical, high, medium, low
       description: str
   
   class PromptInjectionDetector:
       """Detects prompt injection attempts"""
       
       PATTERNS = [
           InjectionPattern(
               pattern=r'ignore\s+(previous|all|prior)\s+instructions',
               severity='critical',
               description='Instruction override attempt'
           ),
           InjectionPattern(
               pattern=r'system\s+prompt',
               severity='high',
               description='System prompt reference'
           ),
           InjectionPattern(
               pattern=r'you\s+are\s+now',
               severity='high',
               description='Identity override attempt'
           ),
           InjectionPattern(
               pattern=r'forget\s+(everything|all)',
               severity='high',
               description='Memory wipe attempt'
           ),
           InjectionPattern(
               pattern=r'\[INST\]|\[/INST\]',
               severity='critical',
               description='Llama instruction injection'
           ),
           InjectionPattern(
               pattern=r'<\|im_start\|>|<\|im_end\|>',
               severity='critical',
               description='ChatML injection attempt'
           ),
       ]
       
       def detect(self, text: str) -> List[Dict[str, Any]]:
           """Detect injection patterns in text"""
           detections = []
           for pattern_obj in self.PATTERNS:
               matches = re.finditer(pattern_obj.pattern, text, re.IGNORECASE)
               for match in matches:
                   detections.append({
                       'pattern': pattern_obj.description,
                       'severity': pattern_obj.severity,
                       'matched_text': match.group(),
                       'position': match.span()
                   })
           return detections
   ```

2. Add pattern configuration loader
   - Read patterns from `empirica/core/sentinel/injection_patterns.yaml`
   - Allow custom pattern additions

**Day 2: Sentinel Integration**
1. Integrate with MCP Sentinel
   - Hook into Sentinel CHECK gate
   - Add injection detection to noetic filter
   - Log detections to audit log

2. Create action handlers
   ```python
   def handle_injection_detection(detections, context):
       """Handle detected injection attempts"""
       if any(d['severity'] == 'critical' for d in detections):
           # Halt immediately
           return GateAction.HALT_AND_AUDIT
       elif any(d['severity'] == 'high' for d in detections):
           # Require human review
           return GateAction.REQUIRE_HUMAN
       else:
           # Log and continue
           return GateAction.LOG_AND_CONTINUE
   ```

**Day 3: Testing & Documentation**
1. Create test cases
   - OWASP prompt injection test vectors
   - Custom Empirica-specific tests
   - False positive validation

2. Add CLI command
   ```bash
   empirica security-check-prompt --text "Your input here"
   # Returns: injection patterns detected
   ```

3. Document in security spec
   - Usage examples
   - Integration guide
   - Pattern customization

#### Acceptance Criteria
- [ ] Detector catches all OWASP prompt injection test cases
- [ ] Integration with Sentinel CHECK gate works
- [ ] False positive rate < 5% on legitimate inputs
- [ ] CLI command functional
- [ ] Unit tests achieve >90% coverage
- [ ] Documentation complete

#### Files Created/Modified
- `empirica/core/sentinel/injection_detector.py` (NEW)
- `empirica/core/sentinel/injection_patterns.yaml` (NEW)
- `empirica/core/sentinel/orchestrator.py` (MODIFY - add integration)
- `empirica/cli/parsers/security_parsers.py` (NEW)
- `empirica/cli/command_handlers/security_commands.py` (NEW)
- `tests/security/test_prompt_injection.py` (NEW)
- `docs/SECURITY_SPECIFICATION.md` (UPDATE)

---

### WP-002: SQL Injection Prevention Audit

**Control ID:** SEC-002  
**Priority:** HIGH  
**Effort:** 2 days  
**Dependencies:** None

#### Objectives
Audit all database operations and extend SQL injection prevention across the entire codebase.

#### Tasks

**Day 1: Audit & Inventory**
1. Find all database operations
   ```bash
   # Search for potential SQL operations
   grep -r "execute\|query\|_execute" empirica/data/repositories/
   grep -r "f-string.*SELECT\|f-string.*INSERT" empirica/
   ```

2. Create audit spreadsheet
   | File | Line | Operation | Safe? | Action Needed |
   |------|------|-----------|-------|---------------|
   | cascades.py | 60 | UPDATE | ✅ Yes | None |
   | sessions.py | 45 | SELECT | ❌ No | Add validation |

3. Identify vulnerable patterns
   - String concatenation in queries
   - Unvalidated user input
   - Missing parameter binding

**Day 2: Fix & Test**
1. Create validation helper
   ```python
   # empirica/security/sql_validators.py
   from typing import Set, Any
   
   def validate_against_whitelist(value: str, allowed: Set[str], field_name: str) -> str:
       """Validate value is in whitelist"""
       if value not in allowed:
           raise ValueError(
               f"Invalid {field_name}: {value}. "
               f"Must be one of: {allowed}"
           )
       return value
   
   def validate_uuid(value: str) -> str:
       """Validate UUID format"""
       try:
           uuid.UUID(value)
           return value
       except ValueError:
           raise ValueError(f"Invalid UUID format: {value}")
   ```

2. Apply fixes to identified vulnerabilities
   - Add input validation
   - Convert to parameterized queries
   - Use SQLAlchemy ORM where possible

3. Add automated tests
   ```python
   # tests/security/test_sql_injection.py
   def test_phase_validation():
       """Verify phase parameter validation"""
       with pytest.raises(ValueError):
           update_cascade_phase(cascade_id, "'; DROP TABLE--")
   
   def test_uuid_validation():
       """Verify UUID validation prevents injection"""
       with pytest.raises(ValueError):
           get_session("' OR 1=1--")
   ```

#### Acceptance Criteria
- [ ] All database operations audited
- [ ] No unvalidated user input in SQL queries
- [ ] Validation helper library created
- [ ] All identified vulnerabilities fixed
- [ ] Test suite includes SQL injection tests
- [ ] Documentation updated

#### Files Created/Modified
- `empirica/security/sql_validators.py` (NEW)
- `empirica/data/repositories/*.py` (MODIFY - add validation)
- `tests/security/test_sql_injection.py` (NEW)
- `docs/security/SQL_INJECTION_PREVENTION.md` (NEW)

---

### WP-003: Secure Session Management

**Control ID:** SEC-005  
**Priority:** CRITICAL  
**Effort:** 3 days  
**Dependencies:** None

#### Objectives
Implement secure session ID generation, timeout, and invalidation mechanisms.

#### Tasks

**Day 1: Session ID Security**
1. Update session ID generation
   ```python
   # empirica/data/repositories/sessions.py
   import secrets
   
   def generate_session_id() -> str:
       """Generate cryptographically secure session ID"""
       return secrets.token_urlsafe(32)  # 256-bit entropy
   ```

2. Add session metadata
   ```python
   # Add to sessions table schema
   ALTER TABLE sessions ADD COLUMN created_at TEXT;
   ALTER TABLE sessions ADD COLUMN last_accessed_at TEXT;
   ALTER TABLE sessions ADD COLUMN expires_at TEXT;
   ALTER TABLE sessions ADD COLUMN invalidated BOOLEAN DEFAULT FALSE;
   ```

**Day 2: Timeout & Invalidation**
1. Implement session timeout
   ```python
   def is_session_valid(session_id: str) -> bool:
       """Check if session is valid and not expired"""
       session = get_session(session_id)
       if not session:
           return False
       if session.invalidated:
           return False
       
       now = datetime.now(UTC)
       expires_at = datetime.fromisoformat(session.expires_at)
       if now > expires_at:
           return False
       
       # Update last accessed
       update_session_access_time(session_id, now)
       return True
   ```

2. Add session invalidation
   ```python
   def invalidate_session(session_id: str, reason: str = "manual"):
       """Explicitly invalidate a session"""
       execute(
           "UPDATE sessions SET invalidated = TRUE WHERE session_id = ?",
           (session_id,)
       )
       audit_log(
           event_type="session_invalidated",
           session_id=session_id,
           reason=reason
       )
   ```

3. Create CLI commands
   ```bash
   empirica session-invalidate --session-id <id>
   empirica sessions-cleanup --expired  # Clean up expired sessions
   ```

**Day 3: Testing & Integration**
1. Add session validation to API
   - Middleware to check session validity
   - Return 401 on invalid session

2. Create tests
   ```python
   def test_session_timeout():
       session = create_session(timeout_hours=1)
       # Fast-forward time
       with freeze_time(now + timedelta(hours=2)):
           assert not is_session_valid(session.id)
   
   def test_session_invalidation():
       session = create_session()
       invalidate_session(session.id)
       assert not is_session_valid(session.id)
   ```

3. Add background cleanup task
   - Periodically remove expired sessions
   - Configurable cleanup interval

#### Acceptance Criteria
- [ ] Session IDs use cryptographically secure generation
- [ ] Session timeout implemented (default 24 hours)
- [ ] Manual session invalidation works
- [ ] Expired sessions automatically cleaned up
- [ ] API validates sessions on requests
- [ ] CLI commands functional
- [ ] Tests cover timeout and invalidation scenarios

#### Files Created/Modified
- `empirica/data/repositories/sessions.py` (MODIFY)
- `empirica/data/migrations/add_session_security.sql` (NEW)
- `empirica/api/middleware/session_validator.py` (NEW)
- `empirica/cli/command_handlers/session_commands.py` (MODIFY)
- `tests/security/test_session_management.py` (NEW)

---

### WP-004: RBAC Authorization Model

**Control ID:** SEC-006  
**Priority:** HIGH  
**Effort:** 5 days  
**Dependencies:** WP-003 (Session Management)

#### Objectives
Define and implement Role-Based Access Control (RBAC) for resources.

#### Tasks

**Day 1: Schema Design**
1. Define RBAC schema
   ```sql
   -- Users table
   CREATE TABLE IF NOT EXISTS users (
       user_id TEXT PRIMARY KEY,
       username TEXT UNIQUE NOT NULL,
       email TEXT UNIQUE,
       created_at TEXT NOT NULL,
       active BOOLEAN DEFAULT TRUE
   );
   
   -- Roles table
   CREATE TABLE IF NOT EXISTS roles (
       role_id TEXT PRIMARY KEY,
       role_name TEXT UNIQUE NOT NULL,
       description TEXT
   );
   
   -- Permissions table
   CREATE TABLE IF NOT EXISTS permissions (
       permission_id TEXT PRIMARY KEY,
       resource TEXT NOT NULL,  -- sessions, findings, goals, config
       action TEXT NOT NULL,    -- read, write, delete, configure
       description TEXT
   );
   
   -- Role-Permission mapping
   CREATE TABLE IF NOT EXISTS role_permissions (
       role_id TEXT,
       permission_id TEXT,
       FOREIGN KEY (role_id) REFERENCES roles(role_id),
       FOREIGN KEY (permission_id) REFERENCES permissions(permission_id),
       PRIMARY KEY (role_id, permission_id)
   );
   
   -- User-Role mapping
   CREATE TABLE IF NOT EXISTS user_roles (
       user_id TEXT,
       role_id TEXT,
       FOREIGN KEY (user_id) REFERENCES users(user_id),
       FOREIGN KEY (role_id) REFERENCES roles(role_id),
       PRIMARY KEY (user_id, role_id)
   );
   ```

2. Define default roles
   ```yaml
   # empirica/security/default_roles.yaml
   roles:
     admin:
       description: Full system access
       permissions:
         - read:*
         - write:*
         - delete:*
         - configure:*
     
     user:
       description: Standard user with own data access
       permissions:
         - read:own_sessions
         - write:own_sessions
         - read:own_findings
         - write:own_findings
         - read:own_goals
         - write:own_goals
     
     viewer:
       description: Read-only access
       permissions:
         - read:sessions
         - read:findings
         - read:goals
   ```

**Day 2-3: Implementation**
1. Create RBAC module
   ```python
   # empirica/security/rbac.py
   from typing import List, Set
   
   class RBACManager:
       """Role-Based Access Control Manager"""
       
       def __init__(self, db_path: str):
           self.db = Database(db_path)
       
       def check_permission(
           self,
           user_id: str,
           resource: str,
           action: str
       ) -> bool:
           """Check if user has permission"""
           user_permissions = self.get_user_permissions(user_id)
           required = f"{action}:{resource}"
           
           # Check wildcard permissions
           if f"{action}:*" in user_permissions:
               return True
           if f"*:{resource}" in user_permissions:
               return True
           
           return required in user_permissions
       
       def get_user_permissions(self, user_id: str) -> Set[str]:
           """Get all permissions for a user"""
           roles = self.get_user_roles(user_id)
           permissions = set()
           for role in roles:
               role_perms = self.get_role_permissions(role)
               permissions.update(role_perms)
           return permissions
   ```

2. Add session ownership
   ```python
   def check_session_access(user_id: str, session_id: str) -> bool:
       """Check if user can access session"""
       session = get_session(session_id)
       
       # Owner can always access
       if session.owner_id == user_id:
           return True
       
       # Admin can access any
       rbac = RBACManager()
       if rbac.check_permission(user_id, "sessions", "read"):
           return True
       
       return False
   ```

**Day 4: API Integration**
1. Add authorization middleware
   ```python
   # empirica/api/middleware/auth_middleware.py
   from flask import request, abort
   
   def require_permission(resource: str, action: str):
       """Decorator to check permissions"""
       def decorator(f):
           @wraps(f)
           def decorated_function(*args, **kwargs):
               user_id = get_current_user_id()
               rbac = RBACManager()
               if not rbac.check_permission(user_id, resource, action):
                   abort(403, "Insufficient permissions")
               return f(*args, **kwargs)
           return decorated_function
       return decorator
   ```

2. Apply to routes
   ```python
   @app.route('/api/sessions/<session_id>')
   @require_permission('sessions', 'read')
   def get_session_api(session_id):
       # Verify ownership
       if not check_session_access(current_user.id, session_id):
           abort(403, "Access denied")
       return jsonify(get_session(session_id))
   ```

**Day 5: CLI & Testing**
1. Add RBAC CLI commands
   ```bash
   empirica user-create --username alice --role user
   empirica role-assign --user alice --role admin
   empirica permission-check --user alice --resource sessions --action read
   ```

2. Create comprehensive tests
   ```python
   def test_admin_access():
       admin = create_user(role='admin')
       session = create_session(owner='user1')
       assert check_session_access(admin.id, session.id) == True
   
   def test_user_own_data_only():
       user = create_user(role='user')
       own_session = create_session(owner=user.id)
       other_session = create_session(owner='other')
       assert check_session_access(user.id, own_session.id) == True
       assert check_session_access(user.id, other_session.id) == False
   ```

#### Acceptance Criteria
- [ ] RBAC schema implemented
- [ ] Default roles created (admin, user, viewer)
- [ ] Permission checking works
- [ ] Session ownership enforced
- [ ] API routes protected
- [ ] CLI commands functional
- [ ] Tests cover all role scenarios
- [ ] Documentation complete

#### Files Created/Modified
- `empirica/security/rbac.py` (NEW)
- `empirica/security/default_roles.yaml` (NEW)
- `empirica/data/migrations/add_rbac_tables.sql` (NEW)
- `empirica/api/middleware/auth_middleware.py` (NEW)
- `empirica/api/routes/*.py` (MODIFY - add auth checks)
- `empirica/cli/command_handlers/user_commands.py` (NEW)
- `tests/security/test_rbac.py` (NEW)

---

### WP-005: Secret Scanning Pipeline

**Control ID:** SEC-009  
**Priority:** HIGH  
**Effort:** 2 days  
**Dependencies:** None

#### Objectives
Implement automated secret scanning in pre-commit hooks and CI/CD pipeline.

#### Tasks

**Day 1: Pre-Commit Hooks**
1. Create pre-commit hook script
   ```bash
   #!/bin/bash
   # .git/hooks/pre-commit
   
   echo "🔍 Scanning for secrets..."
   
   # Pattern matching for common secrets
   PATTERNS=(
       'api[_-]?key.*=.*[0-9a-zA-Z]{20,}'
       'secret.*=.*[0-9a-zA-Z]{20,}'
       'password.*=.*[0-9a-zA-Z]{10,}'
       'token.*=.*[0-9a-zA-Z]{20,}'
       'private[_-]?key'
       'BEGIN.*PRIVATE.*KEY'
   )
   
   for pattern in "${PATTERNS[@]}"; do
       if git diff --cached | grep -E "$pattern"; then
           echo "❌ ERROR: Potential secret detected!"
           echo "Pattern: $pattern"
           echo ""
           echo "If this is a false positive, use:"
           echo "  git commit --no-verify"
           exit 1
       fi
   done
   
   echo "✅ No secrets detected"
   exit 0
   ```

2. Add installation script
   ```python
   # scripts/install_git_hooks.py
   import os
   import shutil
   from pathlib import Path
   
   def install_hooks():
       """Install git hooks"""
       repo_root = Path(__file__).parent.parent
       hooks_dir = repo_root / '.git' / 'hooks'
       source = repo_root / 'scripts' / 'git-hooks' / 'pre-commit'
       dest = hooks_dir / 'pre-commit'
       
       shutil.copy(source, dest)
       os.chmod(dest, 0o755)
       print("✅ Git hooks installed")
   ```

**Day 2: CI/CD Integration**
1. Add GitHub Actions workflow
   ```yaml
   # .github/workflows/secret-scanning.yml
   name: Secret Scanning
   
   on: [push, pull_request]
   
   jobs:
     scan-secrets:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
           with:
             fetch-depth: 0  # Full history for scanning
         
         - name: TruffleHog Secret Scan
           uses: trufflesecurity/trufflehog@v3
           with:
             path: ./
             base: ${{ github.event.repository.default_branch }}
             head: HEAD
             extra_args: --json --fail
         
         - name: GitGuardian Scan
           uses: GitGuardian/ggshield-action@v1
           env:
             GITGUARDIAN_API_KEY: ${{ secrets.GITGUARDIAN_API_KEY }}
   ```

2. Add history scanning script
   ```python
   # scripts/scan_git_history.py
   import subprocess
   import re
   
   def scan_git_history():
       """Scan entire git history for secrets"""
       patterns = [
           r'api[_-]?key.*=.*[0-9a-zA-Z]{20,}',
           r'secret.*=.*[0-9a-zA-Z]{20,}',
           r'password.*=.*[0-9a-zA-Z]{10,}',
       ]
       
       commits = subprocess.check_output(
           ['git', 'log', '--all', '--pretty=format:%H']
       ).decode().split('\n')
       
       findings = []
       for commit in commits:
           diff = subprocess.check_output(
               ['git', 'show', commit]
           ).decode()
           
           for pattern in patterns:
               matches = re.findall(pattern, diff, re.IGNORECASE)
               if matches:
                   findings.append({
                       'commit': commit,
                       'pattern': pattern,
                       'matches': matches
                   })
       
       return findings
   ```

3. Create documentation
   - Developer guide for avoiding secrets in commits
   - Procedure for handling detected secrets
   - Incident response for leaked secrets

#### Acceptance Criteria
- [ ] Pre-commit hook installed and functional
- [ ] GitHub Actions workflow active
- [ ] TruffleHog integrated
- [ ] Git history scanning script works
- [ ] Documentation complete
- [ ] Team trained on secret handling

#### Files Created/Modified
- `scripts/git-hooks/pre-commit` (NEW)
- `scripts/install_git_hooks.py` (NEW)
- `scripts/scan_git_history.py` (NEW)
- `.github/workflows/secret-scanning.yml` (NEW)
- `docs/security/SECRET_HANDLING.md` (NEW)
- `CONTRIBUTING.md` (UPDATE - add secret handling section)

---

## Phase 2: Web Application Security

### WP-006: XSS Prevention

**Control ID:** SEC-004  
**Priority:** HIGH  
**Effort:** 3 days  
**Dependencies:** None

#### Objectives
Implement XSS prevention for Flask API and web dashboard.

#### Tasks

**Day 1: Output Encoding**
1. Create encoding helpers
   ```python
   # empirica/security/output_encoding.py
   from html import escape
   from urllib.parse import quote
   
   def html_escape(text: str) -> str:
       """Escape HTML entities"""
       return escape(text, quote=True)
   
   def js_escape(text: str) -> str:
       """Escape for JavaScript context"""
       return text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')
   
   def url_encode(text: str) -> str:
       """URL encode"""
       return quote(text, safe='')
   ```

2. Apply to all Flask routes
   ```python
   @app.route('/api/sessions/<session_id>')
   def get_session_route(session_id):
       session = get_session(session_id)
       # Escape all user-generated content
       session['description'] = html_escape(session['description'])
       return jsonify(session)
   ```

**Day 2: Security Headers**
1. Add security middleware
   ```python
   # empirica/api/middleware/security_headers.py
   from flask import Flask
   
   def add_security_headers(app: Flask):
       @app.after_request
       def set_security_headers(response):
           # Content Security Policy
           response.headers['Content-Security-Policy'] = (
               "default-src 'self'; "
               "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
               "style-src 'self' 'unsafe-inline'; "
               "img-src 'self' data:; "
               "font-src 'self' data:; "
               "connect-src 'self'; "
               "frame-ancestors 'none'"
           )
           
           # Other security headers
           response.headers['X-Content-Type-Options'] = 'nosniff'
           response.headers['X-Frame-Options'] = 'DENY'
           response.headers['X-XSS-Protection'] = '1; mode=block'
           response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
           
           # HTTPS enforcement
           response.headers['Strict-Transport-Security'] = (
               'max-age=31536000; includeSubDomains'
           )
           
           return response
   ```

2. Update Flask app initialization
   ```python
   # empirica/api/app.py
   from empirica.api.middleware.security_headers import add_security_headers
   
   app = Flask(__name__)
   add_security_headers(app)
   ```

**Day 3: Testing & Validation**
1. Create XSS test suite
   ```python
   # tests/security/test_xss.py
   XSS_PAYLOADS = [
       '<script>alert("XSS")</script>',
       '<img src=x onerror=alert("XSS")>',
       '"><script>alert(String.fromCharCode(88,83,83))</script>',
       '<iframe src="javascript:alert(\'XSS\')">',
   ]
   
   def test_xss_in_session_description():
       for payload in XSS_PAYLOADS:
           session = create_session(description=payload)
           response = client.get(f'/api/sessions/{session.id}')
           # Verify payload is escaped
           assert '<script>' not in response.data.decode()
           assert '&lt;script&gt;' in response.data.decode()
   ```

2. Audit all user input points
   - CLI arguments
   - API request bodies
   - File uploads
   - URL parameters

#### Acceptance Criteria
- [ ] All user-generated content is escaped
- [ ] Security headers implemented
- [ ] CSP policy defined and active
- [ ] XSS test suite passes
- [ ] All input points audited
- [ ] Documentation updated

#### Files Created/Modified
- `empirica/security/output_encoding.py` (NEW)
- `empirica/api/middleware/security_headers.py` (NEW)
- `empirica/api/app.py` (MODIFY)
- `empirica/api/routes/*.py` (MODIFY - add escaping)
- `tests/security/test_xss.py` (NEW)

---

### WP-007: CSRF Protection

**Control ID:** SEC-014 (NEW)  
**Priority:** HIGH  
**Effort:** 2 days  
**Dependencies:** None

#### Objectives
Implement CSRF token protection for state-changing operations.

#### Tasks

**Day 1: Implementation**
1. Install Flask-WTF
   ```bash
   pip install Flask-WTF
   ```

2. Configure CSRF protection
   ```python
   # empirica/api/app.py
   from flask_wtf.csrf import CSRFProtect
   
   app = Flask(__name__)
   app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
   csrf = CSRFProtect(app)
   
   # Exempt read-only endpoints
   @csrf.exempt
   @app.route('/api/sessions/<session_id>', methods=['GET'])
   def get_session(session_id):
       pass
   ```

3. Add SameSite cookie attribute
   ```python
   app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
   app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
   app.config['SESSION_COOKIE_HTTPONLY'] = True
   ```

**Day 2: Testing & Documentation**
1. Create CSRF tests
   ```python
   def test_csrf_protection():
       # Try to create session without CSRF token
       response = client.post('/api/session-create', json={})
       assert response.status_code == 400
       
       # Get CSRF token
       csrf_token = client.get('/api/csrf-token').json['token']
       
       # Try with token
       response = client.post(
           '/api/session-create',
           json={},
           headers={'X-CSRF-Token': csrf_token}
       )
       assert response.status_code == 200
   ```

2. Document for API users
   - How to get CSRF token
   - Include token in requests
   - Handle token expiration

#### Acceptance Criteria
- [ ] CSRF protection enabled
- [ ] SameSite cookies configured
- [ ] Tests pass
- [ ] API documentation updated

#### Files Created/Modified
- `empirica/api/app.py` (MODIFY)
- `pyproject.toml` (MODIFY - add Flask-WTF)
- `tests/security/test_csrf.py` (NEW)
- `docs/api/CSRF_PROTECTION.md` (NEW)

---

(Continue with similar detailed work packages for WP-008 through WP-018...)

---

## Work Package Template

When creating new work packages, use this template:

```markdown
### WP-XXX: [Work Package Title]

**Control ID:** SEC-XXX  
**Priority:** CRITICAL | HIGH | MEDIUM | LOW  
**Effort:** X days  
**Dependencies:** WP-XXX, WP-YYY

#### Objectives
[Clear statement of what this work package achieves]

#### Tasks
**Day 1: [Phase Name]**
1. [Specific task]
2. [Specific task]
   ```python
   # Example code
   ```

**Day X: [Phase Name]**
1. [Specific task]

#### Acceptance Criteria
- [ ] [Testable criterion]
- [ ] [Testable criterion]

#### Files Created/Modified
- `path/to/file.py` (NEW | MODIFY)
```

---

## Progress Tracking

Use this section to track overall progress:

### Phase 1: Critical Foundations
- [ ] WP-001: Prompt Injection Detector
- [ ] WP-002: SQL Injection Prevention Audit
- [ ] WP-003: Secure Session Management
- [ ] WP-004: RBAC Authorization Model
- [ ] WP-005: Secret Scanning Pipeline

### Phase 2: Web Application Security
- [ ] WP-006: XSS Prevention
- [ ] WP-007: CSRF Protection
- [ ] WP-008: API Token Management
- [ ] WP-009: Rate Limiting

### Phase 3: Advanced Security
- [ ] WP-010: Command Injection Prevention
- [ ] WP-011: Path Traversal Protection
- [ ] WP-012: NoSQL Injection Prevention
- [ ] WP-013: Security Audit Logger
- [ ] WP-014: Anomaly Detection

### Phase 4: Testing & Compliance
- [ ] WP-015: Security Test Suite
- [ ] WP-016: Automated Security Scanning
- [ ] WP-017: HIPAA Compliance Enhancement
- [ ] WP-018: Security Documentation

---

## Notes for Implementers

1. **Test-Driven Approach**: Write tests first, then implementation
2. **Incremental Deployment**: Deploy and validate each work package
3. **Security Review**: Each WP should be reviewed before merging
4. **Documentation**: Update docs as you implement, not after
5. **Team Sync**: Brief the team on new security controls

---

*This is a living document. Update as work packages are completed or new security requirements emerge.*
