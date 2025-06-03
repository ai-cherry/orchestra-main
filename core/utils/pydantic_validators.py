"""
"""
    """Base model with strict validation and helpful error messages."""
            "example": {}
        }
    )


# Custom validators for common patterns
def validate_email(email: str) -> str:
    """Validate email format."""
        raise ValueError(f"Invalid email format: {email}")
    return email.lower()


def validate_url(url: str) -> str:
    """Validate URL format."""
        raise ValueError(f"Invalid URL format: {url}")
    return url


def validate_api_key(api_key: str) -> str:
    """Validate API key format (alphanumeric, 32-64 chars)."""
        raise ValueError("API key must be 32-64 alphanumeric characters")
    return api_key


def validate_persona_slug(slug: str) -> str:
    """Validate persona slug format."""
        raise ValueError("Persona slug must contain only lowercase letters, numbers, and hyphens")
    return slug


def validate_temperature(temp: float) -> float:
    """Validate LLM temperature parameter."""
        raise ValueError("Temperature must be between 0.0 and 2.0")
    return temp


def validate_max_tokens(tokens: int) -> int:
    """Validate max tokens parameter."""
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
    """
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
        revalidate_instances="never"  # Don't revalidate instances
    )
    
    @classmethod
    def construct_fast(cls, **data):
        """
        """
    """Context manager for efficient batch validation."""
        """Validate a single item, collecting errors."""
        """Get validation summary."""
            "validated": self.validated_count,
            "errors": len(self.errors),
            "error_details": self.errors[:10]  # First 10 errors
        }


# Performance-optimized validation with computed fields
class EnhancedPersonaConfig(StrictBaseModel):
    """Enhanced persona configuration with computed fields for performance."""
        """Computed field for UI display - no DB query needed."""
        """Performance scoring for LLM routing decisions."""
    @field_validator("capabilities")
    def validate_capabilities(cls, v: List[str]) -> List[str]:
        """Ensure capabilities are valid and normalized."""
                raise ValueError(f"Invalid capability: {cap}")
        return list(set(v))  # Remove duplicates


# Cross-field validation for LLM routing
class LLMRoutingConfig(StrictBaseModel):
    """LLM routing configuration with business rule validation."""
        """Ensure routing configuration is logically consistent."""
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
        """Format cost for frontend display."""
        return f"${value:.4f}"
    
    @computed_field
    @property
    def performance_grade(self) -> str:
        """Performance grade based on response time."""
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
        """Validate with caching for repeated validations."""