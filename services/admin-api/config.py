from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    PROJECT_ID: str
    REGION: str = "us-central1"
    API_URL: str = "http://localhost:8080" # Default for local development

    # Database settings (example for PostgreSQL)
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"

    # Firestore settings
    FIRESTORE_COLLECTION: str = "memory"

    # Gemini settings
    GEMINI_MODEL_ID: str = "gemini-2.5-pro-preview-05-06"
    GEMINI_LOCATION: str = "us-central1" # Vertex AI location

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()