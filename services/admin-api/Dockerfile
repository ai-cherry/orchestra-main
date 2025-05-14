# Multi-stage build for AI Orchestra admin-api service
# Optimized for performance and security with proper Poetry integration

# --- Build stage ---
FROM python:3.11-slim AS builder

# Set environment variables for Poetry
ENV POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Install Poetry with exact version
RUN pip install --upgrade pip && pip install "poetry==$POETRY_VERSION"

# Copy pyproject.toml and create an empty poetry.lock if it doesn't exist
COPY pyproject.toml ./
RUN if [ ! -f poetry.lock ]; then touch poetry.lock; fi

# Install dependencies without development dependencies
RUN poetry install --without dev --no-root

# Copy application code
COPY . .

# Install project
RUN poetry install --without dev

# --- Runtime stage ---
FROM python:3.11-slim

# Upgrade pip in runtime image
RUN pip install --upgrade pip

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8080

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY --from=builder /app/app /app/app
COPY --from=builder /app/main.py /app/main.py

# Add health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Run as non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app
USER appuser

# Run the service
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}