# Epistemic Commit Hook - Quick Reference

**What:** Git hook that automatically injects learning metrics into commits
**Where:** `.git/hooks/prepare-commit-msg`
**Status:** ✅ Installed and working
**Impact:** Every commit now shows what you learned making it

---

## Quick Examples

### View Learning in Your Last Commit

```bash
# Show all epistemic trailers
git log -1 --pretty=format:"%(trailers)" | grep Epistemic

# Show just learning delta
git log -1 --pretty=format:"%(trailers:key=Epistemic-Learning-Delta,valueonly)"
```

### Find Commits With Learning Growth

```bash
# Show commits with learning deltas
git log --all --pretty=format:"%h %s | %(trailers:key=Epistemic-Learning-Delta,valueonly)" | head -20

# Filter to high-learning commits (+0.10 or more)
git log --all --pretty=format:"%h | %(trailers:key=Epistemic-Learning-Delta)" | grep -E "\+0\.[1-9]|+[1-9]"
```

### Analyze Team Learning

```bash
# Total team learning
git log --all --pretty=format:"%(trailers:key=Epistemic-Learning-Delta)" \
  | grep -oE '[+-][0-9.]+' | awk '{sum+=$1} END {print "Total:", sum}'

# Learning by AI agent
for ai in claude-code claude-sonnet qwen-code; do
  echo -n "$ai: "
  git log --all --grep="Epistemic-AI: $ai" --pretty=format:"%(trailers:key=Epistemic-Learning-Delta)" \
    | grep -oE '[+-][0-9.]+' | awk '{sum+=$1} END {print sum}'
done
```

---

## What You'll See

Every commit now has trailers like this:

```
Epistemic-AI: claude-code
Epistemic-Model: claude-haiku-4-5
Epistemic-Persona: implementer

Epistemic-Learning-Delta: 0.15 (0.65 → 0.8)
Epistemic-Mastery-Delta: 0.25 (0.55 → 0.80)
Epistemic-Uncertainty-Delta: -0.25 (0.45 → 0.2)
Epistemic-Engagement: 0.85
Epistemic-Completion: 1.0
Epistemic-Session: f3a61cfc-9d4d-455e-b88e-b3f3358f6a10
```

**Reading this:**
- **Learning-Delta: 0.15** = Gained 0.15 points of knowledge
- **Mastery-Delta: 0.25** = Uncertainty improved 0.25 points
- **Uncertainty-Delta: -0.25** = Confusion reduced (negative = better)
- **Session** = Links to SQLite for full epistemic data

---

## How It Works (Simple Version)

1. You commit code
2. Git runs the hook (invisible)
3. Hook checks: "Did this AI learn something?"
   - Reads PREFLIGHT vectors (start of session)
   - Reads POSTFLIGHT vectors (end of session)
   - Calculates difference
4. Hook adds trailers to commit message
5. Commit is saved with learning metrics
6. You can see learning in `git log`

---

## Essential Trailers (Always Present)

| Trailer | Means | Example |
|---------|-------|---------|
| **Epistemic-AI** | Who made it | `claude-code` |
| **Epistemic-Model** | Which model | `claude-haiku-4-5` |
| **Epistemic-Learning-Delta** | Knowledge growth | `+0.15 (0.70 → 0.85)` |
| **Epistemic-Mastery-Delta** | Better decisions | `+0.20 (0.75 → 0.95)` |
| **Epistemic-Session** | Session ID | `f3a61cfc-...` |

---

## Validation

Test the hook:

```bash
./test-commit-hook.sh
```

Expected: All checks pass ✅

---

## Integration Points

The epistemic data in commits can be:
- **Aggregated** by leaderboard (learning growth)
- **Graphed** by statusline (learning trends)
- **Searched** by GitHub (find commits by AI agent)
- **Analyzed** by dashboards (team performance)
- **Exported** for reports (learning metrics over time)

---

## Performance

- **Overhead:** <100ms per commit
- **Graceful fallback:** Works even if database is down
- **Zero disruption:** Commits proceed normally with or without data

---

## Examples in the Wild

```bash
# "Show me commits where Claude learned a lot"
git log --all --pretty=format:"%h %s" \
  --grep="Epistemic-AI: claude-code" | head

# "What's the learning rate (learning per commit)?"
TOTAL_LEARNING=$(git log --all --pretty=format:"%(trailers:key=Epistemic-Learning-Delta)" \
  | grep -oE '[+-][0-9.]+' | awk '{sum+=$1} END {print sum}')
TOTAL_COMMITS=$(git rev-list --count HEAD)
echo "Learning per commit: $(echo "scale=4; $TOTAL_LEARNING / $TOTAL_COMMITS" | bc)"

# "Which AI is learning fastest?"
git log --all --pretty=format:"%(trailers:key=Epistemic-AI) %(trailers:key=Epistemic-Learning-Delta)" \
  | awk '{ai=$1; delta=$NF; sum[ai]+=(delta+0)} END {for (a in sum) print a": "sum[a]}' | sort -t: -k2 -nr
```

---

## Troubleshooting

**Q: Why do some commits not have trailers?**
A: Commits made before the hook was installed, or made without CASCADE PREFLIGHT/POSTFLIGHT data.

**Q: Can I view the hook log?**
A: Yes, check `/tmp/empirica_commit_hook.log` for debug info.

**Q: Does the hook slow down commits?**
A: No, <100ms overhead (barely noticeable).

**Q: What if the database is down?**
A: Hook gracefully skips adding trailers. Commits proceed normally.

---

## Related Commands

```bash
# See all our tools for epistemic data
ls -la | grep epistemic

# Run analytics
./empirica-git-stats.sh

# Read full documentation
cat EPISTEMIC_COMMIT_HOOK_IMPLEMENTATION.md

# See the hook source
cat .git/hooks/prepare-commit-msg
```

---

## The Philosophy

Every commit should answer: **"What did I learn making this change?"**

With this hook, that answer is now visible in git history.

```
Before: "I made a commit" ← No context on learning
After:  "I learned 0.15 points making this commit" ← Transparent
```

This is what measured, responsible AI development looks like.

---

**Status:** ✅ Live in repository
**First commit with data:** d8f77978 (hook implementation)
**Last verified:** 2025-12-06
