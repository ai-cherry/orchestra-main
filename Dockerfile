FROM python:3.11-slim-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements*.txt .
COPY core/orchestrator/requirements.txt ./core/orchestrator/
COPY packages/shared/requirements.txt ./packages/shared/

# Install Python dependencies
# First install the consolidated requirements which is referenced by other requirement files
RUN pip3 install --no-cache-dir -r requirements-consolidated.txt \
    && pip3 install --no-cache-dir -r requirements.txt \
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
# Using /tmp/vertex-agent-key.json for consistency with local development
ENV GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json

# Expose port for the application
EXPOSE ${PORT}

# Run the application
CMD exec python3 -m orchestrator.main
