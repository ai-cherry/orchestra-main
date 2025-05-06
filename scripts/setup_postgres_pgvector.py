#!/usr/bin/env python
"""
PostgreSQL with pgvector Setup Script for Cloud SQL

This script sets up a PostgreSQL Cloud SQL instance with pgvector extension and
creates the necessary schema for Phidata agent storage and memory. It handles
both IAM authentication and password authentication via Secret Manager.

Usage:
    python scripts/setup_postgres_pgvector.py [--apply]
    
    Without --apply flag, the script will only print the SQL commands without executing them.
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional, List

# Import google cloud libraries with error handling
try:
    from google.cloud.sql.connector import Connector
    from google.cloud import secretmanager
    import sqlalchemy
except ImportError:
    print("Required Google Cloud libraries not found. Installing...")
    import subprocess
    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "google-cloud-sql-connector",
        "google-cloud-secret-manager",
        "sqlalchemy>=2.0.0",
        "pg8000"  # PostgreSQL driver
    ])
    # Retry imports
    from google.cloud.sql.connector import Connector
    from google.cloud import secretmanager
    import sqlalchemy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def get_cloud_sql_connection(
    instance_connection_name: str,
    database: str,
    user: str,
    use_iam_auth: bool = False,
    password: Optional[str] = None,
    project_id: Optional[str] = None,
    password_secret_name: Optional[str] = None
) -> sqlalchemy.engine.Engine:
    """
    Create a connection to Cloud SQL using either IAM or password authentication.
    
    Args:
        instance_connection_name: Cloud SQL instance connection name (project:region:instance)
        database: Database name
        user: Database user
        use_iam_auth: Whether to use IAM authentication (True) or password auth (False)
        password: Database password (if not using IAM auth and not using Secret Manager)
        project_id: GCP project ID (needed for Secret Manager)
        password_secret_name: Name of the secret in Secret Manager containing the password
    
    Returns:
        SQLAlchemy engine connected to Cloud SQL
    """
    # Create SQL connection using google-cloud-sql-connector
    connector = Connector()
    
    # Use IAM authentication if enabled
    if use_iam_auth:
        logger.info(f"Connecting to Cloud SQL with IAM auth: {instance_connection_name}")
        
        def getconn():
            try:
                conn = connector.connect(
                    instance_connection_string=instance_connection_name,
                    driver="pg8000",
                    user=user,
                    db=database,
                    enable_iam_auth=True
                )
                return conn
            except Exception as e:
                logger.error(f"Error connecting to Cloud SQL with IAM auth: {e}")
                raise
    
    # Otherwise use password auth
    else:
        # If password is not provided, try to get it from Secret Manager
        if password is None and password_secret_name and project_id:
            try:
                # Get the database password from Secret Manager
                client = secretmanager.SecretManagerServiceClient()
                name = f"projects/{project_id}/secrets/{password_secret_name}/versions/latest"
                response = client.access_secret_version(name=name)
                password = response.payload.data.decode("UTF-8")
                logger.info(f"Retrieved password from Secret Manager: {password_secret_name}")
            except Exception as e:
                logger.error(f"Error retrieving database password from Secret Manager: {e}")
                raise
        
        if password is None:
            raise ValueError("Password is required for non-IAM authentication")
        
        logger.info(f"Connecting to Cloud SQL with password auth: {instance_connection_name}")
        
        def getconn():
            try:
                conn = connector.connect(
                    instance_connection_string=instance_connection_name,
                    driver="pg8000",
                    user=user,
                    password=password,
                    db=database
                )
                return conn
            except Exception as e:
                logger.error(f"Error connecting to Cloud SQL with password auth: {e}")
                raise
    
    # Create SQLAlchemy engine using the Cloud SQL connection
    try:
        engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            echo=True  # Log SQL statements (useful for debugging)
        )
        return engine
    except Exception as e:
        logger.error(f"Error creating SQLAlchemy engine: {e}")
        raise


def setup_postgres_pgvector(
    engine: sqlalchemy.engine.Engine,
    schema_name: str = "llm",
    apply: bool = False
) -> None:
    """
    Set up PostgreSQL with pgvector extension and create the necessary schema.
    
    Args:
        engine: SQLAlchemy engine connected to Cloud SQL
        schema_name: Name of the schema to create
        apply: Whether to apply the changes (True) or just print them (False)
    """
    # Define SQL statements
    sql_statements = [
        # Create the pgvector extension if it doesn't exist
        "CREATE EXTENSION IF NOT EXISTS vector;",
        
        # Create the schema if it doesn't exist
        f"CREATE SCHEMA IF NOT EXISTS {schema_name};",
        
        # Grant permissions to the schema
        f"GRANT ALL PRIVILEGES ON SCHEMA {schema_name} TO PUBLIC;",
        
        # Additional database settings useful for AI storage
        "ALTER SYSTEM SET max_connections = '100';",
        "ALTER SYSTEM SET shared_buffers = '1GB';",
        "ALTER SYSTEM SET effective_cache_size = '3GB';",
        "ALTER SYSTEM SET maintenance_work_mem = '256MB';",
        "ALTER SYSTEM SET random_page_cost = '1.1';",
        "ALTER SYSTEM SET effective_io_concurrency = '200';",
        "ALTER SYSTEM SET work_mem = '16MB';",
        
        # Vacuum and analyze settings
        "ALTER SYSTEM SET autovacuum = on;",
        "ALTER SYSTEM SET autovacuum_vacuum_scale_factor = '0.05';",
        "ALTER SYSTEM SET autovacuum_analyze_scale_factor = '0.1';",
    ]
    
    # Execute SQL statements
    with engine.connect() as conn:
        for statement in sql_statements:
            logger.info(f"SQL: {statement}")
            
            if apply:
                try:
                    conn.execute(sqlalchemy.text(statement))
                    logger.info("✅ Executed successfully")
                except Exception as e:
                    logger.error(f"❌ Error executing SQL: {e}")
            else:
                logger.info("⚠️ Skipped execution (dry run)")
        
        if apply:
            conn.commit()
            logger.info("✅ All SQL statements executed and committed")
        else:
            logger.info("⚠️ Dry run completed. Use --apply to execute the SQL statements")


def create_indexes_for_pgvector(
    engine: sqlalchemy.engine.Engine,
    schema_name: str = "llm",
    apply: bool = False
) -> None:
    """
    Create recommended indexes for pgvector tables.
    
    Args:
        engine: SQLAlchemy engine connected to Cloud SQL
        schema_name: Schema name
        apply: Whether to apply the changes
    """
    # Check if tables exist first
    with engine.connect() as conn:
        # Query to get all tables in the schema
        check_tables_query = f"""
        SELECT tablename 
        FROM pg_tables
        WHERE schemaname = '{schema_name}';
        """
        
        logger.info(f"Checking for existing tables in schema '{schema_name}'...")
        if apply:
            try:
                result = conn.execute(sqlalchemy.text(check_tables_query))
                tables = [row[0] for row in result]
                logger.info(f"Found tables: {tables}")
                
                # Create indexes for each table that looks like a vector table
                # (contains 'vector' or 'pgvector' in the name)
                vector_tables = [t for t in tables if 'vector' in t.lower() or 'memory' in t.lower()]
                
                for table in vector_tables:
                    # Check if the table has a vector column
                    check_vector_col_query = f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = '{schema_name}'
                    AND table_name = '{table}'
                    AND data_type = 'vector';
                    """
                    
                    vector_cols = [row[0] for row in conn.execute(sqlalchemy.text(check_vector_col_query))]
                    
                    if vector_cols:
                        for vector_col in vector_cols:
                            # Create an index for the vector column
                            index_name = f"idx_{table}_{vector_col}_ivfflat"
                            create_index_query = f"""
                            CREATE INDEX IF NOT EXISTS {index_name}
                            ON {schema_name}.{table} USING ivfflat ({vector_col} vector_l2_ops)
                            WITH (lists = 100);
                            """
                            
                            logger.info(f"Creating IVFFlat index on {schema_name}.{table}.{vector_col}...")
                            conn.execute(sqlalchemy.text(create_index_query))
                            logger.info(f"✅ Created index {index_name}")
                
                # Commit changes
                conn.commit()
                logger.info("✅ All indexes created and committed")
            except Exception as e:
                logger.error(f"❌ Error creating indexes: {e}")
        else:
            logger.info("⚠️ Skipping index creation in dry run mode")


