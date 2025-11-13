#!/bin/bash
# Example 1: Basic Reasoning Reconstruction
# 
# Purpose: Extract and analyze reasoning from a completed session
# Use case: Understand what an AI learned and how

set -e

echo "================================================"
echo "Example 1: Basic Reasoning Reconstruction"
echo "================================================"
echo ""

# Check if session_id provided
if [ -z "$1" ]; then
    echo "Usage: $0 <session_id>"
    echo ""
    echo "Finding recent sessions..."
    python3 << 'EOF'
from empirica.data.session_database import SessionDatabase
import json

db = SessionDatabase()
cursor = db.conn.cursor()

# Get last 5 sessions
cursor.execute("""
    SELECT session_id, ai_id, start_time, total_turns
    FROM sessions
    ORDER BY start_time DESC
    LIMIT 5
""")

sessions = cursor.fetchall()
if sessions:
    print("\nRecent sessions:")
    for s in sessions:
        print(f"  - {s[0]} (AI: {s[1]}, Started: {s[2]}, Turns: {s[3]})")
    print(f"\nExample: ./{sessions[0][0]}")
else:
    print("\nNo sessions found. Run 'empirica bootstrap' to create one.")

db.close()
EOF
    exit 1
fi

SESSION_ID="$1"
OUTPUT_DIR="./reasoning_analysis_${SESSION_ID}"

echo "Analyzing session: $SESSION_ID"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Step 1: Check if session exists
echo "Step 1: Verifying session exists..."
python3 << EOF
from empirica.data.session_database import SessionDatabase
import sys

db = SessionDatabase()
cursor = db.conn.cursor()

cursor.execute("SELECT session_id, ai_id, start_time FROM sessions WHERE session_id = ?", ("$SESSION_ID",))
session = cursor.fetchone()

if not session:
    print(f"❌ Error: Session $SESSION_ID not found")
    sys.exit(1)
    
print(f"✅ Found session: {session[0]}")
print(f"   AI: {session[1]}")
print(f"   Started: {session[2]}")
db.close()
EOF

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""

# Step 2: Export reflex logs  
echo "Step 2: Finding reflex logs..."
REFLEX_DIR=".empirica_reflex_logs"

if [ -d "$REFLEX_DIR" ]; then
    # Find logs for this session
    find "$REFLEX_DIR" -name "*${SESSION_ID}*.json" -o -name "*.json" | head -10 > "$OUTPUT_DIR/reflex_log_files.txt"
    
    LOG_COUNT=$(wc -l < "$OUTPUT_DIR/reflex_log_files.txt")
    echo "✅ Found $LOG_COUNT reflex log files"
    
    if [ $LOG_COUNT -gt 0 ]; then
        echo "   Sample logs:"
        head -3 "$OUTPUT_DIR/reflex_log_files.txt" | while read log; do
            echo "     - $log"
        done
    fi
else
    echo "⚠️  Reflex log directory not found: $REFLEX_DIR"
fi

echo ""

# Step 3: Query database for epistemic snapshots
echo "Step 3: Extracting epistemic snapshots from database..."
python3 << 'EOF'
from empirica.data.session_database import SessionDatabase
import json

db = SessionDatabase()
cursor = db.conn.cursor()

# Get cascades for this session
cursor.execute("""
    SELECT 
        cascade_id,
        task,
        started_at,
        completed_at,
        final_confidence,
        investigation_rounds
    FROM cascades
    WHERE session_id = ?
    ORDER BY started_at
""", ("$SESSION_ID",))

cascades = []
for row in cursor.fetchall():
    cascade = {
        "cascade_id": row[0],
        "task": row[1],
        "started_at": row[2],
        "completed_at": row[3],
        "final_confidence": row[4],
        "investigation_rounds": row[5]
    }
    
    # Get epistemic assessments for this cascade
    cursor.execute("""
        SELECT phase, overall_confidence, created_at
        FROM epistemic_assessments
        WHERE cascade_id = ?
        ORDER BY created_at
    """, (row[0],))
    
    cascade["assessments"] = []
    for assessment in cursor.fetchall():
        cascade["assessments"].append({
            "phase": assessment[0],
            "confidence": assessment[1],
            "timestamp": assessment[2]
        })
    
    cascades.append(cascade)

