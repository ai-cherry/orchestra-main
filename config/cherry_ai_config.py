#!/usr/bin/env python3
"""
Cherry AI Centralized Configuration Management System
Consolidates all configuration into a single, validated, environment-aware system
"""

import os
import json
import logging
import secrets
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from urllib.parse import urlparse

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cherry-ai-config")

@dataclass
class DatabaseConfig:
    """Database configuration with validation"""
    host: str = "localhost"
    port: int = 5432
    database: str = "cherry_ai"
    username: str = "postgres"
    password: str = "postgres"
    ssl_mode: str = "prefer"
    pool_size: int = 20
    min_pool_size: int = 5
    max_pool_size: int = 50
    statement_timeout: int = 30000
    query_timeout: int = 30
    
    def get_url(self, async_driver: bool = True) -> str:
        """Generate properly formatted database URL"""
        # asyncpg expects plain 'postgresql://' not 'postgresql+asyncpg://'
        driver = "postgresql"
        return f"{driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_psycopg_url(self) -> str:
        """Generate psycopg-compatible URL for synchronous operations"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class CacheConfig:
    """Multi-tier cache configuration"""
    # L1 Cache (In-Memory)
    l1_max_size: int = 1000
    l1_ttl_seconds: int = 300
    l1_enabled: bool = True
    
    # L2 Cache (Redis)
    redis_url: str = "redis://localhost:6379/0"
    l2_ttl_seconds: int = 3600
    redis_pool_size: int = 10
    l2_enabled: bool = True
    compression_enabled: bool = True
    compression_threshold: int = 1024
    
    # L3 Cache (PostgreSQL)
    l3_cleanup_interval: int = 86400
    l3_auto_cleanup: bool = True
    l3_max_table_size_mb: int = 1024
    l3_enabled: bool = True

@dataclass
class PersonaConfig:
    """Individual persona configuration"""
    name: str
    domain: str
    description: str
    personality_traits: Dict[str, float]
    skills: List[str]
    tools: List[str]
    voice_config: Dict[str, Any]
    learning_config: Dict[str, Any]
    
    def get_trait_value(self, trait_name: str, default: float = 0.5) -> float:
        """Get trait value with fallback to default"""
        return self.personality_traits.get(trait_name, default)

@dataclass
class SecurityConfig:
    """Security and authentication configuration"""
    secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    mfa_enabled: bool = False
    session_timeout_minutes: int = 120
    api_rate_limit_per_hour: int = 1000

@dataclass
class AIConfig:
    """AI model and conversation configuration"""
    default_model: str = "gpt-4"
    fallback_model: str = "gpt-3.5-turbo"
    max_tokens: int = 2048
    temperature: float = 0.7
    conversation_memory_limit: int = 50
    learning_rate: float = 0.05
    confidence_threshold: float = 0.7
    max_trait_adjustment: float = 0.2
    sentiment_analysis_enabled: bool = True
    mood_tracking_enabled: bool = True

@dataclass
class MonitoringConfig:
    """Monitoring and analytics configuration"""
    metrics_enabled: bool = True
    performance_logging: bool = True
    analytics_retention_days: int = 365
    health_check_interval_seconds: int = 60
    alert_email_enabled: bool = False
    alert_email_address: Optional[str] = None
    prometheus_enabled: bool = False
    prometheus_port: int = 8000

class CherryAIConfig:
    """
    Centralized configuration management for Cherry AI system
    
    Features:
    - Environment-aware configuration loading
    - Validation and type checking
    - Default value management
    - Database URL generation
    - Configuration hot-reloading
    """
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv("CHERRY_AI_ENV", "development")
        self.config_dir = Path(__file__).parent
        self.validate_environment()
        
        # Load configuration
        self.database = self._load_database_config()
        self.cache = self._load_cache_config()
        self.security = self._load_security_config()
        self.ai = self._load_ai_config()
        self.monitoring = self._load_monitoring_config()
        self.personas = self._load_personas_config()
        
        # Validate complete configuration
        self._validate_configuration()
        
        logger.info(f"Cherry AI configuration loaded for environment: {self.environment}")

    def validate_environment(self) -> None:
        """Validate that the environment is supported"""
        supported_envs = ["development", "testing", "staging", "production"]
        if self.environment not in supported_envs:
            raise ValueError(f"Unsupported environment: {self.environment}. Must be one of: {supported_envs}")

    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment and config files"""
        # Environment variable overrides
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            parsed = urlparse(db_url)
            return DatabaseConfig(
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/') if parsed.path else "cherry_ai",
                username=parsed.username or "postgres",
                password=parsed.password or "postgres",
                ssl_mode=os.getenv("DB_SSL_MODE", "prefer"),
                pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
                min_pool_size=int(os.getenv("DB_MIN_POOL_SIZE", "5")),
                max_pool_size=int(os.getenv("DB_MAX_POOL_SIZE", "50"))
            )
        
        # Default configuration based on environment
        config_defaults = {
            "development": DatabaseConfig(
                host="localhost",
                port=5432,
                database="cherry_ai_dev",
                username="postgres",
                password="postgres"
            ),
            "testing": DatabaseConfig(
                host="localhost",
                port=5432,
                database="cherry_ai_test",
                username="postgres",
                password="postgres"
            ),
            "staging": DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database="cherry_ai_staging",
                username=os.getenv("DB_USER", "cherry_ai_staging"),
                password=os.getenv("DB_PASSWORD", "staging_password")
            ),
            "production": DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database="cherry_ai_production",
                username=os.getenv("DB_USER", "cherry_ai_prod"),
                password=os.getenv("DB_PASSWORD", "production_password"),
                ssl_mode="require",
                pool_size=50,
                min_pool_size=10,
                max_pool_size=100
            )
        }
        
        return config_defaults[self.environment]

    def _load_cache_config(self) -> CacheConfig:
        """Load cache configuration"""
        return CacheConfig(
            # L1 Cache settings
            l1_max_size=int(os.getenv("CACHE_L1_MAX_SIZE", "1000")),
            l1_ttl_seconds=int(os.getenv("CACHE_L1_TTL", "300")),
            l1_enabled=os.getenv("CACHE_L1_ENABLED", "true").lower() == "true",
            
            # L2 Cache (Redis) settings
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            l2_ttl_seconds=int(os.getenv("CACHE_L2_TTL", "3600")),
            redis_pool_size=int(os.getenv("REDIS_POOL_SIZE", "10")),
            l2_enabled=os.getenv("CACHE_L2_ENABLED", "true").lower() == "true",
            
            # L3 Cache (PostgreSQL) settings
            l3_cleanup_interval=int(os.getenv("CACHE_L3_CLEANUP_INTERVAL", "86400")),
            l3_auto_cleanup=os.getenv("CACHE_L3_AUTO_CLEANUP", "true").lower() == "true",
            l3_enabled=os.getenv("CACHE_L3_ENABLED", "true").lower() == "true"
        )

    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        # Generate or load secret key
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            secret_key = secrets.token_urlsafe(32)
            logger.warning("No SECRET_KEY found in environment, generated temporary key")
        
        return SecurityConfig(
            secret_key=secret_key,
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
            mfa_enabled=os.getenv("MFA_ENABLED", "false").lower() == "true",
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "120")),
            api_rate_limit_per_hour=int(os.getenv("API_RATE_LIMIT_PER_HOUR", "1000"))
        )

    def _load_ai_config(self) -> AIConfig:
        """Load AI model configuration"""
        return AIConfig(
            default_model=os.getenv("AI_DEFAULT_MODEL", "gpt-4"),
            fallback_model=os.getenv("AI_FALLBACK_MODEL", "gpt-3.5-turbo"),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", "2048")),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.7")),
            conversation_memory_limit=int(os.getenv("AI_CONVERSATION_MEMORY_LIMIT", "50")),
            learning_rate=float(os.getenv("AI_LEARNING_RATE", "0.05")),
            confidence_threshold=float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.7")),
            max_trait_adjustment=float(os.getenv("AI_MAX_TRAIT_ADJUSTMENT", "0.2")),
            sentiment_analysis_enabled=os.getenv("AI_SENTIMENT_ANALYSIS", "true").lower() == "true",
            mood_tracking_enabled=os.getenv("AI_MOOD_TRACKING", "true").lower() == "true"
        )

    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring and analytics configuration"""
        return MonitoringConfig(
            metrics_enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            performance_logging=os.getenv("PERFORMANCE_LOGGING", "true").lower() == "true",
            analytics_retention_days=int(os.getenv("ANALYTICS_RETENTION_DAYS", "365")),
            health_check_interval_seconds=int(os.getenv("HEALTH_CHECK_INTERVAL", "60")),
            alert_email_enabled=os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true",
            alert_email_address=os.getenv("ALERT_EMAIL_ADDRESS"),
            prometheus_enabled=os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true",
            prometheus_port=int(os.getenv("PROMETHEUS_PORT", "8000"))
        )

    def _load_personas_config(self) -> Dict[str, PersonaConfig]:
        """Load persona configurations"""
        personas = {}
        
        # Cherry persona
        personas["cherry"] = PersonaConfig(
            name="Cherry",
            domain="Personal Life",
            description="Personal life coach, friend, and lifestyle manager with a playful and flirty personality",
            personality_traits={
                "playful": 0.9,
                "flirty": 0.8,
                "creative": 0.9,
                "smart": 0.95,
                "empathetic": 0.9,
                "supportive": 0.95,
                "warm": 0.95
            },
            skills=[
                "personal_development", "lifestyle_management", "relationship_advice",
                "health_wellness", "travel_planning", "emotional_support"
            ],
            tools=[
                "calendar", "fitness_tracker", "meal_planner", "travel_booking", "social_media"
            ],
            voice_config={
                "tone": "warm_playful",
                "speech_rate": "medium",
                "voice_model": "cherry_v2"
            },
            learning_config={
                "adaptation_rate": 0.05,
                "confidence_threshold": 0.7,
                "max_trait_adjustment": 0.2,
                "learning_focus": ["preferences", "emotional_patterns", "goals"]
            }
        )
        
        # Sophia persona
        personas["sophia"] = PersonaConfig(
            name="Sophia",
            domain="Pay Ready Business",
            description="Business strategist, client expert, and revenue advisor for apartment rental business",
            personality_traits={
                "strategic": 0.95,
                "professional": 0.9,
                "intelligent": 0.95,
                "confident": 0.9,
                "analytical": 0.9
            },
            skills=[
                "market_analysis", "client_management", "revenue_optimization",
                "business_strategy", "financial_planning", "competitive_analysis"
            ],
            tools=[
                "crm", "analytics_dashboard", "market_research", "financial_modeling", "client_portal"
            ],
            voice_config={
                "tone": "professional_confident",
                "speech_rate": "medium",
                "voice_model": "sophia_v2"
            },
            learning_config={
                "adaptation_rate": 0.03,
                "confidence_threshold": 0.8,
                "max_trait_adjustment": 0.15,
                "learning_focus": ["business_patterns", "client_preferences", "strategic_thinking"]
            }
        )
        
        # Karen persona
        personas["karen"] = PersonaConfig(
            name="Karen",
            domain="ParagonRX Healthcare",
            description="Healthcare expert, clinical trial specialist, and compliance advisor",
            personality_traits={
                "knowledgeable": 0.95,
                "trustworthy": 0.95,
                "patient_centered": 0.9,
                "detail_oriented": 0.95,
                "reliable": 0.95
            },
            skills=[
                "clinical_research", "regulatory_compliance", "patient_recruitment",
                "clinical_operations", "healthcare_analytics", "protocol_development"
            ],
            tools=[
                "clinical_trial_management", "regulatory_database", "patient_portal",
                "compliance_tracker", "analytics_suite"
            ],
            voice_config={
                "tone": "medical_professional",
                "speech_rate": "medium",
                "voice_model": "karen_v2"
            },
            learning_config={
                "adaptation_rate": 0.02,
                "confidence_threshold": 0.85,
                "max_trait_adjustment": 0.1,
                "learning_focus": ["compliance_patterns", "patient_needs", "regulatory_changes"]
            }
        )
        
        return personas

    def _validate_configuration(self) -> None:
        """Validate the complete configuration"""
        errors = []
        
        # Validate database configuration
        if not self.database.host:
            errors.append("Database host cannot be empty")
        if not (1 <= self.database.port <= 65535):
            errors.append("Database port must be between 1 and 65535")
        if not self.database.database:
            errors.append("Database name cannot be empty")
        
        # Validate cache configuration
        if self.cache.l1_max_size <= 0:
            errors.append("L1 cache max size must be positive")
        if self.cache.l1_ttl_seconds <= 0:
            errors.append("L1 cache TTL must be positive")
        
        # Validate security configuration
        if len(self.security.secret_key) < 32:
            errors.append("Secret key must be at least 32 characters")
        if self.security.password_min_length < 8:
            errors.append("Password minimum length should be at least 8 characters")
        
        # Validate AI configuration
        if not (0.0 <= self.ai.temperature <= 2.0):
            errors.append("AI temperature must be between 0.0 and 2.0")
        if not (0.0 <= self.ai.learning_rate <= 1.0):
            errors.append("AI learning rate must be between 0.0 and 1.0")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

    def get_database_url(self, async_driver: bool = True) -> str:
        """Get properly formatted database URL"""
        return self.database.get_url(async_driver)

    def get_persona_config(self, persona_type: str) -> PersonaConfig:
        """Get configuration for specific persona"""
        if persona_type not in self.personas:
            raise ValueError(f"Unknown persona type: {persona_type}")
        return self.personas[persona_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)"""
        config_dict = {
            "environment": self.environment,
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "ssl_mode": self.database.ssl_mode,
                "pool_size": self.database.pool_size
            },
            "cache": {
                "l1_enabled": self.cache.l1_enabled,
                "l2_enabled": self.cache.l2_enabled,
                "l3_enabled": self.cache.l3_enabled
            },
            "ai": {
                "default_model": self.ai.default_model,
                "max_tokens": self.ai.max_tokens,
                "temperature": self.ai.temperature,
                "learning_rate": self.ai.learning_rate
            },
            "personas": {
                name: {
                    "name": config.name,
                    "domain": config.domain,
                    "description": config.description
                }
                for name, config in self.personas.items()
            }
        }
        return config_dict

    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to file (excluding sensitive data)"""
        config_dict = self.to_dict()
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
        elif file_path.suffix.lower() in ['.yml', '.yaml']:
            with open(file_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        else:
            raise ValueError("File format must be .json, .yml, or .yaml")
        
        logger.info(f"Configuration saved to {file_path}")

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on configuration"""
        health = {
            "status": "healthy",
            "environment": self.environment,
            "database_reachable": False,
            "cache_reachable": False,
            "personas_loaded": len(self.personas),
            "errors": []
        }
        
        try:
            # Test database URL generation
            db_url = self.get_database_url()
            health["database_url_valid"] = bool(db_url)
        except Exception as e:
            health["errors"].append(f"Database URL generation failed: {e}")
            health["status"] = "unhealthy"
        
        try:
            # Validate personas
            for persona_name, persona_config in self.personas.items():
                if not persona_config.name:
                    health["errors"].append(f"Persona {persona_name} missing name")
        except Exception as e:
            health["errors"].append(f"Persona validation failed: {e}")
            health["status"] = "unhealthy"
        
        return health

# Global configuration instance
_config_instance: Optional[CherryAIConfig] = None

def get_config(environment: str = None, force_reload: bool = False) -> CherryAIConfig:
    """Get global configuration instance with lazy loading"""
    global _config_instance
    
    if _config_instance is None or force_reload:
        _config_instance = CherryAIConfig(environment)
    
    return _config_instance

def reload_config(environment: str = None) -> CherryAIConfig:
    """Force reload configuration"""
    return get_config(environment, force_reload=True)

# Example usage and testing
if __name__ == "__main__":
    # Test configuration loading
    config = CherryAIConfig("development")
    
    print("=== Cherry AI Configuration ===")
    print(f"Environment: {config.environment}")
    print(f"Database URL: {config.get_database_url()}")
    print(f"Personas loaded: {list(config.personas.keys())}")
    
    # Test health check
    health = config.health_check()
    print(f"Health check: {health['status']}")
    
    # Test persona access
    cherry_config = config.get_persona_config("cherry")
    print(f"Cherry playfulness: {cherry_config.get_trait_value('playful')}")
    
    # Save configuration (for reference)
    config.save_to_file("config/cherry_ai_config_example.json")
    
    print("Configuration test completed successfully!") 