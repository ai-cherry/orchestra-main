"""
CORS configuration for AI Orchestration API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

def configure_cors(app: FastAPI):
    """Configure CORS middleware with security best practices"""
    
    # Get allowed origins from environment
    allowed_origins = os.getenv(
        "CORS_ALLOWED_ORIGINS", 
        "http://localhost:3000,http://localhost:8000"
    ).split(",")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRF-Token"
        ],
        expose_headers=["X-Total-Count", "X-Page-Count"],
        max_age=3600  # Cache preflight requests for 1 hour
    )
    
    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
        
    return app
