FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a directory for data persistence
RUN mkdir -p /app/data

# Install Poetry
ENV POETRY_VERSION=1.8.2
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Install poetry separated from system interpreter
RUN python -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Add poetry to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

# Configure poetry to not use virtualenvs inside the container
RUN poetry config virtualenvs.create false

# Copy only necessary files for dependency installation
COPY mcp_server/pyproject.toml mcp_server/poetry.lock* ./

# Install dependencies
RUN poetry install --no-interaction --no-root --without dev

# Copy application code
COPY mcp_server ./mcp_server

# Install the application
RUN poetry install --no-interaction --only-root

# Create configuration
COPY mcp_server/config.json.example mcp_server/config.json

# Create non-root user for security
RUN groupadd -r mcp && \
    useradd -r -g mcp -d /app -s /bin/bash mcp && \
    chown -R mcp:mcp /app

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/status || exit 1

# Expose port for web interface
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_DATA_DIR=/app/data

# Switch to non-root user
USER mcp

# Run the MCP server
CMD ["poetry", "run", "mcp-server", "--config", "mcp_server/config.json"]
