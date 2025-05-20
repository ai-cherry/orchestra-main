#!/usr/bin/env python3
"""
AI Orchestra GCP Migration - Deploy Minimal Service

This script creates and deploys a minimal service to Cloud Run 
to test the deployment infrastructure.
"""

import os
import subprocess
import tempfile
import time
import json
from typing import Dict, List, Optional, Tuple

# Constants
PROJECT_ID = "cherry-ai-project"
SERVICE_NAME = "ai-orchestra-minimal"
REGION = "us-central1"
TEMP_DIR = tempfile.mkdtemp(prefix="ai-orchestra-")


def log(message: str) -> None:
    """Print and log a message."""
    print(f"[DEPLOY] {message}")


def run_command(cmd: str) -> Tuple[int, str]:
    """Run a shell command and return the exit code and output."""
    log(f"Running command: {cmd}")
    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    output, _ = process.communicate()
    exit_code = process.returncode
    output_str = output.decode("utf-8")

    if exit_code == 0:
        log("Command succeeded")
    else:
        log(f"Command failed with exit code {exit_code}")

    return exit_code, output_str


def create_minimal_app() -> str:
    """Create a minimal FastAPI application."""
    log(f"Creating minimal FastAPI app in {TEMP_DIR}")

    # Create main.py
    with open(os.path.join(TEMP_DIR, "main.py"), "w") as f:
        f.write(
            """from fastapi import FastAPI
import os
import platform
import datetime

app = FastAPI(
    title="AI Orchestra Minimal Service",
    description="A minimal service to test Cloud Run deployment",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "message": "AI Orchestra Minimal Service is running",
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/info")
def get_info():
    return {
        "service": "ai-orchestra-minimal",
        "version": "1.0.0",
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "system": platform.system(),
        "environment": os.environ.get("ENV", "development")
    }
"""
        )

    # Create requirements.txt
    with open(os.path.join(TEMP_DIR, "requirements.txt"), "w") as f:
        f.write("fastapi==0.110.0\nuvicorn==0.29.0\n")

    # Create Dockerfile
    with open(os.path.join(TEMP_DIR, "Dockerfile"), "w") as f:
        f.write(
            """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV HOST=0.0.0.0

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
"""
        )

    return TEMP_DIR


def build_and_deploy() -> bool:
    """Build and deploy the minimal service."""
    log("Building and deploying minimal service")

    # Change to temp directory
    original_dir = os.getcwd()
    os.chdir(TEMP_DIR)

    try:
        # Build the container
        image_name = f"gcr.io/{PROJECT_ID}/{SERVICE_NAME}:latest"
        cmd = f"docker build -t {image_name} ."
        exit_code, output = run_command(cmd)
        if exit_code != 0:
            log("Docker build failed")
            return False

        # Configure docker authentication if needed
        run_command("gcloud auth configure-docker --quiet")

        # Push the image
        cmd = f"docker push {image_name}"
        exit_code, output = run_command(cmd)
        if exit_code != 0:
            log("Docker push failed")
            return False

        # Deploy to Cloud Run
        cmd = f"""gcloud run deploy {SERVICE_NAME} \
            --image={image_name} \
            --platform=managed \
            --region={REGION} \
            --allow-unauthenticated \
            --memory=256Mi \
            --cpu=1 \
            --min-instances=1 \
            --max-instances=5 \
            --port=8080 \
            --set-env-vars=ENV=production \
            --quiet"""
        exit_code, output = run_command(cmd)
        if exit_code != 0:
            log("Cloud Run deployment failed")
            return False

        log("Deployment completed successfully")
        return True

    finally:
        # Restore original directory
        os.chdir(original_dir)


def check_deployment() -> Dict:
    """Check the deployment status."""
    log("Checking deployment status")

    # Get service URL
    cmd = f"gcloud run services describe {SERVICE_NAME} --region={REGION} --format='get(status.url)'"
    _, output = run_command(cmd)
    service_url = output.strip()

    result = {
        "service_name": SERVICE_NAME,
        "service_url": service_url,
        "region": REGION,
        "timestamp": time.time(),
    }

    # Check if service is accessible
    if service_url:
        cmd = f"curl -s {service_url}/health"
        exit_code, output = run_command(cmd)
        result["health_check"] = {"success": exit_code == 0, "response": output.strip()}

    # Write report
    report_dir = os.path.join(os.path.dirname(__file__), "migration_logs")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "minimal_service_report.json")

    with open(report_path, "w") as f:
        json.dump(result, f, indent=2)

    log(f"Deployment report written to {report_path}")

    return result


def main():
    """Main function."""
    log("Starting minimal service deployment")

    # Create the app
    app_dir = create_minimal_app()
    log(f"Minimal app created in {app_dir}")

    # Build and deploy
    success = build_and_deploy()

    if success:
        # Check deployment
        result = check_deployment()
        log(f"Service deployed at: {result.get('service_url')}")
    else:
        log("Deployment failed")

    log("Minimal service deployment process completed")


if __name__ == "__main__":
    main()
