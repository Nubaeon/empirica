"""
Integrity Test: NO HEURISTICS

This test validates the core principle of Empirica:
NO HEURISTICS. NO KEYWORD MATCHING. NO CONFABULATION.

All epistemic assessments must come from genuine AI self-assessment,
not from static values, rules, or keyword matching.
"""

import pytest
import ast
import inspect
from pathlib import Path
from typing import List, Tuple


@pytest.mark.integrity
class TestNoHeuristics:
    """Test suite to ensure no heuristics exist in codebase"""
    
    def test_no_static_baseline_values_in_canonical_assessor(self):
        """Ensure CanonicalEpistemicAssessor has no hardcoded vector scores"""
        from empirica.core.canonical import CanonicalEpistemicAssessor
        
        source = inspect.getsource(CanonicalEpistemicAssessor)
        
        # Check for suspicious static value patterns
        suspicious_patterns = [
            "'know': 0.",
            "'do': 0.",
            "'context': 0.",
            "'clarity': 0.",
            "'coherence': 0.",
            "'signal': 0.",
            "'density': 0.",
            "'state': 0.",
            "'change': 0.",
            "'completion': 0.",
            "'impact': 0.",
            "'engagement': 0.",
            "'uncertainty': 0.",
            '"know": 0.',
            '"do": 0.',
            '"context": 0.',
        ]
        
        for pattern in suspicious_patterns:
            assert pattern not in source, (
                f"Found suspicious static value pattern '{pattern}' in CanonicalEpistemicAssessor. "
                f"All vector scores must come from genuine LLM self-assessment."
            )
    
    def test_no_static_values_in_cli_commands(self):
        """Ensure CLI commands don't use static baseline values"""
        from empirica.cli.command_handlers import cascade_commands
        
        source = inspect.getsource(cascade_commands)
        
        # Check that there are no dictionaries with all 13 vectors set to static values
        # This would indicate a baseline being created without genuine assessment
        
        # Look for patterns like: vectors = { 'know': 0.5, 'do': 0.5, ... }
        lines = source.split('\n')
        
        suspicious_blocks = []
        in_suspect_block = False
        block_lines = []
        
        for line in lines:
            if 'vectors = {' in line or 'vectors={' in line:
                in_suspect_block = True
                block_lines = [line]
            elif in_suspect_block:
                block_lines.append(line)
                if '}' in line:
                    in_suspect_block = False
                    # Check if this block has static values
                    block_text = '\n'.join(block_lines)
                    if "'know':" in block_text and "'do':" in block_text:
                        # This looks like it might be defining all vectors
                        suspicious_blocks.append(block_text)
        
        # If we find suspicious blocks, they should only be in demo/test contexts
        for block in suspicious_blocks:
            # Allow in workflow demo mode (marked with "demo mode" comment)
            if "demo mode" not in block.lower() and "demonstration" not in block.lower():
                pytest.fail(
                    f"Found suspicious static vector definition in CLI commands:\n{block}\n\n"
                    f"All vector scores must come from genuine AI self-assessment via "
                    f"--assessment-json or parse_llm_response()."
                )
    
    def test_assessment_requires_llm_response_parsing(self):
        """Verify assessment functions require parsing LLM responses"""
        from empirica.core.canonical import CanonicalEpistemicAssessor
        
        # Check that assessor has parse_llm_response method
        assert hasattr(CanonicalEpistemicAssessor, 'parse_llm_response'), (
            "CanonicalEpistemicAssessor must have parse_llm_response method"
        )
        
        # Check that assess() method returns a prompt, not scores
        source = inspect.getsource(CanonicalEpistemicAssessor.assess)
        
        # The assess method should return something with 'self_assessment_prompt'
        assert 'self_assessment_prompt' in source.lower() or 'prompt' in source.lower(), (
            "assess() method should generate self-assessment prompts, not scores"
        )
    
    def test_no_keyword_matching_in_assessor(self):
        """Ensure no keyword-based scoring logic exists"""
        from empirica.core.canonical import CanonicalEpistemicAssessor
        
        source = inspect.getsource(CanonicalEpistemicAssessor)
        
        # Keywords that might indicate rule-based scoring
        forbidden_patterns = [
            'if "error" in',
            'if "fail" in',
            'if "success" in',
            'if "complete" in',
            '.count(',  # counting keywords
            're.search',  # regex pattern matching for scoring
            're.match',
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source, (
                f"Found forbidden pattern '{pattern}' in CanonicalEpistemicAssessor. "
                f"Assessment must not use keyword matching or rule-based heuristics."
            )
    
    def test_reflex_logger_stores_genuine_assessments(self):
        """Verify RefLex logger stores actual assessment data, not synthetic"""
        from empirica.core.canonical import ReflexLogger
        
        source = inspect.getsource(ReflexLogger)
        
        # Should not contain default/baseline score generation
        assert "'know': 0.5" not in source, (
            "ReflexLogger should store genuine assessments, not generate defaults"
        )
        
        assert "baseline" not in source.lower() or "genuine" in source.lower(), (
            "If 'baseline' is mentioned, it should be in context of genuine assessment"
        )


@pytest.mark.integrity
class TestGenuineAssessmentEnforcement:
    """Test that genuine assessment is properly enforced"""
    
    @pytest.mark.asyncio
    async def test_canonical_assessor_returns_prompt_not_scores(self):
        """Verify canonical assessor returns self-assessment prompt"""
        from empirica.core.canonical import CanonicalEpistemicAssessor
        
        assessor = CanonicalEpistemicAssessor(agent_id="test")
        result = await assessor.assess("test task", {})
        
        # Should return a dict with prompt, not scores
        assert isinstance(result, dict), "assess() should return dict"
        assert "self_assessment_prompt" in result, (
            "assess() must return self_assessment_prompt for AI to respond to"
        )
        assert "assessment_id" in result, "assess() must return assessment_id"
        
        # Should NOT contain vector scores directly
        assert "vectors" not in result, (
            "assess() should return prompt, not pre-computed vector scores"
        )
    
    def test_cli_preflight_requires_assessment_json(self):
        """Verify CLI preflight command requires genuine assessment"""
        from empirica.cli.command_handlers.cascade_commands import handle_preflight_command
        from argparse import Namespace
        import io
        import sys
        
        # Capture output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        args = Namespace(
            prompt="test task",
            session_id=None,
            assessment_json=None,  # No assessment provided
            json=False,
            compact=False,
            kv=False,
            quiet=True,  # Quiet mode should exit without assessment
            verbose=False
        )
        
        try:
            handle_preflight_command(args)
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        
        # In quiet mode without assessment_json, should indicate cannot proceed
        # (The actual behavior is to display prompt and exit, or request input)
        # This test verifies it doesn't just use static values
        assert "GENUINE SELF-ASSESSMENT" in output or "assessment" in output.lower(), (
            "CLI should require genuine assessment, not use static values"
        )


