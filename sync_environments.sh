#!/bin/bash

# 🎼 Orchestra AI Environment Synchronization Script
# Ensures alignment between development, staging, and production environments

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENTS=("development" "staging" "production")
CONFIG_FILES=(".env" "docker-compose.yml" "claude_mcp_config.json")
VALIDATION_SCRIPT="validate_environment.py"

# Log functions
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] INFO: $1${NC}"
}

# Environment validation
validate_environment() {
    local env_name=$1
    log "🔍 Validating $env_name environment..."
    
    # Check if environment directory exists
    if [ ! -d "environments/$env_name" ]; then
        warn "Environment directory not found: environments/$env_name"
        mkdir -p "environments/$env_name"
    fi
    
    # Validate configuration files
    for config_file in "${CONFIG_FILES[@]}"; do
        local env_config="environments/$env_name/$config_file"
        if [ -f "$env_config" ]; then
            log "✅ Found $config_file for $env_name"
        else
            warn "❌ Missing $config_file for $env_name"
        fi
    done
    
    # Run environment-specific validation
    if [ -f "$VALIDATION_SCRIPT" ]; then
        log "Running validation script for $env_name..."
        if python3 "$VALIDATION_SCRIPT"; then
            log "✅ Validation passed for $env_name"
        else
            error "❌ Validation failed for $env_name"
            return 1
        fi
    fi
}

# Synchronize dependencies
sync_dependencies() {
    local env_name=$1
    log "📦 Synchronizing dependencies for $env_name..."
    
    # Python dependencies
    if [ -f "api/requirements.txt" ]; then
        local env_requirements="environments/$env_name/requirements.txt"
        if [ -f "$env_requirements" ]; then
            # Compare and update if needed
            if ! diff -q "api/requirements.txt" "$env_requirements" > /dev/null; then
                warn "Requirements differ for $env_name, updating..."
                cp "api/requirements.txt" "$env_requirements"
            else
                log "✅ Python requirements in sync for $env_name"
            fi
        else
            cp "api/requirements.txt" "$env_requirements"
            log "✅ Created requirements.txt for $env_name"
        fi
    fi
    
    # Node.js dependencies
    if [ -f "web/package.json" ]; then
        local env_package="environments/$env_name/package.json"
        if [ -f "$env_package" ]; then
            # Compare versions
            local current_version=$(jq -r '.version' "web/package.json")
            local env_version=$(jq -r '.version' "$env_package")
            if [ "$current_version" != "$env_version" ]; then
                warn "Package versions differ for $env_name"
                info "Current: $current_version, Environment: $env_version"
            fi
        else
            cp "web/package.json" "$env_package"
            log "✅ Created package.json for $env_name"
        fi
    fi
}

# Synchronize configuration
sync_configuration() {
    local env_name=$1
    log "⚙️  Synchronizing configuration for $env_name..."
    
    # Environment-specific configurations
    case $env_name in
        "development")
            sync_development_config
            ;;
        "staging")
            sync_staging_config
            ;;
        "production")
            sync_production_config
            ;;
    esac
}

# Development environment configuration
sync_development_config() {
    log "🔧 Configuring development environment..."
    
    # Create development .env
    cat > "environments/development/.env" << EOF
# Orchestra AI Development Environment
NODE_ENV=development
DEBUG=true
LOG_LEVEL=debug

# Database Configuration
DATABASE_URL=sqlite:///./orchestra.db
USE_SQLITE=true
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=orchestra_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080

# API Configuration
API_HOST=localhost
API_PORT=8000
FRONTEND_URL=http://localhost:3000

# MCP Server Configuration
MCP_ENABLED=false
MCP_MEMORY_PORT=8003
MCP_CODE_INTELLIGENCE_PORT=8007
MCP_GIT_INTELLIGENCE_PORT=8008
MCP_TOOLS_REGISTRY_PORT=8006
MCP_INFRASTRUCTURE_PORT=8009

# Lambda Labs Configuration (Development)
LAMBDA_LABS_ENABLED=false
LAMBDA_LABS_API_KEY=dev_key_placeholder

# Security (Development)
JWT_SECRET=dev_jwt_secret_change_in_production
CORS_ORIGINS=http://localhost:3000

# File Processing
MAX_FILE_SIZE=100MB
UPLOAD_DIR=./uploads

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
EOF
    
    log "✅ Development configuration created"
}

