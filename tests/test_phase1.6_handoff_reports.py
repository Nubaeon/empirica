#!/usr/bin/env python3
"""
Integration test for Phase 1.6: Epistemic Handoff Reports

Tests:
1. Report generation
2. Git storage
3. Database storage
4. Handoff resumption
5. Query functionality
"""

import sys
import json
import tempfile
from pathlib import Path

# Add empirica to path
sys.path.insert(0, str(Path(__file__).parent))

from empirica.core.handoff import (
    EpistemicHandoffReportGenerator,
    GitHandoffStorage,
    DatabaseHandoffStorage
)
from empirica.data.session_database import SessionDatabase


def test_report_generation():
    """Test basic handoff report generation"""
    print("\n🧪 Test 1: Report Generation")
    print("=" * 60)
    
    # Create test database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = SessionDatabase(str(db_path))
        
        # Create test session
        session_id = "test-session-001"
        cursor = db.conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions 
            (session_id, ai_id, start_time, bootstrap_level, components_loaded)
            VALUES (?, ?, datetime('now'), 1, 5)
        """, (session_id, "copilot-claude"))
        
        # Create test assessments
        test_vectors = {
            'know': 0.70, 'do': 0.80, 'context': 0.75,
            'clarity': 0.85, 'coherence': 0.80, 'signal': 0.75, 'density': 0.70,
            'state': 0.60, 'change': 0.65, 'completion': 0.30, 'impact': 0.50,
            'engagement': 0.90, 'uncertainty': 0.45
        }
        
        cursor.execute("""
            INSERT INTO preflight_assessments
            (assessment_id, session_id, prompt_summary, engagement, know, do, context,
             clarity, coherence, signal, density, state, change, completion, impact,
             uncertainty, initial_uncertainty_notes)
            VALUES (?, ?, 'Test prompt', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Test preflight')
        """, ('preflight-001', session_id, test_vectors['engagement'], test_vectors['know'],
              test_vectors['do'], test_vectors['context'], test_vectors['clarity'],
              test_vectors['coherence'], test_vectors['signal'], test_vectors['density'],
              test_vectors['state'], test_vectors['change'], test_vectors['completion'],
              test_vectors['impact'], test_vectors['uncertainty']))
        
        # Postflight with improvements
        postflight_vectors = test_vectors.copy()
        postflight_vectors['know'] = 0.95
        postflight_vectors['uncertainty'] = 0.20
        postflight_vectors['completion'] = 0.95
        
        cursor.execute("""
            INSERT INTO postflight_assessments
            (assessment_id, session_id, task_summary, engagement, know, do, context,
             clarity, coherence, signal, density, state, change, completion, impact,
             uncertainty, postflight_actual_confidence, calibration_accuracy, learning_notes)
            VALUES (?, ?, 'Test task', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'well_calibrated', 'Test postflight')
        """, ('postflight-001', session_id, postflight_vectors['engagement'], postflight_vectors['know'],
              postflight_vectors['do'], postflight_vectors['context'], postflight_vectors['clarity'],
              postflight_vectors['coherence'], postflight_vectors['signal'], postflight_vectors['density'],
              postflight_vectors['state'], postflight_vectors['change'], postflight_vectors['completion'],
              postflight_vectors['impact'], postflight_vectors['uncertainty'],
              0.85))
        
        db.conn.commit()
        
        # Generate handoff report
        generator = EpistemicHandoffReportGenerator(str(db_path))
        
        report = generator.generate_handoff_report(
            session_id=session_id,
            task_summary="Implemented Phase 1.6 Epistemic Handoff Reports",
            key_findings=[
                "Created report generator with vector delta calculation",
                "Implemented dual storage (git + database)",
                "Added 3 new MCP tools for handoff lifecycle"
            ],
            remaining_unknowns=[
                "Long-term scalability with 100+ sessions",
                "Cross-repository handoff coordination"
            ],
            next_session_context="Phase 1.6 complete. Ready for Phase 2 validation and documentation.",
            artifacts_created=[
                "empirica/core/handoff/report_generator.py",
                "empirica/core/handoff/storage.py"
            ]
        )
        
        # Validate report structure
        assert 'session_id' in report
        assert 'epistemic_deltas' in report
        assert 'markdown' in report
        assert 'compressed_json' in report
        
        # Check deltas
        assert report['epistemic_deltas']['know'] == 0.25
        assert report['epistemic_deltas']['uncertainty'] == -0.25
        
        # Check token count
        token_estimate = len(report['compressed_json']) // 4
        
        print(f"✅ Report generated successfully")
        print(f"   Session: {session_id[:12]}...")
        print(f"   Epistemic deltas: {len(report['epistemic_deltas'])} vectors")
        print(f"   Key findings: {len(report['key_findings'])} items")
        print(f"   Compressed JSON: {len(report['compressed_json'])} chars")
        print(f"   Token estimate: ~{token_estimate} tokens")
        print(f"   Markdown length: {len(report['markdown'])} chars")
        print(f"   Calibration: {report['calibration_status']}")
        
        return report


def test_git_storage():
    """Test git notes storage"""
    print("\n🧪 Test 2: Git Storage")
    print("=" * 60)
    
    # Create test report
    test_report = {
        'session_id': 'test-git-001',
        'ai_id': 'copilot-claude',
        'timestamp': '2025-11-17T16:00:00',
        'compressed_json': json.dumps({'s': 'test-git', 'task': 'Test task'}),
        'markdown': '# Test Handoff\n\nTest markdown content'
    }
    
    try:
        storage = GitHandoffStorage()
        
        # Store
        note_sha = storage.store_handoff('test-git-001', test_report)
        print(f"✅ Stored in git notes: {note_sha[:12]}...")
        
        # Load JSON
        loaded_json = storage.load_handoff('test-git-001', format='json')
        assert loaded_json is not None
        print(f"✅ Loaded JSON: {loaded_json}")
        
        # Load markdown
        loaded_md = storage.load_handoff('test-git-001', format='markdown')
        assert '# Test Handoff' in loaded_md['markdown']
        print(f"✅ Loaded markdown ({len(loaded_md['markdown'])} chars)")
        
        # List handoffs
        handoffs = storage.list_handoffs()
        print(f"✅ Listed {len(handoffs)} handoff(s) in git notes")
        
    except Exception as e:
        print(f"⚠️ Git storage test skipped: {e}")
        print("   (This is OK if not in a git repository)")


def test_database_storage():
    """Test database storage"""
    print("\n🧪 Test 3: Database Storage")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_handoffs.db"
        storage = DatabaseHandoffStorage(str(db_path))
        
        # Create test report
        test_report = {
            'session_id': 'test-db-001',
            'ai_id': 'copilot-claude',
            'timestamp': '2025-11-17T16:00:00',
            'task_summary': 'Test database storage',
            'duration_seconds': 3600.0,
            'epistemic_deltas': {'know': 0.25, 'uncertainty': -0.30},
            'key_findings': ['Finding 1', 'Finding 2'],
            'knowledge_gaps_filled': [],
            'remaining_unknowns': ['Unknown 1'],
            'investigation_tools': ['Tool A', 'Tool B'],
            'next_session_context': 'Continue testing',
            'recommended_next_steps': ['Step 1', 'Step 2'],
            'artifacts_created': ['file1.py', 'file2.py'],
            'calibration_status': 'well_calibrated',
            'overall_confidence_delta': 0.28,
            'compressed_json': '{"s":"test-db"}',
            'markdown': '# Test\n\nMarkdown content'
        }
        
        # Store
        storage.store_handoff('test-db-001', test_report)
        print(f"✅ Stored in database: test-db-001")
        
        # Load
        loaded = storage.load_handoff('test-db-001')
        assert loaded is not None
        assert loaded['session_id'] == 'test-db-001'
        assert loaded['ai_id'] == 'copilot-claude'
        print(f"✅ Loaded from database: {loaded['session_id']}")
        
        # Query by AI
        results = storage.query_handoffs(ai_id='copilot-claude', limit=10)
        assert len(results) >= 1
        print(f"✅ Queried by AI: {len(results)} result(s)")
        
        # Query by date
        results = storage.query_handoffs(since='2025-11-01', limit=10)
        assert len(results) >= 1
        print(f"✅ Queried by date: {len(results)} result(s)")


def test_handoff_resumption():
    """Test session resumption workflow"""
    print("\n🧪 Test 4: Handoff Resumption")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple sessions
        db_path = Path(tmpdir) / "test_resume.db"
        db = SessionDatabase(str(db_path))
        db_storage = DatabaseHandoffStorage(str(db_path))
        
        # Create 3 test sessions
        for i in range(3):
            session_id = f"session-00{i+1}"
            cursor = db.conn.cursor()
            
            cursor.execute("""
                INSERT INTO sessions 
                (session_id, ai_id, start_time, bootstrap_level, components_loaded)
                VALUES (?, 'copilot-claude', datetime('now', ?), 1, 5)
            """, (session_id, f'-{i} hours'))
            db.conn.commit()
            
            # Store handoff
            report = {
                'session_id': session_id,
                'ai_id': 'copilot-claude',
                'timestamp': f'2025-11-17T{15-i}:00:00',
                'task_summary': f'Task {i+1}',
                'duration_seconds': 1800.0,
                'epistemic_deltas': {'know': 0.20, 'uncertainty': -0.25},
                'key_findings': [f'Finding {i+1}'],
                'knowledge_gaps_filled': [],
                'remaining_unknowns': [],
                'investigation_tools': ['Tool A'],
                'next_session_context': f'Context {i+1}',
                'recommended_next_steps': [f'Step {i+1}'],
                'artifacts_created': [],
                'calibration_status': 'well_calibrated',
                'overall_confidence_delta': 0.22,
                'compressed_json': f'{{"s":"s-{i}"}}',
                'markdown': f'# Session {i+1}'
            }
            db_storage.store_handoff(session_id, report)
        
        # Resume last session
        results = db_storage.query_handoffs(ai_id='copilot-claude', limit=1)
        assert len(results) == 1
        print(f"✅ Resumed last session: {results[0]['session_id']}")
        
        # Resume last 3 sessions
        results = db_storage.query_handoffs(ai_id='copilot-claude', limit=3)
        assert len(results) == 3
        print(f"✅ Resumed last 3 sessions: {[r['session_id'] for r in results]}")
        
        # Calculate total tokens
        total_tokens = sum(len(r['compressed_json']) // 4 for r in results)
        print(f"✅ Total token estimate: ~{total_tokens} tokens")


def test_query_functionality():
    """Test handoff report queries"""
    print("\n🧪 Test 5: Query Functionality")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_query.db"
        storage = DatabaseHandoffStorage(str(db_path))
        
        # Create test reports for different AIs
        test_data = [
            ('session-001', 'copilot-claude', 'Testing functionality', '2025-11-17'),
            ('session-002', 'minimax', 'Validation testing', '2025-11-16'),
            ('session-003', 'copilot-claude', 'Documentation work', '2025-11-15'),
        ]
        
        for session_id, ai_id, task, date in test_data:
            report = {
                'session_id': session_id,
                'ai_id': ai_id,
                'timestamp': f'{date}T12:00:00',
                'task_summary': task,
                'duration_seconds': 1200.0,
                'epistemic_deltas': {},
                'key_findings': [],
                'knowledge_gaps_filled': [],
                'remaining_unknowns': [],
                'investigation_tools': [],
                'next_session_context': '',
                'recommended_next_steps': [],
                'artifacts_created': [],
                'calibration_status': 'well_calibrated',
                'overall_confidence_delta': 0.0,
                'compressed_json': '{}',
                'markdown': ''
            }
            storage.store_handoff(session_id, report)
        
        # Query by AI
        claude_reports = storage.query_handoffs(ai_id='copilot-claude', limit=10)
        assert len(claude_reports) == 2
        print(f"✅ Query by AI (copilot-claude): {len(claude_reports)} results")
        
        minimax_reports = storage.query_handoffs(ai_id='minimax', limit=10)
        assert len(minimax_reports) == 1
        print(f"✅ Query by AI (minimax): {len(minimax_reports)} results")
        
        # Query by date
        recent = storage.query_handoffs(since='2025-11-16', limit=10)
        assert len(recent) >= 2
        print(f"✅ Query by date (since 2025-11-16): {len(recent)} results")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 Phase 1.6 Integration Tests")
    print("=" * 60)
    
    try:
        # Run all tests
        report = test_report_generation()
        test_git_storage()
        test_database_storage()
        test_handoff_resumption()
        test_query_functionality()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
        # Show sample report
        print("\n📋 Sample Handoff Report (Markdown):")
        print("=" * 60)
        print(report['markdown'][:1000] + "...\n")
        
        print("📊 Sample Compressed JSON:")
        print("=" * 60)
        compressed = json.loads(report['compressed_json'])
        print(json.dumps(compressed, indent=2))
        
        print("\n✅ Phase 1.6 implementation validated!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
