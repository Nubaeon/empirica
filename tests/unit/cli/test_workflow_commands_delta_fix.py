"""
Unit tests for workflow_commands delta calculation fix

Tests that the postflight delta calculation correctly handles both:
- Simple float format: {"engagement": 0.95}
- Nested dict format: {"engagement": {"score": 0.95, "rationale": "..."}}
"""

import pytest
from empirica.cli.command_handlers.workflow_commands import _extract_numeric_value


class TestExtractNumericValue:
    """Test the _extract_numeric_value helper function"""

    def test_simple_float(self):
        """Should extract simple float values"""
        assert _extract_numeric_value(0.85) == 0.85
        assert _extract_numeric_value(0.5) == 0.5
        assert _extract_numeric_value(1.0) == 1.0
        assert _extract_numeric_value(0) == 0.0

    def test_simple_int(self):
        """Should convert int to float"""
        assert _extract_numeric_value(1) == 1.0
        assert _extract_numeric_value(0) == 0.0

    def test_nested_dict_with_score(self):
        """Should extract 'score' from nested dict (VectorAssessment format)"""
        nested = {
            "score": 0.95,
            "rationale": "High engagement with collaborative work",
            "evidence": "Multiple user clarifications incorporated"
        }
        assert _extract_numeric_value(nested) == 0.95

        nested2 = {
            "score": 0.7,
            "rationale": "Moderate knowledge"
        }
        assert _extract_numeric_value(nested2) == 0.7

    def test_nested_dict_without_score(self):
        """Should fallback to any numeric value if 'score' not present"""
        # This shouldn't normally happen, but we handle it gracefully
        nested = {"value": 0.8}
        assert _extract_numeric_value(nested) == 0.8

    def test_invalid_inputs(self):
        """Should return None for invalid inputs"""
        assert _extract_numeric_value(None) is None
        assert _extract_numeric_value("string") is None
        assert _extract_numeric_value({}) is None
        assert _extract_numeric_value({"text": "no numbers"}) is None
        assert _extract_numeric_value([]) is None
        assert _extract_numeric_value([0.5]) is None  # List not supported


