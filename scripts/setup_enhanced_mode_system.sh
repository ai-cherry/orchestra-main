#!/usr/bin/env bash
# setup_enhanced_mode_system.sh - Initialize and configure the enhanced mode system
#
# This script sets up the enhanced mode system for AI Orchestra, ensuring
# configurations persist across restarts, rebuilds, and deployments by:
#
# 1. Installing required dependencies
# 2. Setting up necessary directory structure
# 3. Initializing GCP resources for persistence (Secret Manager, Cloud Storage, Firestore)
# 4. Configuring automatic startup for the persistence system
# 5. Setting up environment variables for the mode system
#
# The script uses GCP for robust persistence, with local fallbacks when offline.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ID=${PROJECT_ID:-"cherry-ai-project"}
ENVIRONMENT=${ENVIRONMENT:-"development"}
MODE_CONFIG_BUCKET="${PROJECT_ID}-mode-config"
MODE_CONFIG_SECRET="mode-system-config"
FIRESTORE_COLLECTION="mode_system_config"

# Check if we're running in a CI/CD environment
is_ci() {
  [ -n "${CI}" ] || [ -n "${GITHUB_ACTIONS}" ] || [ -n "${GITLAB_CI}" ] || [ -n "${BUILDKITE}" ]
}

# Banner
echo -e "${BLUE}======================================================${NC}"
echo -e "${BOLD}AI Orchestra Enhanced Mode System Setup${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}Project ID:${NC} ${PROJECT_ID}"
echo -e "${YELLOW}Environment:${NC} ${ENVIRONMENT}"
echo -e "${BLUE}======================================================${NC}"

# Create necessary directories
mkdir -p "${PROJECT_ROOT}/config/backups"
mkdir -p "${PROJECT_ROOT}/core/persistency"
mkdir -p "${PROJECT_ROOT}/tools"
mkdir -p "${PROJECT_ROOT}/docs"

echo -e "\n${GREEN}${BOLD}Step 1: Install required dependencies${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Install required Python packages
echo -e "${YELLOW}Installing required Python packages...${NC}"
pip3 install --quiet pyyaml colorama google-cloud-storage google-cloud-firestore google-cloud-secretmanager

# Check if we can authenticate with GCP
echo -e "\n${GREEN}${BOLD}Step 2: Check GCP authentication${NC}"
if command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}Checking GCP authentication...${NC}"
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
        echo -e "${GREEN}Authenticated with GCP as ${ACTIVE_ACCOUNT}${NC}"
        GCP_AVAILABLE=true
    else
        echo -e "${YELLOW}Not authenticated with GCP. Some persistence features may be limited.${NC}"
        echo -e "${YELLOW}To authenticate, run 'gcloud auth login'${NC}"
        GCP_AVAILABLE=false
    fi
else
    echo -e "${YELLOW}gcloud CLI not found. Some persistence features may be limited.${NC}"
    GCP_AVAILABLE=false
fi

# Check for mode configuration file
echo -e "\n${GREEN}${BOLD}Step 3: Verify mode configuration${NC}"
MODE_CONFIG_PATH="${PROJECT_ROOT}/config/mode_definitions.yaml"

if [ -f "${MODE_CONFIG_PATH}" ]; then
    echo -e "${GREEN}Mode configuration file found at ${MODE_CONFIG_PATH}${NC}"
else
    echo -e "${YELLOW}Mode configuration file not found. Creating default configuration...${NC}"
    cat > "${MODE_CONFIG_PATH}" << EOL
# AI Orchestra Mode Definitions
# Default configuration with optimized model assignments

modes:
  code:
    name: "💻 Code"
    model: "gpt-4.1"
    description: "Expert Python/FastAPI developer focused on implementing features and refactoring code"
    write_access: true
    file_patterns:
      - ".*\\.py$"
      - ".*\\.js$"
      - ".*\\.ts$"
      - ".*\\.html$"
      - ".*\\.css$"
    capabilities:
      - "file_creation"
      - "file_modification"
      - "code_generation"
    token_limit: 128000

  debug:
    name: "🪲 Debug"
    model: "gpt-4.1"
    description: "Expert troubleshooter and debugger for the AI Orchestra project"
    write_access: true
    file_patterns:
      - ".*\\.py$"
      - ".*\\.js$"
      - ".*\\.ts$"
    capabilities:
      - "error_analysis"
      - "file_modification"
      - "logging_enhancement"
    token_limit: 128000

  architect:
    name: "🏗 Architect"
    model: "gemini-2.5-pro"
    description: "Senior AI/Cloud architect specializing in multi-agent systems and GCP infrastructure"
    write_access: true
    file_patterns:
      - ".*\\.md$"
      - "infrastructure/.*\\.yaml$"
      - "config/.*\\.yaml$"
    capabilities:
      - "system_design"
      - "architectural_planning"
    token_limit: 1000000

