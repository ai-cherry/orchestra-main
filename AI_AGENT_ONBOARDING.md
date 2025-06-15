# 🤖 AI Agent Onboarding Guide for Orchestra AI

## 🎯 **Welcome, AI Coding Agent!**

This guide provides essential context for AI coding agents working on the Orchestra AI platform. Follow this guide to understand the codebase, patterns, and integration points.

## 🏗️ **Platform Overview**

### **What is Orchestra AI?**
Orchestra AI is a production-ready AI orchestration platform that integrates multiple AI services, databases, and tools into a unified system. It serves as a central hub for AI operations with comprehensive monitoring, security, and scalability.

### **Core Architecture**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Infrastructure│
│   React/TS      │◄──►│   FastAPI       │◄──►│   Pulumi/Lambda │
│   Tailwind CSS  │    │   PostgreSQL    │    │   Docker/K8s    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Components │    │   Health Monitor│    │   Secret Manager│
│   Health Dash   │    │   API Gateway   │    │   Vector DBs    │
│   Admin Panel   │    │   MCP Servers   │    │   Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚨 **Critical Rules for AI Agents**

### **🗑️ NEVER Create These Files**
```bash
# Temporary files that clutter the repository
*_temp.py          # Use proper temp directories
*_draft.py         # Use feature branches
*_backup.py        # Use git for version control
*_test.py          # Use tests/ directory
*_old.py           # Delete old code, don't rename
temp_*.py          # Use /tmp directories
draft_*.py         # Use feature branches
backup_*.py        # Use git for backups
```

### **✅ Always Follow These Patterns**
1. **Use descriptive, permanent names** - `user_authentication.py` not `temp_auth.py`
2. **Check existing documentation** - Review MASTER_DOCUMENTATION_INDEX.md first
3. **Follow project structure** - Place files in appropriate directories
4. **Use git for versions** - Don't create backup files manually
5. **Integrate with monitoring** - Add health checks for new services

## 🎯 **Essential Integration Points**

### **1. Secret Management**
```python
# ✅ ALWAYS use the enhanced secret manager
from security.enhanced_secret_manager import secret_manager

# Get secrets (supports .env, Pulumi, encrypted files)
api_key = secret_manager.get_secret("OPENAI_API_KEY")
database_url = secret_manager.get_secret("DATABASE_URL")

# ❌ NEVER hardcode secrets
api_key = "sk-1234567890abcdef"  # DON'T DO THIS
```

### **2. Health Monitoring**
```python
# ✅ ALWAYS integrate with health monitoring
from api.health_monitor import health_monitor

# Check system health before major operations
health_data = await health_monitor.get_system_health()
if health_data["overall_status"] != "healthy":
    logger.warning("System health issues detected")
```

### **3. Database Operations**
```python
# ✅ ALWAYS use async SQLAlchemy patterns
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import UserModel

async def get_user(db: AsyncSession, user_id: str) -> UserModel:
    """Get user with proper async pattern."""
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

### **4. Error Handling & Logging**
```python
# ✅ ALWAYS include comprehensive error handling
import structlog
logger = structlog.get_logger(__name__)

async def process_data(data: Dict[str, Any]) -> ProcessResult:
    """Process data with comprehensive error handling."""
    try:
        logger.info("Processing data", data_size=len(data))
        # Implementation
        logger.info("Data processed successfully")
        return result
    except Exception as e:
        logger.error("Data processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Processing failed")
```

## 📁 **Directory Structure & File Placement**

### **Backend Files**
```
api/
├── main.py                 # Main FastAPI application
├── health_monitor.py       # Health monitoring endpoints
├── database/
│   ├── connection.py       # Database connection management
│   └── models.py          # SQLAlchemy models
└── services/              # Business logic services
```

### **Frontend Files**
```
modern-admin/src/
├── components/            # React components
│   ├── ui/               # Base UI components
│   └── HealthDashboard.jsx # Health monitoring UI
├── pages/                # Page components
└── lib/                  # Utilities and helpers
```

### **Infrastructure Files**
```
pulumi/                   # Infrastructure as code
security/                 # Secret management
tests/                   # Test suite
.cursor/                 # AI agent configuration
```

## 🎯 **Common Development Patterns**

### **Adding New API Endpoints**
```python
# Template for new API endpoints
from fastapi import APIRouter, HTTPException, Depends
from security.enhanced_secret_manager import secret_manager
import structlog

router = APIRouter(prefix="/api/feature", tags=["feature"])
logger = structlog.get_logger(__name__)

