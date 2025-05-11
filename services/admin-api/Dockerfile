# Stage 1: Builder
FROM python:3.11-slim-bullseye AS builder

WORKDIR /app

# Install Poetry and build dependencies
RUN pip install --no-cache-dir poetry==1.8.2 \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files only (for better caching)
COPY pyproject.toml poetry.lock ./

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root --without dev

# Copy application code
COPY ./main.py ./
COPY ./app ./app

# Stage 2: Production
FROM python:3.11-slim-bullseye AS production

WORKDIR /app

# Set environment variables with improved performance settings
ENV PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    WEB_CONCURRENCY=4 \
    WORKERS_PER_CORE=2 \
    MAX_KEEPALIVE=120 \
    LIMIT_MAX_REQUESTS=10000

# Install runtime dependencies only
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app/main.py ./
COPY --from=builder /app/app ./app

# Create cache directories with full permissions
RUN mkdir -p /app/logs /app/data /app/cache

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Command to run the application with performance settings
CMD uvicorn app.application:app --host 0.0.0.0 --port $PORT \
    --workers $WEB_CONCURRENCY \
    --limit-max-requests $LIMIT_MAX_REQUESTS \
    --timeout-keep-alive $MAX_KEEPALIVE \
    --log-level warning