#!/bin/bash
################################################################################
# EMPIRICA TRACKING DASHBOARD
# Complete tracking: AI → Session → CASCADE → Goals → Subtasks → Findings
# Shows: PREFLIGHT/POSTFLIGHT, goals, subtasks, findings, unknowns, deadends
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
BLUE='\033[0;34m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DB_PATH="$REPO_ROOT/.empirica/sessions/sessions.db"

if [ ! -f "$DB_PATH" ]; then
  DB_PATH="$HOME/.empirica/sessions/sessions.db"
fi

# Header
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}EMPIRICA TRACKING DASHBOARD${NC}"
echo -e "${CYAN}AI → Session → CASCADE → Goals → Subtasks → Findings${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Get AI filter from argument
AI_FILTER="${1:-}"

if [ -n "$AI_FILTER" ]; then
  echo -e "${YELLOW}Filtering by AI: $AI_FILTER${NC}"
  echo ""
fi

# Query for tracking data
sqlite3 "$DB_PATH" << EOF
.mode box
.headers on

-- Overview: Active AIs with sessions
SELECT 
  '📊 ACTIVE AIs' as section;
  
SELECT 
  s.ai_id as AI_ID,
  COUNT(DISTINCT s.session_id) as Sessions,
  COUNT(DISTINCT g.id) as Goals,
  COUNT(DISTINCT st.id) as Subtasks,
  COUNT(DISTINCT CASE WHEN r.phase='PREFLIGHT' THEN r.id END) as Preflights,
  COUNT(DISTINCT CASE WHEN r.phase='POSTFLIGHT' THEN r.id END) as Postflights
FROM sessions s
LEFT JOIN goals g ON s.session_id = g.session_id
LEFT JOIN subtasks st ON g.id = st.goal_id
LEFT JOIN reflexes r ON s.session_id = r.session_id
WHERE s.end_time IS NULL
  AND (s.ai_id LIKE '%${AI_FILTER}%' OR '${AI_FILTER}' = '')
GROUP BY s.ai_id
ORDER BY Sessions DESC, Goals DESC
LIMIT 10;

EOF

echo ""
echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Recent sessions with CASCADE data
sqlite3 "$DB_PATH" << EOF
.mode box
.headers on

SELECT 
  '🔄 RECENT SESSIONS (Last 10)' as section;

SELECT 
  substr(s.ai_id, 1, 25) as AI_ID,
  substr(s.session_id, 1, 8) as Session,
  datetime(s.created_at, 'unixepoch') as Created,
  CASE WHEN s.end_time IS NULL THEN '🟢 Active' ELSE '⚪ Ended' END as Status,
  COUNT(DISTINCT g.id) as Goals,
  COALESCE(MAX(CASE WHEN r.phase='PREFLIGHT' THEN printf('%.2f', r.know) END), '-') as Pre_Know,
  COALESCE(MAX(CASE WHEN r.phase='POSTFLIGHT' THEN printf('%.2f', r.know) END), '-') as Post_Know,
  COALESCE(MAX(CASE WHEN r.phase='PREFLIGHT' THEN printf('%.2f', r.uncertainty) END), '-') as Pre_Unc,
  COALESCE(MAX(CASE WHEN r.phase='POSTFLIGHT' THEN printf('%.2f', r.uncertainty) END), '-') as Post_Unc
FROM sessions s
LEFT JOIN goals g ON s.session_id = g.session_id
LEFT JOIN reflexes r ON s.session_id = r.session_id
WHERE s.ai_id LIKE '%${AI_FILTER}%' OR '${AI_FILTER}' = ''
GROUP BY s.session_id
ORDER BY s.created_at DESC
LIMIT 10;

EOF

echo ""
echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Goals with subtasks
sqlite3 "$DB_PATH" << EOF
.mode box
.headers on

SELECT 
  '🎯 ACTIVE GOALS WITH SUBTASKS' as section;

SELECT 
  substr(s.ai_id, 1, 20) as AI_ID,
  substr(g.objective, 1, 40) as Goal_Objective,
  g.status as Status,
  COUNT(st.id) as Total_Subtasks,
  COUNT(CASE WHEN st.status='completed' THEN 1 END) as Completed,
  COUNT(CASE WHEN st.status='pending' THEN 1 END) as Pending,
  printf('%.0f%%', 
    CAST(COUNT(CASE WHEN st.status='completed' THEN 1 END) AS FLOAT) / 
    NULLIF(COUNT(st.id), 0) * 100
  ) as Progress
