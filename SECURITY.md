# Security Policy

## Supported Versions

We actively support the following versions of Empirica with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :x:                |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

We take security seriously and appreciate responsible disclosure. If you discover a security vulnerability in Empirica, please report it to us following these guidelines:

### How to Report

1. **Email:** Send details to the project maintainers (see AUTHORS file or repository owners)
2. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)
   - Your contact information

### What to Expect

- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days
- **Fix Timeline:**
  - Critical: 48 hours
  - High: 1 week
  - Medium: 2 weeks
  - Low: Next release cycle

### Disclosure Policy

- We will work with you to understand and validate the issue
- We will develop and test a fix
- We will coordinate disclosure timing with you
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices

When using Empirica, follow these best practices:

### Dependency Management

1. **Keep dependencies updated:**
   ```bash
   pip install --upgrade empirica
   ```

2. **Use lock files:**
   ```bash
   # Generate from pyproject.toml
   pip-compile pyproject.toml -o requirements-lock.txt
   
   # Install from lock file
   pip install -r requirements-lock.txt
   ```

3. **Regular security audits:**
   ```bash
   pip install pip-audit
   pip-audit
   ```

### Configuration Security

1. **YAML Files:** All YAML loading uses `yaml.safe_load()` by design
   - Config files are for dynamic context injection
   - Not intended for untrusted/public input
   - Always validate configuration sources

2. **Secrets Management:**
   - Never commit secrets to git
   - Use environment variables or secret management tools (e.g., Doppler)
   - See `SECRETS.md` for project-specific guidance

3. **API Keys:**
   - Store in environment variables or `.env` files (gitignored)
   - Use credential rotation policies
   - Limit API key permissions to minimum required

### Git Notes Security

Empirica uses git notes for metadata storage:

1. **Local repositories:** git notes are safe
2. **Shared repositories:** Be aware git notes can be pushed/pulled
3. **Sensitive data:** Don't store secrets in git notes
4. **Access control:** Use repository permissions appropriately

### AI Identity & Checkpoint Signing

Empirica uses cryptography for:
- AI identity verification
- Checkpoint signing
- Secure data integrity

**Requirements:**
- `cryptography>=42.0.4` (critical security fixes)
- Keep this package updated
- Verify signatures on critical operations

## Known Security Considerations

### YAML Configuration Files

**Status:** ✅ SECURE BY DESIGN

- All YAML loading uses `yaml.safe_load()` (not `yaml.load()`)
- Config files are for internal/developer use
- Not exposed to public/untrusted input
- Dynamic context injection is intentional architecture

**Mitigation:** No action required - secure by default

### Git Notes Integration

**Status:** ⚠️ AWARENESS REQUIRED

- Git notes store epistemic metadata
- Can be pushed to remote repositories
- Not encrypted by default

**Mitigation:**
- Review repository access controls
- Don't store secrets in git notes
- Use private repositories for sensitive projects

### API Integrations (Anthropic, OpenAI, etc.)

**Status:** ⚠️ USER RESPONSIBILITY

- API keys grant access to AI services
- Costs can accumulate
- Data sent to third-party APIs

**Mitigation:**
- Use environment variables for API keys
- Set spending limits on AI service accounts
- Review data privacy policies
- Consider self-hosted alternatives when appropriate

## Dependency Security Updates

### Current Status (2026-01-05)

Recent security audit identified and addressed:
- ✅ cryptography: Updated to >=42.0.4 (CVE fixes)
- ✅ gitpython: Updated to >=3.1.43 (RCE fix)
- ✅ setuptools: Updated to >=78.1.1 (path traversal fix)
- ✅ requests: Updated to >=2.32.3 (credential leak fix)

See `DEPENDENCY_SECURITY_SPEC.md` for full details.

### Automated Monitoring

We recommend:

1. **GitHub Dependabot:** Enable in repository settings
2. **CI/CD Security Scanning:** Add pip-audit to workflows
3. **Monthly Reviews:** Check for new vulnerabilities

### Update Policy

| Severity | Response Time | Release Cycle |
|----------|---------------|---------------|
| Critical | 48 hours      | Emergency patch |
| High     | 1 week        | Patch release |
| Medium   | 2 weeks       | Minor release |
| Low      | Next cycle    | Regular release |

## Security Features

### Built-in Security

Empirica includes:
- ✅ Secure YAML loading (`safe_load` only)
- ✅ Cryptographic signatures for data integrity
- ✅ Git notes for tamper-evident metadata
- ✅ Input validation with Pydantic models
- ✅ SQLAlchemy for SQL injection protection

### Optional Security Features

Available through integrations:
- HTTPS for API endpoints (Flask/FastAPI)
- Authentication/authorization (via plugins)
- Encrypted storage (via external tools)
- Audit logging (via BEADS integration)

## Compliance

### OWASP Top 10 (2021)

| Category | Status | Notes |
|----------|--------|-------|
| A01: Broken Access Control | ⚠️ User Responsibility | Configure git repo permissions |
| A02: Cryptographic Failures | ✅ Addressed | Uses modern cryptography library |
| A03: Injection | ✅ Addressed | SQLAlchemy, safe YAML loading |
| A04: Insecure Design | ✅ Addressed | Secure by default architecture |
| A05: Security Misconfiguration | ⚠️ User Responsibility | Follow best practices guide |
| A06: Vulnerable Components | ✅ Addressed | Regular dependency updates |
| A07: Auth/AuthZ Failures | ⚠️ User Responsibility | Implement as needed |
| A08: Software/Data Integrity | ✅ Addressed | Cryptographic signatures |
| A09: Logging Failures | ⚠️ Partial | BEADS provides audit trail |
| A10: SSRF | ✅ Addressed | No unvalidated URL requests |

### Supply Chain Security

- Dependencies with upper bound constraints
- Regular security audits
- GitHub Advisory Database monitoring
- Reproducible builds (via lock files)

## Contact

For security-related questions or concerns:
- **Security Issues:** Report privately to maintainers
- **General Questions:** Open a GitHub Discussion
- **Documentation:** See project README and docs/

## Acknowledgments

We thank the security researchers and developers who help keep Empirica secure:
- GitHub Advisory Database
- Python Security Team
- Dependency maintainers
- Community contributors

---

**Last Updated:** 2026-01-05  
**Next Review:** 2026-04-05
