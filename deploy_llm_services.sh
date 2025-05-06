#!/bin/bash
# Deployment script for LLM Services
# This script helps with deploying and starting LLM services with proper configuration

# Color output for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEPLOY_MODE="local"
ENVIRONMENT="development"
VALIDATE_ONLY=false
CHECK_DOCKER=true
CHECK_GCP=true
BUILDKIT_ENABLED=true
INSTALL_DEPS=true
START_SERVICE=true
SKIP_PROMPTS=false

# Print usage information
function print_usage {
  echo -e "${BLUE}Usage:${NC} ./deploy_llm_services.sh [options]"
  echo -e ""
  echo -e "${YELLOW}Options:${NC}"
  echo -e "  --mode=<local|docker|gcp>      Deployment mode (default: local)"
  echo -e "  --env=<development|production> Environment to deploy to (default: development)"
  echo -e "  --validate-only                Only validate without deploying"
  echo -e "  --no-docker-check              Skip Docker checks"
  echo -e "  --no-gcp-check                 Skip GCP credential checks"
  echo -e "  --no-buildkit                  Disable Docker BuildKit"
  echo -e "  --no-deps                      Skip dependency installation"
  echo -e "  --no-start                     Don't start services after deployment"
  echo -e "  --yes                          Skip all prompts (non-interactive mode)"
  echo -e "  --help                         Display this help message"
  echo -e ""
  echo -e "${BLUE}Examples:${NC}"
  echo -e "  ./deploy_llm_services.sh --mode=docker --env=production"
  echo -e "  ./deploy_llm_services.sh --validate-only"
  echo -e ""
}

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    --mode=*)
      DEPLOY_MODE="${arg#*=}"
      ;;
    --env=*)
      ENVIRONMENT="${arg#*=}"
      ;;
    --validate-only)
      VALIDATE_ONLY=true
      ;;
    --no-docker-check)
      CHECK_DOCKER=false
      ;;
    --no-gcp-check)
      CHECK_GCP=false
      ;;
    --no-buildkit)
      BUILDKIT_ENABLED=false
      ;;
    --no-deps)
      INSTALL_DEPS=false
      ;;
    --no-start)
      START_SERVICE=false
      ;;
    --yes)
      SKIP_PROMPTS=true
      ;;
    --help)
      print_usage
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $arg${NC}"
      print_usage
      exit 1
      ;;
  esac
done

# Validate options
if [[ "$DEPLOY_MODE" != "local" && "$DEPLOY_MODE" != "docker" && "$DEPLOY_MODE" != "gcp" ]]; then
  echo -e "${RED}Error: Invalid deployment mode '$DEPLOY_MODE'. Must be one of: local, docker, gcp${NC}"
  exit 1
fi

if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
  echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'. Must be one of: development, production${NC}"
  exit 1
fi

