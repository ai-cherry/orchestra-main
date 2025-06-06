"""
Database Schema Manager
Handles all database schema operations following SOLID principles
"""

import asyncio
import asyncpg
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class SchemaManager:
    """Manages database schema migrations"""
    
    def __init__(self, db_pool: asyncpg.Pool, migrations_dir: str = "migrations"):
        self.db_pool = db_pool
        self.migrations_dir = Path(migrations_dir)
    
    async def initialize(self):
        """Initialize schema management tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    async def get_current_version(self) -> int:
        """Get current schema version"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
            )
            return result or 0
    
    async def apply_migrations(self):
        """Apply pending migrations"""
        current_version = await self.get_current_version()
        migrations = self._get_pending_migrations(current_version)
        
        for migration in migrations:
            await self._apply_migration(migration)
    
    def _get_pending_migrations(self, current_version: int) -> List[Path]:
        """Get list of pending migration files"""
        migrations = []
        for file in sorted(self.migrations_dir.glob("*.sql")):
            # Extract version from filename (e.g., 001_initial_schema.sql)
            version = int(file.stem.split("_")[0])
            if version > current_version:
                migrations.append(file)
        return migrations
    
    async def _apply_migration(self, migration_file: Path):
        """Apply a single migration"""
        version = int(migration_file.stem.split("_")[0])
        name = migration_file.stem
        
        logger.info(f"Applying migration {name}...")
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Execute migration
                sql = migration_file.read_text()
                await conn.execute(sql)
                
                # Record migration
                await conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES ($1, $2)",
                    version, name
                )
        
        logger.info(f"Migration {name} applied successfully")
