#!/bin/bash
################################################################################
# EMPIRICA UNIFIED DASHBOARD
# Single command: ./empirica.sh
# Shows: Everything happening in Empirica right now
# Purpose: Single source of truth for decision making and tracking
################################################################################

set -e
export LC_ALL=C

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
MAGENTA='\033[0;35m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$REPO_ROOT/.empirica/sessions/sessions.db"

if [ ! -f "$DB_PATH" ]; then
  DB_PATH="$HOME/.empirica/sessions/sessions.db"
fi

# SECTION 1: HEADER
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}EMPIRICA UNIFIED DASHBOARD - YOUR SINGLE SOURCE OF TRUTH${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

# System metrics
TOTAL=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions;" 2>/dev/null || echo "0")
COMPLETED=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions WHERE end_time IS NOT NULL;" 2>/dev/null || echo "0")
ACTIVE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sessions WHERE end_time IS NULL;" 2>/dev/null || echo "0")
GOALS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM goals;" 2>/dev/null || echo "0")
METRICS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM reflexes;" 2>/dev/null || echo "0")

COMPLETION_PCT=$((COMPLETED * 100 / TOTAL))

echo -e "${WHITE}System Status: ${GREEN}✅ OPERATIONAL${NC}"
echo ""
echo "📊 Sessions:      ${YELLOW}$TOTAL${NC} total | ${GREEN}$COMPLETED${NC} completed ($COMPLETION_PCT%) | ${MAGENTA}$ACTIVE${NC} active"
echo "🎯 Goals:         ${YELLOW}$GOALS${NC} tracked"
echo "📈 Learning Data: ${CYAN}$METRICS${NC} epistemic vectors"
echo ""

# SECTION 2: TOP PERFORMERS
echo -e "${WHITE}🏆 TOP LEARNING PERFORMERS${NC}"
echo -e "${CYAN}(Use this to guide decisions - who's learning, who's stuck?)${NC}"
echo ""

sqlite3 "$DB_PATH" << 'EOSQL' 2>/dev/null | head -10 | nl
SELECT
  substr(ai_id, 1, 30) ||
  ' | Learning: ' ||
  substr(CAST(ROUND(know_end - know_start, 2) AS TEXT), 1, 5) ||
  ' | Sessions: ' ||
  CAST(sessions AS TEXT) ||
  ' | Mastery: ' ||
  CAST(ROUND(1.0 - avg_unc, 2), 1, 5) AS text
FROM (
  SELECT
    ai_id,
    MAX(CASE WHEN phase='POSTFLIGHT' THEN know ELSE 0 END) as know_end,
    MAX(CASE WHEN phase='PREFLIGHT' THEN know ELSE 0 END) as know_start,
    COUNT(DISTINCT session_id) as sessions,
    AVG(CASE WHEN phase='POSTFLIGHT' THEN uncertainty ELSE 0 END) as avg_unc
  FROM reflexes
  WHERE ai_id IS NOT NULL
  GROUP BY ai_id
  ORDER BY (know_end - know_start) DESC
)
LIMIT 10;
EOSQL

echo ""

# SECTION 3: OTHER AIs STATUS
echo -e "${WHITE}🤖 OTHER AIs IN THE SYSTEM${NC}"
echo -e "${CYAN}(Track what parallel work is happening)${NC}"
echo ""

sqlite3 "$DB_PATH" << 'EOSQL' 2>/dev/null | head -20
SELECT
  CASE
    WHEN (MAX(CASE WHEN phase='POSTFLIGHT' THEN know ELSE 0 END) -
          MAX(CASE WHEN phase='PREFLIGHT' THEN know ELSE 0 END)) > 0.1
    THEN '  🚀 Fast: '
    WHEN (MAX(CASE WHEN phase='POSTFLIGHT' THEN know ELSE 0 END) -
          MAX(CASE WHEN phase='PREFLIGHT' THEN know ELSE 0 END)) > 0.01
    THEN '  ⚡ Learning: '
    ELSE '  ⏸️  Slow: '
  END ||
  substr(ai_id, 1, 30) ||
  ' | Sessions: ' ||
  CAST(COUNT(DISTINCT session_id) AS TEXT)
FROM reflexes
GROUP BY ai_id
ORDER BY ai_id;
EOSQL

echo ""

# SECTION 4: ACTIVE SESSIONS
echo -e "${WHITE}🔴 SESSIONS IN PROGRESS ($ACTIVE active)${NC}"
echo -e "${CYAN}(These are the decisions being made RIGHT NOW)${NC}"
echo ""

if [ "$ACTIVE" -gt 0 ]; then
  sqlite3 "$DB_PATH" "SELECT '  • ' || substr(ai_id, 1, 30) || ' | Started: ' || substr(created_at, 1, 10) FROM sessions WHERE end_time IS NULL ORDER BY created_at DESC LIMIT 10;" 2>/dev/null
else
  echo "  No active sessions"
fi

echo ""

# SECTION 5: DECISION GUIDANCE
echo -e "${WHITE}💡 DECISION GUIDANCE${NC}"
echo -e "${CYAN}(Based on current system state)${NC}"
echo ""

LEARNING=$(sqlite3 "$DB_PATH" "SELECT COUNT(DISTINCT ai_id) FROM reflexes WHERE (SELECT MAX(CASE WHEN phase='POSTFLIGHT' THEN know ELSE 0 END) - MAX(CASE WHEN phase='PREFLIGHT' THEN know ELSE 0 END)) > 0.05;" 2>/dev/null || echo "0")
STUCK=$(sqlite3 "$DB_PATH" "SELECT COUNT(DISTINCT ai_id) FROM sessions;" 2>/dev/null || echo "0")

echo "System Health:"
echo "  ${GREEN}✓${NC} $LEARNING AIs showing measurable learning"
echo "  ${YELLOW}⚠${NC} Monitor $STUCK active AIs"
echo ""

echo "Next Steps:"
echo "  • Run: ${CYAN}./status.sh${NC} for detailed system view"
echo "  • Run: ${CYAN}./leaderboard.sh${NC} for performance metrics"
echo ""

# FOOTER
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo "Last Updated: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Database: $DB_PATH"
echo ""
echo "This dashboard is your single source of truth for:"
echo "  ✓ System state at a glance"
echo "  ✓ Decision guidance (who's learning, who's stuck)"
echo "  ✓ Tracking other AIs working in parallel"
echo "  ✓ Quick health check"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
