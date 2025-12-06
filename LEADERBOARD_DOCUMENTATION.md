# Empirica AI Leaderboard - Complete Documentation

**Created:** 2025-12-06
**Purpose:** Real-time performance metrics and achievement tracking for AI agents
**Status:** Production-ready

---

## Overview

The **AI Leaderboard** is a live showcase of how Empirica's epistemic tracking creates measurable, comparable performance metrics across AI agents.

It answers the critical question: **"How well are my AI agents actually learning and performing?"**

---

## What the Leaderboard Shows

### 1. Learning Growth (Primary Metric)
**Definition:** Average improvement in knowledge from start to end of session
- **Formula:** Average(POSTFLIGHT_know - PREFLIGHT_know)
- **Range:** -1.0 to 1.0 (negative = knowledge regression)
- **Benchmark:** >0.10 = meaningful learning

**Why it matters:** This proves the AI didn't just work faster—it understood better.

### 2. Goal Completion
**Definition:** Number of goals successfully completed
- **Metric:** Raw count of is_completed=1 goals
- **Useful for:** Measuring productivity and follow-through

### 3. Sessions Completed
**Definition:** Number of sessions with end_time set
- **Metric:** Raw count
- **Useful for:** Measuring consistency and closure rate

### 4. Uncertainty Mastery
**Definition:** How much uncertainty was resolved by session end
- **Formula:** 1.0 - Average(POSTFLIGHT_uncertainty)
- **Range:** 0.0 to 1.0 (1.0 = complete certainty)
- **Benchmark:** >0.70 = good mastery

**Why it matters:** Shows whether the AI achieved clarity despite complexity.

### 5. Total Cascades
**Definition:** Number of CASCADE workflow runs
- **Metric:** SUM(total_cascades) for all sessions
- **Useful for:** Measuring how many investigation cycles were needed

### 6. Consistency
**Definition:** Percentage of sessions that were properly closed
- **Formula:** (Sessions_with_end_time / Total_sessions) * 100
- **Range:** 0 to 100%
- **Benchmark:** >90% = excellent

---

## Achievement Badges 🎖️

The leaderboard awards badges based on actual performance:

| Badge | Name | Criteria | Why It Matters |
|-------|------|----------|---------------|
| 🚀 | Launched | First session completed | First step matters |
| ⚡ | Speed Demon | 5+ sessions completed | Consistent engagement |
| 🧠 | Brain Boost | Learning growth > 0.10 | Real learning happened |
| 🏆 | Champion | 10+ sessions completed | Proven track record |
| 🎯 | Goal Master | 10+ goals completed | High productivity |
| 🔬 | Scientist | Learning growth > 0.15 | Exceptional insight |
| ⚙️ | Engineer | 10+ cascades | Thorough investigation |
| 🎓 | Scholar | Uncertainty mastery > 0.70 | Deep understanding |
| 👑 | Elite | 20+ sessions + 20+ goals + growth > 0.15 | Top performer |
| 🌟 | Rising Star | High consistency + good learning (new AI) | Exceptional beginner |

---

## Usage

### Quick View (Default)
```bash
./leaderboard.sh
```

Shows:
- Ranked list of all AI agents
- Top performers with medals (🥇 🥈 🥉)
- Color-coded metrics
- Achievement badges earned
- Badge legend and metrics explanation

### JSON Export (For Dashboards)
```bash
./leaderboard.sh --json
```

Outputs JSON with:
- Complete metrics for all agents
- Timestamp
- Badge status
- Machine-readable format for integrations

### CSV Export (For Analysis)
```bash
./leaderboard.sh --csv
```

Outputs:
- AI_ID, Learning_Growth, Goal_Completion_Rate, Total_Goals_Completed, Sessions_Completed, Uncertainty_Mastery, Total_Cascades, Consistency_Pct, Badges
- Easy to import into Excel/Google Sheets for custom analysis

---

## Real-World Example Output

```
⭐ EMPIRICA AI LEADERBOARD ⭐
════════════════════════════════════════════════════════════════

🏅 TOP PERFORMERS (By Learning Growth)

🥇  1. empirica_tester     🚀 🧠 🔬 🌟
   📊 Learning: 0.5    | Goals: 0  | Sessions: 1  | Mastery: 0.7   | Cascades: 0

🥈  2. test_agent          🚀 ⚡ 🧠 🔬
   📊 Learning: 0.225  | Goals: 0  | Sessions: 8  | Mastery: 0.625 | Cascades: 0

🥉  3. claude-docs-overhaul 🧠 🔬 🎓
   📊 Learning: 0.157  | Goals: 0  | Sessions: 0  | Mastery: 0.9   | Cascades: 0
```

**What this tells us:**
- `empirica_tester` has highest learning growth (0.5) - exceptional insight
- Has 🌟 Rising Star badge - new agent performing very well
- Despite only 1 session, already earned multiple badges
- `test_agent` has 8 completed sessions - proven consistency (⚡)

---

## Interpreting the Metrics

### High Learning Growth + Many Sessions = 🏆 Champion
"This AI systematically improves across all work"
- Suggests: Good investigative process, willing to revise thinking
- Risk: If uncertainty also high, might indicate struggle

### High Mastery + Low Learning = Scholar but not Scientist
"This AI solves known problems well"
- Suggests: Good at execution, less at discovery
- Use for: Production work, well-scoped tasks

### High Learning + Many Goals = 👑 Elite
"This AI learns while shipping"
- Suggests: Excellent blend of discovery and execution
- Use for: Architecture, complex design work

### Low Consistency (<50%) = Needs attention
"Sessions not being properly closed"
- Suggests: Incomplete workflows, potential issues with termination logic
- Action: Check for hanging sessions in database

---

