#!/bin/bash
################################################################################
# EMPIRICA STATUS DASHBOARD
# Single command to check everything: git, SQLite, sessions, goals, artifacts
# Usage: ./status.sh [--summary] [--verbose] [--ai-id <id>]
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Options
VERBOSE=false
SUMMARY=false
AI_ID=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --verbose) VERBOSE=true; shift ;;
    --summary) SUMMARY=true; shift ;;
    --ai-id) AI_ID="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Paths
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$REPO_ROOT/.empirica/sessions/sessions.db"
DB_PATH_FALLBACK="$HOME/.empirica/sessions/sessions.db"

# Verify database exists
if [ ! -f "$DB_PATH" ]; then
  DB_PATH="$DB_PATH_FALLBACK"
  if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}ERROR: SQLite database not found at:${NC}"
    echo "  $REPO_ROOT/.empirica/sessions/sessions.db"
    echo "  $HOME/.empirica/sessions/sessions.db"
    exit 1
  fi
fi

################################################################################
# SECTION 1: GIT STATUS
################################################################################
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}GIT STATUS${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"

CURRENT_BRANCH=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)
LATEST_COMMIT=$(git -C "$REPO_ROOT" rev-parse --short HEAD)
COMMIT_MESSAGE=$(git -C "$REPO_ROOT" log -1 --pretty=format:"%s")
GIT_NOTES_COUNT=$(git -C "$REPO_ROOT" notes --ref=refs/notes/empirica/checkpoints list 2>/dev/null | wc -l)
UNCOMMITTED=$(git -C "$REPO_ROOT" status --short | wc -l)

echo "Branch: $CURRENT_BRANCH"
echo "Latest: $LATEST_COMMIT - $COMMIT_MESSAGE"
echo "Git Notes (Empirica): $GIT_NOTES_COUNT checkpoints"
echo "Uncommitted Changes: $UNCOMMITTED files"

if [ "$VERBOSE" = true ]; then
  echo -e "\n${YELLOW}Recent Commits:${NC}"
  git -C "$REPO_ROOT" log --oneline -n 5
fi

################################################################################
# SECTION 2: SESSIONS OVERVIEW
################################################################################
echo -e "\n${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}SESSIONS OVERVIEW${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"

# Count sessions by AI
SESSIONS_TOTAL=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions;" 2>/dev/null || echo "0")
SESSIONS_WITH_CASCADES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions WHERE total_cascades > 0;" 2>/dev/null || echo "0")
SESSIONS_WITH_ENDTIME=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions WHERE end_time IS NOT NULL;" 2>/dev/null || echo "0")

echo "Total Sessions: $SESSIONS_TOTAL"
echo "  ✅ With CASCADE Runs: $SESSIONS_WITH_CASCADES"
echo "  ✅ Completed (with end_time): $SESSIONS_WITH_ENDTIME"

# AI breakdown
echo -e "\n${YELLOW}By AI Agent:${NC}"
sqlite3 "$DB_PATH" \
  "SELECT ai_id, COUNT(*) as count, SUM(CASE WHEN end_time IS NOT NULL THEN 1 ELSE 0 END) as complete
   FROM sessions GROUP BY ai_id ORDER BY ai_id;" 2>/dev/null | \
  while IFS='|' read ai_id count complete; do
    if [ -n "$ai_id" ]; then
      printf "  ${BLUE}%-20s${NC} %d sessions (✅ %d completed)\n" "$ai_id" "$count" "$complete"
    fi
  done

################################################################################
# SECTION 3: CURRENT SESSION DETAILS
################################################################################
echo -e "\n${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}ACTIVE/RECENT SESSIONS${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"

