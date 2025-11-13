"""
Onboarding Command Handler

Runs the interactive onboarding wizard to teach AI agents epistemic self-assessment.
Based on the onboarding guide at docs/ONBOARDING_GUIDE.md
"""

import asyncio
import sys
from pathlib import Path
from ..cli_utils import handle_cli_error


def handle_onboard_command(args):
    """
    Handle 'empirica onboard' command for first-time AI setup.
    
    Runs interactive onboarding wizard that teaches:
    - 4 core epistemic vectors (KNOW, DO, CONTEXT, UNCERTAINTY)
    - 7-phase cascade workflow
    - Calibration patterns (well-calibrated vs over/underconfident)
    - How to demonstrate epistemic transparency to users
    
    Args:
        args: CLI arguments
            - ai_id: Identifier for this AI agent
            - save: Whether to save onboarding session (default: True)
            - verbose: Show detailed output
    """
    try:
        ai_id = getattr(args, 'ai_id', 'unnamed_ai')
        save_session = getattr(args, 'save', True)
        
        print(f"\n🎓 Starting Empirica Onboarding for AI: {ai_id}")
        print(f"📖 Following onboarding guide: docs/ONBOARDING_GUIDE.md")
        print()
        
        # Import and run onboarding wizard
        from empirica.bootstraps.onboarding_wizard import EmpericaOnboardingWizard
        
        # Create wizard instance
        wizard = EmpericaOnboardingWizard(ai_id=ai_id)
        
        # Run interactive onboarding
        asyncio.run(wizard.run_interactive())
        
        # Export session if requested
        if save_session:
            print(f"\n✅ Onboarding session saved to ~/.empirica/onboarding/{ai_id}_*.json")
            print(f"   Use this for calibration baseline and session resumption")
        
        print("\n🎉 Onboarding complete!")
        print("\n📚 Next steps:")
        print("   1. Read: docs/skills/SKILL.md (30 min)")
        print("   2. Practice: Run 2-3 real tasks using PREFLIGHT → ACT → POSTFLIGHT")
        print("   3. Review: Check your calibration after each task")
        print("   4. Teach: Demonstrate Empirica to a first-time user")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Onboarding interrupted. You can resume anytime.")
        sys.exit(1)
    except Exception as e:
        handle_cli_error(e, "Onboarding command", getattr(args, 'verbose', False))
        sys.exit(1)


def check_if_onboarded(ai_id: str) -> bool:
    """
    Check if AI has completed onboarding.
    
    Args:
        ai_id: AI identifier
    
    Returns:
        True if onboarding session exists, False otherwise
    """
    onboarding_dir = Path.home() / ".empirica" / "onboarding"
    
    if not onboarding_dir.exists():
        return False
    
    # Look for any onboarding session for this AI
    sessions = list(onboarding_dir.glob(f"{ai_id}_*.json"))
    
    return len(sessions) > 0


def get_onboarding_status(ai_id: str) -> dict:
    """
    Get onboarding status for an AI.
    
    Args:
        ai_id: AI identifier
    
    Returns:
        Dict with onboarding status info
    """
    import json
    from datetime import datetime
    
    onboarding_dir = Path.home() / ".empirica" / "onboarding"
    
    if not onboarding_dir.exists():
        return {
            'onboarded': False,
            'session_count': 0,
            'latest_session': None
        }
    
    sessions = sorted(onboarding_dir.glob(f"{ai_id}_*.json"))
    
    if not sessions:
        return {
            'onboarded': False,
            'session_count': 0,
            'latest_session': None
        }
    
    # Read latest session
    latest = sessions[-1]
    try:
        with open(latest) as f:
            session_data = json.load(f)
        
        return {
            'onboarded': True,
            'session_count': len(sessions),
            'latest_session': latest.name,
            'completed_at': session_data.get('completed_at'),
            'phases_completed': session_data.get('phases_completed', []),
            'learning_delta': session_data.get('learning_delta', {}),
            'calibration': session_data.get('calibration', 'unknown')
        }
    except Exception as e:
        return {
            'onboarded': True,
            'session_count': len(sessions),
            'latest_session': latest.name,
            'error': str(e)
        }
