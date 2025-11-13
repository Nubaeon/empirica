#!/usr/bin/env python3
"""
Adaptive Uncertainty Calibration System - Core Implementation
Self-calibrating empirical grounding with KNOW-DO-CONTEXT framework
"""

import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy
import os

class UQVector(Enum):
    """Simplified 3-vector uncertainty framework"""
    KNOW = "know"        # Knowledge certainty - what we know vs don't know
    DO = "do"           # Capability confidence - can we execute effectively
    CONTEXT = "context" # Environmental validity - is our context accurate

@dataclass
class CalibrationResult:
    """Result from uncertainty calibration assessment"""
    vectors: Dict[UQVector, float]
    implicit_confidence: float
    calibrated_confidence: float
    uvl_color: str
    decision: str  # ACT, CHECK, INVESTIGATE
    calibration_id: str
    timestamp: float = field(default_factory=time.time)

@dataclass
class FeedbackOutcome:
    """Feedback structure for calibration learning"""
    accuracy: float  # 0-1 how accurate was the prediction
    task_success: bool
    human_correction: bool
    execution_quality: float  # 0-1
    semantic_notes: Optional[str] = None

class UVLProtocol:
    """UVL (Uncertainty Visualization Language) Protocol"""
    
    @staticmethod
    def color_for_uncertainty(uncertainty: float) -> str:
        """Map uncertainty to UVL color"""
        if uncertainty < 0.2:
            return '🟢'  # Green - confident
        elif uncertainty < 0.6:
            return '🟡'  # Yellow - moderate uncertainty
        else:
            return '🔴'  # Red - high uncertainty
    
    @staticmethod
    def render_uvl_state(vectors: Dict[UQVector, float], node_emoji: str = '🤖') -> str:
        """Render UVL visualization for current state"""
        max_uncertainty = max(vectors.values())
        node_color = UVLProtocol.color_for_uncertainty(max_uncertainty)
        
        uvl_output = f"""
{node_emoji}{node_color} Metacognitive State:
├─ KNOW: {vectors[UQVector.KNOW]:.2f} {UVLProtocol.color_for_uncertainty(vectors[UQVector.KNOW])}
├─ DO: {vectors[UQVector.DO]:.2f} {UVLProtocol.color_for_uncertainty(vectors[UQVector.DO])}
└─ CONTEXT: {vectors[UQVector.CONTEXT]:.2f} {UVLProtocol.color_for_uncertainty(vectors[UQVector.CONTEXT])}
"""
        return uvl_output.strip()
    
    @staticmethod
    def emit_uvl(message: str):
        """Emit UVL message (for tmux integration)"""
        # This will be enhanced with actual tmux integration
        print(f"[UVL] {message}")

