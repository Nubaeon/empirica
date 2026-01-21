"""
Empirica Vision Module

Provides visual analysis capabilities for epistemic assessment:
- Image/slide analysis for documentation
- Visual observation logging
- Screenshot and diagram processing

Components:
- vision_analyze: Analyze images and extract metadata
- vision_log: Log visual observations to sessions

Usage:
    from empirica.vision import analyze_image, log_observation

    # Analyze slide deck
    results = analyze_image("slides/*.png", session_id="abc")

    # Log visual observation
    log_observation(session_id, "Diagram shows 3-tier architecture")
"""
