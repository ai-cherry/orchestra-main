"""
Example of registering a Phidata agent with PostgreSQL/PGVector storage.

This example demonstrates how to register a Phidata agent with enhanced PostgreSQL
storage features, using Cloud SQL for storage and PGVector for vector memory,
with VertexAI textembedding-gecko@003 for embeddings.

Usage:
    python examples/register_phidata_postgres_agent.py
"""

import logging
import os
from typing import Any, Dict, Optional

# Import the agent registry
from packages.agent_registry import get_agent_instance, register_agent
from packages.agent_types import AGENT_TYPE_PHIDATA

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register_phidata_postgres_agent(
    agent_id: str = "phidata-postgres",
    agent_name: str = "PostgreSQL Phidata Agent",
    description: str = "Phidata agent with PostgreSQL/PGVector storage and VertexAI embeddings",
    llm_ref: str = "gpt-4-turbo",  # Reference to preconfigured LLM
    cloud_sql_config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Register a Phidata agent with PostgreSQL storage.

    Args:
        agent_id: Unique identifier for the agent
        agent_name: Human-readable name for the agent
        description: Agent description
        llm_ref: Reference to a preconfigured LLM model
        cloud_sql_config: Optional CloudSQL configuration overrides
    """
    # Set up CloudSQL configuration (or use environment variables)
    if cloud_sql_config is None:
        cloud_sql_config = {
            "project_id": os.environ.get("GCP_PROJECT_ID", "your-project-id"),
            "region": os.environ.get("GCP_REGION", "us-central1"),
            "instance_connection_name": os.environ.get(
                "CLOUD_SQL_INSTANCE_CONNECTION_NAME", ""
            ),
            "database": os.environ.get("CLOUD_SQL_DATABASE", "phidata"),
            "user": os.environ.get("CLOUD_SQL_USER", "postgres"),
            "use_iam_auth": os.environ.get("CLOUD_SQL_USE_IAM_AUTH", "false").lower()
            == "true",
            # Only needed if use_iam_auth is False
            "password_secret_name": os.environ.get(
                "CLOUD_SQL_PASSWORD_SECRET_NAME", "cloudsql-postgres-password"
            ),
        }

    # Define agent configuration
    agent_config = {
        "id": agent_id,
        "name": agent_name,
        "description": description,
        "type": AGENT_TYPE_PHIDATA,
        # Phidata-specific configuration
        "phidata_agent_class": "agno.agent.Agent",  # Use full import path
        "llm_ref": llm_ref,  # Reference to LLM model in Portkey client
        "markdown": True,
        "show_tool_calls": True,
        # CloudSQL configuration
        "cloudsql_config": cloud_sql_config,
        # Storage configuration
        "storage": {
            "table_name": f"{agent_id}_storage",  # PostgreSQL table name for agent storage
            "schema_name": "llm",  # PostgreSQL schema name
        },
        # Memory configuration with PGVector
        "memory": {
            "table_name": f"{agent_id}_memory",  # PostgreSQL table name for vector memory
            "schema_name": "llm",  # PostgreSQL schema name
            "vector_dimension": 768,  # Dimension for textembedding-gecko@003
        },
        # Agent instructions (system prompt)
        "instructions": [
            "You are a helpful AI assistant with access to PostgreSQL database storage.",
            "You can remember conversations and use vector memory for semantic search.",
            "You provide clear, accurate, and helpful responses.",
        ],
        # Tool configurations - add tools as needed
        "tools": [
            # Example tool configuration
            # {
            #     "type": "phi.tools.web.WebSearch",
            #     "params": {
            #         "api_key": os.environ.get("GOOGLE_SEARCH_API_KEY"),
            #         "search_engine_id": os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
            #     }
            # }
        ],
    }

    # Register the agent with the agent registry
    register_agent(agent_config)
    logger.info(
        f"Successfully registered Phidata agent '{agent_name}' with PostgreSQL storage"
    )


def register_phidata_team_with_postgres(
    team_id: str = "postgres-team",
    team_name: str = "PostgreSQL Phidata Team",
    description: str = "Phidata team with Postgres storage and VertexAI embeddings",
    llm_ref: str = "gpt-4-turbo",  # Reference to preconfigured LLM
    cloud_sql_config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Register a Phidata team with PostgreSQL storage.

    Args:
        team_id: Unique identifier for the team
        team_name: Human-readable name for the team
        description: Team description
        llm_ref: Reference to a preconfigured LLM model
        cloud_sql_config: Optional CloudSQL configuration overrides
    """
    # Set up CloudSQL configuration (or use environment variables)
    if cloud_sql_config is None:
        cloud_sql_config = {
            "project_id": os.environ.get("GCP_PROJECT_ID", "your-project-id"),
            "region": os.environ.get("GCP_REGION", "us-central1"),
            "instance_connection_name": os.environ.get(
                "CLOUD_SQL_INSTANCE_CONNECTION_NAME", ""
            ),
            "database": os.environ.get("CLOUD_SQL_DATABASE", "phidata"),
            "user": os.environ.get("CLOUD_SQL_USER", "postgres"),
            "use_iam_auth": os.environ.get("CLOUD_SQL_USE_IAM_AUTH", "false").lower()
            == "true",
            # Only needed if use_iam_auth is False
            "password_secret_name": os.environ.get(
                "CLOUD_SQL_PASSWORD_SECRET_NAME", "cloudsql-postgres-password"
            ),
        }

    # Define team configuration
    team_config = {
        "id": team_id,
        "name": team_name,
        "description": description,
        "type": AGENT_TYPE_PHIDATA,
        # Phidata-specific configuration
        "phidata_agent_class": "agno.team.Team",  # Use Team class
        "llm_ref": llm_ref,  # Default LLM for team members
        "team_model_ref": llm_ref,  # LLM for team coordinator
        "markdown": True,
        "show_tool_calls": True,
        # Team settings
        "team_mode": "coordinate",  # Options: coordinate, collaborate, delegate
        "team_success_criteria": "The task is considered complete when all facts are verified and a comprehensive response is provided.",
        "team_instructions": [
            "You are a team of AI agents working together to solve complex problems.",
            "Coordinate with your team members to provide the most accurate and helpful responses.",
        ],
        # CloudSQL configuration
        "cloudsql_config": cloud_sql_config,
        # Storage configuration for the team
        "storage": {"table_name": f"{team_id}_storage", "schema_name": "llm"},
        # Memory configuration for the team
        "memory": {
            "table_name": f"{team_id}_memory",
            "schema_name": "llm",
            "vector_dimension": 768,
        },
        # Team members configuration
        "members": [
            {
                "name": "Researcher",
                "role": "Researches facts and gathers information",
                "model_ref": llm_ref,  # Use same LLM as team
                "instructions": [
                    "You are a research specialist who excels at finding accurate information.",
                    "Your role is to thoroughly investigate topics and verify facts.",
                ],
                # Member-specific storage (optional - will use team storage if not specified)
                "storage": {"table_name": f"{team_id}_researcher_storage"},
                # Member-specific tools (optional)
                "tools": [
                    # Example tool configuration for researcher
                    # {
                    #     "type": "phi.tools.web.WebSearch",
                    #     "params": {"api_key": "..."}
                    # }
                ],
            },
            {
                "name": "Writer",
                "role": "Crafts clear and well-structured content",
                "model_ref": llm_ref,  # Use same LLM as team
                "instructions": [
                    "You are a content specialist who excels at clear communication.",
                    "Your role is to organize information into well-structured, easy-to-understand content.",
                ],
                # Member-specific storage
                "storage": {"table_name": f"{team_id}_writer_storage"},
            },
            {
                "name": "Reviewer",
                "role": "Reviews content for accuracy and quality",
                "model_ref": llm_ref,  # Use same LLM as team
                "instructions": [
                    "You are a critical reviewer who ensures accuracy and quality.",
                    "Your role is to verify facts, check logical consistency, and improve content quality.",
                ],
                # Member-specific storage
                "storage": {"table_name": f"{team_id}_reviewer_storage"},
            },
        ],
    }

    # Register the team with the agent registry
    register_agent(team_config)
    logger.info(
        f"Successfully registered Phidata team '{team_name}' with PostgreSQL storage"
    )


def test_postgres_agent(agent_id: str = "phidata-postgres") -> None:
    """
    Test the registered PostgreSQL Phidata agent.

    Args:
        agent_id: ID of the registered agent to test
    """
    try:
        # Get an instance of the registered agent
        agent = get_agent_instance(agent_id)

        if agent:
            # Check agent health
            import asyncio

            health_result = asyncio.run(agent.health_check())

            if health_result:
                logger.info(f"✅ Agent '{agent_id}' is healthy and ready!")

                # Example input to test the agent
                from packages.core.src.models import AgentInput

                # Create test input
                test_input = AgentInput(
                    request_id="test-request",
                    prompt="Tell me about PostgreSQL's advantages for storing AI agent data.",
                    user_id="test-user",
                    session_id="test-session",
                )

                # Run the agent
                response = asyncio.run(agent.run(test_input))

                # Print the response
                logger.info(f"Agent Response:\n{response.content}")

            else:
                logger.error(f"❌ Agent '{agent_id}' health check failed")
        else:
            logger.error(f"❌ Failed to get instance of agent '{agent_id}'")

    except Exception as e:
        logger.error(f"❌ Error testing agent '{agent_id}': {e}", exc_info=True)


if __name__ == "__main__":
    # Register a single Phidata agent with PostgreSQL storage
    register_phidata_postgres_agent()

    # Register a Phidata team with PostgreSQL storage
    register_phidata_team_with_postgres()

    # Test the single agent (uncomment to test)
    # test_postgres_agent()

    logger.info("✅ Completed registration of Phidata agents with PostgreSQL storage")