class TestDeltaCalculation:
    """Test that delta calculation works with both vector formats"""

    def test_delta_simple_format(self):
        """Delta calculation with simple float format (current working case)"""
        preflight = {
            "engagement": 0.90,
            "know": 0.65,
            "do": 0.80,
            "uncertainty": 0.25
        }

        postflight = {
            "engagement": 0.95,
            "know": 0.85,
            "do": 0.90,
            "uncertainty": 0.15
        }

        deltas = {}
        for key in postflight:
            if key in preflight:
                post_val = _extract_numeric_value(postflight[key])
                pre_val = _extract_numeric_value(preflight[key])
                if post_val is not None and pre_val is not None:
                    deltas[key] = post_val - pre_val

        assert abs(deltas["engagement"] - 0.05) < 0.001
        assert abs(deltas["know"] - 0.20) < 0.001
        assert abs(deltas["do"] - 0.10) < 0.001
        assert abs(deltas["uncertainty"] - (-0.10)) < 0.001

    def test_delta_nested_format(self):
        """Delta calculation with nested dict format (was causing the error)"""
        preflight = {
            "engagement": 0.90,
            "know": 0.65,
            "do": 0.80,
            "uncertainty": 0.25
        }

        # This format was causing: "unsupported operand type(s) for -: 'dict' and 'float'"
        postflight = {
            "engagement": {
                "score": 0.95,
                "rationale": "Highly collaborative session with iterative clarification"
            },
            "know": {
                "score": 0.85,
                "rationale": "Deep implementation knowledge from hands-on work"
            },
            "do": {
                "score": 0.90,
                "rationale": "Successful delivery with all tests passing"
            },
            "uncertainty": {
                "score": 0.15,
                "rationale": "Low uncertainty after schema verification"
            }
        }

        deltas = {}
        for key in postflight:
            if key in preflight:
                post_val = _extract_numeric_value(postflight[key])
                pre_val = _extract_numeric_value(preflight[key])
                if post_val is not None and pre_val is not None:
                    deltas[key] = post_val - pre_val

        # Should calculate deltas without error
        assert abs(deltas["engagement"] - 0.05) < 0.001
        assert abs(deltas["know"] - 0.20) < 0.001
        assert abs(deltas["do"] - 0.10) < 0.001
        assert abs(deltas["uncertainty"] - (-0.10)) < 0.001

    def test_delta_mixed_format(self):
        """Delta calculation with mixed formats (some nested, some simple)"""
        preflight = {
            "engagement": 0.90,
            "know": 0.65,
            "do": 0.80,
            "uncertainty": 0.25
        }

        # Mixed: some simple floats, some nested dicts
        postflight = {
            "engagement": 0.95,  # Simple
            "know": {"score": 0.85, "rationale": "Deep knowledge"},  # Nested
            "do": 0.90,  # Simple
            "uncertainty": {"score": 0.15}  # Nested (minimal)
        }

        deltas = {}
        for key in postflight:
            if key in preflight:
                post_val = _extract_numeric_value(postflight[key])
                pre_val = _extract_numeric_value(preflight[key])
                if post_val is not None and pre_val is not None:
                    deltas[key] = post_val - pre_val

        assert abs(deltas["engagement"] - 0.05) < 0.001
        assert abs(deltas["know"] - 0.20) < 0.001
        assert abs(deltas["do"] - 0.10) < 0.001
        assert abs(deltas["uncertainty"] - (-0.10)) < 0.001

    def test_delta_with_missing_keys(self):
        """Delta calculation should skip missing keys gracefully"""
        preflight = {
            "engagement": 0.90,
            "know": 0.65
        }

        postflight = {
            "engagement": 0.95,
            "know": 0.85,
            "do": 0.90,  # New key not in preflight
            "uncertainty": 0.15  # New key not in preflight
        }

        deltas = {}
        for key in postflight:
            if key in preflight:
                post_val = _extract_numeric_value(postflight[key])
                pre_val = _extract_numeric_value(preflight[key])
                if post_val is not None and pre_val is not None:
                    deltas[key] = post_val - pre_val

        # Should only calculate deltas for keys present in both
        assert "engagement" in deltas
        assert "know" in deltas
        assert "do" not in deltas
        assert "uncertainty" not in deltas
        assert len(deltas) == 2


class TestRegressionForOriginalError:
    """Regression test for the original error: 'unsupported operand type(s) for -: dict and float'"""

    def test_original_error_scenario(self):
        """
        Reproduce and verify fix for the original error scenario.

        The error occurred when:
        1. PREFLIGHT was submitted with simple floats: {"engagement": 0.90}
        2. POSTFLIGHT was submitted with nested dicts: {"engagement": {"score": 0.95, ...}}
        3. Delta calculation tried: {"score": 0.95, ...} - 0.90  → TypeError
        """
        # PREFLIGHT format (simple floats)
        preflight_vectors = {
            "engagement": 0.90,
            "know": 0.65,
            "do": 0.80,
            "context": 0.75,
            "clarity": 0.70,
            "coherence": 0.85,
            "signal": 0.80,
            "density": 0.55,
            "state": 0.70,
            "change": 0.75,
            "completion": 0.60,
            "impact": 0.75,
            "uncertainty": 0.25
        }

        # POSTFLIGHT format (nested dicts - this caused the error)
        postflight_vectors = {
            "engagement": {
                "score": 0.95,
                "rationale": "Highly collaborative",
                "evidence": "Multiple user clarifications"
            },
            "know": {
                "score": 0.85,
                "rationale": "Deep implementation knowledge"
            },
            # ... (abbreviated for brevity)
        }

        # This should NOT raise: TypeError: unsupported operand type(s) for -: 'dict' and 'float'
        deltas = {}
        for key in postflight_vectors:
            if key in preflight_vectors:
                post_val = _extract_numeric_value(postflight_vectors[key])
                pre_val = _extract_numeric_value(preflight_vectors[key])
                if post_val is not None and pre_val is not None:
                    deltas[key] = post_val - pre_val

        # Verify deltas calculated correctly
        assert abs(deltas["engagement"] - 0.05) < 0.001
        assert abs(deltas["know"] - 0.20) < 0.001
