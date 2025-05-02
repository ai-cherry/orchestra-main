# Dockerfile for Orchestra File Ingestion Worker
#
# This Dockerfile builds a container image for the ingestion worker service
# that can be deployed to Cloud Run or other container environments.

# Builder Stage
FROM python:3.10-slim AS builder
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    libmagic1 \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements for caching
COPY packages/ingestion/requirements.txt ./packages/ingestion/requirements.txt

# Install Python dependencies in a virtual environment
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install --no-cache-dir -r packages/ingestion/requirements.txt && \
    pip install --no-cache-dir gunicorn uvicorn fastapi

# Copy the package code
COPY packages/ingestion ./packages/ingestion
COPY packages/shared ./packages/shared
COPY core/orchestrator/src/config ./core/orchestrator/src/config

# Runtime Stage
FROM python:3.10-slim
WORKDIR /app

# Copy the virtual environment from builder stage
COPY --from=builder /app/venv ./venv
# Copy the application code from builder stage
COPY --from=builder /app/packages ./packages
COPY --from=builder /app/core ./core

# Create directory for temp files
RUN mkdir -p /tmp/ingestion && chmod 777 /tmp/ingestion

# Set environment variables
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service-account.json
ENV TEMP_DIR=/tmp/ingestion

# Create a volume for credentials
VOLUME ["/app/credentials"]

# Default command - run the worker
CMD ["python", "packages/ingestion/src/worker/run_worker.py"]
