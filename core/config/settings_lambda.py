# TODO: Consider adding connection pooling configuration
"""
"""
    """Application settings for Lambda deployment."""
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Lambda configuration
    LAMBDA_PROJECT_ID: str = Field(default="cherry_ai-ai", env="LAMBDA_PROJECT_ID")
    LAMBDA_REGION: str = Field(default="ewr", env="LAMBDA_REGION")  # New Jersey
    LAMBDA_API_KEY: Optional[str] = Field(default=None, env="LAMBDA_API_KEY")
    LAMBDA_CREDENTIALS_PATH: Optional[str] = Field(default=None, env="LAMBDA_CREDENTIALS_PATH")
    
    # Database configuration
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/cherry_ai",
        env="DATABASE_URL"
    )
    
    # Weaviate configuration
    weaviate_url: str = Field(default="http://localhost:8080", env="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    
    # Redis configuration (for Celery)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")  # Standard Redis config
    
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
    
    def get_LAMBDA_PROJECT_ID(self) -> Optional[str]:
        """Get Lambda project ID."""
        """Get Lambda credentials path."""
        """Get project ID (Lambda)."""
        """Get credentials path."""