"""
Database connection and session management for Orchestra AI
"""
import os
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
import structlog

logger = structlog.get_logger()

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/orchestra_ai"
)

# SQLite fallback for development
if DATABASE_URL.startswith("sqlite"):
    # Convert sqlite:// to sqlite+aiosqlite://
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

# Create base class for models
Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection"""
        if self._initialized:
            return
            
        try:
            # Create engine with appropriate settings
            if DATABASE_URL.startswith("sqlite"):
                # SQLite specific settings
                self.engine = create_async_engine(
                    DATABASE_URL,
                    echo=False,
                    connect_args={"check_same_thread": False}
                )
            else:
                # PostgreSQL settings
                self.engine = create_async_engine(
                    DATABASE_URL,
                    echo=False,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=300
                )
            
            # Create session factory
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("Database connection initialized", url=DATABASE_URL.split("@")[-1])
            
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise
    
    async def create_tables(self):
        """Create all tables"""
        if not self.engine:
            await self.initialize()
            
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connection closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session"""
        if not self._initialized:
            await self.initialize()
            
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with db_manager.get_session() as session:
        yield session


# Lifecycle functions
async def init_database():
    """Initialize database on startup"""
    await db_manager.initialize()
    await db_manager.create_tables()


async def close_database():
    """Close database on shutdown"""
    await db_manager.close() 