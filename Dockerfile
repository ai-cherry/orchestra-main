# AI Orchestra Dockerfile
# Uses multi-stage build for optimized production image

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=1.5.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=0 \
    POETRY_HOME="/opt/poetry"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry export -f requirements.txt > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PYTHONPATH=/app \
    USE_RECOVERY_MODE=false \
    STANDARD_MODE=true \
    VSCODE_DISABLE_WORKSPACE_TRUST=true \
    DISABLE_WORKSPACE_TRUST=true \
    PORT=8080

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Add startup script to enforce standard mode
RUN echo '#!/bin/bash\n\
# Force standard mode with all required environment variables\n\
export USE_RECOVERY_MODE=false\n\
export STANDARD_MODE=true\n\
export VSCODE_DISABLE_WORKSPACE_TRUST=true\n\
export DISABLE_WORKSPACE_TRUST=true\n\
\n\
# Create standard mode marker file\n\
touch /app/.standard_mode\n\
\n\
# Start the application\n\
exec python -m core.orchestrator.src.main\n\
' > /app/startup.sh && chmod +x /app/startup.sh

# Create non-root user
RUN groupadd -r orchestra && \
    useradd -r -g orchestra -d /app -s /bin/bash orchestra && \
    chown -R orchestra:orchestra /app

# Switch to non-root user
USER orchestra

# Expose port
EXPOSE ${PORT}

# Set health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Set entrypoint to use the startup script
ENTRYPOINT ["/app/startup.sh"]
