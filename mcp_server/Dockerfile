# Performance-optimized Dockerfile for MCP Server
# Uses multi-stage build for smaller image size and faster builds

# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN ~/.local/bin/poetry install --no-root --no-dev

# Stage 2: Runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=2 \
    PATH="/app/.venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Set up a non-root user
RUN groupadd -r mcp && useradd -r -g mcp mcp \
    && chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Use tini as entrypoint to handle signals properly
ENTRYPOINT ["/usr/bin/tini", "--"]

# Command to run the application
CMD ["python", "-m", "mcp_server.main"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Metadata
LABEL org.opencontainers.image.title="MCP Server" \
      org.opencontainers.image.description="Model Context Protocol (MCP) Memory System" \
      org.opencontainers.image.vendor="AI Orchestra Team" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.url="https://github.com/ai-orchestra/mcp-server" \
      org.opencontainers.image.documentation="https://github.com/ai-orchestra/mcp-server/README.md"