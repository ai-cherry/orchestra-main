#!/usr/bin/env python3
"""
"""
    """
    """
    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint for service monitoring."""
        return jsonify({"status": "healthy", "service": "mcp-server"})

    @app.route("/readiness", methods=["GET"])
    def readiness_check():
        """Readiness check endpoint for service monitoring."""
        return jsonify({"status": "ready", "service": "mcp-server"})