@router.get("/")
async def get_feature_data() -> Dict[str, Any]:
    """Get feature data with comprehensive error handling."""
    try:
        # Check system health
        health_data = await health_monitor.get_system_health()
        if health_data["overall_status"] != "healthy":
            logger.warning("System health issues detected")
        
        # Use secret manager for API keys
        api_key = secret_manager.get_secret("REQUIRED_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        # Implementation
        logger.info("Feature data retrieved successfully")
        return {"status": "success", "data": data}
        
    except Exception as e:
        logger.error("Failed to retrieve feature data", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
```

### **Creating React Components**
```typescript
// Template for new React components
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ComponentProps {
  data: DataType;
  onUpdate: (data: DataType) => Promise<void>;
}

export const FeatureComponent: React.FC<ComponentProps> = ({ data, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthStatus, setHealthStatus] = useState<string>('unknown');

  // Check health status
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('/api/health/');
        const health = await response.json();
        setHealthStatus(health.overall_status);
      } catch (err) {
        setHealthStatus('error');
      }
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Feature Component</CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {/* Component content */}
      </CardContent>
    </Card>
  );
};
```

## 🔧 **Development Workflow**

### **Before Starting Any Task**
1. **Check health status**: `curl http://localhost:8000/api/health/`
2. **Review existing code**: Look for similar patterns in the codebase
3. **Check documentation**: Review MASTER_DOCUMENTATION_INDEX.md
4. **Follow naming conventions**: Use descriptive, permanent names

### **During Development**
1. **Use async patterns**: All I/O operations should be async
2. **Include error handling**: Comprehensive try/catch with logging
3. **Integrate monitoring**: Add health checks for new services
4. **Follow type safety**: Use TypeScript types and Python type hints

### **After Implementation**
1. **Add tests**: Unit and integration tests in tests/ directory
2. **Update documentation**: Add or update relevant documentation
3. **Check integration**: Verify health monitoring integration
4. **Validate security**: Ensure proper secret management

## 📚 **Key Documentation References**

### **Essential Reading**
- [Cursor AI Rules](/.cursor/enhanced_rules.md) - Comprehensive coding guidelines
- [Architecture Overview](./ARCHITECTURE_OVERVIEW.md) - System architecture
- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Security Guide](./SECURITY_GUIDE.md) - Security patterns and practices

### **Development Guides**
- [Backend Development](./guides/BACKEND_DEVELOPMENT.md) - FastAPI patterns
- [Frontend Development](./guides/FRONTEND_DEVELOPMENT.md) - React patterns
- [Database Operations](./guides/DATABASE_OPERATIONS.md) - SQLAlchemy patterns
- [Testing Guide](./tests/README.md) - Testing patterns

### **Operations**
- [Deployment Guide](./DEPLOYMENT_GUIDE_MASTER.md) - Production deployment
- [Monitoring Guide](./guides/MONITORING_GUIDE.md) - System monitoring
- [Troubleshooting](./TROUBLESHOOTING_GUIDE.md) - Common issues

## 🎯 **Quick Commands for AI Agents**

### **Health Checks**
```bash
# Check overall system health
curl http://localhost:8000/api/health/

# Check specific service health
curl http://localhost:8000/api/health/database
curl http://localhost:8000/api/health/redis
curl http://localhost:8000/api/health/apis
```

### **Development Commands**
```bash
# Start development environment
./start_orchestra.sh

# Run tests
python -m pytest tests/

# Check code quality
python -m flake8 api/
npm run lint
```

### **Documentation Commands**
```bash
# View API documentation
open http://localhost:8000/docs

# Generate API documentation
python -m api.generate_docs

# Update documentation index
python scripts/update_docs_index.py
```

## 🚀 **Success Checklist**

### **For Every New Feature**
- [ ] Uses enhanced secret manager for credentials
- [ ] Integrates with health monitoring system
- [ ] Follows established directory structure
- [ ] Includes comprehensive error handling and logging
- [ ] Has corresponding tests
- [ ] Updates relevant documentation
- [ ] No temporary or junk files created
- [ ] Follows async/await patterns
- [ ] Uses proper TypeScript/Python types

### **Before Submitting Code**
- [ ] All tests pass
- [ ] Health monitoring integration works
- [ ] Documentation is updated
- [ ] No hardcoded secrets or credentials
- [ ] Follows established coding patterns
- [ ] Error handling is comprehensive
- [ ] Logging is structured and informative

## 🎼 **Orchestra AI Philosophy**

**"Build once, maintain forever"** - Create permanent, well-structured code that integrates seamlessly with the existing architecture. Every file should have a clear purpose, proper error handling, and integration with our monitoring and security systems.

**Remember**: You're contributing to a production-ready AI orchestration platform that needs to be reliable, secure, and maintainable. Follow the patterns, integrate with the systems, and create code that other AI agents can easily understand and extend.

---

**Welcome to the Orchestra AI development team! 🎼**

