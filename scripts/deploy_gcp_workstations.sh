#!/bin/bash
# Performance-optimized deployment script for GitHub Codespaces to GCP Workstations migration
# This script orchestrates the end-to-end migration process

set -e

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Function to display messages
info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

header() {
  echo -e "\n${BLUE}${BOLD}===== $1 =====${NC}\n"
}

# Display script banner
echo -e "${BLUE}"
echo "  ____________________    __          __         __        __  _            "
echo " / ___/ ___/ ____/ __ \  / /_  ____  / /______  / /_____ _/ /_(_)___  ____  "
echo "/ (_ / /__/ /___/ /_/ / / __/ / __ \/ __/ ___/ / __/ __ \`/ __/ / __ \/ __ \ "
echo "\___/\___/\____/\____/  / / _ / /_/ / / (__  )  / /_/ /_/ / /_/ / /_/ / / / /"
echo "                       /_/( )/ .___/_/  /____/   \__/\__,_/\__/_/\____/_/ /_/ "
echo "                          |/ /_/                                            "
echo -e "${NC}"
echo -e "${BOLD}Performance-Optimized GCP Workstation Deployment Script${NC}"
echo -e "${BLUE}============================================================${NC}\n"

# Parse command line arguments
PROJECT_ID=""
REGION="us-central1"
ZONE="us-central1-a"
AUTO_APPROVE=false
SKIP_BENCHMARK=false
SKIP_TERRAFORM=false
SKIP_CONTAINER=false
SKIP_SECRETS=false
ENV_FILE=".env"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --project)
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    --zone)
      ZONE="$2"
      shift 2
      ;;
    --auto-approve)
      AUTO_APPROVE=true
      shift
      ;;
    --skip-benchmark)
      SKIP_BENCHMARK=true
      shift
      ;;
    --skip-terraform)
      SKIP_TERRAFORM=true
      shift
      ;;
    --skip-container)
      SKIP_CONTAINER=true
      shift
      ;;
    --skip-secrets)
      SKIP_SECRETS=true
      shift
      ;;
    --env-file)
      ENV_FILE="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo
      echo "Options:"
      echo "  --project ID          The GCP project ID (required if not in gcloud config)"
      echo "  --region REGION       The GCP region (default: us-central1)"
      echo "  --zone ZONE           The GCP zone (default: us-central1-a)"
      echo "  --auto-approve        Skip confirmation prompts"
      echo "  --skip-benchmark      Skip environment benchmarking"
      echo "  --skip-terraform      Skip Terraform infrastructure deployment"
      echo "  --skip-container      Skip container image building"
      echo "  --skip-secrets        Skip secret migration"
      echo "  --env-file FILE       Path to .env file with secrets (default: .env)"
      echo "  --help                Display this help message"
      exit 0
      ;;
    *)
      error "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Determine project ID if not provided
if [ -z "$PROJECT_ID" ]; then
  info "No project ID provided, attempting to get from gcloud config..."
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
  
  if [ -z "$PROJECT_ID" ]; then
    error "No project ID provided and couldn't determine from gcloud config."
    error "Please provide a project ID with --project or set it with 'gcloud config set project'"
    exit 1
  fi
fi

info "Using GCP project: $PROJECT_ID"
info "Using GCP region: $REGION"
info "Using GCP zone: $ZONE"

# Check for required tools
header "Checking prerequisites"

check_command() {
  local cmd=$1
  local install_msg=$2
  
  if ! command -v "$cmd" &> /dev/null; then
    error "$cmd not found. $install_msg"
    exit 1
  fi
  
  success "$cmd found: $(command -v "$cmd")"
}

check_command "gcloud" "Please install Google Cloud SDK from https://cloud.google.com/sdk/docs/install"
check_command "terraform" "Please install Terraform from https://www.terraform.io/downloads"
check_command "docker" "Please install Docker from https://docs.docker.com/get-docker/"
check_command "python3" "Please install Python 3 from https://www.python.org/downloads/"

# Check for GCP authentication
info "Checking GCP authentication..."
if ! gcloud auth print-access-token &> /dev/null; then
  error "Not authenticated with GCP. Please run 'gcloud auth login' first."
  exit 1
fi
success "GCP authentication verified"

# Create working directories if they don't exist
mkdir -p logs

