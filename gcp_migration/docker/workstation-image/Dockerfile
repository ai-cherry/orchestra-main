# Performance-optimized container image for GCP Cloud Workstations
# This container includes all necessary tools for AI Orchestra development

FROM us-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest

# Set environment variables for improved performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=0 \
    NODE_OPTIONS="--max-old-space-size=8192" \
    DEBIAN_FRONTEND="noninteractive" \
    TZ="UTC" \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.6.1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PATH="/opt/poetry/bin:$PATH"

# Install common tools and dependencies in a single layer to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    gnupg \
    jq \
    libffi-dev \
    libssl-dev \
    lsb-release \
    nodejs \
    npm \
    python3-dev \
    python3-pip \
    python3-venv \
    software-properties-common \
    tmux \
    vim \
    wget \
    zsh \
    apt-transport-https \
    ca-certificates \
    # Performance monitoring tools
    htop \
    iotop \
    # Network tools
    net-tools \
    netcat \
    dnsutils \
    # Additional utilities
    unzip \
    zip \
    rsync \
    parallel \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install latest Git (for better performance and features)
RUN add-apt-repository ppa:git-core/ppa -y && \
    apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Google Cloud CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-cli google-cloud-cli-gke-gcloud-auth-plugin && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.create true && \
    poetry config virtualenvs.in-project true

# Add terraform and kubectl
RUN wget -O- https://apt.releases.hashicorp.com/gpg | \
    gpg --dearmor | \
    tee /usr/share/keyrings/hashicorp-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
    https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
    tee /etc/apt/sources.list.d/hashicorp.list && \
    apt-get update && apt-get install -y terraform && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install common Python packages for AI Orchestra development
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir \
    google-cloud-firestore \
    google-cloud-aiplatform \
    google-cloud-storage \
    google-cloud-secretmanager \
    # AI/ML packages
    numpy \
    pandas \
    # Web frameworks
    fastapi \
    uvicorn \
    httpx \
    # Utilities
    pydantic \
    pydantic-settings \
    python-dotenv \
    rich \
    typer \
    # Testing and linting
    pytest \
    pytest-asyncio \
    black \
    isort \
    mypy \
    ruff \
    # Performance testing
    memory-profiler \
    py-spy

# Install VS Code extensions for better developer experience
RUN code-server --install-extension ms-python.python && \
    code-server --install-extension ms-azuretools.vscode-docker && \
    code-server --install-extension ms-toolsai.jupyter && \
    code-server --install-extension googlecloudtools.cloudcode && \
    code-server --install-extension hashicorp.terraform && \
    code-server --install-extension esbenp.prettier-vscode && \
    code-server --install-extension ms-python.vscode-pylance && \
    code-server --install-extension ms-python.black-formatter && \
    code-server --install-extension ms-python.isort && \
    code-server --install-extension github.vscode-github-actions && \
    # AI coding assistants
    code-server --install-extension anthropic.claude && \
    code-server --install-extension google.cloud-code-ai && \
    # Performance optimizations
    code-server --install-extension eamodio.gitlens && \
    # Disable telemetry for all extensions
    mkdir -p /home/user/.vscode-server/data/Machine && \
    echo '{"telemetry.telemetryLevel": "off"}' > /home/user/.vscode-server/data/Machine/settings.json

# Setup MCP memory system directory
RUN mkdir -p /home/user/.ai-memory

# Setup optimized zsh with Oh My Zsh for better developer experience
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended && \
    sed -i 's/ZSH_THEME="robbyrussell"/ZSH_THEME="agnoster"/' /root/.zshrc && \
    echo 'export PATH=$PATH:/home/user/.local/bin' >> /root/.zshrc && \
    echo 'alias python=python3' >> /root/.zshrc

# Add improved git configuration
RUN git config --system credential.helper store && \
    git config --system pull.rebase true && \
    git config --system fetch.prune true && \
    git config --system core.compression 9 && \
    git config --system core.bigFileThreshold 10m && \
    git config --system pack.threads 4 && \
    git config --system pack.deltaCacheSize 2047m && \
    git config --system pack.windowMemory 2047m && \
    git config --system feature.manyFiles true

# Copy VS Code settings for performance optimization
COPY settings.json /home/user/.vscode-server/data/Machine/settings.json

# Create development workspace directory and persistent cache directories
RUN mkdir -p /home/user/persistent/ai-orchestra && \
    mkdir -p /home/user/persistent/.cache/pip && \
    mkdir -p /home/user/persistent/.cache/npm && \
    mkdir -p /home/user/persistent/.cache/yarn && \
    mkdir -p /home/user/persistent/.cache/go-build && \
    mkdir -p /home/user/persistent/.vscode-server/extensions

# Set symbolic links to persistent cache directories
RUN rm -rf /root/.cache/pip && ln -s /home/user/persistent/.cache/pip /root/.cache/pip && \
    rm -rf /root/.cache/npm && ln -s /home/user/persistent/.cache/npm /root/.cache/npm && \
    rm -rf /root/.cache/yarn && ln -s /home/user/persistent/.cache/yarn /root/.cache/yarn && \
    rm -rf /root/.cache/go-build && ln -s /home/user/persistent/.cache/go-build /root/.cache/go-build && \
    rm -rf /home/user/.vscode-server/extensions && ln -s /home/user/persistent/.vscode-server/extensions /home/user/.vscode-server/extensions

# Performance monitoring tools
RUN pip3 install --no-cache-dir glances

# Set working directory
WORKDIR /home/user/persistent

# Copy startup script
COPY startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

# Create welcome message
RUN echo "# Welcome to GCP Workstations\n\nThis environment is optimized for AI Orchestra development.\n\n## Getting Started\n\n1. Clone your repository: \`git clone https://github.com/your-org/ai-orchestra.git\`\n2. Open the project in VS Code\n3. Start developing!\n" > /home/user/persistent/WELCOME.md

# Set the ENTRYPOINT to our startup script
ENTRYPOINT ["/usr/local/bin/startup.sh"]
