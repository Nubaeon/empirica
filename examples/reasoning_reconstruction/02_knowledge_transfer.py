#!/usr/bin/env python3
"""
Example 2: Knowledge Transfer Between AI Agents

Purpose: Export knowledge from one AI's session and prepare it for another AI to learn from
Use case: AI-A completes a task, AI-B wants to learn faster from AI-A's experience
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add empirica to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from empirica.data.session_database import SessionDatabase


def export_knowledge_package(
    session_id: str,
    output_file: str,
    min_delta: float = 0.3,
    include_reasoning: bool = True,
    anonymize: bool = False
) -> Dict:
    """
    Export a knowledge package from a completed session.
    
    Args:
        session_id: Session to export from
        output_file: Where to save the knowledge package
        min_delta: Minimum learning delta to include (default 0.3)
        include_reasoning: Include reasoning text (default True)
        anonymize: Remove identifying information (default False)
    
    Returns:
        Knowledge package dict
    """
    print(f"📦 Exporting Knowledge Package")
    print(f"   Session: {session_id}")
    print(f"   Min Delta: {min_delta}")
    print(f"   Output: {output_file}")
    print("")
    
    db = SessionDatabase()
    cursor = db.conn.cursor()
    
    # Get session info
    cursor.execute("""
        SELECT session_id, ai_id, start_time, end_time
        FROM sessions
        WHERE session_id = ?
    """, (session_id,))
    
    session = cursor.fetchone()
    if not session:
        print(f"❌ Error: Session {session_id} not found")
        db.close()
        return None
    
    print(f"✅ Found session from AI: {session[1]}")
    
    # Get cascades with significant learning
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
    """, (session_id,))
    
    cascades = cursor.fetchall()
    print(f"✅ Found {len(cascades)} cascades")
    
    # Build knowledge package
    knowledge_package = {
        "format": "empirica_knowledge_package_v1",
        "exported_from_session": session_id if not anonymize else "anonymized",
        "exported_from_ai": session[1] if not anonymize else "anonymized",
        "exported_at": session[2],
        "min_delta_threshold": min_delta,
        "key_learnings": [],
        "reasoning_patterns": [],
        "calibration_info": {}
    }
    
    significant_learnings = 0
    
    for cascade in cascades:
        cascade_id = cascade[0]
        
        # Get epistemic assessments
        cursor.execute("""
            SELECT 
                phase,
                know_score,
                do_score,
                context_score,
                uncertainty_score,
                overall_confidence,
                created_at
            FROM epistemic_assessments
            WHERE cascade_id = ?
            ORDER BY created_at
        """, (cascade_id,))
        
        assessments = cursor.fetchall()
        
        if len(assessments) < 2:
            continue
        
        # Calculate deltas
        first = assessments[0]
        last = assessments[-1]
        
        know_delta = last[1] - first[1]  # know_score
        uncertainty_delta = last[4] - first[4]  # uncertainty_score
        
        # Check if significant learning occurred
        if abs(know_delta) >= min_delta or abs(uncertainty_delta) >= min_delta:
            significant_learnings += 1
            
            learning = {
                "topic": cascade[1] if not anonymize else "task_content_removed",
                "learned_at": cascade[2],
                "duration": (cascade[3] - cascade[2]) if cascade[3] else None,
                "investigation_rounds": cascade[5],
                "epistemic_progression": {
                    "initial_state": {
                        "know": first[1],
                        "do": first[2],
                        "context": first[3],
                        "uncertainty": first[4],
                        "confidence": first[5]
                    },
                    "final_state": {
                        "know": last[1],
                        "do": last[2],
                        "context": last[3],
                        "uncertainty": last[4],
                        "confidence": last[5]
                    },
                    "deltas": {
                        "know": know_delta,
                        "do": last[2] - first[2],
                        "context": last[3] - first[3],
                        "uncertainty": uncertainty_delta,
                        "confidence": last[5] - first[5]
                    }
                },
                "calibration_pattern": {
                    "confidence_increased": last[5] > first[5],
                    "uncertainty_decreased": last[4] < first[4],
                    "well_calibrated": (last[5] > first[5]) and (last[4] < first[4])
                }
            }
            
            knowledge_package["key_learnings"].append(learning)
    
    print(f"✅ Identified {significant_learnings} significant learnings")
    
    # Add reasoning patterns (high-level, no specifics)
    if significant_learnings > 0:
        avg_investigation = sum(c[5] or 0 for c in cascades) / len(cascades)
        
        knowledge_package["reasoning_patterns"] = [
            {
                "pattern": "investigation_strategy",
                "description": f"Average {avg_investigation:.1f} investigation rounds per task",
                "recommendation": "Consider investigation when uncertainty > 0.7"
            }
        ]
    
    # Calculate calibration statistics
    cursor.execute("""
        SELECT 
            AVG(CASE WHEN calibration_status = 'WELL_CALIBRATED' THEN 1 ELSE 0 END) as calibration_rate
        FROM cascades
        WHERE session_id = ? AND calibration_status IS NOT NULL
    """, (session_id,))
    
    calibration = cursor.fetchone()
    if calibration[0] is not None:
        knowledge_package["calibration_info"] = {
            "calibration_rate": calibration[0],
            "interpretation": "high" if calibration[0] > 0.7 else "moderate" if calibration[0] > 0.4 else "low"
        }
    
    # Save package
    with open(output_file, "w") as f:
        json.dump(knowledge_package, f, indent=2)
    
    print(f"\n✅ Knowledge package saved to: {output_file}")
    print(f"   Significant learnings: {significant_learnings}")
    print(f"   Calibration rate: {knowledge_package.get('calibration_info', {}).get('calibration_rate', 'N/A')}")
    
    db.close()
    return knowledge_package


