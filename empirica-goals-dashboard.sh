#!/bin/bash
################################################################################
# EMPIRICA GOALS & WORK DASHBOARD
# Shows each AI's actual work: goals, subtasks, unknowns, findings, deadends
# Maps to git commits and investigation history
################################################################################

set -e
export LC_ALL=C

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
MAGENTA='\033[0;35m'
RED='\033[0;31m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$REPO_ROOT/.empirica/sessions/sessions.db"

if [ ! -f "$DB_PATH" ]; then
  DB_PATH="$HOME/.empirica/sessions/sessions.db"
fi

# HEADER
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}EMPIRICA GOALS & WORK DASHBOARD${NC}"
echo -e "${CYAN}Each AI's actual goals, subtasks, unknowns, findings${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Get session/AI filter if provided
AI_FILTER="${1:-%}"

# SECTION 1: Goals Overview
echo -e "${WHITE}📋 GOALS OVERVIEW${NC}"
echo ""

TOTAL_GOALS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM goals;" 2>/dev/null || echo "0")
COMPLETED_GOALS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM goals WHERE is_completed=1;" 2>/dev/null || echo "0")
IN_PROGRESS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM goals WHERE status='in_progress';" 2>/dev/null || echo "0")

echo "Total Goals: ${YELLOW}$TOTAL_GOALS${NC} | Completed: ${GREEN}$COMPLETED_GOALS${NC} | In Progress: ${MAGENTA}$IN_PROGRESS${NC}"
echo ""

# SECTION 2: Goals by Session/AI
echo -e "${WHITE}🎯 GOALS BY SESSION/AI${NC}"
echo ""

sqlite3 "$DB_PATH" << 'EOF' 2>/dev/null | head -20
SELECT
  CASE
    WHEN s.session_id IS NOT NULL THEN s.ai_id
    ELSE 'Unknown'
  END as ai_id,
  COUNT(DISTINCT g.id) as goal_count,
  SUM(CASE WHEN g.is_completed=1 THEN 1 ELSE 0 END) as completed,
  GROUP_CONCAT(CASE WHEN g.status='in_progress' THEN substr(g.objective, 1, 40) ELSE NULL END, ' | ')
FROM goals g
LEFT JOIN sessions s ON g.session_id = s.session_id
GROUP BY COALESCE(s.session_id, 'unknown')
ORDER BY goal_count DESC;
EOF

echo ""

# SECTION 3: Active Goals (In Progress)
echo -e "${WHITE}🔴 ACTIVE GOALS (In Progress)${NC}"
echo ""

sqlite3 "$DB_PATH" << 'EOF' 2>/dev/null | head -15
SELECT
  printf("%-8s", substr(g.id, 1, 8)) || ' | ' ||
  printf("%-50s", substr(g.objective, 1, 50)) || ' | ' ||
  COALESCE(s.ai_id, 'no-session')
FROM goals g
LEFT JOIN sessions s ON g.session_id = s.session_id
WHERE g.status = 'in_progress'
ORDER BY g.created_timestamp DESC;
EOF

echo ""

# SECTION 4: Subtasks Status
echo -e "${WHITE}📝 SUBTASKS BREAKDOWN${NC}"
echo ""

TOTAL_SUBTASKS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM subtasks;" 2>/dev/null || echo "0")
COMPLETED_SUBTASKS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM subtasks WHERE status='completed';" 2>/dev/null || echo "0")
IN_PROGRESS_SUBTASKS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM subtasks WHERE status='in_progress';" 2>/dev/null || echo "0")

echo "Total Subtasks: ${YELLOW}$TOTAL_SUBTASKS${NC} | Completed: ${GREEN}$COMPLETED_SUBTASKS${NC} | In Progress: ${MAGENTA}$IN_PROGRESS_SUBTASKS${NC}"
echo ""

# SECTION 5: Subtasks by Importance
echo -e "${WHITE}⭐ SUBTASKS BY IMPORTANCE${NC}"
echo ""

sqlite3 "$DB_PATH" << 'EOF' 2>/dev/null
SELECT
  printf("%-10s", epistemic_importance) || ' | ' ||
  printf("%-10s", status) || ' | ' ||
  printf("%-3s", COUNT(*)) || ' tasks'
FROM subtasks
GROUP BY epistemic_importance, status
ORDER BY
  CASE epistemic_importance
    WHEN 'critical' THEN 1
    WHEN 'high' THEN 2
    WHEN 'medium' THEN 3
    ELSE 4
  END,
  status;
EOF

echo ""

# SECTION 6: Investigation & Findings
echo -e "${WHITE}🔍 INVESTIGATION LOGS${NC}"
echo ""

TOTAL_INVESTIGATIONS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM investigation_logs;" 2>/dev/null || echo "0")

if [ "$TOTAL_INVESTIGATIONS" -gt 0 ]; then
  echo "Total investigations: $TOTAL_INVESTIGATIONS"
  echo ""

  sqlite3 "$DB_PATH" << 'EOF' 2>/dev/null | head -10
SELECT
  substr(log_id, 1, 8) || ' | Round ' ||
  round_number || ' | ' ||
  substr(COALESCE(summary, 'No summary'), 1, 50)
FROM investigation_logs
ORDER BY assessed_at DESC;
EOF
else
  echo "No investigation logs yet"
fi

echo ""

# SECTION 7: Detailed Goal View
echo -e "${WHITE}📌 SAMPLE ACTIVE GOALS${NC}"
echo ""

sqlite3 "$DB_PATH" "SELECT substr(g.id, 1, 8) || ' | ' || substr(g.objective, 1, 50) || ' | ' || COUNT(DISTINCT st.id) || ' subtasks' FROM goals g LEFT JOIN subtasks st ON st.goal_id = g.id WHERE g.status='in_progress' GROUP BY g.id LIMIT 5;" 2>/dev/null | while read -r line; do
  echo "  • $line"
done

echo ""

# SECTION 8: Git Mapping
echo -e "${WHITE}🔗 GIT MAPPING${NC}"
echo "Goals can be traced to git commits via session_id in database"
echo ""

RECENT_COMMITS=$(cd "$REPO_ROOT" && git log --oneline -5 2>/dev/null | head -3)

echo "Recent commits:"
echo "$RECENT_COMMITS" | while read -r line; do
  echo "  • $line"
done

echo ""

# FOOTER
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo "Last Updated: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Database: $DB_PATH"
echo ""
echo "This dashboard shows:"
echo "  ✓ All goals (what each AI/session is working on)"
echo "  ✓ Subtasks breakdown (concrete work items)"
echo "  ✓ Investigation logs (unknowns, findings)"
echo "  ✓ Status tracking (completed, in progress)"
echo "  ✓ Git mapping (links to commits)"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
