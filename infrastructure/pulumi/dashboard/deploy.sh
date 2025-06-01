#!/bin/bash

# Pulumi-based deployment script for Admin UI
# This script provides a one-command deployment solution using Pulumi
# Usage: ./deploy.sh [dev|prod] [preview|up|destroy]

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_color "$BLUE" "Checking prerequisites..."
    
    # Check if Pulumi is installed
    if ! command -v pulumi &> /dev/null; then
        print_color "$RED" "Error: Pulumi is not installed. Please install Pulumi first."
        echo "Visit: https://www.pulumi.com/docs/get-started/install/"
        exit 1
    fi
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        print_color "$RED" "Error: Node.js is not installed. Please install Node.js 18 or later."
        exit 1
    fi
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_color "$RED" "Error: Google Cloud SDK is not installed. Please install gcloud CLI."
        exit 1
    fi
    
    # Check if npm dependencies are installed
    if [ ! -d "node_modules" ]; then
        print_color "$YELLOW" "Installing npm dependencies..."
        npm ci
    fi
    
    print_color "$GREEN" "✓ All prerequisites met"
}

# Function to validate environment
validate_environment() {
    local env=$1
    if [[ "$env" != "dev" && "$env" != "prod" ]]; then
        print_color "$RED" "Error: Invalid environment. Use 'dev' or 'prod'"
        exit 1
    fi
}

# Function to validate action
validate_action() {
    local action=$1
    if [[ "$action" != "preview" && "$action" != "up" && "$action" != "destroy" ]]; then
        print_color "$RED" "Error: Invalid action. Use 'preview', 'up', or 'destroy'"
        exit 1
    fi
}

# Function to load environment variables
load_env_vars() {
    local env=$1
    
    # Check for environment file
    local env_file="../../../.env.${env}"
    if [ -f "$env_file" ]; then
        print_color "$BLUE" "Loading environment variables from $env_file"
        export $(cat "$env_file" | grep -v '^#' | xargs)
    else
        print_color "$YELLOW" "Warning: No environment file found at $env_file"
        print_color "$YELLOW" "Make sure required environment variables are set"
    fi
    
    # Verify required environment variables
    local required_vars=(
        "GCP_PROJECT_ID"
        "PULUMI_ACCESS_TOKEN"
        "GCP_SA_KEY"
        "API_URL"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            print_color "$RED" "Error: Required environment variable $var is not set"
            exit 1
        fi
    done
}

# Function to configure GCP authentication
configure_gcp() {
    print_color "$BLUE" "Configuring GCP authentication..."
    
    # Create temporary key file
    local key_file="/tmp/gcp-key-$$.json"
    echo "$GCP_SA_KEY" > "$key_file"
    
    # Authenticate with GCP
    gcloud auth activate-service-account --key-file="$key_file"
    gcloud config set project "$GCP_PROJECT_ID"
    
    # Configure Docker for GCR
    gcloud auth configure-docker --quiet
    
    # Clean up key file
    rm -f "$key_file"
    
    print_color "$GREEN" "✓ GCP authentication configured"
}

# Function to select Pulumi stack
select_stack() {
    local env=$1
    local stack_name="${env}"
    
    print_color "$BLUE" "Selecting Pulumi stack: $stack_name"
    
    # Create stack if it doesn't exist
    if ! pulumi stack ls | grep -q "$stack_name"; then
        print_color "$YELLOW" "Creating new stack: $stack_name"
        pulumi stack init "$stack_name"
    else
        pulumi stack select "$stack_name"
    fi
    
    # Copy environment-specific config
    if [ -f "Pulumi.${env}.yaml" ]; then
        print_color "$BLUE" "Applying environment-specific configuration"
        cp "Pulumi.${env}.yaml" "Pulumi.${stack_name}.yaml"
    fi
}

# Function to configure Pulumi stack
configure_stack() {
    local env=$1
    
    print_color "$BLUE" "Configuring Pulumi stack..."
    
    # Set configuration values
    pulumi config set gcp:project "$GCP_PROJECT_ID"
    pulumi config set gcp:region "${GCP_REGION:-us-central1}"
    pulumi config set apiUrl "$API_URL"
    
    # Set secrets
    pulumi config set --secret apiKey "${API_KEY:-}"
    pulumi config set --secret gcpServiceAccountKey "$GCP_SA_KEY"
    
    # Set optional values
    [ -n "${ALERT_CHANNEL:-}" ] && pulumi config set alertChannelId "$ALERT_CHANNEL"
    
    print_color "$GREEN" "✓ Stack configuration complete"
}

# Function to run Pulumi command
run_pulumi() {
    local action=$1
    local env=$2
    
    case $action in
        preview)
            print_color "$BLUE" "Running Pulumi preview..."
            pulumi preview --diff
            ;;
        up)
            print_color "$BLUE" "Deploying infrastructure with Pulumi..."
            
            # Add confirmation for production
            if [ "$env" = "prod" ]; then
                print_color "$YELLOW" "⚠️  You are about to deploy to PRODUCTION!"
                read -p "Are you sure? (yes/no): " confirm
                if [ "$confirm" != "yes" ]; then
                    print_color "$RED" "Deployment cancelled"
                    exit 0
                fi
            fi
            
            # Run deployment
            pulumi up --yes --skip-preview
            
            # Show outputs
            print_color "$GREEN" "✓ Deployment complete!"
            print_color "$BLUE" "Stack outputs:"
            pulumi stack output --json | jq '.'
            ;;
        destroy)
            print_color "$YELLOW" "⚠️  Destroying infrastructure..."
            
            # Add confirmation
            read -p "Are you sure you want to destroy the $env infrastructure? (yes/no): " confirm
            if [ "$confirm" != "yes" ]; then
                print_color "$RED" "Destruction cancelled"
                exit 0
            fi
            
            pulumi destroy --yes
            print_color "$GREEN" "✓ Infrastructure destroyed"
            ;;
    esac
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <environment> <action>"
    echo ""
    echo "Environments:"
    echo "  dev    - Development environment"
    echo "  prod   - Production environment"
    echo ""
    echo "Actions:"
    echo "  preview  - Preview changes without applying"
    echo "  up       - Deploy infrastructure"
    echo "  destroy  - Destroy infrastructure"
    echo ""
    echo "Examples:"
    echo "  $0 dev preview    # Preview dev changes"
    echo "  $0 dev up         # Deploy to dev"
    echo "  $0 prod up        # Deploy to production"
    echo "  $0 dev destroy    # Destroy dev infrastructure"
}

# Main execution
main() {
    # Check arguments
    if [ $# -ne 2 ]; then
        show_usage
        exit 1
    fi
    
    local env=$1
    local action=$2
    
    # Validate inputs
    validate_environment "$env"
    validate_action "$action"
    
    # Change to script directory
    cd "$(dirname "$0")"
    
    # Run deployment steps
    check_prerequisites
    load_env_vars "$env"
    configure_gcp
    select_stack "$env"
    configure_stack "$env"
    run_pulumi "$action" "$env"
}

# Run main function
main "$@"