# Staging environment configuration
sync_staging_config() {
    log "🎭 Configuring staging environment..."
    
    # Create staging .env template
    cat > "environments/staging/.env.template" << EOF
# Orchestra AI Staging Environment
NODE_ENV=staging
DEBUG=false
LOG_LEVEL=info

# Database Configuration
DATABASE_URL=postgresql+asyncpg://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/\${POSTGRES_DB}
USE_SQLITE=false
POSTGRES_HOST=staging-postgres.example.com
POSTGRES_PORT=5432
POSTGRES_DB=orchestra_staging
POSTGRES_USER=\${STAGING_POSTGRES_USER}
POSTGRES_PASSWORD=\${STAGING_POSTGRES_PASSWORD}

# Redis Configuration
REDIS_HOST=staging-redis.example.com
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=\${STAGING_REDIS_PASSWORD}

# Weaviate Configuration
WEAVIATE_URL=http://staging-weaviate.example.com:8080

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=https://staging.orchestra-ai.com

# MCP Server Configuration
MCP_ENABLED=true
MCP_MEMORY_PORT=8003
MCP_CODE_INTELLIGENCE_PORT=8007
MCP_GIT_INTELLIGENCE_PORT=8008
MCP_TOOLS_REGISTRY_PORT=8006
MCP_INFRASTRUCTURE_PORT=8009

# Lambda Labs Configuration
LAMBDA_LABS_ENABLED=true
LAMBDA_LABS_API_KEY=\${STAGING_LAMBDA_LABS_API_KEY}

# Security
JWT_SECRET=\${STAGING_JWT_SECRET}
CORS_ORIGINS=https://staging.orchestra-ai.com

# File Processing
MAX_FILE_SIZE=500MB
UPLOAD_DIR=/app/uploads

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
EOF
    
    log "✅ Staging configuration template created"
}

# Production environment configuration
sync_production_config() {
    log "🚀 Configuring production environment..."
    
    # Create production .env template
    cat > "environments/production/.env.template" << EOF
# Orchestra AI Production Environment
NODE_ENV=production
DEBUG=false
LOG_LEVEL=warn

# Database Configuration
DATABASE_URL=postgresql+asyncpg://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@\${POSTGRES_HOST}:\${POSTGRES_PORT}/\${POSTGRES_DB}
USE_SQLITE=false
POSTGRES_HOST=45.77.87.106
POSTGRES_PORT=5432
POSTGRES_DB=orchestra_production
POSTGRES_USER=\${PRODUCTION_POSTGRES_USER}
POSTGRES_PASSWORD=\${PRODUCTION_POSTGRES_PASSWORD}

# Redis Configuration
REDIS_HOST=45.77.87.106
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=\${PRODUCTION_REDIS_PASSWORD}

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=https://orchestra-ai.com

# MCP Server Configuration
MCP_ENABLED=true
MCP_MEMORY_PORT=8003
MCP_CODE_INTELLIGENCE_PORT=8007
MCP_GIT_INTELLIGENCE_PORT=8008
MCP_TOOLS_REGISTRY_PORT=8006
MCP_INFRASTRUCTURE_PORT=8009

# Lambda Labs Configuration
LAMBDA_LABS_ENABLED=true
LAMBDA_LABS_API_KEY=\${PRODUCTION_LAMBDA_LABS_API_KEY}
LAMBDA_LABS_REGION=us-west-2
LAMBDA_LABS_INSTANCE_TYPE=gpu_1x_a100

# Security
JWT_SECRET=\${PRODUCTION_JWT_SECRET}
CORS_ORIGINS=https://orchestra-ai.com
API_KEY_ROTATION_DAYS=30
SESSION_TIMEOUT_MINUTES=720

# File Processing
MAX_FILE_SIZE=1GB
UPLOAD_DIR=/app/uploads

# Monitoring
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
ALERTMANAGER_ENABLED=true

# Scaling
AUTO_SCALING_ENABLED=true
MIN_INSTANCES=2
MAX_INSTANCES=20
TARGET_CPU_UTILIZATION=70
TARGET_MEMORY_UTILIZATION=80
EOF
    
    log "✅ Production configuration template created"
}

# Create Docker Compose for each environment
create_docker_compose() {
    local env_name=$1
    log "🐳 Creating Docker Compose for $env_name..."
    
    local compose_file="environments/$env_name/docker-compose.yml"
    
    cat > "$compose_file" << EOF
version: '3.8'

services:
  api:
    build:
      context: ../../api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=$env_name
    env_file:
      - .env
    volumes:
      - ../../api:/app
      - uploads:/app/uploads
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ../../web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=$env_name
    volumes:
      - ../../web:/app
    depends_on:
      - api

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: orchestra_$env_name
      POSTGRES_USER: \${POSTGRES_USER}
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
    volumes:
      - weaviate_data:/var/lib/weaviate

volumes:
  postgres_data:
  redis_data:
  weaviate_data:
  uploads:
EOF

    # Add MCP servers for staging and production
    if [ "$env_name" != "development" ]; then
        cat >> "$compose_file" << EOF

  mcp-memory:
    build:
      context: ../../mcp-servers/memory
      dockerfile: Dockerfile
    ports:
      - "8003:8003"
    environment:
      - POSTGRES_HOST=postgres
      - WEAVIATE_URL=http://weaviate:8080
    depends_on:
      - postgres
      - weaviate

  mcp-code-intelligence:
    build:
      context: ../../mcp-servers/code-intelligence
      dockerfile: Dockerfile
    ports:
      - "8007:8007"
    depends_on:
      - mcp-memory

  mcp-tools-registry:
    build:
      context: ../../mcp-servers/tools-registry
      dockerfile: Dockerfile
    ports:
      - "8006:8006"
    environment:
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis

  mcp-git-intelligence:
    build:
      context: ../../mcp-servers/git-intelligence
      dockerfile: Dockerfile
    ports:
      - "8008:8008"
    depends_on:
      - mcp-memory

  mcp-infrastructure:
    build:
      context: ../../mcp-servers/infrastructure
      dockerfile: Dockerfile
    ports:
      - "8009:8009"
    environment:
      - LAMBDA_LABS_API_KEY=\${LAMBDA_LABS_API_KEY}
    depends_on:
      - mcp-memory
EOF
    fi
    
    log "✅ Docker Compose created for $env_name"
}