workflows:
  feature_development:
    name: "Feature Development Workflow"
    description: "Complete workflow for developing new features"
    steps:
      - mode: "architect"
        task: "Design system components and integration points"
      - mode: "code"
        task: "Implement the feature"
      - mode: "debug"
        task: "Test and fix any issues"
EOL
    echo -e "${GREEN}Default mode configuration created.${NC}"
fi

# Setup GCP persistence resources (if GCP is available)
if [ "$GCP_AVAILABLE" = true ]; then
    echo -e "\n${GREEN}${BOLD}Step 4: Setup GCP persistence resources${NC}"
    
    # Set up Secret Manager
    echo -e "${YELLOW}Setting up Secret Manager...${NC}"
    if gcloud secrets describe "${MODE_CONFIG_SECRET}" --project="${PROJECT_ID}" &> /dev/null; then
        echo -e "${GREEN}Secret ${MODE_CONFIG_SECRET} already exists.${NC}"
    else
        echo -e "${YELLOW}Creating secret ${MODE_CONFIG_SECRET}...${NC}"
        gcloud secrets create "${MODE_CONFIG_SECRET}" \
            --project="${PROJECT_ID}" \
            --replication-policy="automatic"
        
        # Add initial version with mode configuration
        echo -e "${YELLOW}Adding initial secret version...${NC}"
        gcloud secrets versions add "${MODE_CONFIG_SECRET}" \
            --project="${PROJECT_ID}" \
            --data-file="${MODE_CONFIG_PATH}"
        
        echo -e "${GREEN}Secret created and initialized.${NC}"
    fi
    
    # Set up Cloud Storage bucket
    echo -e "${YELLOW}Setting up Cloud Storage...${NC}"
    if gsutil ls -p "${PROJECT_ID}" "gs://${MODE_CONFIG_BUCKET}" &> /dev/null; then
        echo -e "${GREEN}Bucket ${MODE_CONFIG_BUCKET} already exists.${NC}"
    else
        echo -e "${YELLOW}Creating bucket ${MODE_CONFIG_BUCKET}...${NC}"
        gsutil mb -p "${PROJECT_ID}" -l us-central1 "gs://${MODE_CONFIG_BUCKET}"
        
        # Upload initial configuration
        echo -e "${YELLOW}Uploading initial configuration...${NC}"
        gsutil cp "${MODE_CONFIG_PATH}" "gs://${MODE_CONFIG_BUCKET}/${ENVIRONMENT}/mode_definitions.yaml"
        
        echo -e "${GREEN}Bucket created and initialized.${NC}"
    fi
    
    # Set up Firestore (if not already setup)
    echo -e "${YELLOW}Setting up Firestore...${NC}"
    # We'll use the Python script for this since Firestore setup is more complex in shell
    
    cat > /tmp/setup_firestore.py << EOL
import os
import sys
from google.cloud import firestore
import yaml

try:
    # Initialize Firestore client
    db = firestore.Client(project="${PROJECT_ID}")
    
    # Read mode configuration
    with open("${MODE_CONFIG_PATH}", "r") as f:
        content = f.read()
        config = yaml.safe_load(content)
    
    # Add to Firestore
    doc_ref = db.collection("${FIRESTORE_COLLECTION}").document("mode_definitions")
    doc_ref.set({
        "environment": "${ENVIRONMENT}",
        "content": content,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })
    
    print("Firestore collection initialized successfully.")
except Exception as e:
    print(f"Warning: Could not initialize Firestore: {e}")
    sys.exit(0)  # Non-zero exit would fail the script, but this is non-critical
EOL
    
    python3 /tmp/setup_firestore.py
    rm /tmp/setup_firestore.py
fi

# Create startup script to ensure persistence across restarts
echo -e "\n${GREEN}${BOLD}Step 5: Create startup integration${NC}"

# Create the startup script
STARTUP_SCRIPT_PATH="${PROJECT_ROOT}/scripts/mode_system_startup.sh"
cat > "${STARTUP_SCRIPT_PATH}" << EOL
#!/usr/bin/env bash
# mode_system_startup.sh - Run on system startup to restore mode configuration

set -e

# Project root
PROJECT_ROOT="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")/.." && pwd)"

# Load mode configuration from persistent storage
echo "Restoring mode configuration from persistent storage..."
python3 -c "
import sys
sys.path.append('\${PROJECT_ROOT}')
from core.persistency.mode_config_persistence import get_persistence_manager
manager = get_persistence_manager()
config = manager.load_mode_definitions()
if config:
    print('Mode configuration restored successfully.')
else:
    print('Failed to restore mode configuration. Using local files if available.')
"