# Step 1: Run benchmarks on current environment
if [ "$SKIP_BENCHMARK" != "true" ]; then
  header "Step 1: Benchmarking current environment"
  info "Running environment benchmark script..."
  
  # Check if script exists
  if [ ! -f "scripts/benchmark_environment.py" ]; then
    error "Benchmark script not found at scripts/benchmark_environment.py"
    exit 1
  fi
  
  # Make script executable if it's not
  chmod +x scripts/benchmark_environment.py
  
  # Run the benchmark script
  python3 scripts/benchmark_environment.py --output logs/benchmark_results_$(date +%Y%m%d_%H%M%S).json
  
  success "Environment benchmarking complete"
fi

# Step 2: Build and push container image
if [ "$SKIP_CONTAINER" != "true" ]; then
  header "Step 2: Building container image"
  
  # Check if Dockerfile exists
  if [ ! -f "docker/workstation-image/Dockerfile" ]; then
    error "Dockerfile not found at docker/workstation-image/Dockerfile"
    exit 1
  fi
  
  # Create artifact registry repository if it doesn't exist
  REPO_NAME="workstation-images"
  REPO_PATH="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"
  
  info "Checking if Artifact Registry repository exists..."
  
  # Enable Artifact Registry API if not already enabled
  gcloud services enable artifactregistry.googleapis.com --project="$PROJECT_ID"
  
  # Check if repository exists, create if it doesn't
  if ! gcloud artifacts repositories describe "$REPO_NAME" \
    --project="$PROJECT_ID" \
    --location="$REGION" &>/dev/null; then
    
    info "Creating Artifact Registry repository..."
    gcloud artifacts repositories create "$REPO_NAME" \
      --repository-format=docker \
      --location="$REGION" \
      --project="$PROJECT_ID" \
      --description="Docker images for GCP Workstations"
      
    success "Created Artifact Registry repository: $REPO_PATH"
  else
    success "Artifact Registry repository already exists: $REPO_PATH"
  fi
  
  # Configure Docker to authenticate with Artifact Registry
  info "Configuring Docker authentication..."
  gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet
  
  # Build and tag the Docker image
  IMAGE_TAG="$REPO_PATH/workstation-image:latest"
  info "Building container image: $IMAGE_TAG"
  
  # Add timestamp to image tag for versioning
  TIMESTAMP=$(date +%Y%m%d%H%M%S)
  VERSIONED_IMAGE_TAG="$REPO_PATH/workstation-image:$TIMESTAMP"
  
  # Build the container image
  (
    cd docker/workstation-image
    docker build -t "$IMAGE_TAG" -t "$VERSIONED_IMAGE_TAG" .
  )
  
  # Push the container image
  info "Pushing container image to Artifact Registry..."
  docker push "$IMAGE_TAG"
  docker push "$VERSIONED_IMAGE_TAG"
  
  success "Container image built and pushed: $IMAGE_TAG"
  success "Versioned image: $VERSIONED_IMAGE_TAG"
  
  # Update Terraform variables with the new container image
  echo "container_image = \"$IMAGE_TAG\"" > terraform/image.auto.tfvars
  
  success "Updated Terraform variables with container image reference"
fi

# Step 3: Deploy Terraform infrastructure
if [ "$SKIP_TERRAFORM" != "true" ]; then
  header "Step 3: Deploying Terraform infrastructure"
  
  # Check if Terraform files exist
  if [ ! -f "terraform/main.tf" ]; then
    error "Terraform configuration not found at terraform/main.tf"
    exit 1
  fi
  
  # Create terraform.tfvars if it doesn't exist
  if [ ! -f "terraform/terraform.tfvars" ]; then
    info "Creating terraform.tfvars file..."
    cat > terraform/terraform.tfvars << EOF
project_id = "$PROJECT_ID"
region = "$REGION"
zone = "$ZONE"
project_prefix = "ai-orchestra"
enable_gpu = true
performance_optimized = true
EOF
    success "Created terraform.tfvars file"
  else
    info "Using existing terraform.tfvars file"
  fi
  
  # Initialize Terraform
  info "Initializing Terraform..."
  (
    cd terraform
    terraform init -upgrade
  )
  
  # Plan Terraform changes
  info "Planning Terraform changes..."
  (
    cd terraform
    terraform plan -out=tfplan
  )
  
  # Apply Terraform changes
  if [ "$AUTO_APPROVE" = "true" ]; then
    info "Auto-approving Terraform apply..."
    (
      cd terraform
      terraform apply -auto-approve tfplan
    )
  else
    echo
    read -p "Apply Terraform changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      (
        cd terraform
        terraform apply tfplan
      )
    else
      warn "Terraform apply skipped by user"
    fi
  fi
  
  # Capture key outputs
  info "Capturing Terraform outputs..."
  CLUSTER_NAME=$(cd terraform && terraform output -raw workstation_cluster_endpoint 2>/dev/null || echo "unknown")
  STANDARD_CONFIG_NAME=$(cd terraform && terraform output -raw standard_config_name 2>/dev/null || echo "unknown")
  ML_CONFIG_NAME=$(cd terraform && terraform output -raw ml_config_name 2>/dev/null || echo "unknown")
  SERVICE_ACCOUNT=$(cd terraform && terraform output -raw service_account 2>/dev/null || echo "unknown")
  
  # Save outputs to a file for reference
  cat > logs/terraform_outputs.txt << EOF
