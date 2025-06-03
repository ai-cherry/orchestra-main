# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agents table
CREATE TABLE IF NOT EXISTS orchestra.agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    capabilities JSONB DEFAULT '{}',
    autonomy_level INTEGER DEFAULT 1 CHECK (autonomy_level >= 0 AND autonomy_level <= 5),
    model_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflows table
CREATE TABLE IF NOT EXISTS orchestra.workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    definition JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Memory snapshots table
CREATE TABLE IF NOT EXISTS orchestra.memory_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES orchestra.agents(id) ON DELETE CASCADE,
    snapshot_data JSONB DEFAULT '{}',
    vector_ids TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS orchestra.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table (replacing Redis session storage)
CREATE TABLE IF NOT EXISTS orchestra.sessions (
    id VARCHAR(255) PRIMARY KEY,
    data JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API keys table
CREATE TABLE IF NOT EXISTS orchestra.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    permissions JSONB DEFAULT '{}',
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_agents_name ON orchestra.agents(name);
CREATE INDEX IF NOT EXISTS idx_agents_created_at ON orchestra.agents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON orchestra.workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON orchestra.workflows(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_snapshots_agent_id ON orchestra.memory_snapshots(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON orchestra.audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON orchestra.audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON orchestra.audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON orchestra.sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON orchestra.api_keys(key_hash);

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION orchestra.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to tables with updated_at
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON orchestra.agents
    FOR EACH ROW EXECUTE FUNCTION orchestra.update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON orchestra.workflows
    FOR EACH ROW EXECUTE FUNCTION orchestra.update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON orchestra.sessions
    FOR EACH ROW EXECUTE FUNCTION orchestra.update_updated_at_column();

CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON orchestra.api_keys
    FOR EACH ROW EXECUTE FUNCTION orchestra.update_updated_at_column();
"""
        "name": "research_agent",
        "description": "Specialized in research and information gathering",
        "capabilities": {"web_search": True, "document_analysis": True, "summarization": True},
        "autonomy_level": 2,
        "model_config": {"model": "gpt-4", "temperature": 0.7},
    },
    {
        "name": "code_agent",
        "description": "Specialized in code generation and review",
        "capabilities": {"code_generation": True, "code_review": True, "debugging": True, "testing": True},
        "autonomy_level": 3,
        "model_config": {"model": "gpt-4", "temperature": 0.3},
    },
    {
        "name": "orchestrator",
        "description": "Main orchestrator agent for coordinating other agents",
        "capabilities": {"agent_coordination": True, "workflow_management": True, "task_delegation": True},
        "autonomy_level": 4,
        "model_config": {"model": "gpt-4", "temperature": 0.5},
    },
]

def setup_schema(db: PostgreSQLClient, drop_existing: bool = False) -> None:
    """Setup PostgreSQL schema."""
        logger.warning("Dropping existing schema...")
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DROP SCHEMA IF EXISTS orchestra CASCADE")
                conn.commit()
        logger.info("Existing schema dropped")

    logger.info("Creating schema and tables...")
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            # Execute schema SQL
            for statement in SCHEMA_SQL.split(";"):
                if statement.strip():
                    cur.execute(statement)
            conn.commit()

    logger.info("Schema created successfully")

def insert_default_agents(db: PostgreSQLClient) -> None:
    """Insert default agents if they don't exist."""
    logger.info("Inserting default agents...")

    for agent_data in DEFAULT_AGENTS:
        # Check if agent already exists
        existing = db.# TODO: Consider adding EXPLAIN ANALYZE for performance
execute_query("SELECT id FROM orchestra.agents WHERE name = %s", (agent_data["name"],))

        if not existing:
            agent = db.create_agent(agent_data)
            logger.info(f"Created agent: {agent['name']} (ID: {agent['id']})")
        else:
            logger.info(f"Agent already exists: {agent_data['name']}")

def verify_schema(db: PostgreSQLClient) -> None:
    """Verify schema was created correctly."""
    logger.info("Verifying schema...")

    # Check tables exist
    tables_query = """
    """
    table_names = [t["table_name"] for t in tables]

    expected_tables = ["agents", "api_keys", "audit_logs", "memory_snapshots", "sessions", "workflows"]

    for table in expected_tables:
        if table in table_names:
            logger.info(f"✓ Table 'orchestra.{table}' exists")
        else:
            logger.error(f"✗ Table 'orchestra.{table}' is missing!")

    # Check indexes
    indexes_query = """
    """
    logger.info(f"Found {len(indexes)} indexes in orchestra schema")

    # Check triggers
    triggers_query = """
    """
    logger.info(f"Found {len(triggers)} triggers in orchestra schema")

def main():
    parser = argparse.ArgumentParser(description="Setup PostgreSQL schema for Orchestra AI")
    parser.add_argument("--drop", action="store_true", help="Drop existing schema before creating")
    parser.add_argument("--no-defaults", action="store_true", help="Don't insert default agents")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing schema")

    args = parser.parse_args()

    # Initialize database client
    db = PostgreSQLClient()

    try:


        pass
        # Test connection
        if not db.health_check():
            logger.error("Failed to connect to PostgreSQL")
            return 1

        logger.info("Connected to PostgreSQL successfully")

        if args.verify_only:
            verify_schema(db)
        else:
            # Setup schema
            setup_schema(db, drop_existing=args.drop)

            # Insert default agents
            if not args.no_defaults:
                insert_default_agents(db)

            # Verify
            verify_schema(db)

            logger.info("✅ PostgreSQL schema setup completed successfully!")

        return 0

    except Exception:


        pass
        logger.error(f"Setup failed: {e}")
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())
