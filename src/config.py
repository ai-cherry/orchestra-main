import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

class Config:
    """Application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "Orchestra_AI_Unified_2025_Secure_Key")

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'app.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
