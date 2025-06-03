# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""Simple script to set up MCP database tables"""
    """Create basic tables for MCP functionality"""
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "orchestrator"),
        "user": os.getenv("POSTGRES_USER", "orchestrator"),
        "password": os.getenv("POSTGRES_PASSWORD", "orch3str4_2024"),
    }

    print("🔧 Setting up MCP database tables...")

    try:


        pass
        # Connect to database
        with psycopg.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                # Create orchestra schema if not exists
                cur.execute("CREATE SCHEMA IF NOT EXISTS orchestra")

                # Create sessions table
                cur.execute(
                    """
                """
                print("✅ Created sessions table")

                # Create agents table
                cur.execute(
                    """
                """
                print("✅ Created agents table")

                # Create knowledge_base table
                cur.execute(
                    """
                """
                print("✅ Created knowledge_base table")

                # Create api_keys table
                cur.execute(
                    """
                """
                print("✅ Created api_keys table")

                # Create audit_logs table
                cur.execute(
                    """
                """
                print("✅ Created audit_logs table")

                # Create workflows table
                cur.execute(
                    """
                """
                print("✅ Created workflows table")

                # Create memory_snapshots table
                cur.execute(
                    """
                """
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

    except Exception:


        pass
        print(f"\n❌ Error setting up database: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. User 'orchestrator' exists with correct password")
        print("  3. Database 'orchestrator' exists")

if __name__ == "__main__":
    setup_mcp_database()
