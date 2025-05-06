#!/bin/bash
# Setup script for Orchestra integrations with SuperAGI, AutoGen, LangChain, and Vertex AI
# This script installs required dependencies and configures the integration components

set -e

# Configuration
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}
REGION=${REGION:-"us-central1"}
INTEGRATION_CONFIG_FILE="./config/integrations.yaml"
GEMINI_MODEL=${GEMINI_MODEL:-"gemini-2.5-pro"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Orchestra Integration Setup ===${NC}"
echo "This script will set up integrations with SuperAGI, AutoGen, LangChain, and Vertex AI"

# Check for required tools
check_dependencies() {
    echo -e "\n${BLUE}Checking dependencies...${NC}"
    
    local missing_deps=0
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}Error: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
        missing_deps=1
    fi
    
    if ! command -v terraform &> /dev/null; then
        echo -e "${YELLOW}Warning: terraform not found. Terraform deployment will be skipped.${NC}"
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 not found. Please install Python 3.8 or higher.${NC}"
        missing_deps=1
    else
        python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        echo -e "Python version: ${python_version}"
        
        if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'; then
            echo -e "${GREEN}Python version requirement met.${NC}"
        else
            echo -e "${RED}Error: Python 3.8 or higher is required.${NC}"
            missing_deps=1
        fi
    fi
    
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}Error: pip3 not found. Please install pip.${NC}"
        missing_deps=1
    fi
    
    if [ $missing_deps -eq 1 ]; then
        echo -e "${RED}Please install missing dependencies and run again.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}All required dependencies found.${NC}"
}

# Authenticate with Google Cloud if needed
setup_gcp_auth() {
    echo -e "\n${BLUE}Setting up Google Cloud authentication...${NC}"
    
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${YELLOW}No project ID found. Please set PROJECT_ID environment variable or run 'gcloud config set project YOUR_PROJECT_ID'${NC}"
        read -p "Enter Google Cloud project ID: " PROJECT_ID
        gcloud config set project "$PROJECT_ID"
    fi
    
    # Check if already authenticated
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
        echo -e "${GREEN}Already authenticated with Google Cloud.${NC}"
    else
        echo -e "${YELLOW}Not authenticated with Google Cloud. Initiating login...${NC}"
        gcloud auth login
    fi
    
    # Enable required APIs
    echo -e "\n${BLUE}Enabling required Google Cloud APIs...${NC}"
    apis=(
        "aiplatform.googleapis.com"         # Vertex AI
        "secretmanager.googleapis.com"      # Secret Manager
        "redis.googleapis.com"              # Redis
        "alloydb.googleapis.com"            # AlloyDB
        "bigquery.googleapis.com"           # BigQuery
        "monitoring.googleapis.com"         # Cloud Monitoring
        "iam.googleapis.com"                # IAM
        "artifactregistry.googleapis.com"   # Artifact Registry
    )
    
    for api in "${apis[@]}"; do
        echo "Enabling $api..."
        gcloud services enable "$api" --project="$PROJECT_ID"
    done
    
    echo -e "${GREEN}All required APIs enabled.${NC}"
}

# Install required Python packages
install_python_packages() {
    echo -e "\n${BLUE}Installing required Python packages...${NC}"
    
    # Create requirements file
    cat > integration_requirements.txt << EOF
# Core dependencies
pyyaml>=6.0
requests>=2.28.0
aiohttp>=3.8.4
protobuf>=4.21.0

# Google Cloud dependencies
google-cloud-aiplatform>=1.26.0
google-cloud-storage>=2.7.0
google-cloud-bigquery>=3.3.5
google-cloud-secret-manager>=2.15.1
vertexai>=1.32.0

# LangChain dependencies
langchain>=0.1.0
langchain-community>=0.1.0
langchain-chroma>=0.0.13
langchain-core>=0.1.13
langchain-google-vertexai>=0.1.0

# SuperAGI dependencies
superagi-client>=0.1.1

# AutoGen dependencies
pyautogen>=0.2.3

# Vector embedding dependencies
transformers>=4.30.2
torch>=2.0.1
chromadb>=0.4.6
EOF

    echo "Installing packages from integration_requirements.txt..."
    pip3 install -r integration_requirements.txt
    
    echo -e "${GREEN}All required Python packages installed.${NC}"
}

# Create configuration directory if it doesn't exist
setup_config_directory() {
    echo -e "\n${BLUE}Setting up configuration directory...${NC}"
    
    mkdir -p "$(dirname "$INTEGRATION_CONFIG_FILE")"
    
    echo -e "${GREEN}Configuration directory created.${NC}"
}

# Create integration configuration file
create_integration_config() {
    echo -e "\n${BLUE}Creating integration configuration file...${NC}"
    
    cat > "$INTEGRATION_CONFIG_FILE" << EOF
# Orchestra Integration Configuration
project_id: "$PROJECT_ID"
region: "$REGION"

# Gemini Context Manager
gemini_context_manager:
  enabled: true
  model: "$GEMINI_MODEL"
  max_tokens: 2000000  # 2M tokens
  token_estimator: "transformers"  # Use transformers for token estimation
  priority_threshold: 0.7

# SuperAGI Integration
superagi:
  enabled: false  # Set to true to enable
  api_url: "https://api.superagi.com/v1"
  # API key will be fetched from Secret Manager

# AutoGen Integration
autogen:
  enabled: false  # Set to true to enable
  default_llm: "gpt-4o"
  max_rounds: 10
  speaker_selection: "auto"

# LangChain Integration
langchain:
  enabled: false  # Set to true to enable
  use_entity_memory: true
  use_summary_memory: true
  use_vectorstore: true
  collection_name: "orchestra_memories"
  embedding_model: "textembedding-gecko@latest"

# Vertex AI Integration
vertex_ai:
  enabled: true
  model: "gemini-2.5-pro"
EOF

    echo -e "${GREEN}Integration configuration file created at ${INTEGRATION_CONFIG_FILE}${NC}"
}

