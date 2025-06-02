"""
Pydantic validation utilities and custom validators for Orchestra AI.

This module provides reusable validators, strict types, and validation patterns
to ensure data integrity across the application.
"""

from typing import Any, Dict, List, Optional, Union
import re
from datetime import datetime
from pydantic import BaseModel, Field, StrictStr, StrictInt, validator, field_validator, ValidationError, computed_field, model_validator, field_serializer
from pydantic.config import ConfigDict
from decimal import Decimal

# Strict type aliases for common fields
StrictEmail = StrictStr
StrictUrl = StrictStr
StrictUUID = StrictStr


class StrictBaseModel(BaseModel):
    """Base model with strict validation and helpful error messages."""
    
    model_config = ConfigDict(
        validate_assignment=True,  # Validate on assignment
        use_enum_values=True,      # Use enum values instead of enum instances
        str_strip_whitespace=True, # Strip whitespace from strings
        json_schema_extra={        # Extra schema for OpenAPI
            "example": {}
        }
    )


# Custom validators for common patterns
def validate_email(email: str) -> str:
    """Validate email format."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError(f"Invalid email format: {email}")
    return email.lower()


def validate_url(url: str) -> str:
    """Validate URL format."""
    url_pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    if not re.match(url_pattern, url):
        raise ValueError(f"Invalid URL format: {url}")
    return url


def validate_api_key(api_key: str) -> str:
    """Validate API key format (alphanumeric, 32-64 chars)."""
    if not re.match(r'^[a-zA-Z0-9]{32,64}$', api_key):
        raise ValueError("API key must be 32-64 alphanumeric characters")
    return api_key


def validate_persona_slug(slug: str) -> str:
    """Validate persona slug format."""
    if not re.match(r'^[a-z0-9-]+$', slug):
        raise ValueError("Persona slug must contain only lowercase letters, numbers, and hyphens")
    return slug


def validate_temperature(temp: float) -> float:
    """Validate LLM temperature parameter."""
    if not 0.0 <= temp <= 2.0:
        raise ValueError("Temperature must be between 0.0 and 2.0")
    return temp


def validate_max_tokens(tokens: int) -> int:
    """Validate max tokens parameter."""
    if not 1 <= tokens <= 32000:
        raise ValueError("Max tokens must be between 1 and 32000")
    return tokens


# Example strict models for common entities
class StrictPersonaConfig(StrictBaseModel):
    """Strict validation for Persona configuration."""
    
    name: StrictStr = Field(..., min_length=1, max_length=100, description="Persona name")
    slug: str = Field(..., description="Unique persona identifier")
    description: StrictStr = Field(..., min_length=1, max_length=1000, description="Persona description")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: StrictInt = Field(2000, ge=100, le=32000, description="Maximum tokens")
    
    @field_validator("slug")
    def validate_slug(cls, v: str) -> str:
        return validate_persona_slug(v)
    
    @field_validator("temperature")
    def validate_temp(cls, v: float) -> float:
        return validate_temperature(v)


class StrictLLMRequest(StrictBaseModel):
    """Strict validation for LLM requests."""
    
    prompt: StrictStr = Field(..., min_length=1, max_length=10000, description="LLM prompt")
    model: StrictStr = Field(..., description="Model identifier")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[StrictInt] = Field(None, ge=1, le=32000)
    persona_id: Optional[str] = Field(None, description="Associated persona ID")
    
    @field_validator("persona_id")
    def validate_persona_id(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[a-zA-Z0-9-]+$', v):
            raise ValueError("Invalid persona ID format")
        return v


class StrictAPICredentials(StrictBaseModel):
    """Strict validation for API credentials."""
    
    api_key: StrictStr = Field(..., description="API key")
    endpoint: StrictUrl = Field(..., description="API endpoint URL")
    
    @field_validator("api_key")
    def validate_api_key_field(cls, v: str) -> str:
        return validate_api_key(v)
    
    @field_validator("endpoint")
    def validate_endpoint(cls, v: str) -> str:
        return validate_url(v)


# Validation error formatter
def format_validation_errors(errors: List[Dict[str, Any]]) -> str:
    """
    Format Pydantic validation errors into user-friendly messages.
    
    Args:
        errors: List of error dictionaries from Pydantic
        
    Returns:
        Formatted error message string
    """
    messages = []
    for error in errors:
        loc = " → ".join(str(x) for x in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        error_type = error.get("type", "value_error")
        
        # Customize messages based on error type
        if error_type == "missing":
            messages.append(f"Missing required field: {loc}")
        elif error_type == "string_too_short":
            messages.append(f"{loc}: Value is too short")
        elif error_type == "string_too_long":
            messages.append(f"{loc}: Value is too long")
        elif error_type == "value_error":
            messages.append(f"{loc}: {msg}")
        else:
            messages.append(f"{loc}: {msg}")
    
    return "; ".join(messages)


# Performance-optimized validation
class OptimizedModel(BaseModel):
    """Base model with performance optimizations."""
    
    model_config = ConfigDict(
        validate_default=False,    # Don't validate defaults
        validate_return=False,     # Don't validate return values
        revalidate_instances="never"  # Don't revalidate instances
    )
    
    @classmethod
    def construct_fast(cls, **data):
        """
        Fast construction without validation for trusted data.
        Use only when data is pre-validated or from trusted sources.
        """
        return cls.model_construct(**data)


# Validation context manager for batch operations
class ValidationContext:
    """Context manager for efficient batch validation."""
    
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.validated_count = 0
        
    def validate_item(self, model_class: type[BaseModel], data: Dict[str, Any]) -> Optional[BaseModel]:
        """Validate a single item, collecting errors."""
        try:
            instance = model_class(**data)
            self.validated_count += 1
            return instance
        except ValidationError as e:
            self.errors.extend(e.errors())
            return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            "validated": self.validated_count,
            "errors": len(self.errors),
            "error_details": self.errors[:10]  # First 10 errors
        }


# Performance-optimized validation with computed fields
class EnhancedPersonaConfig(StrictBaseModel):
    """Enhanced persona configuration with computed fields for performance."""
    
    name: StrictStr = Field(..., min_length=1, max_length=100)
    slug: str = Field(...)
    description: StrictStr = Field(..., min_length=1, max_length=1000)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: StrictInt = Field(2000, ge=100, le=32000)
    capabilities: List[str] = Field(default_factory=list)
    
    @computed_field
    @property
    def capability_count(self) -> int:
        """Computed field for UI display - no DB query needed."""
        return len(self.capabilities)
    
    @computed_field
    @property  
    def complexity_score(self) -> float:
        """Performance scoring for LLM routing decisions."""
        base_score = len(self.capabilities) * 0.1
        temp_factor = self.temperature * 0.5
        token_factor = (self.max_tokens / 1000) * 0.2
        return round(base_score + temp_factor + token_factor, 2)
    
    @field_validator("capabilities")
    def validate_capabilities(cls, v: List[str]) -> List[str]:
        """Ensure capabilities are valid and normalized."""
        valid_capabilities = {
            'text-generation', 'code-generation', 'analysis', 
            'summarization', 'translation', 'reasoning'
        }
        for cap in v:
            if cap not in valid_capabilities:
                raise ValueError(f"Invalid capability: {cap}")
        return list(set(v))  # Remove duplicates


# Cross-field validation for LLM routing
class LLMRoutingConfig(StrictBaseModel):
    """LLM routing configuration with business rule validation."""
    
    primary_model: StrictStr
    fallback_models: List[str] = Field(default_factory=list)
    use_fallback: bool = Field(default=True)
    max_cost_per_request: Decimal = Field(default=Decimal('0.10'))
    max_latency_ms: int = Field(default=5000, ge=100, le=30000)
    
    @model_validator(mode='after')
    def validate_routing_logic(self):
        """Ensure routing configuration is logically consistent."""
        if self.use_fallback and not self.fallback_models:
            raise ValueError("Fallback models required when use_fallback=True")
        
        if self.primary_model in self.fallback_models:
            raise ValueError("Primary model cannot be in fallback list")
        
        # Business rule: expensive models should have fallbacks
        expensive_models = {'gpt-4', 'claude-3-opus', 'gemini-pro'}
        if (self.primary_model in expensive_models and 
            not self.fallback_models and 
            self.max_cost_per_request > Decimal('0.05')):
            raise ValueError("Expensive models should have fallback options")
        
        return self


# API response model with custom serialization
class APIResponseModel(StrictBaseModel):
    """Enhanced API response with custom serialization for frontend."""
    
    status: str = Field(...)
    data: Any = Field(...)
    cost: Optional[Decimal] = Field(None)
    processing_time_ms: Optional[int] = Field(None)
    
    @field_serializer('cost')
    def serialize_cost(self, value: Optional[Decimal]) -> Optional[str]:
        """Format cost for frontend display."""
        if value is None:
            return None
        return f"${value:.4f}"
    
    @computed_field
    @property
    def performance_grade(self) -> str:
        """Performance grade based on response time."""
        if self.processing_time_ms is None:
            return "unknown"
        
        if self.processing_time_ms < 1000:
            return "excellent"
        elif self.processing_time_ms < 3000:
            return "good"
        elif self.processing_time_ms < 5000:
            return "fair"
        else:
            return "poor"


# Enhanced validation context with caching
class CachedValidationContext(ValidationContext):
    """Validation context with performance caching."""
    
    def __init__(self, cache_size: int = 1000):
        super().__init__()
        self._validation_cache: Dict[str, Any] = {}
        self._cache_size = cache_size
    
    def validate_item_cached(self, model_class: type[BaseModel], data: Dict[str, Any], cache_key: Optional[str] = None) -> Optional[BaseModel]:
        """Validate with caching for repeated validations."""
        if cache_key and cache_key in self._validation_cache:
            self.validated_count += 1
            return self._validation_cache[cache_key]
        
        result = self.validate_item(model_class, data)
        
        if cache_key and result and len(self._validation_cache) < self._cache_size:
            self._validation_cache[cache_key] = result
        
        return result 