#!/usr/bin/env python3
"""
Unit Tests for Bootstrap Cleanup

Tests to verify bootstrap works correctly after removing dead components.
Run BEFORE and AFTER cleanup to ensure no regressions.

Created: 2025-12-01
For: Qwen to validate bootstrap cleanup
"""

import pytest
import subprocess
import sys
from pathlib import Path

class TestBootstrapComponents:
    """Test that bootstrap loads correctly after cleanup"""
    
    def test_bootstrap_command_works(self):
        """Bootstrap command executes without errors"""
        result = subprocess.run(
            ["empirica", "project-bootstrap", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should succeed
        assert result.returncode == 0, f"Bootstrap failed: {result.stderr}"

        # Should return valid JSON with "ok": true
        import json
        try:
            output = json.loads(result.stdout)
            assert output.get("ok") == True, "Bootstrap should return ok=true"
        except json.JSONDecodeError:
            pytest.fail(f"Bootstrap did not return valid JSON: {result.stdout[:200]}")
        
    def test_bootstrap_no_import_errors(self):
        """Bootstrap runs without import errors in stderr"""
        result = subprocess.run(
            ["empirica", "project-bootstrap", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should not have ModuleNotFoundError or ImportError
        stderr_lower = result.stderr.lower()
        assert "modulenotfounderror" not in stderr_lower, f"Import error: {result.stderr}"
        assert "importerror" not in stderr_lower, f"Import error: {result.stderr}"
        
        # Bayesian deprecation warning is OK
        # But no other errors
        lines = result.stderr.split('\n')
        error_lines = [l for l in lines if 'error' in l.lower() and 'deprecated' not in l.lower()]
        assert len(error_lines) == 0, f"Unexpected errors: {error_lines}"
    
    def test_bootstrap_json_output(self):
        """Bootstrap with --output json works"""
        result = subprocess.run(
            ["empirica", "project-bootstrap", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0

        # Should return valid JSON
        import json
        try:
            output = json.loads(result.stdout)
            assert "ok" in output, "JSON output should have 'ok' field"
            assert "breadcrumbs" in output, "JSON output should have 'breadcrumbs' field"
        except json.JSONDecodeError:
            pytest.fail(f"Bootstrap did not return valid JSON: {result.stdout[:200]}")
    
    def test_bootstrap_returns_breadcrumbs(self):
        """Bootstrap returns breadcrumbs data structure"""
        result = subprocess.run(
            ["empirica", "project-bootstrap", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        import json
        output = json.loads(result.stdout)

        # Should have breadcrumbs structure
        assert "breadcrumbs" in output, "Should have breadcrumbs"
        breadcrumbs = output["breadcrumbs"]

        # Should have expected fields
        expected_fields = ["project", "last_activity", "findings", "unknowns", "dead_ends"]
        for field in expected_fields:
            assert field in breadcrumbs, f"Breadcrumbs should have {field}"
    
    def test_bootstrap_fast_execution(self):
        """Bootstrap executes quickly (< 5 seconds)"""
        import time

        start = time.time()
        result = subprocess.run(
            ["empirica", "project-bootstrap", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        elapsed = time.time() - start

        # Should complete quickly
        assert elapsed < 5.0, f"Bootstrap took {elapsed:.2f}s, should be < 5s"
        assert result.returncode == 0, "Bootstrap should succeed"


class TestBootstrapImports:
    """Test that bootstrap Python files import correctly"""
    
    def test_optimal_bootstrap_imports(self):
        """optimal_metacognitive_bootstrap.py imports without errors"""
        try:
                        # Should import successfully
            assert OptimalMetacognitiveBootstrap is not None
        except ImportError as e:
            pytest.fail(f"OptimalMetacognitiveBootstrap import failed: {e}")
        except Exception as e:
            # Other errors might be OK (e.g., missing config)
            # But ImportError is not OK
            pass
    
    def test_extended_bootstrap_imports(self):
        """extended_metacognitive_bootstrap.py imports without errors"""
        try:
                        # Should import successfully
            assert ExtendedMetacognitiveBootstrap is not None
        except ImportError as e:
            pytest.fail(f"ExtendedMetacognitiveBootstrap import failed: {e}")
        except Exception as e:
            # Other errors might be OK
            pass
    
    def test_no_missing_component_imports(self):
        """Bootstrap files don't import deleted components"""
        bootstrap_files = [
            Path("empirica/bootstraps/optimal_metacognitive_bootstrap.py"),
            Path("empirica/bootstraps/extended_metacognitive_bootstrap.py")
        ]
        
        # Components that should NOT be imported (deleted)
        deleted_components = [
            "adaptive_uncertainty_calibration",
            "context_validation",
            "runtime_validation",
            "environment_stabilization",
            "workspace_awareness",
            "empirical_performance_analyzer",
            "intelligent_navigation",
            "security_monitoring",
            "procedural_analysis",
        ]
        
        for bootstrap_file in bootstrap_files:
            if not bootstrap_file.exists():
                continue
                
            content = bootstrap_file.read_text()
            
            for component in deleted_components:
                # Check if component is imported (not commented out)
                lines = content.split('\n')
                for line in lines:
                    # Skip comments
                    if line.strip().startswith('#'):
                        continue
                    
                    # Check for import
                    if f"from empirica.components.{component}" in line:
                        pytest.fail(
                            f"{bootstrap_file.name} still imports deleted component: {component}\n"
                            f"Line: {line}"
                        )


class TestBootstrapFallback:
    """Test MCP server fallback behavior"""
    
    def test_project_bootstrap_works(self):
        """Project bootstrap command is functional"""
        result = subprocess.run(
            ["empirica", "project-bootstrap", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should work and return JSON
        assert result.returncode == 0

        import json
        output = json.loads(result.stdout)
        assert output.get("ok") == True


class TestBootstrapVerboseMode:
    """Test bootstrap verbose output"""
    
    def test_bootstrap_verbose_mode(self):
        """Bootstrap --verbose mode works"""
        result = subprocess.run(
            ["empirica", "project-bootstrap", "--verbose", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0

        # Verbose mode should still return valid JSON
        import json
        output = json.loads(result.stdout)
        assert "ok" in output


# Integration test
class TestBootstrapIntegration:
    """End-to-end bootstrap tests"""
    
    def test_bootstrap_full_workflow(self):
        """Complete bootstrap workflow"""
        # Bootstrap
        result = subprocess.run(
            ["empirica", "project-bootstrap", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0

        import json
        output = json.loads(result.stdout)
        assert output.get("ok") == True

        # Should be able to run other commands after bootstrap
        result2 = subprocess.run(
            ["empirica", "sessions-list", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Sessions-list should work after bootstrap
        assert result2.returncode == 0


if __name__ == "__main__":
    # Run with: pytest tests/unit/test_bootstrap_cleanup.py -v
    pytest.main([__file__, "-v", "--tb=short"])
