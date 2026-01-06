# Empirica Privacy Agent

**Goal ID:** `1b5197c4-f191-499a-8840-ccf69a05b36c`  
**Status:** Planned  
**Complexity:** 0.65  
**Motivation:** Prevent "automating stupidity" as Empirica adoption grows

---

## Problem Statement

Git privacy is poorly understood. Most developers don't realize:
- `.gitignore` is **publicly visible** on GitHub
- It reveals internal project structure, other platforms, strategies
- Listing `twitter/`, `REDDIT_APPLICATION*.md`, `.empirica/` exposes your operations

**Real incident:** Preparing empirica-outreach for Reddit API review, we exposed:
- Other platforms (twitter, discord, hackernews)
- Planning documents (*PLAN.md, *STRATEGY.md)
- Internal framework paths (.empirica/)
- Application drafts (REDDIT_APPLICATION*.md)

This leaked our multi-platform strategy to Reddit reviewers.

---

## The Core Insight

**"Automates stupidity as well as intelligence"**

As Empirica enables sophisticated multi-platform operations:
- Users will have sensitive internal docs
- Automated workflows will generate strategy files
- Multi-AI coordination will create coordination artifacts

**Without privacy awareness, Empirica will amplify privacy mistakes at scale.**

---

## Solution: Epistemic Privacy Sentinel

Pre-push scanner that reasons about information disclosure:
- "Does this pattern reveal project scope?"
- "Would an adversary learn something from this?"
- "Is this exposing coordination between platforms?"

Acts as **circuit breaker** for privacy leaks.

---

## Features

### 1. Pattern Detection
**Scans `.gitignore` for:**
- Platform names: `twitter/`, `discord/`, `hackernews/`, `linkedin/`
- Doc patterns: `*PLAN*.md`, `*STRATEGY*.md`, `REDDIT_APPLICATION*`
- Framework internals: `.empirica/`, `.qdrant_data/`
- Project-specific: `research/`, `assets/`, `spec/`

### 2. Commit Message Scanner
**Detects context leaks:**
- Platform mentions: "Updated Twitter strategy"
- Internal terminology: "MCO handoff", "epistemic vault"
- Sensitive context: "Preparing for Reddit review"

### 3. Filename Checker
**Flags revealing names:**
- `REDDIT_APPLICATION.md` (reveals application in progress)
- `TWITTER_STRATEGY.md` (exposes other channels)
- `COMPETITOR_ANALYSIS.md` (obvious leak)

### 4. Auto-Fix Mode
**Automatically:**
- Moves sensitive patterns from `.gitignore` to `.git/info/exclude`
- Preserves comments and structure
- Reports what was changed and why

### 5. Git Hook Integration
**Pre-push validation:**
```bash
empirica privacy-install-hook --strict
# Blocks pushes if privacy issues detected
```

---

## CLI Commands

```bash
# Scan current repo
empirica privacy-scan

# Show detailed analysis
empirica privacy-scan --verbose

# Auto-fix issues
empirica privacy-scan --auto-fix

# Check specific file
empirica privacy-check .gitignore

# Install pre-push hook
empirica privacy-install-hook

# Strict mode (blocks pushes)
empirica privacy-install-hook --strict
```

---

## Output Example

```json
{
  "ok": false,
  "repo": "/home/user/empirica-outreach",
  "scan_timestamp": "2026-01-03T15:30:00Z",
  "issues": [
    {
      "file": ".gitignore",
      "line": 45,
      "pattern": "twitter/",
      "risk": "high",
      "reasoning": "Reveals multi-platform operations to Reddit reviewers",
      "suggestion": "Move to .git/info/exclude (local-only ignores)",
      "fix_command": "empirica privacy-scan --auto-fix"
    },
    {
      "file": ".gitignore",
      "line": 67,
      "pattern": "REDDIT_APPLICATION*.md",
      "risk": "medium",
      "reasoning": "Exposes that you're applying for Reddit API access",
      "suggestion": "Move to .git/info/exclude"
    }
  ],
  "commit_issues": [
    {
      "commit": "3cb1a19",
      "message": "Update Twitter outreach strategy",
      "risk": "medium",
      "reasoning": "Mentions other platform in public commit history"
    }
  ],
  "summary": {
    "total_issues": 3,
    "high_risk": 1,
    "medium_risk": 2,
    "auto_fixable": 2
  }
}
```

---

## Educational Component

Privacy agent teaches while protecting:

**On first run:**
```
🔒 Empirica Privacy Scan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️  Did you know?
.gitignore is PUBLIC and visible on GitHub. Listing sensitive
patterns reveals your internal project structure.

Use .git/info/exclude for private patterns instead.
Learn more: empirica privacy-scan --explain

Found 3 privacy issues. Run with --auto-fix to resolve.
```

---

## Git Privacy Best Practices

### Two-Tier Ignore Strategy

**`.gitignore` (public):**
```gitignore
# Generic patterns everyone needs
__pycache__/
*.pyc
.env
*.db
node_modules/
```

**`.git/info/exclude` (local-only, NEVER pushed):**
```gitignore
# Your internal structure (private)
twitter/
discord/
hackernews/
*PLAN*.md
*STRATEGY*.md
REDDIT_APPLICATION*.md
.empirica/
research/
```

### Key Insight
`.git/info/exclude` has same syntax as `.gitignore` but lives in `.git/info/exclude` and is **never** pushed to remote.

---

## Implementation Roadmap

### Phase 1: Research (2-3 days)
- Survey developer awareness (Reddit, HN, Twitter)
- Document common misconceptions
- Analyze real-world .gitignore leaks

### Phase 2: Design (3-4 days)
- Define pattern detection rules
- Create risk scoring system
- Design epistemic reasoning logic

### Phase 3: Core Implementation (1 week)
- Build `empirica privacy-scan` command
- Implement .gitignore analyzer
- Add commit message scanner
- Create filename checker

### Phase 4: Auto-Fix (3-4 days)
- Pattern migration logic
- .git/info/exclude management
- Preserve comments/structure

### Phase 5: Git Integration (2-3 days)
- Pre-push hook installer
- Strict mode implementation
- Hook uninstaller

### Phase 6: Testing (1 week)
- Real-world repo validation
- False positive elimination
- Edge case handling

### Phase 7: Documentation (2-3 days)
- .git/info/exclude guide
- Git privacy fundamentals
- Usage examples

---

## Success Criteria

✅ Detects leaky patterns with zero false positives  
✅ Auto-fix mode works seamlessly  
✅ Pre-push hook blocks privacy leaks  
✅ Educational warnings explain reasoning  
✅ Handles edge cases gracefully  
✅ Documentation comprehensive  
✅ Users understand .git/info/exclude after first use

---

## Long-Term Vision

**Epistemic Security Framework:**
- Privacy agent for git exposure
- Secret detection in code/comments
- Context leak detection in docs
- Multi-repo coordination analysis
- Adversarial simulation ("What can they infer?")

**Goal:** Build privacy awareness into Empirica's core, so users can't accidentally expose internal operations even in complex multi-platform, multi-AI workflows.

**Principle:** Automate intelligence, prevent automating stupidity.

---

## Related

- Mistake: `22e37f2a-3e60-46bd-9772-b3b9c03a4d81` (.gitignore privacy leak)
- Finding: `9a946cc6-d703-41a6-84ea-0546ce2817fe` (.git/info/exclude solution)
- Unknown: `efc72d5c-fa47-44fb-8c96-dcf0329e2c24` (developer awareness research)

---

**Created:** 2026-01-03  
**Session:** `copilot-outreach-cleanup`  
**Priority:** High (prevents scaling privacy mistakes)
