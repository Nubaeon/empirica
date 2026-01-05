# 🚀 Security Implementation Quick Start

**Version:** 1.0.0  
**For:** Development Team  
**Goal:** Get started with security enhancements quickly

---

## First Week Checklist

Use this checklist to make immediate security improvements while the full roadmap is being planned.

### Day 1: Assessment & Setup

- [ ] **Read Security Documentation** (2 hours)
  - [ ] Read [SECURITY_README.md](./SECURITY_README.md)
  - [ ] Skim [SECURITY_SPECIFICATION.md](./SECURITY_SPECIFICATION.md) sections 1-2
  - [ ] Review existing security features (Sentinel, memory gap detector)

- [ ] **Set Up Development Environment** (1 hour)
  - [ ] Install dependencies: `pip install -e ".[api,vector]"`
  - [ ] Set up Doppler: Follow [SECRETS.md](../SECRETS.md)
  - [ ] Verify tests run: `pytest tests/ -v`

- [ ] **Install Security Tools** (1 hour)
  ```bash
  # Install security scanning tools
  pip install bandit safety
  
  # Install pre-commit hooks (if not already)
  pip install pre-commit
  pre-commit install
  
  # Run initial scans
  bandit -r empirica/ -f json -o security-scan.json
  safety check --json
  ```

### Day 2: Quick Wins

- [ ] **Secret Scanning** (2 hours) - WP-005 (simplified)
  - [ ] Run: `git log --all --pretty=format:%H | head -20`
  - [ ] Manually check recent commits for secrets
  - [ ] Update `.gitignore` if needed
  - [ ] Add basic pre-commit hook:
    ```bash
    # Create .git/hooks/pre-commit
    #!/bin/bash
    if git diff --cached | grep -E "api_key|password|secret|token" | grep -v "^#"; then
        echo "⚠️  Warning: Potential secret detected. Review carefully."
        echo "Continue? (y/n)"
        read answer
        if [ "$answer" != "y" ]; then
            exit 1
        fi
    fi
    ```

- [ ] **SQL Injection Audit** (3 hours) - WP-002 (partial)
  - [ ] Find all database operations:
    ```bash
    grep -r "execute\|query" empirica/data/repositories/ --include="*.py" > sql-audit.txt
    ```
  - [ ] Review each for user input
  - [ ] Document in spreadsheet: File | Line | Safe? | Notes
  - [ ] Fix any obvious issues found

### Day 3: Testing Infrastructure

- [ ] **Create Security Test Directory** (1 hour)
  ```bash
  mkdir -p tests/security
  touch tests/security/__init__.py
  touch tests/security/conftest.py
  ```

- [ ] **Write First Security Test** (2 hours)
  ```python
  # tests/security/test_sql_injection.py
  import pytest
  from empirica.data.repositories.cascades import CascadeRepository
  
  def test_phase_validation_prevents_sql_injection():
      """Verify phase parameter validation prevents SQL injection"""
      repo = CascadeRepository()
      
      malicious_inputs = [
          "'; DROP TABLE sessions; --",
          "' OR '1'='1",
          "admin'--",
          "1; UPDATE sessions SET owner='attacker'--"
      ]
      
      for malicious in malicious_inputs:
          with pytest.raises(ValueError, match="Invalid phase"):
              repo.update_cascade_phase("cascade-123", malicious)
  
  def test_valid_phases_accepted():
      """Verify legitimate phases are accepted"""
      repo = CascadeRepository()
      valid_phases = ['preflight', 'check', 'postflight']
      
      for phase in valid_phases:
          # Should not raise
          try:
              # Note: This will fail if cascade doesn't exist, but won't raise ValueError
              repo.update_cascade_phase("cascade-123", phase)
          except ValueError as e:
              if "Invalid phase" in str(e):
                  pytest.fail(f"Valid phase '{phase}' was rejected")
  ```

- [ ] **Run Test** (15 minutes)
  ```bash
  pytest tests/security/test_sql_injection.py -v
  ```

### Day 4: Documentation & Planning

- [ ] **Document Current State** (2 hours)
  - [ ] Create `docs/security/CURRENT_STATE.md`
  - [ ] List all database operations audited
  - [ ] Document secret scanning results
  - [ ] Note any vulnerabilities found

