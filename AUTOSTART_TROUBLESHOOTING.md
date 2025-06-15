# Orchestra AI Autostart Troubleshooting Guide

## Common Issues and Solutions

### 1. macOS Permission Error with psutil

**Error**: `psutil.AccessDenied: (pid=94705)`

**Solution**: Fixed in latest version - the script now falls back to socket binding test when psutil fails.

### 2. Missing Dependencies

**Error**: `No module named 'greenlet'` or `No module named 'magic'`

**Solution**:
```bash
# Run the dependency fix script
chmod +x scripts/fix_dependencies.sh
./scripts/fix_dependencies.sh
```

### 3. Database Connection Issues

**Error**: `[Errno 61] Connection refused` (PostgreSQL)

**Solution**:
```bash
# For macOS:
brew services start postgresql@16
brew services start redis

# For Linux:
sudo systemctl start postgresql
sudo systemctl start redis
```

### 4. Port Already in Use

**Error**: `[Errno 48] Address already in use`

**Solution**: Use the simple startup script which handles port conflicts:
```bash
chmod +x start_orchestra_simple.sh
./start_orchestra_simple.sh
```

### 5. Docker Build Failures

**Error**: `gcc: command not found` when building psutil

**Solution**: Update Dockerfiles to include gcc (already fixed in api/Dockerfile and mcp_servers/Dockerfile)

## Quick Start Commands

### Option 1: Simple Startup (Recommended for Development)
```bash
# First time setup
chmod +x scripts/fix_dependencies.sh
./scripts/fix_dependencies.sh

# Start services
chmod +x start_orchestra_simple.sh
./start_orchestra_simple.sh

# Stop services
./stop_orchestra_simple.sh
```

### Option 2: Full Autostart (Requires all dependencies)
```bash
# Fix permissions
chmod +x scripts/orchestra_autostart.py
chmod +x scripts/install_autostart.sh

# Install as system service (optional)
./scripts/install_autostart.sh

# Or run directly
./orchestra-autostart
```

### Option 3: Docker Compose
```bash
# Ensure Docker is running
docker-compose up --build
```

## Service Status Check

Check if services are running:
```bash
# Check ports
lsof -i :8000  # API
lsof -i :3000  # Frontend  
lsof -i :8003  # MCP Server

# Check processes
ps aux | grep python | grep orchestra
ps aux | grep "npm run dev"
```

## Development Tips

1. **Start Simple**: Use `start_orchestra_simple.sh` for quick development
2. **Check Logs**: Look in `logs/` directory for detailed error messages
3. **Environment Variables**: Ensure `.env` file exists with proper configuration
4. **Database**: For full functionality, ensure PostgreSQL and Redis are running

## Still Having Issues?

1. Check the detailed logs:
   ```bash
   tail -f logs/autostart.log
   ```

2. Run services individually to debug:
   ```bash
   # API
   cd api && python main_simple.py
   
   # Frontend
   cd web && npm run dev
   
   # MCP Server
   cd mcp_servers && uvicorn memory_management_server:app --host 0.0.0.0 --port 8003
   ```

3. Verify Python environment:
   ```bash
   which python
   python --version  # Should be 3.11+
   pip list | grep -E "greenlet|magic|psutil"
   ``` 