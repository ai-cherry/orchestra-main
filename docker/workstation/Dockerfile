# AI Orchestra GCP Workstation Container Image
# This Dockerfile creates a container image for the AI Orchestra GCP Workstations

# Use the official Debian-based Python image
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PATH="$POETRY_HOME/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    openssh-client \
    sudo \
    vim \
    nano \
    less \
    nodejs \
    npm \
    graphviz \
    jq \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud SDK
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && \
    apt-get install -y google-cloud-sdk google-cloud-sdk-gke-gcloud-auth-plugin

# Install Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && apt-get install -y docker-ce-cli

# Install Terraform CLI
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add - && \
    apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main" && \
    apt-get update && apt-get install -y terraform

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Create a non-root user
RUN useradd -m -s /bin/bash -N -u 1000 user && \
    echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/user && \
    chmod 0440 /etc/sudoers.d/user

# Set up the orchestra directory
RUN mkdir -p /home/user/orchestra && \
    chown -R user:user /home/user/orchestra

# Install common Python packages
RUN pip install --no-cache-dir --upgrade \
    pip \
    setuptools \
    wheel \
    ipython \
    jupyter \
    pytest \
    pytest-asyncio \
    black \
    isort \
    mypy \
    flake8 \
    google-cloud-storage \
    google-cloud-secret-manager \
    google-cloud-aiplatform \
    fastapi \
    uvicorn \
    httpx \
    python-dotenv \
    pydantic \
    pyyaml \
    pendulum \
    rich \
    typer

# Create scripts directory
RUN mkdir -p /opt/orchestra/scripts && \
    chmod 755 /opt/orchestra/scripts

# Copy startup script
COPY startup.sh /opt/orchestra/startup.sh
RUN chmod +x /opt/orchestra/startup.sh

# Copy utility scripts
COPY scripts/ /opt/orchestra/scripts/
RUN chmod +x /opt/orchestra/scripts/*.sh

# Set working directory
WORKDIR /home/user/orchestra

# Switch to the non-root user
USER user

# Create a welcome message
RUN echo 'echo "Welcome to AI Orchestra Development Environment"' >> /home/user/.bashrc && \
    echo 'echo "Project: ${PROJECT_ID}"' >> /home/user/.bashrc && \
    echo 'echo "Environment: ${ENV}"' >> /home/user/.bashrc && \
    echo 'echo "Region: ${REGION}"' >> /home/user/.bashrc && \
    echo 'echo "Type \"orchestra-help\" for available commands"' >> /home/user/.bashrc && \
    echo 'alias orchestra-help="cat /opt/orchestra/scripts/help.txt"' >> /home/user/.bashrc && \
    echo 'alias orchestrate="/opt/orchestra/scripts/orchestrate.sh"' >> /home/user/.bashrc

# Default command
CMD ["/bin/bash"]