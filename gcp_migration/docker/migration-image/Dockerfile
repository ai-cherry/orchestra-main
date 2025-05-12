# Dockerfile for GCP Migration Toolkit
# Uses Poetry for dependency management and multi-stage build for optimization

# Builder stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry==1.6.1 \
    && poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install dependencies only (without development dependencies)
RUN poetry install --no-interaction --no-ansi --without dev

# Copy source code
COPY . .

# Build the package
RUN poetry build

# Final stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Google Cloud SDK
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    lsb-release \
    ca-certificates \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update && apt-get install -y --no-install-recommends \
    google-cloud-sdk \
    google-cloud-sdk-gke-gcloud-auth-plugin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy built package from builder stage
COPY --from=builder /app/dist/*.whl /app/

# Install the package
RUN pip install --no-cache-dir /app/*.whl

# Create directory for configuration and data
RUN mkdir -p /app/config /app/data

# Set environment variables for GCP
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/config/credentials.json

# Create non-root user for running the application
RUN groupadd -r appuser && useradd -r -g appuser -m -d /home/appuser appuser \
    && chown -R appuser:appuser /app/config /app/data

# Switch to non-root user
USER appuser

# Set default command to run the CLI
ENTRYPOINT ["gcp-migrate"]
CMD ["--help"]