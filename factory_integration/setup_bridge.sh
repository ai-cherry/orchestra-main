#!/bin/bash

# Factory AI Bridge Setup Script
# This script sets up the Factory AI integration bridge with proper
# environment validation, Lambda API integration, and Pulumi configuration

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Validate required environment variables
validate_environment() {
    log_info "Validating environment variables..."
    
    local required_vars=(
        "FACTORY_AI_API_KEY"
        "LAMBDA_API_KEY"
        "POSTGRES_CONNECTION_STRING"
        "WEAVIATE_URL"
        "WEAVIATE_API_KEY"
        "REDIS_URL"
        "PULUMI_CONFIG_PASSPHRASE"
    )
    
    local optional_vars=(
        "JAEGER_ENDPOINT"
        "PROMETHEUS_PORT"
        "FACTORY_AI_BASE_URL"
    )
    
    local missing_vars=()
    
    # Check required variables
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        else
            log_success "$var is set"
        fi
    done
    
    # Check optional variables
    for var in "${optional_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_warning "$var is not set (optional)"
        else
            log_success "$var is set"
        fi
    done
    
    # Exit if required variables are missing
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please set these variables in your .envrc file or export them before running this script."
        exit 1
    fi
    
    log_success "All required environment variables are set"
}

# Validate Lambda API access
validate_Lambda_api() {
    log_info "Validating Lambda API access..."
    
    # Test Lambda API connection
    local response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer ${LAMBDA_API_KEY}" \
        "https://cloud.lambdalabs.com/api/v1/account")
    
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)
    
    if [[ "$http_code" == "200" ]]; then
        log_success "Lambda API access validated"
        
        # Extract account info
        local email=$(echo "$body" | jq -r '.account.email // "unknown"')
        local balance=$(echo "$body" | jq -r '.account.balance // "0"')
        
        log_info "Lambda Account: $email (Balance: \$$balance)"
    else
        log_error "Failed to validate Lambda API access (HTTP $http_code)"
        echo "$body" | jq . 2>/dev/null || echo "$body"
        exit 1
    fi
}

# Setup Pulumi configuration
setup_pulumi() {
    log_info "Setting up Pulumi configuration..."
    
    # Create Pulumi directory if it doesn't exist
    mkdir -p "${PROJECT_ROOT}/pulumi"
    
    # Set Pulumi passphrase
    export PULUMI_CONFIG_PASSPHRASE="${PULUMI_CONFIG_PASSPHRASE}"
    
    # Initialize Pulumi stack if not exists
    cd "${PROJECT_ROOT}/pulumi"
    
    if [[ ! -f "Pulumi.yaml" ]]; then
        log_info "Initializing Pulumi project..."
        pulumi new python -y \
            --name "factory-ai-integration" \
            --description "Factory AI integration infrastructure" \
            --stack "dev"
    else
        log_info "Pulumi project already initialized"
    fi
    
    # Set Pulumi configuration
    pulumi config set Lambda:api_key "${LAMBDA_API_KEY}" --secret
    pulumi config set postgres:connection_string "${POSTGRES_CONNECTION_STRING}" --secret
    pulumi config set weaviate:url "${WEAVIATE_URL}"
    pulumi config set weaviate:api_key "${WEAVIATE_API_KEY}" --secret
    pulumi config set redis:url "${REDIS_URL}" --secret
    
    log_success "Pulumi configuration completed"
    
    cd "${PROJECT_ROOT}"
}

# Create Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    if [[ ! -d "${PROJECT_ROOT}/venv" ]]; then
        python3 -m venv "${PROJECT_ROOT}/venv"
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "${PROJECT_ROOT}/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install required packages
    log_info "Installing Python dependencies..."
    pip install -r "${PROJECT_ROOT}/requirements/factory-bridge.txt" 2>/dev/null || {
        log_warning "factory-bridge.txt not found, installing base packages..."
        pip install \
            fastapi \
            uvicorn \
            aiohttp \
            pydantic \
            pulumi \
            pulumi-lambda \
            redis \
            asyncpg \
            weaviate-client \
            prometheus-client \
            pyyaml
    }
    
    log_success "Python environment setup completed"
}

