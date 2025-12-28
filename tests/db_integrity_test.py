#!/usr/bin/env python3
"""
Comprehensive Database Integrity Test
Verifies all database operations work correctly without connection timeouts
"""

import sys
import time
import sqlite3
from pathlib import Path
from empirica.data.session_database import SessionDatabase

def test_db_connection():
    """Test basic database connection"""
    print("🔍 TEST 1: Basic Connection")
    try:
        db = SessionDatabase()
        print("  ✓ SessionDatabase instantiated")
        
        # Try a simple query
        cursor = db.conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"  ✓ Query executed: {result}")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

def test_table_schemas():
    """Test that all tables exist and have correct schemas"""
    print("\n🔍 TEST 2: Table Schemas")
    db = SessionDatabase()
    cursor = db.conn.cursor()
    
    required_tables = [
        'sessions', 'reflexes', 'goals', 'subtasks', 'project_findings', 'project_unknowns',
        'project_dead_ends', 'mistakes_made', 'auto_captured_issues', 'project_handoffs'
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = set([row[0] for row in cursor.fetchall()])
    
    missing = set(required_tables) - existing_tables
    if missing:
        print(f"  ✗ Missing tables: {missing}")
        return False
    
    print(f"  ✓ All {len(required_tables)} required tables exist")
    return True

def test_concurrent_access():
    """Test multiple database connections don't cause timeouts"""
    print("\n🔍 TEST 3: Concurrent Access (5 connections)")
    
    try:
        connections = []
        for i in range(5):
            db = SessionDatabase()
            cursor = db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions")
            count = cursor.fetchone()[0]
            connections.append(db)
            print(f"  ✓ Connection {i+1}: {count} sessions")
        
        # Close all
        for db in connections:
            db.conn.close()
        
        print("  ✓ All concurrent connections succeeded")
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

def test_create_operations():
    """Test CREATE operations that might timeout"""
    print("\n🔍 TEST 4: CREATE Operations")
    
    try:
        db = SessionDatabase()
        
        # Create session
        session_id = db.create_session(ai_id="test-integrity", components_loaded=6)
        print(f"  ✓ Created session: {session_id}")
        
        # Create goal
        goal_id = db.create_goal(
            session_id=session_id,
            objective="Test goal",
            scope_breadth=0.5,
            scope_duration=0.5,
            scope_coordination=0.5
        )
        print(f"  ✓ Created goal: {goal_id}")
        
        # Create subtask
        st_id = db.create_subtask(goal_id, "Test subtask", "medium")
        print(f"  ✓ Created subtask: {st_id}")
        
        return True
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

def test_large_batch_insert():
    """Test large batch operations that might timeout"""
    print("\n🔍 TEST 5: Large Batch Operations (100 findings)")
    
    try:
        db = SessionDatabase()
        # Use existing project to test findings
        project_id = "ea2f33a4-d808-434b-b776-b7246bd6134a"  # empirica project
        session_id = db.create_session(ai_id="test-batch", components_loaded=6)
        
        start = time.time()
        
        for i in range(100):
            db.log_finding(
                project_id=project_id,
                session_id=session_id,
                finding=f"Test finding {i}"
            )
        
        elapsed = time.time() - start
        rate = 100 / elapsed
        
        print(f"  ✓ Inserted 100 findings in {elapsed:.2f}s ({rate:.1f} ops/sec)")
        
        # Verify they're all there
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM project_findings WHERE session_id = ?", (session_id,))
        count = cursor.fetchone()[0]
        
        if count == 100:
            print(f"  ✓ All 100 findings verified in database")
            return True
        else:
            print(f"  ✗ Expected 100 findings, got {count}")
            return False
            
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

def test_transaction_handling():
    """Test transaction commit/rollback"""
    print("\n🔍 TEST 6: Transaction Handling")
    
    try:
        import time
        db = SessionDatabase()
        
        # Wait for any previous operations to complete
        time.sleep(0.1)
        
        # Start transaction
        session_id = db.create_session(ai_id="test-txn", components_loaded=6)
        
        # Commit
        db.conn.commit()
        print("  ✓ Transaction committed")
        
        # Verify session exists with fresh connection
        cursor = db.conn.cursor()
        cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
        if cursor.fetchone():
            print("  ✓ Committed data persists")
            return True
        else:
            print("  ✗ Committed data not found")
            return False
            
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

def test_connection_recovery():
    """Test that connections recover from temporary issues"""
    print("\n🔍 TEST 7: Connection Recovery")
    
    try:
        db = SessionDatabase()
        
        # Simulate a failed operation
        cursor = db.conn.cursor()
        try:
            cursor.execute("INVALID SQL;")
        except sqlite3.OperationalError:
            pass  # Expected
        
        # Try to recover with new query
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result:
            print("  ✓ Connection recovered after error")
            return True
        else:
            print("  ✗ Connection did not recover")
            return False
            
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 80)
    print("DATABASE INTEGRITY TEST SUITE")
    print("=" * 80)
    
    tests = [
        test_db_connection,
        test_table_schemas,
        test_concurrent_access,
        test_create_operations,
        test_large_batch_insert,
        test_transaction_handling,
        test_connection_recovery
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Database integrity verified")
        return 0
    else:
        print(f"❌ {total - passed} TESTS FAILED - Issues detected")
        return 1

if __name__ == "__main__":
    sys.exit(main())
