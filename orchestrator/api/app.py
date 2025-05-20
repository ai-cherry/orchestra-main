"""
Main Flask application for the Orchestra Admin API.

This module initializes the Flask application and registers API blueprints.
"""

import logging
from flask import Flask
from flask_cors import CORS

from orchestrator.api.personas import personas_api
from orchestrator.api.projects import projects_api

# Initialize logger
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configure CORS to allow requests from the frontend
    CORS(app)

    # Register API blueprints
    app.register_blueprint(personas_api)
    app.register_blueprint(projects_api)

    logger.info("Flask application initialized with API blueprints")

    return app


# Create application instance
app = create_app()


@app.route("/")
def index():
    """Default route for health check."""
    return {"status": "healthy", "service": "Orchestra Admin API"}
