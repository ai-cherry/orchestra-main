# 🤝 Cursor AI Coding Guidelines for the Orchestra AI Platform - ENHANCED

This document outlines enhanced best practices for working with Cursor AI within the Orchestra AI codebase, including critical anti-junk file rules and integration with our production-ready infrastructure.

## 🚨 **CRITICAL: Anti-Junk File Rules**

### **🗑️ NEVER Create These File Patterns**
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

### **✅ Proper File Creation Guidelines**
1. **Use descriptive, permanent names** - `user_authentication.py` not `temp_auth.py`
2. **Check DOCUMENTATION_INDEX.md** - Before creating new documentation
3. **Follow project structure** - Place files in appropriate directories
4. **Use git for versions** - Don't create backup files manually
5. **Archive one-time scripts** - Move to `archive/one_time_scripts/`

## 🏛️ **Enhanced Architectural Principles**

### **Production-Ready Infrastructure**
- **Backend**: FastAPI with async/await, PostgreSQL, Redis, Vector DBs
- **Frontend**: React 18+ with TypeScript, Tailwind CSS, shadcn/ui
- **Infrastructure**: Pulumi (Python-based IaC), Lambda Labs GPU
- **Deployment**: Vercel (frontend), Lambda Labs (backend)
- **Monitoring**: Comprehensive health monitoring system
- **Security**: Centralized secret management with encryption

### **Key Integration Points**
1. **Secret Management**: Always use `security/enhanced_secret_manager.py`
2. **Health Monitoring**: Integrate with `api/health_monitor.py`
3. **Database**: Async SQLAlchemy patterns only
4. **Testing**: Use established `tests/` structure
5. **Documentation**: Follow `DOCUMENTATION_INDEX.md` guidelines

## ✍️ **Enhanced Prompting Best Practices**

### **Context-Aware Prompting**
```bash
# ✅ GOOD: Specific, context-aware prompts
"Add a new health check endpoint to the health monitoring system for checking Pinecone vector database connectivity. Use the existing pattern in api/health_monitor.py and integrate with the enhanced secret manager for API key access."

# ❌ BAD: Vague, context-free prompts  
"Add a health check for the database."
```

### **Integration-Focused Requests**
```bash
# ✅ GOOD: Integration-aware requests
"Create a new React component for displaying API health status in the admin dashboard. It should fetch data from /api/health/apis endpoint and integrate with the existing HealthDashboard component styling."

# ❌ BAD: Isolated requests
"Make a component that shows API status."
```

## 🎯 **Enhanced Development Patterns**

### **Backend Development (FastAPI)**
```python
# ✅ ALWAYS use this enhanced pattern
from fastapi import APIRouter, HTTPException, Depends
from security.enhanced_secret_manager import secret_manager
from api.health_monitor import health_monitor
import structlog

router = APIRouter(prefix="/api/feature", tags=["feature"])
logger = structlog.get_logger(__name__)

@router.get("/")
async def get_feature_data() -> Dict[str, Any]:
    """Get feature data with comprehensive error handling and monitoring."""
    try:
        # Check system health before major operations
        health_data = await health_monitor.get_system_health()
        if health_data["overall_status"] != "healthy":
            logger.warning("System health issues detected", status=health_data["overall_status"])
        
        # Use secret manager for any API keys
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

### **Frontend Development (React + TypeScript)**
```typescript
// ✅ ALWAYS use this enhanced pattern
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

interface FeatureComponentProps {
  data: DataType;
  onUpdate: (data: DataType) => Promise<void>;
}

export const FeatureComponent: React.FC<FeatureComponentProps> = ({ data, onUpdate }) => {
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
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const handleUpdate = async () => {
    setLoading(true);
    setError(null);
    
    try {
      await onUpdate(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Feature Component</CardTitle>
        <Badge variant={healthStatus === 'healthy' ? 'default' : 'destructive'}>
          {healthStatus}
        </Badge>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {/* Component content with proper loading and error states */}
        
        <button 
          onClick={handleUpdate}
          disabled={loading || healthStatus !== 'healthy'}
          className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded disabled:opacity-50"
        >
          {loading ? 'Updating...' : 'Update'}
        </button>
      </CardContent>
    </Card>
  );
};
```

## 🔧 **Enhanced Task Patterns**

### **Adding New API Endpoints**
```bash
# ✅ Enhanced prompt pattern
"Add a new API endpoint at /api/users/{user_id}/preferences for managing user preferences. 
- Use the existing FastAPI pattern in api/main.py
- Integrate with enhanced secret manager for any external API calls
- Add health monitoring for the new service dependencies
- Include comprehensive error handling and logging
- Add corresponding tests in tests/unit/
- Update the health dashboard if this affects system health"
```

### **Creating New React Components**
```bash
# ✅ Enhanced prompt pattern
"Create a new UserPreferences component for the admin dashboard.
- Follow the existing pattern in modern-admin/src/components/
- Integrate with the health monitoring system to show connection status
- Use proper TypeScript types and error boundaries
- Include loading states and error handling
- Style with Tailwind CSS to match existing components
- Add to the appropriate route in App.jsx"
```

### **Database Operations**
```bash
# ✅ Enhanced prompt pattern
"Add a new database model for user preferences.
- Create the model in api/database/models/
- Use async SQLAlchemy patterns
- Include proper relationships and constraints
- Add migration script
- Create corresponding service in api/services/
- Add health check for database connectivity
- Include tests for the new model and service"
```

## 🎯 **Quality Assurance Patterns**

### **Before Submitting Code**
1. **No junk files created** - Check for temp, draft, backup patterns
2. **Secret manager integration** - No hardcoded credentials
3. **Health monitoring** - New services have health checks
4. **Error handling** - Comprehensive try/catch with logging
5. **TypeScript compliance** - No `any` types without justification
6. **Test coverage** - Unit and integration tests included

### **Integration Checklist**
- [ ] Uses enhanced secret manager for credentials
- [ ] Integrates with health monitoring system
- [ ] Follows established directory structure
- [ ] Includes proper error handling and logging
- [ ] Has corresponding tests
- [ ] Updates documentation if needed
- [ ] No temporary or junk files created

## 🚨 **Critical Success Factors**

### **File Management Excellence**
- **Zero junk files** - Use proper naming conventions
- **Organized structure** - Follow established patterns
- **Git for versions** - No manual backup files
- **Archive properly** - One-time scripts go to archive/

### **Integration Excellence**
- **Secret management** - Always use the centralized system
- **Health monitoring** - Integrate all new services
- **Error handling** - Comprehensive and user-friendly
- **Testing** - Cover all new functionality

### **Code Quality Excellence**
- **Async patterns** - Use async/await for I/O operations
- **Type safety** - Proper TypeScript and Python types
- **Documentation** - Clear, comprehensive, up-to-date
- **Performance** - Efficient, scalable implementations

By following these enhanced guidelines, Cursor AI will generate production-ready code that integrates seamlessly with the Orchestra AI platform's sophisticated architecture while maintaining the highest standards of code quality and system reliability. 