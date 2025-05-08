# Dockerfile for AI Orchestra with flexible GCP authentication
FROM python:3.11-slim

WORKDIR /app

# Create a directory for GCP credentials (will be mounted or populated at runtime)
RUN mkdir -p /app/.gcp
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/.gcp/service-account.json

# Copy Poetry configuration files for dependency caching
COPY pyproject.toml poetry.lock* ./

# Install Poetry and dependencies
RUN pip install --no-cache-dir poetry==1.8.2 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --without dev

# Copy only necessary application code
COPY packages/ ./packages/
COPY core/ ./core/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080
ENV PROJECT_ID=cherry-ai-project
ENV REGION=us-central1
ENV VERTEX_LOCATION=us-central1

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

# Run the application
CMD ["poetry", "run", "uvicorn", "packages.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
