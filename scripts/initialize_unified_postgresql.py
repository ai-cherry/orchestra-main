#!/usr/bin/env python3
"""
Initialize the unified PostgreSQL system with all required schemas,
indexes, and configurations for optimal performance.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.database.connection_manager_enhanced import (
    get_connection_manager_enhanced as get_connection_manager,
    close_connection_manager,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class UnifiedPostgreSQLInitializer:
    """Handles initialization of the unified PostgreSQL system."""

    def __init__(self):
        self.manager = None
        self.schemas_created = []
        self.indexes_created = []
        self.functions_created = []

    async def initialize(self):
        """Initialize database connection."""
        logger.info("Connecting to PostgreSQL...")
        self.manager = await get_connection_manager()
        logger.info("Connected successfully")

    async def create_schemas(self):
        """Create all required schemas."""
        schemas = [
            ("orchestra", "Main application schema for agents, workflows, and audit logs"),
            ("cache", "High-performance caching schema"),
            ("sessions", "User and agent session management"),
        ]

        for schema_name, comment in schemas:
            try:
                await self.manager.execute(
                    f"""
                    CREATE SCHEMA IF NOT EXISTS {schema_name};
                    COMMENT ON SCHEMA {schema_name} IS '{comment}';
                """
                )
                self.schemas_created.append(schema_name)
                logger.info(f"Created schema: {schema_name}")
            except Exception as e:
                logger.error(f"Failed to create schema {schema_name}: {e}")
                raise

    async def create_tables(self):
        """Create all required tables with optimal structure."""

        # Cache entries table
        await self.manager.execute(
            """
            CREATE TABLE IF NOT EXISTS cache.entries (
                key VARCHAR(255) PRIMARY KEY,
                value JSONB NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1,
                tags TEXT[] DEFAULT '{}',
                metadata JSONB DEFAULT '{}'
            );
            
            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache.entries(expires_at);
            CREATE INDEX IF NOT EXISTS idx_cache_tags ON cache.entries USING GIN(tags);
            CREATE INDEX IF NOT EXISTS idx_cache_accessed_at ON cache.entries(accessed_at);
            
            -- Comments
            COMMENT ON TABLE cache.entries IS 'High-performance cache storage with TTL and tagging';
            COMMENT ON COLUMN cache.entries.key IS 'Unique cache key';
            COMMENT ON COLUMN cache.entries.value IS 'Cached value in JSONB format';
            COMMENT ON COLUMN cache.entries.expires_at IS 'Expiration timestamp for TTL';
            COMMENT ON COLUMN cache.entries.tags IS 'Tags for grouping and bulk operations';
        """
        )
        logger.info("Created cache.entries table")

        # Sessions table
        await self.manager.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions.sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(255),
                agent_id VARCHAR(255),
                data JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1,
                metadata JSONB DEFAULT '{}'
            );
            
            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions.sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_agent_id ON sessions.sessions(agent_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions.sessions(expires_at);
            CREATE INDEX IF NOT EXISTS idx_sessions_user_agent ON sessions.sessions(user_id, agent_id);
            
            -- Comments
            COMMENT ON TABLE sessions.sessions IS 'User and agent session storage';
            COMMENT ON COLUMN sessions.sessions.id IS 'Unique session identifier';
            COMMENT ON COLUMN sessions.sessions.data IS 'Session data in JSONB format';
        """
        )
        logger.info("Created sessions.sessions table")

        # Agents table
        await self.manager.execute(
            """
            CREATE TABLE IF NOT EXISTS orchestra.agents (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100) NOT NULL,
                config JSONB NOT NULL DEFAULT '{}',
                capabilities TEXT[] DEFAULT '{}',
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}',
                version INTEGER DEFAULT 1
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_agents_type ON orchestra.agents(type);
            CREATE INDEX IF NOT EXISTS idx_agents_status ON orchestra.agents(status);
            CREATE INDEX IF NOT EXISTS idx_agents_capabilities ON orchestra.agents USING GIN(capabilities);
            CREATE INDEX IF NOT EXISTS idx_agents_name ON orchestra.agents(name);
            
            -- Comments
            COMMENT ON TABLE orchestra.agents IS 'AI agent configurations and metadata';
        """
        )
        logger.info("Created orchestra.agents table")

        # Workflows table
        await self.manager.execute(
            """
            CREATE TABLE IF NOT EXISTS orchestra.workflows (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                definition JSONB NOT NULL,
                status VARCHAR(50) DEFAULT 'draft',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(255),
                tags TEXT[] DEFAULT '{}',
                metadata JSONB DEFAULT '{}',
                version INTEGER DEFAULT 1
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_workflows_status ON orchestra.workflows(status);
            CREATE INDEX IF NOT EXISTS idx_workflows_tags ON orchestra.workflows USING GIN(tags);
            CREATE INDEX IF NOT EXISTS idx_workflows_created_by ON orchestra.workflows(created_by);
            
            -- Comments
            COMMENT ON TABLE orchestra.workflows IS 'Workflow definitions and configurations';
        """
        )
        logger.info("Created orchestra.workflows table")

        # Audit logs table
        await self.manager.execute(
            """
            CREATE TABLE IF NOT EXISTS orchestra.audit_logs (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(100) NOT NULL,
                entity_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255),
                details JSONB DEFAULT '{}',
                metadata JSONB DEFAULT '{}',
                ip_address INET,
                user_agent TEXT
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON orchestra.audit_logs(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_action ON orchestra.audit_logs(action);
            CREATE INDEX IF NOT EXISTS idx_audit_entity ON orchestra.audit_logs(entity_type, entity_id);
            CREATE INDEX IF NOT EXISTS idx_audit_user ON orchestra.audit_logs(user_id);
            
            -- Partitioning for performance (monthly partitions)
            -- Note: Requires PostgreSQL 11+
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relname = 'audit_logs' AND n.nspname = 'orchestra'
                    AND c.relkind = 'p'
                ) THEN
                    -- Convert to partitioned table if not already
                    -- This is a placeholder - actual partitioning requires more complex migration
                    NULL;
                END IF;
            END $$;
            
            -- Comments
            COMMENT ON TABLE orchestra.audit_logs IS 'Comprehensive audit trail for all operations';
        """
        )
        logger.info("Created orchestra.audit_logs table")

        # Memory snapshots table
        await self.manager.execute(
            """
            CREATE TABLE IF NOT EXISTS orchestra.memory_snapshots (
                id SERIAL PRIMARY KEY,
                agent_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255),
                snapshot_data JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}',
                version INTEGER DEFAULT 1
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_memory_agent_id ON orchestra.memory_snapshots(agent_id);
            CREATE INDEX IF NOT EXISTS idx_memory_user_id ON orchestra.memory_snapshots(user_id);
            CREATE INDEX IF NOT EXISTS idx_memory_created_at ON orchestra.memory_snapshots(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_memory_agent_user ON orchestra.memory_snapshots(agent_id, user_id);
            
            -- Comments
            COMMENT ON TABLE orchestra.memory_snapshots IS 'Agent memory state snapshots';
        """
        )
        logger.info("Created orchestra.memory_snapshots table")

    async def create_functions(self):
        """Create database functions for maintenance and optimization."""

        # Function to cleanup expired cache entries
        await self.manager.execute(
            """
            CREATE OR REPLACE FUNCTION cache.cleanup_expired_entries()
            RETURNS INTEGER AS $$
            DECLARE
                deleted_count INTEGER;
            BEGIN
                DELETE FROM cache.entries
                WHERE expires_at < CURRENT_TIMESTAMP;
                
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                RETURN deleted_count;
            END;
            $$ LANGUAGE plpgsql;
            
            COMMENT ON FUNCTION cache.cleanup_expired_entries() IS 
            'Remove expired cache entries and return count of deleted rows';
        """
        )
        self.functions_created.append("cache.cleanup_expired_entries")

        # Function to cleanup expired sessions
        await self.manager.execute(
            """
            CREATE OR REPLACE FUNCTION sessions.cleanup_expired_sessions()
            RETURNS INTEGER AS $$
            DECLARE
                deleted_count INTEGER;
            BEGIN
                DELETE FROM sessions.sessions
                WHERE expires_at < CURRENT_TIMESTAMP;
                
                GET DIAGNOSTICS deleted_count = ROW_COUNT;
                RETURN deleted_count;
            END;
            $$ LANGUAGE plpgsql;
            
            COMMENT ON FUNCTION sessions.cleanup_expired_sessions() IS 
            'Remove expired sessions and return count of deleted rows';
        """
        )
        self.functions_created.append("sessions.cleanup_expired_sessions")

        # Function to update cache access statistics
        await self.manager.execute(
            """
            CREATE OR REPLACE FUNCTION cache.update_access_stats(p_key VARCHAR)
            RETURNS VOID AS $$
            BEGIN
                UPDATE cache.entries
                SET accessed_at = CURRENT_TIMESTAMP,
                    access_count = access_count + 1
                WHERE key = p_key;
            END;
            $$ LANGUAGE plpgsql;
            
            COMMENT ON FUNCTION cache.update_access_stats(VARCHAR) IS 
            'Update access timestamp and count for cache entries';
        """
        )
        self.functions_created.append("cache.update_access_stats")

        # Function to get cache statistics
        await self.manager.execute(
            """
            CREATE OR REPLACE FUNCTION cache.get_statistics()
            RETURNS TABLE (
                total_entries BIGINT,
                total_size_mb NUMERIC,
                expired_entries BIGINT,
                avg_access_count NUMERIC,
                most_accessed_keys TEXT[]
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    COUNT(*)::BIGINT as total_entries,
                    ROUND(SUM(pg_column_size(value))::NUMERIC / 1048576, 2) as total_size_mb,
                    COUNT(*) FILTER (WHERE expires_at < CURRENT_TIMESTAMP)::BIGINT as expired_entries,
                    ROUND(AVG(access_count)::NUMERIC, 2) as avg_access_count,
                    ARRAY(
                        SELECT key FROM cache.entries 
                        ORDER BY access_count DESC 
                        LIMIT 10
                    ) as most_accessed_keys
                FROM cache.entries;
            END;
            $$ LANGUAGE plpgsql;
            
            COMMENT ON FUNCTION cache.get_statistics() IS 
            'Get comprehensive cache statistics';
        """
        )
        self.functions_created.append("cache.get_statistics")

        logger.info(f"Created {len(self.functions_created)} database functions")

    async def create_triggers(self):
        """Create triggers for automatic updates."""

        # Update timestamp triggers
        await self.manager.execute(
            """
            -- Generic function for updating timestamps
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Apply to agents table
            DROP TRIGGER IF EXISTS update_agents_updated_at ON orchestra.agents;
            CREATE TRIGGER update_agents_updated_at
                BEFORE UPDATE ON orchestra.agents
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
                
            -- Apply to workflows table
            DROP TRIGGER IF EXISTS update_workflows_updated_at ON orchestra.workflows;
            CREATE TRIGGER update_workflows_updated_at
                BEFORE UPDATE ON orchestra.workflows
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
                
            -- Apply to sessions table
            DROP TRIGGER IF EXISTS update_sessions_updated_at ON sessions.sessions;
            CREATE TRIGGER update_sessions_updated_at
                BEFORE UPDATE ON sessions.sessions
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """
        )
        logger.info("Created update timestamp triggers")

    async def optimize_settings(self):
        """Apply PostgreSQL performance optimizations."""

        # Note: Some settings require superuser privileges
        optimizations = [
            # Autovacuum settings for better performance
            "ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.05",
            "ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05",
            # Enable pg_stat_statements for query monitoring
            "CREATE EXTENSION IF NOT EXISTS pg_stat_statements",
            # Enable UUID generation
            "CREATE EXTENSION IF NOT EXISTS pgcrypto",
            # Enable trigram search for better text search
            "CREATE EXTENSION IF NOT EXISTS pg_trgm",
        ]

        for optimization in optimizations:
            try:
                await self.manager.execute(optimization)
                logger.info(f"Applied: {optimization}")
            except Exception as e:
                logger.warning(f"Could not apply optimization '{optimization}': {e}")

    async def create_initial_data(self):
        """Create initial data for testing."""

        # Create a default agent
        await self.manager.execute(
            """
            INSERT INTO orchestra.agents (name, type, config, capabilities, status)
            VALUES ('System Assistant', 'system', '{"model": "gpt-4"}', '{"admin", "debug"}', 'active')
            ON CONFLICT DO NOTHING;
        """
        )

        # Create a sample workflow
        await self.manager.execute(
            """
            INSERT INTO orchestra.workflows (name, description, definition, status)
            VALUES (
                'Sample Workflow',
                'A sample workflow for testing',
                '{"steps": [{"id": "start", "type": "input"}, {"id": "end", "type": "output"}]}',
                'active'
            )
            ON CONFLICT DO NOTHING;
        """
        )

        logger.info("Created initial data")

    async def verify_installation(self):
        """Verify the installation is complete and working."""

        # Check schemas
        schemas = await self.manager.fetch(
            """
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name IN ('orchestra', 'cache', 'sessions')
        """
        )

        if len(schemas) != 3:
            raise Exception("Not all schemas were created")

        # Check tables
        tables = await self.manager.fetch(
            """
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema IN ('orchestra', 'cache', 'sessions')
            AND table_type = 'BASE TABLE'
        """
        )

        expected_tables = 6  # Total number of tables
        if len(tables) < expected_tables:
            raise Exception(f"Expected {expected_tables} tables, found {len(tables)}")

        # Test basic operations
        test_key = "test_init_key"
        await self.manager.execute(
            """
            INSERT INTO cache.entries (key, value, expires_at)
            VALUES ($1, $2, CURRENT_TIMESTAMP + INTERVAL '1 hour')
            ON CONFLICT (key) DO UPDATE SET value = $2
        """,
            test_key,
            '{"test": true}',
        )

        result = await self.manager.fetchval("SELECT value FROM cache.entries WHERE key = $1", test_key)

        if not result:
            raise Exception("Cache test failed")

        # Cleanup test data
        await self.manager.execute("DELETE FROM cache.entries WHERE key = $1", test_key)

        logger.info("Installation verified successfully")

    async def print_summary(self):
        """Print installation summary."""

        # Get database size
        db_size = await self.manager.fetchval(
            """
            SELECT pg_size_pretty(pg_database_size(current_database()))
        """
        )

        # Get table counts
        table_stats = await self.manager.fetch(
            """
            SELECT 
                schemaname || '.' || tablename as table_name,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            WHERE schemaname IN ('orchestra', 'cache', 'sessions')
            ORDER BY schemaname, tablename
        """
        )

        print("\n" + "=" * 60)
        print("UNIFIED POSTGRESQL INITIALIZATION COMPLETE")
        print("=" * 60)
        print(f"\nDatabase Size: {db_size}")
        print(f"\nSchemas Created: {', '.join(self.schemas_created)}")
        print(f"\nFunctions Created: {len(self.functions_created)}")
        print("\nTable Statistics:")
        for stat in table_stats:
            print(f"  - {stat['table_name']}: {stat['row_count']} rows")
        print("\nNext Steps:")
        print("1. Run the migration script if upgrading from old architecture:")
        print("   python scripts/migrate_to_unified_postgresql.py")
        print("2. Start the performance monitoring dashboard:")
        print("   python monitoring/postgresql_performance_dashboard.py")
        print("3. Run tests to verify functionality:")
        print("   pytest tests/test_unified_postgresql.py -v")
        print("=" * 60 + "\n")

    async def run(self):
        """Run the complete initialization process."""
        try:
            await self.initialize()

            logger.info("Starting PostgreSQL initialization...")

            # Create schemas
            await self.create_schemas()

            # Create tables
            await self.create_tables()

            # Create functions
            await self.create_functions()

            # Create triggers
            await self.create_triggers()

            # Apply optimizations
            await self.optimize_settings()

            # Create initial data
            await self.create_initial_data()

            # Verify installation
            await self.verify_installation()

            # Print summary
            await self.print_summary()

            logger.info("Initialization completed successfully!")

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise
        finally:
            await close_connection_manager()


async def main():
    """Main entry point."""
    initializer = UnifiedPostgreSQLInitializer()
    await initializer.run()


if __name__ == "__main__":
    asyncio.run(main())
