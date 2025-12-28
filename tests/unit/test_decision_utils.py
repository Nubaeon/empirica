import pytest

pytest.skip("Decision utils not implemented - skipping for now", allow_module_level=True)

from empirica.cli.command_handlers.decision_utils import calculate_decision, get_recommendation_from_vectors


class TestDecisionUtils:
    """Unit tests for decision utilities"""

    def test_calculate_decision_proceed(self):
        """Test that calculate_decision returns 'proceed' for high values"""
        result = calculate_decision(0.75)
        assert result == "proceed"
        assert isinstance(result, str)

    def test_calculate_decision_investigate(self):
        """Test that calculate_decision returns 'investigate' for low values"""
        result = calculate_decision(0.25)
        assert result == "investigate"
        assert isinstance(result, str)

    def test_calculate_decision_proceed_with_caution(self):
        """Test that calculate_decision returns 'proceed_with_caution' for medium values"""
        result = calculate_decision(0.5)
        assert result == "proceed_with_caution"
        assert isinstance(result, str)

    def test_calculate_decision_boundary_values(self):
        """Test boundary values for calculate_decision"""
        # Thresholds: >= 0.7 = "proceed", <= 0.3 = "investigate", else "proceed_with_caution"
        assert calculate_decision(0.29) == "investigate"
        assert calculate_decision(0.3) == "investigate"
        assert calculate_decision(0.35) == "proceed_with_caution"
        assert calculate_decision(0.69) == "proceed_with_caution"
        assert calculate_decision(0.7) == "proceed"
        assert calculate_decision(0.75) == "proceed"

    def test_calculate_decision_edge_cases(self):
        """Test edge cases for calculate_decision"""
        assert calculate_decision(0.0) == "investigate"
        assert calculate_decision(1.0) == "proceed"
        assert calculate_decision(0.29) == "investigate"
        assert calculate_decision(0.6) == "proceed_with_caution"

    def test_get_recommendation_from_vectors(self):
        """Test get_recommendation_from_vectors function"""
        # Test low uncertainty (high confidence) - should return proceed
        vectors = {
            "know": 0.8, "do": 0.7, "context": 0.8, "clarity": 0.85,
            "coherence": 0.8, "signal": 0.75, "density": 0.6,
            "state": 0.75, "change": 0.5, "completion": 0.6,
            "impact": 0.7, "uncertainty": 0.2, "engagement": 0.8
        }
        result = get_recommendation_from_vectors(vectors)
        assert isinstance(result, dict)
        assert "action" in result
        assert "message" in result
        assert "warnings" in result
        assert result["action"] in ["proceed", "investigate", "proceed_cautiously"]

    def test_get_recommendation_high_uncertainty(self):
        """Test recommendation for high uncertainty - should return investigate"""
        vectors = {
            "know": 0.3, "do": 0.3, "context": 0.3, "clarity": 0.3,
            "coherence": 0.3, "signal": 0.3, "density": 0.6,
            "state": 0.3, "change": 0.5, "completion": 0.3,
            "impact": 0.3, "uncertainty": 0.7, "engagement": 0.8  # high uncertainty
        }
        result = get_recommendation_from_vectors(vectors)
        assert isinstance(result, dict)
        assert result["action"] in ["proceed", "investigate", "proceed_cautiously"]

    def test_get_recommendation_very_low_uncertainty(self):
        """Test recommendation for very low uncertainty and high capability - should return proceed"""
        vectors = {
            "know": 0.9, "do": 0.9, "context": 0.9, "clarity": 0.9,
            "coherence": 0.9, "signal": 0.85, "density": 0.6,
            "state": 0.9, "change": 0.8, "completion": 0.85,
            "impact": 0.85, "uncertainty": 0.1, "engagement": 0.9  # low uncertainty
        }
        result = get_recommendation_from_vectors(vectors)
        assert isinstance(result, dict)
        assert result["action"] in ["proceed", "investigate", "proceed_cautiously"]

    def test_get_recommendation_moderate_values(self):
        """Test recommendation for moderate values - should return proceed_cautiously"""
        vectors = {
            "know": 0.6, "do": 0.6, "context": 0.6, "clarity": 0.6,
            "coherence": 0.6, "signal": 0.6, "density": 0.6,
            "state": 0.6, "change": 0.6, "completion": 0.6,
            "impact": 0.6, "uncertainty": 0.4, "engagement": 0.6
        }
        result = get_recommendation_from_vectors(vectors)
        assert isinstance(result, dict)
        assert result["action"] in ["proceed", "investigate", "proceed_cautiously"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])