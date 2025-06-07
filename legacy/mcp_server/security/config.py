"""
Security configuration for MCP servers
"""

import os
from typing import Dict, List
from datetime import timedelta

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# API Key Configuration
API_KEY_HEADER = "X-API-Key"
API_KEY_PREFIX = "sk-"
API_KEY_LENGTH = 48

# Rate Limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = timedelta(minutes=1)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
ALLOWED_HEADERS = ["*"]

# Security Headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
}

# Password Policy
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = True

# Session Configuration
SESSION_TIMEOUT = timedelta(hours=24)
SESSION_SECURE_COOKIE = True
SESSION_HTTPONLY = True
SESSION_SAMESITE = "Strict"

# Encryption
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
ENCRYPTION_ALGORITHM = "AES-256-GCM"

def validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    if not api_key:
        return False
    if not api_key.startswith(API_KEY_PREFIX):
        return False
    if len(api_key) != len(API_KEY_PREFIX) + API_KEY_LENGTH:
        return False
    return True

def get_security_headers() -> Dict[str, str]:
    """Get security headers for responses"""
    return SECURITY_HEADERS.copy()
