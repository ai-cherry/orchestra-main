#!/bin/bash
# Setup MCP Environment on Lambda Labs Instance
# This script configures the Orchestra MCP servers and services

set -e

echo "🚀 Setting up Orchestra MCP Environment"
echo "======================================"

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    docker.io \
    docker-compose \
    postgresql-client \
    redis-tools \
    jq \
    git

# Add user to docker group
sudo usermod -aG docker $USER

# Set up Python environment
echo "🐍 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Set up environment variables
echo "🔧 Configuring environment..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Lambda Labs Configuration
INSTANCE_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || echo "localhost")
LAMBDA_API_KEY=${LAMBDA_API_KEY:-""}
GITHUB_TOKEN=${GITHUB_TOKEN:-""}

# Database Configuration
DATABASE_URL=postgresql://orchestra:orchestra@localhost:5432/orchestra_db
REDIS_URL=redis://localhost:6379

# MCP Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8765
MCP_ORCHESTRATOR_PORT=8766
MCP_MEMORY_PORT=8767

# Weaviate Configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-weaviate-key

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
EOF
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p .pulumi

# Set up PostgreSQL
echo "🐘 Setting up PostgreSQL..."
if ! command -v psql &> /dev/null; then
    sudo apt-get install -y postgresql postgresql-contrib
fi

# Start PostgreSQL if not running
if ! sudo systemctl is-active --quiet postgresql; then
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Create database and user
sudo -u postgres psql << EOF || true
CREATE USER orchestra WITH PASSWORD 'orchestra';
CREATE DATABASE orchestra_db OWNER orchestra;
GRANT ALL PRIVILEGES ON DATABASE orchestra_db TO orchestra;
EOF

# Set up Redis
echo "🔴 Setting up Redis..."
if ! command -v redis-server &> /dev/null; then
    sudo apt-get install -y redis-server
fi

# Start Redis if not running
if ! sudo systemctl is-active --quiet redis-server; then
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
fi

# Set up Docker services
echo "🐳 Setting up Docker services..."
if [ -f "docker-compose.yml" ]; then
    docker-compose up -d
else
    echo "⚠️  No docker-compose.yml found, skipping Docker setup"
fi

# Set up MCP servers as systemd services
echo "🔧 Setting up MCP systemd services..."

# Main MCP Server
sudo tee /etc/systemd/system/mcp-server.service > /dev/null << EOF
[Unit]
Description=MCP Server for Orchestra
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment="PATH=$PWD/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$PWD/venv/bin/python $PWD/mcp_server/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# MCP Orchestrator
sudo tee /etc/systemd/system/mcp-orchestrator.service > /dev/null << EOF
[Unit]
Description=MCP Orchestrator for Orchestra
After=network.target mcp-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment="PATH=$PWD/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="MCP_SERVER_PORT=8766"
ExecStart=$PWD/venv/bin/python $PWD/mcp_server/servers/coordinator_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# MCP Memory Server
sudo tee /etc/systemd/system/mcp-memory.service > /dev/null << EOF
[Unit]
Description=MCP Memory Server for Orchestra
After=network.target mcp-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment="PATH=$PWD/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="MCP_SERVER_PORT=8767"
ExecStart=$PWD/venv/bin/python $PWD/mcp_server/servers/memory_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start services
echo "🚀 Starting MCP services..."
sudo systemctl daemon-reload
sudo systemctl enable mcp-server mcp-orchestrator mcp-memory
sudo systemctl start mcp-server mcp-orchestrator mcp-memory

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 5

# Check service status
echo "📊 Checking service status..."
sudo systemctl status mcp-server --no-pager || true
sudo systemctl status mcp-orchestrator --no-pager || true
sudo systemctl status mcp-memory --no-pager || true

# Set up monitoring (optional)
if [ -f "prometheus.yml" ]; then
    echo "📊 Setting up monitoring..."
    docker run -d \
        --name prometheus \
        -p 9090:9090 \
        -v $PWD/prometheus.yml:/etc/prometheus/prometheus.yml \
        prom/prometheus || true
fi

# Final setup
echo "🔧 Final configuration..."

# Create helper scripts
cat > check_services.sh << 'EOF'
#!/bin/bash
echo "MCP Services Status:"
echo "==================="
sudo systemctl status mcp-server --no-pager | grep Active
sudo systemctl status mcp-orchestrator --no-pager | grep Active
sudo systemctl status mcp-memory --no-pager | grep Active
echo ""
echo "Port Status:"
echo "============"
sudo netstat -tlnp | grep -E "8765|8766|8767|5432|6379" || true
EOF
chmod +x check_services.sh

cat > restart_services.sh << 'EOF'
#!/bin/bash
echo "Restarting MCP services..."
sudo systemctl restart mcp-server mcp-orchestrator mcp-memory
echo "Services restarted. Checking status..."
sleep 3
./check_services.sh
EOF
chmod +x restart_services.sh

# Display summary
echo ""
echo "✅ Setup Complete!"
echo "=================="
echo "Instance IP: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 || echo 'unknown')"
echo ""
echo "Services:"
echo "- PostgreSQL: localhost:5432"
echo "- Redis: localhost:6379"
echo "- MCP Server: localhost:8765"
echo "- MCP Orchestrator: localhost:8766"
echo "- MCP Memory: localhost:8767"
echo ""
echo "Commands:"
echo "- Check services: ./check_services.sh"
echo "- Restart services: ./restart_services.sh"
echo "- View logs: sudo journalctl -u mcp-server -f"
echo ""
echo "Next steps:"
echo "1. Test MCP connection: curl http://localhost:8765/health"
echo "2. Configure your local VS Code to connect via Remote-SSH"
echo "3. Start developing!"