# TODO: Consider adding connection pooling configuration
"""
"""
    """Application settings for Vultr deployment."""
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Vultr configuration
    vultr_project_id: str = Field(default="orchestra-ai", env="VULTR_PROJECT_ID")
    vultr_region: str = Field(default="ewr", env="VULTR_REGION")  # New Jersey
    vultr_api_key: Optional[str] = Field(default=None, env="VULTR_API_KEY")
    vultr_credentials_path: Optional[str] = Field(default=None, env="VULTR_CREDENTIALS_PATH")
    
    # Database configuration
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/orchestra",
        env="DATABASE_URL"
    )
    
    # Weaviate configuration
    weaviate_url: str = Field(default="http://localhost:8080", env="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    
    # Redis configuration (for Celery)
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Application configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra environment variables
    }
    
    def get_vultr_project_id(self) -> Optional[str]:
        """Get Vultr project ID."""
        """Get Vultr credentials path."""
        """Get project ID (Vultr)."""
        """Get credentials path."""