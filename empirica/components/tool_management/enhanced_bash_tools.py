"""
Enhanced Bash Tools - Inspired by Mini-Agent
Background process management for long-running investigations

Integrates with Empirica's investigation framework to handle long-running
processes (tests, builds, analysis) without blocking epistemic assessments.
"""

import subprocess
import time
import signal
import os
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProcessState(Enum):
    """State of a background process"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"
    UNKNOWN = "unknown"


@dataclass
class BashSession:
    """Represents a background bash session"""
    session_id: str
    command: str
    process: subprocess.Popen
    started_at: float
    output_lines: List[str] = field(default_factory=list)
    error_lines: List[str] = field(default_factory=list)
    exit_code: Optional[int] = None
    state: ProcessState = ProcessState.RUNNING


class EnhancedBashTools:
    """Bash tools with background process support for investigations"""
    
    def __init__(self):
        """Initialize enhanced bash tools"""
        self.sessions: Dict[str, BashSession] = {}
    
    def execute_background(
        self,
        command: str,
        session_id: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Execute command in background
        
        Useful for long-running investigations like:
        - pytest tests/ -v
        - make build
        - npm test
        - mypy . --check
        
        Args:
            command: Shell command to execute
            session_id: Unique identifier for this session
            cwd: Working directory (defaults to current)
            env: Environment variables (adds to current env)
            
        Returns:
            {
                'session_id': str,
                'started': bool,
                'pid': int,
                'command': str,
                'error': str (if failed)
            }
        """
        if session_id in self.sessions:
            return {
                'error': f"Session '{session_id}' already exists. Use kill_session() first or choose different ID.",
                'started': False,
                'session_id': session_id
            }
        
        try:
            # Prepare environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            # Start process
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                env=process_env,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            session = BashSession(
                session_id=session_id,
                command=command,
                process=process,
                started_at=time.time()
            )
            
            self.sessions[session_id] = session
            
            logger.info(f"Started background session '{session_id}': {command} (PID: {process.pid})")
            
            return {
                'session_id': session_id,
                'started': True,
                'pid': process.pid,
                'command': command
            }
            
        except Exception as e:
            logger.error(f"Failed to start background session '{session_id}': {e}")
            return {
                'error': f"Failed to start process: {str(e)}",
                'started': False,
                'session_id': session_id
            }
    
    def get_output(
        self, 
        session_id: str, 
        tail_lines: Optional[int] = 50,
        include_stderr: bool = True
    ) -> Dict:
        """
        Get output from background session
        
        Args:
            session_id: Session identifier
            tail_lines: Number of recent lines to return (None = all)
            include_stderr: Include stderr in output
            
        Returns:
            {
                'output': str,
                'stderr': str,
                'running': bool,
                'exit_code': Optional[int],
                'state': str,
                'runtime_seconds': float,
                'total_output_lines': int,
                'total_error_lines': int
            }
        """
        if session_id not in self.sessions:
            return {
                'error': f"Session '{session_id}' not found. Available: {list(self.sessions.keys())}",
                'running': False
            }
        
        session = self.sessions[session_id]
        process = session.process
        
        # Read available output (non-blocking)
        try:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                session.output_lines.append(line.rstrip())
        except Exception as e:
            logger.debug(f"Error reading stdout for '{session_id}': {e}")
        
        # Read available errors
        try:
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                session.error_lines.append(line.rstrip())
        except Exception as e:
            logger.debug(f"Error reading stderr for '{session_id}': {e}")
        
        # Check if still running
        exit_code = process.poll()
        running = exit_code is None
        
        if not running and session.exit_code is None:
            session.exit_code = exit_code
            session.state = ProcessState.COMPLETED if exit_code == 0 else ProcessState.FAILED
            logger.info(f"Session '{session_id}' completed with exit code {exit_code}")
        
        # Get tail lines
        output_lines = session.output_lines[-tail_lines:] if tail_lines else session.output_lines
        error_lines = session.error_lines[-tail_lines:] if tail_lines else session.error_lines
        
        runtime = time.time() - session.started_at
        
        result = {
            'output': '\n'.join(output_lines),
            'running': running,
            'exit_code': exit_code,
            'state': session.state.value,
            'runtime_seconds': runtime,
            'total_output_lines': len(session.output_lines),
            'total_error_lines': len(session.error_lines),
            'command': session.command
        }
        
        if include_stderr:
            result['stderr'] = '\n'.join(error_lines)
        
        return result
    
    def kill_session(self, session_id: str, force: bool = False) -> Dict:
        """
        Terminate background session
        
        Args:
            session_id: Session to terminate
            force: Use SIGKILL instead of SIGTERM
            
        Returns:
            {
                'killed': bool,
                'session_id': str,
                'exit_code': int,
                'runtime_seconds': float
            }
        """
        if session_id not in self.sessions:
            return {
                'error': f"Session '{session_id}' not found",
                'killed': False
            }
        
        session = self.sessions[session_id]
        process = session.process
        
        try:
            if force:
                process.kill()  # SIGKILL
                logger.info(f"Force killed session '{session_id}' (SIGKILL)")
            else:
                process.terminate()  # SIGTERM
                logger.info(f"Terminated session '{session_id}' (SIGTERM)")
            
            # Wait for process to exit
            try:
                exit_code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Session '{session_id}' did not exit after 5s, force killing")
                process.kill()
                exit_code = process.wait(timeout=2)
            
            runtime = time.time() - session.started_at
            session.exit_code = exit_code
            session.state = ProcessState.KILLED
            
            # Remove from active sessions
            del self.sessions[session_id]
            
            return {
                'killed': True,
                'session_id': session_id,
                'exit_code': exit_code,
                'runtime_seconds': runtime
            }
            
        except Exception as e:
            logger.error(f"Error killing session '{session_id}': {e}")
            return {
                'error': f"Failed to kill process: {str(e)}",
                'killed': False,
                'session_id': session_id
            }
    
    def list_sessions(self) -> Dict:
        """
        List all active background sessions
        
        Returns:
            {
                'sessions': [
                    {
                        'session_id': str,
                        'command': str,
                        'state': str,
                        'runtime_seconds': float,
                        'pid': int
                    }
                ],
                'count': int
            }
        """
        sessions_info = []
        
        for session_id, session in self.sessions.items():
            runtime = time.time() - session.started_at
            
            # Update state
            exit_code = session.process.poll()
            if exit_code is not None and session.exit_code is None:
                session.exit_code = exit_code
                session.state = ProcessState.COMPLETED if exit_code == 0 else ProcessState.FAILED
            
            sessions_info.append({
                'session_id': session_id,
                'command': session.command,
                'state': session.state.value,
                'runtime_seconds': runtime,
                'pid': session.process.pid,
                'exit_code': session.exit_code
            })
        
        return {
            'sessions': sessions_info,
            'count': len(sessions_info)
        }
    
    def wait_for_completion(
        self,
        session_id: str,
        timeout: Optional[float] = None,
        poll_interval: float = 1.0
    ) -> Dict:
        """
        Wait for session to complete
        
        Args:
            session_id: Session to wait for
            timeout: Maximum seconds to wait (None = forever)
            poll_interval: Seconds between checks
            
        Returns:
            Same as get_output(), plus 'timed_out': bool
        """
        if session_id not in self.sessions:
            return {
                'error': f"Session '{session_id}' not found",
                'timed_out': False
            }
        
        session = self.sessions[session_id]
        start_wait = time.time()
        
        while True:
            result = self.get_output(session_id)
            
            if not result['running']:
                result['timed_out'] = False
                return result
            
            if timeout and (time.time() - start_wait) > timeout:
                result['timed_out'] = True
                result['error'] = f"Timed out after {timeout}s"
                return result
            
            time.sleep(poll_interval)
    
    def cleanup_completed(self) -> Dict:
        """
        Remove completed sessions from memory
        
        Returns:
            {
                'cleaned': int,
                'remaining': int
            }
        """
        to_remove = []
        
        for session_id, session in self.sessions.items():
            if session.state in [ProcessState.COMPLETED, ProcessState.FAILED, ProcessState.KILLED]:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.sessions[session_id]
        
        return {
            'cleaned': len(to_remove),
            'remaining': len(self.sessions)
        }


# Example usage for investigations
if __name__ == "__main__":
    import sys
    
    bash = EnhancedBashTools()
    
    # Example 1: Run tests in background
    print("=== Example 1: Background Test Execution ===")
    result = bash.execute_background(
        command="sleep 3 && echo 'Tests passed!' && exit 0",
        session_id="test_run_1"
    )
    print(f"Started: {result['started']}, PID: {result.get('pid')}")
    
    # Check progress
    time.sleep(1)
    output = bash.get_output("test_run_1")
    print(f"After 1s - Running: {output['running']}, Output: {output['output']}")
    
    # Wait for completion
    final = bash.wait_for_completion("test_run_1")
    print(f"Completed - Exit Code: {final['exit_code']}, Output: {final['output']}")
    
    print("\n=== Example 2: List and Kill ===")
    bash.execute_background("sleep 100", "long_task")
    sessions = bash.list_sessions()
    print(f"Active sessions: {sessions['count']}")
    
    bash.kill_session("long_task")
    print("Killed long_task")
    
    bash.cleanup_completed()
    print("Cleaned up completed sessions")
