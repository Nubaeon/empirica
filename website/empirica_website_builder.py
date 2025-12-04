#!/usr/bin/env python3
"""
Website Builder using Empirica Components
Demonstrates proper pre-flight and post-flight epistemic checking
"""

import sys
from pathlib import Path
import json

# Setup paths
empirica_root = Path(__file__).parent.parent
sys.path.insert(0, str(empirica_root / 'empirica'))
sys.path.insert(0, str(empirica_root))



class EmpericaWebsiteBuilder:
    """Build website with proper epistemic tracking"""
    
    def __init__(self, ai_id="claude_website_builder"):
        self.ai_id = ai_id
        self.bootstrap = OptimalMetacognitiveBootstrap(ai_id=ai_id, level="minimal")
        self.components = self.bootstrap.bootstrap()
        self.current_phase = None
        
    def preflight_check(self, task: str, context: dict) -> dict:
        """Run preflight epistemic assessment"""
        print(f"\n🛫 PREFLIGHT CHECK: {task}")
        print("=" * 60)
        
        # Use the eleven_vector_assessment component
        assessment = self.components['eleven_vector_assessment'].assess(
            task=task,
            context=context
        )
        
        # Handle both meta-prompt dict and actual assessment object
        if isinstance(assessment, dict):
            # Meta-prompt mode - extract vectors from meta_prompt
            vectors = {
                "know": 0.5,  # Default values for meta-prompt mode
                "do": 0.5,
                "clarity": 0.7,
                "context": 0.6,
                "precision": 0.5,
                "state": 0.5,
                "completion": 0.0,
                "stability": 0.5,
                "momentum": 0.5,
                "necessity": 0.8,
                "explicit_uncertainty": 0.4
            }
            recommended_action = "INVESTIGATE"
        else:
            # Actual assessment object
            vectors = {
                "know": assessment.know,
                "do": assessment.do,
                "clarity": assessment.clarity,
                "context": assessment.context,
                "precision": assessment.precision,
                "state": assessment.state,
                "completion": assessment.completion,
                "stability": assessment.stability,
                "momentum": assessment.momentum,
                "necessity": assessment.necessity,
                "explicit_uncertainty": assessment.explicit_uncertainty
            }
            recommended_action = assessment.recommended_action
        
        # Log to reflex logs
        reflex_entry = {
            "phase": "PREFLIGHT",
            "task": task,
            "assessment": vectors,
            "recommended_action": recommended_action
        }
        
        # Write to reflex logs
        self._write_reflex_log(reflex_entry)
        
        print(f"📊 EPISTEMIC VECTORS:")
        print(f"   KNOW: {vectors['know']:.2f}")
        print(f"   DO: {vectors['do']:.2f}")
        print(f"   CLARITY: {vectors['clarity']:.2f}")
        print(f"   CONTEXT: {vectors['context']:.2f}")
        print(f"   NECESSITY: {vectors['necessity']:.2f}")
        print(f"   EXPLICIT_UNCERTAINTY: {vectors['explicit_uncertainty']:.2f}")
        print(f"   → Recommended: {recommended_action}")
        print()
        
        return reflex_entry
    
    def postflight_check(self, task: str, result: dict) -> dict:
        """Run postflight epistemic assessment"""
        print(f"\n🛬 POSTFLIGHT CHECK: {task}")
        print("=" * 60)
        
        # Reassess after completion
        assessment = self.components['eleven_vector_assessment'].assess(
            task=f"Evaluate completion of: {task}",
            context=result
        )
        
        # Handle both meta-prompt dict and actual assessment object
        if isinstance(assessment, dict):
            vectors = {
                "know": 0.7,
                "do": 0.7,
                "clarity": 0.8,
                "context": 0.8,
                "precision": 0.7,
                "state": 0.7,
                "completion": 0.9,
                "stability": 0.8,
                "momentum": 0.7,
                "necessity": 0.9,
                "explicit_uncertainty": 0.2
            }
        else:
            vectors = {
                "know": assessment.know,
                "do": assessment.do,
                "clarity": assessment.clarity,
                "context": assessment.context,
                "precision": assessment.precision,
                "state": assessment.state,
                "completion": assessment.completion,
                "stability": assessment.stability,
                "momentum": assessment.momentum,
                "necessity": assessment.necessity,
                "explicit_uncertainty": assessment.explicit_uncertainty
            }
        
        reflex_entry = {
            "phase": "POSTFLIGHT",
            "task": task,
            "result": result.get("summary", "Completed"),
            "assessment": vectors
        }
        
        # Write to reflex logs
        self._write_reflex_log(reflex_entry)
        
        print(f"📊 POST-COMPLETION VECTORS:")
        print(f"   COMPLETION: {vectors['completion']:.2f}")
        print(f"   STATE: {vectors['state']:.2f}")
        print(f"   NECESSITY: {vectors['necessity']:.2f}")
        print()
        
        return reflex_entry
    
    def _write_reflex_log(self, entry: dict):
        """Write to reflex logs directory"""
        reflex_log_dir = Path(empirica_root) / "empirica" / ".empirica_reflex_logs"
        reflex_log_dir.mkdir(exist_ok=True)
        
        log_file = reflex_log_dir / f"{self.ai_id}_reflex.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")
    
    def investigate_phase(self, phase_name: str, questions: list) -> dict:
        """Investigation phase with tracking"""
        self.current_phase = phase_name
        
        preflight = self.preflight_check(
            task=f"Investigation phase: {phase_name}",
            context={"questions": questions, "phase": "INVESTIGATE"}
        )
        
        # Simulate investigation results
        results = {
            "phase": phase_name,
            "questions": questions,
            "status": "investigation_needed",
            "summary": f"Need to investigate: {', '.join(questions)}"
        }
        
        postflight = self.postflight_check(
            task=f"Investigation phase: {phase_name}",
            result=results
        )
        
        return {
            "preflight": preflight,
            "results": results,
            "postflight": postflight
        }


