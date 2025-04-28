"""
Phidata Cloud SQL Configuration with PGVector for Agent Storage and Memory.

This module provides configuration for Phidata to use Cloud SQL (PostgreSQL) 
with PGVector for agent storage and memory, utilizing the google-cloud-sql-connector
for IAM authentication (or password auth via Secret Manager) and VertexAiEmbedder for embeddings.

Usage:
    from packages.phidata.src.cloudsql_pgvector import get_pgvector_memory, get_pg_agent_storage
    
    # Get vector memory store with Vertex AI embeddings
    vector_memory = get_pgvector_memory(user_id="user-123")
    
    # Get agent storage partitioned by agent_id
    agent_storage = get_pg_agent_storage(agent_id="my-agent-id")
"""

import os
import logging
import sqlalchemy
from typing import Dict, Any, Optional, Union
from google.cloud.sql.connector import Connector
from google.cloud import secretmanager

# Import Phidata classes with error handling
try:
    from phi.embedder import VertexAiEmbedder
    from phi.storage.postgres.pgvector import PgVector2
    from phi.storage.assistant.pg import PgAssistantStorage
except ImportError as e:
    raise ImportError(
        f"Failed to import Phidata modules. Please install required packages: {e}\n"
        "Try: pip install 'phi-postgres>=0.2.0' 'phi-vectordb>=0.1.0'"
    )

logger = logging.getLogger(__name__)

# Default configuration - override with environment variables
DEFAULT_CONFIG = {
    "project_id": os.environ.get("GCP_PROJECT_ID", ""),
    "region": os.environ.get("GCP_REGION", "us-central1"),
    "instance_connection_name": os.environ.get("CLOUD_SQL_INSTANCE_CONNECTION_NAME", ""),
    "database": os.environ.get("CLOUD_SQL_DATABASE", "phidata"),
    "user": os.environ.get("CLOUD_SQL_USER", "postgres"),
    "password_secret_name": os.environ.get("CLOUD_SQL_PASSWORD_SECRET_NAME", "cloudsql-postgres-password"),
    "use_iam_auth": os.environ.get("CLOUD_SQL_USE_IAM_AUTH", "false").lower() == "true",
    "schema_name": os.environ.get("PG_SCHEMA_NAME", "llm"),
    "vector_dimension": int(os.environ.get("EMBEDDING_VECTOR_SIZE", "768")),  # gecko-003 dimension
    "embedding_model": os.environ.get("VERTEX_EMBEDDING_MODEL", "textembedding-gecko@003"),
    "environment": os.environ.get("APP_ENV", "development")
}


def get_cloud_sql_connection(config: Optional[Dict[str, Any]] = None) -> sqlalchemy.engine.Engine:
    """
    Create a connection to Cloud SQL using either IAM or password authentication.
    
    Args:
        config: Configuration dictionary (falls back to environment variables)
    
    Returns:
        SQLAlchemy engine connected to Cloud SQL
    """
    # Use provided config or defaults
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    
    # Validate required configuration
    if not cfg["instance_connection_name"]:
        raise ValueError("Missing Cloud SQL instance connection name")
    if not cfg["project_id"]:
        raise ValueError("Missing GCP project ID")
    
    # Create SQL connection using google-cloud-sql-connector
    connector = Connector()
    
    # Use IAM authentication if enabled
    if cfg["use_iam_auth"]:
        def getconn():
            try:
                logger.info(f"Connecting to Cloud SQL with IAM auth: {cfg['instance_connection_name']}")
                conn = connector.connect(
                    instance_connection_string=cfg["instance_connection_name"],
                    driver="pg8000",
                    user=cfg["user"],
                    db=cfg["database"],
                    enable_iam_auth=True
                )
                return conn
            except Exception as e:
                logger.error(f"Error connecting to Cloud SQL with IAM auth: {e}")
                raise
    
    # Otherwise use password auth via Secret Manager
    else:
        try:
            # Get the database password from Secret Manager
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{cfg['project_id']}/secrets/{cfg['password_secret_name']}/versions/latest"
            response = client.access_secret_version(name=name)
            db_password = response.payload.data.decode("UTF-8")
            
            def getconn():
                try:
                    logger.info(f"Connecting to Cloud SQL with password auth: {cfg['instance_connection_name']}")
                    conn = connector.connect(
                        instance_connection_string=cfg["instance_connection_name"],
                        driver="pg8000",
                        user=cfg["user"],
                        password=db_password,
                        db=cfg["database"]
                    )
                    return conn
                except Exception as e:
                    logger.error(f"Error connecting to Cloud SQL with password auth: {e}")
                    raise
        except Exception as e:
            logger.error(f"Error retrieving database password from Secret Manager: {e}")
            raise
    
    # Create SQLAlchemy engine using the Cloud SQL connection
    try:
        engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            # Connection pool settings
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
        )
        return engine
    except Exception as e:
        logger.error(f"Error creating SQLAlchemy engine: {e}")
        raise


