#!/bin/bash
################################################################################
# EMPIRICA AI LEADERBOARD
# Real-time performance metrics for AI agents
# Usage: ./leaderboard.sh [--json] [--csv]
################################################################################

set -e

# Force C locale for consistent decimal separator
export LC_ALL=C

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Options
JSON_OUTPUT=false
CSV_OUTPUT=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --json) JSON_OUTPUT=true; shift ;;
    --csv) CSV_OUTPUT=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Paths
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DB_PATH="$REPO_ROOT/.empirica/sessions/sessions.db"
DB_PATH_FALLBACK="$HOME/.empirica/sessions/sessions.db"

if [ ! -f "$DB_PATH" ]; then
  DB_PATH="$DB_PATH_FALLBACK"
  if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}ERROR: SQLite database not found${NC}"
    exit 1
  fi
fi

################################################################################
# BADGE SYSTEM
################################################################################

# Badge definitions (emoji + name + criteria)
declare -A BADGES=(
  ["🚀"]="Launched"
  ["⚡"]="Speed Demon"
  ["🧠"]="Brain Boost"
  ["🏆"]="Champion"
  ["🎯"]="Goal Master"
  ["🔬"]="Scientist"
  ["⚙️"]="Engineer"
  ["🎓"]="Scholar"
  ["👑"]="Elite"
  ["🌟"]="Rising Star"
)

################################################################################
# Calculate AI Metrics
################################################################################

# Get all unique AIs
get_all_ais() {
  sqlite3 "$DB_PATH" \
    "SELECT DISTINCT ai_id FROM sessions ORDER BY ai_id;" 2>/dev/null
}

# Learning growth: PREFLIGHT know vs POSTFLIGHT know (simplified)
calculate_learning_growth() {
  local ai_id=$1

  sqlite3 "$DB_PATH" \
    "SELECT COALESCE(ROUND(AVG(
      CASE WHEN phase='POSTFLIGHT' THEN know ELSE 0 END -
      CASE WHEN phase='PREFLIGHT' THEN know ELSE 0 END
    ), 3), 0.0)
    FROM reflexes
    WHERE session_id IN (SELECT session_id FROM sessions WHERE ai_id='$ai_id' LIMIT 100);" 2>/dev/null
}

# Goal completion rate
calculate_goal_completion() {
  local ai_id=$1

  sqlite3 "$DB_PATH" \
    "SELECT COALESCE(ROUND(
      (SELECT COUNT(*) FROM goals WHERE session_id IN (SELECT session_id FROM sessions WHERE ai_id='$ai_id') AND is_completed=1) * 100.0 /
      (SELECT COUNT(*) FROM goals WHERE session_id IN (SELECT session_id FROM sessions WHERE ai_id='$ai_id')),
      1), 0) as completion_pct;" 2>/dev/null
}

# Total goals completed
calculate_total_goals() {
  local ai_id=$1

  sqlite3 "$DB_PATH" \
    "SELECT COUNT(*) FROM goals
     WHERE session_id IN (SELECT session_id FROM sessions WHERE ai_id='$ai_id')
     AND is_completed=1;" 2>/dev/null
}

# Sessions completed
calculate_sessions_completed() {
  local ai_id=$1

  sqlite3 "$DB_PATH" \
    "SELECT COUNT(*) FROM sessions WHERE ai_id='$ai_id' AND end_time IS NOT NULL;" 2>/dev/null
}

# Uncertainty reduction: Average uncertainty at POSTFLIGHT (simplified)
calculate_uncertainty_mastery() {
  local ai_id=$1

  sqlite3 "$DB_PATH" \
    "SELECT COALESCE(ROUND(1.0 - AVG(CASE WHEN phase='POSTFLIGHT' THEN uncertainty ELSE NULL END), 3), 0.0)
    FROM reflexes
    WHERE session_id IN (SELECT session_id FROM sessions WHERE ai_id='$ai_id' LIMIT 100)
    AND uncertainty IS NOT NULL;" 2>/dev/null
}

# Average confidence during CHECKs (simplified)
calculate_check_confidence() {
  local ai_id=$1

  sqlite3 "$DB_PATH" \
    "SELECT COALESCE(ROUND(AVG(know + do + context), 3), 0.0)
    FROM reflexes
    WHERE session_id IN (SELECT session_id FROM sessions WHERE ai_id='$ai_id' LIMIT 100)
    AND phase='CHECK';" 2>/dev/null
}

# Total work: lines of code or similar metric
calculate_total_cascades() {
  local ai_id=$1

  sqlite3 "$DB_PATH" \
    "SELECT SUM(total_cascades) FROM sessions WHERE ai_id='$ai_id';" 2>/dev/null
}

