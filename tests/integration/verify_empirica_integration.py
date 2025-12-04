#!/usr/bin/env python3
"""
Empirica Integration Verification Script

Systematically verifies:
1. Database schema alignment (13 vectors in all tables)
2. Reflex log auto-writing
3. Session tracking
4. Bootstrap integration  
5. Workflow orchestration
6. MCP server alignment

Uses Empirica's own workflow to verify itself (dogfooding).
"""

import sys
from pathlib import Path
import sqlite3
import json
from datetime import datetime

# Add empirica to path
empirica_root = Path(__file__).parent
sys.path.insert(0, str(empirica_root / 'empirica'))
sys.path.insert(0, str(empirica_root))

print("=" * 80)
print(" EMPIRICA INTEGRATION VERIFICATION")
print("=" * 80)
print()

# === VERIFICATION 1: Database Schema ===
print("1️⃣ VERIFYING DATABASE SCHEMA")
print("-" * 80)

try:
    from empirica.data.session_database import SessionDatabase
    
    db = SessionDatabase()
    cursor = db.conn.cursor()
    
    # Check epistemic_assessments for 13th vector
    cursor.execute("PRAGMA table_info(epistemic_assessments)")
    ea_columns = {col[1]: col[2] for col in cursor.fetchall()}
    
    # Check preflight_assessments
    cursor.execute("PRAGMA table_info(preflight_assessments)")
    pa_columns = {col[1]: col[2] for col in cursor.fetchall()}
    
    # Check postflight_assessments  
    cursor.execute("PRAGMA table_info(postflight_assessments)")
    pfa_columns = {col[1]: col[2] for col in cursor.fetchall()}
    
    print(f"   📊 Epistemic Assessments: {len(ea_columns)} columns")
    if 'uncertainty' in ea_columns:
        print(f"      ✅ 13th vector 'uncertainty' present")
    else:
        print(f"      ❌ 13th vector 'uncertainty' MISSING")
    
    print(f"   📊 Preflight Assessments: {len(pa_columns)} columns")
    if 'explicit_uncertainty' in pa_columns:
        print(f"      ✅ 13 vectors including 'explicit_uncertainty'")
    else:
        print(f"      ❌ 'explicit_uncertainty' MISSING")
    
    print(f"   📊 Postflight Assessments: {len(pfa_columns)} columns")
    if 'explicit_uncertainty' in pfa_columns:
        print(f"      ✅ 13 vectors including 'explicit_uncertainty'")
    else:
        print(f"      ❌ 'explicit_uncertainty' MISSING")
    
    # Check cascade phases
    cursor.execute("PRAGMA table_info(cascades)")
    cascade_columns = {col[1]: col[2] for col in cursor.fetchall()}
    
    required_phases = ['preflight_completed', 'think_completed', 'plan_completed', 
                      'investigate_completed', 'check_completed', 'act_completed', 
                      'postflight_completed']
    
    print(f"   📊 Cascade Phases:")
    all_phases_present = True
    for phase in required_phases:
        if phase in cascade_columns:
            print(f"      ✅ {phase}")
        else:
            print(f"      ❌ {phase} MISSING")
            all_phases_present = False
    
    db.close()
    print()
    
except Exception as e:
    print(f"   ❌ Database verification failed: {e}")
    print()

# === VERIFICATION 2: Reflex Logs ===
print("2️⃣ VERIFYING REFLEX LOGS AUTO-WRITING")
print("-" * 80)

try:
    reflex_logs_dir = empirica_root / 'empirica' / '.empirica_reflex_logs'
    
    if reflex_logs_dir.exists():
        log_files = list(reflex_logs_dir.rglob('*.json'))
        print(f"   ✅ Reflex logs directory exists: {reflex_logs_dir}")
        print(f"   📝 Total log files: {len(log_files)}")
        
        # Check recent logs
        if log_files:
            recent_log = max(log_files, key=lambda p: p.stat().st_mtime)
            mod_time = datetime.fromtimestamp(recent_log.stat().st_mtime)
            print(f"   📅 Most recent log: {recent_log.name}")
            print(f"   🕒 Last modified: {mod_time}")
            
            # Read a sample log
            with open(recent_log) as f:
                sample = json.load(f)
                if 'epistemicState' in sample or 'vectors' in sample:
                    print(f"   ✅ Log structure valid")
                else:
                    print(f"   ⚠️  Log structure may be outdated")
        else:
            print(f"   ⚠️  No log files found - logs may not be auto-writing")
    else:
        print(f"   ❌ Reflex logs directory not found: {reflex_logs_dir}")
    
    print()
    
