#!/bin/bash
# Ensure required services are running for Cherry AI

echo "🔍 Checking required services..."

# PostgreSQL
if systemctl is-active --quiet postgresql; then
    echo "✅ PostgreSQL is running"
else
    echo "🚀 Starting PostgreSQL..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Test PostgreSQL connection
if PGPASSWORD=orch3str4_2024 psql -h localhost -U conductor -d conductor -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ PostgreSQL connection working"
else
    echo "🔧 Fixing PostgreSQL permissions..."
    sudo -u postgres psql << EOF >/dev/null 2>&1
ALTER USER conductor WITH PASSWORD 'orch3str4_2024';
GRANT ALL PRIVILEGES ON DATABASE conductor TO conductor;
EOF
    echo "✅ PostgreSQL permissions fixed"
fi

# Check if Weaviate is running (Docker)
if docker ps 2>/dev/null | grep -q weaviate; then
    echo "✅ Weaviate is running (Docker)"
elif curl -s http://localhost:8080/v1/meta >/dev/null 2>&1; then
    echo "✅ Weaviate is running (standalone)"
else
    echo "⚠️  Weaviate is not running"
    echo "   To start Weaviate:"
    echo "   docker-compose -f weaviate-docker-compose.yml up -d"
fi

# Clean up failed MCP systemd services
echo ""
echo "🧹 Cleaning up MCP systemd services (not needed)..."
for service in mcp-memory mcp-conductor mcp-tools mcp-weaviate; do
    if systemctl is-enabled --quiet $service 2>/dev/null; then
        sudo systemctl stop $service 2>/dev/null
        sudo systemctl disable $service 2>/dev/null
        sudo rm -f /etc/systemd/system/$service.service
    fi
done
sudo systemctl daemon-reload

echo ""
echo "✅ Service check complete!"
echo ""
echo "📝 Remember: MCP servers are started automatically by Cursor"
echo "   See CURSOR_MCP_SETUP.md for configuration details" 