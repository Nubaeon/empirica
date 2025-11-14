#!/usr/bin/env python3
"""
Session JSON Handler - Export SQLite data to AI-readable JSON format

Provides:
- Session exports (complete session with all cascades)
- Cascade graph exports (flow visualization)
- Previous session context loading (session continuity)
- Compact summaries for AI consumption

Pattern: SQLite is source of truth, JSON files are exports/cache
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from empirica.data.session_database import SessionDatabase

logger = logging.getLogger(__name__)

class SessionJSONHandler:
    """Manages JSON exports and caching from SQLite database"""
    
    def __init__(self, export_dir: Optional[str] = None):
        if export_dir is None:
            # Default to .empirica/exports/
            base_dir = Path(__file__).parent.parent / '.empirica' / 'exports'
            export_dir = base_dir
        
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"JSON Handler initialized: {self.export_dir}")
    
    def export_session(self, db: SessionDatabase, session_id: str) -> Path:
        """Export complete session to JSON file"""
        session = db.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        cascades = db.get_session_cascades(session_id)
        
        # Build complete session structure
        session_data = {
            'session_id': session['session_id'],
            'ai_id': session['ai_id'],
            'user_id': session['user_id'],
            'start_time': session['start_time'],
            'end_time': session['end_time'],
            'bootstrap_level': session['bootstrap_level'],
            'components_loaded': session['components_loaded'],
            'statistics': {
                'total_turns': session['total_turns'],
                'total_cascades': session['total_cascades'],
                'avg_confidence': session['avg_confidence'],
                'drift_detected': bool(session['drift_detected'])
            },
            'cascades': []
        }
        
        # Add each cascade with full details
        for cascade in cascades:
            cascade_data = {
                'cascade_id': cascade['cascade_id'],
                'task': cascade['task'],
                'context': json.loads(cascade['context_json']) if cascade['context_json'] else {},
                'phases': {
                    'preflight': bool(cascade.get('preflight_completed', 0)),
                    'think': bool(cascade['think_completed']),
                    'plan': bool(cascade.get('plan_completed', 0)),
                    'investigate': bool(cascade['investigate_completed']),
                    'check': bool(cascade['check_completed']),
                    'act': bool(cascade['act_completed']),
                    'postflight': bool(cascade.get('postflight_completed', 0))
                },
                'results': {
                    'final_action': cascade['final_action'],
                    'final_confidence': cascade['final_confidence'],
                    'investigation_rounds': cascade['investigation_rounds'],
                    'engagement_gate_passed': bool(cascade['engagement_gate_passed']),
                    'bayesian_active': bool(cascade['bayesian_active']),
                    'drift_monitored': bool(cascade['drift_monitored'])
                },
                'timing': {
                    'started_at': cascade['started_at'],
                    'completed_at': cascade['completed_at'],
                    'duration_ms': cascade['duration_ms']
                },
                'assessments': self._get_cascade_assessments_summary(db, cascade['cascade_id'])
            }
            
            session_data['cascades'].append(cascade_data)
        
        # Write to file
        filepath = self.export_dir / f"session_{session_id}.json"
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
        
        logger.info(f"Exported session to: {filepath}")
        return filepath
    
    def export_cascade_graph(self, db: SessionDatabase, cascade_id: str) -> Path:
        """Export cascade as graph JSON for visualization"""
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM cascades WHERE cascade_id = ?", (cascade_id,))
        cascade = cursor.fetchone()
        
        if not cascade:
            raise ValueError(f"Cascade {cascade_id} not found")
        
        cascade = dict(cascade)
        
        # Get assessments for node data
        assessments = db.get_cascade_assessments(cascade_id)
        
        # Build graph structure
        nodes = []
        edges = []
        
        # PREFLIGHT node
        if cascade.get('preflight_completed', 0):
            preflight_assessment = next((a for a in assessments if a['phase'] == 'preflight'), None)
            nodes.append({
                'id': 'preflight',
                'type': 'assessment',
                'label': 'PREFLIGHT',
                'data': {
                    'completed': True,
                    'vectors': preflight_assessment['vectors'] if preflight_assessment else None,
                    'explicit_uncertainty': preflight_assessment.get('explicit_uncertainty') if preflight_assessment else None
                }
            })
        
        # THINK node
        if cascade['think_completed']:
            nodes.append({
                'id': 'think',
                'type': 'phase',
                'label': 'THINK',
                'data': {'completed': True}
            })
            if cascade.get('preflight_completed', 0):
                edges.append({'from': 'preflight', 'to': 'think'})
        
        # PLAN node (for complex tasks)
        if cascade.get('plan_completed', 0):
            nodes.append({
                'id': 'plan',
                'type': 'phase',
                'label': 'PLAN',
                'data': {'completed': True}
            })
            edges.append({'from': 'think', 'to': 'plan'})
        
        # INVESTIGATE nodes (one per round)
        if cascade['investigate_completed']:
            for i in range(cascade['investigation_rounds']):
                node_id = f'investigate_round_{i+1}'
                nodes.append({
                    'id': node_id,
                    'type': 'phase',
                    'label': f'INVESTIGATE Round {i+1}',
                    'data': {'completed': True, 'round': i+1}
                })
                
                if i == 0:
                    # Connect from plan if it exists, otherwise from think
                    prev_node = 'plan' if cascade.get('plan_completed', 0) else 'think'
                    edges.append({'from': prev_node, 'to': node_id})
                else:
                    edges.append({'from': f'investigate_round_{i}', 'to': node_id})
        
        # CHECK node
        if cascade['check_completed']:
            check_assessment = next((a for a in assessments if a['phase'] == 'check'), None)
            nodes.append({
                'id': 'check',
                'type': 'phase',
                'label': 'CHECK',
                'data': {
                    'completed': True,
                    'self_confidence': check_assessment.get('overall_confidence') if check_assessment else None,
                    'needs_more_investigation': check_assessment.get('recommended_action') == 'investigate_more' if check_assessment else None
                }
            })
            
            if cascade['investigation_rounds'] > 0:
                edges.append({'from': f'investigate_round_{cascade["investigation_rounds"]}', 'to': 'check'})
            else:
                # No investigation rounds - direct from plan or think
                prev_node = 'plan' if cascade.get('plan_completed', 0) else 'think'
                edges.append({'from': prev_node, 'to': 'check'})
        
        # ACT node
        if cascade['act_completed']:
            nodes.append({
                'id': 'act',
                'type': 'phase',
                'label': 'ACT',
                'data': {
                    'completed': True,
                    'final_action': cascade['final_action'],
                    'final_confidence': cascade['final_confidence']
                }
            })
            edges.append({'from': 'check', 'to': 'act'})
        
        # POSTFLIGHT node
        if cascade.get('postflight_completed', 0):
            postflight_assessment = next((a for a in assessments if a['phase'] == 'postflight'), None)
            nodes.append({
                'id': 'postflight',
                'type': 'assessment',
                'label': 'POSTFLIGHT',
                'data': {
                    'completed': True,
                    'vectors': postflight_assessment.get('vectors') if postflight_assessment else None,
                    'calibration_accuracy': postflight_assessment.get('calibration_accuracy') if postflight_assessment else None,
                    'delta_from_preflight': postflight_assessment.get('delta_from_preflight') if postflight_assessment else None
                }
            })
            edges.append({'from': 'act', 'to': 'postflight'})
        
        graph_data = {
            'cascade_id': cascade_id,
            'task': cascade['task'],
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'total_duration_ms': cascade['duration_ms'],
                'investigation_rounds': cascade['investigation_rounds'],
                'bayesian_active': bool(cascade['bayesian_active']),
                'drift_monitored': bool(cascade['drift_monitored'])
            }
        }
        
        # Write to file
        filepath = self.export_dir / f"cascade_{cascade_id}_graph.json"
        with open(filepath, 'w') as f:
            json.dump(graph_data, f, indent=2, default=str)
        
        logger.info(f"Exported cascade graph to: {filepath}")
        return filepath
    
    def load_session_context(self, session_id: str) -> Optional[Dict]:
        """Load session JSON for AI reading (session continuity)"""
        filepath = self.export_dir / f"session_{session_id}.json"
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load session context: {e}")
            return None
    
    def read_synthesis_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Read synthesis history for a session from database

        Synthesis history tracks:
        - User inputs (expectations, requirements)
        - AI responses (interpretations, solutions)
        - Alignment scores (how well AI understood user intent)

        This is used by DriftMonitor to detect sycophancy and tension avoidance.

        Args:
            session_id: Session UUID

        Returns:
            List of synthesis events, each containing:
            - timestamp: When the synthesis occurred
            - user_input: What user said/requested
            - ai_response: How AI interpreted/responded
            - alignment_score: 0.0-1.0 (how well aligned)
            - tension_present: bool (was there disagreement/challenge)
        """
        db = SessionDatabase()

        # Get all cascades for this session
        cascades = db.get_session_cascades(session_id)

        synthesis_events = []

        for cascade in cascades:
            # Get CHECK phase assessments (where synthesis happens)
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT assessed_at, phase, overall_confidence, recommended_action, 
                       engagement, know, do, context, clarity, coherence, 
                       signal, density, state, change, completion, impact
                FROM epistemic_assessments
                WHERE cascade_id = ? AND phase IN ('preflight', 'check', 'postflight')
                ORDER BY assessed_at ASC
            """, (cascade['cascade_id'],))

            assessments = cursor.fetchall()

            for assessment in assessments:
                # Build synthesis event from assessment
                synthesis_event = {
                    'timestamp': assessment['assessed_at'],
                    'cascade_id': cascade['cascade_id'],
                    'task': cascade['task'],
                    'phase': assessment['phase'],
                    'user_input': cascade['task'],  # User's original request
                    'ai_response': self._extract_reasoning_summary(assessment),  # AI's assessment
                    'alignment_score': assessment['overall_confidence'],  # How confident AI is
                    'tension_present': assessment['recommended_action'] in ['investigate', 'proceed_with_caution'],  # Investigation = tension
                    'vectors': {
                        'engagement': assessment['engagement'],
                        'know': assessment['know'],
                        'do': assessment['do'],
                        'context': assessment['context'],
                        'clarity': assessment['clarity'],
                        'coherence': assessment['coherence'],
                        'signal': assessment['signal'],
                        'density': assessment['density'],
                        'state': assessment['state'],
                        'change': assessment['change'],
                        'completion': assessment['completion'],
                        'impact': assessment['impact']
                    },
                    'recommended_action': assessment['recommended_action']
                }

                synthesis_events.append(synthesis_event)

        db.close()

        return synthesis_events
    
    def _extract_reasoning_summary(self, assessment: Dict) -> str:
        """
        Extract a concise reasoning summary from assessment data
        Used to populate ai_response field in synthesis events
        """
        try:
            # Build a summary from key vectors that indicate reasoning
            vectors = {
                'know': assessment.get('know', 0),
                'do': assessment.get('do', 0),
                'context': assessment.get('context', 0),
                'clarity': assessment.get('clarity', 0),
                'state': assessment.get('state', 0),
                'completion': assessment.get('completion', 0)
            }
            
            # Create a basic reasoning summary
            avg_confidence = sum(vectors.values()) / len(vectors)
            action = assessment.get('recommended_action', 'unknown')
            
            if avg_confidence >= 0.8:
                confidence_level = "high confidence"
            elif avg_confidence >= 0.6:
                confidence_level = "moderate confidence"
            else:
                confidence_level = "low confidence"
            
            return f"AI assessment with {confidence_level} ({avg_confidence:.2f}), recommended action: {action}"
            
        except Exception as e:
            return f"Assessment summary: {assessment.get('recommended_action', 'unknown action')}"
    
    def create_compact_summary(self, db: SessionDatabase, session_id: str) -> Dict:
        """Create compact summary for previous session context"""
        session = db.get_session(session_id)
        if not session:
            return {}
        
        cascades = db.get_session_cascades(session_id)
        
        # Calculate aggregate metrics
        avg_confidence = session['avg_confidence']
        total_cascades = len(cascades)
        
        # Get divergence and drift info
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count, AVG(divergence_score) as avg_score
            FROM divergence_tracking dt
            JOIN cascades c ON dt.cascade_id = c.cascade_id
            WHERE c.session_id = ? AND synthesis_needed = 1
        """, (session_id,))
        divergence_stats = dict(cursor.fetchone())
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM drift_monitoring
            WHERE session_id = ? AND (sycophancy_detected = 1 OR tension_avoidance_detected = 1)
        """, (session_id,))
        drift_count = cursor.fetchone()['count']
        
        summary = {
            'session_id': session_id,
            'ai_id': session['ai_id'],
            'duration': session['end_time'] if session['end_time'] else 'ongoing',
            'statistics': {
                'total_cascades': total_cascades,
                'avg_confidence': avg_confidence,
                'divergence_events': divergence_stats['count'],
                'avg_divergence_score': divergence_stats['avg_score'],
                'drift_incidents': drift_count
            },
            'behavioral_summary': {
                'drift_detected': bool(session['drift_detected']),
                'needs_attention': drift_count > 0 or (divergence_stats['avg_score'] or 0) > 0.5
            }
        }
        
        return summary
    
    def _get_cascade_assessments_summary(self, db: SessionDatabase, cascade_id: str) -> List[Dict]:
        """Get summary of assessments for a cascade"""
        assessments = db.get_cascade_assessments(cascade_id)
        
        summary = []
        for a in assessments:
            summary.append({
                'phase': a['phase'],
                'engagement': a['engagement'],
                'overall_confidence': a['overall_confidence'],
                'foundation': a['foundation_confidence'],
                'comprehension': a['comprehension_confidence'],
                'execution': a['execution_confidence'],
                'recommended_action': a['recommended_action']
            })
        
        return summary


if __name__ == "__main__":
    # Test the JSON handler
    logger.info("Testing JSON Handler...")
    
    # Create test data
    from empirica.data.session_database import SessionDatabase
    
    db = SessionDatabase()
    handler = SessionJSONHandler()
    
    # Create test session with cascade
    session_id = db.create_session("test_claude", bootstrap_level=2, components_loaded=30)
    cascade_id = db.create_cascade(session_id, "Test JSON export", {"test": True})
    
    # Complete cascade with new workflow phases
    for phase in ['preflight', 'think', 'plan', 'investigate', 'check', 'act', 'postflight']:
        db.update_cascade_phase(cascade_id, phase, True)
    
    db.complete_cascade(cascade_id, "proceed", 0.85, 2, 5000, True, True, False)
    
    # Export session
    session_file = handler.export_session(db, session_id)
    logger.info(f"Session exported: {session_file.name}")
    
    # Export cascade graph
    graph_file = handler.export_cascade_graph(db, cascade_id)
    logger.info(f"Cascade graph exported: {graph_file.name}")
    
    # Load back
    loaded = handler.load_session_context(session_id)
    logger.info(f"Loaded session: {loaded['ai_id']}, {len(loaded['cascades'])} cascades")
    
    # Compact summary
    summary = handler.create_compact_summary(db, session_id)
    logger.info(f"Compact summary: {summary['statistics']}")
    
    db.close()
    logger.info("JSON Handler tests passed!")