def main():
    """Main function to set up PostgreSQL with pgvector."""
    parser = argparse.ArgumentParser(
        description="Set up PostgreSQL Cloud SQL instance with pgvector extension"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the SQL commands (without this flag, commands are only printed)"
    )
    parser.add_argument(
        "--schema",
        default="llm",
        help="Schema name to create (default: llm)"
    )
    parser.add_argument(
        "--use-iam-auth",
        action="store_true",
        help="Use IAM authentication instead of password auth"
    )
    parser.add_argument(
        "--database",
        default=os.environ.get("CLOUD_SQL_DATABASE", "phidata"),
        help="Database name"
    )
    parser.add_argument(
        "--user",
        default=os.environ.get("CLOUD_SQL_USER", "postgres"),
        help="Database user"
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Database password (if not using IAM auth or Secret Manager)"
    )
    parser.add_argument(
        "--instance-connection-name",
        default=os.environ.get("CLOUD_SQL_INSTANCE_CONNECTION_NAME", ""),
        help="Cloud SQL instance connection name (project:region:instance)"
    )
    parser.add_argument(
        "--project-id",
        default=os.environ.get("GCP_PROJECT_ID", ""),
        help="GCP project ID"
    )
    parser.add_argument(
        "--password-secret-name",
        default=os.environ.get("CLOUD_SQL_PASSWORD_SECRET_NAME", "cloudsql-postgres-password"),
        help="Name of the secret in Secret Manager containing the password"
    )
    
    args = parser.parse_args()
    
    # Validate required arguments
    if not args.instance_connection_name:
        parser.error("--instance-connection-name is required")
    
    if not args.use_iam_auth and not args.password and not (args.project_id and args.password_secret_name):
        parser.error("Either --use-iam-auth flag, --password, or both --project-id and --password-secret-name are required")
    
    # Create connection
    try:
        engine = get_cloud_sql_connection(
            instance_connection_name=args.instance_connection_name,
            database=args.database,
            user=args.user,
            use_iam_auth=args.use_iam_auth,
            password=args.password,
            project_id=args.project_id,
            password_secret_name=args.password_secret_name
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT version();"))
            version = result.scalar()
            logger.info(f"Connected to PostgreSQL: {version}")
        
        # Set up pgvector and schema
        setup_postgres_pgvector(engine, schema_name=args.schema, apply=args.apply)
        
        # Create recommended indexes if applying changes
        if args.apply:
            create_indexes_for_pgvector(engine, schema_name=args.schema, apply=args.apply)
        
        logger.info(f"{'Applied' if args.apply else 'Dry run of'} PostgreSQL setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error setting up PostgreSQL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()