with open("$OUTPUT_DIR/cascades_data.json", "w") as f:
    json.dump(cascades, f, indent=2)

print(f"✅ Extracted {len(cascades)} cascades")
if cascades:
    print("\nCascade Summary:")
    for c in cascades[:3]:  # Show first 3
        print(f"  - {c['task'][:60]}...")
        print(f"    Started: {c['started_at']}, Confidence: {c['final_confidence']}")
        print(f"    Assessments: {len(c['assessments'])}")
    if len(cascades) > 3:
        print(f"  ... and {len(cascades) - 3} more")

db.close()
EOF

echo ""

# Step 4: Create learning timeline from database
echo "Step 4: Creating learning timeline..."
python3 << 'EOF'
from empirica.data.session_database import SessionDatabase
import json

db = SessionDatabase()
cursor = db.conn.cursor()

# Get all assessments ordered by time
cursor.execute("""
    SELECT 
        ea.created_at,
        ea.phase,
        ea.overall_confidence,
        ea.recommended_action,
        ea.know_score,
        ea.do_score,
        ea.context_score,
        ea.uncertainty_score,
        c.task
    FROM epistemic_assessments ea
    JOIN cascades c ON ea.cascade_id = c.cascade_id
    WHERE c.session_id = ?
    ORDER BY ea.created_at
""", ("$SESSION_ID",))

timeline = []
for row in cursor.fetchall():
    timeline.append({
        "timestamp": row[0],
        "phase": row[1],
        "confidence": row[2],
        "action": row[3],
        "know": row[4],
        "do": row[5],
        "context": row[6],
        "uncertainty": row[7],
        "task": row[8]
    })

with open("$OUTPUT_DIR/learning_timeline.json", "w") as f:
    json.dump(timeline, f, indent=2)

print(f"✅ Created timeline with {len(timeline)} events")

if timeline:
    print("\nTimeline Preview:")
    for i, event in enumerate(timeline[:5]):
        print(f"  [{i+1}] {event['timestamp']} - {event['phase']}")
        print(f"      KNOW: {event['know']:.2f}, UNCERTAINTY: {event['uncertainty']:.2f}")
        print(f"      Action: {event['action']}")
        print("")
    if len(timeline) > 5:
        print(f"  ... and {len(timeline) - 5} more events")

db.close()
EOF

echo ""

# Step 5: Calculate learning deltas
echo "Step 5: Calculating learning deltas..."
python3 << 'EOF'
import json

try:
    with open("$OUTPUT_DIR/learning_timeline.json", "r") as f:
        timeline = json.load(f)
except:
    print("⚠️  No timeline data available")
    exit(0)

if len(timeline) < 2:
    print("⚠️  Not enough data points for delta calculation")
    exit(0)

# Calculate deltas between first and last
first = timeline[0]
last = timeline[-1]

deltas = {
    "from_timestamp": first["timestamp"],
    "to_timestamp": last["timestamp"],
    "from_phase": first["phase"],
    "to_phase": last["phase"],
    "deltas": {
        "know": last["know"] - first["know"],
        "do": last["do"] - first["do"],
        "context": last["context"] - first["context"],
        "uncertainty": last["uncertainty"] - first["uncertainty"],
        "confidence": last["confidence"] - first["confidence"]
    }
}

with open("$OUTPUT_DIR/learning_deltas.json", "w") as f:
    json.dump(deltas, f, indent=2)

print("✅ Calculated learning deltas")
print("\nOverall Learning:")
print(f"  Period: {first['timestamp']} → {last['timestamp']}")
print(f"  Phase: {first['phase']} → {last['phase']}")
print("")

for key, value in deltas["deltas"].items():
    direction = "↑" if value > 0 else "↓" if value < 0 else "→"
    symbol = "✅" if (key == "uncertainty" and value < 0) or (key != "uncertainty" and value > 0) else "⚠️ "
    print(f"  {symbol} {key.upper():12} : {value:+.2f} {direction}")

