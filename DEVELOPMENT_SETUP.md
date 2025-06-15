# 🎼 Orchestra AI Development Setup Guide

## Quick Start (Emergency Fix)

If you're experiencing import errors or environment issues, run this **ONE COMMAND** to fix everything:

```bash
./setup_dev_environment.sh
```

This will:
- ✅ Fix all Python import issues
- ✅ Setup virtual environment properly  
- ✅ Install all dependencies
- ✅ Create convenient startup scripts
- ✅ Test the installation

## 🚀 Starting the Application

### Option 1: Full Stack (Recommended)
```bash
./start_orchestra.sh
```
This starts both API (port 8000) and frontend (port 3000) together.

### Option 2: Individual Services
```bash
# API only
./start_api.sh

# Frontend only  
./start_frontend.sh
```

### Option 3: Manual (for debugging)
```bash
# Terminal 1 - API
source venv/bin/activate
cd api
python3 -m uvicorn main:app --reload

# Terminal 2 - Frontend
cd web
npm run dev
```

## 📚 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React admin interface |
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Health Check | http://localhost:8000/api/health | API health status |

## 🔧 Troubleshooting

### Common Issues & Solutions

#### Issue: "attempted relative import beyond top-level package"
**Solution:** Run the setup script - it fixes Python path issues
```bash
./setup_dev_environment.sh
```

#### Issue: "command not found: python"
**Solution:** Use `python3` instead of `python`, or install Python 3.11+

#### Issue: Virtual environment not activating
**Solution:** 
```bash
rm -rf venv  # Remove broken venv
./setup_dev_environment.sh  # Recreate everything
```

#### Issue: Import errors in development
**Solution:** Make sure you're in the project root and Python path is set:
```bash
export PYTHONPATH="$(pwd):$(pwd)/api:${PYTHONPATH}"
```

#### Issue: Database connection errors
**Solution:** 
1. Install PostgreSQL locally, or
2. Update DATABASE_URL in start scripts to use SQLite for development

#### Issue: Port already in use
**Solution:**
```bash
# Kill processes on ports
lsof -ti:8000 | xargs kill -9  # Kill API
lsof -ti:3000 | xargs kill -9  # Kill frontend
```

## 🛠️ Development Workflow

### 1. Environment Setup (First Time)
```bash
git clone <repository>
cd orchestra-dev
./setup_dev_environment.sh
```

### 2. Daily Development
```bash
./start_orchestra.sh  # Start everything
# ... develop ...
# Ctrl+C to stop
```

### 3. Adding Dependencies
```bash
source venv/bin/activate
pip install <new-package>
pip freeze > api/requirements.txt
```

### 4. Database Changes
```bash
cd api
python3 -c "from database.models import *; print('Models loaded')"
# Add migration commands here when Alembic is setup
```

## 📁 Project Structure

```
orchestra-dev/
├── api/                    # FastAPI backend
│   ├── database/          # Database models & connection
│   ├── services/          # Business logic services  
│   ├── main.py           # FastAPI application
│   └── requirements.txt  # Python dependencies
├── web/                   # React frontend
│   ├── src/              # React source code
│   ├── public/           # Static assets
│   └── package.json      # Node dependencies
├── venv/                  # Python virtual environment
├── setup_dev_environment.sh  # Environment setup script
├── start_orchestra.sh    # Start full stack
├── start_api.sh          # Start API only
└── start_frontend.sh     # Start frontend only
```

## 🔬 Testing the Setup

### Quick Health Check
```bash
# Test API
curl http://localhost:8000/api/health

# Test frontend
open http://localhost:3000
```

### Import Test
```bash
source venv/bin/activate
cd api
python3 -c "
from database.connection import init_database
from services.file_service import enhanced_file_service
print('✅ All imports working')
"
```

## 🎯 Development Environment Status

### ✅ What's Working
- React frontend with hot reload
- FastAPI backend with auto-reload  
- Database models and connections
- File processing services
- Vector store integration
- WebSocket communication
- Structured logging

### 🚧 What's In Progress  
- Lambda Labs GPU integration
- MCP server implementation
- Production monitoring
- Automated deployment

### 🔄 Next Steps
1. Setup PostgreSQL database
2. Configure Lambda Labs GPU instances
3. Implement comprehensive monitoring
4. Setup CI/CD pipeline

## 💡 Pro Tips

1. **Use the setup script** - It fixes 90% of development issues
2. **Check the logs** - Both API and frontend show detailed error messages
3. **Use the API docs** - Visit http://localhost:8000/docs for interactive testing
4. **Monitor the console** - Watch for hot reload updates and error messages
5. **Keep it simple** - Use the startup scripts instead of complex commands

## 📞 Getting Help

If you encounter issues not covered here:

1. Check the terminal output for specific error messages
2. Verify all services are running on correct ports
3. Ensure virtual environment is activated
4. Run the setup script again to reset everything
5. Check the GitHub issues for similar problems

---

**Happy Development! 🎼✨** 