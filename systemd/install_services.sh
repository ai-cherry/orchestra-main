#!/bin/bash

# 🎼 Orchestra AI - Systemd Service Installer
# Install and configure systemd services for always-running Orchestra AI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORCHESTRA_HOME="$(dirname "$SCRIPT_DIR")"
SYSTEMD_DIR="/etc/systemd/system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Install systemd service
install_service() {
    local service_name=$1
    local service_file="$SCRIPT_DIR/$service_name.service"
    
    if [ ! -f "$service_file" ]; then
        error "Service file not found: $service_file"
        return 1
    fi
    
    log "Installing $service_name service..."
    
    # Copy service file
    cp "$service_file" "$SYSTEMD_DIR/"
    
    # Set proper permissions
    chmod 644 "$SYSTEMD_DIR/$service_name.service"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service (auto-start on boot)
    systemctl enable "$service_name"
    
    success "$service_name service installed and enabled"
}

# Uninstall systemd service
uninstall_service() {
    local service_name=$1
    
    log "Uninstalling $service_name service..."
    
    # Stop service if running
    if systemctl is-active --quiet "$service_name" 2>/dev/null; then
        systemctl stop "$service_name"
    fi
    
    # Disable service
    if systemctl is-enabled --quiet "$service_name" 2>/dev/null; then
        systemctl disable "$service_name"
    fi
    
    # Remove service file
    if [ -f "$SYSTEMD_DIR/$service_name.service" ]; then
        rm -f "$SYSTEMD_DIR/$service_name.service"
    fi
    
    # Reload systemd
    systemctl daemon-reload
    
    success "$service_name service uninstalled"
}

# Install all Orchestra AI services
install_all() {
    log "Installing all Orchestra AI systemd services..."
    
    # Core services
    install_service "orchestra-api"
    install_service "orchestra-frontend"
    
    # MCP services
    install_service "orchestra-mcp-memory"
    
    # Create log directories
    mkdir -p /var/log/orchestra/{api,frontend,mcp-memory,mcp-task,mcp-agent,mcp-data,mcp-monitor}
    chown -R ubuntu:ubuntu /var/log/orchestra
    
    # Create PID directories
    mkdir -p /var/run/orchestra
    chown -R ubuntu:ubuntu /var/run/orchestra
    
    success "All Orchestra AI services installed successfully"
    
    echo ""
    echo "🎼 Orchestra AI Services Installed"
    echo "=================================="
    echo ""
    echo "Available commands:"
    echo "  sudo systemctl start orchestra-api        # Start API service"
    echo "  sudo systemctl start orchestra-frontend   # Start Frontend service"
    echo "  sudo systemctl start orchestra-mcp-memory # Start MCP Memory service"
    echo ""
    echo "  sudo systemctl enable orchestra-api       # Enable auto-start on boot"
    echo "  sudo systemctl status orchestra-api       # Check service status"
    echo "  sudo journalctl -u orchestra-api -f       # View service logs"
    echo ""
    echo "To start all services:"
    echo "  sudo systemctl start orchestra-api orchestra-frontend orchestra-mcp-memory"
    echo ""
}

# Uninstall all Orchestra AI services
uninstall_all() {
    log "Uninstalling all Orchestra AI systemd services..."
    
    # Core services
    uninstall_service "orchestra-api"
    uninstall_service "orchestra-frontend"
    
    # MCP services
    uninstall_service "orchestra-mcp-memory"
    
    success "All Orchestra AI services uninstalled"
}

# Show service status
status() {
    echo ""
    echo "🎼 Orchestra AI Systemd Service Status"
    echo "======================================"
    
    declare -a services=("orchestra-api" "orchestra-frontend" "orchestra-mcp-memory")
    
    for service in "${services[@]}"; do
        echo ""
        echo "=== $service ==="
        
        if systemctl is-enabled --quiet "$service" 2>/dev/null; then
            echo -e "Enabled:  ${GREEN}YES${NC}"
        else
            echo -e "Enabled:  ${RED}NO${NC}"
        fi
        
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            echo -e "Status:   ${GREEN}RUNNING${NC}"
        else
            echo -e "Status:   ${RED}STOPPED${NC}"
        fi
        
        # Show last few log lines
        echo "Recent logs:"
        journalctl -u "$service" --no-pager -n 3 --output=cat 2>/dev/null | sed 's/^/  /' || echo "  No logs available"
    done
    
    echo ""
}

# Start all services
start_all() {
    log "Starting all Orchestra AI services..."
    
    systemctl start orchestra-api
    sleep 5
    systemctl start orchestra-frontend
    sleep 3
    systemctl start orchestra-mcp-memory
    
    success "All services started"
    status
}

# Stop all services
stop_all() {
    log "Stopping all Orchestra AI services..."
    
    systemctl stop orchestra-mcp-memory orchestra-frontend orchestra-api
    
    success "All services stopped"
}

# Main command handler
case "${1:-help}" in
    install)
        check_root
        install_all
        ;;
    uninstall)
        check_root
        uninstall_all
        ;;
    start)
        check_root
        start_all
        ;;
    stop)
        check_root
        stop_all
        ;;
    restart)
        check_root
        stop_all
        sleep 3
        start_all
        ;;
    status)
        status
        ;;
    logs)
        service_name=${2:-"orchestra-api"}
        echo "🎼 Orchestra AI - $service_name Logs"
        echo "===================================="
        journalctl -u "$service_name" -f
        ;;
    *)
        echo "🎼 Orchestra AI - Systemd Service Installer"
        echo "==========================================="
        echo ""
        echo "Usage: sudo $0 {install|uninstall|start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  install    Install all Orchestra AI systemd services"
        echo "  uninstall  Remove all Orchestra AI systemd services"
        echo "  start      Start all services"
        echo "  stop       Stop all services"
        echo "  restart    Restart all services"
        echo "  status     Show service status"
        echo "  logs [service]  Show logs for service (default: orchestra-api)"
        echo ""
        echo "Examples:"
        echo "  sudo $0 install           Install services"
        echo "  sudo $0 start             Start all services"
        echo "  sudo $0 status            Show service status"
        echo "  sudo $0 logs orchestra-api Show API logs"
        echo ""
        echo "Note: Most commands require root privileges (use sudo)"
        echo ""
        exit 1
        ;;
esac