# Set environment variables for persistence
export MODE_SYSTEM_ENVIRONMENT="${ENVIRONMENT}"
export MODE_SYSTEM_PROJECT_ID="${PROJECT_ID}"
export MODE_SYSTEM_BUCKET="${MODE_CONFIG_BUCKET}"
export MODE_SYSTEM_SECRET="${MODE_CONFIG_SECRET}"
export MODE_SYSTEM_COLLECTION="${FIRESTORE_COLLECTION}"

echo "Mode system startup complete."
EOL

chmod +x "${STARTUP_SCRIPT_PATH}"
echo -e "${GREEN}Created startup script at ${STARTUP_SCRIPT_PATH}${NC}"

# Update .bashrc or equivalent to source the startup script
if [ -f "${HOME}/.bashrc" ]; then
    if ! grep -q "mode_system_startup.sh" "${HOME}/.bashrc"; then
        echo -e "${YELLOW}Adding startup script to .bashrc...${NC}"
        echo "" >> "${HOME}/.bashrc"
        echo "# AI Orchestra Mode System" >> "${HOME}/.bashrc"
        echo "if [ -f \"${STARTUP_SCRIPT_PATH}\" ]; then" >> "${HOME}/.bashrc"
        echo "    source \"${STARTUP_SCRIPT_PATH}\"" >> "${HOME}/.bashrc"
        echo "fi" >> "${HOME}/.bashrc"
        echo -e "${GREEN}Added startup script to .bashrc${NC}"
    else
        echo -e "${GREEN}Startup script already in .bashrc${NC}"
    fi
fi

# Setup integration with Docker for containerized environments
echo -e "\n${GREEN}${BOLD}Step 6: Set up Docker integration${NC}"

# Create Dockerfile snippet for integration
DOCKER_SNIPPET_PATH="${PROJECT_ROOT}/docker/mode_system_docker_snippet.txt"
mkdir -p "${PROJECT_ROOT}/docker"
cat > "${DOCKER_SNIPPET_PATH}" << EOL
# Mode System Configuration
# Add this to your Dockerfile to ensure mode configuration persists

# Copy mode system files
COPY config/mode_definitions.yaml /app/config/mode_definitions.yaml
COPY core/persistency/mode_config_persistence.py /app/core/persistency/mode_config_persistence.py
COPY core/mode_manager.py /app/core/mode_manager.py
COPY scripts/mode_system_startup.sh /app/scripts/mode_system_startup.sh

# Set environment variables
ENV MODE_SYSTEM_ENVIRONMENT="${ENVIRONMENT}"
ENV MODE_SYSTEM_PROJECT_ID="${PROJECT_ID}"
ENV MODE_SYSTEM_BUCKET="${MODE_CONFIG_BUCKET}"
ENV MODE_SYSTEM_SECRET="${MODE_CONFIG_SECRET}"
ENV MODE_SYSTEM_COLLECTION="${FIRESTORE_COLLECTION}"

# Run startup script on container launch
RUN chmod +x /app/scripts/mode_system_startup.sh
ENTRYPOINT ["/bin/bash", "-c", "source /app/scripts/mode_system_startup.sh && exec \$@"]
EOL

echo -e "${GREEN}Created Docker integration snippet at ${DOCKER_SNIPPET_PATH}${NC}"
echo -e "${YELLOW}Add this to your Dockerfile to ensure mode configuration persists in containers.${NC}"

# Create Kubernetes ConfigMap/Secret definition
if [ "$GCP_AVAILABLE" = true ]; then
    K8S_DIR="${PROJECT_ROOT}/kubernetes"
    mkdir -p "${K8S_DIR}"
    K8S_CONFIG_PATH="${K8S_DIR}/mode-system-config.yaml"
    
    cat > "${K8S_CONFIG_PATH}" << EOL
# Mode System Kubernetes Configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: mode-system-config
data:
  MODE_SYSTEM_ENVIRONMENT: "${ENVIRONMENT}"
  MODE_SYSTEM_PROJECT_ID: "${PROJECT_ID}"
  MODE_SYSTEM_BUCKET: "${MODE_CONFIG_BUCKET}"
  MODE_SYSTEM_SECRET: "${MODE_CONFIG_SECRET}"
  MODE_SYSTEM_COLLECTION: "${FIRESTORE_COLLECTION}"
---
apiVersion: v1
kind: Secret
metadata:
  name: mode-system-secrets
type: Opaque
stringData:
  mode_definitions.yaml: |
$(sed 's/^/    /' "${MODE_CONFIG_PATH}")
EOL
    
    echo -e "${GREEN}Created Kubernetes configuration at ${K8S_CONFIG_PATH}${NC}"
fi

# Setup Cloud Build integration
if [ "$GCP_AVAILABLE" = true ]; then
    CLOUDBUILD_PATH="${PROJECT_ROOT}/cloudbuild_mode_system.yaml"
    
    cat > "${CLOUDBUILD_PATH}" << EOL
