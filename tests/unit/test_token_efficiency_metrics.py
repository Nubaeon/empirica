"""
Unit Tests for TokenEfficiencyMetrics

Tests token counting, efficiency comparison, and report generation.
"""

import pytest
import json
from pathlib import Path
from empirica.metrics.token_efficiency import TokenEfficiencyMetrics, TokenMeasurement


class TestTokenMeasurement:
    """Test token measurement recording"""
    
    @pytest.fixture
    def metrics(self, tmp_path):
        """Create metrics instance"""
        return TokenEfficiencyMetrics(
            session_id="test-session",
            storage_dir=str(tmp_path / ".empirica/metrics")
        )
    
    def test_measure_context_load(self, metrics):
        """Test measuring context load"""
        content = json.dumps({
            "session_id": "test",
            "vectors": {"know": 0.8, "do": 0.9},
            "phase": "PREFLIGHT"
        })
        
        measurement = metrics.measure_context_load(
            phase="PREFLIGHT",
            method="git",
            content=content,
            content_type="checkpoint"
        )
        
        assert isinstance(measurement, TokenMeasurement)
        assert measurement.phase == "PREFLIGHT"
        assert measurement.method == "git"
        assert measurement.tokens > 0
        assert measurement.content_type == "checkpoint"
    
    def test_multiple_measurements(self, metrics):
        """Test recording multiple measurements"""
        # Add PREFLIGHT measurement
        metrics.measure_context_load(
            phase="PREFLIGHT",
            method="git",
            content="test content " * 100
        )
        
        # Add CHECK measurement
        metrics.measure_context_load(
            phase="CHECK",
            method="git",
            content="check content " * 50
        )
        
        assert len(metrics.measurements) == 2


class TestTokenCounting:
    """Test token counting approximation"""
    
    @pytest.fixture
    def metrics(self, tmp_path):
        return TokenEfficiencyMetrics(
            session_id="test-session",
            storage_dir=str(tmp_path / ".empirica/metrics")
        )
    
    def test_token_counting_approximation(self, metrics):
        """Test simple token counting approximation"""
        # 10 words * 1.3 = 13 tokens
        text = "one two three four five six seven eight nine ten"
        count = metrics._count_tokens(text)
        
        assert count == 13  # 10 words * 1.3
    
    def test_token_counting_empty_string(self, metrics):
        """Test token counting for empty string"""
        count = metrics._count_tokens("")
        assert count == 0
    
    def test_token_counting_json(self, metrics):
        """Test token counting for JSON content"""
        checkpoint = {
            "session_id": "test",
            "phase": "PREFLIGHT",
            "vectors": {"know": 0.8, "do": 0.9}
        }
        
        json_text = json.dumps(checkpoint)
        count = metrics._count_tokens(json_text)
        
        # Should be reasonable (not 0, not huge)
        assert count > 0
        assert count < 100  # Small JSON


class TestPhaseAggregation:
    """Test phase-level token aggregation"""
    
    @pytest.fixture
    def metrics_with_data(self, tmp_path):
        """Create metrics with sample measurements"""
        metrics = TokenEfficiencyMetrics(
            session_id="test-session",
            storage_dir=str(tmp_path / ".empirica/metrics")
        )
        
        # Add measurements
        metrics.measure_context_load("PREFLIGHT", "git", "content " * 100)
        metrics.measure_context_load("PREFLIGHT", "git", "content " * 50)
        metrics.measure_context_load("CHECK", "git", "content " * 80)
        
        return metrics
    
    def test_get_phase_total(self, metrics_with_data):
        """Test getting total tokens for a phase"""
        preflight_total = metrics_with_data.get_phase_total("PREFLIGHT")
        check_total = metrics_with_data.get_phase_total("CHECK")
        
        assert preflight_total > 0
        assert check_total > 0
        assert preflight_total > check_total  # PREFLIGHT had 2 measurements
    
    def test_get_phase_total_with_method_filter(self, metrics_with_data):
        """Test filtering phase total by method"""
        # Add a prompt-based measurement
        metrics_with_data.measure_context_load("PREFLIGHT", "prompt", "content " * 500)
        
        git_total = metrics_with_data.get_phase_total("PREFLIGHT", method="git")
        prompt_total = metrics_with_data.get_phase_total("PREFLIGHT", method="prompt")
        
        assert git_total > 0
        assert prompt_total > 0
        assert prompt_total > git_total  # Prompt method should use more tokens


