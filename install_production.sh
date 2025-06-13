#!/bin/bash

# 🎼 Orchestra AI Production Installer
# Complete setup for zero-maintenance operation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHAGENT_PLIST="com.orchestra.ai.supervisor.plist"
LAUNCHAGENT_DIR="$HOME/Library/LaunchAgents"
USER=$(whoami)

echo -e "${BLUE}🎼 Orchestra AI Production Installer${NC}"
echo "======================================"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   exit 1
fi

# Function to log success
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to log warning
log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to log error
log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to log info
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check macOS version
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This installer is designed for macOS only"
        exit 1
    fi
    
    # Check Homebrew
    if ! command -v brew &> /dev/null; then
        log_warning "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    log_success "Homebrew available"
    
    # Check Python 3.11
    if ! command -v python3 &> /dev/null; then
        log_warning "Python 3 not found. Installing via Homebrew..."
        brew install python@3.11
    fi
    log_success "Python 3 available"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_warning "Node.js not found. Installing via Homebrew..."
        brew install node
    fi
    log_success "Node.js available"
    
    # Check libmagic
    if [[ ! -f "/opt/homebrew/lib/libmagic.dylib" ]] && [[ ! -f "/usr/local/lib/libmagic.dylib" ]]; then
        log_warning "libmagic not found. Installing via Homebrew..."
        brew install libmagic
    fi
    log_success "libmagic available"
    
    # Check PostgreSQL (optional for production)
    if ! command -v psql &> /dev/null; then
        log_warning "PostgreSQL not found. Installing via Homebrew..."
        brew install postgresql@15
        brew services start postgresql@15
    fi
    log_success "PostgreSQL available"
    
    # Check Redis (optional for production)
    if ! command -v redis-server &> /dev/null; then
        log_warning "Redis not found. Installing via Homebrew..."
        brew install redis
        brew services start redis
    fi
    log_success "Redis available"
}

# Setup virtual environment and dependencies
setup_python_environment() {
    log_info "Setting up Python environment..."
    
    cd "$PROJECT_DIR"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        log_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install Python dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        log_success "Python dependencies installed"
    else
        log_warning "requirements.txt not found. Installing basic dependencies..."
        pip install fastapi uvicorn sqlalchemy aiosqlite python-magic psutil requests
    fi
    
    # Install additional production dependencies
    pip install supervisor gunicorn setproctitle
    
    log_success "Python environment configured"
}

# Setup Node.js environment
setup_node_environment() {
    log_info "Setting up Node.js environment..."
    
    cd "$PROJECT_DIR/web"
    
    # Install Node.js dependencies
    if [[ -f "package.json" ]]; then
        npm install
        log_success "Node.js dependencies installed"
    else
        log_warning "package.json not found in web directory"
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/data"
    mkdir -p "$PROJECT_DIR/uploads"
    mkdir -p "$PROJECT_DIR/backups"
    
    # Set proper permissions
    chmod 755 "$PROJECT_DIR/logs"
    chmod 755 "$PROJECT_DIR/data"
    chmod 755 "$PROJECT_DIR/uploads"
    chmod 755 "$PROJECT_DIR/backups"
    
    log_success "Directories created and permissions set"
}

# Install LaunchAgent for auto-startup
install_launchagent() {
    log_info "Installing LaunchAgent for automatic startup..."
    
    # Create LaunchAgents directory if it doesn't exist
    mkdir -p "$LAUNCHAGENT_DIR"
    
    # Update the plist file with current user path
    sed "s|/Users/lynnmusil|$HOME|g" "$PROJECT_DIR/$LAUNCHAGENT_PLIST" > "$LAUNCHAGENT_DIR/$LAUNCHAGENT_PLIST"
    
    # Load the LaunchAgent
    launchctl unload "$LAUNCHAGENT_DIR/$LAUNCHAGENT_PLIST" 2>/dev/null || true
    launchctl load "$LAUNCHAGENT_DIR/$LAUNCHAGENT_PLIST"
    
    log_success "LaunchAgent installed and loaded"
}

