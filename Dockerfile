FROM python:3.13-slim-bullseye

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

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy Poetry configuration files
COPY pyproject.toml ./

# Configure Poetry - using in-project virtualenv to be consistent with development environment
RUN poetry config virtualenvs.in-project true

# Install dependencies with better error handling
RUN poetry install --no-interaction --no-root --without dev || \
    (echo "Retrying poetry install..." && \
     poetry lock --no-update && \
     poetry install --no-interaction --no-root --without dev)

# Copy application code
COPY . .

# Set Python path and environment variables to ensure standard mode
ENV PYTHONPATH=/app
ENV USE_RECOVERY_MODE=false
ENV STANDARD_MODE=true

# Default environment is staging (will be overridden in deployment)
ENV ENVIRONMENT=staging
ENV PORT=8000

# Set Google Cloud credentials environment variable
ENV GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json

# Expose port for the application
EXPOSE ${PORT}

# Create force standard mode script during build
RUN echo '#!/bin/bash\npython3 -c "import os; os.environ[\"USE_RECOVERY_MODE\"]=\"false\"; os.environ[\"STANDARD_MODE\"]=\"true\";"' > /app/force_standard_mode.sh && \
    chmod +x /app/force_standard_mode.sh

# Run the application with forced standard mode
CMD bash -c "source /app/force_standard_mode.sh && exec python3 -m orchestrator.main"
