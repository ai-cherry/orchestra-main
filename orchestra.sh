#!/bin/bash
# orchestra.sh - Unified workflow tool for AI Orchestra
# This script provides a centralized interface for all common development tasks

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
CONFIG_DIR="$HOME/.orchestra"
HISTORY_FILE="$CONFIG_DIR/workflow_history.txt"
CONFIG_FILE="$CONFIG_DIR/config.json"
MAX_HISTORY=10

# Create configuration directory if it doesn't exist
mkdir -p "$CONFIG_DIR"
touch "$HISTORY_FILE"

# Function to print section header
section() {
    echo ""
    echo -e "${BOLD}${BLUE}==== $1 ====${NC}"
    echo ""
}

# Function to record command in history
record_command() {
    local cmd="$1"
    
    # Create a temporary file
    local temp_file=$(mktemp)
    
    # Add the new command at the beginning
    echo "$cmd" > "$temp_file"
    
    # Add existing history, limited to MAX_HISTORY-1 entries
    if [ -f "$HISTORY_FILE" ]; then
        head -n $(($MAX_HISTORY - 1)) "$HISTORY_FILE" >> "$temp_file"
    fi
    
    # Replace the history file with the temporary file
    mv "$temp_file" "$HISTORY_FILE"
}

# Function to get recent commands
get_recent_commands() {
    if [ -f "$HISTORY_FILE" ]; then
        cat "$HISTORY_FILE" | head -n 5
    fi
}

# Function to detect environment
detect_environment() {
    # Check for .dev_mode file
    if [ -f .dev_mode ] && [ "$(cat .dev_mode)" == "true" ]; then
        echo "dev"
    else
        # Check for environment variable
        if [ "$DEPLOYMENT_ENVIRONMENT" == "production" ] || [ "$DEPLOYMENT_ENVIRONMENT" == "prod" ]; then
            echo "prod"
        else
            echo "dev"
        fi
    fi
}

# Function to get project ID
get_project_id() {
    # Try to get from environment variable
    if [ -n "$GCP_PROJECT_ID" ]; then
        echo "$GCP_PROJECT_ID"
    # Try to get from gcloud config
    elif command -v gcloud &> /dev/null; then
        gcloud config get-value project 2>/dev/null || echo "cherry-ai-project"
    else
        echo "cherry-ai-project"
    fi
}

# Function to get region
get_region() {
    # Try to get from environment variable
    if [ -n "$GCP_REGION" ]; then
        echo "$GCP_REGION"
    # Try to get from gcloud config
    elif command -v gcloud &> /dev/null; then
        gcloud config get-value compute/region 2>/dev/null || echo "us-west4"
    else
        echo "us-west4"
    fi
}

# Function to suggest commands based on context
suggest_commands() {
    local env=$(detect_environment)
    local suggestions=()
    
    # Check if we're in a git repository
    if git rev-parse --is-inside-work-tree &> /dev/null; then
        # Check if there are uncommitted changes
        if ! git diff-index --quiet HEAD --; then
            suggestions+=("git:Commit and push changes")
        fi
    fi
    
    # Check if there are deployment-related files
    if [ -f "deploy_with_adc.sh.updated" ] || [ -f "deploy_with_adc.sh" ]; then
        suggestions+=("deploy:Deploy to Cloud Run ($env environment)")
    fi
    
    # Check if there are Docker-related files
    if [ -f "Dockerfile" ] || [ -f "docker-compose.yml" ]; then
        suggestions+=("docker:Build and run Docker container")
    fi
    
    # Check if there are Python files
    if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
        suggestions+=("dev:Start local development environment")
        suggestions+=("test:Run tests")
    fi
    
    # Check for MCP server configurations
    if [ -d "mcp-servers" ] || [ -d "mcp_server" ]; then
        suggestions+=("mcp:Manage MCP servers")
    fi
    
    # Always suggest these commands
    suggestions+=("auth:Manage authentication")
    suggestions+=("secrets:Manage GitHub and GCP secrets")
    suggestions+=("logs:View Cloud Run logs")
    
    # Return the suggestions
    for suggestion in "${suggestions[@]}"; do
        echo "$suggestion"
    done
}