def import_knowledge_as_context(
    knowledge_file: str,
    output_context_file: str
) -> str:
    """
    Convert knowledge package into learning context for another AI.
    
    Args:
        knowledge_file: Knowledge package JSON file
        output_context_file: Where to save the learning context
    
    Returns:
        Learning context as markdown string
    """
    print(f"\n📚 Converting Knowledge Package to Learning Context")
    print(f"   Input: {knowledge_file}")
    print(f"   Output: {output_context_file}")
    print("")
    
    with open(knowledge_file, "r") as f:
        package = json.load(f)
    
    # Generate learning context in markdown
    context = []
    context.append("# Learning Context from Previous AI Experience")
    context.append("")
    context.append(f"**Source:** {package.get('exported_from_ai', 'Anonymous AI')}")
    context.append(f"**Exported:** {package.get('exported_at', 'Unknown')}")
    context.append("")
    context.append("---")
    context.append("")
    context.append("## Key Learnings")
    context.append("")
    
    for i, learning in enumerate(package.get("key_learnings", []), 1):
        context.append(f"### Learning {i}: {learning.get('topic', 'Task')}")
        context.append("")
        
        prog = learning.get("epistemic_progression", {})
        initial = prog.get("initial_state", {})
        final = prog.get("final_state", {})
        deltas = prog.get("deltas", {})
        
        context.append(f"**Epistemic Progression:**")
        context.append(f"- KNOW: {initial.get('know', 0):.2f} → {final.get('know', 0):.2f} (Δ {deltas.get('know', 0):+.2f})")
        context.append(f"- UNCERTAINTY: {initial.get('uncertainty', 0):.2f} → {final.get('uncertainty', 0):.2f} (Δ {deltas.get('uncertainty', 0):+.2f})")
        context.append(f"- Investigation rounds: {learning.get('investigation_rounds', 0)}")
        context.append("")
        
        cal = learning.get("calibration_pattern", {})
        if cal.get("well_calibrated"):
            context.append("**Result:** Well-calibrated (confidence ↑, uncertainty ↓)")
        else:
            context.append("**Result:** Learning occurred but calibration unclear")
        
        context.append("")
        context.append("**Key Insight:** Significant learning delta indicates this was a valuable learning experience.")
        context.append("")
    
    context.append("---")
    context.append("")
    context.append("## Reasoning Patterns Observed")
    context.append("")
    
    for pattern in package.get("reasoning_patterns", []):
        context.append(f"- **{pattern.get('pattern', 'Pattern')}**: {pattern.get('description', '')}")
        context.append(f"  - Recommendation: {pattern.get('recommendation', 'N/A')}")
        context.append("")
    
    context.append("---")
    context.append("")
    context.append("## How to Use This Context")
    context.append("")
    context.append("1. Review the epistemic progressions to understand learning trajectories")
    context.append("2. Note which tasks required investigation (high uncertainty)")
    context.append("3. Use reasoning patterns as guidance, not rules")
    context.append("4. Still assess your own epistemic state - this is context, not direct knowledge")
    context.append("")
    context.append("**Remember:** You still need to learn through your own experience. This context helps you learn faster, not skip learning.")
    
    context_text = "\n".join(context)
    
    # Save context
    with open(output_context_file, "w") as f:
        f.write(context_text)
    
    print(f"✅ Learning context saved to: {output_context_file}")
    print(f"   Learnings included: {len(package.get('key_learnings', []))}")
    print("")
    print("Preview:")
    print("-" * 70)
    print("\n".join(context[:20]))
    if len(context) > 20:
        print(f"... and {len(context) - 20} more lines")
    
    return context_text


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Export: python 02_knowledge_transfer.py export <session_id> [output_file] [min_delta]")
        print("  Import: python 02_knowledge_transfer.py import <knowledge_file> [context_file]")
        print("")
        print("Examples:")
        print("  python 02_knowledge_transfer.py export session_abc123")
        print("  python 02_knowledge_transfer.py import knowledge_package.json")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "export":
        if len(sys.argv) < 3:
            print("Error: session_id required")
            sys.exit(1)
        
        session_id = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else f"knowledge_package_{session_id}.json"
        min_delta = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
        
        export_knowledge_package(session_id, output_file, min_delta=min_delta)
    
    elif action == "import":
        if len(sys.argv) < 3:
            print("Error: knowledge_file required")
            sys.exit(1)
        
        knowledge_file = sys.argv[2]
        output_context = sys.argv[3] if len(sys.argv) > 3 else f"learning_context_{Path(knowledge_file).stem}.md"
        
        import_knowledge_as_context(knowledge_file, output_context)
    
    else:
        print(f"Error: Unknown action '{action}'")
        print("Use 'export' or 'import'")
        sys.exit(1)


if __name__ == "__main__":
    main()
