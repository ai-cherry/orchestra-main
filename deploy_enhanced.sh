#!/bin/bash
# deploy_enhanced.sh - Enhanced deployment script for AI Orchestra
# This script provides a comprehensive deployment process with verification and rollback

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration with fallbacks to environment variables
PROJECT_ID="${GCP_PROJECT_ID:-${1:-cherry-ai-project}}"
REGION="${GCP_REGION:-${2:-us-west4}}"
ENVIRONMENT="${DEPLOYMENT_ENVIRONMENT:-${3:-dev}}"  # Default to dev if not specified
COMPONENT="${4:-all}"  # Default to all if not specified
DRY_RUN="${5:-false}"  # Default to false if not specified

# Function to print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

# Function to check prerequisites
check_prerequisites() {
    section "Checking Prerequisites"
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}Error: gcloud CLI not found. Please install it first.${NC}"
        echo -e "${YELLOW}Visit https://cloud.google.com/sdk/docs/install for installation instructions.${NC}"
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker not found. Please install it first.${NC}"
        echo -e "${YELLOW}Visit https://docs.docker.com/get-docker/ for installation instructions.${NC}"
        exit 1
    fi
    
    # Check if user is authenticated with gcloud
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")
    if [[ -z "$ACCOUNT" ]]; then
        echo -e "${YELLOW}You are not authenticated with gcloud CLI. Let's log in now.${NC}"
        
        # Try to use Application Default Credentials
        if [ -z "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
            echo -e "${YELLOW}GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.${NC}"
            echo -e "${YELLOW}Attempting to use gcloud application-default login...${NC}"
            gcloud auth application-default login
        else
            echo -e "${GREEN}Using Application Default Credentials from ${GOOGLE_APPLICATION_CREDENTIALS}${NC}"
        fi
    fi
    
    echo -e "${GREEN}Currently authenticated as: $ACCOUNT${NC}"
    
    # Set project and region
    echo -e "${BLUE}Setting project to $PROJECT_ID...${NC}"
    gcloud config set project ${PROJECT_ID}
    echo -e "${BLUE}Setting region to $REGION...${NC}"
    gcloud config set run/region ${REGION}
    
    echo -e "${GREEN}Prerequisites check completed successfully.${NC}"
}

# Function to load environment-specific configurations
load_environment_config() {
    section "Loading Environment Configuration"
    
    # Load environment-specific configurations
    if [ -f "config/environments/${ENVIRONMENT}.env" ]; then
        source "config/environments/${ENVIRONMENT}.env"
        echo -e "${GREEN}Loaded configuration for ${ENVIRONMENT} environment.${NC}"
        echo -e "${GREEN}Memory: ${MEMORY}${NC}"
        echo -e "${GREEN}CPU: ${CPU}${NC}"
        echo -e "${GREEN}Min Instances: ${MIN_INSTANCES}${NC}"
        echo -e "${GREEN}Max Instances: ${MAX_INSTANCES}${NC}"
    else
        echo -e "${YELLOW}No environment-specific config found for ${ENVIRONMENT}, using defaults.${NC}"
        MEMORY="1Gi"
        CPU="1"
        MIN_INSTANCES="0"
        MAX_INSTANCES="10"
    fi
}

# Function to build and push Docker image
build_and_push_image() {
    section "Building and Pushing Docker Image"
    
    local component=$1
    local dockerfile=$2
    local service_name=$3
    
    # Build and push Docker image
    echo -e "${GREEN}Building and pushing Docker image for ${component}...${NC}"
    IMAGE_NAME="gcr.io/${PROJECT_ID}/${service_name}-${ENVIRONMENT}:$(date +%Y%m%d%H%M%S)"
    
    echo -e "${GREEN}Using Dockerfile: ${dockerfile}${NC}"
    
    if [ "$DRY_RUN" == "true" ]; then
        echo -e "${YELLOW}DRY RUN: Would build and push Docker image: ${IMAGE_NAME}${NC}"
    else
        # Build the Docker image with optimized caching
        echo -e "${GREEN}Building Docker image: ${IMAGE_NAME}${NC}"
        docker build \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --cache-from=gcr.io/${PROJECT_ID}/${service_name}-${ENVIRONMENT}:latest \
            -t ${IMAGE_NAME} \
            -t gcr.io/${PROJECT_ID}/${service_name}-${ENVIRONMENT}:latest \
            -f ${dockerfile} .
        
        # Configure Docker to use gcloud credentials
        gcloud auth configure-docker gcr.io
        
        # Push the Docker image
        echo -e "${GREEN}Pushing Docker image: ${IMAGE_NAME}${NC}"
        docker push ${IMAGE_NAME}
        docker push gcr.io/${PROJECT_ID}/${service_name}-${ENVIRONMENT}:latest
    fi
    
    echo -e "${GREEN}Docker image built and pushed successfully.${NC}"
    
    # Return the image name
    echo ${IMAGE_NAME}
}

