import importlib
import logging
from typing import Any, Dict

from phidata.utils.log import logger

# Placeholder for actual MemoryManager, PortkeyClient, ToolRegistry if they are external or defined elsewhere
# If they are part of this project, ensure correct import paths.
# from missing_module import MemoryManager, PortkeyClient, ToolRegistry
# from missing_module import get_pg_agent_storage, get_pgvector_memory

class MemoryManager:
    pass

class PortkeyClient:
    pass

class ToolRegistry:
    pass

def get_pg_agent_storage():
    pass

def get_pgvector_memory():
    pass

# Initialize logger if not already done by phidata.utils.log
if not hasattr(logger, "info"):  # Basic check if logger is configured
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)  # Basic config

def __init__(
    self,
    agent_config: Dict[str, Any],
    memory_manager: MemoryManager,
    llm_client: PortkeyClient,
    tool_registry: ToolRegistry,
):
    """
    """
        agno_team = importlib.import_module("agno.team")
        agno_agent = importlib.import_module("agno.agent")
        Team = getattr(agno_team, "Team")
        Agent = getattr(agno_agent, "Agent")
    except Exception:

        pass
        logger.error(f"Failed to import Phidata/Agno modules: {e}")
        raise ImportError(f"Phidata/Agno modules not available: {e}")

    # Parse team configuration from agent_config
    self.team_config = agent_config["phidata_hn_team"]

    # Extract team settings
    self.team_name = self.team_config.get("name", "HN Analysis Team")
    self.team_mode = self.team_config.get("team_mode", "coordinate")
    self.team_model_ref = self.team_config.get("team_model_ref")
    self.team_instructions = self.team_config.get("team_instructions", [])
    self.team_success_criteria = self.team_config.get("team_success_criteria", "")
    self.team_markdown = self.team_config.get("markdown", True)

    # Extract members configuration
    self.members_config = self.team_config.get("members", [])
    if not self.members_config:
        raise ValueError("PhidataAgentWrapper with Team requires 'members' in config")

    # Initialize storage and memory configurations
    self._init_storage_and_memory()

    # Initialize team members
    members = []
    for member_config in self.members_config:
        # Extract member-specific configuration
        name = member_config.get("name")
        role = member_config.get("role", "")
        instructions = member_config.get("instructions", [])
        member_llm_ref = member_config.get("llm_ref", self.team_config.get("default_llm_ref"))
        tools_config = member_config.get("tools", [])

        if not name:
            logger.error("Member config missing required 'name' field")
            continue

        if not member_llm_ref:
            logger.error(f"Member '{name}' missing llm_ref and no default_llm_ref provided")
            continue

        # Get the LLM model for this member from Portkey client
        try:

            pass
            member_model = self._get_llm_from_ref(member_llm_ref)
        except Exception:

            pass
            logger.error(f"Failed to get LLM for member '{name}': {e}")
            continue

        # Initialize tools for this member
        member_tools = []
        for tool_config in tools_config:
            try:

                pass
                # Process tool configuration
                tool_type = tool_config.get("type")
                tool_params = tool_config.get("params", {})

                if not tool_type:
                    logger.warning(f"Skipping tool config without 'type' for member '{name}'")
                    continue

                # Handle registry tools
                if tool_type.startswith("registry:"):
                    tool_id = tool_type.replace("registry:", "").strip()
                    cherry_ai_tool = self.tools.get_tool(tool_id)
                    if cherry_ai_tool and hasattr(cherry_ai_tool, "to_phidata_tool"):
                        phidata_tool = cherry_ai_tool.to_phidata_tool(**tool_params)
                        if phidata_tool:
                            member_tools.append(phidata_tool)
                            logger.info(f"Added registry tool '{tool_id}' to member '{name}'")
                    continue

                # Handle direct tool class references
                module_path, class_name = tool_type.rsplit(".", 1)
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)
                tool_instance = tool_class(**tool_params)

                # Set custom name if provided
                if "name" in tool_config:
                    tool_instance.name = tool_config["name"]

                member_tools.append(tool_instance)
                logger.info(f"Added tool '{tool_type}' to member '{name}'")

            except Exception:


                pass
                logger.error(f"Failed to initialize tool for member '{name}': {e}")

        # Setup member-specific storage/memory or use team's
        member_storage = self.agent_storage
        member_memory = self.agent_memory

        # Use member-specific storage if configured
        if "storage" in member_config:
            storage_table = member_config["storage"].get("table_name", f"{name.lower()}_storage")
            cloudsql_config = self.team_config.get("cloudsql_config", {})

            try:


                pass
                member_storage = get_pg_agent_storage(
                    agent_id=f"{self.id}_{name.lower()}",
                    config=cloudsql_config,
                    table_name=storage_table,
                )
                logger.info(f"Initialized member-specific storage for '{name}'")
            except Exception:

                pass
                logger.error(f"Failed to initialize storage for member '{name}': {e}")

        # Use member-specific memory if configured
        if "memory" in member_config:
            memory_table = member_config["memory"].get("table_name", f"{name.lower()}_memory")
            cloudsql_config = self.team_config.get("cloudsql_config", {})

            try:


                pass
                member_memory = get_pgvector_memory(
                    user_id=f"{self.id}_{name.lower()}",
                    config=cloudsql_config,
                    table_name=memory_table,
                )
                logger.info(f"Initialized member-specific memory for '{name}'")
            except Exception:

                pass
                logger.error(f"Failed to initialize memory for member '{name}': {e}")

        # Create the member Agent
        try:

            pass
            member_agent = Agent(
                model=member_model,
                tools=member_tools,
                instructions=instructions,
                name=name,
                role=role,
                markdown=member_config.get("markdown", self.team_markdown),
                show_tool_calls=member_config.get("show_tool_calls", True),
                storage=member_storage,
                memory=member_memory,
            )

            members.append(member_agent)
            logger.info(f"Initialized team member: '{name}' with role '{role}'")
        except Exception:

            pass
            logger.error(f"Failed to initialize team member '{name}': {e}")

    # Ensure we have at least one member
    if not members:
        raise ValueError("Failed to initialize any team members")

    # Get the team model
    team_model = self._get_llm_from_ref(self.team_model_ref)

    # Finally, initialize the Team with all members
    try:

        pass
        self.phidata_agent = Team(
            members=members,
            model=team_model,
            mode=self.team_mode,
            success_criteria=self.team_success_criteria,
            instructions=self.team_instructions,
            markdown=self.team_markdown,
            name=self.team_name,
            storage=self.agent_storage,
            memory=self.agent_memory,
        )
        logger.info(f"Successfully initialized Phidata Team '{self.team_name}' with {len(members)} members")
    except Exception:

        pass
        logger.error(f"Failed to initialize Phidata Team: {e}")
        raise RuntimeError(f"Failed to initialize Phidata Team: {e}")
