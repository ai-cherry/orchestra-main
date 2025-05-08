# Dockerfile for containerizing Phidata agents for Cloud Run deployment
# Base image with Python
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry for dependency management
RUN pip install poetry==1.8.2

# Copy Poetry configuration files for dependency caching
COPY pyproject.toml poetry.lock* /app/

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy only necessary application code
COPY packages/agents /app/packages/agents
COPY packages/shared /app/packages/shared
COPY packages/llm /app/packages/llm
COPY packages/phidata /app/packages/phidata

# Install Google Cloud SDK for authentication and deployment
RUN apt-get update && apt-get install -y gnupg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update && apt-get install -y google-cloud-sdk \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Google Cloud authentication
# Note: GOOGLE_APPLICATION_CREDENTIALS will be set at runtime via Cloud Run environment variables
ENV PROJECT_ID=cherry-ai-project
ENV REGION=us-central1
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/.gcp/service-account.json

# Create directory for GCP credentials
RUN mkdir -p /app/.gcp

# Copy entrypoint script for agent initialization
COPY scripts/phidata-agent-entrypoint.sh /app/scripts/phidata-agent-entrypoint.sh
RUN chmod +x /app/scripts/phidata-agent-entrypoint.sh

# Create non-root user for security
RUN groupadd -r orchestra && \
    useradd -r -g orchestra -d /app -s /bin/bash orchestra && \
    chown -R orchestra:orchestra /app

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root user
USER orchestra

# Expose port for Cloud Run
EXPOSE 8080

# Command to run the Phidata agent on Cloud Run
CMD ["/app/scripts/phidata-agent-entrypoint.sh"]