# Function to show command menu with intelligent suggestions
show_menu() {
    section "AI Orchestra Workflow Tool"
    
    echo -e "${BOLD}Project:${NC} $(get_project_id)"
    echo -e "${BOLD}Region:${NC} $(get_region)"
    echo -e "${BOLD}Environment:${NC} $(detect_environment)"
    echo ""
    
    echo -e "${BOLD}Recent commands:${NC}"
    get_recent_commands | while read cmd; do
        echo "  - orchestra $cmd"
    done
    
    echo ""
    echo -e "${BOLD}Suggested commands:${NC}"
    suggest_commands | while IFS=':' read -r cmd desc; do
        echo "  $cmd - $desc"
    done
    
    echo ""
    echo -e "${BOLD}Available commands:${NC}"
    echo "  dev       - Start local development environment"
    echo "  deploy    - Deploy to Cloud Run"
    echo "  test      - Run tests"
    echo "  auth      - Manage authentication"
    echo "  secrets   - Manage GitHub and GCP secrets"
    echo "  logs      - View Cloud Run logs"
    echo "  docker    - Build and run Docker container"
    echo "  git       - Git operations"
    echo "  mode      - Toggle development/production mode"
    echo "  mcp       - Manage MCP servers"
    echo "  help      - Show this help message"
}

# Function to start local development environment
cmd_dev() {
    section "Starting Local Development Environment"
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Docker is not running. Please start Docker and try again.${NC}"
        exit 1
    fi
    
    # Check if docker-compose.yml exists
    if [ -f "docker-compose.yml" ]; then
        echo -e "${GREEN}Starting services with Docker Compose...${NC}"
        docker-compose up -d
    else
        echo -e "${YELLOW}No docker-compose.yml found. Starting Python development server...${NC}"
        
        # Check if this is a Python project
        if [ -f "pyproject.toml" ]; then
            echo -e "${GREEN}Starting Poetry development server...${NC}"
            poetry run python -m ai_orchestra.run --reload
        elif [ -f "requirements.txt" ]; then
            echo -e "${GREEN}Starting Python development server...${NC}"
            python -m ai_orchestra.run --reload
        else
            echo -e "${RED}No Python project found. Please run this command in a Python project directory.${NC}"
            exit 1
        fi
    fi
}

# Function to deploy to Cloud Run
cmd_deploy() {
    section "Deploying to Cloud Run"
    
    local env="${1:-$(detect_environment)}"
    local component="${2:-all}"
    
    echo -e "${GREEN}Deploying to ${BOLD}$env${NC}${GREEN} environment...${NC}"
    
    # Check if deploy_with_adc.sh.updated exists
    if [ -f "deploy_with_adc.sh.updated" ]; then
        ./deploy_with_adc.sh.updated "$env" "$component"
    elif [ -f "deploy_with_adc.sh" ]; then
        ./deploy_with_adc.sh "$env" "$component"
    elif [ -f "deploy.sh" ]; then
        ./deploy.sh "$env" "$component"
    else
        echo -e "${RED}No deployment script found. Please create deploy.sh or deploy_with_adc.sh.${NC}"
        exit 1
    fi
}

# Function to run tests
cmd_test() {
    section "Running Tests"
    
    # Check if this is a Python project
    if [ -f "pyproject.toml" ]; then
        echo -e "${GREEN}Running tests with Poetry...${NC}"
        poetry run pytest
    elif [ -f "requirements.txt" ]; then
        echo -e "${GREEN}Running tests with pytest...${NC}"
        python -m pytest
    else
        echo -e "${RED}No Python project found. Please run this command in a Python project directory.${NC}"
        exit 1
    fi
}