# Get most recent session(s)
if [ -n "$AI_ID" ]; then
  SESSIONS=$(sqlite3 "$DB_PATH" \
    "SELECT session_id, ai_id, total_cascades, created_at FROM sessions
     WHERE ai_id='$AI_ID' ORDER BY created_at DESC LIMIT 3;" 2>/dev/null)
else
  SESSIONS=$(sqlite3 "$DB_PATH" \
    "SELECT session_id, ai_id, total_cascades, created_at FROM sessions
     ORDER BY created_at DESC LIMIT 5;" 2>/dev/null)
fi

if [ -z "$SESSIONS" ]; then
  echo "No sessions found"
else
  while IFS='|' read session_id ai_id total_cascades created_at; do
    if [ -n "$session_id" ]; then
      # Get latest reflex for this session
      LATEST_VECTOR=$(sqlite3 "$DB_PATH" \
        "SELECT know, do, uncertainty, phase, round_num
         FROM reflexes WHERE session_id='$session_id'
         ORDER BY created_at DESC LIMIT 1;" 2>/dev/null)

      STATUS="in_progress"
      if [ -n "$total_cascades" ] && [ "$total_cascades" -gt 0 ]; then
        STATUS="has_cascades"
      fi

      echo -e "${GREEN}${session_id:0:8}...${NC} | $ai_id | $STATUS"
      echo "  Created: $created_at"
      echo "  Cascades: $total_cascades"

      if [ -n "$LATEST_VECTOR" ]; then
        IFS='|' read know do uncertainty phase round_num <<< "$LATEST_VECTOR"
        echo "  Latest: Phase=$phase Round=$round_num | Know=$know | Do=$do | Uncertainty=$uncertainty"
      fi

      # Count goals for this session
      GOAL_COUNT=$(sqlite3 "$DB_PATH" \
        "SELECT COUNT(*) FROM goals WHERE session_id='$session_id';" 2>/dev/null || echo "0")
      echo "  Goals: $GOAL_COUNT"
      echo ""
    fi
  done <<< "$SESSIONS"
fi

################################################################################
# SECTION 4: GOALS & SUBTASKS
################################################################################
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}GOALS SUMMARY${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"

GOALS_TOTAL=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM goals;" 2>/dev/null || echo "0")
GOALS_COMPLETE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM goals WHERE is_completed=1;" 2>/dev/null || echo "0")
GOALS_INPROGRESS=$((GOALS_TOTAL - GOALS_COMPLETE))

echo "Total Goals: $GOALS_TOTAL"
echo "  ✅ Complete: $GOALS_COMPLETE"
echo "  ⏳ In Progress: $GOALS_INPROGRESS"

SUBTASKS_TOTAL=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM subtasks;" 2>/dev/null || echo "0")
SUBTASKS_COMPLETE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM subtasks WHERE status='completed';" 2>/dev/null || echo "0")

echo "Total Subtasks: $SUBTASKS_TOTAL"
echo "  ✅ Complete: $SUBTASKS_COMPLETE"

if [ "$VERBOSE" = true ]; then
  echo -e "\n${YELLOW}Active Goals:${NC}"
  sqlite3 "$DB_PATH" \
    "SELECT id, objective, is_completed
     FROM goals WHERE is_completed=0
     LIMIT 5;" 2>/dev/null | \
    while IFS='|' read goal_id objective is_completed; do
      if [ -n "$goal_id" ]; then
        printf "  ${BLUE}%s${NC} - $objective\n" "${goal_id:0:8}..."
      fi
    done
fi

################################################################################
# SECTION 5: ARTIFACTS
################################################################################
echo -e "\n${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}ARTIFACTS & CHANGES${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"

# Count recent file changes
FILES_MODIFIED=$(find "$REPO_ROOT" -type f -newer "$DB_PATH" 2>/dev/null | grep -v ".git" | grep -v ".pytest" | wc -l)
echo "Files Modified (Recent): $FILES_MODIFIED"

# Lines of code stats
TOTAL_LINES=$(find "$REPO_ROOT" -type f \( -name "*.py" -o -name "*.sh" -o -name "*.md" \) \
  -not -path "*/.git/*" -not -path "*/.venv*/*" \
  -not -path "*/__pycache__/*" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')

echo "Total Lines (Python/Shell/Markdown): $TOTAL_LINES"

################################################################################
# SECTION 6: EPISTEMIC STATE
################################################################################
echo -e "\n${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}EPISTEMIC STATE (Latest Assessment)${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"

if [ -n "$AI_ID" ]; then
  LATEST_EPISTEMIC=$(sqlite3 "$DB_PATH" \
    "SELECT
       ROUND(engagement, 2) as engagement,
       ROUND(know, 2) as know,
       ROUND(do, 2) as do,
       ROUND(context, 2) as context,
       ROUND(uncertainty, 2) as uncertainty,
       phase, round_num
     FROM reflexes
     WHERE session_id IN (SELECT session_id FROM sessions WHERE ai_id='$AI_ID')
     ORDER BY created_at DESC LIMIT 1;" 2>/dev/null)

  if [ -n "$LATEST_EPISTEMIC" ]; then
    IFS='|' read eng know do ctx unc phase round <<< "$LATEST_EPISTEMIC"
    echo -e "${YELLOW}AI: $AI_ID (Latest)${NC}"
    echo "  Engagement: $eng | Know: $know | Do: $do | Context: $ctx"
    echo "  Uncertainty: $unc | Phase: $phase | Round: $round"
  fi
else
  # Show aggregate state
  echo -e "${YELLOW}Team Aggregate (All Sessions):${NC}"
  AGG_STATE=$(sqlite3 "$DB_PATH" \
    "SELECT
       ROUND(AVG(engagement), 2) as engagement,
       ROUND(AVG(know), 2) as know,
       ROUND(AVG(do), 2) as do,
       ROUND(AVG(uncertainty), 2) as uncertainty
     FROM reflexes WHERE engagement IS NOT NULL;" 2>/dev/null)

  if [ -n "$AGG_STATE" ]; then
    IFS='|' read eng know do unc <<< "$AGG_STATE"
    echo "  Engagement: $eng | Know: $know | Do: $do | Uncertainty: $unc"
  fi
fi

################################################################################
# SECTION 7: SUMMARY MODE
################################################################################
if [ "$SUMMARY" = true ]; then
  echo -e "\n${CYAN}════════════════════════════════════════════════════════════════${NC}"
  echo -e "${CYAN}EXECUTIVE SUMMARY${NC}"
  echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"

  if [ "$SESSIONS_TOTAL" -gt 0 ]; then
    COMPLETION_PCT=$((SESSIONS_WITH_ENDTIME * 100 / SESSIONS_TOTAL))
  else
    COMPLETION_PCT=0
  fi

  if [ "$GOALS_TOTAL" -gt 0 ]; then
    GOAL_COMPLETION_PCT=$((GOALS_COMPLETE * 100 / GOALS_TOTAL))
  else
    GOAL_COMPLETION_PCT=0
  fi

  echo "Project Status: $COMPLETION_PCT% of sessions completed"
  echo "Goals Status: $GOAL_COMPLETION_PCT% of goals completed"
  echo "Latest Commit: $LATEST_COMMIT - $COMMIT_MESSAGE"
  echo "Git Notes: $GIT_NOTES_COUNT checkpoints stored"
fi

################################################################################
# FOOTER
################################################################################
echo -e "\n${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo "Database: $DB_PATH"
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}\n"

# Help text
if [ "$VERBOSE" = false ] && [ "$SUMMARY" = false ]; then
  echo -e "${YELLOW}Usage:${NC}"
  echo "  ./status.sh              # Quick overview"
  echo "  ./status.sh --verbose    # Detailed view with recent commits"
  echo "  ./status.sh --summary    # Executive summary"
  echo "  ./status.sh --ai-id <id> # Filter by AI agent (e.g., claude-code)"
  echo ""
fi
