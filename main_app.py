import os

from core.logging_config import get_logger, setup_logging

# Set up structured JSON logging
# Determine if running in production (Cloud Run) or development
is_production = os.environ.get("K_SERVICE") is not None
setup_logging(json_format=is_production)

logger = get_logger(__name__)

import os

import litellm
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify(
        {
            "status": "success",
            "message": "GCP deployment successful!",
            "environment": "Cloud Run",
            "project": os.environ.get("VULTR_PROJECT_ID", "unknown"),
            "service_account": os.environ.get("GOOGLE_SERVICE_ACCOUNT", "unknown"),
        }
    )

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

@app.route("/info")
def info():
    return jsonify(
        {
            "app": "GCP Test Deployment",
            "version": "1.0.0",
            "gcp_integration": "enabled",
            "ide_sync": "configured",
        }
    )

@app.route("/query", methods=["POST"])
def handle_query():
    data = request.json
    user_id = data.get("user_id")
    query = data.get("query", "")
    logger.info("User query received", extra={"user_id": user_id, "query_length": len(query)})
    return {"status": "ok"}

@app.route("/call-llm", methods=["POST"])
def call_llm():
    try:
        data = request.json
        prompt = data.get("prompt", "")
        model = data.get("model", "gpt-3.5-turbo")

        # Use litellm for LLM API calls
        response = litellm.completion(model=model, messages=[{"role": "user", "content": prompt}])

        logger.info("LLM API call successful", extra={"model": model})
        return jsonify({"status": "success", "response": response.choices[0].message.content})
    except Exception as e:
        logger.error(
            "LLM API call failed",
            exc_info=False,
            extra={"api_endpoint": model, "error": str(e)},
        )
        return jsonify({"error": "LLM API call failed"}), 500

@app.route("/health/detailed")
def health_detailed():
    """Detailed health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {
            "app": "running",
            "gcp_project": os.environ.get("VULTR_PROJECT_ID", "not_set"),
            "api_keys_loaded": {
                "openai": bool(os.environ.get("OPENAI_API_KEY")),
                "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            },
        },
    }
    return jsonify(health_status)

@app.errorhandler(Exception)
def handle_exception(e):
    # Don't expose stack traces in production
    is_production = os.environ.get("K_SERVICE") is not None

    if is_production:
        logger.error(
            "Unhandled exception",
            exc_info=True,  # Log full details server-side
            extra={"path": request.path, "method": request.method},
        )
        return jsonify({"error": "Internal server error"}), 500
    else:
        # In development, return more details
        logger.error(
            "Unhandled exception",
            exc_info=True,
            extra={
                "path": request.path,
                "method": request.method,
                "remote_addr": request.remote_addr,
            },
        )
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
