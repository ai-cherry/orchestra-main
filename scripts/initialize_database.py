#!/usr/bin/env python3
"""
Cherry AI Database Initialization Script
Uses unified schema and centralized configuration to set up the database properly
"""

import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional

import asyncpg
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path to import config
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from config.cherry_ai_config import get_config, CherryAIConfig
except ImportError:
    print("Warning: Could not import cherry_ai_config, using fallback configuration")
    CherryAIConfig = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cherry-ai-db-init")

class DatabaseInitializer:
    """
    Comprehensive database initialization for Cherry AI system
    
    Features:
    - Database creation if not exists
    - Schema validation and creation
    - Default data population
    - Health checks and validation
    - Rollback capabilities
    """
    
    def __init__(self, config: Optional['CherryAIConfig'] = None):
        self.config = config or self._load_fallback_config()
        self.schema_file = parent_dir / "database" / "unified_schema.sql"
        self.connection_pool: Optional[asyncpg.Pool] = None
        
        logger.info(f"Database initializer configured for environment: {self.config.environment}")

    def _load_fallback_config(self):
        """Load fallback configuration if main config not available"""
        class FallbackConfig:
            def __init__(self):
                self.environment = os.getenv("CHERRY_AI_ENV", "development")
                
            def get_database_url(self, async_driver=True):
                db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cherry_ai")
                if async_driver and not db_url.startswith("postgresql+asyncpg"):
                    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
                return db_url
                
            def get_psycopg_url(self):
                db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/cherry_ai")
                return db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        return FallbackConfig()

    async def initialize_database(self, create_if_not_exists: bool = True) -> bool:
        """
        Complete database initialization process
        
        Args:
            create_if_not_exists: Whether to create database if it doesn't exist
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("🚀 Starting Cherry AI database initialization...")
            
            # Step 1: Create database if needed
            if create_if_not_exists:
                await self._create_database_if_not_exists()
            
            # Step 2: Test connection
            if not await self._test_connection():
                logger.error("❌ Database connection test failed")
                return False
            
            # Step 3: Load and execute schema
            if not await self._execute_schema():
                logger.error("❌ Schema execution failed")
                return False
            
            # Step 4: Validate schema
            if not await self._validate_schema():
                logger.error("❌ Schema validation failed")
                return False
            
            # Step 5: Run health check
            health_result = await self._health_check()
            if not health_result["healthy"]:
                logger.error(f"❌ Health check failed: {health_result['errors']}")
                return False
            
            logger.info("✅ Cherry AI database initialization completed successfully!")
            logger.info(f"📊 Database statistics: {health_result['statistics']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
        finally:
            await self._cleanup()

    async def _create_database_if_not_exists(self) -> bool:
        """Create database if it doesn't exist using synchronous connection"""
        try:
            # Parse database URL to get connection info
            if hasattr(self.config, 'database'):
                host = self.config.database.host
                port = self.config.database.port
                database = self.config.database.database
                username = self.config.database.username
                password = self.config.database.password
            else:
                # Fallback parsing
                db_url = self.config.get_psycopg_url()
                from urllib.parse import urlparse
                parsed = urlparse(db_url)
                host = parsed.hostname or "localhost"
                port = parsed.port or 5432
                database = parsed.path.lstrip('/') if parsed.path else "cherry_ai"
                username = parsed.username or "postgres"
                password = parsed.password or "postgres"
            
            # Connect to postgres database (not target database)
            conn = psycopg2.connect(
                host=host,
                port=port,
                database="postgres",
                user=username,
                password=password
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (database,)
            )
            exists = cursor.fetchone()
            
            if not exists:
                logger.info(f"📦 Creating database: {database}")
                cursor.execute(f'CREATE DATABASE "{database}"')
                logger.info(f"✅ Database {database} created successfully")
            else:
                logger.info(f"✅ Database {database} already exists")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            return False

    async def _test_connection(self) -> bool:
        """Test database connection"""
        try:
            db_url = self.config.get_database_url(async_driver=True)
            
            # Create connection pool
            self.connection_pool = await asyncpg.create_pool(
                db_url,
                min_size=1,
                max_size=5,
                timeout=30
            )
            
            # Test connection
            async with self.connection_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    logger.info("✅ Database connection test successful")
                    return True
                else:
                    logger.error("❌ Database connection test returned unexpected result")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False

    async def _execute_schema(self) -> bool:
        """Load and execute the unified schema"""
        try:
            if not self.schema_file.exists():
                logger.error(f"❌ Schema file not found: {self.schema_file}")
                return False
            
            logger.info(f"📋 Loading schema from: {self.schema_file}")
            schema_sql = self.schema_file.read_text()
            
            # Execute schema
            async with self.connection_pool.acquire() as conn:
                # Split on semicolons and execute each statement
                statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                
                total_statements = len(statements)
                logger.info(f"🔄 Executing {total_statements} schema statements...")
                
                for i, statement in enumerate(statements, 1):
                    try:
                        await conn.execute(statement)
                        if i % 10 == 0 or i == total_statements:
                            logger.info(f"✅ Executed {i}/{total_statements} statements")
                    except Exception as e:
                        logger.warning(f"⚠️  Statement {i} failed (may be expected): {e}")
                        continue
                
                logger.info("✅ Schema execution completed")
                return True
                
        except Exception as e:
            logger.error(f"❌ Schema execution failed: {e}")
            return False

    async def _validate_schema(self) -> bool:
        """Validate that all required schemas and tables exist"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Check schemas
                required_schemas = ['shared', 'cherry', 'sophia', 'karen', 'cache']
                existing_schemas = await conn.fetch(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = ANY($1)",
                    required_schemas
                )
                existing_schema_names = [row['schema_name'] for row in existing_schemas]
                
                missing_schemas = set(required_schemas) - set(existing_schema_names)
                if missing_schemas:
                    logger.error(f"❌ Missing schemas: {missing_schemas}")
                    return False
                
                logger.info(f"✅ All required schemas exist: {existing_schema_names}")
                
                # Check core tables in shared schema
                required_tables = [
                    'users', 'ai_personas', 'conversations', 'relationship_development',
                    'learning_patterns', 'personality_adaptations', 'user_sessions', 'audit_logs'
                ]
                
                existing_tables = await conn.fetch(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'shared' AND table_name = ANY($1)
                    """,
                    required_tables
                )
                existing_table_names = [row['table_name'] for row in existing_tables]
                
                missing_tables = set(required_tables) - set(existing_table_names)
                if missing_tables:
                    logger.error(f"❌ Missing tables in shared schema: {missing_tables}")
                    return False
                
                logger.info(f"✅ All required tables exist: {existing_table_names}")
                
                # Check that default personas are inserted
                persona_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM shared.ai_personas"
                )
                
                if persona_count < 3:
                    logger.error(f"❌ Expected 3 personas, found {persona_count}")
                    return False
                
                logger.info(f"✅ Found {persona_count} personas in database")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Schema validation failed: {e}")
            return False

    async def _health_check(self) -> dict:
        """Comprehensive health check of the database"""
        health = {
            "healthy": True,
            "errors": [],
            "statistics": {}
        }
        
        try:
            async with self.connection_pool.acquire() as conn:
                # Check database connection
                await conn.fetchval("SELECT 1")
                
                # Get table counts
                table_counts = await conn.fetch("""
                    SELECT schemaname, tablename, 
                           (xpath('/row/cnt/text()', xml_count))[1]::text::int as row_count
                    FROM (
                        SELECT schemaname, tablename, 
                               query_to_xml(format('select count(*) as cnt from %I.%I', 
                                                   schemaname, tablename), false, true, '') as xml_count
                        FROM pg_tables 
                        WHERE schemaname IN ('shared', 'cache')
                    ) t
                """)
                
                statistics = {}
                for row in table_counts:
                    schema_table = f"{row['schemaname']}.{row['tablename']}"
                    statistics[schema_table] = row['row_count']
                
                health["statistics"] = statistics
                
                # Check personas specifically
                personas = await conn.fetch("SELECT persona_type, name FROM shared.ai_personas")
                health["personas"] = [dict(persona) for persona in personas]
                
                # Check indexes
                index_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM pg_indexes 
                    WHERE schemaname IN ('shared', 'cache')
                """)
                health["statistics"]["total_indexes"] = index_count
                
                logger.info("✅ Health check completed successfully")
                
        except Exception as e:
            health["healthy"] = False
            health["errors"].append(str(e))
            logger.error(f"❌ Health check failed: {e}")
        
        return health

    async def _cleanup(self):
        """Clean up connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("🧹 Connection pool cleaned up")

    async def reset_database(self) -> bool:
        """Reset database by dropping and recreating all schemas"""
        try:
            logger.warning("🔄 Resetting database - this will delete all data!")
            
            async with self.connection_pool.acquire() as conn:
                # Drop schemas in reverse dependency order
                schemas_to_drop = ['cache', 'analytics', 'karen', 'sophia', 'cherry', 'shared']
                
                for schema in schemas_to_drop:
                    try:
                        await conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
                        logger.info(f"🗑️  Dropped schema: {schema}")
                    except Exception as e:
                        logger.warning(f"⚠️  Could not drop schema {schema}: {e}")
                
                logger.info("✅ Database reset completed")
                return True
                
        except Exception as e:
            logger.error(f"❌ Database reset failed: {e}")
            return False

