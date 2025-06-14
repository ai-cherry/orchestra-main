"""
Updated Database Connection with Secure Secret Management
"""

import os
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import structlog

# Import secure secret management
from security.secret_manager import secret_manager

logger = structlog.get_logger(__name__)

# Base class for all SQLAlchemy models
Base = declarative_base()

class DatabaseManager:
    """Manages database connections with secure secret handling"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
        self.database_url = self._get_secure_database_url()
        
    def _get_secure_database_url(self) -> str:
        """Get database URL using secure secret management"""
        
        # Try to get full DATABASE_URL first
        db_url = secret_manager.get_secret('DATABASE_URL')
        if db_url:
            return db_url
        
        # Build URL from individual components
        environment = secret_manager.get_secret('ENVIRONMENT', 'production')
        
        if environment == 'development':
            # SQLite for development
            from pathlib import Path
            db_path = Path(__file__).parent.parent.parent / 'data' / 'orchestra_dev.db'
            db_path.parent.mkdir(exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path}"
        else:
            # PostgreSQL for staging/production with secure credentials
            host = secret_manager.get_secret('POSTGRES_HOST', 'postgres')
            port = secret_manager.get_secret('POSTGRES_PORT', '5432')
            user = secret_manager.get_secret('POSTGRES_USER', 'orchestra')
            password = secret_manager.get_secret('POSTGRES_PASSWORD')
            database = secret_manager.get_secret('POSTGRES_DB', 'orchestra_ai')
            
            if not password:
                logger.error("PostgreSQL password not found in secure storage")
                raise ValueError("Database password required for production environment")
            
            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    
    async def initialize(self):
        """Initialize database engine and session factory"""
        try:
            # Validate database URL is secure
            if 'password' in self.database_url.lower() and 'password' in self.database_url:
                logger.warning("Database URL may contain hardcoded password")
            
            # Different configuration for SQLite vs PostgreSQL
            if self.database_url.startswith('sqlite'):
                # SQLite configuration (no pooling)
                self.engine = create_async_engine(
                    self.database_url,
                    echo=False,  # Never log SQL in production
                )
            else:
                # PostgreSQL configuration (with pooling)
                self.engine = create_async_engine(
                    self.database_url,
                    echo=False,  # Never log SQL in production
                    pool_size=20,
                    max_overflow=30,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    # Security: Hide connection string in logs
                    hide_parameters=True
                )
            
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("Database initialized successfully", 
                       environment=secret_manager.get_secret('ENVIRONMENT', 'production'))
            
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

