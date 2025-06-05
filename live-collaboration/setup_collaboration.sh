#!/bin/bash

# Live Collaboration System Setup Script
# Purpose: Set up complete Cursor ↔ Manus real-time collaboration

set -e

echo "🚀 Setting up Live Collaboration System"
echo "======================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print colored output
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    error "Please run this script from the live-collaboration directory"
    exit 1
fi

# 1. Install Python dependencies
log "📦 Installing Python dependencies..."
pip install -r requirements.txt
log "✅ Dependencies installed"

# 2. Set up database schema
log "🗃️ Setting up database schema..."
if command -v psql &> /dev/null; then
    # Use environment variables or defaults
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    DB_NAME=${DB_NAME:-orchestra_main}
    DB_USER=${DB_USER:-postgres}
    
    log "Creating collaboration schema in database..."
    PGPASSWORD=${DB_PASSWORD:-postgres} psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/schema.sql
    log "✅ Database schema created"
else
    warn "psql not found. Please install PostgreSQL client or run schema.sql manually"
fi

# 3. Create configuration file
log "⚙️ Creating configuration file..."
cat > collaboration_config.env << EOF
# Live Collaboration Configuration
# Database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=orchestra_main
DB_USER=postgres
DB_PASSWORD=postgres

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# Collaboration server settings
COLLABORATION_PORT=8765
COLLABORATION_HOST=0.0.0.0

# Logging level
LOG_LEVEL=INFO

# Session settings
SESSION_TIMEOUT_HOURS=24
MAX_FILE_SIZE_MB=50
DEBOUNCE_DELAY_SECONDS=0.5

# File tracking settings
TRACK_EXTENSIONS=.py,.js,.ts,.jsx,.tsx,.html,.css,.json,.md,.txt,.sql,.yaml,.yml
IGNORE_PATTERNS=.git,.vscode,__pycache__,node_modules,.env,.DS_Store,*.log,*.tmp
EOF
log "✅ Configuration file created: collaboration_config.env"

# 4. Create start scripts
log "📜 Creating start scripts..."

# Collaboration server start script
cat > start_collaboration_server.sh << 'EOF'
#!/bin/bash
source collaboration_config.env
export DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD
export REDIS_HOST REDIS_PORT REDIS_DB
python sync-server/collaboration_server.py
EOF

# Cursor watcher start script
cat > start_cursor_watcher.sh << 'EOF'
#!/bin/bash
if [ -z "$1" ]; then
    echo "Usage: ./start_cursor_watcher.sh <workspace_path> [session_id]"
    echo "Example: ./start_cursor_watcher.sh /path/to/your/project my-session-123"
    exit 1
fi

WORKSPACE_PATH="$1"
SESSION_ID="$2"

source collaboration_config.env
export DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD
export REDIS_HOST REDIS_PORT REDIS_DB

if [ -n "$SESSION_ID" ]; then
    python cursor-plugin/file_watcher.py "$WORKSPACE_PATH" --session-id "$SESSION_ID" --verbose
else
    python cursor-plugin/file_watcher.py "$WORKSPACE_PATH" --verbose
fi
EOF

# Manus client example script
cat > start_manus_client.sh << 'EOF'
#!/bin/bash
source collaboration_config.env
export DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD
export REDIS_HOST REDIS_PORT REDIS_DB
python manus-interface/manus_client.py
EOF

# Test script
cat > run_tests.sh << 'EOF'
#!/bin/bash
source collaboration_config.env
export DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD
export REDIS_HOST REDIS_PORT REDIS_DB
python tests/test_collaboration.py
EOF

# Make scripts executable
chmod +x start_collaboration_server.sh
chmod +x start_cursor_watcher.sh
chmod +x start_manus_client.sh
chmod +x run_tests.sh

log "✅ Start scripts created"

# 5. Create systemd service files (optional)
log "🔧 Creating systemd service files..."
mkdir -p systemd

cat > systemd/collaboration-server.service << EOF
[Unit]
Description=Live Collaboration Server
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
EnvironmentFile=$(pwd)/collaboration_config.env
ExecStart=$(which python) sync-server/collaboration_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

log "✅ Systemd service files created in systemd/"

# 6. Create VS Code launch configuration
log "🔧 Creating VS Code debug configuration..."
mkdir -p .vscode

cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Collaboration Server",
            "type": "python",
            "request": "launch",
            "program": "sync-server/collaboration_server.py",
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/collaboration_config.env"
        },
        {
            "name": "File Watcher",
            "type": "python",
            "request": "launch",
            "program": "cursor-plugin/file_watcher.py",
            "args": ["/path/to/workspace", "--verbose"],
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/collaboration_config.env"
        },
        {
            "name": "Manus Client",
            "type": "python",
            "request": "launch",
            "program": "manus-interface/manus_client.py",
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/collaboration_config.env"
        },
        {
            "name": "Run Tests",
            "type": "python",
            "request": "launch",
            "program": "tests/test_collaboration.py",
            "console": "integratedTerminal",
            "envFile": "${workspaceFolder}/collaboration_config.env"
        }
    ]
}
EOF

log "✅ VS Code launch configuration created"

# 7. Test database connection
log "🔍 Testing database connection..."
python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'orchestra_main'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# 8. Test Redis connection
log "🔍 Testing Redis connection..."
python3 -c "
import redis
import os
try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 1))
    )
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    exit(1)
"

echo ""
echo "🎉 Live Collaboration System Setup Complete!"
echo "============================================="
echo ""
echo "📋 What's been set up:"
echo "  ✅ Python dependencies installed"
echo "  ✅ Database schema created"
echo "  ✅ Configuration file: collaboration_config.env"
echo "  ✅ Start scripts created"
echo "  ✅ Systemd service files (in systemd/)"
echo "  ✅ VS Code debug configuration"
echo "  ✅ Database and Redis connections tested"
echo ""
echo "🚀 Next steps:"
echo ""
echo "1. Start the collaboration server:"
echo "   ./start_collaboration_server.sh"
echo ""
echo "2. In Cursor IDE, start file watching for your project:"
echo "   ./start_cursor_watcher.sh /path/to/your/project"
echo ""
echo "3. Connect Manus AI client:"
echo "   ./start_manus_client.sh"
echo ""
echo "4. Run tests to verify everything works:"
echo "   ./run_tests.sh"
echo ""
echo "📖 For more details, see docs/README.md"
echo ""
echo "🔧 Troubleshooting:"
echo "  - Check logs in collaboration server output"
echo "  - Verify database and Redis are running"
echo "  - Ensure firewall allows port 8765"
echo "  - Check collaboration_config.env for correct settings"
echo ""
echo "✨ Happy collaborating with Manus AI!" 