# Generate documentation
generate_documentation() {
    log "📚 Generating environment documentation..."
    
    cat > "environments/README.md" << EOF
# 🎼 Orchestra AI Environment Management

This directory contains environment-specific configurations for Orchestra AI.

## Environment Structure

\`\`\`
environments/
├── development/          # Local development environment
├── staging/             # Staging environment for testing
├── production/          # Production environment
└── README.md           # This file
\`\`\`

## Environment Setup

### Development
\`\`\`bash
cd environments/development
cp .env.example .env
docker-compose up -d
\`\`\`

### Staging
\`\`\`bash
cd environments/staging
cp .env.template .env
# Configure environment variables
docker-compose up -d
\`\`\`

### Production
\`\`\`bash
cd environments/production
cp .env.template .env
# Configure environment variables
docker-compose up -d
\`\`\`

## Environment Synchronization

Run the synchronization script to ensure all environments are aligned:

\`\`\`bash
./sync_environments.sh
\`\`\`

## Configuration Management

### Environment Variables
- Development: Uses local services and mock configurations
- Staging: Uses shared services with staging credentials
- Production: Uses production services with proper security

### Service Dependencies
- **Database**: SQLite (dev) → PostgreSQL (staging/prod)
- **Cache**: In-memory (dev) → Redis (staging/prod)
- **Vector DB**: Mock (dev) → Weaviate (staging/prod)
- **MCP Servers**: Disabled (dev) → Enabled (staging/prod)

### Security Considerations
- Development: Simplified authentication for ease of development
- Staging: Production-like security with test credentials
- Production: Full security implementation with proper secrets management

## Monitoring

Each environment includes:
- Health check endpoints
- Metrics collection (Prometheus)
- Log aggregation
- Performance monitoring

## Deployment

Use the deployment scripts for each environment:
- \`deploy_to_staging.sh\`
- \`deploy_to_production.sh\`

## Troubleshooting

1. **Environment Validation**: Run \`validate_environment.py\`
2. **Service Health**: Check \`http://localhost:8000/api/health\`
3. **Log Analysis**: Use \`docker-compose logs [service]\`
4. **Performance**: Monitor metrics in Grafana dashboards
EOF
    
    log "✅ Documentation generated"
}

# Main synchronization process
main() {
    log "🎼 Orchestra AI Environment Synchronization"
    log "=========================================="
    
    # Parse arguments
    local sync_all=true
    local target_env=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env)
                target_env="$2"
                sync_all=false
                shift 2
                ;;
            --validate-only)
                # Just run validation without sync
                if [ -n "$target_env" ]; then
                    validate_environment "$target_env"
                else
                    for env in "${ENVIRONMENTS[@]}"; do
                        validate_environment "$env"
                    done
                fi
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--env ENVIRONMENT] [--validate-only]"
                exit 1
                ;;
        esac
    done
    
    # Create environments directory
    mkdir -p environments
    
    # Synchronize environments
    if [ "$sync_all" = true ]; then
        for env in "${ENVIRONMENTS[@]}"; do
            log "🔄 Synchronizing $env environment..."
            mkdir -p "environments/$env"
            validate_environment "$env"
            sync_dependencies "$env"
            sync_configuration "$env"
            create_docker_compose "$env"
        done
    else
        log "🔄 Synchronizing $target_env environment..."
        mkdir -p "environments/$target_env"
        validate_environment "$target_env"
        sync_dependencies "$target_env"
        sync_configuration "$target_env"
        create_docker_compose "$target_env"
    fi
    
    # Generate documentation
    generate_documentation
    
    log "✅ Environment synchronization completed!"
    log ""
    log "📋 Next Steps:"
    log "   1. Review generated configurations in environments/"
    log "   2. Set up environment-specific secrets"
    log "   3. Run validation: ./validate_environment.py"
    log "   4. Deploy: ./deploy_to_production.sh --verify"
}

# Execute main function
main "$@" 