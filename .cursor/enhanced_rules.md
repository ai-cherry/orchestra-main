# 🎯 Orchestra AI - Enhanced AI Coder Rules & Guidelines

## 🚨 **CRITICAL: Anti-Junk File Rules**

### **🗑️ NEVER Create These Files**
```bash
# Temporary files that clutter the repository
*_temp.py          # Use proper temp directories instead
*_draft.py         # Use feature branches for drafts
*_backup.py        # Use git for version control
*_test.py          # Use tests/ directory structure
*_old.py           # Delete old code, don't rename
temp_*.py          # Use /tmp or proper temp directories
draft_*.py         # Use feature branches
backup_*.py        # Use git for backups
one_time_*.sh      # Archive in archive/one_time_scripts/
quick_*.sh         # Create proper scripts with descriptive names
temp_*.sh          # Use /tmp for temporary scripts
TEMP_*.md          # Use proper documentation structure
DRAFT_*.md         # Use feature branches for draft docs
*_BACKUP.md        # Use git for version control
```

### **🎯 File Creation Guidelines**
1. **Use descriptive, permanent names** - `user_authentication.py` not `temp_auth.py`
2. **Follow project structure** - Place files in appropriate directories
3. **Use git for versions** - Don't create backup files manually
4. **Archive one-time scripts** - Move to `archive/one_time_scripts/`
5. **Check DOCUMENTATION_INDEX.md** - Before creating new docs

---

## 🏗️ **Project Architecture Overview**

### **Core Technology Stack**
- **Backend**: FastAPI (Python 3.11+) with async/await patterns
- **Frontend**: React 18+ with TypeScript, Vite, Tailwind CSS
- **Databases**: PostgreSQL (primary), Redis (cache), Pinecone/Weaviate (vectors)
- **Infrastructure**: Pulumi (Python-based IaC), Lambda Labs (GPU), Docker
- **Deployment**: Vercel (frontend), Lambda Labs (backend)

### **Directory Structure**
```
orchestra-main/
├── api/                    # FastAPI backend
│   ├── main.py            # Main application
│   ├── health_monitor.py  # Health monitoring API
│   └── database/          # Database models and connections
├── modern-admin/          # React admin interface
│   └── src/components/    # UI components
├── security/              # Security and secret management
├── tests/                 # Test suite (unit, integration)
├── archive/               # Archived files (don't modify)
└── .cursor/               # Cursor AI configuration
```

---

## 🎯 **AI Agent Behavior Rules**

### **1. Code Generation Standards**

#### **Backend (FastAPI) Patterns**
```python
# ✅ ALWAYS use this pattern for new API endpoints
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import structlog

router = APIRouter(prefix="/api/feature", tags=["feature"])
logger = structlog.get_logger(__name__)

@router.get("/")
async def get_feature_data() -> Dict[str, Any]:
    """Get feature data with proper error handling."""
    try:
        # Implementation
        logger.info("Feature data retrieved successfully")
        return {"status": "success", "data": data}
    except Exception as e:
        logger.error("Failed to retrieve feature data", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### **Frontend (React) Patterns**
```typescript
// ✅ ALWAYS use this pattern for new components
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ComponentProps {
  data: DataType;
  onUpdate: (data: DataType) => Promise<void>;
}

export const FeatureComponent: React.FC<ComponentProps> = ({ data, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Implementation with proper error handling
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Feature Title</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Content with loading and error states */}
      </CardContent>
    </Card>
  );
};
```

### **2. Secret Management Rules**

#### **✅ ALWAYS Use Enhanced Secret Manager**
```python
# Import the centralized secret manager
from security.enhanced_secret_manager import secret_manager

# Get secrets (supports .env, Pulumi, encrypted files)
api_key = secret_manager.get_secret("OPENAI_API_KEY")
database_url = secret_manager.get_secret("DATABASE_URL")

# For AI agent context (masked for security)
secrets_status = secret_manager.get_all_secrets_for_ai_agents()
```

#### **🚨 NEVER Hardcode Secrets**
```python
# ❌ NEVER do this
api_key = "sk-1234567890abcdef"
database_url = "postgresql://user:pass@host:5432/db"

# ✅ ALWAYS do this
api_key = secret_manager.get_secret("OPENAI_API_KEY")
database_url = secret_manager.get_secret("DATABASE_URL")
```

### **3. Health Monitoring Integration**

#### **✅ ALWAYS Check Health Status**
```python
# Use health monitoring for system awareness
from api.health_monitor import health_monitor

