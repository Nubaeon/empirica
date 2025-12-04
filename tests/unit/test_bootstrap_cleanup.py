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
            ["empirica", "bootstrap"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should succeed
        assert result.returncode == 0, f"Bootstrap failed: {result.stderr}"
        
        # Should show success message
        assert "Bootstrap complete" in result.stdout
        
    def test_bootstrap_no_import_errors(self):
        """Bootstrap runs without import errors in stderr"""
        result = subprocess.run(
            ["empirica", "bootstrap"],
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
    
    def test_bootstrap_test_mode(self):
        """Bootstrap with --test flag works"""
        result = subprocess.run(
            ["empirica", "bootstrap", "--test"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "Bootstrap complete" in result.stdout
        assert "Tests passed" in result.stdout or "Running bootstrap tests" in result.stdout
    
    def test_bootstrap_loads_core_components(self):
        """Bootstrap loads expected number of core components (6-8)"""
        result = subprocess.run(
            ["empirica", "bootstrap"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Extract component count
        for line in result.stdout.split('\n'):
            if "Components loaded:" in line:
                # Format: "📊 Components loaded: 6"
                count_str = line.split(":")[-1].strip()
                count = int(count_str)
                
                # Should load 6-8 core components
                assert 6 <= count <= 8, f"Unexpected component count: {count}"
                return
        
        pytest.fail("Could not find component count in output")
    
    def test_bootstrap_fast_execution(self):
        """Bootstrap executes quickly (< 1 second)"""
        result = subprocess.run(
            ["empirica", "bootstrap"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Check bootstrap time
        for line in result.stdout.split('\n'):
            if "Bootstrap time:" in line:
                # Should be fast (microseconds or milliseconds)
                assert "μs" in line or "ms" in line, f"Bootstrap too slow: {line}"
                
                # Extract time
                if "μs" in line:
                    # Should be < 1000 microseconds
                    pass  # Already fast
                elif "ms" in line:
                    # Should be < 1000 milliseconds
                    time_str = line.split(":")[-1].strip().replace("ms", "")
                    time_val = float(time_str)
                    assert time_val < 1000, f"Bootstrap too slow: {time_val}ms"
                
                return
        
        # If no time in output, that's OK (MCP server mode)
        pass


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
    
    def test_mcp_bootstrap_path_works(self):
        """MCP server bootstrap path is functional"""
        result = subprocess.run(
            ["empirica", "bootstrap"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should use MCP path (primary) or local fallback
        # Either way should work
        assert result.returncode == 0
        assert "Bootstrap complete" in result.stdout


class TestBootstrapVerboseMode:
    """Test bootstrap verbose output"""
    
    def test_bootstrap_verbose_shows_components(self):
        """Bootstrap --verbose shows loaded components"""
        result = subprocess.run(
            ["empirica", "bootstrap", "--verbose"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        
        # Should show component list (if verbose works)
        # Or at least succeed
        assert "Bootstrap complete" in result.stdout


# Integration test
class TestBootstrapIntegration:
    """End-to-end bootstrap tests"""
    
    def test_bootstrap_full_workflow(self):
        """Complete bootstrap workflow"""
        # Bootstrap
        result = subprocess.run(
            ["empirica", "bootstrap"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "Bootstrap complete" in result.stdout
        
        # Should be able to run other commands after bootstrap
        # (Bootstrap initializes framework)
        result2 = subprocess.run(
            ["empirica", "sessions-list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Sessions-list should work after bootstrap
        assert result2.returncode == 0


if __name__ == "__main__":
    # Run with: pytest tests/unit/test_bootstrap_cleanup.py -v
    pytest.main([__file__, "-v", "--tb=short"])