- [ ] **Prioritize Work Packages** (2 hours)
  - [ ] Review [SECURITY_WORK_PACKAGES.md](./SECURITY_WORK_PACKAGES.md)
  - [ ] Select 3-5 work packages for next sprint
  - [ ] Estimate effort with team
  - [ ] Assign owners

- [ ] **Team Sync** (1 hour)
  - [ ] Present security findings to team
  - [ ] Discuss priorities
  - [ ] Get buy-in for security work

### Day 5: CI/CD Integration

- [ ] **Add Security to CI** (3 hours)
  - [ ] Create `.github/workflows/security.yml`:
    ```yaml
    name: Security Checks
    
    on: [push, pull_request]
    
    jobs:
      security-tests:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v3
          
          - name: Set up Python
            uses: actions/setup-python@v4
            with:
              python-version: '3.11'
          
          - name: Install dependencies
            run: |
              pip install -e .
              pip install bandit safety pytest
          
          - name: Run Bandit (SAST)
            run: bandit -r empirica/ -ll -f json -o bandit-report.json || true
          
          - name: Check dependencies
            run: safety check --json || true
          
          - name: Run security tests
            run: pytest tests/security/ -v
          
          - name: Upload results
            uses: actions/upload-artifact@v3
            if: always()
            with:
              name: security-reports
              path: |
                bandit-report.json
    ```

- [ ] **Test Workflow** (30 minutes)
  - [ ] Commit and push
  - [ ] Verify workflow runs
  - [ ] Check results

---

## Priority Order for Work Packages

Based on risk and effort, implement in this order:

### Week 1-2: Critical Foundations
1. **WP-005: Secret Scanning** (2 days) - Quick win, prevents future issues
2. **WP-002: SQL Injection Audit** (2 days) - Complete the audit from Day 2
3. **WP-003: Session Management** (3 days) - Critical for auth
4. **WP-001: Prompt Injection Detector** (3 days) - AI-specific threat

### Week 3-4: Web Security
5. **WP-006: XSS Prevention** (3 days) - Protect web interfaces
6. **WP-007: CSRF Protection** (2 days) - State-changing operations
7. **WP-009: Rate Limiting** (3 days) - DoS protection

### Week 5-6: Authorization & Advanced
8. **WP-004: RBAC** (5 days) - Define access control model
9. **WP-013: Audit Logger** (3 days) - Compliance requirement
10. **WP-010: Command Injection** (3 days) - High severity

---

## Quick Command Reference

### Security Scanning
```bash
# SAST with Bandit
bandit -r empirica/ -ll -f json -o security-scan.json

# Dependency vulnerabilities
safety check --json

# Secret scanning (requires trufflehog)
trufflehog filesystem . --json > secret-scan.json

# Run security tests
pytest tests/security/ -v --cov=empirica/security
```

### Database Auditing
```bash
# Find all SQL operations
grep -r "_execute\|execute\|query" empirica/data/repositories/ \
  --include="*.py" | grep -v "test" > sql-operations.txt

# Find string formatting in queries (danger!)
grep -r "f\".*SELECT\|f'.*SELECT" empirica/ --include="*.py"
grep -r '%.format' empirica/data/ --include="*.py"
```

### Session Management
```bash
# List active sessions
empirica sessions-list --active

# Invalidate session
empirica session-invalidate --session-id <id>

# Check session validity
empirica session-validate --session-id <id>
```

### MCP Sentinel
```bash
# Check Sentinel status
empirica sentinel-status --session-id <id>

# Load security profile
empirica sentinel-load-profile --profile healthcare --session-id <id>

# Run compliance check
empirica sentinel-check --session-id <id> --know 0.7 --uncertainty 0.3
```

---

## Common Security Patterns

### Input Validation
```python
# Always validate user input before using in queries
VALID_VALUES = {'option1', 'option2', 'option3'}

def validate_input(user_input: str) -> str:
    if user_input not in VALID_VALUES:
        raise ValueError(f"Invalid input: {user_input}")
    return user_input

# Use in function
def process_data(input_value: str):
    validated = validate_input(input_value)  # Validate first
    # Now safe to use
    query = f"SELECT * FROM table WHERE col = ?"
    execute(query, (validated,))  # Still use parameterized queries
```