class AdaptiveUncertaintyCalibration:
    """Self-calibrating uncertainty system with empirical feedback loops"""
    
    def __init__(self, calibration_id: str = "default"):
        self.calibration_id = calibration_id
        self.vectors = [UQVector.KNOW, UQVector.DO, UQVector.CONTEXT]
        
        # Calibration weights (learned over time)
        self.weights = {
            UQVector.KNOW: {
                'epistemic_depth': 1.0,
                'freshness': 1.0, 
                'coverage': 1.0
            },
            UQVector.DO: {
                'tool_confidence': 1.0,
                'execution_history': 1.0,
                'capability_match': 1.0
            },
            UQVector.CONTEXT: {
                'state_validity': 1.0,
                'environment_stability': 1.0,
                'info_integrity': 1.0
            }
        }
        
        # Performance tracking
        self.calibration_log = []
        self.response_count = 0
        self.predictions = {}  # Store predictions for feedback
        
        # Safety bounds
        self.MAX_ADJUSTMENT = 0.10  # 10% max change per cycle
        self.MIN_WEIGHT = 0.3       # Never go below 30%
        self.MAX_WEIGHT = 2.0       # Never exceed 200%
        
        # Load existing calibration if available
        self._load_calibration_state()
    
    def assess_uncertainty(self, decision_context: Dict[str, Any]) -> CalibrationResult:
        """Generate calibrated uncertainty assessment with UVL visualization"""
        
        # Get implicit confidence (simulated neural confidence)
        implicit_confidence = self._get_implicit_confidence(decision_context)
        
        # Structured uncertainty assessment
        raw_vectors = {
            UQVector.KNOW: self._assess_knowledge(decision_context),
            UQVector.DO: self._assess_capability(decision_context), 
            UQVector.CONTEXT: self._assess_environment(decision_context)
        }
        
        # Apply learned calibration weights
        calibrated_vectors = self._apply_calibration(raw_vectors)
        
        # Generate calibrated confidence
        calibrated_confidence = 1.0 - max(calibrated_vectors.values())
        
        # Determine decision based on uncertainty
        decision = self._determine_action(calibrated_vectors)
        
        # UVL visualization
        uvl_color = UVLProtocol.color_for_uncertainty(max(calibrated_vectors.values()))
        
        # Create result (convert enum keys to strings for consistency)
        calibration_id = self._generate_prediction_id()
        vectors_as_strings = {vector.value: uncertainty for vector, uncertainty in calibrated_vectors.items()}
        
        result = CalibrationResult(
            vectors=vectors_as_strings,
            implicit_confidence=implicit_confidence,
            calibrated_confidence=calibrated_confidence,
            uvl_color=uvl_color,
            decision=decision,
            calibration_id=calibration_id
        )
        
        # Store prediction for feedback
        self.predictions[calibration_id] = {
            'result': result,
            'context': decision_context,
            'timestamp': time.time()
        }
        
        # UVL output (use enum keys for UVL rendering)
        UVLProtocol.emit_uvl(UVLProtocol.render_uvl_state(calibrated_vectors))
        UVLProtocol.emit_uvl(f"→ Decision: {decision} (confidence: {calibrated_confidence:.2f})")
        
        return result
    
    def receive_feedback(self, prediction_id: str, outcome: FeedbackOutcome):
        """Receive empirical feedback for calibration learning"""
        if prediction_id not in self.predictions:
            return
        
        self.response_count += 1
        
        # Log feedback (convert dataclass to dict for JSON serialization)
        feedback_entry = {
            'prediction_id': prediction_id,
            'outcome': {
                'accuracy': outcome.accuracy,
                'task_success': outcome.task_success,
                'human_correction': outcome.human_correction,
                'execution_quality': outcome.execution_quality,
                'semantic_notes': outcome.semantic_notes
            },
            'timestamp': time.time(),
            'response_count': self.response_count
        }
        self.calibration_log.append(feedback_entry)
        
        # Light calibration check (every response)
        self._light_calibration_check(prediction_id, outcome)
        
        # Medium recalibration (every 25 responses)
        if self.response_count % 25 == 0:
            self._medium_recalibration()
        
        # Save state
        self._save_calibration_state()
    
    def _assess_knowledge(self, context: Dict[str, Any]) -> float:
        """Assess KNOW vector - knowledge certainty"""
        task = context.get('task', '')
        available_info = context.get('available_info', [])
        domain = context.get('domain', 'general')
        
        # Base uncertainty
        uncertainty = 0.5
        
        # Reduce uncertainty if we have domain knowledge
        if domain in ['python', 'programming', 'analysis']:
            uncertainty -= 0.2
        
        # Reduce uncertainty if we have specific information
        info_confidence = min(len(available_info) * 0.1, 0.3)
        uncertainty -= info_confidence
        
        # Increase uncertainty for complex/research tasks
        complex_indicators = ['research', 'novel', 'experimental', 'unknown']
        if any(word in task.lower() for word in complex_indicators):
            uncertainty += 0.3
        
        return max(0.0, min(1.0, uncertainty))
    
    def _assess_capability(self, context: Dict[str, Any]) -> float:
        """Assess DO vector - capability confidence"""
        task = context.get('task', '')
        tools_available = context.get('tools_available', [])
        execution_history = context.get('execution_history', {})
        
        # Base uncertainty
        uncertainty = 0.4
        
        # Reduce uncertainty if we have relevant tools
        if tools_available:
            tool_confidence = min(len(tools_available) * 0.05, 0.2)
            uncertainty -= tool_confidence
        
        # Reduce uncertainty based on execution history
        if execution_history.get('success_rate', 0) > 0.8:
            uncertainty -= 0.2
        
        # Increase uncertainty for new/complex operations
        complex_ops = ['deploy', 'migrate', 'refactor', 'architecture']
        if any(op in task.lower() for op in complex_ops):
            uncertainty += 0.2
        
        return max(0.0, min(1.0, uncertainty))
    
    def _assess_environment(self, context: Dict[str, Any]) -> float:
        """Assess CONTEXT vector - environmental validity"""
        workspace_state = context.get('workspace_state', {})
        environment_type = context.get('environment', 'development')
        context_age = context.get('context_age_seconds', 0)
        
        # Base uncertainty
        uncertainty = 0.3
        
        # Increase uncertainty for stale context
        if context_age > 3600:  # 1 hour
            uncertainty += 0.2
        
        # Increase uncertainty for production environments
        if environment_type == 'production':
            uncertainty += 0.3
        
        # Reduce uncertainty for stable workspace
        if workspace_state.get('is_clean', False):
            uncertainty -= 0.1
        
        # Increase uncertainty for unstable workspace
        if workspace_state.get('has_errors', False):
            uncertainty += 0.2
        
        return max(0.0, min(1.0, uncertainty))
    
    def _get_implicit_confidence(self, context: Dict[str, Any]) -> float:
        """Simulate implicit neural confidence"""
        # This would be replaced with actual model confidence in practice
        task_complexity = len(context.get('task', '').split()) / 20.0
        return max(0.1, min(0.9, 0.7 - task_complexity))
    
    def _apply_calibration(self, raw_vectors: Dict[UQVector, float]) -> Dict[UQVector, float]:
        """Apply learned calibration weights"""
        calibrated = {}
        
        for vector, uncertainty in raw_vectors.items():
            # Get weighted factors
            factors = self.weights[vector]
            avg_weight = sum(factors.values()) / len(factors)
            
            # Apply calibration (weight influences the uncertainty)
            calibrated_uncertainty = uncertainty * avg_weight
            calibrated[vector] = max(0.0, min(1.0, calibrated_uncertainty))
        
        return calibrated
    
    def _determine_action(self, vectors: Dict[UQVector, float]) -> str:
        """Determine action based on uncertainty vectors"""
        max_uncertainty = max(vectors.values())
        avg_uncertainty = sum(vectors.values()) / len(vectors)
        
        if max_uncertainty < 0.2:
            return "ACT"
        elif max_uncertainty < 0.6 or avg_uncertainty < 0.4:
            return "CHECK"
        else:
            return "INVESTIGATE"
    
    def _light_calibration_check(self, prediction_id: str, outcome: FeedbackOutcome):
        """Quick discrepancy detection"""
        prediction = self.predictions[prediction_id]
        predicted_confidence = prediction['result'].calibrated_confidence
        actual_accuracy = outcome.accuracy
        
        # Expected: high confidence → high accuracy
        discrepancy = abs(predicted_confidence - actual_accuracy)
        
        if discrepancy > 0.3:  # Significant mismatch
            self.calibration_log.append({
                'type': 'discrepancy',
                'predicted_confidence': predicted_confidence,
                'actual_accuracy': actual_accuracy,
                'vector_breakdown': prediction['result'].vectors,
                'timestamp': time.time()
            })
            
            UVLProtocol.emit_uvl(f"🔄💭 Calibration flag: confidence {predicted_confidence:.2f} vs accuracy {actual_accuracy:.2f}")
    
    def _medium_recalibration(self):
        """Adjust weights based on recent performance"""
        recent_logs = [log for log in self.calibration_log if log.get('type') == 'discrepancy'][-25:]
        
        if not recent_logs:
            return
        
        # Simple weight adjustment based on discrepancies
        for vector in self.vectors:
            # If this vector had high uncertainty but good outcomes, increase its weight
            # If this vector had low uncertainty but poor outcomes, decrease its weight
            
            vector_performance = self._analyze_vector_performance(vector, recent_logs)
            
            for factor in self.weights[vector]:
                current_weight = self.weights[vector][factor]
                
                if vector_performance > 0.7:  # Good predictor
                    adjustment = min(current_weight * 0.1, self.MAX_ADJUSTMENT)
                    new_weight = min(current_weight + adjustment, self.MAX_WEIGHT)
                elif vector_performance < 0.3:  # Poor predictor
                    adjustment = min(current_weight * 0.1, self.MAX_ADJUSTMENT)
                    new_weight = max(current_weight - adjustment, self.MIN_WEIGHT)
                else:
                    new_weight = current_weight
                
                self.weights[vector][factor] = new_weight
        
        UVLProtocol.emit_uvl(f"⚙💭 Recalibrated weights after {self.response_count} responses")
    
    def _analyze_vector_performance(self, vector: UQVector, logs: List[Dict]) -> float:
        """Analyze how well a vector predicted outcomes"""
        if not logs:
            return 0.5
        
        # Simple heuristic: if vector had high uncertainty and outcome was poor, that's good prediction
        # If vector had low uncertainty and outcome was good, that's also good prediction
        correct_predictions = 0
        
        for log in logs:
            vector_uncertainty = log['vector_breakdown'].get(vector, 0.5)
            actual_accuracy = log['actual_accuracy']
            
            # Good prediction if high uncertainty predicted low accuracy or vice versa
            if (vector_uncertainty > 0.5 and actual_accuracy < 0.5) or \
               (vector_uncertainty < 0.5 and actual_accuracy > 0.5):
                correct_predictions += 1
        
        return correct_predictions / len(logs) if logs else 0.5
    
    def _generate_prediction_id(self) -> str:
        """Generate unique prediction ID"""
        return hashlib.md5(f"{self.calibration_id}_{time.time()}_{self.response_count}".encode()).hexdigest()[:12]
    
    def _save_calibration_state(self):
        """Save calibration state to disk"""
        # Convert enum keys to strings for JSON serialization
        weights_serializable = {
            vector.value: weights for vector, weights in self.weights.items()
        }
        
        state = {
            'weights': weights_serializable,
            'response_count': self.response_count,
            'calibration_log': self.calibration_log[-100:],  # Keep last 100 entries
            'last_updated': time.time()
        }
        
        calibration_dir = os.path.expanduser("~/.empirica/calibration")
        os.makedirs(calibration_dir, exist_ok=True)
        
        state_file = os.path.join(calibration_dir, f"{self.calibration_id}.json")
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _load_calibration_state(self):
        """Load existing calibration state"""
        calibration_dir = os.path.expanduser("~/.empirica/calibration")
        state_file = os.path.join(calibration_dir, f"{self.calibration_id}.json")
        
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Convert string keys back to enum keys
                loaded_weights = state.get('weights', {})
                if loaded_weights:
                    converted_weights = {}
                    for vector_str, weights in loaded_weights.items():
                        # Find matching enum
                        for vector_enum in UQVector:
                            if vector_enum.value == vector_str:
                                converted_weights[vector_enum] = weights
                                break
                    self.weights = converted_weights if converted_weights else self.weights
                
                self.response_count = state.get('response_count', 0)
                self.calibration_log = state.get('calibration_log', [])
                
                UVLProtocol.emit_uvl(f"📊 Loaded calibration state: {self.response_count} responses")
            except Exception as e:
                UVLProtocol.emit_uvl(f"⚠️ Failed to load calibration state: {e}")
    
    def get_calibration_status(self) -> Dict[str, Any]:
        """Get current calibration status for monitoring"""
        recent_accuracy = self._calculate_recent_accuracy()
        
        return {
            'calibration_id': self.calibration_id,
            'response_count': self.response_count,
            'weights': self.weights,
            'recent_accuracy': recent_accuracy,
            'next_recalibration': 25 - (self.response_count % 25),
            'last_updated': time.time()
        }
    
    def _calculate_recent_accuracy(self) -> float:
        """Calculate recent prediction accuracy"""
        recent_feedback = [log for log in self.calibration_log[-25:] 
                          if 'outcome' in log and hasattr(log['outcome'], 'accuracy')]
        
        if not recent_feedback:
            return 0.5
        
        total_accuracy = sum(log['outcome'].accuracy for log in recent_feedback)
        return total_accuracy / len(recent_feedback)

# CLI Integration Functions
def create_default_calibrator() -> AdaptiveUncertaintyCalibration:
    """Create default calibrator instance for CLI usage"""
    return AdaptiveUncertaintyCalibration("empirica_default")

def assess_task_uncertainty(task: str, context: Dict[str, Any] = None) -> CalibrationResult:
    """Convenience function for CLI uncertainty assessment"""
    calibrator = create_default_calibrator()
    
    decision_context = {
        'task': task,
        'context': context or {},
        'timestamp': time.time()
    }
    
    return calibrator.assess_uncertainty(decision_context)

# Convenience function for easy import
def assess_uncertainty(decision_context: str) -> CalibrationResult:
    """Convenience function for uncertainty assessment"""
    return assess_task_uncertainty(decision_context)