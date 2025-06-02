#!/usr/bin/env python3
"""Simple script to set up MCP database tables"""

import os
import psycopg
from psycopg import sql

def setup_mcp_database():
    """Create basic tables for MCP functionality"""

    # Connection parameters
    conn_params = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "orchestrator"),
        "user": os.getenv("POSTGRES_USER", "orchestrator"),
        "password": os.getenv("POSTGRES_PASSWORD", "orch3str4_2024"),
    }

    print("🔧 Setting up MCP database tables...")

    try:
        # Connect to database
        with psycopg.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                # Create orchestra schema if not exists
                cur.execute("CREATE SCHEMA IF NOT EXISTS orchestra")

                # Create sessions table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orchestra.sessions (
                        id VARCHAR(255) PRIMARY KEY,
                        data JSONB NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                print("✅ Created sessions table")

                # Create agents table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orchestra.agents (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        capabilities JSONB,
                        autonomy_level FLOAT DEFAULT 0.5,
                        model_config JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                print("✅ Created agents table")

                # Create knowledge_base table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orchestra.knowledge_base (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        title VARCHAR(500) NOT NULL,
                        content TEXT NOT NULL,
                        category VARCHAR(100) NOT NULL,
                        tags TEXT[],
                        source VARCHAR(500),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                print("✅ Created knowledge_base table")

                # Create api_keys table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orchestra.api_keys (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(255) NOT NULL,
                        key_hash VARCHAR(255) NOT NULL UNIQUE,
                        permissions JSONB,
                        last_used TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP
                    )
                """
                )
                print("✅ Created api_keys table")

                # Create audit_logs table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orchestra.audit_logs (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        event_type VARCHAR(100) NOT NULL,
                        actor VARCHAR(255) NOT NULL,
                        resource_type VARCHAR(100) NOT NULL,
                        resource_id VARCHAR(255) NOT NULL,
                        details JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                print("✅ Created audit_logs table")

                # Create workflows table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orchestra.workflows (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(255) NOT NULL,
                        definition JSONB NOT NULL,
                        status VARCHAR(50) DEFAULT 'created',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                print("✅ Created workflows table")

                # Create memory_snapshots table
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orchestra.memory_snapshots (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        agent_id UUID NOT NULL,
                        snapshot_data JSONB NOT NULL,
                        vector_ids TEXT[],
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )
                print("✅ Created memory_snapshots table")

                # Create indexes for better performance
                cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON orchestra.sessions(expires_at)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_agents_name ON orchestra.agents(name)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_category ON orchestra.knowledge_base(category)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON orchestra.knowledge_base USING GIN(tags)")
                print("✅ Created indexes")

                # Commit all changes
                conn.commit()

                print("\n✨ MCP database setup complete!")
                print("   Tables created in schema: orchestra")

    except Exception as e:
        print(f"\n❌ Error setting up database: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. User 'orchestrator' exists with correct password")
        print("  3. Database 'orchestrator' exists")

if __name__ == "__main__":
    setup_mcp_database()
