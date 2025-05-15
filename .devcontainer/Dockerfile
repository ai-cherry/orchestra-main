FROM python:3.11-slim-bullseye

# Keep environment variables consistent during build
ENV PYTHONUNBUFFERED=1

# Install additional system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        lsof \
        curl \
        git \
        sudo \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install mypy for static type checking
RUN pip install --no-cache-dir mypy

# Install Node.js and pnpm (using ARG for version)
ARG NODE_VERSION=22.15.0
RUN curl -fsSL https://unpkg.com/@pnpm/self-installer | node \
    && corepack enable pnpm \
    && npm config set update-notifier false \
    && npm install -g npm@latest

# Create a non-root user - this is required for DevContainer to work properly
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    # Add sudo support for non-root user
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

WORKDIR /workspaces/orchestra-main

# Set Python path for imports
ENV PYTHONPATH=/workspaces/orchestra-main
# Force standard mode
ENV USE_RECOVERY_MODE=false
ENV STANDARD_MODE=true
ENV ENVIRONMENT=development

# Final settings
ENV DEBIAN_FRONTEND=dialog

# Set the default user - this ensures we don't run as root
USER $USERNAME
ENV PATH="/usr/local/py-utils/bin:${PATH}"
