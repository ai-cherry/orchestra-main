import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Attempt to import from the central config, falling back to os.getenv for standalone use/testing
try:
    from agent.app.core import config as app_config
    DATABASE_URL = app_config.DATABASE_URL # This should be the primary source
    if not DATABASE_URL.startswith("postgresql+psycopg://"):
        # If the main DATABASE_URL isn't in psycopg format, construct it
        DATABASE_URL = f"postgresql+psycopg://{app_config.POSTGRES_USER}:{app_config.POSTGRES_PASSWORD}@{app_config.POSTGRES_HOST}:{app_config.POSTGRES_PORT}/{app_config.POSTGRES_DB}"
except ImportError:
    # Fallback if agent.app.core.config is not available (e.g. running script standalone)
    PG_USER = os.getenv("POSTGRES_USER", "orchestrator")
    PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "orch3str4_2024")
    PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
    PG_PORT = os.getenv("POSTGRES_PORT", "5432")
    PG_DB = os.getenv("POSTGRES_DB", "orchestrator")
    DATABASE_URL = f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    # Final fallback if individual vars also not set, using a placeholder that will likely fail but shows intent
    if PG_USER == "orchestrator" and PG_HOST == "localhost" and os.getenv("DATABASE_URL") is None:
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://user:pass@host:5432/db") # Ensure port is numeric here

print(f"[shared.database.core] Using DATABASE_URL: {DATABASE_URL}") # For debugging startup

async_engine = create_async_engine(DATABASE_URL, echo=False) # Set echo=True for SQL logging
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to provide an SQLAlchemy AsyncSession."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit() # Commit if no exceptions
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close() 