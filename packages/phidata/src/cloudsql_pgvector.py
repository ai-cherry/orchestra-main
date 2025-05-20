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

"""
Phidata Cloud SQL Configuration with PGVector for Agent Storage and Memory.

This module provides configuration for Phidata to use Cloud SQL (PostgreSQL)
with PGVector for agent storage and memory, utilizing the google-cloud-sql-connector
for IAM authentication (or password auth via Secret Manager) and VertexAiEmbedder for embeddings.

Usage:
    from packages.phidata.src.cloudsql_pgvector import get_pgvector_memory, get_pg_agent_storage

    # Assuming you have a StorageConfig instance available
    # from packages.shared.src.storage.config import StorageConfig
    # storage_config = StorageConfig(...)

    # Get vector memory store with Vertex AI embeddings
    # vector_memory = get_pgvector_memory(storage_config=storage_config, user_id="user-123")

    # Get agent storage partitioned by agent_id
    # agent_storage = get_pg_agent_storage(storage_config=storage_config, agent_id="my-agent-id")
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

# Import StorageConfig
from packages.shared.src.storage.config import StorageConfig, PrivacyLevel

logger = logging.getLogger(__name__)


def get_cloud_sql_connection(storage_config: StorageConfig) -> sqlalchemy.engine.Engine:
    """
    Create a connection to Cloud SQL using either IAM or password authentication.

    Args:
        storage_config: The StorageConfig instance containing connection details.

    Returns:
        SQLAlchemy engine connected to Cloud SQL
    """
    # Get configuration from StorageConfig (which reads from env vars/defaults)
    project_id = storage_config.get_config_value("GCP_PROJECT_ID", required=True)
    instance_connection_name = storage_config.get_config_value(
        "CLOUD_SQL_INSTANCE_CONNECTION_NAME", required=True
    )
    database = storage_config.get_config_value("CLOUD_SQL_DATABASE", default="phidata")
    user = storage_config.get_config_value("CLOUD_SQL_USER", default="postgres")
    password_secret_name = storage_config.get_config_value(
        "CLOUD_SQL_PASSWORD_SECRET_NAME", default="cloudsql-postgres-password"
    )
    use_iam_auth = (
        storage_config.get_config_value(
            "CLOUD_SQL_USE_IAM_AUTH", default="false"
        ).lower()
        == "true"
    )

    # Create SQL connection using google-cloud-sql-connector
    connector = Connector()

    # Use IAM authentication if enabled
    if use_iam_auth:

        def getconn():
            try:
                logger.info(
                    f"Connecting to Cloud SQL with IAM auth: {instance_connection_name}"
                )
                conn = connector.connect(
                    instance_connection_string=instance_connection_name,
                    driver="pg8000",
                    user=user,
                    db=database,
                    enable_iam_auth=True,
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
            name = (
                f"projects/{project_id}/secrets/{password_secret_name}/versions/latest"
            )
            response = client.access_secret_version(name=name)
            db_password = response.payload.data.decode("UTF-8")

            def getconn():
                try:
                    logger.info(
                        f"Connecting to Cloud SQL with password auth: {instance_connection_name}"
                    )
                    conn = connector.connect(
                        instance_connection_string=instance_connection_name,
                        driver="pg8000",
                        user=user,
                        password=db_password,
                        db=database,
                    )
                    return conn
                except Exception as e:
                    logger.error(
                        f"Error connecting to Cloud SQL with password auth: {e}"
                    )
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


def get_vertexai_embedder(storage_config: StorageConfig) -> VertexAiEmbedder:
    """
    Create a VertexAiEmbedder for vector embeddings.

    Args:
        storage_config: The StorageConfig instance containing embedding details.

    Returns:
        Configured VertexAiEmbedder
    """
    # Get configuration from StorageConfig
    project_id = storage_config.get_config_value("GCP_PROJECT_ID", required=True)
    region = storage_config.get_config_value("GCP_REGION", default="us-central1")
    embedding_model = storage_config.get_config_value(
        "VERTEX_EMBEDDING_MODEL", default="textembedding-gecko@003"
    )

    try:
        # Create the embedder using Vertex AI
        embedder = VertexAiEmbedder(
            model=embedding_model, project_id=project_id, location=region
        )
        logger.info(f"Created VertexAiEmbedder with model: {embedding_model}")
        return embedder
    except Exception as e:
        logger.error(f"Error creating VertexAiEmbedder: {e}")
        raise


def get_pgvector_memory(
    storage_config: StorageConfig,
    user_id: Optional[str] = None,
    table_base_name: str = "pgvector_memory",
    privacy_level: Optional[PrivacyLevel] = None,
) -> PgVector2:
    """
    Get a configured PgVector2 for memory with VertexAI embeddings.

    Args:
        storage_config: The StorageConfig instance.
        user_id: Optional user ID for potential table naming/partitioning.
        table_base_name: The base name for the memory table.
        privacy_level: Optional privacy classification level for the table name.

    Returns:
        Configured PgVector2 instance
    """
    # Get configuration from StorageConfig
    schema_name = storage_config.get_config_value("PG_SCHEMA_NAME", default="llm")
    vector_dimension = int(
        storage_config.get_config_value("EMBEDDING_VECTOR_SIZE", default="768")
    )

    # Create the database connection
    try:
        engine = get_cloud_sql_connection(storage_config)

        # Create the embedder
        embedder = get_vertexai_embedder(storage_config)

        # Configure the table name using StorageConfig's method
        table_name = storage_config.get_collection_name(
            table_base_name,
            privacy_level=privacy_level
            # Note: user_id is not directly used in get_collection_name,
            # but could be incorporated into the base_name or handled by partitioning
        )

        # Create and initialize PgVector2
        vector_store = PgVector2(
            db_engine=engine,
            table_name=table_name,
            schema_name=schema_name,
            embedder=embedder,
            vector_dimension=vector_dimension,
            create_tables=True,  # Auto-create tables if they don't exist
        )

        logger.info(f"Created PgVector2 memory with table: {schema_name}.{table_name}")
        return vector_store
    except Exception as e:
        logger.error(f"Error creating PgVector2 memory: {e}")
        raise


def get_pg_agent_storage(
    storage_config: StorageConfig,
    agent_id: Optional[str] = None,
    table_base_name: str = "agent_storage",
    privacy_level: Optional[PrivacyLevel] = None,
) -> PgAssistantStorage:
    """
    Get a configured PgAssistantStorage for agent data with partitioning.

    Args:
        storage_config: The StorageConfig instance.
        agent_id: Optional agent ID for partitioning.
        table_base_name: The base name for the agent storage table.
        privacy_level: Optional privacy classification level for the table name.

    Returns:
        Configured PgAssistantStorage instance
    """
    # Get configuration from StorageConfig
    schema_name = storage_config.get_config_value("PG_SCHEMA_NAME", default="llm")

    # Create the database connection
    try:
        engine = get_cloud_sql_connection(storage_config)

        # Configure the table name using StorageConfig's method
        table_name = storage_config.get_collection_name(
            table_base_name,
            privacy_level=privacy_level
            # Note: agent_id is not directly used in get_collection_name,
            # but is used by the PgAssistantStorage for partitioning
        )

        # Create and initialize PgAssistantStorage
        agent_storage = PgAssistantStorage(
            db_engine=engine,
            table_name=table_name,
            schema_name=schema_name,
            create_tables=True,
            # Enable partitioning by agent_id if supported
            partitioning_field="agent_id" if agent_id else None,
        )

        logger.info(
            f"Created PgAssistantStorage with table: {schema_name}.{table_name}"
        )
        return agent_storage
    except Exception as e:
        logger.error(f"Error creating PgAssistantStorage: {e}")
        raise
