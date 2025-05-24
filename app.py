from core.logging_config import setup_logging, get_logger
import os

# Set up structured JSON logging
# Determine if running in production (Cloud Run) or development
is_production = os.environ.get("K_SERVICE") is not None
setup_logging(json_format=is_production)

logger = get_logger(__name__)

from flask import Flask, jsonify, request
import os
from utils import retry
import requests

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify(
        {
            "status": "success",
            "message": "GCP deployment successful!",
            "environment": "Cloud Run",
            "project": os.environ.get("GOOGLE_CLOUD_PROJECT", "unknown"),
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
        # ... code that calls the LLM API ...
        pass
    except Exception as e:
        logger.error("LLM API call failed", exc_info=True, extra={"api_endpoint": "openai_v1"})
        return {"error": "LLM API call failed"}, 500


@retry(max_attempts=3, delay=2, exponential_backoff=2)
def fetch_external_data():
    response = requests.get("https://api.example.com/data", timeout=10)
    response.raise_for_status()
    return response.json()


@app.route("/fetch-data")
def fetch_data_sync():
    try:
        logger.info("Fetching external data", extra={"endpoint": "/fetch-data"})
        data = fetch_external_data()
        return jsonify(data)
    except requests.RequestException as e:
        logger.error(
            "External API call failed", exc_info=True, extra={"endpoint": "/fetch-data", "error_type": type(e).__name__}
        )
        return jsonify({"error": "Failed to fetch data"}), 502


@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(
        "Unhandled exception",
        exc_info=True,
        extra={"path": request.path, "method": request.method, "remote_addr": request.remote_addr},
    )
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