# Function to deploy to Cloud Run
deploy_to_cloud_run() {
    section "Deploying to Cloud Run"
    
    local component=$1
    local service_name=$2
    local image_name=$3
    
    # Get current deployment for rollback
    CURRENT_IMAGE=$(gcloud run services describe ${service_name}-${ENVIRONMENT} \
        --platform managed \
        --region ${REGION} \
        --format="value(spec.template.spec.containers[0].image)" 2>/dev/null || echo "")
    
    if [ -n "$CURRENT_IMAGE" ]; then
        echo -e "${GREEN}Current deployment image: ${CURRENT_IMAGE}${NC}"
    else
        echo -e "${YELLOW}No existing deployment found. This will be the first deployment.${NC}"
    fi
    
    # Deploy to Cloud Run
    echo -e "${GREEN}Deploying ${component} to Cloud Run...${NC}"
    
    if [ "$DRY_RUN" == "true" ]; then
        echo -e "${YELLOW}DRY RUN: Would deploy ${image_name} to Cloud Run service ${service_name}-${ENVIRONMENT}${NC}"
    else
        # Deploy with traffic splitting for canary deployment
        if [ "$ENVIRONMENT" == "prod" ] && [ -n "$CURRENT_IMAGE" ]; then
            echo -e "${GREEN}Performing canary deployment (20% traffic to new version)...${NC}"
            gcloud run services update ${service_name}-${ENVIRONMENT} \
                --image ${image_name} \
                --platform managed \
                --region ${REGION} \
                --memory=${MEMORY} \
                --cpu=${CPU} \
                --min-instances=${MIN_INSTANCES} \
                --max-instances=${MAX_INSTANCES} \
                --concurrency=80 \
                --timeout=300s \
                --set-env-vars=ENV=${ENVIRONMENT},PROJECT_ID=${PROJECT_ID} \
                --no-traffic
            
            # Create a tag for the new revision
            NEW_REVISION=$(gcloud run services describe ${service_name}-${ENVIRONMENT} \
                --platform managed \
                --region ${REGION} \
                --format="value(status.latestReadyRevision)")
            
            gcloud run services update-traffic ${service_name}-${ENVIRONMENT} \
                --platform managed \
                --region ${REGION} \
                --to-revisions=${NEW_REVISION}=20
        else
            # Standard deployment
            gcloud run deploy ${service_name}-${ENVIRONMENT} \
                --image ${image_name} \
                --platform managed \
                --region ${REGION} \
                --allow-unauthenticated \
                --memory=${MEMORY} \
                --cpu=${CPU} \
                --min-instances=${MIN_INSTANCES} \
                --max-instances=${MAX_INSTANCES} \
                --concurrency=80 \
                --timeout=300s \
                --set-env-vars=ENV=${ENVIRONMENT},PROJECT_ID=${PROJECT_ID}
        fi
    fi
    
    # Get the deployed service URL
    SERVICE_URL=$(gcloud run services describe ${service_name}-${ENVIRONMENT} \
        --platform managed \
        --region ${REGION} \
        --format='value(status.url)' 2>/dev/null || echo "")
    
    echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
    
    # Return the service URL
    echo ${SERVICE_URL}
}

# Function to verify deployment
verify_deployment() {
    section "Verifying Deployment"
    
    local service_name=$1
    local service_url=$2
    
    if [ "$DRY_RUN" == "true" ]; then
        echo -e "${YELLOW}DRY RUN: Would verify deployment at ${service_url}${NC}"
        return 0
    fi
    
    # Wait for the service to be fully available
    echo -e "${GREEN}Waiting for service to be fully available...${NC}"
    sleep 15
    
    # Perform basic health check
    echo -e "${GREEN}Performing health check...${NC}"
    if curl -s ${service_url}/health | grep -q "ok"; then
        echo -e "${GREEN}Health check passed!${NC}"
    else
        echo -e "${RED}Health check failed!${NC}"
        return 1
    fi
    
    # Perform basic load test if in production
    if [ "$ENVIRONMENT" == "prod" ]; then
        echo -e "${GREEN}Performing basic load test...${NC}"
        
        # Check if ab (Apache Benchmark) is installed
        if command -v ab &> /dev/null; then
            # Simple load test with 10 concurrent requests
            ab -n 100 -c 10 ${service_url}/health
        else
            echo -e "${YELLOW}Apache Benchmark (ab) not found. Skipping load test.${NC}"
        fi
    fi
    
    # Check for errors in logs
    echo -e "${GREEN}Checking logs for errors...${NC}"
    ERROR_COUNT=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${service_name}-${ENVIRONMENT} AND severity>=ERROR" --limit=10 --format="value(textPayload)" | wc -l)
    
    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "${YELLOW}Found ${ERROR_COUNT} errors in logs. Please check the logs for details.${NC}"
        gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${service_name}-${ENVIRONMENT} AND severity>=ERROR" --limit=10 --format="table(timestamp,severity,textPayload)"
    else
        echo -e "${GREEN}No errors found in logs.${NC}"
    fi
    
    return 0
}