# Function to manage authentication
cmd_auth() {
    section "Managing Authentication"
    
    echo "Select authentication type:"
    echo "1) GitHub authentication"
    echo "2) GCP authentication"
    echo "3) Both GitHub and GCP authentication"
    echo -e "${YELLOW}Enter your choice (1-3):${NC}"
    read -n 1 -r
    echo
    
    case $REPLY in
        1)
            # GitHub authentication
            if [ -f "github_auth.sh" ]; then
                ./github_auth.sh
            else
                echo -e "${RED}No GitHub authentication script found. Please create github_auth.sh.${NC}"
                exit 1
            fi
            ;;
        2)
            # GCP authentication
            if [ -f "setup_wif.sh" ]; then
                ./setup_wif.sh
            else
                echo -e "${RED}No GCP authentication script found. Please create setup_wif.sh.${NC}"
                exit 1
            fi
            ;;
        3)
            # Both GitHub and GCP authentication
            if [ -f "github_auth.sh" ]; then
                ./github_auth.sh
            else
                echo -e "${RED}No GitHub authentication script found. Please create github_auth.sh.${NC}"
                exit 1
            fi
            
            if [ -f "setup_wif.sh" ]; then
                ./setup_wif.sh
            else
                echo -e "${RED}No GCP authentication script found. Please create setup_wif.sh.${NC}"
                exit 1
            fi
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
}

# Function to manage secrets
cmd_secrets() {
    section "Managing Secrets"
    
    echo "Select secret management operation:"
    echo "1) Verify GitHub secrets"
    echo "2) Sync local .env to GitHub secrets"
    echo "3) Create template .env from GitHub secrets"
    echo -e "${YELLOW}Enter your choice (1-3):${NC}"
    read -n 1 -r
    echo
    
    case $REPLY in
        1)
            # Verify GitHub secrets
            if [ -f "verify_github_secrets.sh" ]; then
                ./verify_github_secrets.sh
            else
                echo -e "${RED}No GitHub secrets verification script found. Please create verify_github_secrets.sh.${NC}"
                exit 1
            fi
            ;;
        2)
            # Sync local .env to GitHub secrets
            if [ -f ".env" ]; then
                echo -e "${GREEN}Syncing secrets from local .env to GitHub...${NC}"
                
                # Get GitHub repository
                GITHUB_REPO=$(git config --get remote.origin.url | sed -n 's/.*github.com[:/]\([^/]*\/[^.]*\).*/\1/p')
                
                if [ -z "$GITHUB_REPO" ]; then
                    echo -e "${YELLOW}Unable to automatically determine repository. Please enter your GitHub repository (format: owner/repo):${NC}"
                    read GITHUB_REPO
                fi
                
                # Source the GitHub authentication utility
                if [ -f "github_auth.sh" ]; then
                    source github_auth.sh
                    GITHUB_TOKEN=$(get_github_token)
                    authenticate_github "$GITHUB_TOKEN"
                fi
                
                # Sync secrets
                while IFS='=' read -r key value; do
                    # Skip comments and empty lines
                    [[ $key == \#* ]] && continue
                    [[ -z "$key" ]] && continue
                    
                    # Trim whitespace
                    key=$(echo "$key" | xargs)
                    value=$(echo "$value" | xargs)
                    
                    echo "Setting GitHub secret: $key"
                    echo "$value" | gh secret set "$key" -R "$GITHUB_REPO"
                done < .env
                
                echo -e "${GREEN}Secrets synced successfully!${NC}"
            else
                echo -e "${RED}No .env file found. Please create .env file first.${NC}"
                exit 1
            fi
            ;;
        3)
            # Create template .env from GitHub secrets
            echo -e "${GREEN}Creating template .env from GitHub secrets...${NC}"
            
            # Get GitHub repository
            GITHUB_REPO=$(git config --get remote.origin.url | sed -n 's/.*github.com[:/]\([^/]*\/[^.]*\).*/\1/p')
            
            if [ -z "$GITHUB_REPO" ]; then
                echo -e "${YELLOW}Unable to automatically determine repository. Please enter your GitHub repository (format: owner/repo):${NC}"
                read GITHUB_REPO
            fi
            
            # Source the GitHub authentication utility
            if [ -f "github_auth.sh" ]; then
                source github_auth.sh
                GITHUB_TOKEN=$(get_github_token)
                authenticate_github "$GITHUB_TOKEN"
            fi
            
            # Create backup of existing .env
            if [ -f .env ]; then
                cp .env .env.bak
                echo -e "${GREEN}Created backup of existing .env at .env.bak${NC}"
            fi
            
            # Get list of secrets
            secrets=$(gh secret list -R "$GITHUB_REPO" --json name --jq '.[].name')
            
            # Create new .env file
            > .env
            for secret in $secrets; do
                echo "Adding $secret to .env"
                echo "$secret=<value stored in GitHub>" >> .env
            done
            
            echo -e "${GREEN}Template .env created successfully!${NC}"
            echo -e "${YELLOW}Note: Values are placeholders. Fill in actual values as needed.${NC}"
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
}

