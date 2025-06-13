"""
Orchestra AI Admin API - Phase 2 Configuration Example

Copy this file to config.py and update with your specific values.
"""

import os
from typing import Dict, Any

# Database Configuration
DATABASE_CONFIG = {
    "url": os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/orchestra_ai"),
    "echo": os.getenv("DB_ECHO", "false").lower() == "true",
    "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

# Vector Store Configuration
VECTOR_STORE_CONFIG = {
    "type": os.getenv("VECTOR_STORE_TYPE", "faiss"),  # Options: faiss, weaviate
    "weaviate_url": os.getenv("WEAVIATE_URL", "http://localhost:8080"),
    "weaviate_api_key": os.getenv("WEAVIATE_API_KEY", ""),
    "faiss_storage_path": os.getenv("FAISS_STORAGE_PATH", "./data/faiss"),
}

# File Storage Configuration
FILE_STORAGE_CONFIG = {
    "upload_dir": os.getenv("UPLOAD_DIR", "./uploads"),
    "max_file_size": int(os.getenv("MAX_FILE_SIZE", "2147483648")),  # 2GB
    "chunk_size": int(os.getenv("CHUNK_SIZE", "8388608")),  # 8MB
    "allowed_extensions": [
        # Documents
        ".pdf", ".docx", ".doc", ".txt", ".md", ".rtf",
        # Spreadsheets
        ".xlsx", ".xls", ".csv",
        # Presentations
        ".pptx", ".ppt",
        # Images
        ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp",
        # Videos
        ".mp4", ".mov", ".avi", ".mkv", ".wmv",
        # Audio
        ".mp3", ".wav", ".flac", ".aac",
        # Code
        ".js", ".ts", ".jsx", ".tsx", ".py", ".java", ".cpp", ".c", 
        ".html", ".css", ".json", ".xml", ".yaml", ".yml",
        # Archives
        ".zip", ".rar", ".7z", ".tar", ".gz"
    ]
}

# AI Model Configuration
AI_MODEL_CONFIG = {
    "embedding_model": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "default_model": "gpt-3.5-turbo",
    "max_tokens": 4000,
    "temperature": 0.7,
}

# External Service Integration
EXTERNAL_SERVICES = {
    "notion": {
        "api_key": os.getenv("NOTION_API_KEY", ""),
        "version": "2022-06-28",
    },
    "openrouter": {
        "api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "base_url": "https://openrouter.ai/api/v1",
    },
    "portkey": {
        "api_key": os.getenv("PORTKEY_API_KEY", ""),
        "base_url": "https://api.portkey.ai/v1",
    }
}

# Security Configuration
SECURITY_CONFIG = {
    "jwt_secret": os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production"),
    "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
    "jwt_expire_minutes": int(os.getenv("JWT_EXPIRE_MINUTES", "1440")),
    "bcrypt_rounds": 12,
}

# Redis Configuration (for caching and sessions)
REDIS_CONFIG = {
    "url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "password": os.getenv("REDIS_PASSWORD", ""),
    "decode_responses": True,
    "max_connections": 20,
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": os.getenv("LOG_FORMAT", "json"),
    "handlers": ["console", "file"],
    "file_path": "./logs/orchestra-ai.log",
}

# Development Settings
DEVELOPMENT_CONFIG = {
    "debug": os.getenv("DEBUG", "false").lower() == "true",
    "reload": os.getenv("RELOAD", "false").lower() == "true",
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", "8000")),
}

# CORS Configuration
CORS_CONFIG = {
    "allow_origins": os.getenv("CORS_ORIGINS", "*").split(","),
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

# Production Settings
PRODUCTION_CONFIG = {
    "workers": int(os.getenv("WORKERS", "4")),
    "worker_class": "uvicorn.workers.UvicornWorker",
    "bind": os.getenv("BIND", "0.0.0.0:8000"),
    "max_requests": int(os.getenv("MAX_REQUESTS", "1000")),
    "max_requests_jitter": int(os.getenv("MAX_REQUESTS_JITTER", "100")),
}

# Cloud Storage Configuration (for production)
CLOUD_STORAGE_CONFIG = {
    "provider": os.getenv("CLOUD_STORAGE_PROVIDER", "aws"),  # aws, gcp, azure
    "aws": {
        "access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        "region": os.getenv("AWS_REGION", "us-west-2"),
        "bucket": os.getenv("S3_BUCKET", "orchestra-ai-files"),
    },
    "gcp": {
        "project_id": os.getenv("GCP_PROJECT_ID", ""),
        "credentials_path": os.getenv("GCP_CREDENTIALS_PATH", ""),
        "bucket": os.getenv("GCS_BUCKET", "orchestra-ai-files"),
    }
}

# Monitoring and Analytics
MONITORING_CONFIG = {
    "prometheus_enabled": os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true",
    "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "9090")),
    "metrics_path": "/metrics",
    "health_check_interval": 30,  # seconds
}

# Rate Limiting Configuration
RATE_LIMIT_CONFIG = {
    "enabled": os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
    "requests": int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
    "window": int(os.getenv("RATE_LIMIT_WINDOW", "60")),  # seconds
    "storage": "redis",  # redis, memory
}

# WebSocket Configuration
WEBSOCKET_CONFIG = {
    "max_connections": int(os.getenv("WS_MAX_CONNECTIONS", "100")),
    "heartbeat_interval": int(os.getenv("WS_HEARTBEAT_INTERVAL", "30")),
    "message_size_limit": int(os.getenv("WS_MESSAGE_SIZE_LIMIT", "65536")),  # 64KB
}

# Search Configuration
SEARCH_CONFIG = {
    "max_results": 50,
    "timeout_seconds": 30,
    "cache_ttl": 300,  # 5 minutes
    "modes": {
        "basic": {"max_tokens": 1000, "model": "gpt-3.5-turbo"},
        "deep": {"max_tokens": 2000, "model": "gpt-4"},
        "super_deep": {"max_tokens": 4000, "model": "gpt-4"},
        "creative": {"max_tokens": 2000, "model": "gpt-4", "temperature": 0.9},
        "private": {"max_tokens": 1000, "model": "gpt-3.5-turbo", "secure": True},
        "uncensored": {"max_tokens": 2000, "model": "gpt-4", "filters": False},
    }
}

# Persona Configuration
PERSONA_CONFIG = {
    "cherry": {
        "name": "Cherry (Creative AI)",
        "description": "Creative AI specializing in design, content creation, and artistic tasks",
        "default_model": "gpt-4",
        "temperature": 0.8,
        "max_tokens": 2000,
        "knowledge_domains": ["design", "content", "branding", "marketing"],
    },
    "sophia": {
        "name": "Sophia (Strategic AI)",
        "description": "Strategic AI focused on business analysis and decision-making",
        "default_model": "gpt-4",
        "temperature": 0.3,
        "max_tokens": 3000,
        "knowledge_domains": ["strategy", "business", "analysis", "planning"],
    },
    "karen": {
        "name": "Karen (Operational AI)",
        "description": "Operational AI optimizing processes and workflows",
        "default_model": "gpt-3.5-turbo",
        "temperature": 0.2,
        "max_tokens": 2000,
        "knowledge_domains": ["operations", "processes", "optimization", "efficiency"],
    }
}

# Feature Flags
FEATURE_FLAGS = {
    "vector_search": True,
    "file_processing": True,
    "persona_management": True,
    "real_time_notifications": True,
    "external_integrations": True,
    "advanced_search": True,
    "analytics": True,
    "rate_limiting": True,
}

# Application Configuration (combines all configs)
APP_CONFIG = {
    "database": DATABASE_CONFIG,
    "vector_store": VECTOR_STORE_CONFIG,
    "file_storage": FILE_STORAGE_CONFIG,
    "ai_models": AI_MODEL_CONFIG,
    "external_services": EXTERNAL_SERVICES,
    "security": SECURITY_CONFIG,
    "redis": REDIS_CONFIG,
    "logging": LOGGING_CONFIG,
    "development": DEVELOPMENT_CONFIG,
    "cors": CORS_CONFIG,
    "production": PRODUCTION_CONFIG,
    "cloud_storage": CLOUD_STORAGE_CONFIG,
    "monitoring": MONITORING_CONFIG,
    "rate_limiting": RATE_LIMIT_CONFIG,
    "websocket": WEBSOCKET_CONFIG,
    "search": SEARCH_CONFIG,
    "personas": PERSONA_CONFIG,
    "features": FEATURE_FLAGS,
}

def get_config() -> Dict[str, Any]:
    """Get complete application configuration"""
    return APP_CONFIG

def get_database_config() -> Dict[str, Any]:
    """Get database configuration"""
    return DATABASE_CONFIG

def get_vector_store_config() -> Dict[str, Any]:
    """Get vector store configuration"""
    return VECTOR_STORE_CONFIG

def is_development() -> bool:
    """Check if running in development mode"""
    return DEVELOPMENT_CONFIG["debug"]

def is_production() -> bool:
    """Check if running in production mode"""
    return not is_development() 