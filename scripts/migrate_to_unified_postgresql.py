#!/usr/bin/env python3
"""
Migration script to transition from duplicated PostgreSQL implementations
to the new unified architecture.

This script:
1. Migrates data from old tables to new unified structure
2. Updates all references to use the new unified clients
3. Removes deprecated code and tables
4. Validates the migration
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.database.connection_manager_enhanced import get_connection_manager_enhanced as get_connection_manager
from shared.database.unified_postgresql_enhanced import get_unified_postgresql_enhanced as get_unified_postgresql
from shared.database.unified_db_v2 import get_unified_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class UnifiedPostgreSQLMigration:
    """Handles migration to unified PostgreSQL architecture."""

    def __init__(self):
        self.manager = None
        self.unified_pg = None
        self.unified_db = None
        self.migration_stats = {
            "sessions_migrated": 0,
            "cache_entries_migrated": 0,
            "deprecated_tables_removed": 0,
            "files_updated": 0,
            "errors": [],
        }

    async def initialize(self):
        """Initialize database connections."""
        logger.info("Initializing migration tools...")
        self.manager = await get_connection_manager()
        self.unified_pg = await get_unified_postgresql()
        self.unified_db = await get_unified_database()
        logger.info("Migration tools initialized")

    async def run_migration(self):
        """Run the complete migration process."""
        try:
            await self.initialize()

            # Step 1: Backup existing data
            logger.info("Step 1: Creating backup...")
            await self.create_backup()

            # Step 2: Migrate sessions
            logger.info("Step 2: Migrating sessions...")
            await self.migrate_sessions()

            # Step 3: Migrate cache entries
            logger.info("Step 3: Migrating cache entries...")
            await self.migrate_cache()

            # Step 4: Update code references
            logger.info("Step 4: Updating code references...")
            await self.update_code_references()

            # Step 5: Remove deprecated tables
            logger.info("Step 5: Cleaning up deprecated tables...")
            await self.cleanup_deprecated_tables()

            # Step 6: Validate migration
            logger.info("Step 6: Validating migration...")
            await self.validate_migration()

            # Print summary
            self.print_summary()

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.migration_stats["errors"].append(str(e))
            raise

    async def create_backup(self):
        """Create backup of existing data."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(f"backups/migration_{timestamp}")
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Export existing tables to JSON
        tables_to_backup = [
            ("orchestra.sessions", "sessions.json"),
            ("orchestra.agents", "agents.json"),
            ("orchestra.workflows", "workflows.json"),
            ("orchestra.audit_logs", "audit_logs.json"),
        ]

        for table, filename in tables_to_backup:
            try:
                rows = await self.manager.fetch(f"SELECT * FROM {table}")
                data = [dict(row) for row in rows]

                # Convert datetime objects to strings
                for row in data:
                    for key, value in row.items():
                        if isinstance(value, datetime):
                            row[key] = value.isoformat()

                with open(backup_dir / filename, "w") as f:
                    json.dump(data, f, indent=2, default=str)

                logger.info(f"Backed up {len(data)} rows from {table}")
            except Exception as e:
                logger.warning(f"Could not backup {table}: {e}")

    async def migrate_sessions(self):
        """Migrate sessions from old structure to new."""
        try:
            # Check if old sessions table exists
            old_sessions = await self.manager.fetch(
                """
                SELECT * FROM orchestra.sessions 
                WHERE expires_at > CURRENT_TIMESTAMP
            """
            )

            for session in old_sessions:
                try:
                    # Parse session data
                    session_data = session["data"]
                    if isinstance(session_data, str):
                        session_data = json.loads(session_data)

                    # Create session in new structure
                    await self.unified_pg.session_create(
                        user_id=session_data.get("user_id"),
                        agent_id=session_data.get("agent_id"),
                        data=session_data,
                        ttl=86400,  # Default 24 hours
                        metadata={"migrated": True, "old_id": session["id"]},
                    )

                    self.migration_stats["sessions_migrated"] += 1

                except Exception as e:
                    logger.error(f"Failed to migrate session {session['id']}: {e}")
                    self.migration_stats["errors"].append(f"Session {session['id']}: {e}")

            logger.info(f"Migrated {self.migration_stats['sessions_migrated']} sessions")

        except Exception as e:
            logger.warning(f"No existing sessions to migrate: {e}")

    async def migrate_cache(self):
        """Migrate cache entries if any exist."""
        try:
            # Check for any existing cache tables
            cache_tables = await self.manager.fetch(
                """
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename LIKE '%cache%'
            """
            )

            for table in cache_tables:
                table_name = table["tablename"]
                try:
                    rows = await self.manager.fetch(
                        f"""
                        SELECT * FROM public.{table_name}
                        WHERE expires_at > CURRENT_TIMESTAMP
                    """
                    )

                    for row in rows:
                        await self.unified_pg.cache_set(
                            key=row.get("key", row.get("id")),
                            value=row.get("value", row.get("data")),
                            ttl=3600,
                            tags=["migrated", f"from_{table_name}"],
                        )
                        self.migration_stats["cache_entries_migrated"] += 1

                except Exception as e:
                    logger.warning(f"Could not migrate from {table_name}: {e}")

            logger.info(f"Migrated {self.migration_stats['cache_entries_migrated']} cache entries")

        except Exception as e:
            logger.warning(f"No cache entries to migrate: {e}")

    async def update_code_references(self):
        """Update Python files to use new unified clients."""
        replacements = [
            # Old imports to new imports
            (
                "from shared.database.postgresql_client import PostgreSQLClient",
                "from shared.database.unified_postgresql_enhanced import get_unified_postgresql_enhanced as get_unified_postgresql",
            ),
            (
                "from shared.cache.postgresql_cache import PostgreSQLCache",
                "from shared.database.unified_postgresql_enhanced import get_unified_postgresql_enhanced as get_unified_postgresql",
            ),
            (
                "from shared.sessions.postgresql_sessions import PostgreSQLSessionStore",
                "from shared.database.unified_postgresql_enhanced import get_unified_postgresql_enhanced as get_unified_postgresql",
            ),
            (
                "from shared.database.unified_db import UnifiedDatabase",
                "from shared.database.unified_db_v2 import get_unified_database",
            ),
            # Old instantiations to new
            ("PostgreSQLClient(", "await get_unified_postgresql(  # Updated by migration"),
            ("PostgreSQLCache(", "await get_unified_postgresql(  # Updated by migration"),
            ("PostgreSQLSessionStore(", "await get_unified_postgresql(  # Updated by migration"),
            ("UnifiedDatabase(", "await get_unified_database(  # Updated by migration"),
            # Method name changes
            (".create_session(", ".session_create("),
            (".get_session(", ".session_get("),
            (".delete_session(", ".session_delete("),
            (".get(", ".cache_get("),
            (".set(", ".cache_set("),
            (".delete(", ".cache_delete("),
        ]

        # Find all Python files
        python_files = list(Path(".").rglob("*.py"))

        for py_file in python_files:
            # Skip virtual environments and this script
            if (
                "venv" in str(py_file)
                or "__pycache__" in str(py_file)
                or py_file.name == "migrate_to_unified_postgresql.py"
            ):
                continue

            try:
                content = py_file.read_text()
                original_content = content

                # Apply replacements
                for old, new in replacements:
                    if old in content:
                        content = content.replace(old, new)

                # Write back if changed
                if content != original_content:
                    py_file.write_text(content)
                    self.migration_stats["files_updated"] += 1
                    logger.info(f"Updated {py_file}")

            except Exception as e:
                logger.error(f"Failed to update {py_file}: {e}")
                self.migration_stats["errors"].append(f"File update {py_file}: {e}")

    async def cleanup_deprecated_tables(self):
        """Remove deprecated tables and schemas."""
        deprecated_items = [
            # Old session tables in wrong schema
            "DROP TABLE IF EXISTS orchestra.sessions CASCADE",
            # Old cache tables
            "DROP TABLE IF EXISTS public.cache CASCADE",
            "DROP TABLE IF EXISTS public.cache_entries CASCADE",
            "DROP TABLE IF EXISTS public.redis_cache CASCADE",
            # Remove duplicate functions
            "DROP FUNCTION IF EXISTS public.cleanup_expired_sessions CASCADE",
            "DROP FUNCTION IF EXISTS public.cleanup_expired_cache CASCADE",
        ]

        for sql in deprecated_items:
            try:
                await self.manager.execute(sql)
                self.migration_stats["deprecated_tables_removed"] += 1
                logger.info(f"Executed: {sql}")
            except Exception as e:
                logger.warning(f"Could not execute {sql}: {e}")

    async def validate_migration(self):
        """Validate the migration was successful."""
        validations = []

        # Check new tables exist
        required_tables = [
            ("cache.entries", "Cache table"),
            ("sessions.sessions", "Sessions table"),
            ("orchestra.agents", "Agents table"),
            ("orchestra.workflows", "Workflows table"),
            ("orchestra.audit_logs", "Audit logs table"),
            ("orchestra.memory_snapshots", "Memory snapshots table"),
        ]

        for table, description in required_tables:
            exists = await self.manager.fetchval(
                f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = split_part('{table}', '.', 1)
                    AND table_name = split_part('{table}', '.', 2)
                )
            """
            )

            validations.append({"check": description, "passed": exists, "message": "Exists" if exists else "Missing"})

        # Check connection pool is working
        try:
            health = await self.unified_pg.health_check()
            validations.append(
                {
                    "check": "Connection pool health",
                    "passed": health["status"] == "healthy",
                    "message": f"Pool: {health['pool']['used_connections']}/{health['pool']['max_size']} connections",
                }
            )
        except Exception as e:
            validations.append({"check": "Connection pool health", "passed": False, "message": str(e)})

        # Check unified database is working
        try:
            db_health = await self.unified_db.health_check()
            validations.append(
                {
                    "check": "Unified database health",
                    "passed": db_health["status"] == "healthy",
                    "message": "All systems operational",
                }
            )
        except Exception as e:
            validations.append({"check": "Unified database health", "passed": False, "message": str(e)})

        # Print validation results
        logger.info("\n=== Migration Validation ===")
        all_passed = True
        for validation in validations:
            status = "✓" if validation["passed"] else "✗"
            logger.info(f"{status} {validation['check']}: {validation['message']}")
            if not validation["passed"]:
                all_passed = False

        if not all_passed:
            raise Exception("Migration validation failed")

    def print_summary(self):
        """Print migration summary."""
        logger.info("\n=== Migration Summary ===")
        logger.info(f"Sessions migrated: {self.migration_stats['sessions_migrated']}")
        logger.info(f"Cache entries migrated: {self.migration_stats['cache_entries_migrated']}")
        logger.info(f"Deprecated items removed: {self.migration_stats['deprecated_tables_removed']}")
        logger.info(f"Files updated: {self.migration_stats['files_updated']}")

        if self.migration_stats["errors"]:
            logger.error(f"\nErrors encountered: {len(self.migration_stats['errors'])}")
            for error in self.migration_stats["errors"][:5]:  # Show first 5 errors
                logger.error(f"  - {error}")
            if len(self.migration_stats["errors"]) > 5:
                logger.error(f"  ... and {len(self.migration_stats['errors']) - 5} more")
        else:
            logger.info("\n✅ Migration completed successfully with no errors!")

        logger.info("\n=== Next Steps ===")
        logger.info("1. Test all functionality with the new unified system")
        logger.info("2. Monitor performance and connection pool usage")
        logger.info("3. Remove old import statements from any remaining files")
        logger.info("4. Delete deprecated Python files:")
        logger.info("   - shared/database/postgresql_client.py")
        logger.info("   - shared/cache/postgresql_cache.py")
        logger.info("   - shared/sessions/postgresql_sessions.py")
        logger.info("   - shared/database/unified_db.py")

async def main():
    """Run the migration."""
    migration = UnifiedPostgreSQLMigration()

    logger.info("=== PostgreSQL Unification Migration ===")
    logger.info("This will migrate all PostgreSQL components to the unified architecture.")

    # Confirm before proceeding
    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() != "yes":
        logger.info("Migration cancelled.")
        return

    try:
        await migration.run_migration()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        # Close connections
        from shared.database.connection_manager import close_connection_manager
        from shared.database.unified_postgresql import close_unified_postgresql
        from shared.database.unified_db_v2 import close_unified_database

        await close_unified_database()
        await close_unified_postgresql()
        await close_connection_manager()

if __name__ == "__main__":
    asyncio.run(main())
