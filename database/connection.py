"""
Database Connection Management

Handles PostgreSQL connections, connection pooling, and database session management.
"""

import os
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import structlog

logger = structlog.get_logger(__name__)

# Base class for all SQLAlchemy models
Base = declarative_base()

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
        self.database_url = self._get_database_url()
        
    def _get_database_url(self) -> str:
        """Get database URL from environment or use default"""
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            return db_url
        
        # Use SQLite for development by default
        environment = os.getenv('ENVIRONMENT', 'development')
        
        if environment == 'development':
            # SQLite for development
            from pathlib import Path
            db_path = Path(__file__).parent.parent.parent / 'data' / 'orchestra_dev.db'
            db_path.parent.mkdir(exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path}"
        else:
            # PostgreSQL for staging/production
            host = os.getenv('POSTGRES_HOST', '45.77.87.106')
            port = os.getenv('POSTGRES_PORT', '5432')
            user = os.getenv('POSTGRES_USER', 'postgres')
            password = os.getenv('POSTGRES_PASSWORD', 'password')
            database = os.getenv('POSTGRES_DB', 'orchestra_ai')
            
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    
    async def initialize(self):
        """Initialize database engine and session factory"""
        try:
            # Different configuration for SQLite vs PostgreSQL
            if self.database_url.startswith('sqlite'):
                # SQLite configuration (no pooling)
                self.engine = create_async_engine(
                    self.database_url,
                    echo=False,  # Set to True for SQL logging in development
                )
            else:
                # PostgreSQL configuration (with pooling)
                self.engine = create_async_engine(
                    self.database_url,
                    echo=False,  # Set to True for SQL logging in development
                    pool_size=20,
                    max_overflow=30,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
            
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("Database initialized successfully", url=self.database_url)
            
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise
    
    async def create_tables(self):
        """Create all database tables"""
        try:
            # Import here to avoid circular imports
            from . import models
            async with self.engine.begin() as conn:
                await conn.run_sync(models.Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check database connection health"""
        try:
            async with self.async_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for database sessions"""
    async with db_manager.async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_database():
    """Initialize database for application startup"""
    await db_manager.initialize()
    await db_manager.create_tables()

async def close_database():
    """Close database for application shutdown"""
    await db_manager.close() 