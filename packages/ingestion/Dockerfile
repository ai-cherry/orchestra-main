# Dockerfile for Orchestra File Ingestion Worker
#
# This Dockerfile builds a container image for the ingestion worker service
# that can be deployed to Cloud Run or other container environments.

# Builder Stage
FROM python:3.11-slim AS builder
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    libmagic1 \
    pkg-config \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Poetry configuration files for dependency caching
COPY pyproject.toml poetry.lock* ./

# Install Poetry and dependencies
RUN pip install --no-cache-dir poetry==1.8.2 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --without dev

# Copy only necessary application code
COPY packages/ingestion ./packages/ingestion
COPY packages/shared ./packages/shared
COPY core/orchestrator/src/config ./core/orchestrator/src/config

# Runtime Stage
FROM python:3.11-slim
WORKDIR /app

# Copy dependencies and application code from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/packages ./packages
COPY --from=builder /app/core ./core

# Create directory for temp files and credentials
RUN mkdir -p /tmp/ingestion && chmod 777 /tmp/ingestion
RUN mkdir -p /app/.gcp

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/.gcp/service-account.json
ENV TEMP_DIR=/tmp/ingestion
ENV PROJECT_ID=cherry-ai-project
ENV REGION=us-central1

# Create non-root user for security
RUN groupadd -r orchestra && \
    useradd -r -g orchestra -d /app -s /bin/bash orchestra && \
    chown -R orchestra:orchestra /app /tmp/ingestion

# Add health check with improved parameters
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Add STOPSIGNAL for graceful shutdown
STOPSIGNAL SIGTERM

# Add environment variable for graceful shutdown
ENV GRACEFUL_SHUTDOWN_TIMEOUT=30

# Switch to non-root user
USER orchestra

# Expose port for Cloud Run
EXPOSE 8080

# Default command - run the worker
CMD ["python", "packages/ingestion/src/worker/run_worker.py"]