# Make scripts executable
make_scripts_executable() {
    log_info "Making scripts executable..."
    
    chmod +x "$PROJECT_DIR/orchestra_supervisor.py"
    chmod +x "$PROJECT_DIR/start_orchestra_complete.sh"
    
    # Make all shell scripts executable
    find "$PROJECT_DIR" -name "*.sh" -exec chmod +x {} \;
    
    log_success "Scripts made executable"
}

# Create systemd service (for Linux compatibility)
create_systemd_service() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_info "Creating systemd service..."
        
        cat > /tmp/orchestra-ai.service << EOF
[Unit]
Description=Orchestra AI Supervisor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$PROJECT_DIR:$PROJECT_DIR/api
Environment=VIRTUAL_ENV=$PROJECT_DIR/venv
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/orchestra_supervisor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        sudo mv /tmp/orchestra-ai.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable orchestra-ai.service
        
        log_success "Systemd service created and enabled"
    fi
}

# Setup database
setup_database() {
    log_info "Setting up database..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Create SQLite database directory
    mkdir -p data
    
    # Initialize database (this will be done by the application on first run)
    log_success "Database setup completed"
}

# Create configuration files
create_config_files() {
    log_info "Creating configuration files..."
    
    # Create environment configuration
    cat > "$PROJECT_DIR/.env" << EOF
# Orchestra AI Production Configuration
ENVIRONMENT=production
DATABASE_URL=sqlite+aiosqlite:///$PROJECT_DIR/data/orchestra_production.db
UPLOAD_DIR=$PROJECT_DIR/uploads
LOG_LEVEL=INFO
MAGIC_LIB=/opt/homebrew/lib/libmagic.dylib

# MCP Server Configuration
MCP_MEMORY_PORT=8003
MCP_INFRASTRUCTURE_PORT=8004

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend Configuration
FRONTEND_PORT=3002
EOF
    
    log_success "Configuration files created"
}

# Setup monitoring and alerting
setup_monitoring() {
    log_info "Setting up monitoring and alerting..."
    
    # Create simple monitoring script
    cat > "$PROJECT_DIR/monitor_orchestra.sh" << 'EOF'
#!/bin/bash

# Simple monitoring script for Orchestra AI
LOG_FILE="$HOME/orchestra-dev/logs/monitor.log"

check_service() {
    local service_name=$1
    local port=$2
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "$(date): ✅ $service_name is healthy" >> "$LOG_FILE"
        return 0
    else
        echo "$(date): ❌ $service_name is unhealthy" >> "$LOG_FILE"
        return 1
    fi
}

# Check all services
check_service "MCP Memory Server" 8003
check_service "API Server" 8000
check_service "Frontend" 3002

# Check supervisor process
if pgrep -f "orchestra_supervisor.py" > /dev/null; then
    echo "$(date): ✅ Supervisor is running" >> "$LOG_FILE"
else
    echo "$(date): ❌ Supervisor is not running" >> "$LOG_FILE"
    # Restart supervisor via LaunchAgent
    launchctl stop com.orchestra.ai.supervisor
    launchctl start com.orchestra.ai.supervisor
fi
EOF
    
    chmod +x "$PROJECT_DIR/monitor_orchestra.sh"
    
    # Add to crontab for periodic monitoring
    (crontab -l 2>/dev/null || true; echo "*/5 * * * * $PROJECT_DIR/monitor_orchestra.sh") | sort -u | crontab -
    
    log_success "Monitoring setup completed"
}

# Create backup script
create_backup_script() {
    log_info "Creating backup script..."
    
    cat > "$PROJECT_DIR/backup_orchestra.sh" << 'EOF'
#!/bin/bash

# Orchestra AI Backup Script
BACKUP_DIR="$HOME/orchestra-dev/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="orchestra_backup_$DATE.tar.gz"

# Create backup
cd "$HOME/orchestra-dev"
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='venv' \
    --exclude='node_modules' \
    --exclude='logs' \
    --exclude='.git' \
    .

# Keep only last 10 backups
cd "$BACKUP_DIR"
ls -t orchestra_backup_*.tar.gz | tail -n +11 | xargs rm -f

echo "$(date): Backup created: $BACKUP_FILE"
EOF
    
    chmod +x "$PROJECT_DIR/backup_orchestra.sh"
    
    # Add daily backup to crontab
    (crontab -l 2>/dev/null || true; echo "0 2 * * * $PROJECT_DIR/backup_orchestra.sh") | sort -u | crontab -
    
    log_success "Backup script created and scheduled"
}

