#!/bin/bash
# Integrated script to run Terraform and Vertex AI Agent Manager
# This script initializes infrastructure using Terraform and then
# registers it with the Vertex AI Agent Manager

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Usage information
function show_usage {
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  init                Run infrastructure initialization"
    echo "  deploy <env>        Deploy infrastructure to an environment (dev, stage, prod)"
    echo "  create-team <name>  Create and deploy an agent team"
    echo "  monitor             Monitor resource usage and cost"
    echo
    echo "Options:"
    echo "  --verbose, -v       Show detailed output"
    echo
    echo "Examples:"
    echo "  $0 init             Initialize the infrastructure"
    echo "  $0 deploy dev       Deploy infrastructure to dev environment"
    echo "  $0 create-team clinical-trial-followup"
    echo "  $0 monitor          Show resource usage and cost"
}

# Check if Vertex AI Agent Manager is installed
function check_vertex_client {
    if ! python -c "import packages.vertex_client" 2>/dev/null; then
        echo -e "${YELLOW}Vertex AI Agent Manager not found. Installing...${NC}"
        cd ../packages/vertex_client
        pip install -e .
        cd ../../infra
    fi
}

# Run initialization
function run_init {
    echo -e "${GREEN}Running infrastructure initialization...${NC}"
    
    # First, run the basic initialization script
    ./init.sh
    
    # Then, trigger the Vertex AI Agent Manager
    echo -e "${GREEN}Registering with Vertex AI Agent Manager...${NC}"
    python -c "from packages.vertex_client import trigger_vertex_task; trigger_vertex_task('run init script')"
    
    echo -e "${GREEN}Initialization complete!${NC}"
}

# Deploy to an environment
function deploy_env {
    local env=$1
    
    if [[ ! "$env" =~ ^(dev|stage|prod)$ ]]; then
        echo -e "${RED}Error: Invalid environment. Must be one of: dev, stage, prod${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Deploying infrastructure to $env environment...${NC}"
    
    # Trigger the Vertex AI Agent Manager
    python -c "from packages.vertex_client import trigger_vertex_task; print(trigger_vertex_task('apply terraform $env'))"
    
    echo -e "${GREEN}Deployment to $env complete!${NC}"
}

# Create and deploy an agent team
function create_team {
    local team_name=$1
    
    if [[ -z "$team_name" ]]; then
        echo -e "${RED}Error: Missing team name${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Creating agent team: $team_name...${NC}"
    
    # Trigger the Vertex AI Agent Manager
    python -c "from packages.vertex_client import trigger_vertex_task; print(trigger_vertex_task('create agent team $team_name'))"
    
    echo -e "${GREEN}Agent team created: $team_name${NC}"
}

# Monitor resource usage and cost
function monitor_resources {
    echo -e "${GREEN}Monitoring resource usage and cost...${NC}"
    
    # Trigger the Vertex AI Agent Manager
    python -c "from packages.vertex_client import trigger_vertex_task; 
              result = trigger_vertex_task('monitor resources');
              
              if result['status'] == 'success':
                  costs = result['monitoring_data']['costs']
                  resources = result['monitoring_data']['resources']
                  
                  print('\nCosts:')
                  print(f'  Daily: \${costs[\"estimated_daily\"]:.2f}')
                  print(f'  Monthly: \${costs[\"estimated_monthly\"]:.2f}')
                  
                  print('\nResource Usage:')
                  print(f'  Cloud Run: {resources[\"cloud_run\"][\"instances\"]} instances, '
                        f'{resources[\"cloud_run\"][\"cpu_utilization\"]*100:.1f}% CPU, '
                        f'{resources[\"cloud_run\"][\"memory_utilization\"]*100:.1f}% Memory')
                  print(f'  Firestore: {resources[\"firestore\"][\"read_ops\"]} reads, '
                        f'{resources[\"firestore\"][\"write_ops\"]} writes, '
                        f'{resources[\"firestore\"][\"delete_ops\"]} deletes')
                  print(f'  Vertex AI: {resources[\"vertex_ai\"][\"vector_searches\"]} vector searches, '
                        f'{resources[\"vertex_ai\"][\"embeddings_generated\"]} embeddings generated')
              else:
                  print(f'\nError monitoring resources: {result.get(\"error\", \"Unknown error\")}')
              "
    
    echo -e "${GREEN}Monitoring complete!${NC}"
}

# Main script logic
if [[ $# -lt 1 ]]; then
    show_usage
    exit 1
fi

# Check for Python Vertex client
check_vertex_client

# Process commands
case "$1" in
    init)
        run_init
        ;;
    deploy)
        if [[ $# -lt 2 ]]; then
            echo -e "${RED}Error: Missing environment parameter${NC}"
            show_usage
            exit 1
        fi
        deploy_env "$2"
        ;;
    create-team)
        if [[ $# -lt 2 ]]; then
            echo -e "${RED}Error: Missing team name parameter${NC}"
            show_usage
            exit 1
        fi
        create_team "$2"
        ;;
    monitor)
        monitor_resources
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo -e "${RED}Error: Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac

exit 0