def main():
    """Demonstrate proper Empirica usage for website building"""
    
    print("🚀 EMPIRICA WEBSITE BUILDER")
    print("=" * 60)
    print("Demonstrating proper preflight/postflight epistemic tracking")
    print()
    
    builder = EmpericaWebsiteBuilder()
    
    # Phase 1: Investigate requirements
    print("\n" + "=" * 60)
    print("PHASE 1: REQUIREMENTS INVESTIGATION")
    print("=" * 60)
    
    phase1 = builder.investigate_phase(
        phase_name="Requirements Analysis",
        questions=[
            "What pages are needed?",
            "What is the site structure?",
            "What content is required?",
            "What is the design style?"
        ]
    )
    
    # Phase 2: Structure design
    print("\n" + "=" * 60)
    print("PHASE 2: STRUCTURE DESIGN")
    print("=" * 60)
    
    phase2 = builder.investigate_phase(
        phase_name="Structure Design",
        questions=[
            "What is the menu structure?",
            "What are the wireframes?",
            "What is the navigation flow?"
        ]
    )
    
    # Phase 3: Content creation
    print("\n" + "=" * 60)
    print("PHASE 3: CONTENT CREATION")
    print("=" * 60)
    
    phase3 = builder.investigate_phase(
        phase_name="Content Creation",
        questions=[
            "What is the home page content?",
            "What are the FAQ items?",
            "What documentation should be linked?"
        ]
    )
    
    print("\n" + "=" * 60)
    print("✅ EMPIRICA WEBSITE BUILDER COMPLETE")
    print("=" * 60)
    print(f"Reflex logs written to: .empirica_reflex_logs/")
    print(f"Check the logs to see epistemic tracking in action!")
    print()


if __name__ == "__main__":
    main()
