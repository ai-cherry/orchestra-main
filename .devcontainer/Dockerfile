# Use the official Python image instead of devcontainers for better stability
FROM python:3.11-slim-bullseye

# Add cache-busting argument
ARG CACHE_BUST=1

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install minimal dependencies with explicit error handling
RUN set -e \
    && echo "Installing system packages..." \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
        sudo \
        procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && echo "System packages installed successfully."

# Create and configure non-root user
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 -m vscode \
    && echo vscode ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode \
    && mkdir -p /workspaces \
    && chown vscode:vscode /workspaces

# Switch to non-root user
USER vscode

# Set working directory
WORKDIR /workspaces/orchestra-main

# Verify essential functionality during build
RUN echo "Verifying Python installation..." \
    && python --version \
    && echo "Python installation verified."

# Reset to interactive mode
ENV DEBIAN_FRONTEND=dialog