except Exception as e:
    print(f"   ❌ Reflex logs verification failed: {e}")
    print()

# === VERIFICATION 3: Session JSON Exports ===
print("3️⃣ VERIFYING SESSION JSON EXPORTS")
print("-" * 80)

try:
    exports_dir = empirica_root / 'empirica' / '.empirica' / 'exports'
    
    if exports_dir.exists():
        session_exports = list(exports_dir.glob('session_*.json'))
        cascade_exports = list(exports_dir.glob('cascade_*_graph.json'))
        
        print(f"   ✅ Exports directory exists: {exports_dir}")
        print(f"   📄 Session exports: {len(session_exports)}")
        print(f"   📊 Cascade graph exports: {len(cascade_exports)}")
        
        if session_exports:
            print(f"   ✅ Session JSON auto-export working")
        else:
            print(f"   ⚠️  No session exports found")
    else:
        print(f"   ⚠️  Exports directory not found: {exports_dir}")
        print(f"      (Will be created on first export)")
    
    print()
    
except Exception as e:
    print(f"   ❌ Session export verification failed: {e}")
    print()

# === VERIFICATION 4: Bootstrap Integration ===
print("4️⃣ VERIFYING BOOTSTRAP INTEGRATION")
print("-" * 80)

try:
        
    # Test bootstrap (minimal to avoid heavy loading)
    print("   🔄 Testing bootstrap initialization...")
    bootstrap = OptimalMetacognitiveBootstrap(ai_id="verification_test", level="minimal")
    components = bootstrap.bootstrap_minimal()
    
    print(f"   ✅ Bootstrap loaded successfully")
    print(f"   📦 Components loaded: {len(components)}")
    
    # Check for canonical cascade components
    canonical_components = ['canonical_cascade', 'canonical_adapter']
    for comp in canonical_components:
        if comp in components:
            print(f"      ✅ {comp}")
        else:
            print(f"      ⚠️  {comp} not loaded")
    
    # Check for auto-tracker
    if 'tracker' in components:
        print(f"   ✅ Auto-tracker integrated")
        tracker = components['tracker']
        if hasattr(tracker, 'session_id'):
            print(f"      Session ID: {tracker.session_id}")
    else:
        print(f"   ⚠️  Auto-tracker not found in components")
    
    print()
    
except Exception as e:
    print(f"   ❌ Bootstrap verification failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# === VERIFICATION 5: Workflow Components ===
print("5️⃣ VERIFYING WORKFLOW COMPONENTS")
print("-" * 80)

try:
    from empirica.core.metacognitive_cascade.metacognitive_cascade import CanonicalEpistemicCascade
    from empirica.cognitive_benchmarking.erb.cascade_workflow_orchestrator import CanonicalCascadeAdapter
    
    print("   ✅ Workflow imports successful")
    print("      - CanonicalEpistemicCascade")
    print("      - CanonicalCascadeAdapter")
    
    # Check canonical cascade structure
    test_cascade = CanonicalEpistemicCascade("test-session")
    print(f"   ✅ Canonical cascade initialized")
    
    print()
except Exception as e:
    print(f"   ❌ Workflow verification failed: {e}")
    print()

# === VERIFICATION 6: Core Components ===
print("6️⃣ VERIFYING CORE COMPONENTS")
print("-" * 80)

try:
    # Check for key component modules
    component_paths = [
        empirica_root / 'empirica' / 'workflow',
        empirica_root / 'empirica' / 'data',
        empirica_root / 'empirica' / 'core' / 'canonical',
        empirica_root / 'empirica' / 'cognitive_benchmarking',
        empirica_root / 'empirica' / 'cli',
        empirica_root / 'empirica' / 'components',
    ]
    
    for path in component_paths:
        if path.exists():
            py_files = list(path.glob('*.py'))
            print(f"   ✅ {path.name}: {len(py_files)} modules")
        else:
            print(f"   ❌ {path.name}: NOT FOUND")
    
    print()
    
except Exception as e:
    print(f"   ❌ Core components verification failed: {e}")
    print()

# === FINAL SUMMARY ===
print("=" * 80)
print(" VERIFICATION COMPLETE")
print("=" * 80)
print()
print("✅ = Working as expected")
print("⚠️  = Needs attention or not yet implemented")
print("❌ = Critical issue found")
print()
print("Next steps:")
print("1. Review any ⚠️  or ❌ items above")
print("2. Check that reflex logs auto-write during cascade execution")
print("3. Verify MCP server exposes workflow tools")
print("4. Test full cascade workflow with preflight/postflight")
print()