# Function to perform rollback
rollback() {
    section "Rolling Back Deployment"
    
    local service_name=$1
    local current_image=$2
    
    if [ -z "$current_image" ]; then
        echo -e "${RED}No previous image found for rollback.${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Rolling back to previous version: ${current_image}${NC}"
    
    if [ "$DRY_RUN" == "true" ]; then
        echo -e "${YELLOW}DRY RUN: Would roll back to ${current_image}${NC}"
    else
        gcloud run services update ${service_name}-${ENVIRONMENT} \
            --image ${current_image} \
            --platform managed \
            --region ${REGION}
        
        echo -e "${GREEN}Rollback completed.${NC}"
    fi
    
    return 0
}

# Function to complete canary deployment
complete_canary() {
    section "Completing Canary Deployment"
    
    local service_name=$1
    
    if [ "$ENVIRONMENT" != "prod" ]; then
        echo -e "${YELLOW}Canary deployment is only used in production environment.${NC}"
        return 0
    fi
    
    echo -e "${GREEN}Checking canary deployment status...${NC}"
    
    # Get the latest revision
    NEW_REVISION=$(gcloud run services describe ${service_name}-${ENVIRONMENT} \
        --platform managed \
        --region ${REGION} \
        --format="value(status.latestReadyRevision)")
    
    if [ "$DRY_RUN" == "true" ]; then
        echo -e "${YELLOW}DRY RUN: Would migrate 100% traffic to ${NEW_REVISION}${NC}"
    else
        echo -e "${GREEN}Migrating 100% traffic to new version...${NC}"
        gcloud run services update-traffic ${service_name}-${ENVIRONMENT} \
            --platform managed \
            --region ${REGION} \
            --to-revisions=${NEW_REVISION}=100
        
        echo -e "${GREEN}Canary deployment completed successfully.${NC}"
    fi
    
    return 0
}

# Function to deploy a component
deploy_component() {
    local component=$1
    local dockerfile=$2
    local service_name=$3
    
    echo -e "${GREEN}Deploying ${component}...${NC}"
    
    # Build and push Docker image
    IMAGE_NAME=$(build_and_push_image "$component" "$dockerfile" "$service_name")
    
    # Get current deployment for rollback
    CURRENT_IMAGE=$(gcloud run services describe ${service_name}-${ENVIRONMENT} \
        --platform managed \
        --region ${REGION} \
        --format="value(spec.template.spec.containers[0].image)" 2>/dev/null || echo "")
    
    # Deploy to Cloud Run
    SERVICE_URL=$(deploy_to_cloud_run "$component" "$service_name" "$IMAGE_NAME")
    
    # Verify deployment
    if ! verify_deployment "$service_name" "$SERVICE_URL"; then
        echo -e "${RED}Deployment verification failed!${NC}"
        
        if [ -n "$CURRENT_IMAGE" ]; then
            echo -e "${YELLOW}Rolling back to previous version...${NC}"
            rollback "$service_name" "$CURRENT_IMAGE"
        fi
        
        return 1
    fi
    
    # If this is a canary deployment in production, ask for confirmation to complete
    if [ "$ENVIRONMENT" == "prod" ] && [ -n "$CURRENT_IMAGE" ]; then
        echo -e "${YELLOW}Canary deployment is at 20% traffic. Do you want to complete the migration to 100%? (y/n)${NC}"
        read -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            complete_canary "$service_name"
        else
            echo -e "${YELLOW}Canary deployment remains at 20% traffic. You can complete it later with:${NC}"
            echo -e "${BLUE}./deploy_enhanced.sh $PROJECT_ID $REGION $ENVIRONMENT $component complete-canary${NC}"
        fi
    fi
    
    echo -e "${GREEN}Deployment of ${component} completed successfully!${NC}"
    return 0
}

