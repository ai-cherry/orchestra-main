FROM python:3.11-slim-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt .
COPY core/orchestrator/requirements.txt ./core/orchestrator/
COPY packages/shared/requirements.txt ./packages/shared/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir -r core/orchestrator/requirements.txt \
    && pip3 install --no-cache-dir -r packages/shared/requirements.txt

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Default environment is staging (will be overridden in deployment)
ENV ENVIRONMENT=staging
ENV PORT=8000

# Set Google Cloud credentials environment variable
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json

# Expose port for the application
EXPOSE ${PORT}

# Run the application
CMD exec python3 -m orchestrator.main
