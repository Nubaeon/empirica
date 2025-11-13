"""Test Reflex Logger - external JSON logging."""

import json
import tempfile
import asyncio
from pathlib import Path
from datetime import date
from empirica.core.canonical.reflex_logger import ReflexLogger, log_assessment, log_assessment_sync
from empirica.core.canonical.reflex_frame import ReflexFrame, EpistemicAssessment, VectorState, Action


class TestReflexLogger:
    """Test Reflex Logger functionality."""
    
    def test_temporal_separation(self):
        """Test temporal separation - logs assessments externally to prevent recursion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create logger with temporary directory
            logger = ReflexLogger(base_log_dir=temp_dir)
            
            # Create a test assessment and frame
            assessment = EpistemicAssessment(
                engagement=VectorState(score=0.7, rationale="Test engagement"),
                engagement_gate_passed=True,
                know=VectorState(score=0.5, rationale="Test know"),
                do=VectorState(score=0.6, rationale="Test do"),
                context=VectorState(score=0.7, rationale="Test context"),
                foundation_confidence=0.6,
                clarity=VectorState(score=0.6, rationale="Test clarity"),
                coherence=VectorState(score=0.7, rationale="Test coherence"),
                signal=VectorState(score=0.6, rationale="Test signal"),
                density=VectorState(score=0.3, rationale="Test density"),
                comprehension_confidence=0.6,
                state=VectorState(score=0.5, rationale="Test state"),
                change=VectorState(score=0.7, rationale="Test change"),
                completion=VectorState(score=0.6, rationale="Test completion"),
                impact=VectorState(score=0.5, rationale="Test impact"),
                execution_confidence=0.6,
                uncertainty=VectorState(score=0.3, rationale="Test uncertainty"),
                overall_confidence=0.6,
                recommended_action=Action.PROCEED,
                assessment_id="test_id"
            )
            
            frame = ReflexFrame.from_assessment(
                assessment=assessment,
                frame_id="frame_123",
                task="Test task"
            )
            
            # Log the frame synchronously
            log_path = logger.log_frame_sync(frame, agent_id="test_agent")
            
            # Verify file was created
            assert log_path.exists()
            
            # Verify file contains frame data
            with open(log_path, 'r') as f:
                logged_data = json.load(f)
                assert logged_data['frameId'] == 'frame_123'
                assert logged_data['epistemicVector']['engagement'] == 0.7
                assert logged_data['epistemicVector']['know'] == 0.5
                assert logged_data['recommendedAction'] == 'proceed'
    
    def test_async_logging(self):
        """Test async file I/O works correctly."""
        import aiofiles
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ReflexLogger(base_log_dir=temp_dir)
            
            assessment = EpistemicAssessment(
                engagement=VectorState(score=0.8, rationale="Test engagement"),
                engagement_gate_passed=True,
                know=VectorState(score=0.7, rationale="Test know"),
                do=VectorState(score=0.8, rationale="Test do"),
                context=VectorState(score=0.8, rationale="Test context"),
                foundation_confidence=0.75,
                clarity=VectorState(score=0.8, rationale="Test clarity"),
                coherence=VectorState(score=0.9, rationale="Test coherence"),
                signal=VectorState(score=0.8, rationale="Test signal"),
                density=VectorState(score=0.2, rationale="Test density"),
                comprehension_confidence=0.75,
                state=VectorState(score=0.7, rationale="Test state"),
                change=VectorState(score=0.8, rationale="Test change"),
                completion=VectorState(score=0.8, rationale="Test completion"),
                impact=VectorState(score=0.7, rationale="Test impact"),
                execution_confidence=0.75,
                uncertainty=VectorState(score=0.2, rationale="Test uncertainty"),
                overall_confidence=0.75,
                recommended_action=Action.PROCEED,
                assessment_id="async_test_id"
            )
            
            frame = ReflexFrame.from_assessment(
                assessment=assessment,
                frame_id="async_frame_456",
                task="Async test task"
            )
            
            async def test_async_log():
                log_path = await logger.log_frame(frame, agent_id="test_agent")
                
                # Verify file was created
                assert log_path.exists()
                
                # Verify file content using aiofiles for async file operations
                async with aiofiles.open(log_path, 'r') as f:
                    content = await f.read()
                    logged_data = json.loads(content)
                    assert logged_data['frameId'] == 'async_frame_456'
                    assert logged_data['epistemicVector']['engagement'] == 0.8
                    assert logged_data['recommendedAction'] == 'proceed'
                
                return True
            
            # Run the async test
            result = asyncio.run(test_async_log())
            assert result is True
    
    def test_log_directory_structure(self):
        """Test log directory structure creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ReflexLogger(base_log_dir=temp_dir)
            
            # Create frame to trigger directory creation
            assessment = EpistemicAssessment(
                engagement=VectorState(score=0.7, rationale="Test"),
                engagement_gate_passed=True,
                know=VectorState(score=0.5, rationale="Test"),
                do=VectorState(score=0.6, rationale="Test"),
                context=VectorState(score=0.7, rationale="Test"),
                foundation_confidence=0.6,
                clarity=VectorState(score=0.6, rationale="Test"),
                coherence=VectorState(score=0.7, rationale="Test"),
                signal=VectorState(score=0.6, rationale="Test"),
                density=VectorState(score=0.3, rationale="Test"),
                comprehension_confidence=0.6,
                state=VectorState(score=0.5, rationale="Test"),
                change=VectorState(score=0.7, rationale="Test"),
                completion=VectorState(score=0.6, rationale="Test"),
                impact=VectorState(score=0.5, rationale="Test"),
                execution_confidence=0.6,
                uncertainty=VectorState(score=0.3, rationale="Test"),
                overall_confidence=0.6,
                recommended_action=Action.PROCEED,
                assessment_id="dir_test_id"
            )
            
            frame = ReflexFrame.from_assessment(
                assessment=assessment,
                frame_id="dir_frame_789",
                task="Dir test task"
            )
            
            log_path = logger.log_frame_sync(frame, agent_id="test_agent")
            
            # Verify directory structure: base_log_dir / agent_id / date / files
            expected_parts = ['test_agent', date.today().isoformat()]
            for part in expected_parts:
                assert part in str(log_path)
            
            # Verify directory exists
            assert log_path.parent.exists()
            assert log_path.parent.is_dir()
    
    def test_get_recent_frames(self):
        """Test retrieving recent frames."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ReflexLogger(base_log_dir=temp_dir)
            
            # Create multiple frames
            for i in range(5):
                assessment = EpistemicAssessment(
                    engagement=VectorState(score=0.7, rationale="Test engagement"),
                    engagement_gate_passed=True,
                    know=VectorState(score=0.5, rationale="Test know"),
                    do=VectorState(score=0.6, rationale="Test do"),
                    context=VectorState(score=0.7, rationale="Test context"),
                    foundation_confidence=0.6,
                    clarity=VectorState(score=0.6, rationale="Test clarity"),
                    coherence=VectorState(score=0.7, rationale="Test coherence"),
                    signal=VectorState(score=0.6, rationale="Test signal"),
                    density=VectorState(score=0.3, rationale="Test density"),
                    comprehension_confidence=0.6,
                    state=VectorState(score=0.5, rationale="Test state"),
                    change=VectorState(score=0.7, rationale="Test change"),
                    completion=VectorState(score=0.6, rationale="Test completion"),
                    impact=VectorState(score=0.5, rationale="Test impact"),
                    execution_confidence=0.6,
                    uncertainty=VectorState(score=0.3, rationale="Test uncertainty"),
                    overall_confidence=0.6,
                    recommended_action=Action.PROCEED,
                    assessment_id=f"recent_test_id_{i}"
                )
                
                frame = ReflexFrame.from_assessment(
                    assessment=assessment,
                    frame_id=f"recent_frame_{i}",
                    task="Recent test task"
                )
                
                logger.log_frame_sync(frame, agent_id="test_agent")
            
            # Get recent frames (sync version)
            recent_frames = logger.get_recent_frames_sync(
                agent_id="test_agent",
                limit=3
            )
            
            assert len(recent_frames) == 3
            
            # Verify the structure of retrieved frames
            for frame in recent_frames:
                assert 'frameId' in frame
                assert 'epistemicVector' in frame
                assert 'recommendedAction' in frame
    
    def test_get_recent_frames_async(self):
        """Test retrieving recent frames async."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ReflexLogger(base_log_dir=temp_dir)
            
            async def test_retrieve_frames():
                # Create multiple frames
                for i in range(3):
                    assessment = EpistemicAssessment(
                        engagement=VectorState(score=0.7, rationale="Test engagement"),
                        engagement_gate_passed=True,
                        know=VectorState(score=0.5, rationale="Test know"),
                        do=VectorState(score=0.6, rationale="Test do"),
                        context=VectorState(score=0.7, rationale="Test context"),
                        foundation_confidence=0.6,
                        clarity=VectorState(score=0.6, rationale="Test clarity"),
                        coherence=VectorState(score=0.7, rationale="Test coherence"),
                        signal=VectorState(score=0.6, rationale="Test signal"),
                        density=VectorState(score=0.3, rationale="Test density"),
                        comprehension_confidence=0.6,
                        state=VectorState(score=0.5, rationale="Test state"),
                        change=VectorState(score=0.7, rationale="Test change"),
                        completion=VectorState(score=0.6, rationale="Test completion"),
                        impact=VectorState(score=0.5, rationale="Test impact"),
                        execution_confidence=0.6,
                        uncertainty=VectorState(score=0.3, rationale="Test uncertainty"),
                        overall_confidence=0.6,
                        recommended_action=Action.PROCEED,
                        assessment_id=f"async_recent_test_id_{i}"
                    )
                    
                    frame = ReflexFrame.from_assessment(
                        assessment=assessment,
                        frame_id=f"async_recent_frame_{i}",
                        task="Async recent test task"
                    )
                    
                    await logger.log_frame(frame, agent_id="test_agent")
                
                # Get recent frames (async version)
                recent_frames = await logger.get_recent_frames(
                    agent_id="test_agent",
                    limit=2
                )
                
                assert len(recent_frames) == 2
                
                # Verify structure
                for frame in recent_frames:
                    assert 'frameId' in frame
                    assert 'epistemicVector' in frame
                    assert 'recommendedAction' in frame
                
                return True
            
            result = asyncio.run(test_retrieve_frames())
            assert result is True
    
    def test_get_frames_by_action(self):
        """Test retrieving frames filtered by action."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ReflexLogger(base_log_dir=temp_dir)
            
            # Create frames with different actions
            actions = [Action.PROCEED, Action.INVESTIGATE, Action.CLARIFY, Action.PROCEED, Action.RESET]
            
            for i, action in enumerate(actions):
                assessment = EpistemicAssessment(
                    engagement=VectorState(score=0.7, rationale="Test engagement"),
                    engagement_gate_passed=True,
                    know=VectorState(score=0.5, rationale="Test know"),
                    do=VectorState(score=0.6, rationale="Test do"),
                    context=VectorState(score=0.7, rationale="Test context"),
                    foundation_confidence=0.6,
                    clarity=VectorState(score=0.6, rationale="Test clarity"),
                    coherence=VectorState(score=0.7 if action != Action.RESET else 0.3, rationale="Test coherence"),
                    signal=VectorState(score=0.6, rationale="Test signal"),
                    density=VectorState(score=0.3, rationale="Test density"),
                    comprehension_confidence=0.6,
                    state=VectorState(score=0.5, rationale="Test state"),
                    change=VectorState(score=0.7 if action != Action.STOP else 0.3, rationale="Test change"),
                    completion=VectorState(score=0.6, rationale="Test completion"),
                    impact=VectorState(score=0.5, rationale="Test impact"),
                    execution_confidence=0.6,
                    uncertainty=VectorState(score=0.3, rationale="Test uncertainty"),
                    overall_confidence=0.6,
                    recommended_action=action,
                    assessment_id=f"action_test_id_{i}"
                )
                
                frame = ReflexFrame.from_assessment(
                    assessment=assessment,
                    frame_id=f"action_frame_{i}",
                    task="Action test task"
                )
                
                logger.log_frame_sync(frame, agent_id="test_agent")
            
            # Get frames with PROCEED action
            proceed_frames = logger.get_recent_frames_sync(
                agent_id="test_agent"
            )
            
            # Filter for PROCEED actions
            proceed_frames = [
                frame for frame in proceed_frames
                if frame.get('recommendedAction') == 'proceed'
            ]
            
            assert len(proceed_frames) >= 2  # Should have at least 2 PROCEED actions
    
    def test_convenience_functions(self):
        """Test convenience functions for logging assessments."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test async convenience function
            assessment = EpistemicAssessment(
                engagement=VectorState(score=0.75, rationale="Test engagement"),
                engagement_gate_passed=True,
                know=VectorState(score=0.6, rationale="Test know"),
                do=VectorState(score=0.7, rationale="Test do"),
                context=VectorState(score=0.75, rationale="Test context"),
                foundation_confidence=0.65,
                clarity=VectorState(score=0.7, rationale="Test clarity"),
                coherence=VectorState(score=0.8, rationale="Test coherence"),
                signal=VectorState(score=0.7, rationale="Test signal"),
                density=VectorState(score=0.25, rationale="Test density"),
                comprehension_confidence=0.7,
                state=VectorState(score=0.6, rationale="Test state"),
                change=VectorState(score=0.75, rationale="Test change"),
                completion=VectorState(score=0.7, rationale="Test completion"),
                impact=VectorState(score=0.6, rationale="Test impact"),
                execution_confidence=0.65,
                uncertainty=VectorState(score=0.25, rationale="Test uncertainty"),
                overall_confidence=0.65,
                recommended_action=Action.PROCEED,
                assessment_id="convenience_test_id"
            )
            
            async def test_convenience_log():
                log_path = await log_assessment(
                    assessment=assessment,
                    frame_id="convenience_frame_001",
                    task="Convenience test task",
                    context={"test": "context"},
                    agent_id="convenience_test_agent",
                    logger=ReflexLogger(base_log_dir=temp_dir)
                )
                
                # Verify file was created and contains the right data
                assert log_path.exists()
                
                with open(log_path, 'r') as f:
                    data = json.load(f)
                    assert data['frameId'] == 'convenience_frame_001'
                    assert data['epistemicVector']['engagement'] == 0.75
                    assert data['epistemicVector']['know'] == 0.6
                    assert data['recommendedAction'] == 'proceed'
                    assert data['task'] == 'Convenience test task'
                    assert data['context'] == {"test": "context"}
                
                return True
            
            result = asyncio.run(test_convenience_log())
            assert result is True
            
            # Test sync convenience function
            sync_log_path = log_assessment_sync(
                assessment=assessment,
                frame_id="convenience_frame_002",
                task="Sync convenience test task",
                context={"test": "sync_context"},
                agent_id="convenience_test_agent",
                logger=ReflexLogger(base_log_dir=temp_dir)
            )
            
            assert sync_log_path.exists()
            
            with open(sync_log_path, 'r') as f:
                data = json.load(f)
                assert data['frameId'] == 'convenience_frame_002'
                assert data['epistemicVector']['engagement'] == 0.75
                assert data['recommendedAction'] == 'proceed'
                assert data['task'] == 'Sync convenience test task'
                assert data['context'] == {"test": "sync_context"}