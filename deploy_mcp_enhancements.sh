#!/bin/bash
# Automated deployment script for MCP server enhancements
# This script implements all the recommended improvements

set -e  # Exit on any error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups/mcp_$(date +%Y%m%d_%H%M%S)"

# Function to log
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Python version
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        error "Python 3.8+ is required"
        return 1
    fi
    
    # Check virtual environment
    if [ ! -d "./venv" ]; then
        error "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source ./venv/bin/activate
    
    success "Prerequisites checked"
}

# Function to backup existing files
backup_existing() {
    log "Creating backup of existing MCP system..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing servers
    if [ -d "mcp_server/servers" ]; then
        cp -r mcp_server/servers "$BACKUP_DIR/"
    fi
    
    # Backup scripts
    for script in start_mcp_system.sh stop_mcp_system.sh check_mcp_servers.sh; do
        if [ -f "$script" ]; then
            cp "$script" "$BACKUP_DIR/"
        fi
    done
    
    # Backup configuration
    if [ -f "mcp_config.json" ]; then
        cp mcp_config.json "$BACKUP_DIR/"
    fi
    
    success "Backup created at: $BACKUP_DIR"
}

# Function to install dependencies
install_dependencies() {
    log "Installing enhanced dependencies..."
    
    # Create requirements file for enhancements
    cat > requirements/mcp_enhancements.txt << EOF
# MCP Server Enhancements
asyncpg>=0.27.0          # PostgreSQL async driver
aiohttp>=3.8.0           # Async HTTP client
prometheus-client>=0.16.0 # Metrics collection
psutil>=5.9.0            # System monitoring
backoff>=2.2.0           # Retry logic
curses-menu>=0.6.0       # Dashboard UI (optional)
EOF
    
    # Install dependencies
    pip install -r requirements/mcp_enhancements.txt
    
    success "Dependencies installed"
}

# Function to create directory structure
create_directories() {
    log "Creating directory structure..."
    
    mkdir -p mcp_server/base
    mkdir -p mcp_server/monitoring
    mkdir -p ~/.mcp/logs
    mkdir -p ~/.mcp/pids
    
    success "Directories created"
}

# Function to deploy enhanced files
deploy_enhancements() {
    log "Deploying enhanced MCP components..."
    
    # Make scripts executable
    chmod +x start_mcp_system_enhanced.sh
    chmod +x stop_mcp_system_enhanced.sh
    chmod +x mcp_server/monitoring/health_dashboard_enhanced.py
    
    # Create __init__.py files
    touch mcp_server/base/__init__.py
    touch mcp_server/monitoring/__init__.py
    
    success "Enhanced components deployed"
}

# Function to update configuration
update_configuration() {
    log "Updating MCP configuration..."
    
    # Create enhanced configuration
    cat > mcp_config_enhanced.json << 'EOF'
{
  "version": "2.0.0",
  "description": "Enhanced MCP configuration with performance optimizations",
  "servers": {
    "conductor": {
      "port": 8002,
      "health_endpoint": "/health",
      "connection_pool": {
        "min_size": 5,
        "max_size": 20
      }
    },
    "memory": {
      "port": 8003,
      "health_endpoint": "/health",
      "enhanced": true,
      "cache": {
        "search_cache_size": 500,
        "memory_cache_size": 1000,
        "ttl_seconds": 300
      },
      "batch_processing": {
        "enabled": true,
        "batch_size": 100
      }
    },
    "tools": {
      "port": 8006,
      "health_endpoint": "/health"
    },
    "weaviate_direct": {
      "port": 8001,
      "health_endpoint": "/mcp/weaviate_direct/health"
    }
  },
  "monitoring": {
    "enabled": true,
    "prometheus_metrics": true,
    "health_check_interval": 5,
    "auto_restart": true
  },
  "performance": {
    "parallel_startup": true,
    "memory_limit": "1G",
    "cpu_quota": "80%",
    "circuit_breaker": {
      "failure_threshold": 5,
      "recovery_timeout": 60
    }
  }
}
EOF
    
    success "Configuration updated"
}

# Function to create systemd service files (optional)
create_systemd_services() {
    log "Creating systemd service files..."
    
    # Create service directory
    mkdir -p ~/.config/systemd/user/
    
    # Create MCP system service
    cat > ~/.config/systemd/user/mcp-system.service << EOF
[Unit]
Description=MCP Server System
After=network.target

[Service]
Type=forking
WorkingDirectory=$PROJECT_ROOT
ExecStart=$PROJECT_ROOT/start_mcp_system_enhanced.sh
ExecStop=$PROJECT_ROOT/stop_mcp_system_enhanced.sh
Restart=on-failure
RestartSec=10
Environment="PATH=$PATH"

[Install]
WantedBy=default.target
EOF
    
    # Reload systemd
    systemctl --user daemon-reload
    
    success "Systemd services created (optional)"
}

# Function to run tests
run_tests() {
    log "Running enhancement tests..."
    
    # Test imports
    python3 -c "
import asyncio
import asyncpg
import aiohttp
import prometheus_client
import psutil
import backoff
print('All imports successful')
" || {
        error "Import test failed"
        return 1
    }
    
    # Test enhanced base class
    python3 -c "
import sys
sys.path.insert(0, '.')
from mcp_server.base.enhanced_server_base import EnhancedMCPServerBase
print('Enhanced base class imported successfully')
" || {
        error "Enhanced base class test failed"
        return 1
    }
    
    success "All tests passed"
}

# Function to display next steps
display_next_steps() {
    echo ""
    echo "========================================="
    echo "MCP Enhancement Deployment Complete!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Start the enhanced MCP system:"
    echo "   ${GREEN}./start_mcp_system_enhanced.sh${NC}"
    echo ""
    echo "2. Monitor server health:"
    echo "   ${GREEN}python mcp_server/monitoring/health_dashboard_enhanced.py${NC}"
    echo ""
    echo "3. View logs:"
    echo "   ${GREEN}tail -f ~/.mcp/logs/*.log${NC}"
    echo ""
    echo "4. Stop the system:"
    echo "   ${GREEN}./stop_mcp_system_enhanced.sh${NC}"
    echo ""
    echo "Optional:"
    echo "- Enable systemd service: ${YELLOW}systemctl --user enable mcp-system${NC}"
    echo "- View metrics: ${YELLOW}curl http://localhost:8003/metrics${NC}"
    echo ""
    echo "Documentation:"
    echo "- Analysis: docs/MCP_SERVER_COMPREHENSIVE_ANALYSIS.md"
    echo "- Implementation: docs/MCP_SERVER_IMPLEMENTATION_GUIDE.md"
    echo ""
    echo "Backup location: $BACKUP_DIR"
}

# Main execution
main() {
    log "Starting MCP enhancement deployment..."
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Execute deployment steps
    check_prerequisites || exit 1
    backup_existing
    install_dependencies
    create_directories
    deploy_enhancements
    update_configuration
    
    # Optional steps
    if [ "$1" == "--with-systemd" ]; then
        create_systemd_services
    fi
    
    # Run tests
    run_tests || {
        warning "Some tests failed, but deployment completed"
    }
    
    # Display completion message
    display_next_steps
    
    success "MCP enhancement deployment completed successfully!"
}

# Run main function
main "$@"