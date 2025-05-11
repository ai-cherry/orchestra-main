# Optimized Dockerfile for containerizing Phidata agents for Cloud Run deployment
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.2

# Copy Poetry configuration files for dependency caching
COPY pyproject.toml poetry.lock* ./

# Configure Poetry and export dependencies
RUN poetry config virtualenvs.create false && \
    poetry export -f requirements.txt --without dev > requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install minimal Google Cloud CLI components instead of full SDK
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    apt-get update && apt-get install -y --no-install-recommends \
    google-cloud-cli-auth \
    google-cloud-cli-storage \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from builder stage
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary application code
COPY packages/agents /app/packages/agents
COPY packages/shared /app/packages/shared
COPY packages/llm /app/packages/llm
COPY packages/phidata /app/packages/phidata

# Create directory for GCP credentials
RUN mkdir -p /app/.gcp

# Copy entrypoint script for agent initialization
COPY scripts/phidata-agent-entrypoint.sh /app/scripts/phidata-agent-entrypoint.sh
RUN chmod +x /app/scripts/phidata-agent-entrypoint.sh

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

# Expose port for Cloud Run
EXPOSE ${PORT}

# Cloud Run optimized settings
ENV WORKERS=2
ENV WORKER_CONNECTIONS=1000
ENV TIMEOUT=300
ENV GRACEFUL_TIMEOUT=120
ENV MAX_REQUESTS=1000
ENV MAX_REQUESTS_JITTER=50

# Command to run the Phidata agent on Cloud Run with optimized settings
CMD ["/app/scripts/phidata-agent-entrypoint.sh"]