# Orchestra AI - Critical Issues Summary

## 🔴 BLOCKING ISSUES (Must fix immediately)

### 1. Docker Build Failures
```dockerfile
# Fix in Dockerfile.api and Dockerfile.mcp:
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*
```

### 2. API Module Import Errors
```python
# Problem: ModuleNotFoundError: No module named 'database.connection'
# Fix: Update WORKDIR and imports in Docker
WORKDIR /app/api
ENV PYTHONPATH=/app:$PYTHONPATH
```

### 3. Frontend Missing Files
```typescript
// Create: web/src/contexts/AppContext.tsx
// Fix: Vite @ alias resolution in vite.config.ts
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src')
  }
}
```

## 🟡 Runtime Issues

### 4. Missing Dependencies
- Add `greenlet` to requirements.txt
- Add `python-magic` to requirements.txt
- Fix SQLite UUID compatibility

### 5. Port Conflicts
- Kill existing processes on ports 8000, 3000-3003
- Use Docker Compose for proper orchestration

## Quick Fix Commands
```bash
# Stop all existing services
./stop_all_services.sh

# Kill specific ports
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
lsof -ti:3003 | xargs kill -9

# Rebuild with fixes
docker-compose down
docker-compose build --no-cache
docker-compose up
``` 