# CLI interface
async def main():
    """Main CLI interface for database initialization"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cherry AI Database Initialization")
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset database (drops all schemas)"
    )
    parser.add_argument(
        "--env", 
        default="development",
        help="Environment (development, testing, staging, production)"
    )
    parser.add_argument(
        "--no-create", 
        action="store_true",
        help="Don't create database if it doesn't exist"
    )
    parser.add_argument(
        "--test-only", 
        action="store_true",
        help="Only test connection, don't initialize"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if CherryAIConfig:
        config = get_config(args.env)
    else:
        config = None
    
    # Initialize database manager
    db_init = DatabaseInitializer(config)
    
    try:
        if args.test_only:
            # Test connection only
            logger.info("🔍 Testing database connection...")
            success = await db_init._test_connection()
            if success:
                logger.info("✅ Database connection test successful")
                sys.exit(0)
            else:
                logger.error("❌ Database connection test failed")
                sys.exit(1)
        
        elif args.reset:
            # Reset database
            logger.warning("⚠️  This will delete all data in the database!")
            response = input("Are you sure you want to reset the database? (yes/no): ")
            if response.lower() == "yes":
                await db_init._test_connection()
                success = await db_init.reset_database()
                if success:
                    logger.info("✅ Database reset successful")
                    # Now initialize fresh
                    success = await db_init.initialize_database(not args.no_create)
                    sys.exit(0 if success else 1)
                else:
                    logger.error("❌ Database reset failed")
                    sys.exit(1)
            else:
                logger.info("Database reset cancelled")
                sys.exit(0)
        
        else:
            # Normal initialization
            success = await db_init.initialize_database(not args.no_create)
            if success:
                logger.info("🎉 Database initialization completed successfully!")
                sys.exit(0)
            else:
                logger.error("💥 Database initialization failed!")
                sys.exit(1)
                
    except KeyboardInterrupt:
        logger.info("❌ Database initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 