# Consistency: % of sessions with end_time
calculate_consistency() {
  local ai_id=$1

  sqlite3 "$DB_PATH" <<EOF 2>/dev/null
SELECT COALESCE(ROUND(
  SUM(CASE WHEN end_time IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
  1), 0) as consistency_pct
FROM sessions WHERE ai_id='$ai_id';
EOF
}

################################################################################
# Determine Badges
################################################################################

get_badges() {
  local ai_id=$1
  local growth=$2
  local goals=$3
  local sessions=$4
  local uncertainty=$5
  local cascades=$6
  local consistency=$7

  local badges=""

  # 🚀 Launched: First session completed
  if (( $(echo "$sessions > 0" | bc -l) )); then
    badges="$badges 🚀"
  fi

  # ⚡ Speed Demon: 5+ sessions completed
  if (( $(echo "$sessions >= 5" | bc -l) )); then
    badges="$badges ⚡"
  fi

  # 🧠 Brain Boost: Learning growth > 0.10
  if (( $(echo "$growth > 0.10" | bc -l) )); then
    badges="$badges 🧠"
  fi

  # 🏆 Champion: 10+ sessions completed
  if (( $(echo "$sessions >= 10" | bc -l) )); then
    badges="$badges 🏆"
  fi

  # 🎯 Goal Master: 10+ goals completed
  if (( $(echo "$goals >= 10" | bc -l) )); then
    badges="$badges 🎯"
  fi

  # 🔬 Scientist: High learning growth (> 0.15)
  if (( $(echo "$growth > 0.15" | bc -l) )); then
    badges="$badges 🔬"
  fi

  # ⚙️ Engineer: 10+ cascades
  if (( $(echo "$cascades >= 10" | bc -l) )); then
    badges="$badges ⚙️"
  fi

  # 🎓 Scholar: Uncertainty mastery > 0.70 (low uncertainty at end)
  if (( $(echo "$uncertainty > 0.70" | bc -l) )); then
    badges="$badges 🎓"
  fi

  # 👑 Elite: 20+ sessions + 20+ goals + learning growth > 0.15
  if (( $(echo "$sessions >= 20 && $goals >= 20 && $growth > 0.15" | bc -l) )); then
    badges="$badges 👑"
  fi

  # 🌟 Rising Star: High consistency + good learning (new agents doing well)
  if (( $(echo "$consistency >= 90 && $growth > 0.08 && $sessions < 10" | bc -l) )); then
    badges="$badges 🌟"
  fi

  echo "$badges"
}

################################################################################
# Main Leaderboard Calculation
################################################################################

if [ "$JSON_OUTPUT" = true ]; then
  echo "{"
  echo "  \"leaderboard\": ["

  first=true
  while IFS= read -r ai_id; do
    if [ -z "$ai_id" ]; then
      continue
    fi

    # Calculate all metrics
    growth=$(calculate_learning_growth "$ai_id")
    completion=$(calculate_goal_completion "$ai_id")
    goals=$(calculate_total_goals "$ai_id")
    sessions=$(calculate_sessions_completed "$ai_id")
    uncertainty=$(calculate_uncertainty_mastery "$ai_id")
    cascades=$(calculate_total_cascades "$ai_id")
    consistency=$(calculate_consistency "$ai_id")

    # Default to 0 if null
    growth=${growth:-0.0}
    completion=${completion:-0}
    goals=${goals:-0}
    sessions=${sessions:-0}
    uncertainty=${uncertainty:-0.0}
    cascades=${cascades:-0}
    consistency=${consistency:-0}

    badges=$(get_badges "$ai_id" "$growth" "$goals" "$sessions" "$uncertainty" "$cascades" "$consistency")

    if [ "$first" = false ]; then
      echo ","
    fi
    first=false

    echo "    {"
    echo "      \"ai_id\": \"$ai_id\","
    echo "      \"metrics\": {"
    echo "        \"learning_growth\": $growth,"
    echo "        \"goal_completion_rate\": $completion,"
    echo "        \"total_goals_completed\": $goals,"
    echo "        \"sessions_completed\": $sessions,"
    echo "        \"uncertainty_mastery\": $uncertainty,"
    echo "        \"total_cascades\": $cascades,"
    echo "        \"consistency\": $consistency"
    echo "      },"
    echo "      \"badges\": \"$badges\""
    echo "    }"
  done < <(get_all_ais)

  echo "  ],"
  echo "  \"timestamp\": \"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\""
  echo "}"

elif [ "$CSV_OUTPUT" = true ]; then
  echo "AI_ID,Learning_Growth,Goal_Completion_Rate,Total_Goals_Completed,Sessions_Completed,Uncertainty_Mastery,Total_Cascades,Consistency_Pct,Badges"

  while IFS= read -r ai_id; do
    if [ -z "$ai_id" ]; then
      continue
    fi

    growth=$(calculate_learning_growth "$ai_id")
    completion=$(calculate_goal_completion "$ai_id")
    goals=$(calculate_total_goals "$ai_id")
    sessions=$(calculate_sessions_completed "$ai_id")
    uncertainty=$(calculate_uncertainty_mastery "$ai_id")
    cascades=$(calculate_total_cascades "$ai_id")
    consistency=$(calculate_consistency "$ai_id")

    growth=${growth:-0.0}
    completion=${completion:-0}
    goals=${goals:-0}
    sessions=${sessions:-0}
    uncertainty=${uncertainty:-0.0}
    cascades=${cascades:-0}
    consistency=${consistency:-0}

    badges=$(get_badges "$ai_id" "$growth" "$goals" "$sessions" "$uncertainty" "$cascades" "$consistency")

    echo "$ai_id,$growth,$completion,$goals,$sessions,$uncertainty,$cascades,$consistency,\"$badges\""
  done < <(get_all_ais)

else
  # Terminal output (default)

  echo -e "\n${CYAN}════════════════════════════════════════════════════════════════${NC}"
  echo -e "${BOLD}${MAGENTA}⭐ EMPIRICA AI LEADERBOARD ⭐${NC}"
  echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}\n"

  # Build leaderboard array
  declare -a LEADERBOARD
  declare -a AI_IDS

  while IFS= read -r ai_id; do
    if [ -z "$ai_id" ]; then
      continue
    fi

    growth=$(calculate_learning_growth "$ai_id")
    completion=$(calculate_goal_completion "$ai_id")
    goals=$(calculate_total_goals "$ai_id")
    sessions=$(calculate_sessions_completed "$ai_id")
    uncertainty=$(calculate_uncertainty_mastery "$ai_id")
    cascades=$(calculate_total_cascades "$ai_id")
    consistency=$(calculate_consistency "$ai_id")

    # Default to 0 if null
    growth=${growth:-0.0}
    completion=${completion:-0}
    goals=${goals:-0}
    sessions=${sessions:-0}
    uncertainty=${uncertainty:-0.0}
    cascades=${cascades:-0}
    consistency=${consistency:-0}

    badges=$(get_badges "$ai_id" "$growth" "$goals" "$sessions" "$uncertainty" "$cascades" "$consistency")

    # Sort by learning growth (descending)
    LEADERBOARD+=("$growth|$ai_id|$goals|$sessions|$uncertainty|$cascades|$consistency|$badges")
    AI_IDS+=("$ai_id")
  done < <(get_all_ais)

  # Sort leaderboard by learning growth (descending)
  IFS=$'\n' sorted=($(sort -rn <<<"${LEADERBOARD[*]}" | uniq))
  unset IFS

  # Display leaderboard with ranking
  rank=1
  echo -e "${BOLD}🏅 TOP PERFORMERS (By Learning Growth)${NC}\n"

  for entry in "${sorted[@]}"; do
    IFS='|' read -r growth ai_id goals sessions uncertainty cascades consistency badges <<< "$entry"

    # Medal/rank display
    medal=""
    case $rank in
      1) medal="🥇" ;;
      2) medal="🥈" ;;
      3) medal="🥉" ;;
      *) medal="  " ;;
    esac

    # Color based on rank
    color="$NC"
    if [ $rank -eq 1 ]; then
      color="$BOLD$MAGENTA"
    elif [ $rank -eq 2 ]; then
      color="$BOLD$YELLOW"
    elif [ $rank -eq 3 ]; then
      color="$BOLD$GREEN"
    fi

    # Format: Medal Rank AI_ID [Badges] Metrics
    printf "${color}%s %2d. %-20s${NC} %s\n" "$medal" "$rank" "$ai_id" "$badges"

    # Detailed metrics on next line
    printf "   📊 Learning: ${YELLOW}%-6s${NC} | Goals: ${GREEN}%-3s${NC} | Sessions: ${BLUE}%-3s${NC} | Mastery: ${MAGENTA}%-6s${NC} | Cascades: %.0f\n" \
      "$growth" "$goals" "$sessions" "$uncertainty" "$cascades"

    rank=$((rank + 1))
  done

  echo ""
  echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}\n"

  # Badge legend
  echo -e "${BOLD}🎖️  ACHIEVEMENT BADGES${NC}\n"
  echo "  🚀 Launched      - Completed first session"
  echo "  ⚡ Speed Demon   - 5+ sessions completed"
  echo "  🧠 Brain Boost   - Learning growth > 0.10"
  echo "  🏆 Champion      - 10+ sessions completed"
  echo "  🎯 Goal Master   - 10+ goals completed"
  echo "  🔬 Scientist     - Learning growth > 0.15"
  echo "  ⚙️  Engineer      - 10+ cascades run"
  echo "  🎓 Scholar       - Uncertainty mastery > 0.70"
  echo "  👑 Elite         - 20+ sessions + 20+ goals + growth > 0.15"
  echo "  🌟 Rising Star   - New AI with high consistency + good learning"
  echo ""

  # Metrics explanation
  echo -e "${BOLD}📈 METRICS EXPLAINED${NC}\n"
  echo "  Learning Growth  - Average improvement from start to end of session"
  echo "  Goals Completed  - Number of goals successfully completed"
  echo "  Sessions         - Number of completed sessions"
  echo "  Uncertainty      - Mastery score (1.0 = complete certainty)"
  echo "  Cascades         - Total CASCADE workflow runs"
  echo ""

  echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
  echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Database: $DB_PATH"
  echo -e "${CYAN}════════════════════════════════════════════════════════════════\n${NC}"
fi
