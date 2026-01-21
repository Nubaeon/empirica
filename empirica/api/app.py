"""
Flask application for Empirica Dashboard API
"""

import logging
import json
from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure Flask application"""

    app = Flask(
        __name__,
        static_url_path="/api/v1/static",
        static_folder="./static"
    )

    # Enable CORS manually (flask-cors not installed)
    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to all responses."""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response

    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health_check():
        """Return API health status."""
        return jsonify({"status": "ok", "service": "empirica-api"})

    # Register blueprints
    from .routes import sessions, deltas, verification, heatmaps, comparison

    app.register_blueprint(sessions.bp, url_prefix="/api/v1")
    app.register_blueprint(deltas.bp, url_prefix="/api/v1")
    app.register_blueprint(verification.bp, url_prefix="/api/v1")
    app.register_blueprint(heatmaps.bp, url_prefix="/api/v1")
    app.register_blueprint(comparison.bp, url_prefix="/api/v1")

    # Global error handler
    @app.errorhandler(Exception)
    def handle_error(error):
        """Handle uncaught exceptions with JSON error response."""
        logger.error(f"API error: {error}")
        return jsonify({
            "ok": False,
            "error": "internal_server_error",
            "message": str(error),
            "status_code": 500
        }), 500

    logger.info("✅ Empirica Dashboard API initialized")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=True)