# Function to view Cloud Run logs
cmd_logs() {
    section "Viewing Cloud Run Logs"
    
    local env="${1:-$(detect_environment)}"
    local service="${2:-ai-orchestra}"
    
    echo -e "${GREEN}Viewing logs for ${BOLD}$service${NC}${GREEN} in ${BOLD}$env${NC}${GREEN} environment...${NC}"
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}Google Cloud SDK (gcloud) is not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # View logs
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$service-$env" --limit=50 --format="table(timestamp,severity,textPayload)"
}

# Function to build and run Docker container
cmd_docker() {
    section "Docker Operations"
    
    echo "Select Docker operation:"
    echo "1) Build Docker image"
    echo "2) Run Docker container"
    echo "3) Build and run Docker container"
    echo "4) Stop Docker container"
    echo -e "${YELLOW}Enter your choice (1-4):${NC}"
    read -n 1 -r
    echo
    
    case $REPLY in
        1)
            # Build Docker image
            echo -e "${GREEN}Building Docker image...${NC}"
            docker build -t ai-orchestra .
            ;;
        2)
            # Run Docker container
            echo -e "${GREEN}Running Docker container...${NC}"
            docker run -p 8000:8000 ai-orchestra
            ;;
        3)
            # Build and run Docker container
            echo -e "${GREEN}Building and running Docker container...${NC}"
            docker build -t ai-orchestra .
            docker run -p 8000:8000 ai-orchestra
            ;;
        4)
            # Stop Docker container
            echo -e "${GREEN}Stopping Docker container...${NC}"
            docker stop $(docker ps -q --filter ancestor=ai-orchestra)
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
}

# Function for Git operations
cmd_git() {
    section "Git Operations"
    
    echo "Select Git operation:"
    echo "1) Commit and push changes"
    echo "2) Pull latest changes"
    echo "3) View status"
    echo "4) View log"
    echo -e "${YELLOW}Enter your choice (1-4):${NC}"
    read -n 1 -r
    echo
    
    case $REPLY in
        1)
            # Commit and push changes
            echo -e "${GREEN}Committing and pushing changes...${NC}"
            echo -e "${YELLOW}Enter commit message:${NC}"
            read commit_message
            git add .
            git commit -m "$commit_message"
            git push
            ;;
        2)
            # Pull latest changes
            echo -e "${GREEN}Pulling latest changes...${NC}"
            git pull
            ;;
        3)
            # View status
            echo -e "${GREEN}Git status:${NC}"
            git status
            ;;
        4)
            # View log
            echo -e "${GREEN}Git log:${NC}"
            git log --oneline -n 10
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
}