# Check system health before major operations
health_data = await health_monitor.get_system_health()
if health_data["overall_status"] != "healthy":
    logger.warning("System health issues detected", status=health_data["overall_status"])
```

### **4. Database Patterns**

#### **✅ ALWAYS Use Async SQLAlchemy**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import UserModel

async def get_user(db: AsyncSession, user_id: str) -> UserModel:
    """Get user with proper async pattern."""
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

---

## 🎯 **Context-Aware Development**

### **Before Creating New Files**
1. **Check DOCUMENTATION_INDEX.md** - See if documentation already exists
2. **Check existing structure** - Follow established patterns
3. **Use descriptive names** - No temp, draft, or backup prefixes
4. **Consider the lifecycle** - Will this be permanent or temporary?

### **When Working with APIs**
1. **Check health status** - Use `/api/health/` endpoints
2. **Use secret manager** - Never hardcode credentials
3. **Follow FastAPI patterns** - Async, proper error handling, logging
4. **Include in health monitoring** - Add health checks for new services

### **When Working with Frontend**
1. **Use existing components** - Check `modern-admin/src/components/`
2. **Follow TypeScript patterns** - Proper types, error boundaries
3. **Integrate with health dashboard** - Add monitoring for new features
4. **Use Tailwind CSS** - Consistent styling with existing components

---

## 🚨 **Critical "DO NOT" Rules**

### **File Management**
- ❌ **DO NOT** create files with temp, draft, backup, or old prefixes
- ❌ **DO NOT** create one-time scripts in root directory
- ❌ **DO NOT** modify files in `archive/` directory
- ❌ **DO NOT** create duplicate documentation

### **Security**
- ❌ **DO NOT** hardcode API keys, passwords, or secrets
- ❌ **DO NOT** commit sensitive data to git
- ❌ **DO NOT** bypass the secret manager
- ❌ **DO NOT** disable security features

### **Code Quality**
- ❌ **DO NOT** skip error handling in async operations
- ❌ **DO NOT** use synchronous database operations
- ❌ **DO NOT** ignore TypeScript errors
- ❌ **DO NOT** skip logging for important operations

---

## ✅ **Always Do Rules**

### **Code Quality**
- ✅ **ALWAYS** use async/await for I/O operations
- ✅ **ALWAYS** include proper error handling and logging
- ✅ **ALWAYS** use type hints in Python and TypeScript
- ✅ **ALWAYS** follow established naming conventions

### **Integration**
- ✅ **ALWAYS** use the enhanced secret manager for credentials
- ✅ **ALWAYS** integrate new features with health monitoring
- ✅ **ALWAYS** follow the established directory structure
- ✅ **ALWAYS** check existing documentation before creating new

### **Testing**
- ✅ **ALWAYS** add tests for new functionality
- ✅ **ALWAYS** use the established test structure in `tests/`
- ✅ **ALWAYS** test error conditions and edge cases
- ✅ **ALWAYS** verify health monitoring integration

---

## 🎯 **AI Agent Context Helpers**

### **Quick Reference Commands**
```bash
# Check system health
curl http://localhost:8000/api/health/

# View secrets status (masked)
curl http://localhost:8000/api/health/secrets

# Check service status
curl http://localhost:8000/api/health/system

# View API documentation
open http://localhost:8000/docs
```

### **Common File Locations**
- **API endpoints**: `api/` directory
- **React components**: `modern-admin/src/components/`
- **Database models**: `api/database/models/`
- **Tests**: `tests/unit/` or `tests/integration/`
- **Documentation**: Root directory (check DOCUMENTATION_INDEX.md first)
- **Scripts**: Root directory (active) or `archive/one_time_scripts/` (historical)

### **Integration Points**
- **Health monitoring**: Add endpoints to `api/health_monitor.py`
- **Secret management**: Use `security/enhanced_secret_manager.py`
- **Frontend health**: Integrate with `modern-admin/src/components/HealthDashboard.jsx`
- **Testing**: Add to appropriate `tests/` subdirectory

---

## 🎼 **Orchestra AI Philosophy**

**"Build once, maintain forever"** - Create permanent, well-structured code that integrates seamlessly with the existing architecture. Every file should have a clear purpose, proper error handling, and integration with our monitoring and security systems.

**Remember**: You're not just writing code, you're contributing to a production-ready AI orchestration platform that needs to be reliable, secure, and maintainable.