# Print deployment information
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}LLM Services Deployment${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "Deployment mode: ${YELLOW}$DEPLOY_MODE${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Validation only: ${YELLOW}$VALIDATE_ONLY${NC}"
echo -e "${BLUE}============================================================${NC}"

# Confirm deployment if not skipping prompts
if [[ "$SKIP_PROMPTS" == "false" ]]; then
  read -p "Continue with deployment? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment cancelled.${NC}"
    exit 1
  fi
fi

# Check for required tools
echo -e "${YELLOW}Checking required tools...${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
  echo -e "${RED}Error: Python 3 is required but not found.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Python 3 is installed.${NC}"

# Check for Poetry
if ! command -v poetry &> /dev/null; then
  echo -e "${YELLOW}Poetry not found. Installing Poetry...${NC}"
  curl -sSL https://install.python-poetry.org | python3 -
  if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install Poetry. Exiting.${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ Poetry installed successfully.${NC}"
else
  echo -e "${GREEN}✓ Poetry is installed.${NC}"
fi

# Check for Docker if needed
if [[ "$CHECK_DOCKER" == "true" && ("$DEPLOY_MODE" == "docker" || "$DEPLOY_MODE" == "gcp") ]]; then
  if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is required for $DEPLOY_MODE deployment but not found.${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ Docker is installed.${NC}"
  
  # Check for Docker BuildKit
  if [[ "$BUILDKIT_ENABLED" == "true" ]]; then
    export DOCKER_BUILDKIT=1
    echo -e "${GREEN}✓ Docker BuildKit enabled.${NC}"
  else
    unset DOCKER_BUILDKIT
    echo -e "${YELLOW}⚠ Docker BuildKit disabled. Builds may be slower.${NC}"
  fi
fi

# Check for gcloud if needed
if [[ "$CHECK_GCP" == "true" && "$DEPLOY_MODE" == "gcp" ]]; then
  if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is required for GCP deployment but not found.${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ gcloud CLI is installed.${NC}"
  
  # Check gcloud auth
  if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with gcloud. Run 'gcloud auth login' first.${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ gcloud authentication is configured.${NC}"
fi

# Install dependencies if needed
if [[ "$INSTALL_DEPS" == "true" ]]; then
  echo -e "${YELLOW}Installing dependencies...${NC}"
  
  if [[ "$ENVIRONMENT" == "production" ]]; then
    ./setup_poetry_env.sh --production
  elif [[ "$DEPLOY_MODE" == "local" ]]; then
    ./setup_poetry_env.sh
  else
    ./setup_poetry_env.sh --llm
  fi
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install dependencies.${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ Dependencies installed successfully.${NC}"
fi

# Create and set up environment variables file
ENV_FILE=".env.${ENVIRONMENT}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo -e "${YELLOW}Creating environment file $ENV_FILE...${NC}"
  if [[ -f ".env.example" ]]; then
    cp .env.example "$ENV_FILE"
    echo -e "${GREEN}✓ Created $ENV_FILE from .env.example.${NC}"
  else
    touch "$ENV_FILE"
    # Add default variables
    echo "# Environment variables for $ENVIRONMENT" > "$ENV_FILE"
    echo "ENVIRONMENT=$ENVIRONMENT" >> "$ENV_FILE"
    
    # Add provider-specific variables as commented examples
    echo -e "\n# LiteLLM configuration" >> "$ENV_FILE"
    echo "#LITELLM_MASTER_KEY=sk-..." >> "$ENV_FILE"
    echo "#LITELLM_VERBOSE=false" >> "$ENV_FILE"
    
    echo -e "\n# OpenAI configuration" >> "$ENV_FILE"
    echo "#OPENAI_API_KEY=sk-..." >> "$ENV_FILE"
    
    echo -e "\n# Azure OpenAI configuration" >> "$ENV_FILE"
    echo "#AZURE_API_KEY=..." >> "$ENV_FILE"
    echo "#AZURE_API_BASE=https://your-resource.openai.azure.com/" >> "$ENV_FILE"
    
    echo -e "\n# Anthropic configuration" >> "$ENV_FILE"
    echo "#ANTHROPIC_API_KEY=sk-ant-..." >> "$ENV_FILE"
    
    echo -e "\n# Portkey configuration" >> "$ENV_FILE"
    echo "#PORTKEY_API_KEY=..." >> "$ENV_FILE"
    echo "#PORTKEY_CONFIG=..." >> "$ENV_FILE"
    
    echo -e "\n# OpenRouter configuration" >> "$ENV_FILE"
    echo "#OPENROUTER_API_KEY=..." >> "$ENV_FILE"
    echo "#OR_SITE_URL=https://orchestra.example.com" >> "$ENV_FILE"
    echo "#OR_APP_NAME=OrchestraLLM" >> "$ENV_FILE"
    
    echo -e "\n# Redis configuration" >> "$ENV_FILE"
    echo "#REDIS_HOST=localhost" >> "$ENV_FILE"
    echo "#REDIS_PORT=6379" >> "$ENV_FILE"
    echo "#REDIS_PASSWORD=" >> "$ENV_FILE"
    
    echo -e "\n# GCP configuration" >> "$ENV_FILE"
    echo "#GOOGLE_CLOUD_PROJECT=your-project-id" >> "$ENV_FILE"
    
    echo -e "\n# Monitoring configuration" >> "$ENV_FILE"
    echo "#START_METRICS_SERVER=false" >> "$ENV_FILE"
    echo "#METRICS_PORT=8000" >> "$ENV_FILE"
    
    echo -e "${GREEN}✓ Created $ENV_FILE with default template.${NC}"
  fi
  
  # Remind to edit the file if not in non-interactive mode
  if [[ "$SKIP_PROMPTS" == "false" ]]; then
    echo -e "${YELLOW}⚠ Please edit $ENV_FILE to set required environment variables.${NC}"
    read -p "Press Enter to continue after editing, or Ctrl+C to cancel..." -r
  fi
else
  echo -e "${GREEN}✓ Environment file $ENV_FILE already exists.${NC}"
fi

# Load environment variables from file
echo -e "${YELLOW}Loading environment variables from $ENV_FILE...${NC}"
export $(grep -v '^#' "$ENV_FILE" | xargs)
echo -e "${GREEN}✓ Environment variables loaded.${NC}"

# Run validation checks
echo -e "${YELLOW}Running environment validation...${NC}"
poetry run python -m core.orchestrator.src.services.llm.startup_validation

if [ $? -ne 0 ]; then
  echo -e "${RED}Error: Environment validation failed.${NC}"
  if [[ "$SKIP_PROMPTS" == "false" ]]; then
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo -e "${RED}Deployment cancelled.${NC}"
      exit 1
    fi
  else
    exit 1
  fi
else
  echo -e "${GREEN}✓ Environment validation successful.${NC}"
fi

# If validation only, exit here
if [[ "$VALIDATE_ONLY" == "true" ]]; then
  echo -e "${GREEN}Validation completed successfully. Exiting without deployment.${NC}"
  exit 0
fi

# Build and deploy based on mode
if [[ "$DEPLOY_MODE" == "docker" ]]; then
  echo -e "${YELLOW}Building Docker container...${NC}"
  
  # Build the Docker image with appropriate tags
  IMAGE_TAG="orchestra-llm:${ENVIRONMENT}"
  if [[ "$BUILDKIT_ENABLED" == "true" ]]; then
    DOCKER_BUILDKIT=1 docker build -t "$IMAGE_TAG" -f Dockerfile.llm-test .
  else
    docker build -t "$IMAGE_TAG" -f Dockerfile.llm-test .
  fi
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed.${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ Docker image built successfully.${NC}"
  
  # Start the container if requested
  if [[ "$START_SERVICE" == "true" ]]; then
    echo -e "${YELLOW}Starting Docker container...${NC}"
    
    # Create a network if it doesn't exist
    if ! docker network inspect orchestra-network &> /dev/null; then
      docker network create orchestra-network
    fi
    
    # Run the container with environment variables from file
    docker run -d --name orchestra-llm-service \
      --network orchestra-network \
      -p 8001:8001 \
      --env-file "$ENV_FILE" \
      --restart unless-stopped \
      "$IMAGE_TAG"
    
    if [ $? -ne 0 ]; then
      echo -e "${RED}Error: Failed to start Docker container.${NC}"
      exit 1
    fi
    echo -e "${GREEN}✓ Docker container started successfully.${NC}"
    echo -e "${GREEN}✓ Service is running at http://localhost:8001${NC}"
  fi
  
elif [[ "$DEPLOY_MODE" == "gcp" ]]; then
  echo -e "${YELLOW}Deploying to Google Cloud Run...${NC}"
  
  # Ensure required env vars are set
  export PROJECT_ID="cherry-ai.me"
  export PROJECT_NUMBER="525398941159"
  export REGION="us-central1"
  export SERVICE_ACCOUNT="vertex-agent@${PROJECT_ID}.iam.gserviceaccount.com"

  if [[ -z "$PROJECT_ID" ]]; then
    echo -e "${RED}Error: PROJECT_ID is required for GCP deployment.${NC}"
    echo -e "${YELLOW}Set it in $ENV_FILE or export it manually.${NC}"
    exit 1
  fi
  
  # Build and push the container to Artifact Registry
  IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/orchestra/llm:latest"
  
  echo -e "${YELLOW}Building and pushing Docker image to Artifact Registry...${NC}"
  if [[ "$BUILDKIT_ENABLED" == "true" ]]; then
    DOCKER_BUILDKIT=1 docker build -t "$IMAGE_NAME" -f Dockerfile.llm-test .
  else
    docker build -t "$IMAGE_NAME" -f Dockerfile.llm-test .
  fi
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed.${NC}"
    exit 1
  fi
  
  docker push "$IMAGE_NAME"
  
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to push Docker image to Artifact Registry.${NC}"
    exit 1
  fi
  echo -e "${GREEN}✓ Docker image pushed to Artifact Registry successfully.${NC}"
  
  # Deploy to Cloud Run if requested
  if [[ "$START_SERVICE" == "true" ]]; then
    echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
    
    gcloud run deploy llm-test \
      --image="$IMAGE_NAME" \
      --platform=managed \
      --region="$REGION" \
      --service-account="$SERVICE_ACCOUNT" \
      --project="$PROJECT_ID" \
      --port=8001 \
      --memory=2Gi \
      --cpu=2 \
      --min-instances=1
    
    if [ $? -ne 0 ]; then
      echo -e "${RED}Error: Failed to deploy to Cloud Run.${NC}"
      exit 1
    fi
    echo -e "${GREEN}✓ Deployed to Cloud Run successfully.${NC}"
  fi
  
  # Create secrets for LLM API keys
  echo -e "${YELLOW}Creating secrets for LLM services...${NC}"
  secrets=(
    "OPENAI_API_KEY"
    "ANTHROPIC_API_KEY"
    "COHERE_API_KEY"
    "VERTEX_API_KEY"
  )

  for secret in "${secrets[@]}"; do
    if ! gcloud secrets describe ${secret} --project=${PROJECT_ID} > /dev/null 2>&1; then
      gcloud secrets create ${secret} \
        --project=${PROJECT_ID} \
        --replication-policy="automatic"
    fi
  done

  echo -e "${GREEN}✓ Secrets for LLM services created successfully.${NC}"
  
else # local mode
  echo -e "${YELLOW}Setting up local development environment...${NC}"
  
  # Create symbolic links if needed
  if [[ ! -L ".env" ]]; then
    ln -sf "$ENV_FILE" .env
    echo -e "${GREEN}✓ Created .env symlink to $ENV_FILE.${NC}"
  fi
  
  # Start the service if requested
  if [[ "$START_SERVICE" == "true" ]]; then
    echo -e "${YELLOW}Starting local LLM service...${NC}"
    
    # Ensure the llm_test_server is installed
    if [[ ! -d "tools/llm_test_server" ]]; then
      echo -e "${RED}Error: llm_test_server directory not found.${NC}"
      echo -e "${YELLOW}Please ensure the repository is complete.${NC}"
      exit 1
    fi
    
    # Start the server in the background
    poetry run python -m tools.llm_test_server.main &
    SERVER_PID=$!
    
    echo -e "${GREEN}✓ Local LLM service started with PID $SERVER_PID.${NC}"
    echo -e "${YELLOW}To stop the service, run: kill $SERVER_PID${NC}"
    echo -e "${GREEN}✓ Service is running at http://localhost:8001${NC}"
    
    # Save PID for later cleanup
    echo "$SERVER_PID" > .llm_server.pid
  fi
fi

echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✓ Deployment completed successfully.${NC}"
echo -e "${BLUE}============================================================${NC}"

# Add a hint about how to stop the service
if [[ "$START_SERVICE" == "true" ]]; then
  if [[ "$DEPLOY_MODE" == "docker" ]]; then
    echo -e "${YELLOW}To stop the service, run: docker stop orchestra-llm-service${NC}"
  elif [[ "$DEPLOY_MODE" == "local" ]]; then
    echo -e "${YELLOW}To stop the service, run: kill $(cat .llm_server.pid)${NC}"
  fi
  
  # Wait for Ctrl+C if not in non-interactive mode
  if [[ "$SKIP_PROMPTS" == "false" && "$DEPLOY_MODE" == "local" ]]; then
    echo -e "${YELLOW}Press Ctrl+C to stop the service...${NC}"
    
    # Set up the trap to catch Ctrl+C
    function cleanup {
      echo -e "${YELLOW}Stopping LLM service...${NC}"
      kill $(cat .llm_server.pid)
      rm .llm_server.pid
      echo -e "${GREEN}✓ Service stopped.${NC}"
      exit 0
    }
    
    trap cleanup INT
    
    # Wait indefinitely
    while true; do
      sleep 1
    done
  fi
fi
