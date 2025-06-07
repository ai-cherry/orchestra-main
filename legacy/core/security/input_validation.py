"""
Input validation middleware for AI Orchestration
Prevents injection attacks and validates all inputs
"""

import re
import json
from typing import Any, Dict, List, Optional
from functools import wraps
import bleach
from pydantic import BaseModel, validator, ValidationError

class InputValidator:
    """Comprehensive input validation for all user inputs"""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"((SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER))",
        r"(--|#|/\*|\*/)",
        r"(OR\s*\d+\s*=\s*\d+)",
        r"(AND\s*\d+\s*=\s*\d+)",
        r"(;|\||&&)"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>"
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
            
        # Truncate to max length
        value = value[:max_length]
        
        # Remove any HTML tags
        value = bleach.clean(value, tags=[], strip=True)
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError("Potential SQL injection detected")
                
        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValueError("Potential XSS attack detected")
                
        return value
        
    @classmethod
    def validate_json(cls, value: str) -> Dict[str, Any]:
        """Validate JSON input"""
        try:
            data = json.loads(value)
            # Recursively sanitize all string values
            return cls._sanitize_dict(data)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
            
    @classmethod
    def _sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values"""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = cls._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls._sanitize_dict(item) if isinstance(item, dict)
                    else cls.sanitize_string(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

# Pydantic models for request validation
class QueryRequest(BaseModel):
    query: str
    domain: Optional[str] = None
    max_results: int = 10
    
    @validator('query')
    def validate_query(cls, v):
        return InputValidator.sanitize_string(v, max_length=500)
        
    @validator('domain')
    def validate_domain(cls, v):
        if v and v not in ['cherry', 'sophia', 'paragonrx']:
            raise ValueError('Invalid domain')
        return v
        
    @validator('max_results')
    def validate_max_results(cls, v):
        if v < 1 or v > 100:
            raise ValueError('max_results must be between 1 and 100')
        return v

class WebScrapingRequest(BaseModel):
    url: str
    scraping_type: str
    
    @validator('url')
    def validate_url(cls, v):
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v

def validate_input(request_model: BaseModel):
    """Decorator for input validation"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request data from kwargs or args
            request_data = kwargs.get('request_data') or (args[1] if len(args) > 1 else {})
            
            try:
                # Validate using Pydantic model
                validated_data = request_model(**request_data)
                kwargs['validated_data'] = validated_data
                return await func(*args, **kwargs)
            except ValidationError as e:
                raise ValueError(f"Input validation failed: {e}")
                
        return wrapper
    return decorator
