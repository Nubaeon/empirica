#!/usr/bin/env python3
"""
Test script to identify MCP dependency issues
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test critical imports"""
    print("Testing critical imports...")
    
    # Test MCP imports
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp import types
        print("✅ MCP imports successful")
    except Exception as e:
        print(f"❌ MCP imports failed: {e}")
        return False
    
    # Test Empirica core imports
    try:
        from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_metacognition
        print("✅ Empirica bootstrap import successful")
    except Exception as e:
        print(f"❌ Empirica bootstrap import failed: {e}")
        return False
    
    # Test database imports
    try:
        from empirica.data.session_database import SessionDatabase
        print("✅ Empirica database import successful")
    except Exception as e:
        print(f"❌ Empirica database import failed: {e}")
        return False
    
    # Test git enhanced imports
    try:
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        print("✅ Git enhanced import successful")
    except Exception as e:
        print(f"❌ Git enhanced import failed: {e}")
        return False
    
    # Test session resolver
    try:
        from empirica.utils.session_resolver import resolve_session_id
        print("✅ Session resolver import successful")
    except Exception as e:
        print(f"❌ Session resolver import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        # Test connection
        print("✅ Database connection successful")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Empirica MCP Dependency Test")
    print("=" * 40)
    
    imports_ok = test_imports()
    functionality_ok = test_basic_functionality()
    
    if imports_ok and functionality_ok:
        print("\n🎉 All tests passed - dependencies are working")
    else:
        print("\n❌ Some tests failed - this explains the MCP tool errors")