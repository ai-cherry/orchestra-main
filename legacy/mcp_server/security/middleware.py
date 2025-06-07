"""
Security middleware for MCP servers
"""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import jwt
from .config import (
    JWT_SECRET_KEY, JWT_ALGORITHM, 
    API_KEY_HEADER, validate_api_key,
    get_security_headers, RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW
)
from .api_keys import APIKeyManager
from .rbac import UserRole, check_permission, Permission

class SecurityMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        headers = get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
            
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""

    def __init__(self, app):
        super().__init__(app)
        self.request_counts: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP or API key)
        client_id = request.client.host
        api_key = request.headers.get(API_KEY_HEADER)
        if api_key:
            client_id = f"api_key:{api_key}"

        # Check rate limit
        current_time = time.time()
        window_start = current_time - RATE_LIMIT_WINDOW.total_seconds()

        if client_id not in self.request_counts:
            self.request_counts[client_id] = []

        # Remove old requests
        self.request_counts[client_id] = [
            req_time for req_time in self.request_counts[client_id]
            if req_time > window_start
        ]

        # Check if limit exceeded
        if len(self.request_counts[client_id]) >= RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        # Add current request
        self.request_counts[client_id].append(current_time)

        response = await call_next(request)
        return response