# Function to toggle development/production mode
cmd_mode() {
    section "Toggle Development/Production Mode"
    
    # Check if toggle_dev_mode.sh exists
    if [ -f "toggle_dev_mode.sh" ]; then
        ./toggle_dev_mode.sh
    else
        # Check current mode
        if [ -f .dev_mode ]; then
            DEV_MODE=$(cat .dev_mode)
        else
            DEV_MODE="false"
        fi
        
        if [ "$DEV_MODE" == "true" ]; then
            echo -e "${YELLOW}Currently in DEVELOPMENT mode.${NC}"
            echo -e "${YELLOW}Do you want to switch to PRODUCTION mode? (y/n)${NC}"
            read -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "false" > .dev_mode
                echo -e "${GREEN}Switched to PRODUCTION mode.${NC}"
                echo -e "${BLUE}Run the following commands to apply the change:${NC}"
                echo "export WIF_DEV_MODE=false"
                echo "export WIF_BYPASS_CSRF=false"
            else
                echo -e "${YELLOW}Remaining in DEVELOPMENT mode.${NC}"
            fi
        else
            echo -e "${YELLOW}Currently in PRODUCTION mode.${NC}"
            echo -e "${YELLOW}Do you want to switch to DEVELOPMENT mode? (y/n)${NC}"
            read -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "true" > .dev_mode
                echo -e "${GREEN}Switched to DEVELOPMENT mode.${NC}"
                echo -e "${BLUE}Run the following commands to apply the change:${NC}"
                echo "export WIF_DEV_MODE=true"
                echo "export WIF_BYPASS_CSRF=true"
            else
                echo -e "${YELLOW}Remaining in PRODUCTION mode.${NC}"
            fi
        fi
    fi
}