# Cloud Build configuration for mode system persistence
steps:
# Step 1: Restore mode configuration from GCP persistence
- name: 'gcr.io/cloud-builders/python'
  id: 'restore-mode-config'
  entrypoint: 'python3'
  args:
  - '-c'
  - |
    import sys
    sys.path.append('.')
    from core.persistency.mode_config_persistence import get_persistence_manager
    manager = get_persistence_manager()
    config = manager.load_mode_definitions()
    if config:
        print('Mode configuration restored successfully.')
    else:
        print('Failed to restore mode configuration. Using local files if available.')

# Step 2: Make environment variables available
- name: 'gcr.io/cloud-builders/gcloud'
  id: 'set-env-vars'
  entrypoint: '/bin/sh'
  args:
  - '-c'
  - |
    echo "MODE_SYSTEM_ENVIRONMENT=${ENVIRONMENT}" >> /workspace/mode_system.env
    echo "MODE_SYSTEM_PROJECT_ID=${PROJECT_ID}" >> /workspace/mode_system.env
    echo "MODE_SYSTEM_BUCKET=${MODE_CONFIG_BUCKET}" >> /workspace/mode_system.env
    echo "MODE_SYSTEM_SECRET=${MODE_CONFIG_SECRET}" >> /workspace/mode_system.env
    echo "MODE_SYSTEM_COLLECTION=${FIRESTORE_COLLECTION}" >> /workspace/mode_system.env

# Step 3: Use the environment in your build
- name: 'gcr.io/cloud-builders/docker'
  id: 'build-with-mode-config'
  entrypoint: '/bin/sh'
  args:
  - '-c'
  - |
    env \$(cat /workspace/mode_system.env) docker build -t gcr.io/$PROJECT_ID/my-image:latest .
EOL
    
    echo -e "${GREEN}Created Cloud Build configuration at ${CLOUDBUILD_PATH}${NC}"
fi

# Add to .gitignore to prevent committing sensitive data
GITIGNORE_PATH="${PROJECT_ROOT}/.gitignore"
if [ -f "${GITIGNORE_PATH}" ]; then
    if ! grep -q "mode_system" "${GITIGNORE_PATH}"; then
        echo -e "${YELLOW}Adding mode system entries to .gitignore...${NC}"
        cat >> "${GITIGNORE_PATH}" << EOL

# Mode System
config/backups/
.mode_system_env
EOL
        echo -e "${GREEN}Added mode system entries to .gitignore${NC}"
    fi
fi

# Run the startup script to initialize everything
echo -e "\n${GREEN}${BOLD}Step 7: Run initial startup${NC}"
source "${STARTUP_SCRIPT_PATH}"

# Success message
echo -e "\n${BLUE}======================================================${NC}"
echo -e "${GREEN}${BOLD}Enhanced Mode System Setup Complete!${NC}"
echo -e "${BLUE}======================================================${NC}"
echo -e "${YELLOW}Your mode system is now configured for persistent operation across restarts.${NC}"
echo -e "\n${BOLD}Key files:${NC}"
echo -e "- Configuration: ${MODE_CONFIG_PATH}"
echo -e "- Mode Manager: ${PROJECT_ROOT}/core/mode_manager.py"
echo -e "- Persistence: ${PROJECT_ROOT}/core/persistency/mode_config_persistence.py"
echo -e "- CLI Tool: ${PROJECT_ROOT}/tools/mode_switcher.py"
echo -e "- Startup Script: ${STARTUP_SCRIPT_PATH}"
echo -e "- Documentation: ${PROJECT_ROOT}/docs/ENHANCED_MODE_SYSTEM.md"

if [ "$GCP_AVAILABLE" = true ]; then
    echo -e "\n${BOLD}GCP Resources:${NC}"
    echo -e "- Secret Manager: ${MODE_CONFIG_SECRET}"
    echo -e "- Cloud Storage: gs://${MODE_CONFIG_BUCKET}/${ENVIRONMENT}/mode_definitions.yaml"
    echo -e "- Firestore Collection: ${FIRESTORE_COLLECTION}"
fi

echo -e "\n${BOLD}Next Steps:${NC}"
echo -e "1. ${YELLOW}Start using the mode system:${NC}"
echo -e "   python3 ${PROJECT_ROOT}/tools/mode_switcher.py --interactive"
echo -e "2. ${YELLOW}View documentation:${NC}"
echo -e "   less ${PROJECT_ROOT}/docs/ENHANCED_MODE_SYSTEM.md"
echo -e "3. ${YELLOW}Customize mode configurations:${NC}"
echo -e "   edit ${MODE_CONFIG_PATH}"
echo -e "${BLUE}======================================================${NC}"

exit 0