### Output Encoding
```python
from html import escape

def render_user_content(user_text: str) -> str:
    """Always escape user-generated content before display"""
    return escape(user_text, quote=True)

# In API
@app.route('/api/session/<id>')
def get_session(id):
    session = get_session_data(id)
    # Escape user-generated fields
    session['description'] = render_user_content(session['description'])
    return jsonify(session)
```

### Secret Handling
```python
import os

# GOOD: Use environment variables
api_key = os.environ.get('API_KEY')
if not api_key:
    raise ValueError("API_KEY not set")

# BAD: Never hardcode
api_key = "sk-1234567890abcdef"  # DON'T DO THIS

# Log safely (mask secrets)
logger.info(f"Using API key: {api_key[:8]}...")  # Only log prefix
```

### Session Validation
```python
from datetime import datetime, UTC

def validate_session(session_id: str) -> bool:
    """Check session is valid and not expired"""
    session = get_session(session_id)
    
    if not session:
        return False
    
    if session.invalidated:
        return False
    
    if datetime.now(UTC) > session.expires_at:
        return False
    
    return True

# Use in API
@app.before_request
def check_session():
    session_id = request.headers.get('X-Session-ID')
    if session_id and not validate_session(session_id):
        abort(401, "Invalid or expired session")
```

---

## When to Escalate

Contact security team immediately if you find:

- **P0 - Immediate**: Active attack, data breach, exposed secrets in public repo
- **P1 - Same Day**: SQL injection vulnerability, authentication bypass
- **P2 - Next Day**: XSS vulnerability, missing authorization checks
- **P3 - This Week**: Outdated dependencies, configuration issues

**Security Contact**: [TBD - Set this up!]

---

## Resources

### Internal Docs
- [SECURITY_SPECIFICATION.md](./SECURITY_SPECIFICATION.md) - Complete specification
- [SECURITY_WORK_PACKAGES.md](./SECURITY_WORK_PACKAGES.md) - Implementation guide
- [SECURITY_README.md](./SECURITY_README.md) - Quick navigation

### External Resources
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP LLM Top 10](https://llmtop10.com/)
- [Python Security Best Practices](https://snyk.io/blog/python-security-best-practices/)
- [Flask Security](https://flask.palletsprojects.com/en/2.3.x/security/)

### Tools
- [Bandit](https://bandit.readthedocs.io/) - Python SAST
- [Safety](https://pyup.io/safety/) - Dependency scanner
- [TruffleHog](https://github.com/trufflesecurity/trufflehog) - Secret scanner
- [OWASP ZAP](https://www.zaproxy.org/) - Web app scanner

---

## FAQ

**Q: Do I need to run security scans on every commit?**  
A: Not manually. Set up CI/CD (Day 5) to run automatically. Do run locally before major PRs.

**Q: What if I find a vulnerability?**  
A: Document it, create a private GitHub security advisory, notify the team. Don't commit a public issue.

**Q: Can I skip XSS protection if we're API-only?**  
A: No. Even JSON APIs can be vulnerable if content is displayed in web contexts. Always encode output.

**Q: How do I test security fixes?**  
A: Write a test that demonstrates the vulnerability, fix it, verify the test passes. See Day 3.

**Q: Do existing tests cover security?**  
A: Some do (SQL injection in cascades.py), but dedicated security tests are needed. That's WP-015.

**Q: Is Doppler required?**  
A: Yes for production. For local development, you can use `.env` but never commit it.

---

## Success Metrics

Track these to measure security improvements:

- [ ] **Test Coverage**: Security tests >80% coverage
- [ ] **Scan Results**: 0 high/critical findings in Bandit
- [ ] **Dependency Security**: 0 known vulnerabilities in Safety
- [ ] **Secret Scanning**: 0 secrets in git history
- [ ] **Incident Response**: <1 hour response time for P1
- [ ] **Compliance**: All domain profile gates passing

---

*Questions? Open an issue or contact the security team.*
