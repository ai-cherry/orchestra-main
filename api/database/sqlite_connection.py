"""
SQLite Database Connection for Development
Simple alternative to PostgreSQL for local development
"""

import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

logger = structlog.get_logger(__name__)

class SQLiteDatabaseManager:
    def __init__(self):
        # Use SQLite database in the api directory
        api_dir = Path(__file__).parent.parent
        db_path = api_dir / "orchestra_ai.db"
        self.database_url = f"sqlite+aiosqlite:///{db_path}"
        self.engine = None
        self.session_factory = None
    
    async def initialize(self):
        """Initialize SQLite database"""
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                future=True
            )
            
            self.session_factory = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("SQLite database initialized", db_path=self.database_url)
            
        except Exception as e:
            logger.error("Failed to initialize SQLite database", error=str(e))
            raise
    
    async def create_tables(self):
        """Create all database tables"""
        try:
            # Import here to avoid circular imports
            from . import models
            async with self.engine.begin() as conn:
                await conn.run_sync(models.Base.metadata.create_all)
            logger.info("SQLite database tables created successfully")
        except Exception as e:
            logger.error("Failed to create SQLite database tables", error=str(e))
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        return self.session_factory()
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()

# Global instance for development
sqlite_db_manager = SQLiteDatabaseManager()

async def init_sqlite_database():
    """Initialize SQLite database for development"""
    await sqlite_db_manager.initialize()
    await sqlite_db_manager.create_tables()

async def get_sqlite_db():
    """Get SQLite database session"""
    async with sqlite_db_manager.get_session() as session:
        yield session 