# Test Gemini Context Manager
test_gemini_context_manager() {
    echo -e "\n${BLUE}Testing Gemini Context Manager...${NC}"
    
    # Create test script
    cat > test_gemini_context.py << EOF
#!/usr/bin/env python3
import asyncio
import os
import sys
import yaml
from datetime import datetime

# Adjust path to import packages
sys.path.append(os.getcwd())

from packages.shared.src.memory.gemini_context_manager import GeminiContextManager
from packages.shared.src.models.base_models import MemoryItem

async def test_gemini_context():
    print("Initializing Gemini Context Manager...")
    
    # Load config
    with open('$INTEGRATION_CONFIG_FILE', 'r') as f:
        config = yaml.safe_load(f)
    
    gemini_config = config.get('gemini_context_manager', {})
    
    # Initialize context manager
    context_manager = GeminiContextManager(gemini_config)
    initialized = await context_manager.initialize()
    
    if not initialized:
        print("Failed to initialize Gemini Context Manager")
        return False
    
    # Create test memory item
    test_item = MemoryItem(
        user_id="test_user",
        session_id="test_session",
        item_type="conversation",
        persona_active="default",
        text_content="This is a test memory item for Gemini Context Manager",
        timestamp=datetime.now(),
        metadata={"source": "test"}
    )
    
    # Add to context
    print("Adding test memory item to context...")
    result = await context_manager.add_to_context(test_item, priority=0.8)
    
    if not result:
        print("Failed to add memory item to context")
        return False
    
    # Retrieve from context
    print("Retrieving memories from context...")
    memories = await context_manager.get_relevant_context("test", user_id="test_user")
    
    # Check results
    if len(memories) == 0:
        print("No memories retrieved from context")
        return False
    
    print(f"Retrieved {len(memories)} memories from context")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_gemini_context())
    sys.exit(0 if result else 1)
EOF

    # Run test
    python3 test_gemini_context.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Gemini Context Manager test passed.${NC}"
    else
        echo -e "${RED}Gemini Context Manager test failed.${NC}"
    fi
    
    # Clean up
    rm test_gemini_context.py
}

# Setup Terraform for infrastructure
setup_terraform() {
    if ! command -v terraform &> /dev/null; then
        echo -e "${YELLOW}Terraform not found. Skipping infrastructure setup.${NC}"
        return
    }
    
    echo -e "\n${BLUE}Setting up Terraform infrastructure...${NC}"
    
    # Create terraform.tfvars file
    cat > terraform/terraform.tfvars << EOF
# Orchestra Integration Infrastructure Configuration
project_id = "$PROJECT_ID"
region = "$REGION"
prefix = "orchestra"
environment = "dev"

# Enable components
enable_gemini_context_manager = true
enable_superagi_integration = false
enable_autogen_integration = false
enable_langchain_integration = false
enable_vertex_ai_integration = true

# Resource configuration
redis_memory_size_gb = 10
alloydb_replica_count = 3
EOF

    echo -e "${GREEN}Terraform configuration created.${NC}"
    echo -e "${YELLOW}To deploy infrastructure, navigate to terraform/ directory and run 'terraform init' followed by 'terraform apply'${NC}"
}

# Create a shell script to set environment variables
create_env_script() {
    echo -e "\n${BLUE}Creating environment variable script...${NC}"
    
    cat > set_integration_env.sh << EOF
#!/bin/bash
# Environment variables for Orchestra integrations

# Google Cloud
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
export GOOGLE_CLOUD_REGION="$REGION"

# Gemini
export GEMINI_API_KEY="\$(gcloud secrets versions access latest --secret=gemini-api-key)"
export GEMINI_MODEL="$GEMINI_MODEL"

# Paths
export INTEGRATION_CONFIG_FILE="$INTEGRATION_CONFIG_FILE"

echo "Environment variables set for Orchestra integrations"
EOF

    chmod +x set_integration_env.sh
    
    echo -e "${GREEN}Environment script created at ./set_integration_env.sh${NC}"
    echo -e "${YELLOW}Run 'source ./set_integration_env.sh' to set environment variables${NC}"
}

# Main execution
main() {
    check_dependencies
    setup_gcp_auth
    install_python_packages
    setup_config_directory
    create_integration_config
    test_gemini_context_manager
    setup_terraform
    create_env_script
    
    echo -e "\n${GREEN}=============================================================${NC}"
    echo -e "${GREEN}Orchestra integration setup completed successfully!${NC}"
    echo -e "${GREEN}=============================================================${NC}"
    echo -e "Next steps:"
    echo -e "1. ${YELLOW}Source the environment script:${NC} source ./set_integration_env.sh"
    echo -e "2. ${YELLOW}Deploy infrastructure:${NC} cd terraform && terraform init && terraform apply"
    echo -e "3. ${YELLOW}Edit configuration file:${NC} $INTEGRATION_CONFIG_FILE"
    echo -e "4. ${YELLOW}Test specific integrations:${NC} python3 ./scripts/test_integrations.py"
}

# Run main function
main