# Identify key learning moments (big deltas between consecutive events)
key_moments = []
for i in range(1, len(timeline)):
    prev = timeline[i-1]
    curr = timeline[i]
    
    know_delta = curr["know"] - prev["know"]
    unc_delta = curr["uncertainty"] - prev["uncertainty"]
    
    if abs(know_delta) > 0.2 or abs(unc_delta) > 0.2:
        key_moments.append({
            "from": prev["timestamp"],
            "to": curr["timestamp"],
            "phase_change": f"{prev['phase']} → {curr['phase']}",
            "know_delta": know_delta,
            "uncertainty_delta": unc_delta,
            "task": curr["task"]
        })

if key_moments:
    with open("$OUTPUT_DIR/key_learning_moments.json", "w") as f:
        json.dump(key_moments, f, indent=2)
    
    print(f"\n✅ Identified {len(key_moments)} key learning moments")
    print("\nMost Significant:")
    for moment in sorted(key_moments, key=lambda x: abs(x["know_delta"]), reverse=True)[:3]:
        print(f"  - {moment['phase_change']}")
        print(f"    KNOW: {moment['know_delta']:+.2f}, UNCERTAINTY: {moment['uncertainty_delta']:+.2f}")
        print(f"    Task: {moment['task'][:50]}...")
        print("")

EOF

echo ""

# Step 6: Generate summary report
echo "Step 6: Generating summary report..."
python3 << 'EOF'
import json
from pathlib import Path

output_dir = Path("$OUTPUT_DIR")

report = []
report.append("=" * 70)
report.append("REASONING RECONSTRUCTION REPORT")
report.append("=" * 70)
report.append("")
report.append(f"Session ID: $SESSION_ID")
report.append("")

# Load timeline
try:
    with open(output_dir / "learning_timeline.json") as f:
        timeline = json.load(f)
    report.append(f"Total Events: {len(timeline)}")
except:
    report.append("Total Events: N/A")

# Load deltas
try:
    with open(output_dir / "learning_deltas.json") as f:
        deltas = json.load(f)
    report.append("")
    report.append("Overall Learning Progress:")
    report.append("-" * 70)
    for key, value in deltas["deltas"].items():
        direction = "↑" if value > 0 else "↓" if value < 0 else "→"
        report.append(f"  {key.upper():12} : {value:+.3f} {direction}")
except:
    pass

# Load key moments
try:
    with open(output_dir / "key_learning_moments.json") as f:
        moments = json.load(f)
    report.append("")
    report.append(f"Key Learning Moments: {len(moments)}")
except:
    pass

report.append("")
report.append("=" * 70)
report.append("Files Generated:")
report.append("-" * 70)
report.append("  1. reflex_log_files.txt     - Reflex log locations")
report.append("  2. cascades_data.json       - Cascade details")
report.append("  3. learning_timeline.json   - Temporal progression")
report.append("  4. learning_deltas.json     - Overall learning deltas")
report.append("  5. key_learning_moments.json - Significant changes")
report.append("  6. summary_report.txt       - This report")
report.append("")
report.append("=" * 70)

report_text = "\n".join(report)
print(report_text)

with open(output_dir / "summary_report.txt", "w") as f:
    f.write(report_text)
EOF

echo ""
echo "================================================"
echo "✅ Reconstruction Complete!"
echo "================================================"
echo ""
echo "Output: $OUTPUT_DIR/"
echo ""
echo "Key files:"
echo "  • summary_report.txt        - Executive summary"
echo "  • learning_timeline.json    - Full temporal progression"
echo "  • learning_deltas.json      - Overall learning metrics"
echo "  • key_learning_moments.json - Significant insights"
echo ""
echo "Next steps:"
echo "  • Review summary_report.txt for overview"
echo "  • Analyze key_learning_moments.json for insights"
echo "  • Use learning_timeline.json for detailed investigation"
echo ""
