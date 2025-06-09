# CRITICAL CONFIGURATION REFERENCE

## PostgreSQL Database

**Connection Details:**
- Host: `localhost`
- Port: `5432`
- Database: `conductor`
- User: `conductor`
- Password: `orch3str4_2024`

**Quick Fix Commands:**
```bash
# Set up PostgreSQL user with correct password
sudo -u postgres psql << EOF
ALTER USER conductor WITH PASSWORD 'orch3str4_2024';
GRANT ALL PRIVILEGES ON DATABASE conductor TO conductor;
EOF

# Test connection
PGPASSWORD=orch3str4_2024 psql -h localhost -U conductor -d conductor -c "SELECT 1;"
```

## Weaviate Vector Database

**Connection Details:**
- URL: `http://localhost:8080`
- API Key: (none set)
- gRPC Port: `50051`

## API Configuration

**API Server:**
- URL: `http://localhost:8080`
 - API Key: `<api-key>`

## MCP Server Ports

- conductor: `8002`
- Memory: `8003`
- Weaviate Direct: `8001`
- Deployment: `8005`
- Tools: `8006`

## Quick Start Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Fix PostgreSQL permissions (if needed)
sudo -u postgres psql -c "ALTER USER conductor WITH PASSWORD 'orch3str4_2024';"

# Start MCP servers (after fixing DB)
./start_mcp_system.sh

# Check MCP status
ps aux | grep mcp_server
```

## Common Issues & Fixes

### PostgreSQL "no password supplied" error
```bash
# Fix the conductor user password
sudo -u postgres psql -c "ALTER USER conductor WITH PASSWORD 'orch3str4_2024';"
```

### MCP servers won't start
1. Check PostgreSQL is running: `sudo systemctl status postgresql`
2. Verify database exists: `sudo -u postgres psql -l | grep conductor`
3. Fix permissions: Run the PostgreSQL fix commands above

## Environment Variables (.env)

Critical ones:
```
POSTGRES_PASSWORD=orch3str4_2024
POSTGRES_USER=conductor
POSTGRES_DB=conductor
API_KEY=4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd
``` 