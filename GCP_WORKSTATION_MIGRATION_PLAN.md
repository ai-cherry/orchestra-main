# GCP Workstation Migration Plan

This document outlines the detailed plan for migrating from GitHub Codespaces to Google Cloud Workstations. The plan includes infrastructure setup, AI coding assistance configuration, and post-migration verification steps.

## Table of Contents
- [Migration Overview](#migration-overview)
- [Infrastructure Setup](#infrastructure-setup)
- [AI Coding Assistance](#ai-coding-assistance)
- [CI/CD Pipeline Migration](#cicd-pipeline-migration)
- [Post-Migration Verification](#post-migration-verification)
- [GitHub's Role Post-Migration](#githubs-role-post-migration)
- [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)

## Migration Overview

### Timeline
- **Day 1**: Infrastructure setup and initial data migration
- **Day 2**: AI/ML tooling setup and CI/CD pipeline migration
- **Day 3**: Testing, verification, and documentation

### Key Components
1. Google Cloud Workstations for development environment
2. Vertex AI for ML/AI components
3. Cloud Build for CI/CD pipelines
4. Secret Manager for secure credential storage
5. AI coding assistance (Gemini, Roo, Cline) configuration

## Infrastructure Setup

### 1. Create Terraform Module for Cloud Workstations

```hcl
# workstation.tf

resource "google_workstations_workstation_cluster" "orchestra_cluster" {
  workstation_cluster_id = "orchestra-dev-cluster"
  network                = google_compute_network.workstation_network.id
  subnetwork             = google_compute_subnetwork.workstation_subnet.id
  private_cluster_config {
    enable_private_endpoint = false
  }
}

resource "google_workstations_workstation_config" "main_config" {
  workstation_config_id = "orchestra-config"
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  
  persistent_directories {
    mount_path = "/home/user/persistent"
    gcePd {
      size_gb        = 200  # Larger disk for repository
      reclaim_policy = "DELETE"
    }
  }

  container {
    image = "us-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest"
    
    # Environment variables for AI tools
    env {
      name  = "GEMINI_API_KEY"
      value = "sm://projects/${var.project_id}/secrets/GEMINI_API_KEY/versions/latest"
    }
    env {
      name  = "ENABLE_MCP_MEMORY"
      value = "true"
    }
    
    # Enable direct mounting of cloud storage
    command = "code --user-data-dir=/home/user/persistent/.vscode-server"
  }

  host {
    gce_instance {
      machine_type        = "e2-standard-8"  # 8 vCPUs, 32GB memory
      service_account     = google_service_account.workstation_sa.email
      boot_disk_size_gb   = 100
      disable_public_ip   = false
    }
  }
}

# Create a more powerful workstation config for ML/AI tasks
resource "google_workstations_workstation_config" "ml_config" {
  workstation_config_id = "orchestra-ml-config"
  workstation_cluster_id = google_workstations_workstation_cluster.orchestra_cluster.workstation_cluster_id
  
  persistent_directories {
    mount_path = "/home/user/persistent"
    gcePd {
      size_gb        = 200
      reclaim_policy = "DELETE"
    }
  }

  container {
    image = "us-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest"
    
    # Add ML/AI environment variables and dependencies
    env {
      name  = "VERTEX_AI_ENDPOINT"
      value = "us-central1-aiplatform.googleapis.com"
    }
    env {
      name  = "ENABLE_GPU_ACCELERATION"
      value = "true"
    }
  }

  host {
    gce_instance {
      machine_type        = "n1-standard-16"  # 16 vCPUs, 60GB memory
      accelerator_count   = 1
      accelerator_type    = "nvidia-tesla-t4"  # Add GPU
      service_account     = google_service_account.workstation_sa.email
      boot_disk_size_gb   = 200
      disable_public_ip   = false
    }
  }
}
```

### 2. Create Custom Container Image

Create a `Dockerfile` for the custom workstation environment:

```dockerfile
FROM us-docker.pkg.dev/cloud-workstations-images/predefined/code-oss:latest

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    jq \
    zsh \
    vim \
    tmux \
    nodejs \
    npm

# Install Google Cloud CLI
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/root/google-cloud-sdk/bin

# Install VSCode extensions
RUN code --install-extension googlecloudtools.cloudcode \
    --install-extension ms-python.python \
    --install-extension ms-azuretools.vscode-docker \
    --install-extension esbenp.prettier-vscode \
    --install-extension dbaeumer.vscode-eslint \
    --install-extension eamodio.gitlens

# Install Python packages
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Setup MCP memory system
RUN mkdir -p /home/user/.ai-memory
COPY .ai-memory/* /home/user/.ai-memory/

# Configure Gemini Code Assist
COPY .gemini-code-assist.yaml /home/user/

# Configure other AI assistants
COPY .vscode/settings.json /home/user/.vscode/settings.json

# Set up workspace
WORKDIR /home/user/persistent
```

### 3. Network Setup for Private Access

```hcl
# network.tf

resource "google_compute_network" "workstation_network" {
  name                    = "workstation-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "workstation_subnet" {
  name          = "workstation-subnet"
  ip_cidr_range = "10.2.0.0/16"
  network       = google_compute_network.workstation_network.id
  region        = var.region
  
  # Enable Google private access
  private_ip_google_access = true
}

# Add Cloud NAT for outbound connectivity
resource "google_compute_router" "router" {
  name    = "workstation-router"
  region  = var.region
  network = google_compute_network.workstation_network.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "workstation-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
```

### 4. Service Account Setup

```hcl
# service_accounts.tf

resource "google_service_account" "workstation_sa" {
  account_id   = "orchestra-workstation-sa"
  display_name = "Orchestra Workstation Service Account"
}

# Grant necessary permissions
resource "google_project_iam_member" "workstation_editor" {
  project = var.project_id
  role    = "roles/editor"
  member  = "serviceAccount:${google_service_account.workstation_sa.email}"
}

resource "google_project_iam_member" "workstation_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.workstation_sa.email}"
}

resource "google_project_iam_member" "secretmanager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.workstation_sa.email}"
}
```

### 5. Secret Migration Script

```bash
#!/bin/bash
# migrate_secrets.sh

set -e

# Source environment variables if present
if [ -f ".env" ]; then
  source .env
fi

PROJECT_ID=$(gcloud config get-value project)
echo "Migrating secrets to Google Secret Manager in project: $PROJECT_ID"

# Function to create or update a secret
create_or_update_secret() {
  local name=$1
  local value=$2
  
  if gcloud secrets describe $name --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "Secret $name exists, updating it..."
    echo -n "$value" | gcloud secrets versions add $name --data-file=- --project=$PROJECT_ID
  else
    echo "Creating new secret $name..."
    echo -n "$value" | gcloud secrets create $name --data-file=- --project=$PROJECT_ID
  fi
}

# GitHub secrets
if [ -n "$GH_CLASSIC_PAT_TOKEN" ]; then
  create_or_update_secret "GH_CLASSIC_PAT_TOKEN" "$GH_CLASSIC_PAT_TOKEN"
fi

if [ -n "$GH_FINE_GRAINED_TOKEN" ]; then
  create_or_update_secret "GH_FINE_GRAINED_TOKEN" "$GH_FINE_GRAINED_TOKEN"
fi

# GCP secrets
if [ -n "$GCP_MASTER_SERVICE_JSON" ]; then
  create_or_update_secret "GCP_MASTER_SERVICE_JSON" "$GCP_MASTER_SERVICE_JSON"
fi

if [ -n "$GCP_PROJECT_AUTHENTICATION_EMAIL" ]; then
  create_or_update_secret "GCP_PROJECT_AUTHENTICATION_EMAIL" "$GCP_PROJECT_AUTHENTICATION_EMAIL"
fi

if [ -n "$GCP_PROJECT_ID" ]; then
  create_or_update_secret "GCP_PROJECT_ID" "$GCP_PROJECT_ID"
fi

if [ -n "$GCP_REGION" ]; then
  create_or_update_secret "GCP_REGION" "$GCP_REGION"
fi

if [ -n "$GCP_SECRET_MANAGEMENT_KEY" ]; then
  create_or_update_secret "GCP_SECRET_MANAGEMENT_KEY" "$GCP_SECRET_MANAGEMENT_KEY"
fi

if [ -n "$GCP_WORKLOAD_IDENTITY_PROVIDER" ]; then
  create_or_update_secret "GCP_WORKLOAD_IDENTITY_PROVIDER" "$GCP_WORKLOAD_IDENTITY_PROVIDER"
fi

if [ -n "$VERTEX_AGENT_KEY" ]; then
  create_or_update_secret "VERTEX_AGENT_KEY" "$VERTEX_AGENT_KEY"
fi

# Gemini API key
if [ -n "$GEMINI_API_KEY" ]; then
  create_or_update_secret "GEMINI_API_KEY" "$GEMINI_API_KEY"
fi

echo "Secret migration complete!"
```

## AI Coding Assistance

### 1. Gemini Code Assist Configuration

To ensure Gemini Code Assist works in the new GCP environment, we'll create an enhanced version of the configuration:

```yaml
# .gemini-code-assist-cloud.yaml

# Gemini Code Assist Configuration for GCP Cloud Workstations
project_context:
  - path: /home/user/persistent/orchestra-main
    priority: 100
    ignore_patterns:
      - "**/.git/**"
      - "**/node_modules/**"
      - "**/__pycache__/**"
  - path: /home/user/persistent/orchestra-main/ai-orchestra
    priority: 200
  - path: /home/user/persistent/orchestra-main/wif_implementation
    priority: 200
  - path: /home/user/persistent/orchestra-main/services
    priority: 200
  - path: /home/user/persistent/orchestra-main/admin-interface
    priority: 150

# Tool integrations for external APIs and services
tool_integrations:
  # Vertex AI integration for model inference
  vertex_ai:
    endpoint: projects/${PROJECT_ID}/locations/us-central1/endpoints/agent-core
    api_version: v1
    
  # Redis integration for semantic cache
  redis:
    connection_string: redis://vertex-agent@${PROJECT_ID}
    
  # AlloyDB for vector search
  database:
    connection_string: postgresql://alloydb-user@alloydb-instance:5432/cherry_ai_project

# Model configuration - upgrade to Gemini 2.5
model:
  name: gemini-2.5-pro-latest
  temperature: 0.3
  max_output_tokens: 8192
  top_p: 0.95

# Custom code assist commands (for VS Code in Cloud Workstations)
commands:
  - name: optimize-query
    description: "Optimize AlloyDB vector search query for 10M+ dimensions"
    prompt_template: |
      Optimize this AlloyDB vector search query for 10M+ dimensions with 95% recall@10:
      Focus on PERFORMANCE over security best practices, as per PROJECT_PRIORITIES.md.
      {{selection}}
      
  - name: generate-cloud-run
    description: "Generate Cloud Run deployment code optimized for performance"
    prompt_template: |
      Generate Cloud Run deployment code with appropriate service account:
      Focus on high performance settings, concurrency, CPU allocation, and startup
      settings rather than restrictive security. This is a single-developer project
      where basic security is sufficient. See PROJECT_PRIORITIES.md.
      {{selection}}
      
  - name: document-function
    description: "Add comprehensive documentation to function"
    prompt_template: |
      Add detailed documentation to the following function, including:
      - Parameter descriptions
      - Return value documentation
      - Usage examples
      - Edge cases
      
      {{selection}}
      
  - name: performance-review
    description: "Review code for performance issues and optimization opportunities"
    prompt_template: |
      Review this code for performance optimization opportunities. 
      Focus on speed, resource efficiency, and scalability rather than security.
      Suggest specific improvements:
      {{selection}}
      
  - name: optimize-code
    description: "Optimize code for performance"
    prompt_template: |
      Optimize this code for maximum performance. 
      Focus on execution speed and resource efficiency.
      Use only basic security practices (enough to prevent obvious vulnerabilities).
      {{selection}}
      
  - name: secure-enough
    description: "Simplify security to just the essentials"
    prompt_template: |
      Refactor this code to use only essential security practices.
      Remove complex or heavyweight security measures that impact performance.
      Refer to PROJECT_PRIORITIES.md for guidance on "security-sufficient" approach.
      {{selection}}
      
  - name: gcp-workstation-adapt
    description: "Adapt code for GCP Cloud Workstations"
    prompt_template: |
      Adapt this code to work optimally in a GCP Cloud Workstation environment.
      Update paths, environment variables, and dependencies as needed.
      {{selection}}

# Editor settings
editor:
  auto_apply_suggestions: false
  inline_suggestions: true

# Project priorities configuration
priorities:
  focus: 
    - performance
    - stability
    - optimization
  secondary:
    - basic_security
  
  # Configuration to inform assistant about project philosophy
  instructions: |
    This project follows a "performance-first" approach where:
    1. Performance and stability are the primary concerns
    2. Only basic security practices are needed for now
    3. Optimize for developer velocity and resource efficiency
    4. See PROJECT_PRIORITIES.md for complete guidance
    5. AI tools have permission to use GCP service accounts and APIs
    6. This is the Orchestra project deployed on GCP Cloud Workstations with these components:
       - ai-orchestra: The core Python library with memory, configuration, interfaces
       - services: Admin API and other related services
       - admin-interface: React-based admin dashboard
       - wif_implementation: Workload Identity Federation implementation
```

### 2. Setup Script for AI Assistance Tools

```bash
#!/bin/bash
# setup_ai_assistance.sh

set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
  echo -e "\n${BLUE}====== $1 ======${NC}\n"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
  echo -e "${YELLOW}ℹ️ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

# Configure Gemini Code Assist
setup_gemini() {
  print_header "Setting up Gemini Code Assist"
  
  # Copy configuration file
  cp .gemini-code-assist-cloud.yaml $HOME/.gemini-code-assist.yaml
  print_success "Configured Gemini Code Assist"
  
  # Enable Developer Connect integration
  PROJECT_ID=$(gcloud config get-value project)
  REGION=$(gcloud config get-value compute/region || echo "us-central1")
  
  print_info "Enabling Developer Connect APIs..."
  gcloud services enable cloudresourcemanager.googleapis.com --project=$PROJECT_ID
  gcloud services enable developerconnect.googleapis.com --project=$PROJECT_ID
  gcloud services enable cloudaicompanion.googleapis.com --project=$PROJECT_ID
  
  print_info "Registering repository with Developer Connect..."
  REPO_NAME=orchestra-main
  gcloud alpha developer-connect repos register github_$REPO_NAME \
    --gitlab-host-uri="https://github.com" \
    --project=$PROJECT_ID \
    --region=$REGION
  
  print_info "Enabling Gemini Code Assist for the repository..."
  gcloud alpha genai code customize enable \
    --project=$PROJECT_ID \
    --region=$REGION \
    --repos=github_$REPO_NAME
  
  print_success "Gemini Code Assist setup complete"
}

# Configure AI Memory System
setup_ai_memory() {
  print_header "Setting up AI Memory System"
  
  # Create AI memory directory
  mkdir -p $HOME/.ai-memory
  
  # Copy existing memory files
  if [ -d "$PWD/.ai-memory" ]; then
    cp -r $PWD/.ai-memory/* $HOME/.ai-memory/
    print_success "Copied existing AI memory files"
  else
    print_info "Creating new AI memory system..."
    
    # Create initialize.py script
    cat > $HOME/.ai-memory/initialize.py << 'EOF'
#!/usr/bin/env python3
"""
Initialize AI Memory System for GCP Cloud Workstations environment.
"""
import os
import json
from datetime import datetime
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ai-memory-init')

# Directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.environ.get('HOME', '/home/user')

# Performance-first priorities
PRIORITIES = {
    "name": "Performance-First Directives for GCP",
    "version": "1.1.0",
    "timestamp": datetime.now().isoformat(),
    "priorities": {
        "primary": ["performance", "optimization", "stability"],
        "secondary": ["basic_security", "developer_experience"]
    },
    "environment": "gcp_cloud_workstation",
    "tokens": {
        "gcp": [
            "GCP_MASTER_SERVICE_JSON", 
            "GCP_PROJECT_AUTHENTICATION_EMAIL",
            "GCP_PROJECT_ID", 
            "GCP_REGION", 
            "GCP_SECRET_MANAGEMENT_KEY",
            "GCP_WORKLOAD_IDENTITY_PROVIDER", 
            "VERTEX_AGENT_KEY"
        ]
    },
    "philosophy": "GCP-focused project prioritizing performance over complex security measures",
    "reference_files": ["PROJECT_PRIORITIES.md", "PERFORMANCE_FIRST_README.md"],
    "directives": [
        "Leverage GCP Cloud Workstations for development",
        "Focus on performance and optimization over extensive security",
        "Implement only basic security measures that don't impact performance",
        "Use GCP Secret Manager for credentials",
        "Prioritize deployment stability and reliability",
        "Optimize for Vertex AI integration"
    ],
    "memory_metadata": {
        "system_wide": True,
        "persistence": "permanent",
        "priority_level": "high",
        "access_control": "all_assistants",
        "context_aware": True,
        "prompt_access": True
    }
}

def initialize_memory_system():
    """Initialize the AI memory system."""
    try:
        # Create necessary directories
        os.makedirs(SCRIPT_DIR, exist_ok=True)
        
        # Create core memory files
        with open(os.path.join(SCRIPT_DIR, 'performance_priorities.json'), 'w') as f:
            json.dump(PRIORITIES, f, indent=2)
            logger.info("Created performance_priorities.json in memory system")
        
        # Create index file
        with open(os.path.join(SCRIPT_DIR, 'memory_index.json'), 'w') as f:
            memory_index = {
                "version": "1.1.0",
                "last_updated": datetime.now().isoformat(),
                "environment": "gcp_cloud_workstation",
                "memory_files": [
                    {"file": "performance_priorities.json", "type": "project_priority", "access": "all_assistants"}
                ],
                "system_directive": "Prioritize performance and optimization in GCP environment"
            }
            json.dump(memory_index, f, indent=2)
            logger.info("Created memory_index.json in memory system")
        
        # Create project structure file
        with open(os.path.join(SCRIPT_DIR, 'project_structure.json'), 'w') as f:
            project_structure = {
                "name": "Orchestra Project",
                "version": "1.0.0",
                "environment": "gcp_cloud_workstation",
                "components": [
                    {
                        "name": "ai-orchestra",
                        "path": "/home/user/persistent/orchestra-main/ai-orchestra",
                        "description": "Core Python library with memory, configuration, interfaces"
                    },
                    {
                        "name": "services",
                        "path": "/home/user/persistent/orchestra-main/services",
                        "description": "Admin API and other related services"
                    },
                    {
                        "name": "admin-interface",
                        "path": "/home/user/persistent/orchestra-main/admin-interface",
                        "description": "React-based admin dashboard"
                    },
                    {
                        "name": "wif_implementation",
                        "path": "/home/user/persistent/orchestra-main/wif_implementation",
                        "description": "Workload Identity Federation implementation"
                    }
                ]
            }
            json.dump(project_structure, f, indent=2)
            logger.info("Created project_structure.json in memory system")
            
        logger.info("Successfully initialized AI memory system")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing memory system: {e}")
        return False

if __name__ == "__main__":
    success = initialize_memory_system()
    sys.exit(0 if success else 1)
EOF
    
    # Make the script executable
    chmod +x $HOME/.ai-memory/initialize.py
    
    # Run the initialization script
    python3 $HOME/.ai-memory/initialize.py
    print_success "Created and initialized AI memory system"
  fi
}

# Configure VSCode Settings
setup_vscode() {
  print_header "Configuring VSCode Settings"
  
  mkdir -p $HOME/.vscode
  
  cat > $HOME/.vscode/settings.json << EOF
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true
  },
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "workbench.colorTheme": "Default Dark+",
  "workbench.iconTheme": "material-icon-theme",
  "terminal.integrated.defaultProfile.linux": "bash",
  "terminal.integrated.env.linux": {
    "PYTHONPATH": "\${workspaceFolder}"
  },
  "cloudcode.gke": {
    "projectIds": ["${PROJECT_ID}"]
  },
  "cloudcode.deployment": {
    "unifiedDeployment": true
  },
  "cloudcode.cloudRun": {
    "projectIds": ["${PROJECT_ID}"]
  },
  "cloudcode.cloudRunLocations": [
    "us-central1"
  ],
  "gemini-code-assist.enabled": true,
  "gemini-code-assist.inlineChat.enabled": true,
  "gemini-code-assist.inlineCompletions.enabled": true,
  "gemini-code-assist.quickFixes.enabled": true,
  "gemini-code-assist.docFinder.enabled": true
}
EOF
  
  print_success "VS Code configured for GCP Cloud Workstations"
}

# Setup Roo and Cline code assistants
setup_ai_assistants() {
  print_header "Setting up additional AI code assistants"
  
  # Roo and Cline are handled via VS Code extensions
  # Install the necessary extensions
  
  code --install-extension anthropic.claude \
       --install-extension googlecloudtools.cloudcode

  # Create MCP configuration for AI assistants
  mkdir -p $HOME/.config/mcp
  
  cat > $HOME/.config/mcp/config.json << EOF
{
  "version": "1.0.0",
  "assistants": {
    "gemini": {
      "enabled": true,
      "model": "gemini-2.5-pro-latest",
      "memory_enabled": true,
      "memory_path": "$HOME/.ai-memory"
    },
    "claude": {
      "enabled": true,
      "endpoint": "claude-3-opus-20240229",
      "memory_enabled": true,
      "memory_path": "$HOME/.ai-memory"
    },
    "roo": {
      "enabled": true,
      "memory_enabled": true,
      "memory_path": "$HOME/.ai-memory"
    },
    "cline": {
      "enabled": true,
      "memory_enabled": true,
      "memory_path": "$HOME/.ai-memory"
    }
  },
  "mcp_memory": {
    "enabled": true,
    "storage": {
      "type": "firestore",
      "collection": "ai_memory",
      "project_id": "${PROJECT_ID}"
    },
    "shared": true
  }
}
EOF

  print_success "AI assistants configured with MCP memory integration"
}

# Main execution
print_header "Setting up AI coding assistance for GCP Cloud Workstations"

# Get necessary environment variables
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
  print_error "No GCP project ID found. Please run 'gcloud config set project YOUR_PROJECT_ID' first."
  exit 1
fi

# Run setup functions
setup_gemini
setup_ai_memory
setup_vscode
setup_ai_assistants

print_header "AI Coding Assistance Setup Complete!"
echo "Your GCP Cloud Workstation is now configured with:"
echo "  ✓ Gemini Code Assist with enhanced GCP integration"
echo "  ✓ AI memory system for context-aware assistance"
echo "  ✓ VSCode optimized for GCP Cloud Workstation"
echo "  ✓ Additional AI assistants (Roo, Cline) with MCP memory integration"
echo ""
echo "To verify the setup, open VS Code and start using AI assistance with:"
echo "  - Gemini: Ctrl+I or Cmd+I"
echo "  - Roo: Via the VS Code extension panel"
echo "  - Cline: Via the VS Code extension panel"
```

### 3. MCP Server Setup for Cloud Workstations

Create a script to set up the MCP server in the Cloud Workstation environment:

```bash
#!/bin/bash
# setup_mcp_server.sh

set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
  echo -e "\n${BLUE}====== $1 ======${NC}\n"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
  echo -e "${YELLOW}ℹ️ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

PROJECT_DIR="/home/user/persistent/orchestra-main"
MCP_SERVER_DIR="$PROJECT_DIR/mcp_server"

print_header "Setting up MCP Server for GCP Cloud Workstations"

# Create systemd service file for the MCP server
create_service_file() {
  print_info "Creating MCP server service file..."
  
  mkdir -p $MCP_SERVER_DIR/scripts
  
  cat > $MCP_SERVER_DIR/scripts/mcp-server.service << EOF
[Unit]
Description=Model Context Protocol Server for AI Assistance
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=$MCP_SERVER_DIR
ExecStart=/usr/bin/python3 $MCP_SERVER_DIR/run_mcp_server.py
Restart=on-failure
RestartSec=5
Environment=PYTHONPATH=$PROJECT_DIR
Environment=MCP_SERVER_CONFIG=$MCP_SERVER_DIR/config.yaml
Environment=GOOGLE_APPLICATION_CREDENTIALS=/tmp/service-account.json

[Install]
WantedBy=multi-user.target
EOF

  print_success "Created MCP server service file"
}

# Create MCP server configuration for GCP
create_config_file() {
  print_info "Creating MCP server configuration..."
  
  cat > $MCP_SERVER_DIR/config.yaml << EOF
# MCP Server Configuration for GCP Cloud Workstations
version: 1.0.