class TestEfficiencyComparison:
    """Test efficiency comparison and reporting"""
    
    @pytest.fixture
    def metrics(self, tmp_path):
        """Create metrics with git-based measurements"""
        metrics = TokenEfficiencyMetrics(
            session_id="test-session",
            storage_dir=str(tmp_path / ".empirica/metrics")
        )
        
        # Simulate git-based context loads (compressed)
        metrics.measure_context_load("PREFLIGHT", "git", "x " * 250)  # ~450 tokens
        metrics.measure_context_load("CHECK", "git", "x " * 220)      # ~400 tokens
        metrics.measure_context_load("ACT", "git", "x " * 280)        # ~500 tokens
        metrics.measure_context_load("POSTFLIGHT", "git", "x " * 470) # ~850 tokens
        
        return metrics
    
    def test_compare_efficiency(self, metrics):
        """Test efficiency comparison against baseline"""
        report = metrics.compare_efficiency()
        
        assert "session_id" in report
        assert "phases" in report
        assert "total" in report
        assert "success_criteria" in report
        
        # Verify per-phase metrics
        assert "PREFLIGHT" in report["phases"]
        assert "CHECK" in report["phases"]
        
        # Verify total metrics
        total = report["total"]
        assert "baseline_tokens" in total
        assert "actual_tokens" in total
        assert "reduction_percentage" in total
    
    def test_reduction_calculation(self, metrics):
        """Test token reduction calculation"""
        report = metrics.compare_efficiency()
        
        total = report["total"]
        
        # Baseline should be ~17,000 tokens (sum of baseline phases)
        assert total["baseline_tokens"] == 17000
        
        # Actual should be much less
        assert total["actual_tokens"] < total["baseline_tokens"]
        
        # Reduction percentage should be positive
        assert total["reduction_percentage"] > 0
    
    def test_cost_savings_calculation(self, metrics):
        """Test cost savings calculation"""
        report = metrics.compare_efficiency()
        
        total = report["total"]
        
        assert "baseline_cost_usd" in total
        assert "actual_cost_usd" in total
        assert "cost_savings_usd" in total
        
        # Cost savings should be positive
        assert total["cost_savings_usd"] > 0
        
        # Baseline cost should be higher than actual
        assert total["baseline_cost_usd"] > total["actual_cost_usd"]
    
    def test_success_criteria_validation(self, metrics):
        """Test success criteria validation"""
        report = metrics.compare_efficiency()
        
        criteria = report["success_criteria"]
        
        assert "target_reduction_pct" in criteria
        assert "achieved_reduction_pct" in criteria
        assert "target_met" in criteria
        
        assert criteria["target_reduction_pct"] == 80  # 80% target


class TestReportExport:
    """Test report export functionality"""
    
    @pytest.fixture
    def metrics_with_data(self, tmp_path):
        """Create metrics with sample data"""
        metrics = TokenEfficiencyMetrics(
            session_id="test-session",
            storage_dir=str(tmp_path / ".empirica/metrics")
        )
        
        metrics.measure_context_load("PREFLIGHT", "git", "x " * 250)
        metrics.measure_context_load("CHECK", "git", "x " * 220)
        
        return metrics
    
    def test_export_report_json(self, metrics_with_data):
        """Test JSON report export"""
        report_content = metrics_with_data.export_report(format="json")
        
        # Verify it's valid JSON
        report = json.loads(report_content)
        
        assert "session_id" in report
        assert "phases" in report
        assert "total" in report
    
    def test_export_report_markdown(self, metrics_with_data):
        """Test Markdown report export"""
        report_content = metrics_with_data.export_report(format="markdown")
        
        # Verify Markdown structure
        assert "# Token Efficiency Report" in report_content
        assert "## Summary" in report_content
        assert "## Per-Phase Breakdown" in report_content
        assert "| Phase |" in report_content  # Table header
    
    def test_export_report_csv(self, metrics_with_data):
        """Test CSV report export"""
        report_content = metrics_with_data.export_report(format="csv")
        
        # Verify CSV structure
        lines = report_content.split("\n")
        assert "phase,method,baseline_tokens" in lines[0]  # Header
        assert len(lines) > 2  # Header + data rows
    
    def test_export_report_to_file(self, metrics_with_data, tmp_path):
        """Test exporting report to file"""
        output_path = tmp_path / "report.json"
        
        metrics_with_data.export_report(
            format="json",
            output_path=str(output_path)
        )
        
        # Verify file was created
        assert output_path.exists()
        
        # Verify content is valid JSON
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert "session_id" in report


