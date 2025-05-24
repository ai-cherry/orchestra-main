"""
Implementation of the PhidataAgentWrapper's __init__ method for instantiating
an agno.team.Team based on the phidata_hn_team configuration.

This code snippet shows how to parse members from the config, instantiate each
member Agent with its specific tools and model (via llm_ref), and then
instantiate the Team with these members, team mode, team model, etc.
"""

import logging
import importlib
from typing import Any, Dict, List

from packages.memory.src.base import MemoryManager
from packages.llm.src.portkey_client import PortkeyClient
from packages.tools.src.base import ToolRegistry
from packages.phidata.src.cloudsql_pgvector import (
    get_pg_agent_storage,
    get_pgvector_memory,
)

logger = logging.getLogger(__name__)


class PhidataAgentWrapper:
    def __init__(
        self,
        agent_config: Dict[str, Any],
        memory_manager: MemoryManager,
        llm_client: PortkeyClient,
        tool_registry: ToolRegistry,
    ):
        """
        Initialize the PhidataAgentWrapper specifically for a Hacker News team configuration.

        This method instantiates an agno.team.Team based on the phidata_hn_team configuration
        from the agent_config dictionary.

        Args:
            agent_config: Agent configuration containing phidata_hn_team settings
            memory_manager: Orchestra's memory management system
            llm_client: Configured LLM provider client (Portkey)
            tool_registry: Access to registered system tools
        """
        # Store base properties necessary for the wrapper
        self.agent_config = agent_config
        self.memory = memory_manager
        self.llm = llm_client
        self.tools = tool_registry

        # Extract agent identification information
        self.id = agent_config.get("id", "phidata_team_agent")
        self.name = agent_config.get("name", "Phidata Team Agent")

        # Set flag indicating this is a Team
        self._is_team = True

        # Import required Phidata/Agno modules
        try:
            agno_team = importlib.import_module("agno.team")
            agno_agent = importlib.import_module("agno.agent")
            Team = getattr(agno_team, "Team")
            Agent = getattr(agno_agent, "Agent")
        except ImportError as e:
            logger.error(f"Failed to import Phidata/Agno modules: {e}")
            raise ImportError(f"Phidata/Agno modules not available: {e}")

        # Extract the phidata_hn_team configuration
        if "phidata_hn_team" not in agent_config:
            raise ValueError("Missing 'phidata_hn_team' configuration in agent_config")

        team_config = agent_config["phidata_hn_team"]

        # Extract team-level settings
        team_name = team_config.get("name", "HN Analysis Team")
        team_mode = team_config.get("team_mode", "coordinate")  # "coordinate", "collaborate", etc.
        team_model_ref = team_config.get("team_model_ref")
        team_instructions = team_config.get("team_instructions", [])
        team_success_criteria = team_config.get("team_success_criteria", "")
        team_markdown = team_config.get("markdown", True)

        # Set up shared storage and memory for the team
        cloudsql_config = team_config.get("cloudsql_config", {})

        # Initialize team-level storage and memory
        storage_table = team_config.get("storage", {}).get("table_name", f"{self.id}_storage")
        memory_table = team_config.get("memory", {}).get("table_name", f"{self.id}_memory")

        # Set up PgAgentStorage for conversation history
        self.agent_storage = get_pg_agent_storage(agent_id=self.id, config=cloudsql_config, table_name=storage_table)
        logger.info(f"Initialized team storage with table: {storage_table}")

        # Set up PgVector for memory/knowledge
        self.agent_memory = get_pgvector_memory(
            user_id=team_config.get("default_user_id", self.id),
            config=cloudsql_config,
            table_name=memory_table,
        )
        logger.info(f"Initialized team memory with table: {memory_table}")

        # Get the members list from configuration
        members_config = team_config.get("members", [])
        if not members_config:
            raise ValueError("PhidataAgentWrapper with Team requires 'members' in config")

        # Initialize each team member agent
        members = []
        for member_config in members_config:
            # Extract member-specific settings
            name = member_config.get("name")
            role = member_config.get("role", "")
            instructions = member_config.get("instructions", [])

            # Get member's model reference, use team's default if not specified
            member_llm_ref = member_config.get("llm_ref", team_config.get("default_llm_ref"))

            if not name:
                logger.warning("Member config missing required 'name' field, skipping")
                continue

            if not member_llm_ref:
                logger.warning(f"Member '{name}' missing llm_ref and no default_llm_ref provided, skipping")
                continue

            try:
                # Get the actual LLM model from the client using the reference
                member_model = self._get_llm_model(member_llm_ref)

                # Initialize member-specific tools
                member_tools = self._init_member_tools(member_config.get("tools", []), name)

                # Set up member-specific storage and memory if configured
                member_storage = self._init_member_storage(member_config, name, cloudsql_config)
                member_memory = self._init_member_memory(member_config, name, cloudsql_config)

                # Create the Agent instance for this team member
                member_agent = Agent(
                    model=member_model,
                    tools=member_tools,
                    instructions=instructions,
                    name=name,
                    role=role,
                    markdown=member_config.get("markdown", team_markdown),
                    show_tool_calls=member_config.get("show_tool_calls", True),
                    storage=member_storage,
                    memory=member_memory,
                )

                members.append(member_agent)
                logger.info(f"Initialized team member: {name} with role: {role}")

            except Exception as e:
                logger.error(f"Failed to initialize team member '{name}': {e}")
                # Continue with other members even if one fails

        # Ensure we have at least one member
        if not members:
            raise ValueError("Failed to initialize any team members")

        # Get the team's language model
        if not team_model_ref:
            raise ValueError("Missing 'team_model_ref' in team configuration")

        team_model = self._get_llm_model(team_model_ref)

        # Finally, instantiate the Team with all configured members
        self.phidata_agent = Team(
            members=members,
            model=team_model,
            mode=team_mode,
            success_criteria=team_success_criteria,
            instructions=team_instructions,
            markdown=team_markdown,
            name=team_name,
            storage=self.agent_storage,
            memory=self.agent_memory,
        )

        logger.info(f"Successfully initialized Phidata Team '{team_name}' with {len(members)} members")

    def _get_llm_model(self, model_ref: str) -> Any:
        """
        Get the LLM model from the Portkey client using the reference name.

        Args:
            model_ref: Reference name for the model in the Portkey client

        Returns:
            LLM model instance
        """
        if not hasattr(self.llm, model_ref):
            raise ValueError(f"LLM reference '{model_ref}' not found in LLM client")

        return getattr(self.llm, model_ref)

    def _init_member_tools(self, tools_config: List[Dict], member_name: str) -> List:
        """
        Initialize tools for a team member based on configuration.

        Args:
            tools_config: List of tool configurations
            member_name: Name of the member for logging

        Returns:
            List of initialized tool instances
        """
        member_tools = []

        for tool_config in tools_config:
            try:
                tool_type = tool_config.get("type")
                tool_params = tool_config.get("params", {})
                tool_name = tool_config.get("name")

                if not tool_type:
                    logger.warning(f"Skipping tool config without 'type' for member '{member_name}'")
                    continue

                # Handle tools from the registry
                if tool_type.startswith("registry:"):
                    tool_id = tool_type.replace("registry:", "").strip()
                    orchestra_tool = self.tools.get_tool(tool_id)

                    if orchestra_tool and hasattr(orchestra_tool, "to_phidata_tool"):
                        phidata_tool = orchestra_tool.to_phidata_tool(**tool_params)
                        if phidata_tool:
                            member_tools.append(phidata_tool)
                            logger.info(f"Added registry tool '{tool_id}' to member '{member_name}'")
                    continue

                # Handle direct tool class references
                module_path, class_name = tool_type.rsplit(".", 1)
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)
                tool_instance = tool_class(**tool_params)

                # Set custom name if provided
                if tool_name and hasattr(tool_instance, "name"):
                    tool_instance.name = tool_name

                member_tools.append(tool_instance)
                logger.info(f"Added tool '{tool_type}' to member '{member_name}'")

            except Exception as e:
                logger.error(f"Failed to initialize tool for member '{member_name}': {e}")
                # Continue with other tools even if one fails

        return member_tools

    def _init_member_storage(self, member_config: Dict, member_name: str, cloudsql_config: Dict) -> Any:
        """
        Initialize member-specific storage or use team's shared storage.

        Args:
            member_config: Configuration for the team member
            member_name: Name of the team member
            cloudsql_config: CloudSQL configuration

        Returns:
            Storage instance
        """
        # By default, use the team's storage
        storage = self.agent_storage

        # Set up member-specific storage if configured
        if "storage" in member_config:
            storage_table = member_config["storage"].get("table_name", f"{member_name.lower()}_storage")

            try:
                storage = get_pg_agent_storage(
                    agent_id=f"{self.id}_{member_name.lower()}",
                    config=cloudsql_config,
                    table_name=storage_table,
                )
                logger.info(f"Initialized member-specific storage for '{member_name}'")
            except Exception as e:
                logger.error(f"Failed to initialize storage for member '{member_name}': {e}")
                # Fall back to team storage
                storage = self.agent_storage

        return storage

    def _init_member_memory(self, member_config: Dict, member_name: str, cloudsql_config: Dict) -> Any:
        """
        Initialize member-specific memory or use team's shared memory.

        Args:
            member_config: Configuration for the team member
            member_name: Name of the team member
            cloudsql_config: CloudSQL configuration

        Returns:
            Memory instance
        """
        # By default, use the team's memory
        memory = self.agent_memory

        # Set up member-specific memory if configured
        if "memory" in member_config:
            memory_table = member_config["memory"].get("table_name", f"{member_name.lower()}_memory")

            try:
                memory = get_pgvector_memory(
                    user_id=f"{self.id}_{member_name.lower()}",
                    config=cloudsql_config,
                    table_name=memory_table,
                )
                logger.info(f"Initialized member-specific memory for '{member_name}'")
            except Exception as e:
                logger.error(f"Failed to initialize memory for member '{member_name}': {e}")
                # Fall back to team memory
                memory = self.agent_memory

        return memory
