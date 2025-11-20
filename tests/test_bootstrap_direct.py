#!/usr/bin/env python3
"""
Direct test of bootstrap functionality
"""

import sys
from pathlib import Path
import json

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

def test_bootstrap():
    """Test bootstrap directly"""
    try:
        from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_metacognition
        from empirica.data.session_database import SessionDatabase
        
        print("Testing bootstrap_metacognition...")
        config = bootstrap_metacognition("test_minimax", level=1)
        print(f"✅ Bootstrap metacognition successful: {len(config) if isinstance(config, dict) else 0} components")
        
        print("Testing session database...")
        db = SessionDatabase()
        session_id = db.create_session(
            ai_id="test_minimax",
            bootstrap_level=1,
            components_loaded=len(config) if isinstance(config, dict) else 0,
            user_id=None
        )
        db.close()
        print(f"✅ Session created: {session_id}")
        
        return True, session_id
        
    except Exception as e:
        import traceback
        print(f"❌ Bootstrap failed: {e}")
        print(traceback.format_exc())
        return False, None

if __name__ == "__main__":
    print("Direct Bootstrap Test")
    print("=" * 30)
    success, session_id = test_bootstrap()
    if success:
        print(f"🎉 Bootstrap test successful - Session ID: {session_id}")
    else:
        print("❌ Bootstrap test failed")