Cluster Name: $CLUSTER_NAME
Standard Configuration: $STANDARD_CONFIG_NAME
ML Configuration: $ML_CONFIG_NAME
Service Account: $SERVICE_ACCOUNT
EOF
  
  success "Infrastructure deployment complete"
  success "Outputs saved to logs/terraform_outputs.txt"
fi

# Step 4: Migrate secrets
if [ "$SKIP_SECRETS" != "true" ]; then
  header "Step 4: Migrating secrets to GCP Secret Manager"
  
  # Check if the script exists
  if [ ! -f "scripts/migrate_secrets.sh" ]; then
    error "Secret migration script not found at scripts/migrate_secrets.sh"
    exit 1
  fi
  
  # Make script executable if it's not
  chmod +x scripts/migrate_secrets.sh
  
  # Check if .env file exists
  if [ ! -f "$ENV_FILE" ]; then
    warn "Environment file $ENV_FILE not found!"
    
    # Ask user if they want to create a sample .env file
    if [ "$AUTO_APPROVE" != "true" ]; then
      echo
      read -p "Create a sample .env file? (y/n) " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "Creating sample .env file..."
        cat > "$ENV_FILE" << EOF
# GitHub credentials
GITHUB_TOKEN=your_github_token_here

# GCP credentials - not needed in GCP Workstations
# GCP_SERVICE_ACCOUNT_KEY={"type":"service_account",...}

# AI API Keys
GEMINI_API_KEY=your_gemini_api_key_here
VERTEX_API_KEY=your_vertex_api_key_here

# Project configuration
PROJECT_ID=$PROJECT_ID
REGION=$REGION
ZONE=$ZONE

# Custom settings
ENABLE_GPU=true
ENABLE_PROFILING=true
EOF
        success "Created sample $ENV_FILE file. Please edit it with your actual secrets."
        exit 0
      else
        warn "Skipping secret migration due to missing $ENV_FILE file"
        SKIP_SECRETS=true
      fi
    else
      warn "Skipping secret migration due to missing $ENV_FILE file"
      SKIP_SECRETS=true
    fi
  fi
  
  # Run the secret migration script if we're still going
  if [ "$SKIP_SECRETS" != "true" ]; then
    AUTO_APPROVE_FLAG=""
    if [ "$AUTO_APPROVE" = "true" ]; then
      AUTO_APPROVE_FLAG="--auto-approve"
    fi
    
    info "Running secret migration script..."
    ./scripts/migrate_secrets.sh --project "$PROJECT_ID" --env-file "$ENV_FILE" $AUTO_APPROVE_FLAG
    
    success "Secret migration complete"
  fi
fi

# Step 5: Print success message
header "Deployment Complete!"

# Check if we have Terraform outputs
if [ -f "logs/terraform_outputs.txt" ]; then
  echo -e "${BLUE}Workstation Information:${NC}"
  cat logs/terraform_outputs.txt
  echo
fi

echo -e "${GREEN}${BOLD}Next Steps:${NC}"
echo -e "  1. ${YELLOW}Access your workstation:${NC}"
echo -e "     Visit the GCP Console > Cloud Workstations page"
echo -e "     https://console.cloud.google.com/workstations/workstations?project=$PROJECT_ID"
echo
echo -e "  2. ${YELLOW}Launch a workstation:${NC}"
echo -e "     Click 'Launch' on one of your workstation configurations"
echo
echo -e "  3. ${YELLOW}Clone your repository:${NC}"
echo -e "     git clone https://github.com/your-org/ai-orchestra.git"
echo
echo -e "  4. ${YELLOW}Setup your development environment:${NC}"
echo -e "     Follow instructions in the WELCOME.md file"
echo

success "Migration from GitHub Codespaces to GCP Workstations complete!"