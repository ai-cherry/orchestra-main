"""
Single-user context-based security system for Cherry AI
Optimized for solo developer projects with operational contexts instead of user roles
"""

from enum import Enum
from typing import Dict, Set, Optional
from pydantic import BaseModel
import os
from datetime import datetime, timedelta
import hashlib
import secrets

class OperationalContext(str, Enum):
    """Operational contexts for single-user deployment"""
    DEVELOPMENT = "development"  # Full access, debug enabled, relaxed security
    PRODUCTION = "production"    # Standard operations, security enforced
    MAINTENANCE = "maintenance"  # System updates, monitoring, limited operations
    TESTING = "testing"         # Test mode with isolated resources

class ContextPermission(str, Enum):
    """Permissions based on operational needs rather than user roles"""
    # Development permissions
    DEBUG_ACCESS = "debug_access"
    HOT_RELOAD = "hot_reload"
    DIRECT_DB_ACCESS = "direct_db_access"
    
    # Core operations
    EXECUTE_WORKFLOWS = "execute_workflows"
    MODIFY_AGENTS = "modify_agents"
    ACCESS_LOGS = "access_logs"
    
    # Data operations
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    DELETE_DATA = "delete_data"
    
    # System operations
    SYSTEM_CONFIG = "system_config"
    DEPLOY_CHANGES = "deploy_changes"
    MONITOR_METRICS = "monitor_metrics"
    
    # API operations
    API_FULL_ACCESS = "api_full_access"
    API_READ_ONLY = "api_read_only"
    API_RATE_LIMIT_BYPASS = "api_rate_limit_bypass"

# Context to permissions mapping
CONTEXT_PERMISSIONS: Dict[OperationalContext, Set[ContextPermission]] = {
    OperationalContext.DEVELOPMENT: set(ContextPermission),  # All permissions in dev
    
    OperationalContext.PRODUCTION: {
        ContextPermission.EXECUTE_WORKFLOWS,
        ContextPermission.MODIFY_AGENTS,
        ContextPermission.ACCESS_LOGS,
        ContextPermission.READ_DATA,
        ContextPermission.WRITE_DATA,
        ContextPermission.MONITOR_METRICS,
        ContextPermission.API_FULL_ACCESS,
    },
    
    OperationalContext.MAINTENANCE: {
        ContextPermission.ACCESS_LOGS,
        ContextPermission.READ_DATA,
        ContextPermission.SYSTEM_CONFIG,
        ContextPermission.MONITOR_METRICS,
        ContextPermission.API_READ_ONLY,
    },
    
    OperationalContext.TESTING: {
        ContextPermission.EXECUTE_WORKFLOWS,
        ContextPermission.READ_DATA,
        ContextPermission.WRITE_DATA,
        ContextPermission.API_FULL_ACCESS,
        ContextPermission.API_RATE_LIMIT_BYPASS,
    },
}

class SecurityContext(BaseModel):
    """Security context for single-user operations"""
    context: OperationalContext
    api_key_hash: str
    permissions: Set[ContextPermission] = set()
    created_at: datetime
    last_used: datetime
    request_count: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-assign permissions based on context
        if not self.permissions:
            self.permissions = CONTEXT_PERMISSIONS.get(self.context, set())
    
    def has_permission(self, permission: ContextPermission) -> bool:
        """Check if context allows specific permission"""
        return permission in self.permissions
    
    def update_usage(self):
        """Update usage statistics"""
        self.last_used = datetime.utcnow()
        self.request_count += 1

class SingleUserAuth:
    """Simplified authentication for single-user deployment"""
    
    def __init__(self):
        self.api_key = os.getenv("cherry_ai_API_KEY", "")
        self.context = self._determine_context()
        self._security_context: Optional[SecurityContext] = None
        
    def _determine_context(self) -> OperationalContext:
        """Determine operational context from environment"""
        env = os.getenv("cherry_ai_CONTEXT", "development").lower()
        
        context_map = {
            "dev": OperationalContext.DEVELOPMENT,
            "development": OperationalContext.DEVELOPMENT,
            "prod": OperationalContext.PRODUCTION,
            "production": OperationalContext.PRODUCTION,
            "maint": OperationalContext.MAINTENANCE,
            "maintenance": OperationalContext.MAINTENANCE,
            "test": OperationalContext.TESTING,
            "testing": OperationalContext.TESTING,
        }
        
        return context_map.get(env, OperationalContext.DEVELOPMENT)
    
    def _hash_api_key(self, api_key: str) -> str:
        """Securely hash API key for comparison"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def authenticate(self, provided_key: Optional[str]) -> SecurityContext:
        """Authenticate and return security context"""
        # Development mode bypass
        if self.context == OperationalContext.DEVELOPMENT and not self.api_key:
            return SecurityContext(
                context=self.context,
                api_key_hash="dev_mode",
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow()
            )
        
        # Validate API key
        if not provided_key or not self.api_key:
            raise ValueError("API key required")
        
        if provided_key != self.api_key:
            raise ValueError("Invalid API key")
        
        # Create or update security context
        if not self._security_context:
            self._security_context = SecurityContext(
                context=self.context,
                api_key_hash=self._hash_api_key(provided_key),
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow()
            )
        else:
            self._security_context.update_usage()
        
        return self._security_context
    
    def check_permission(self, 
                        context: SecurityContext, 
                        permission: ContextPermission) -> bool:
        """Check if current context has permission"""
        return context.has_permission(permission)
    
    def get_rate_limit(self) -> Dict[str, int]:
        """Get rate limits based on context"""
        rate_limits = {
            OperationalContext.DEVELOPMENT: {
                "requests_per_minute": 1000,
                "requests_per_hour": 50000,
                "burst_size": 100
            },
            OperationalContext.PRODUCTION: {
                "requests_per_minute": 100,
                "requests_per_hour": 5000,
                "burst_size": 20
            },
            OperationalContext.MAINTENANCE: {
                "requests_per_minute": 50,
                "requests_per_hour": 1000,
                "burst_size": 10
            },
            OperationalContext.TESTING: {
                "requests_per_minute": 500,
                "requests_per_hour": 25000,
                "burst_size": 50
            }
        }
        
        return rate_limits.get(self.context, rate_limits[OperationalContext.PRODUCTION])

# Singleton instance
auth_manager = SingleUserAuth()

def get_auth_manager() -> SingleUserAuth:
    """Get the singleton auth manager instance"""
    return auth_manager

def require_permission(permission: ContextPermission):
    """Decorator to require specific permission for endpoint"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract security context from request
            context = kwargs.get('security_context')
            if not context:
                raise ValueError("Security context required")
            
            if not auth_manager.check_permission(context, permission):
                raise PermissionError(f"Permission {permission} required")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator