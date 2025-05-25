"""
Vertex AI Agent Manager for Orchestra.

This module provides functionality to interact with Vertex AI Agents for
automation of infrastructure and operational tasks.
"""

import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

# Google Cloud imports
try:
    import vertexai
    from google.cloud import aiplatform, pubsub_v1, run_v2, secretmanager
    from vertexai.preview import agent_builder
except ImportError:
    logging.warning(
        "Google Cloud libraries not found. Install with: pip install google-cloud-aiplatform google-cloud-pubsub google-cloud-run"
    )
    vertexai = None
    agent_builder = None
    aiplatform = None
    pubsub_v1 = None
    run_v2 = None
    secretmanager = None

# Import GCP authentication utilities
try:
    from packages.shared.src.gcp.auth import get_gcp_credentials, initialize_gcp_auth
except ImportError:
    # Fallback for direct import
    try:
        import os.path
        import sys

        sys.path.append(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        )
        from packages.shared.src.gcp.auth import (
            get_gcp_credentials,
            initialize_gcp_auth,
        )
    except ImportError:
        get_gcp_credentials = None
        initialize_gcp_auth = None
        logging.warning(
            "GCP auth utilities not found. Falling back to default credentials."
        )

# Configure logging
logger = logging.getLogger(__name__)


class VertexAgentManager:
    """
    Manager for interacting with Vertex AI Agents.

    This class provides methods for creating, managing, and executing
    tasks through Vertex AI Agents.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-west2",
        agent_id: Optional[str] = None,
        pubsub_topic: str = "orchestra-bus-dev",
        service_account_json: Optional[str] = None,
    ):
        """
        Initialize the Vertex Agent Manager.

        Args:
            project_id: Google Cloud project ID (will be retrieved from env if not provided)
            location: Google Cloud region
            agent_id: Specific agent ID to use (if None, will use default)
            pubsub_topic: Pub/Sub topic for notifications
            service_account_json: Optional service account JSON key content
        """
        # Get project ID from parameters, environment, or GCP auth utilities
        self.project_id = (
            project_id
            or os.environ.get("GCP_PROJECT_ID")
            or os.environ.get("GOOGLE_CLOUD_PROJECT")
        )
        self.location = location
        self.agent_id = agent_id
        self.pubsub_topic = pubsub_topic
        self.service_account_json = service_account_json or os.environ.get(
            "GCP_SA_KEY_JSON"
        )

        # If we still don't have a project_id, try to get it from credentials
        if not self.project_id and get_gcp_credentials is not None:
            _, detected_project_id = get_gcp_credentials(
                service_account_json=self.service_account_json
            )
            self.project_id = detected_project_id

        # Fall back to hardcoded project ID if all else fails
        if not self.project_id:
            self.project_id = "cherry-ai-project"
            logger.warning(
                f"No project ID provided, falling back to default: {self.project_id}"
            )

        # Set up authentication
        self._setup_auth()

        # Initialize clients
        self._initialize_clients()

        # Get OpenRouter API key
        self.api_key = self._get_secret("openrouter")

    def _setup_auth(self) -> None:
        """Set up GCP authentication for all services."""
        # If we're using the new auth utilities
        if get_gcp_credentials is not None and initialize_gcp_auth is not None:
            try:
                # Initialize GCP auth
                auth_result = initialize_gcp_auth()
                if auth_result["success"]:
                    logger.info(
                        f"GCP authentication initialized using {auth_result['method']} "
                        f"for project {auth_result['project_id']}"
                    )

                    # Update project_id if it wasn't explicitly set
                    if not self.project_id and auth_result["project_id"]:
                        self.project_id = auth_result["project_id"]
                else:
                    logger.warning(
                        "GCP authentication initialization was not successful"
                    )
            except Exception as e:
                logger.error(f"Error setting up GCP authentication: {e}")
                # Continue and try default initialization
        else:
            logger.info("Using default GCP authentication mechanisms")

    def _initialize_clients(self) -> None:
        """Initialize all GCP clients with proper authentication."""
        try:
            # Get credentials if we're using the new auth utilities
            credentials = None
            if get_gcp_credentials is not None and self.service_account_json:
                try:
                    credentials, _ = get_gcp_credentials(
                        service_account_json=self.service_account_json,
                        project_id=self.project_id,
                    )
                    logger.info(
                        "Using explicit service account credentials for GCP clients"
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not get credentials using auth utilities: {e}"
                    )

            # Initialize Vertex AI
            if vertexai is not None:
                vertexai.init(
                    project=self.project_id,
                    location=self.location,
                    credentials=credentials,
                )
                logger.info(
                    f"Vertex AI initialized for project {self.project_id} in {self.location}"
                )
            else:
                logger.warning("Vertex AI library not available")

            # Initialize Pub/Sub publisher
            if pubsub_v1 is not None:
                self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
                self.topic_path = self.publisher.topic_path(
                    self.project_id, self.pubsub_topic
                )
                logger.info(
                    f"Pub/Sub publisher initialized for topic: {self.pubsub_topic}"
                )
            else:
                logger.warning("Pub/Sub library not available")
                self.publisher = None
                self.topic_path = None

            # Initialize Cloud Run client
            if run_v2 is not None:
                self.run_client = run_v2.ServicesClient(credentials=credentials)
                logger.info("Cloud Run client initialized")
            else:
                logger.warning("Cloud Run library not available")
                self.run_client = None

            # Initialize Secret Manager client
            if secretmanager is not None:
                self.secret_client = secretmanager.SecretManagerServiceClient(
                    credentials=credentials
                )
                logger.info("Secret Manager client initialized")
            else:
                logger.warning("Secret Manager library not available")
                self.secret_client = None
        except Exception as e:
            logger.error(f"Error initializing GCP clients: {e}")
            raise

    def _get_secret(self, secret_id: str) -> str:
        """
        Get a secret from Secret Manager.

        Args:
            secret_id: ID of the secret to retrieve

        Returns:
            Secret value as a string
        """
        if not self.secret_client:
            logger.warning(
                f"Secret Manager client not initialized, cannot retrieve secret: {secret_id}"
            )
            return ""

        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        try:
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Error accessing secret {secret_id}: {e}")
            return ""

    def get_or_create_agent(
        self,
        display_name: str = "DevOps Bot",
        description: str = "Orchestra DevOps Agent",
    ) -> Any:
        """
        Get or create a Vertex AI Agent.

        Args:
            display_name: Display name for the agent
            description: Description of the agent

        Returns:
            Vertex AI Agent instance
        """
        if agent_builder is None:
            logger.error("Vertex AI Agent Builder library not available")
            raise ImportError("Vertex AI Agent Builder library not available")

        try:
            # Try to get existing agent by ID if provided
            if self.agent_id:
                return agent_builder.Agent.get(agent_id=self.agent_id)

            # List agents and find by display name
            agents = agent_builder.Agent.list()
            for agent in agents:
                if agent.display_name == display_name:
                    self.agent_id = agent.id
                    return agent

            # Create a new agent if not found
            new_agent = agent_builder.Agent.create(
                display_name=display_name, description=description
            )
            self.agent_id = new_agent.id
            logger.info(
                f"Created new Vertex AI Agent: {display_name} (ID: {self.agent_id})"
            )
            return new_agent
        except Exception as e:
            logger.error(f"Error getting or creating agent: {e}")
            raise

    def run_init_script(self) -> Dict[str, Any]:
        """
        Run initialization script safely without command injection vulnerabilities.

        Returns:
            Dictionary with status and output
        """
        logger.info("Running initialization script")
        try:
            # Create the non-interactive script content
            non_interactive_script = "\n".join(
                [
                    "#!/bin/bash",
                    "set -euo pipefail",  # Exit on error, undefined vars, pipe failures
                    "",
                    "# Non-interactive initialization for Vertex AI DevOps Agent",
                    "export DEBIAN_FRONTEND=noninteractive",
                    "export SETUP_VERTEX=y",
                    "",
                    "# Add your actual initialization logic here",
                    "echo 'Initialization script running...'",
                    "echo 'Setup complete!'",
                ]
            )

            # Write script to a temporary file with secure permissions
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
                temp_script_path = f.name
                f.write(non_interactive_script)

            # Set executable permissions
            os.chmod(temp_script_path, 0o755)

            try:
                # Run the script using secure subprocess call
                result = subprocess.run(
                    ["bash", temp_script_path],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                # Clean up
                os.remove(temp_script_path)

                if result.returncode == 0:
                    logger.info("Initialization script completed successfully")
                    return {"status": "success", "output": result.stdout}
                else:
                    logger.error(f"Initialization script failed: {result.stderr}")
                    return {
                        "status": "failed",
                        "error": result.stderr,
                        "output": result.stdout,
                    }

            except subprocess.TimeoutExpired:
                os.remove(temp_script_path)
                return {"status": "failed", "error": "Initialization script timed out"}
            except Exception as e:
                if os.path.exists(temp_script_path):
                    os.remove(temp_script_path)
                raise e

        except Exception as e:
            logger.error(f"Error running initialization script: {e}")
            return {"status": "failed", "error": str(e)}

    def apply_terraform(self, workspace: str) -> Dict[str, Any]:
        """
        Apply Terraform configuration for a specific workspace.

        Args:
            workspace: Terraform workspace (dev, stage, prod)

        Returns:
            Dictionary with status and any output
        """
        logger.info(f"Applying Terraform configuration for workspace: {workspace}")

        # Validate workspace name to prevent injection
        if not workspace.isalnum():
            logger.error(
                f"Invalid workspace name: {workspace}. Only alphanumeric characters allowed."
            )
            return {
                "status": "failed",
                "workspace": workspace,
                "error": "Invalid workspace name",
            }

        try:
            # Change to the infra directory
            original_dir = os.getcwd()
            os.chdir("infra")

            # Select the workspace using secure subprocess calls
            try:
                result = subprocess.run(
                    ["terraform", "workspace", "select", workspace],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode != 0:
                    # Create the workspace if it doesn't exist
                    subprocess.run(
                        ["terraform", "workspace", "new", workspace],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=True,
                    )
                    subprocess.run(
                        ["terraform", "workspace", "select", workspace],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=True,
                    )

                # Run terraform plan
                plan_result = subprocess.run(
                    ["terraform", "plan", f"-var=env={workspace}", "-out=tfplan"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if plan_result.returncode != 0:
                    logger.error(f"Terraform plan failed: {plan_result.stderr}")
                    return {
                        "status": "failed",
                        "workspace": workspace,
                        "error": f"Plan failed: {plan_result.stderr}",
                    }

                # Apply the plan
                apply_result = subprocess.run(
                    ["terraform", "apply", "-auto-approve", f"-var=env={workspace}"],
                    capture_output=True,
                    text=True,
                    timeout=600,
                )

                # Change back to the original directory
                os.chdir(original_dir)

                if apply_result.returncode == 0:
                    logger.info(
                        f"Terraform apply completed successfully for {workspace}"
                    )
                    return {
                        "status": "success",
                        "workspace": workspace,
                        "output": apply_result.stdout,
                    }
                else:
                    logger.error(
                        f"Terraform apply failed for {workspace}: {apply_result.stderr}"
                    )
                    return {
                        "status": "failed",
                        "workspace": workspace,
                        "error": apply_result.stderr,
                    }

            except subprocess.TimeoutExpired:
                os.chdir(original_dir)
                return {
                    "status": "failed",
                    "workspace": workspace,
                    "error": "Terraform operation timed out",
                }
            except subprocess.CalledProcessError as e:
                os.chdir(original_dir)
                return {
                    "status": "failed",
                    "workspace": workspace,
                    "error": f"Terraform command failed: {e.stderr}",
                }

        except Exception as e:
            if "original_dir" in locals():
                os.chdir(original_dir)
            logger.error(f"Error applying Terraform: {e}")
            return {"status": "failed", "workspace": workspace, "error": str(e)}

    def create_agent_team(self, team_name: str, roles: List[str]) -> Dict[str, Any]:
        """
        Create and deploy an agent team.

        Args:
            team_name: Name of the team
            roles: List of roles for the team members

        Returns:
            Dictionary with status and deployment info
        """
        logger.info(f"Creating agent team: {team_name} with roles: {roles}")
        try:
            # Create directory structure
            team_path = f"packages/agents/{team_name.lower()}"
            os.makedirs(team_path, exist_ok=True)

            # Create __init__.py
            with open(f"{team_path}/__init__.py", "w") as f:
                f.write(f'"""\n{team_name.capitalize()} agent team module.\n"""\n\n')

            # Generate agent code for each role
            for role in roles:
                agent_type = role.lower()
                domain = team_name.lower()

                code_snippet = f'''"""
{role.capitalize()} agent for {team_name.capitalize()} team.
"""

import logging
from core.orchestrator.src.agents.agent_base import AgentContext, AgentResponse

logger = logging.getLogger(__name__)

class {role.capitalize()}Agent:
    """
    {role.capitalize()} agent for {team_name.capitalize()} team.

    This agent is responsible for {role.lower()} tasks in the
    {team_name.capitalize()} domain.
    """

    def __init__(self):
        """Initialize the {role.capitalize()} agent."""
        self.domain = "{domain}"
        self.role = "{role}"

    async def execute(self, context: AgentContext) -> AgentResponse:
        """
        Execute a task using this agent.

        Args:
            context: Context information for the agent

        Returns:
            Agent response
        """
        logger.info(f"{{self.role}} agent in {{self.domain}} team executing: {{context.task}}")

        # Placeholder implementation
        return AgentResponse(
            success=True,
            message=f"{{self.role}} agent in {{self.domain}} team executed: {{context.task}}",
            data={{
                "domain": self.domain,
                "role": self.role,
                "task": context.task
            }}
        )
'''

                agent_file = f"{team_path}/{agent_type}_agent.py"
                with open(agent_file, "w") as f:
                    f.write(code_snippet)

                logger.info(f"Generated {role} agent code: {agent_file}")

            # Create Docker build files
            dockerfile_content = f"""FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV ENVIRONMENT=development

EXPOSE 8080

CMD ["python", "-m", "packages.agents.{team_name.lower()}.server"]
"""

            with open(f"{team_path}/Dockerfile", "w") as f:
                f.write(dockerfile_content)

            # Create server file
            server_content = f'''"""
Server for {team_name.capitalize()} agent team.
"""

import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import agents
from .planner_agent import PlannerAgent
from .doer_agent import DoerAgent
from .reviewer_agent import ReviewerAgent

# Create FastAPI app
app = FastAPI(title="{team_name.capitalize()} Agent Team")

class TaskRequest(BaseModel):
    """Task request schema."""
    task: str
    context: dict = {{}}

@app.post("/execute")
async def execute_task(request: TaskRequest):
    """Execute a task with the agent team."""
    logger.info(f"Received task: {{request.task}}")

    # Create instances of the agents
    planner = PlannerAgent()
    doer = DoerAgent()
    reviewer = ReviewerAgent()

    # Execute the task with each agent in sequence
    try:
        # First, plan the task
        from core.orchestrator.src.agents.agent_base import AgentContext
        context = AgentContext(task=request.task, data=request.context)

        plan_response = await planner.execute(context)
        if not plan_response.success:
            return {{"success": False, "error": "Planning failed", "details": plan_response.message}}

        # Update context with planning results
        context.data["plan"] = plan_response.data

        # Execute the plan
        do_response = await doer.execute(context)
        if not do_response.success:
            return {{"success": False, "error": "Execution failed", "details": do_response.message}}

        # Update context with execution results
        context.data["execution"] = do_response.data

        # Review the results
        review_response = await reviewer.execute(context)

        return {{
            "success": True,
            "result": {{
                "plan": plan_response.data,
                "execution": do_response.data,
                "review": review_response.data,
                "final_status": review_response.success
            }}
        }}
    except Exception as e:
        logger.error(f"Error executing task: {{e}}")
        return {{"success": False, "error": str(e)}}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy", "team": "{team_name}"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
'''

            with open(f"{team_path}/server.py", "w") as f:
                f.write(server_content)

            # Create requirements.txt
            with open(f"{team_path}/requirements.txt", "w") as f:
                f.write("fastapi>=0.95.0\nuvicorn>=0.21.0\npydantic>=1.10.7\n")

            logger.info(f"Created agent team: {team_name}")

            # Use Cloud Run API to deploy the team
            # Note: In a real implementation, we would build and push
            # the Docker image before deploying to Cloud Run

            # Publish notification to Pub/Sub
            message = json.dumps(
                {
                    "type": "agent_team_created",
                    "team": team_name,
                    "roles": roles,
                    "status": "created",
                }
            ).encode("utf-8")

            future = self.publisher.publish(self.topic_path, message)
            message_id = future.result()

            return {
                "status": "success",
                "team": team_name,
                "roles": roles,
                "files_created": [
                    f"{team_path}/{role.lower()}_agent.py" for role in roles
                ],
                "message_id": message_id,
            }
        except Exception as e:
            logger.error(f"Error creating agent team: {e}")
            return {"status": "failed", "team": team_name, "error": str(e)}

    def manage_embeddings(self, data: str, index_name: str) -> Dict[str, Any]:
        """
        Manage embeddings in Vertex AI Vector Search.

        Args:
            data: Data to embed
            index_name: Vector index name

        Returns:
            Dictionary with status and results
        """
        logger.info(f"Managing embeddings for index: {index_name}")
        try:
            # Create a mock embedding for demonstration purposes
            # In a real application, you would use OpenRouter or another
            # embedding model to generate the actual embedding
            embedding = [0.1] * 768  # Example 768-dimensional embedding

            # Get the index endpoint
            try:
                index_endpoint = aiplatform.MatchingEngineIndexEndpoint(
                    index_endpoint_name=f"projects/{self.project_id}/locations/{self.location}/indexEndpoints/{index_name}"
                )
            except Exception as e:
                logger.error(f"Error getting index endpoint: {e}")
                return {
                    "status": "failed",
                    "error": f"Index endpoint not found: {str(e)}",
                }

            # Upsert the embedding
            try:
                datapoints = [
                    {
                        "id": f"data_{hash(data) % 10000}",
                        "feature_vector": embedding,
                        "restricts": [{"namespace": "env", "allow_list": ["dev"]}],
                    }
                ]

                response = index_endpoint.upsert_datapoints(datapoints=datapoints)
                logger.info(f"Upserted embedding to index: {index_name}")
            except Exception as e:
                logger.error(f"Error upserting embedding: {e}")
                return {
                    "status": "failed",
                    "error": f"Failed to upsert embedding: {str(e)}",
                }

            # Perform a search query
            try:
                query_embedding = embedding  # Use the same embedding for testing
                search_results = index_endpoint.find_neighbors(
                    queries=[query_embedding], num_neighbors=5
                )

                result_summary = []
                for idx, neighbors in enumerate(search_results):
                    for neighbor in neighbors:
                        result_summary.append(
                            {"id": neighbor.id, "distance": neighbor.distance}
                        )

                logger.info(f"Search results: {result_summary}")
            except Exception as e:
                logger.error(f"Error searching embeddings: {e}")
                return {
                    "status": "partial_success",
                    "error": f"Embedding upserted but search failed: {str(e)}",
                    "upsert_response": str(response),
                }

            # Publish notification to Pub/Sub
            message = json.dumps(
                {
                    "type": "embeddings_managed",
                    "index": index_name,
                    "operation": "upsert_and_search",
                    "search_results": result_summary,
                }
            ).encode("utf-8")

            future = self.publisher.publish(self.topic_path, message)
            message_id = future.result()

            return {
                "status": "success",
                "index": index_name,
                "search_results": result_summary,
                "message_id": message_id,
            }
        except Exception as e:
            logger.error(f"Error managing embeddings: {e}")
            return {"status": "failed", "index": index_name, "error": str(e)}

    def manage_game_session(
        self, game_type: str, session_id: str, player_action: str
    ) -> Dict[str, Any]:
        """
        Manage a live game session.

        Args:
            game_type: Type of game (e.g., trivia, word_game)
            session_id: Unique session identifier
            player_action: Action taken by the player

        Returns:
            Dictionary with status and game state
        """
        logger.info(
            f"Managing game session: {game_type}/{session_id}, action: {player_action}"
        )
        try:
            # In a real implementation, you would store and retrieve
            # game state from Firestore or another database

            # Simulate game state for demonstration purposes
            game_state = {
                "session_id": session_id,
                "game_type": game_type,
                "players": ["player1", "player2"],
                "current_action": player_action,
                "current_round": 1,
                "scores": {"player1": 0, "player2": 0},
                "response": f"Cherry says: Great move, '{player_action}'! Next player, make your choice!",
            }

            # Generate a game event based on the action
            # In a real implementation, you would have game logic here
            if game_type == "trivia":
                if player_action.startswith("answer_"):
                    # Simulate correct answer for answer_a
                    is_correct = player_action == "answer_a"
                    if is_correct:
                        game_state["scores"]["player1"] += 10
                        game_state["response"] = (
                            "Cherry says: That's correct! You earned 10 points!"
                        )
                    else:
                        game_state["response"] = (
                            "Cherry says: Sorry, that's incorrect. The correct answer was A."
                        )
            elif game_type == "word_game":
                # Simple word game logic
                word_length = len(player_action)
                game_state["scores"]["player1"] += word_length
                game_state["response"] = (
                    f"Cherry says: Nice word worth {word_length} points!"
                )

            # Increment the round
            game_state["current_round"] += 1

            # Publish game state to Pub/Sub
            message = json.dumps(
                {
                    "type": "game_update",
                    "game_type": game_type,
                    "session_id": session_id,
                    "state": game_state,
                }
            ).encode("utf-8")

            future = self.publisher.publish(self.topic_path, message)
            message_id = future.result()

            return {
                "status": "success",
                "session": game_state,
                "message_id": message_id,
            }
        except Exception as e:
            logger.error(f"Error managing game session: {e}")
            return {"status": "failed", "error": str(e)}

    def monitor_resources(self) -> Dict[str, Any]:
        """
        Monitor GCP resource usage and costs.

        Returns:
            Dictionary with status and monitoring data
        """
        logger.info("Monitoring GCP resources")
        try:
            # In a real implementation, you would use the Cloud Monitoring API
            # to collect metrics and the Billing API to get cost information

            # Simulate monitoring data for demonstration purposes
            monitoring_data = {
                "resources": {
                    "cloud_run": {
                        "instances": 2,
                        "cpu_utilization": 0.35,
                        "memory_utilization": 0.42,
                    },
                    "firestore": {"read_ops": 1250, "write_ops": 420, "delete_ops": 30},
                    "pubsub": {"topics": 3, "subscriptions": 5, "message_count": 1580},
                    "vertex_ai": {"vector_searches": 340, "embeddings_generated": 120},
                },
                "costs": {
                    "estimated_daily": 4.75,
                    "estimated_monthly": 142.50,
                    "breakdown": {
                        "cloud_run": 1.20,
                        "firestore": 0.85,
                        "pubsub": 0.10,
                        "vertex_ai": 2.40,
                        "other": 0.20,
                    },
                },
            }

            # Publish monitoring data to Pub/Sub
            message = json.dumps(
                {
                    "type": "resource_monitoring",
                    "timestamp": None,  # would be current timestamp
                    "data": monitoring_data,
                }
            ).encode("utf-8")

            future = self.publisher.publish(self.topic_path, message)
            message_id = future.result()

            return {
                "status": "success",
                "monitoring_data": monitoring_data,
                "message_id": message_id,
            }
        except Exception as e:
            logger.error(f"Error monitoring resources: {e}")
            return {"status": "failed", "error": str(e)}


def trigger_vertex_task(task: str, **kwargs) -> Dict[str, Any]:
    """
    Trigger a task to be executed by the Vertex AI Agent.

    Args:
        task: Task identifier
        **kwargs: Additional arguments for the task

    Returns:
        Result of the task execution
    """
    logger.info(f"Triggering Vertex AI task: {task}")

    try:
        # Create manager instance
        manager = VertexAgentManager()

        # Determine which task to execute
        if task == "run init script":
            return manager.run_init_script()
        elif task.startswith("apply terraform"):
            _, _, workspace = task.split()
            return manager.apply_terraform(workspace)
        elif task.startswith("create agent team"):
            parts = task.split(maxsplit=2)
            if len(parts) < 3:
                return {"status": "failed", "error": "Missing team name"}
            team_name = parts[2]
            roles = kwargs.get("roles", ["planner", "doer", "reviewer"])
            return manager.create_agent_team(team_name, roles)
        elif task.startswith("manage embeddings"):
            parts = task.split(maxsplit=2)
            if len(parts) < 3:
                return {"status": "failed", "error": "Missing index name"}
            index_name = parts[2]
            data = kwargs.get("data", "Sample data for embedding")
            return manager.manage_embeddings(data, index_name)
        elif task.startswith("manage game session"):
            parts = task.split(maxsplit=4)
            if len(parts) < 5:
                return {"status": "failed", "error": "Missing game parameters"}
            game_type, session_id, player_action = parts[2], parts[3], parts[4]
            return manager.manage_game_session(game_type, session_id, player_action)
        elif task == "monitor resources":
            return manager.monitor_resources()
        else:
            return {"status": "failed", "error": f"Unknown task: {task}"}
    except Exception as e:
        logger.error(f"Error triggering task: {e}")
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Vertex AI Agent Manager CLI")
    parser.add_argument("task", help="Task to execute")
    parser.add_argument("--workspace", help="Terraform workspace")
    parser.add_argument("--team", help="Agent team name")
    parser.add_argument("--roles", nargs="+", help="Team roles")
    parser.add_argument("--game-type", help="Game type")
    parser.add_argument("--session-id", help="Game session ID")
    parser.add_argument("--player-action", help="Player action")
    parser.add_argument("--index-name", help="Vector index name")
    parser.add_argument("--data", help="Data for embedding")

    args = parser.parse_args()

    # Construct the task string
    task_str = args.task
    if args.task == "apply terraform" and args.workspace:
        task_str = f"apply terraform {args.workspace}"
    elif args.task == "create agent team" and args.team:
        task_str = f"create agent team {args.team}"
    elif args.task == "manage embeddings" and args.index_name:
        task_str = f"manage embeddings {args.index_name}"
    elif (
        args.task == "manage game session"
        and args.game_type
        and args.session_id
        and args.player_action
    ):
        task_str = f"manage game session {args.game_type} {args.session_id} {args.player_action}"

    # Prepare kwargs
    kwargs = {}
    if args.roles:
        kwargs["roles"] = args.roles
    if args.data:
        kwargs["data"] = args.data

    # Trigger the task
    result = trigger_vertex_task(task_str, **kwargs)
    print(json.dumps(result, indent=2))