class TestPersistence:
    """Test metrics persistence"""
    
    @pytest.fixture
    def metrics(self, tmp_path):
        return TokenEfficiencyMetrics(
            session_id="test-session",
            storage_dir=str(tmp_path / ".empirica/metrics")
        )
    
    def test_save_measurements(self, metrics, tmp_path):
        """Test saving measurements to disk"""
        metrics.measure_context_load("PREFLIGHT", "git", "test content " * 100)
        metrics.measure_context_load("CHECK", "git", "test content " * 50)
        
        metrics.save_measurements()
        
        # Verify file was created
        metrics_file = tmp_path / ".empirica/metrics" / "metrics_test-session.json"
        assert metrics_file.exists()
        
        # Verify content
        with open(metrics_file, 'r') as f:
            data = json.load(f)
        
        assert data["session_id"] == "test-session"
        assert len(data["measurements"]) == 2
    
    def test_load_measurements(self, metrics, tmp_path):
        """Test loading measurements from disk"""
        # Save measurements
        metrics.measure_context_load("PREFLIGHT", "git", "test " * 100)
        metrics.save_measurements()
        
        # Create new metrics instance
        new_metrics = TokenEfficiencyMetrics(
            session_id="test-session",
            storage_dir=str(tmp_path / ".empirica/metrics")
        )
        
        # Load measurements
        success = new_metrics.load_measurements()
        
        assert success is True
        assert len(new_metrics.measurements) == 1
        assert new_metrics.measurements[0].phase == "PREFLIGHT"
    
    def test_load_measurements_returns_false_when_not_found(self, tmp_path):
        """Test load returns False when file doesn't exist"""
        metrics = TokenEfficiencyMetrics(
            session_id="nonexistent-session",
            storage_dir=str(tmp_path / ".empirica/metrics")
        )
        
        success = metrics.load_measurements()
        
        assert success is False
        assert len(metrics.measurements) == 0


class TestBaselineData:
    """Test baseline token counts"""
    
    def test_baseline_tokens_defined(self, tmp_path):
        """Test that baseline tokens are properly defined"""
        metrics = TokenEfficiencyMetrics(
            session_id="test-session",
            storage_dir=str(tmp_path / ".empirica/metrics")
        )
        
        # Verify baseline tokens for all phases
        assert metrics.baseline_tokens["PREFLIGHT"] == 6500
        assert metrics.baseline_tokens["CHECK"] == 3500
        assert metrics.baseline_tokens["ACT"] == 1500
        assert metrics.baseline_tokens["POSTFLIGHT"] == 5500
    
    def test_target_tokens_defined(self, tmp_path):
        """Test that target tokens are properly defined"""
        metrics = TokenEfficiencyMetrics(
            session_id="test-session",
            storage_dir=str(tmp_path / ".empirica/metrics")
        )
        
        # Verify target tokens for all phases
        assert metrics.target_tokens["PREFLIGHT"] == 450
        assert metrics.target_tokens["CHECK"] == 400
        assert metrics.target_tokens["ACT"] == 500
        assert metrics.target_tokens["POSTFLIGHT"] == 850


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
