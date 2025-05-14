# Optimized Dockerfile for AI Orchestra with multi-stage build
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --upgrade pip && pip install --no-cache-dir poetry==1.8.2

# Copy Poetry configuration files for dependency caching
COPY pyproject.toml poetry.lock* ./

# Configure Poetry and export dependencies
RUN poetry config virtualenvs.create false && \
    poetry export -f requirements.txt --without dev > requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim

WORKDIR /app

# Create a directory for GCP credentials (will be mounted or populated at runtime)
RUN mkdir -p /app/.gcp

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip

# Copy requirements from builder stage
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary application code
COPY packages/ ./packages/
COPY core/ ./core/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/.gcp/service-account.json

# Create non-root user for security
RUN groupadd -r orchestra && \
    useradd -r -g orchestra -d /app -s /bin/bash orchestra && \
    chown -R orchestra:orchestra /app

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Switch to non-root user
USER orchestra

# Expose port for the application
EXPOSE ${PORT}

# Cloud Run optimized settings
ENV WORKERS=2
ENV WORKER_CONNECTIONS=1000
ENV TIMEOUT=300
ENV GRACEFUL_TIMEOUT=120

# Run the application with optimized settings for Cloud Run
CMD ["python", "-m", "uvicorn", "packages.api.main:app", "--host", "0.0.0.0", "--port", "${PORT}", "--workers", "${WORKERS}", "--timeout-keep-alive", "75", "--log-level", "info"]