# Create systemd service files
create_systemd_services() {
    log_info "Creating systemd service files..."
    
    local service_dir="${PROJECT_ROOT}/factory_integration/services"
    mkdir -p "$service_dir"
    
    # Factory Bridge API service
    cat > "${service_dir}/factory-bridge-api.service" << EOF
[Unit]
Description=Factory AI Bridge API Gateway
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=${PROJECT_ROOT}
Environment="PATH=${PROJECT_ROOT}/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=${PROJECT_ROOT}"
EnvironmentFile=${PROJECT_ROOT}/.env
ExecStart=${PROJECT_ROOT}/venv/bin/uvicorn factory_integration.api.gateway:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Factory Context Sync service
    cat > "${service_dir}/factory-context-sync.service" << EOF
[Unit]
Description=Factory AI Context Synchronization Service
After=network.target factory-bridge-api.service

[Service]
Type=exec
User=$USER
WorkingDirectory=${PROJECT_ROOT}
Environment="PATH=${PROJECT_ROOT}/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=${PROJECT_ROOT}"
EnvironmentFile=${PROJECT_ROOT}/.env
ExecStart=${PROJECT_ROOT}/venv/bin/python -m factory_integration.context_sync
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

    log_success "Systemd service files created"
    log_info "To install services, run:"
    echo "  sudo cp ${service_dir}/*.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable factory-bridge-api factory-context-sync"
}

# Test database connections
test_connections() {
    log_info "Testing database connections..."
    
    # Test PostgreSQL
    python3 -c "
import asyncio
import asyncpg
import os

async def test_postgres():
    try:
        conn = await asyncpg.connect(os.environ['POSTGRES_CONNECTION_STRING'])
        version = await conn.fetchval('SELECT version()')
        print(f'PostgreSQL connected: {version.split()[0]} {version.split()[1]}')
        await conn.close()
        return True
    except Exception as e:
        print(f'PostgreSQL connection failed: {e}')
        return False

asyncio.run(test_postgres())
" || log_warning "PostgreSQL connection test failed"
    
    # Test Redis
    python3 -c "
import redis
import os

try:
    r = redis.from_url(os.environ['REDIS_URL'])
    r.ping()
    print('Redis connected successfully')
except Exception as e:
    print(f'Redis connection failed: {e}')
" || log_warning "Redis connection test failed"
    
    # Test Weaviate
    python3 -c "
import weaviate
import os

try:
    client = weaviate.Client(
        url=os.environ['WEAVIATE_URL'],
        auth_client_secret=weaviate.AuthApiKey(api_key=os.environ['WEAVIATE_API_KEY'])
    )
    if client.is_ready():
        print('Weaviate connected successfully')
    else:
        print('Weaviate connection failed')
except Exception as e:
    print(f'Weaviate connection failed: {e}')
" || log_warning "Weaviate connection test failed"
}

# Create configuration files
create_config_files() {
    log_info "Creating configuration files..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
        cat > "${PROJECT_ROOT}/.env" << EOF
# Factory AI Configuration
FACTORY_AI_API_KEY=${FACTORY_AI_API_KEY}
FACTORY_AI_BASE_URL=${FACTORY_AI_BASE_URL:-https://api.factoryai.com/v1}

# Lambda Configuration
LAMBDA_API_KEY=${LAMBDA_API_KEY}

# Database Configuration
POSTGRES_CONNECTION_STRING=${POSTGRES_CONNECTION_STRING}
WEAVIATE_URL=${WEAVIATE_URL}
WEAVIATE_API_KEY=${WEAVIATE_API_KEY}
REDIS_URL=${REDIS_URL}

# Pulumi Configuration
PULUMI_CONFIG_PASSPHRASE=${PULUMI_CONFIG_PASSPHRASE}

# Monitoring Configuration
JAEGER_ENDPOINT=${JAEGER_ENDPOINT:-http://localhost:14268/api/traces}
PROMETHEUS_PORT=${PROMETHEUS_PORT:-9090}

# Application Configuration
FACTORY_BRIDGE_PORT=8080
FACTORY_BRIDGE_HOST=0.0.0.0
LOG_LEVEL=INFO
EOF
        log_success ".env file created"
    else
        log_info ".env file already exists"
    fi
}

# Main setup function
main() {
    log_info "Starting Factory AI Bridge setup..."
    echo ""
    
    # Check prerequisites
    check_root
    
    # Validate environment
    validate_environment
    echo ""
    
    # Validate Lambda API
    validate_Lambda_api
    echo ""
    
    # Setup Pulumi
    setup_pulumi
    echo ""
    
    # Setup Python environment
    setup_python_env
    echo ""
    
    # Create configuration files
    create_config_files
    echo ""
    
    # Test connections
    test_connections
    echo ""
    
    # Create systemd services
    create_systemd_services
    echo ""
    
    log_success "Factory AI Bridge setup completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "  1. Review the generated configuration files"
    echo "  2. Deploy infrastructure with: cd pulumi && pulumi up"
    echo "  3. Start the bridge API: uvicorn factory_integration.api.gateway:app --reload"
    echo "  4. Install and start systemd services (optional)"
    echo ""
    log_info "For development, you can run:"
    echo "  source venv/bin/activate"
    echo "  python -m factory_integration.api.gateway"
}

# Run main function
main "$@"