FROM goals g
JOIN sessions s ON g.session_id = s.session_id
LEFT JOIN subtasks st ON g.id = st.goal_id
WHERE g.status IN ('in_progress', 'pending')
  AND (s.ai_id LIKE '%${AI_FILTER}%' OR '${AI_FILTER}' = '')
GROUP BY g.id
HAVING COUNT(st.id) > 0
ORDER BY s.created_at DESC
LIMIT 10;

EOF

echo ""
echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# CHECK phases with findings/unknowns
echo -e "${WHITE}🔍 CHECK PHASES (Findings & Unknowns)${NC}"
echo ""

python3 << PYEOF
import sqlite3
import json
import sys
import os

db_path = "${DB_PATH}"
ai_filter = "${AI_FILTER}"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.ai_id,
            substr(s.session_id, 1, 8) as session,
            r.phase,
            r.round,
            r.reflex_data,
            datetime(r.timestamp, 'unixepoch') as check_time
        FROM reflexes r
        JOIN sessions s ON r.session_id = s.session_id
        WHERE r.phase = 'CHECK'
          AND (s.ai_id LIKE ? OR ? = '')
        ORDER BY r.timestamp DESC
        LIMIT 10;
    """, (f'%{ai_filter}%', ai_filter))
    
    results = cursor.fetchall()
    
    if not results:
        print("  No CHECK phases found with findings/unknowns data")
    else:
        for row in results:
            ai_id, session, phase, round_num, reflex_data_str, check_time = row
            
            print(f"\n  AI: {ai_id[:30]}")
            print(f"  Session: {session}... | {phase} Round {round_num} | {check_time}")
            
            # Try to parse findings/unknowns from reflex_data JSON
            if reflex_data_str:
                try:
                    reflex_data = json.loads(reflex_data_str)
                    
                    findings = reflex_data.get('findings', [])
                    unknowns = reflex_data.get('unknowns', [])
                    deadends = reflex_data.get('deadends', [])
                    
                    if findings:
                        print(f"  ✅ Findings ({len(findings)}):")
                        for f in findings[:3]:  # Show first 3
                            print(f"     • {f[:60]}")
                    else:
                        print(f"  ✅ Findings: (none recorded)")
                    
                    if unknowns:
                        print(f"  ❓ Unknowns ({len(unknowns)}):")
                        for u in unknowns[:3]:
                            print(f"     • {u[:60]}")
                    else:
                        print(f"  ❓ Unknowns: (none)")
                    
                    if deadends:
                        print(f"  🚫 Dead Ends ({len(deadends)}):")
                        for d in deadends[:3]:
                            print(f"     • {d[:60]}")
                    
                except json.JSONDecodeError:
                    print(f"  ⚠️  Could not parse reflex_data JSON")
            else:
                print(f"  ⚠️  No reflex_data recorded")
            
            print(f"  {'-' * 60}")
    
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
PYEOF

echo ""
echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Learning deltas
sqlite3 "$DB_PATH" << EOF
.mode box
.headers on

SELECT 
  '📈 LEARNING DELTAS (Recent)' as section;

SELECT 
  substr(s.ai_id, 1, 25) as AI_ID,
  substr(s.session_id, 1, 8) as Session,
  printf('%.3f', 
    MAX(CASE WHEN r.phase='POSTFLIGHT' THEN r.know END) - 
    MAX(CASE WHEN r.phase='PREFLIGHT' THEN r.know END)
  ) as Know_Delta,
  printf('%.3f',
    MAX(CASE WHEN r.phase='PREFLIGHT' THEN r.uncertainty END) - 
    MAX(CASE WHEN r.phase='POSTFLIGHT' THEN r.uncertainty END)
  ) as Unc_Reduction,
  printf('%.3f',
    MAX(CASE WHEN r.phase='POSTFLIGHT' THEN r.completion END)
  ) as Final_Completion
FROM sessions s
JOIN reflexes r ON s.session_id = r.session_id
WHERE r.phase IN ('PREFLIGHT', 'POSTFLIGHT')
  AND (s.ai_id LIKE '%${AI_FILTER}%' OR '${AI_FILTER}' = '')
GROUP BY s.session_id
HAVING COUNT(DISTINCT r.phase) = 2
ORDER BY s.created_at DESC
LIMIT 10;

EOF

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo "Last Updated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo -e "Usage: ${CYAN}./empirica-tracking.sh [ai-filter]${NC}"
echo "Example: ./empirica-tracking.sh claude"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