# Function to manage MCP servers
cmd_mcp() {
    section "Managing MCP Servers"
    
    # Find available MCP servers
    local mcp_servers=()
    local yaml_files=()
    
    # Check in mcp-servers directory
    if [ -d "mcp-servers" ]; then
        for yaml_file in mcp-servers/*.yaml; do
            if [ -f "$yaml_file" ]; then
                server_name=$(basename "$yaml_file" .yaml)
                mcp_servers+=("$server_name")
                yaml_files+=("$yaml_file")
            fi
        done
    fi
    
    # Check in mcp_server directory
    if [ -d "mcp_server" ]; then
        mcp_servers+=("core-mcp")
        yaml_files+=("mcp_server")
    fi
    
    # Check if start_gcp_tools_for_ai.sh exists
    if [ -f "start_gcp_tools_for_ai.sh" ]; then
        # Add as special case if not already found
        local found=0
        for server in "${mcp_servers[@]}"; do
            if [ "$server" = "gcp-resources" ]; then
                found=1
                break
            fi
        done
        
        if [ $found -eq 0 ]; then
            mcp_servers+=("gcp-resources")
            yaml_files+=("mcp-servers/gcp-resources-server.yaml")
        fi
    fi
    
    echo "Select MCP server operation:"
    echo "1) Start all MCP servers"
    echo "2) Start specific MCP server"
    echo "3) Install MCP servers as systemd services (auto-start)"
    echo "4) Check MCP server status"
    echo "5) Stop all MCP servers"
    echo -e "${YELLOW}Enter your choice (1-5):${NC}"
    read -n 1 -r
    echo
    
    case $REPLY in
        1)
            # Start all MCP servers
            echo -e "${GREEN}Starting all MCP servers...${NC}"
            
            # Start core MCP server if exists
            if [ -d "mcp_server" ]; then
                echo -e "${GREEN}Starting core MCP server...${NC}"
                if [ -f "mcp_server/start.sh" ]; then
                    mcp_server/start.sh &
                else
                    # Alternative startup
                    (cd mcp_server && python -m mcp_server.main) &
                fi
                sleep 2  # Give time for the core server to start
            fi
            
            # Start GCP Resources MCP server if exists
            if [ -f "start_gcp_tools_for_ai.sh" ]; then
                echo -e "${GREEN}Starting GCP Resources MCP server...${NC}"
                ./start_gcp_tools_for_ai.sh &
            fi
            
            # Start other MCP servers from mcp-servers directory
            for i in "${!mcp_servers[@]}"; do
                server="${mcp_servers[$i]}"
                yaml="${yaml_files[$i]}"
                
                # Skip core and gcp-resources as they're handled separately
                if [ "$server" == "core-mcp" ] || [ "$server" == "gcp-resources" ]; then
                    continue
                fi
                
                echo -e "${GREEN}Starting $server MCP server...${NC}"
                
                # Get startup command from yaml
                if [ -f "$yaml" ]; then
                    cmd=$(grep -A5 "startup:" "$yaml" | grep "command:" | cut -d: -f2- | sed 's/^[ \t]*//')
                    working_dir=$(grep -A5 "startup:" "$yaml" | grep "working_directory:" | cut -d: -f2- | sed 's/^[ \t]*//')
                    
                    if [ -n "$cmd" ]; then
                        if [ -n "$working_dir" ]; then
                            (cd "$working_dir" && eval "$cmd") &
                        else
                            eval "$cmd" &
                        fi
                    fi
                fi
            done
            
            echo -e "${GREEN}All MCP servers started successfully!${NC}"
            ;;
        2)
            # Start specific MCP server
            echo -e "${GREEN}Select MCP server to start:${NC}"
            for i in "${!mcp_servers[@]}"; do
                echo "$((i+1))) ${mcp_servers[$i]}"
            done
            
            echo -e "${YELLOW}Enter your choice (1-${#mcp_servers[@]}):${NC}"
            read server_choice
            
            if ! [[ "$server_choice" =~ ^[0-9]+$ ]] || [ "$server_choice" -lt 1 ] || [ "$server_choice" -gt "${#mcp_servers[@]}" ]; then
                echo -e "${RED}Invalid choice${NC}"
                exit 1
            fi
            
            server_idx=$((server_choice-1))
            server="${mcp_servers[$server_idx]}"
            yaml="${yaml_files[$server_idx]}"
            
            echo -e "${GREEN}Starting $server MCP server...${NC}"
            
            if [ "$server" == "core-mcp" ]; then
                # Start core MCP server
                if [ -f "mcp_server/start.sh" ]; then
                    mcp_server/start.sh
                else
                    # Alternative startup
                    (cd mcp_server && python -m mcp_server.main)
                fi
            elif [ "$server" == "gcp-resources" ] && [ -f "start_gcp_tools_for_ai.sh" ]; then
                # Start GCP Resources MCP server
                ./start_gcp_tools_for_ai.sh
            else
                # Get startup command from yaml
                if [ -f "$yaml" ]; then
                    cmd=$(grep -A5 "startup:" "$yaml" | grep "command:" | cut -d: -f2- | sed 's/^[ \t]*//')
                    working_dir=$(grep -A5 "startup:" "$yaml" | grep "working_directory:" | cut -d: -f2- | sed 's/^[ \t]*//')
                    
                    if [ -n "$cmd" ]; then
                        if [ -n "$working_dir" ]; then
                            (cd "$working_dir" && eval "$cmd")
                        else
                            eval "$cmd"
                        fi
                    else
                        echo -e "${RED}No startup command found for $server${NC}"
                    fi
                else
                    echo -e "${RED}No configuration found for $server${NC}"
                fi
            fi
            ;;
        3)
            # Install MCP servers as systemd services
            echo -e "${GREEN}Installing MCP servers as systemd services for auto-start...${NC}"
            
            # Check if we have sudo access
            if ! command -v sudo &> /dev/null; then
                echo -e "${RED}sudo not found. Cannot install systemd services without sudo privileges.${NC}"
                exit 1
            fi
            
            # Install core MCP server systemd service if it exists
            if [ -d "mcp_server" ] && [ -f "mcp_server/scripts/mcp-server.service" ]; then
                echo -e "${GREEN}Installing core MCP server systemd service...${NC}"
                sudo cp mcp_server/scripts/mcp-server.service /etc/systemd/system/
                sudo systemctl daemon-reload
                sudo systemctl enable mcp-server
            fi
            
            # Install GCP Resources MCP server systemd service if it exists
            if [ -f "mcp_server/scripts/gcp-resources-mcp-server.service" ]; then
                echo -e "${GREEN}Installing GCP Resources MCP server systemd service...${NC}"
                sudo cp mcp_server/scripts/gcp-resources-mcp-server.service /etc/systemd/system/
                sudo systemctl daemon-reload
                sudo systemctl enable gcp-resources-mcp-server
            fi
            
            echo -e "${GREEN}Systemd services installed successfully!${NC}"
            echo -e "${YELLOW}Start the services with:${NC}"
            echo "sudo systemctl start mcp-server"
            echo "sudo systemctl start gcp-resources-mcp-server"
            ;;
        4)
            # Check MCP server status
            echo -e "${GREEN}Checking MCP server status...${NC}"
            
            # Check if systemd services are installed
            if systemctl list-unit-files | grep -q mcp-server; then
                echo -e "${GREEN}Core MCP Server (systemd):${NC}"
                systemctl status mcp-server
            fi
            
            if systemctl list-unit-files | grep -q gcp-resources-mcp-server; then
                echo -e "${GREEN}GCP Resources MCP Server (systemd):${NC}"
                systemctl status gcp-resources-mcp-server
            fi
            
            # Check running processes
            echo -e "${GREEN}Running MCP Server Processes:${NC}"
            ps aux | grep -E "mcp_server|gcp_resources_mcp_server" | grep -v grep
            
            # Check listening ports
            echo -e "${GREEN}MCP Server Ports:${NC}"
            netstat -tuln | grep -E "8080|8085" || echo "No MCP servers found listening on expected ports"
            ;;
        5)
            # Stop all MCP servers
            echo -e "${GREEN}Stopping all MCP servers...${NC}"
            
            # Try stopping systemd services if installed
            if systemctl list-unit-files | grep -q mcp-server; then
                echo -e "${GREEN}Stopping core MCP server systemd service...${NC}"
                sudo systemctl stop mcp-server
            fi
            
            if systemctl list-unit-files | grep -q gcp-resources-mcp-server; then
                echo -e "${GREEN}Stopping GCP Resources MCP server systemd service...${NC}"
                sudo systemctl stop gcp-resources-mcp-server
            fi
            
            # Kill any remaining processes
            echo -e "${GREEN}Killing any remaining MCP server processes...${NC}"
            pkill -f "mcp_server.main" || true
            pkill -f "gcp_resources_mcp_server" || true
            
            echo -e "${GREEN}All MCP servers stopped successfully!${NC}"
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
}

# Main function
main() {
    if [ $# -eq 0 ]; then
        show_menu
        exit 0
    fi
    
    command=$1
    shift
    
    case "$command" in
        "dev")
            cmd_dev "$@"
            record_command "dev"
            ;;
        "deploy")
            cmd_deploy "$@"
            record_command "deploy $*"
            ;;
        "test")
            cmd_test "$@"
            record_command "test"
            ;;
        "auth")
            cmd_auth "$@"
            record_command "auth"
            ;;
        "secrets")
            cmd_secrets "$@"
            record_command "secrets"
            ;;
        "logs")
            cmd_logs "$@"
            record_command "logs $*"
            ;;
        "docker")
            cmd_docker "$@"
            record_command "docker"
            ;;
        "git")
            cmd_git "$@"
            record_command "git"
            ;;
        "mode")
            cmd_mode "$@"
            record_command "mode"
            ;;
        "mcp")
            cmd_mcp "$@"
            record_command "mcp"
            ;;
        "help")
            show_menu
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            show_menu
            exit 1
            ;;
    esac
}

main "$@"
