#!/usr/bin/env python3
"""
health_check.py - Health check endpoint for the MCP server

This module adds a health check endpoint to the MCP server for Cloud Run deployment.
"""

def register_health_endpoints(app):
    """Register health check endpoints for the Flask application.
    
    Args:
        app: Flask application instance
    """
    from flask import jsonify
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for Cloud Run."""
        return jsonify({
            'status': 'healthy',
            'service': 'mcp-server'
        })
    
    @app.route('/readiness', methods=['GET'])
    def readiness_check():
        """Readiness check endpoint for Cloud Run."""
        return jsonify({
            'status': 'ready',
            'service': 'mcp-server'
        })