"""Test Canonical Epistemic Assessor - LLM reasoning only."""

import asyncio
import json
import pytest
from empirica.core.canonical.canonical_epistemic_assessment import CanonicalEpistemicAssessor, Action
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema
EpistemicAssessment = EpistemicAssessmentSchema  # Alias for backwards compat
from empirica.core.canonical.reflex_frame import VectorState, ENGAGEMENT_THRESHOLD


class TestCanonicalEpistemicAssessor:
    """Test Canonical Epistemic Assessor functionality."""
    
    def test_llm_assessment(self):
        """Verify genuine LLM reasoning, not heuristics."""
        assessor = CanonicalEpistemicAssessor()
        
        # The assess method should return a dictionary with self-assessment prompt
        async def test_assess():
            result = await assessor.assess("Test task", {"test": "context"})
            return result
        
        result = asyncio.run(test_assess())
        
        assert isinstance(result, dict)
        assert 'self_assessment_prompt' in result
        assert 'assessment_id' in result
        assert 'requires_self_assessment' in result
        assert result['requires_self_assessment'] is True
        
        # The prompt should be structured for genuine LLM self-assessment
        prompt = result['self_assessment_prompt']
        assert "You are performing a metacognitive self-assessment" in prompt
        assert "GENUINE reasoning" in prompt
        assert "not heuristics" in prompt.lower()
        assert "Use genuine reasoning" in prompt
        
        # Should return a structured JSON format in the prompt
        assert "structured JSON" in prompt
        assert '"engagement": {' in prompt
        assert '"foundation": {' in prompt
    
    def test_meta_prompt_generation(self):
        """Test that meta-prompt generation returns proper self-assessment prompt."""
        assessor = CanonicalEpistemicAssessor()
        
        task = "Refactor authentication module"
        context = {
            'cwd': '/test/path',
            'available_tools': ['read', 'write'],
            'domain': 'security'
        }
        
        async def test_assess():
            result = await assessor.assess(task, context)
            return result
        
        result = asyncio.run(test_assess())
        prompt = result['self_assessment_prompt']
        
        # Should include task in prompt
        assert task in prompt
        
        # Should include context in prompt
        assert "Working Directory: /test/path" in prompt
        assert "Available Tools: read, write" in prompt
        assert "Domain: security" in prompt
        
        # Should have 12-vector structure
        assert "GATE: ENGAGEMENT" in prompt
        assert "TIER 0: FOUNDATION" in prompt
        assert "TIER 1: COMPREHENSION" in prompt
        assert "TIER 2: EXECUTION" in prompt
        assert "META-EPISTEMIC" in prompt  # Check for the broader term
    
    def test_json_parsing(self):
        """Test parsing structured assessment correctly."""
        assessor = CanonicalEpistemicAssessor()
        
        # Sample LLM response JSON
        llm_response = {
            "engagement": {
                "score": 0.8,
                "rationale": "High engagement with collaborative task",
                "evidence": "Active participation in task"
            },
            "foundation": {
                "know": {
                    "score": 0.7,
                    "rationale": "Good knowledge of security domain",
                    "evidence": "Security background"
                },
                "do": {
                    "score": 0.8,
                    "rationale": "Capable of refactoring tasks",
                    "evidence": "Experience with refactoring"
                },
                "context": {
                    "score": 0.6,
                    "rationale": "Context is mostly clear",
                    "evidence": "Documentation provided"
                }
            },
            "comprehension": {
                "clarity": {
                    "score": 0.7,
                    "rationale": "Task is clearly defined",
                    "evidence": "Clear requirements"
                },
                "coherence": {
                    "score": 0.8,
                    "rationale": "Aligns with previous discussion",
                    "evidence": "Consistent with project goals"
                },
                "signal": {
                    "score": 0.7,
                    "rationale": "Main priorities are clear",
                    "evidence": "Clear success criteria"
                },
                "density": {
                    "score": 0.4,
                    "rationale": "Not overly complex",
                    "evidence": "Well-structured codebase"
                }
            },
            "execution": {
                "state": {
                    "score": 0.7,
                    "rationale": "Clear understanding of current state",
                    "evidence": "Codebase well understood"
                },
                "change": {
                    "score": 0.8,
                    "rationale": "Clear change tracking",
                    "evidence": "Good version control"
                },
                "completion": {
                    "score": 0.7,
                    "rationale": "Clear completion criteria",
                    "evidence": "Defined requirements"
                },
                "impact": {
                    "score": 0.8,
                    "rationale": "Impact well understood",
                    "evidence": "Risk assessment performed"
                }
            },
            "uncertainty": {
                "score": 0.2,
                "rationale": "Low uncertainty about approach",
                "evidence": "Clear plan established"
            }
        }
        
        assessment = assessor.parse_llm_response(
            llm_response=llm_response,
            assessment_id="test_123",
            task="Test task"
        )
        
        # Verify assessment structure
        assert isinstance(assessment, EpistemicAssessment)
        assert assessment.assessment_id == "test_123"
        assert assessment.task == "Test task"
        
        # Verify individual vector values
        assert assessment.engagement.score == 0.8
        assert assessment.engagement.rationale == "High engagement with collaborative task"
        assert assessment.engagement_gate_passed is True  # 0.8 >= 0.6 threshold
        
        # Verify engagement gate calculation
        assert assessment.engagement_gate_passed == (assessment.engagement.score >= ENGAGEMENT_THRESHOLD)
        
        # Verify foundation vectors
        assert assessment.know.score == 0.7
        assert assessment.do.score == 0.8
        assert assessment.context.score == 0.6
        
        # Verify comprehension vectors
        assert assessment.clarity.score == 0.7
        assert assessment.coherence.score == 0.8
        assert assessment.signal.score == 0.7
        assert assessment.density.score == 0.4
        
        # Verify execution vectors
        assert assessment.state.score == 0.7
        assert assessment.change.score == 0.8
        assert assessment.completion.score == 0.7
        assert assessment.impact.score == 0.8
        
        # Verify uncertainty
        assert assessment.uncertainty.score == 0.2
        
        # Verify computed confidences
        assert assessment.foundation_confidence == pytest.approx(0.7, abs=0.01)
        assert assessment.comprehension_confidence == pytest.approx(0.7, abs=0.01)
        assert assessment.execution_confidence == pytest.approx(0.75, abs=0.01)
    
    def test_json_parsing_with_string_response(self):
        """Test parsing JSON from string response."""
        assessor = CanonicalEpistemicAssessor()
        
        llm_response = json.dumps({
            "engagement": {
                "score": 0.7,
                "rationale": "Test engagement",
                "evidence": "Test evidence"
            },
            "foundation": {
                "know": {
                    "score": 0.5,
                    "rationale": "Test know",
                    "evidence": "Test evidence"
                },
                "do": {
                    "score": 0.6,
                    "rationale": "Test do",
                    "evidence": "Test evidence"
                },
                "context": {
                    "score": 0.7,
                    "rationale": "Test context",
                    "evidence": "Test evidence"
                }
            },
            "comprehension": {
                "clarity": {
                    "score": 0.6,
                    "rationale": "Test clarity",
                    "evidence": "Test evidence"
                },
                "coherence": {
                    "score": 0.7,
                    "rationale": "Test coherence",
                    "evidence": "Test evidence"
                },
                "signal": {
                    "score": 0.6,
                    "rationale": "Test signal",
                    "evidence": "Test evidence"
                },
                "density": {
                    "score": 0.3,
                    "rationale": "Test density",
                    "evidence": "Test evidence"
                }
            },
            "execution": {
                "state": {
                    "score": 0.6,
                    "rationale": "Test state",
                    "evidence": "Test evidence"
                },
                "change": {
                    "score": 0.7,
                    "rationale": "Test change",
                    "evidence": "Test evidence"
                },
                "completion": {
                    "score": 0.6,
                    "rationale": "Test completion",
                    "evidence": "Test evidence"
                },
                "impact": {
                    "score": 0.7,
                    "rationale": "Test impact",
                    "evidence": "Test evidence"
                }
            },
            "uncertainty": {
                "score": 0.3,
                "rationale": "Test uncertainty",
                "evidence": "Test evidence"
            }
        })
        
        assessment = assessor.parse_llm_response(
            llm_response=llm_response,
            assessment_id="test_string_123",
            task="Test task"
        )
        
        assert assessment.assessment_id == "test_string_123"
        assert assessment.engagement.score == 0.7
        assert assessment.know.score == 0.5
    
    def test_json_parsing_with_markdown_block(self):
        """Test parsing JSON from markdown code block."""
        assessor = CanonicalEpistemicAssessor()
        
        llm_response = """
```json
{
    "engagement": {
        "score": 0.9,
        "rationale": "High engagement in collaborative task",
        "evidence": "Active participation"
    },
    "foundation": {
        "know": {
            "score": 0.8,
            "rationale": "Strong domain knowledge",
            "evidence": "Relevant experience"
        },
        "do": {
            "score": 0.7,
            "rationale": "Capable execution",
            "evidence": "Previous success"
        },
        "context": {
            "score": 0.8,
            "rationale": "Good context understanding",
            "evidence": "Clear requirements"
        }
    },
    "comprehension": {
        "clarity": {
            "score": 0.8,
            "rationale": "Task is clear",
            "evidence": "Well defined"
        },
        "coherence": {
            "score": 0.9,
            "rationale": "High coherence",
            "evidence": "Consistent context"
        },
        "signal": {
            "score": 0.8,
            "rationale": "Clear signal",
            "evidence": "Prioritized information"
        },
        "density": {
            "score": 0.2,
            "rationale": "Low cognitive load",
            "evidence": "Simple task"
        }
    },
    "execution": {
        "state": {
            "score": 0.8,
            "rationale": "Good state awareness",
            "evidence": "Clear starting point"
        },
        "change": {
            "score": 0.9,
            "rationale": "Good change tracking",
            "evidence": "Version control available"
        },
        "completion": {
            "score": 0.8,
            "rationale": "Clear completion criteria",
            "evidence": "Defined goals"
        },
        "impact": {
            "score": 0.9,
            "rationale": "Clear impact understanding",
            "evidence": "Risk assessment done"
        }
    },
    "uncertainty": {
        "score": 0.1,
        "rationale": "Low uncertainty",
        "evidence": "Clear plan"
    }
}
```
"""
        
        assessment = assessor.parse_llm_response(
            llm_response=llm_response,
            assessment_id="test_markdown_123",
            task="Test task"
        )
        
        assert assessment.assessment_id == "test_markdown_123"
        assert assessment.engagement.score == 0.9
        assert assessment.know.score == 0.8
        assert assessment.uncertainty.score == 0.1
    
    def test_engagement_gate_logic(self):
        """Test engagement gate logic."""
        assessor = CanonicalEpistemicAssessor()
        
        # Test high engagement (should pass)
        high_engagement_response = {
            "engagement": {
                "score": 0.7,
                "rationale": "High engagement",
                "evidence": "Active participation"
            },
            "foundation": {
                "know": {"score": 0.5, "rationale": "Test", "evidence": "Test"},
                "do": {"score": 0.5, "rationale": "Test", "evidence": "Test"},
                "context": {"score": 0.5, "rationale": "Test", "evidence": "Test"}
            },
            "comprehension": {
                "clarity": {"score": 0.6, "rationale": "Test", "evidence": "Test"},
                "coherence": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "signal": {"score": 0.6, "rationale": "Test", "evidence": "Test"},
                "density": {"score": 0.3, "rationale": "Test", "evidence": "Test"}
            },
            "execution": {
                "state": {"score": 0.5, "rationale": "Test", "evidence": "Test"},
                "change": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "completion": {"score": 0.6, "rationale": "Test", "evidence": "Test"},
                "impact": {"score": 0.5, "rationale": "Test", "evidence": "Test"}
            },
            "uncertainty": {
                "score": 0.3,
                "rationale": "Test uncertainty",
                "evidence": "Test evidence"
            }
        }
        
        assessment = assessor.parse_llm_response(
            llm_response=high_engagement_response,
            assessment_id="test_high_engagement",
            task="Test task"
        )
        
        assert assessment.engagement_gate_passed is True
        assert assessment.recommended_action != Action.CLARIFY  # Should not be blocked by engagement gate
        
        # Test low engagement (should not pass)
        low_engagement_response = {
            "engagement": {
                "score": 0.5,
                "rationale": "Low engagement",
                "evidence": "Passive participation"
            },
            "foundation": {
                "know": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "do": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "context": {"score": 0.8, "rationale": "Test", "evidence": "Test"}
            },
            "comprehension": {
                "clarity": {"score": 0.9, "rationale": "Test", "evidence": "Test"},
                "coherence": {"score": 0.9, "rationale": "Test", "evidence": "Test"},
                "signal": {"score": 0.9, "rationale": "Test", "evidence": "Test"},
                "density": {"score": 0.1, "rationale": "Test", "evidence": "Test"}
            },
            "execution": {
                "state": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "change": {"score": 0.9, "rationale": "Test", "evidence": "Test"},
                "completion": {"score": 0.9, "rationale": "Test", "evidence": "Test"},
                "impact": {"score": 0.8, "rationale": "Test", "evidence": "Test"}
            },
            "uncertainty": {
                "score": 0.1,
                "rationale": "Low uncertainty",
                "evidence": "Clear understanding"
            }
        }
        
        assessment = assessor.parse_llm_response(
            llm_response=low_engagement_response,
            assessment_id="test_low_engagement",
            task="Test task"
        )
        
        assert assessment.engagement_gate_passed is False
        assert assessment.recommended_action == Action.CLARIFY  # Should be blocked by engagement gate
    
    def test_action_determination(self):
        """Test action determination logic."""
        assessor = CanonicalEpistemicAssessor()
        
        # Test PROCEED action (high confidence)
        high_confidence_response = {
            "engagement": {
                "score": 0.8,
                "rationale": "High engagement",
                "evidence": "Active participation"
            },
            "foundation": {
                "know": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "do": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "context": {"score": 0.8, "rationale": "Test", "evidence": "Test"}
            },
            "comprehension": {
                "clarity": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "coherence": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "signal": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "density": {"score": 0.2, "rationale": "Test", "evidence": "Test"}
            },
            "execution": {
                "state": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "change": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "completion": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "impact": {"score": 0.8, "rationale": "Test", "evidence": "Test"}
            },
            "uncertainty": {
                "score": 0.1,
                "rationale": "Low uncertainty",
                "evidence": "Clear understanding"
            }
        }
        
        assessment = assessor.parse_llm_response(
            llm_response=high_confidence_response,
            assessment_id="test_proceed",
            task="Test task"
        )
        
        assert assessment.recommended_action == Action.PROCEED
    
    def test_action_determination_for_investigate(self):
        """Test action determination for INVESTIGATE."""
        assessor = CanonicalEpistemicAssessor()
        
        # Test INVESTIGATE due to high uncertainty
        high_uncertainty_response = {
            "engagement": {
                "score": 0.8,
                "rationale": "High engagement",
                "evidence": "Active participation"
            },
            "foundation": {
                "know": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "do": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "context": {"score": 0.7, "rationale": "Test", "evidence": "Test"}
            },
            "comprehension": {
                "clarity": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "coherence": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "signal": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "density": {"score": 0.3, "rationale": "Test", "evidence": "Test"}
            },
            "execution": {
                "state": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "change": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "completion": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "impact": {"score": 0.7, "rationale": "Test", "evidence": "Test"}
            },
            "uncertainty": {
                "score": 0.9,  # High uncertainty
                "rationale": "High uncertainty about approach",
                "evidence": "Several unknown factors"
            }
        }
        
        assessment = assessor.parse_llm_response(
            llm_response=high_uncertainty_response,
            assessment_id="test_investigate",
            task="Test task"
        )
        
        assert assessment.recommended_action == Action.INVESTIGATE
    
    def test_action_determination_for_reset(self):
        """Test action determination for RESET."""
        assessor = CanonicalEpistemicAssessor()
        
        # Test RESET due to low coherence
        low_coherence_response = {
            "engagement": {
                "score": 0.8,
                "rationale": "High engagement",
                "evidence": "Active participation"
            },
            "foundation": {
                "know": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "do": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "context": {"score": 0.7, "rationale": "Test", "evidence": "Test"}
            },
            "comprehension": {
                "clarity": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "coherence": {"score": 0.3, "rationale": "Low coherence", "evidence": "Inconsistent context"},  # Below threshold
                "signal": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "density": {"score": 0.3, "rationale": "Test", "evidence": "Test"}
            },
            "execution": {
                "state": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "change": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "completion": {"score": 0.7, "rationale": "Test", "evidence": "Test"},
                "impact": {"score": 0.7, "rationale": "Test", "evidence": "Test"}
            },
            "uncertainty": {
                "score": 0.3,
                "rationale": "Moderate uncertainty",
                "evidence": "Some unknowns"
            }
        }
        
        assessment = assessor.parse_llm_response(
            llm_response=low_coherence_response,
            assessment_id="test_reset",
            task="Test task"
        )
        
        assert assessment.recommended_action == Action.RESET