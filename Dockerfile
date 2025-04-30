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

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy Poetry configuration files
COPY pyproject.toml ./

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Modify dependencies before installation - remove agno dependency
RUN grep -v "agno" pyproject.toml > pyproject.toml.new && mv pyproject.toml.new pyproject.toml

# Install dependencies
RUN poetry install --no-interaction --no-root --without dev

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Default environment is staging (will be overridden in deployment)
ENV ENVIRONMENT=staging
ENV PORT=8000

# Set Google Cloud credentials environment variable
ENV GOOGLE_APPLICATION_CREDENTIALS=/tmp/vertex-agent-key.json

# Expose port for the application
EXPOSE ${PORT}

# Run the application
CMD exec python3 -m orchestrator.main