# Setup Cursor integration
setup_cursor_integration() {
    log_info "Setting up Cursor AI integration..."
    
    # Ensure MCP configuration is in place
    if [[ -f "$PROJECT_DIR/claude_mcp_config.json" ]]; then
        # Update paths in MCP config to use current user
        sed -i.bak "s|/Users/lynnmusil|$HOME|g" "$PROJECT_DIR/claude_mcp_config.json"
        log_success "Cursor MCP configuration updated"
    else
        log_warning "MCP configuration file not found"
    fi
    
    # Create symlink for easier access
    mkdir -p "$HOME/.config/cursor"
    ln -sf "$PROJECT_DIR/claude_mcp_config.json" "$HOME/.config/cursor/mcp_config.json" 2>/dev/null || true
    
    log_success "Cursor integration configured"
}

# Test installation
test_installation() {
    log_info "Testing installation..."
    
    # Wait a moment for services to start
    sleep 10
    
    # Test MCP Memory Server
    if curl -s "http://localhost:8003/health" > /dev/null; then
        log_success "MCP Memory Server is responding"
    else
        log_warning "MCP Memory Server not responding (may still be starting)"
    fi
    
    # Test API Server
    if curl -s "http://localhost:8000/api/health" > /dev/null; then
        log_success "API Server is responding"
    else
        log_warning "API Server not responding (may still be starting)"
    fi
    
    # Test Frontend
    if curl -s "http://localhost:3002" > /dev/null; then
        log_success "Frontend is responding"
    else
        log_warning "Frontend not responding (may still be starting)"
    fi
    
    # Check LaunchAgent status
    if launchctl list | grep -q "com.orchestra.ai.supervisor"; then
        log_success "LaunchAgent is loaded"
    else
        log_warning "LaunchAgent not loaded"
    fi
}

# Print final instructions
print_final_instructions() {
    echo ""
    echo -e "${BLUE}🎉 Orchestra AI Production Installation Complete!${NC}"
    echo "================================================="
    echo ""
    echo -e "${GREEN}✅ Services will automatically start on boot${NC}"
    echo -e "${GREEN}✅ Health monitoring is active every 5 minutes${NC}"
    echo -e "${GREEN}✅ Daily backups are scheduled${NC}"
    echo -e "${GREEN}✅ Cursor MCP integration is configured${NC}"
    echo ""
    echo "🌐 Access Points:"
    echo "  • Admin Interface: http://localhost:3002/real-admin.html"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • MCP Memory Server: http://localhost:8003/health"
    echo ""
    echo "📁 Important Files:"
    echo "  • Logs: $PROJECT_DIR/logs/"
    echo "  • Backups: $PROJECT_DIR/backups/"
    echo "  • Configuration: $PROJECT_DIR/.env"
    echo ""
    echo "🔧 Management Commands:"
    echo "  • Status: launchctl list | grep orchestra"
    echo "  • Restart: launchctl restart com.orchestra.ai.supervisor"
    echo "  • Stop: launchctl stop com.orchestra.ai.supervisor"
    echo "  • View logs: tail -f $PROJECT_DIR/logs/supervisor-stdout.log"
    echo ""
    echo -e "${YELLOW}📖 See ORCHESTRA_AI_CURSOR_INTEGRATION.md for complete documentation${NC}"
    echo ""
}

# Main installation flow
main() {
    echo -e "${BLUE}Starting installation...${NC}"
    echo ""
    
    check_system_requirements
    echo ""
    
    setup_python_environment
    echo ""
    
    setup_node_environment
    echo ""
    
    create_directories
    echo ""
    
    make_scripts_executable
    echo ""
    
    create_config_files
    echo ""
    
    setup_database
    echo ""
    
    install_launchagent
    echo ""
    
    create_systemd_service
    echo ""
    
    setup_monitoring
    echo ""
    
    create_backup_script
    echo ""
    
    setup_cursor_integration
    echo ""
    
    test_installation
    echo ""
    
    print_final_instructions
}

# Run main installation
main "$@" 