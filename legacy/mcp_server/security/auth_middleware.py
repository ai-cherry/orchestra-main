"""
Authentication middleware for single-user Cherry AI deployment
Provides clean, performant authentication with minimal overhead
"""

from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, Any
import time
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from .single_user_context import (
    get_auth_manager, 
    SecurityContext, 
    OperationalContext,
    ContextPermission
)

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter for single-user deployment"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.cleanup_interval = 300  # Clean up old entries every 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(self, key: str, limits: Dict[str, int]) -> bool:
        """Check if request is within rate limits"""
        now = time.time()
        
        # Periodic cleanup
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
            self.last_cleanup = now
        
        # Get request history
        request_times = self.requests[key]
        
        # Check per-minute limit
        minute_ago = now - 60
        recent_requests = [t for t in request_times if t > minute_ago]
        
        if len(recent_requests) >= limits["requests_per_minute"]:
            return False
        
        # Check burst size
        if len(recent_requests) >= limits["burst_size"]:
            # Check if requests are spread out enough
            if recent_requests[-1] - recent_requests[0] < 1:  # Within 1 second
                return False
        
        # Record this request
        self.requests[key].append(now)
        
        return True
    
    def _cleanup(self):
        """Remove old request records"""
        cutoff = time.time() - 3600  # Keep last hour only
        for key in list(self.requests.keys()):
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
            if not self.requests[key]:
                del self.requests[key]

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for single-user authentication"""
    
    def __init__(self, app, skip_paths: Optional[list] = None):
        super().__init__(app)
        self.auth_manager = get_auth_manager()
        self.rate_limiter = RateLimiter()
        self.skip_paths = skip_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        """Process each request for authentication"""
        
        # Skip authentication for certain paths
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            # Extract API key from header
            api_key = request.headers.get("X-API-Key")
            
            # Authenticate and get security context
            security_context = self.auth_manager.authenticate(api_key)
            
            # Check rate limits (unless in development mode)
            if security_context.context != OperationalContext.DEVELOPMENT:
                rate_limits = self.auth_manager.get_rate_limit()
                if not self.rate_limiter.is_allowed(security_context.api_key_hash, rate_limits):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded"
                    )
            
            # Attach security context to request state
            request.state.security_context = security_context
            request.state.auth_time = time.time() - start_time
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Add context header for debugging
            if security_context.context == OperationalContext.DEVELOPMENT:
                response.headers["X-cherry_ai-Context"] = security_context.context
                response.headers["X-Auth-Time-Ms"] = f"{(time.time() - start_time) * 1000:.2f}"
            
            return response
            
        except ValueError as e:
            # Authentication failed
            logger.warning(f"Authentication failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key"
            )
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Authentication middleware error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication system error"
            )

def get_security_context(request: Request) -> SecurityContext:
    """Extract security context from request"""
    if not hasattr(request.state, "security_context"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No security context found"
        )
    return request.state.security_context

def require_context(*allowed_contexts: OperationalContext):
    """Dependency to require specific operational contexts"""
    async def dependency(request: Request):
        context = get_security_context(request)
        if context.context not in allowed_contexts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not allowed in {context.context} context"
            )
        return context
    return dependency

def require_permission(permission: ContextPermission):
    """Dependency to require specific permission"""
    async def dependency(request: Request):
        context = get_security_context(request)
        if not context.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission {permission} required"
            )
        return context
    return dependency

# Convenience dependencies
require_production = require_context(OperationalContext.PRODUCTION)
require_development = require_context(OperationalContext.DEVELOPMENT)
require_maintenance = require_context(OperationalContext.MAINTENANCE)