# Function to collect performance metrics
collect_performance_metrics() {
    section "Collecting Performance Metrics"
    
    local service_name=$1
    
    if [ "$DRY_RUN" == "true" ]; then
        echo -e "${YELLOW}DRY RUN: Would collect performance metrics for ${service_name}-${ENVIRONMENT}${NC}"
        return 0
    fi
    
    echo -e "${GREEN}Collecting performance metrics for ${service_name}-${ENVIRONMENT}...${NC}"
    
    # Create a metrics file
    METRICS_FILE="metrics_${service_name}_${ENVIRONMENT}_$(date +%Y%m%d%H%M%S).txt"
    
    # Collect CPU utilization
    echo "CPU Utilization:" > $METRICS_FILE
    gcloud monitoring metrics list --filter="metric.type=run.googleapis.com/container/cpu/utilization" >> $METRICS_FILE
    
    # Collect memory utilization
    echo -e "\nMemory Utilization:" >> $METRICS_FILE
    gcloud monitoring metrics list --filter="metric.type=run.googleapis.com/container/memory/utilization" >> $METRICS_FILE
    
    # Collect request count
    echo -e "\nRequest Count:" >> $METRICS_FILE
    gcloud monitoring metrics list --filter="metric.type=run.googleapis.com/request_count" >> $METRICS_FILE
    
    # Collect response latencies
    echo -e "\nResponse Latencies:" >> $METRICS_FILE
    gcloud monitoring metrics list --filter="metric.type=run.googleapis.com/request_latencies" >> $METRICS_FILE
    
    echo -e "${GREEN}Performance metrics collected and saved to ${METRICS_FILE}${NC}"
    return 0
}

# Main function
main() {
    section "AI Orchestra Enhanced Deployment"
    
    echo -e "${BOLD}Project:${NC} $PROJECT_ID"
    echo -e "${BOLD}Region:${NC} $REGION"
    echo -e "${BOLD}Environment:${NC} $ENVIRONMENT"
    echo -e "${BOLD}Component:${NC} $COMPONENT"
    echo -e "${BOLD}Dry Run:${NC} $DRY_RUN"
    
    # Check prerequisites
    check_prerequisites
    
    # Load environment-specific configurations
    load_environment_config
    
    # Handle special command: complete-canary
    if [ "$COMPONENT" == "complete-canary" ]; then
        echo -e "${GREEN}Completing canary deployment for all services...${NC}"
        complete_canary "ai-orchestra"
        complete_canary "mcp-server"
        exit 0
    fi
    
    # Deploy components based on selection
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "ai-orchestra" ]; then
        # Check if Dockerfile.optimized exists, otherwise use regular Dockerfile
        if [ -f "ai-orchestra/Dockerfile.optimized" ]; then
            DOCKERFILE="ai-orchestra/Dockerfile.optimized"
        else
            DOCKERFILE="ai-orchestra/Dockerfile"
        fi
        
        deploy_component "AI Orchestra" "$DOCKERFILE" "ai-orchestra"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "mcp-server" ]; then
        # Check if Dockerfile.optimized exists, otherwise use regular Dockerfile
        if [ -f "mcp_server/Dockerfile.optimized" ]; then
            DOCKERFILE="mcp_server/Dockerfile.optimized"
        else
            DOCKERFILE="mcp_server/Dockerfile"
        fi
        
        deploy_component "MCP Server" "$DOCKERFILE" "mcp-server"
    fi
    
    # Collect performance metrics
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "ai-orchestra" ]; then
        collect_performance_metrics "ai-orchestra"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "mcp-server" ]; then
        collect_performance_metrics "mcp-server"
    fi
    
    section "Deployment Summary"
    
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
    echo -e "${GREEN}Components: ${COMPONENT}${NC}"
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "ai-orchestra" ]; then
        SERVICE_URL=$(gcloud run services describe ai-orchestra-${ENVIRONMENT} \
            --platform managed \
            --region ${REGION} \
            --format='value(status.url)' 2>/dev/null || echo "")
        echo -e "${GREEN}AI Orchestra URL: ${SERVICE_URL}${NC}"
    fi
    
    if [ "$COMPONENT" == "all" ] || [ "$COMPONENT" == "mcp-server" ]; then
        SERVICE_URL=$(gcloud run services describe mcp-server-${ENVIRONMENT} \
            --platform managed \
            --region ${REGION} \
            --format='value(status.url)' 2>/dev/null || echo "")
        echo -e "${GREEN}MCP Server URL: ${SERVICE_URL}${NC}"
    fi
}

# Run the main function
main "$@"