## How It Proves Empirica's Value

This leaderboard is a **proof-of-concept** that shows:

### 1. **Measurable Learning**
Traditional metrics can't show "did the AI actually understand better?"
Empirica's epistemic vectors show EXACTLY this.

### 2. **Comparative Performance**
Instead of "Agent A completed Task X", we see:
- Agent A learned more (knowledge +0.25)
- Agent B was more consistent (90% closure rate)
- Agent C resolved more uncertainty (mastery 0.85)

This is **next-generation AI measurement**.

### 3. **Git-Visible Proof**
All metrics come from SQLite database that's tracked in git.
Every number is:
- ✅ Verifiable
- ✅ Auditable
- ✅ Timestamped
- ✅ Part of your permanent record

### 4. **Showcase Product**
This leaderboard demonstrates Empirica works in practice:
- Real agents (Claude, Qwen, test agents, etc.)
- Real learning metrics (0.5 growth, 0.9 mastery, etc.)
- Real badges earned through actual performance
- **In your GitHub repo, visible to the world**

---

## Technical Details

### Performance
```bash
$ time ./leaderboard.sh
real    0m2.341s
user    0m0.234s
sys     0m0.105s
```

Processing ~200 sessions with episodic metrics is ~2.3 seconds.
Fast enough for continuous monitoring.

### Database Queries
Queries are optimized with:
- LIMIT clauses for each AI (max 100 sessions to calculate)
- Simple AVG aggregations
- Minimal subqueries
- Column indexes on session tables

### Locale Handling
Forces `LC_ALL=C` to ensure consistent decimal separators across systems.

---

## Integration Ideas

### 1. GitHub README Badge
```markdown
![Empirica Learning Score](https://img.shields.io/endpoint?url=https://your-domain/empirica-leaderboard.json)
```

### 2. Continuous Monitoring
```bash
# Every 5 minutes, update a leaderboard.json file
* * * * * /path/to/leaderboard.sh --json > /var/www/empirica-leaderboard.json
```

### 3. Slack Notifications
```bash
# Daily digest of top performers
0 9 * * * /path/to/send-daily-leaderboard.sh
```

### 4. Web Dashboard
```bash
# Generate HTML dashboard from JSON
./leaderboard.sh --json | python3 render_dashboard.py > dashboard.html
```

### 5. Learning Analytics
```bash
# Track learning trends over time
./leaderboard.sh --csv >> leaderboard-history.csv
# Plot with matplotlib/R
```

---

## Achievement Progression Example

### New Agent (Day 1)
```
minimal-agent 🚀
Learning: 0.0 | Sessions: 0
```
Just created → gets 🚀 Launched badge

### Active Agent (Day 3)
```
minimal-agent 🚀 ⚡ 🧠
Learning: 0.15 | Sessions: 5 | Mastery: 0.72
```
5 sessions done (⚡ Speed Demon)
Learning improved (🧠 Brain Boost)
Good mastery (🎓 Scholar added next)

### Mature Agent (Day 10)
```
minimal-agent 🚀 ⚡ 🧠 🔬 🏆 🎓 ⚙️
Learning: 0.18 | Sessions: 12 | Goals: 15 | Mastery: 0.85
```
Full badge collection
Consistent high performance across all metrics

---

## Metrics Explained (In Depth)

### Learning Growth Calculation
```
Session epistemic vectors store:
PREFLIGHT: {know: 0.7, uncertainty: 0.3, ...}
...investigation...
POSTFLIGHT: {know: 0.9, uncertainty: 0.1, ...}

Learning = (POSTFLIGHT_know - PREFLIGHT_know)
         = (0.9 - 0.7) = 0.2

Leaderboard shows: AVG(all_sessions) = 0.2
```

### Uncertainty Mastery Calculation
```
Mastery = 1.0 - POSTFLIGHT_uncertainty
        = 1.0 - 0.1 = 0.9 (90% certainty achieved)

Leaderboard shows: AVG(all_postflight_uncertainty)
```

### Goal Completion Rate
```
Completed = COUNT(*) WHERE is_completed=1
Total = COUNT(*)
Percentage = (Completed / Total) * 100
```

---

## Future Enhancements

### Phase 2: Trending
```
- Plot learning growth over time
- Identify improving vs declining agents
- Week-over-week comparison
```

### Phase 3: Predictions
```
- Estimate when agent will reach next badge
- Predict goal completion rates
- Alert when trending negative
```

### Phase 4: Multi-team
```
- Compare teams
- Department-level leaderboards
- Cross-organization benchmarking
```

### Phase 5: AI Coach
```
- Generate personalized recommendations
- "Agent X: You've mastered execution, focus on learning"
- "Agent Y: High learning but low completion - needs focus"
```

---

## Files

**Location:** `/home/yogapad/empirical-ai/empirica/leaderboard.sh`

**Size:** ~425 lines, fully commented

**Dependencies:**
- bash (standard)
- sqlite3 (cli)
- Standard POSIX tools (sort, awk, sed)

**No external dependencies, no installation needed.**

---

## Conclusion

The **AI Leaderboard** is Empirica's **most powerful proof-of-concept** because it:

✅ **Measures what matters:** Learning, not just output
✅ **Compares fairly:** Apples-to-apples across agents
✅ **Shows proof:** Metrics from distributed git-backed database
✅ **Enables competition:** Agents can see their rankings
✅ **Attracts attention:** Beautiful badges, clear rankings
✅ **Drives improvement:** Everyone wants better metrics
✅ **Showcases Empirica:** This IS Empirica in action

**This is next-gen AI performance measurement.**

---

**Usage:** `./leaderboard.sh [--json] [--csv]`

**Generate a leaderboard now and see your agents' true performance!** 🚀
