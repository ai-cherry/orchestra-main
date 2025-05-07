1from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "GCP deployment successful!",
        "environment": "Cloud Run",
        "project": os.environ.get("GOOGLE_CLOUD_PROJECT", "unknown"),
        "service_account": os.environ.get("GOOGLE_SERVICE_ACCOUNT", "unknown")
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/info')
def info():
    return jsonify({
        "app": "GCP Test Deployment",
        "version": "1.0.0",
        "gcp_integration": "enabled",
        "ide_sync": "configured"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
