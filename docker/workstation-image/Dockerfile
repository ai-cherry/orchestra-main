# Performance-optimized container image for GCP Cloud Workstations
# Based on the Google Cloud Workstations code-oss base image

FROM us-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest

# Set environment variables for improved performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    NODE_OPTIONS="--max-old-space-size=8192" \
    DEBIAN_FRONTEND="noninteractive" \
    TZ="UTC"

# Install build dependencies and common tools in a single layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    jq \
    zsh \
    vim \
    tmux \
    nodejs \
    npm \
    build-essential \
    libssl-dev \
    libffi-dev \
    ca-certificates \
    gnupg \
    lsb-release \
    apt-transport-https \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud CLI
RUN curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir=/usr/local
ENV PATH $PATH:/usr/local/google-cloud-sdk/bin

# Install and upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Install Poetry for package management (AI Orchestra standard)
RUN curl -sSL https://install.python-poetry.org | python3 - --version 1.4.2 \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Install common Python packages for AI Orchestra development
RUN pip3 install --no-cache-dir \
    google-cloud-firestore \
    google-cloud-aiplatform \
    google-cloud-storage \
    google-cloud-secretmanager \
    numpy \
    pandas \
    fastapi \
    uvicorn \
    httpx \
    pydantic \
    pydantic-settings \
    pytest \
    black \
    isort \
    mypy \
    ruff

# Install VS Code extensions
RUN code-server --install-extension ms-python.python \
    && code-server --install-extension ms-azuretools.vscode-docker \
    && code-server --install-extension ms-toolsai.jupyter \
    && code-server --install-extension googlecloudtools.cloudcode \
    && code-server --install-extension hashicorp.terraform \
    && code-server --install-extension esbenp.prettier-vscode \
    && code-server --install-extension eamodio.gitlens \
    && code-server --install-extension ms-python.vscode-pylance \
    && code-server --install-extension matangover.mypy \
    && code-server --install-extension charliermarsh.ruff \
    && code-server --install-extension github.copilot \
    && code-server --install-extension github.vscode-github-actions

# Setup MCP memory system directory
RUN mkdir -p /home/user/.ai-memory

# Setup optimized zsh with Oh My Zsh for better developer experience
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended \
    && sed -i 's/ZSH_THEME="robbyrussell"/ZSH_THEME="agnoster"/' /root/.zshrc \
    && echo 'export PATH=$PATH:/home/user/.local/bin' >> /root/.zshrc \
    && echo 'alias python=python3' >> /root/.zshrc

# Copy customized VS Code settings for performance
COPY settings.json /home/user/.vscode-server/data/Machine/settings.json

# Create development workspace directory
RUN mkdir -p /home/user/persistent/ai-orchestra

# Create build cache directories for improved performance
RUN mkdir -p /home/user/persistent/.cache/pip \
    && mkdir -p /home/user/persistent/.cache/npm \
    && mkdir -p /home/user/persistent/.cache/yarn \
    && mkdir -p /home/user/persistent/.cache/go-build

# Set symbolic links to persistent cache directories
RUN ln -s /home/user/persistent/.cache/pip /root/.cache/pip \
    && ln -s /home/user/persistent/.cache/npm /root/.cache/npm \
    && ln -s /home/user/persistent/.cache/yarn /root/.cache/yarn \
    && ln -s /home/user/persistent/.cache/go-build /root/.cache/go-build

# Install performance monitoring tools
RUN pip3 install --no-cache-dir glances py-spy memory-profiler

# Install NodeJS performance tools
RUN npm install -g lighthouse autocannon clinic

# Set working directory
WORKDIR /home/user/persistent

# Copy startup script
COPY startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

# Set the ENTRYPOINT to our startup script
ENTRYPOINT ["/usr/local/bin/startup.sh"]