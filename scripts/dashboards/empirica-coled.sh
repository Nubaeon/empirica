#!/bin/bash
################################################################################
# EMPIRICA CO-LEAD DASHBOARD
# Quick overview for co-lead decision-making
# What: Active AIs, critical work, blockers, learning status
# When: Coming into session with no memory, making decisions
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

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DB_PATH="$REPO_ROOT/.empirica/sessions/sessions.db"

if [ ! -f "$DB_PATH" ]; then
  DB_PATH="$HOME/.empirica/sessions/sessions.db"
fi

# HEADER
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}EMPIRICA CO-LEAD DASHBOARD${NC}"
echo -e "${CYAN}What's happening right now? What needs your attention?${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Quick system snapshot
TOTAL=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions;" 2>/dev/null || echo "0")
ACTIVE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions WHERE end_time IS NULL;" 2>/dev/null || echo "0")
CRITICAL=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM subtasks WHERE importance='critical' AND status='pending';" 2>/dev/null || echo "0")
HIGH=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM subtasks WHERE importance='high' AND status='pending';" 2>/dev/null || echo "0")

echo -e "${WHITE}SYSTEM SNAPSHOT${NC}"
echo -e "Sessions: ${YELLOW}$TOTAL${NC} total | ${MAGENTA}$ACTIVE${NC} active"
echo -e "Priority work: ${RED}$CRITICAL${NC} critical | ${YELLOW}$HIGH${NC} high pending"
echo ""

# WHAT EACH AI IS DOING RIGHT NOW
echo -e "${WHITE}🤖 WHAT'S IN PROGRESS${NC}"
echo ""

sqlite3 "$DB_PATH" << 'EOF' 2>/dev/null || true
SELECT
  '  ' ||
  CASE
    WHEN (SELECT COUNT(*) FROM goals WHERE session_id=s.session_id AND status='in_progress') > 0
    THEN '🚀 '
    ELSE '⏸️  '
  END ||
  substr(s.ai_id, 1, 25) ||
  ' | ' ||
  CASE
    WHEN g.objective IS NOT NULL THEN substr(g.objective, 1, 45)
    ELSE 'No active goal'
  END
FROM sessions s
LEFT JOIN goals g ON g.session_id = s.session_id AND g.status='in_progress'
WHERE s.end_time IS NULL
ORDER BY s.created_at DESC
LIMIT 10;
EOF

echo ""

# CRITICAL/HIGH PRIORITY WORK SUMMARY
echo -e "${WHITE}🎯 CRITICAL WORK (Next 5)${NC}"
echo ""

sqlite3 "$DB_PATH" << 'EOF' 2>/dev/null || true
SELECT
  '  ' ||
  CASE importance WHEN 'critical' THEN '🔴' WHEN 'high' THEN '🟠' ELSE '🟡' END ||
  ' ' ||
  substr(g.objective, 1, 35) ||
  ' → ' ||
  substr(st.description, 1, 30)
FROM subtasks st
LEFT JOIN goals g ON st.goal_id = g.id
WHERE st.status='pending' AND (st.importance='critical' OR st.importance='high')
ORDER BY
  CASE st.importance WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END
LIMIT 5;
EOF

echo ""

# LEARNING STATUS (Simple)
echo -e "${WHITE}📈 LEARNING STATUS${NC}"
echo ""

sqlite3 "$DB_PATH" << 'EOF' 2>/dev/null || true
SELECT
  '  ' ||
  CASE
    WHEN (MAX(CASE WHEN phase='POSTFLIGHT' THEN know ELSE 0 END) -
          MAX(CASE WHEN phase='PREFLIGHT' THEN know ELSE 0 END)) > 0.15 THEN '🚀 '
    WHEN (MAX(CASE WHEN phase='POSTFLIGHT' THEN know ELSE 0 END) -
          MAX(CASE WHEN phase='PREFLIGHT' THEN know ELSE 0 END)) > 0.05 THEN '⚡ '
    ELSE '⏸️  '
  END ||
  substr(ai_id, 1, 20) ||
  ' | Learning: ' ||
  printf('%.2f', MAX(CASE WHEN phase='POSTFLIGHT' THEN know ELSE 0 END) -
                  MAX(CASE WHEN phase='PREFLIGHT' THEN know ELSE 0 END))
FROM reflexes
WHERE ai_id IS NOT NULL
GROUP BY ai_id
ORDER BY (MAX(CASE WHEN phase='POSTFLIGHT' THEN know ELSE 0 END) -
          MAX(CASE WHEN phase='PREFLIGHT' THEN know ELSE 0 END)) DESC
LIMIT 5;
EOF

echo ""

# GIT MAPPING REMINDER
echo -e "${WHITE}🔗 GIT MAPPING${NC}"
echo "All work is traceable:"
echo "  • Each goal → session_id → git commits"
echo "  • Each subtask → goal → git branch/tag"
echo "  • Epistemic data → commit trailers (git log --format=%(trailers))"
echo ""

# FOOTER
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo "Last Updated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "For more details:"
echo -e "  • Run: ${CYAN}./empirica-goals-dashboard.sh${NC} for full goal breakdown"
echo -e "  • Run: ${CYAN}./leaderboard.sh${NC} for detailed performance metrics"
echo -e "  • Run: ${CYAN}git log --format=%(trailers) -5${NC} to see epistemic data"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
