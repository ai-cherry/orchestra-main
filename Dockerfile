# Stage 1: Builder stage - for installing dependencies including build-time ones
FROM python:3.10-slim-bullseye AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (e.g., for C extensions like psycopg2, or other build tools)
# Only include what's necessary for building your wheels or dependencies.
# If build-essential was only for a specific package, try to install only essential libs for that.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    # Add other build-time system dependencies here if needed (e.g., libpq-dev for psycopg2)
    && rm -rf /var/lib/apt/lists/*

# Install Python build tools
RUN pip install --upgrade pip wheel

# Copy only requirements to leverage Docker cache
COPY requirements-app.txt ./

# Install Python dependencies (build wheels if necessary)
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements-app.txt

# Stage 2: Final runtime stage - minimal image
FROM python:3.10-slim-bullseye AS final

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV APP_HOME=/app

WORKDIR ${APP_HOME}

# Create a non-root user and group
RUN groupadd --system appuser && useradd --system --gid appuser appuser

# Copy built wheels from builder stage
COPY --from=builder /wheels /wheels

# Install Python dependencies from wheels (faster and doesn't need build tools)
# Also copy requirements.txt for completeness or if some packages don't produce wheels easily
COPY requirements-app.txt ./
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements-app.txt

# Copy application code
# Ensure correct ownership if files are created/copied as root before switching user
COPY . ${APP_HOME}
RUN chown -R appuser:appuser ${APP_HOME}

# Switch to non-root user
USER appuser

# Expose the port (for documentation; Cloud Run uses $PORT)
EXPOSE 8080

# Start the app with uvicorn (FastAPI ASGI server)
# exec ensures uvicorn replaces the shell, correctly handling signals
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