@pytest.mark.integrity
class TestCodebaseScanning:
    """Scan entire codebase for heuristic patterns"""
    
    def get_python_files(self) -> List[Path]:
        """Get all Python files in empirica/ and mcp_local/"""
        files = []
        for pattern in ["empirica/**/*.py", "mcp_local/**/*.py"]:
            files.extend(Path(".").glob(pattern))
        
        # Exclude test files and archive
        files = [
            f for f in files 
            if "_archive" not in str(f) 
            and "_dev" not in str(f)
            and "tests" not in str(f)
        ]
        
        return files
    
    def test_no_static_vector_dicts_in_codebase(self):
        """Scan entire codebase for suspicious static vector definitions"""
        files = self.get_python_files()
        
        violations: List[Tuple[Path, str]] = []
        
        for file_path in files:
            try:
                content = file_path.read_text()
                
                # Look for patterns like: {'know': 0.5, 'do': 0.5, ...}
                # This is a simple heuristic - could have false positives
                if "'know':" in content or '"know":' in content:
                    if "'do':" in content or '"do":' in content:
                        # Found potential vector dict - check if it's in an allowed context
                        
                        # Allowed contexts:
                        # - Test files (already excluded)
                        # - Mock/example data (should have "mock" or "example" nearby)
                        # - Demo mode (should have "demo" comment)
                        
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if ("'know':" in line or '"know":' in line) and \
                               ("'do':" in line or '"do":' in line or \
                                (i + 1 < len(lines) and ("'do':" in lines[i+1] or '"do":' in lines[i+1]))):
                                
                                # Check context (5 lines before and after)
                                context_start = max(0, i - 5)
                                context_end = min(len(lines), i + 6)
                                context = '\n'.join(lines[context_start:context_end])
                                
                                # Skip if in allowed context
                                if any(marker in context.lower() for marker in [
                                    "mock", "example", "test", "demo", "sample", "fixture"
                                ]):
                                    continue
                                
                                violations.append((file_path, context))
            except Exception as e:
                # Skip files we can't read
                continue
        
        if violations:
            violation_report = "\n\n".join([
                f"File: {path}\nContext:\n{context}"
                for path, context in violations
            ])
            pytest.fail(
                f"Found {len(violations)} suspicious static vector definitions:\n\n"
                f"{violation_report}\n\n"
                f"All vector scores must come from genuine AI self-assessment."
            )
    
    def test_no_confabulation_keywords(self):
        """Check for keywords that might indicate confabulated assessments"""
        files = self.get_python_files()
        
        # Keywords that might indicate fake/confabulated assessment logic
        forbidden_keywords = [
            "fake_assessment",
            "confabulate",
            "simulate_assessment",
            "generate_baseline",
            "default_vectors",
        ]
        
        violations = []
        
        for file_path in files:
            try:
                content = file_path.read_text()
                for keyword in forbidden_keywords:
                    if keyword in content:
                        violations.append((file_path, keyword))
            except:
                continue
        
        if violations:
            violation_report = "\n".join([
                f"  {path}: found '{keyword}'"
                for path, keyword in violations
            ])
            pytest.fail(
                f"Found confabulation keywords in codebase:\n{violation_report}\n\n"
                f"Empirica must use genuine AI self-assessment only."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