def get_vertexai_embedder(config: Optional[Dict[str, Any]] = None) -> VertexAiEmbedder:
    """
    Create a VertexAiEmbedder for vector embeddings.
    
    Args:
        config: Configuration dictionary (falls back to environment variables)
    
    Returns:
        Configured VertexAiEmbedder
    """
    # Use provided config or defaults
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    
    try:
        # Create the embedder using Vertex AI
        embedder = VertexAiEmbedder(
            model=cfg["embedding_model"],
            project_id=cfg["project_id"],
            location=cfg["region"]
        )
        logger.info(f"Created VertexAiEmbedder with model: {cfg['embedding_model']}")
        return embedder
    except Exception as e:
        logger.error(f"Error creating VertexAiEmbedder: {e}")
        raise


def get_pgvector_memory(
    user_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    table_name: Optional[str] = None
) -> PgVector2:
    """
    Get a configured PgVector2 for memory with VertexAI embeddings.
    
    Args:
        user_id: Optional user ID for table naming/partitioning
        config: Configuration dictionary (falls back to environment variables)
        table_name: Optional custom table name
    
    Returns:
        Configured PgVector2 instance
    """
    # Use provided config or defaults
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    
    # Create the database connection
    try:
        engine = get_cloud_sql_connection(cfg)
        
        # Create the embedder
        embedder = get_vertexai_embedder(cfg)
        
        # Configure the table name
        if not table_name:
            user_part = f"_{user_id}" if user_id else ""
            env_part = f"_{cfg['environment']}"
            table_name = f"pgvector{user_part}{env_part}"
        
        # Create and initialize PgVector2
        vector_store = PgVector2(
            db_engine=engine,
            table_name=table_name,
            schema_name=cfg["schema_name"],
            embedder=embedder,
            vector_dimension=cfg["vector_dimension"],
            create_tables=True  # Auto-create tables if they don't exist
        )
        
        logger.info(f"Created PgVector2 memory with table: {cfg['schema_name']}.{table_name}")
        return vector_store
    except Exception as e:
        logger.error(f"Error creating PgVector2 memory: {e}")
        raise


def get_pg_agent_storage(
    agent_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    table_name: Optional[str] = None
) -> PgAssistantStorage:
    """
    Get a configured PgAssistantStorage for agent data with partitioning.
    
    Args:
        agent_id: Optional agent ID for partitioning
        config: Configuration dictionary (falls back to environment variables)
        table_name: Optional custom table name
    
    Returns:
        Configured PgAssistantStorage instance
    """
    # Use provided config or defaults
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    
    # Create the database connection
    try:
        engine = get_cloud_sql_connection(cfg)
        
        # Configure the table name
        if not table_name:
            agent_part = f"_{agent_id}" if agent_id else ""
            env_part = f"_{cfg['environment']}"
            table_name = f"agent_storage{agent_part}{env_part}"
        
        # Create and initialize PgAssistantStorage
        agent_storage = PgAssistantStorage(
            db_engine=engine,
            table_name=table_name,
            schema_name=cfg["schema_name"],
            create_tables=True,
            # Enable partitioning by agent_id if supported
            partitioning_field="agent_id" if agent_id else None
        )
        
        logger.info(f"Created PgAssistantStorage with table: {cfg['schema_name']}.{table_name}")
        return agent_storage
    except Exception as e:
        logger.error(f"Error creating PgAssistantStorage: {e}")
        raise