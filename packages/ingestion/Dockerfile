# Dockerfile for Orchestra File Ingestion Worker
#
# This Dockerfile builds a container image for the ingestion worker service
# that can be deployed to Cloud Run or other container environments.

# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    libmagic1 \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY packages/ingestion/requirements.txt ./packages/ingestion/requirements.txt
RUN pip install --no-cache-dir -r packages/ingestion/requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn fastapi

# Copy the package code
COPY packages/ingestion ./packages/ingestion
COPY packages/shared ./packages/shared
COPY core/orchestrator/src/config ./core/orchestrator/src/config

# Create directory for temp files
RUN mkdir -p /tmp/ingestion && chmod 777 /tmp/ingestion

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
ENV TEMP_DIR=/tmp/ingestion

# Create a volume for credentials
VOLUME ["/app/credentials"]

# Default command - run the worker
CMD ["python", "packages/ingestion/src/worker/run_worker.py"]
