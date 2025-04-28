"""
DEPRECATED: This file is deprecated and will be removed in a future release.

This older agent wrapper has been moved to the proper package structure and improved.
Please use the official implementation at packages/agents/src/phidata/wrapper.py instead,
which provides:
- Better integration with the agent registry
- Improved error handling
- Support for structured outputs
- Streaming response capabilities
- Better memory and storage integration

Example migration:
from updated_phidata_wrapper import PhidataAgentWrapper  # Old
# Change to:
from packages.agents.src.phidata.wrapper import PhidataAgentWrapper  # New

Phidata Agent Wrapper for Orchestra with Native Postgres Storage

This module provides an updated wrapper for Phidata/Agno agents that utilizes
Phidata's native PostgreSQL storage and memory capabilities. It handles integration
between Orchestra's orchestration system and Phidata's agent framework while leveraging
Phidata's built-in storage and memory management.
"""

import logging
import importlib
import asyncio
from typing import Any, Dict, List, Optional, Type, Union, cast

from packages.agents.src._base import OrchestraAgentBase
from packages.core.src.models import AgentInput, AgentOutput
from packages.memory.src.base import MemoryManager
from packages.llm.src.portkey_client import PortkeyClient
from packages.tools.src.base import ToolRegistry
# Import our new CloudSQL PGVector configuration
from packages.phidata.src.cloudsql_pgvector import get_pg_agent_storage, get_pgvector_memory

logger = logging.getLogger(__name__)

class PhidataAgentWrapper(OrchestraAgentBase):
    """
    Updated wrapper for Phidata/Agno agents with native Postgres storage.
    
    This wrapper handles:
    1. Converting Orchestra's input format to Phidata's expected format
    2. Configuring Phidata's native PgAgentStorage and PgMemoryDb
    3. Executing the Phidata agent with the appropriate context
    4. Converting Phidata's output to Orchestra's standardized output format
    
    Note: With the native storage configured, Phidata itself handles:
    - Loading relevant conversation history
    - Storing interaction results
    """
    
    agent_type: str = "phidata"
    
    def __init__(
        self,
        agent_config: Dict[str, Any],
        memory_manager: MemoryManager,
        llm_client: PortkeyClient,
        tool_registry: ToolRegistry,
    ):
        """
        Initialize the Phidata agent wrapper with native Postgres storage.
        
        Args:
            agent_config: Agent-specific configuration dict from the registry
            memory_manager: Orchestra's centralized memory management system (used for config)
            llm_client: Configured LLM provider (usually via Portkey)
            tool_registry: Access to registered system tools
        """
        super().__init__(agent_config, memory_manager, llm_client, tool_registry)
        
        # Flag to track if we're using a Team or single Agent
        self._is_team = False
        
        # Parse Phidata-specific configuration
        self._parse_config()
        
        # Initialize storage and memory configurations
        self._init_storage_and_memory()
        
        # Initialize the Phidata agent instance
        self._init_phidata_agent()
        
        logger.info(f"PhidataAgentWrapper initialized: {self.name} (using {'Team' if self._is_team else 'Agent'} with Cloud SQL/PGVector storage)")
    
    def _parse_config(self) -> None:
        """
        Parse the Phidata-specific configuration from the agent_config.
        """
        # Get agent class path (e.g., "agno.agent.Agent" or "agno.team.Team")
        self.phidata_agent_class = self.agent_config.get("phidata_agent_class", "agno.agent.Agent")
        self._is_team = self.phidata_agent_class.endswith(".Team")
        
        # Get LLM reference (which LLM to use from those configured via Portkey)
        self.llm_ref = self.agent_config.get("llm_ref")
        if not self.llm_ref:
            raise ValueError("PhidataAgentWrapper requires a 'llm_ref' in config")
        
        # Parse tool configurations
        self.tools_config = self.agent_config.get("tools", [])
        
        # Get instructions for the agent
        self.instructions = self.agent_config.get("instructions", [])
        
        # Get markdown and show_tool_calls flags
        self.markdown = self.agent_config.get("markdown", True)
        self.show_tool_calls = self.agent_config.get("show_tool_calls", True)
        
        # Parse storage configurations
        self.storage_config = self.agent_config.get("storage", {})
        self.memory_config = self.agent_config.get("memory", {})
        
        # If this is a team, parse team-specific config
        if self._is_team:
            self.team_mode = self.agent_config.get("team_mode", "coordinate")
            self.team_model_ref = self.agent_config.get("team_model_ref", self.llm_ref)
            self.team_success_criteria = self.agent_config.get("team_success_criteria", "")
            self.team_instructions = self.agent_config.get("team_instructions", self.instructions)
            self.team_markdown = self.agent_config.get("team_markdown", self.markdown)
            self.members_config = self.agent_config.get("members", [])
            if not self.members_config:
                raise ValueError("PhidataAgentWrapper with Team requires 'members' in config")
    
    def _init_storage_and_memory(self) -> None:
        """
        Initialize Phidata's native storage and memory configurations using CloudSQL.
        """
        try:
            # Extract custom CloudSQL configuration from agent config if provided
            cloudsql_config = self.agent_config.get("cloudsql_config", {})
            
            # Setup PgAgentStorage using CloudSQL
            storage_table = self.storage_config.get("table_name", f"{self.id}_storage")
            
            # Initialize PgAgentStorage with agent_id for partitioning
            self.agent_storage = get_pg_agent_storage(
                agent_id=self.id,
                config=cloudsql_config,
                table_name=storage_table
            )
            logger.info(f"Initialized CloudSQL PgAgentStorage with table: {storage_table}")
            
            # Setup PgVector2 for memory using VertexAI embeddings
            memory_table = self.memory_config.get("table_name", f"{self.id}_memory")
            
            # Initialize PgVector2 with user_id if available
            user_id = self.agent_config.get("default_user_id")
            self.agent_memory = get_pgvector_memory(
                user_id=user_id,
                config=cloudsql_config,
                table_name=memory_table
            )
            logger.info(f"Initialized CloudSQL PgVector2 memory with table: {memory_table}")
            
        except Exception as e:
            logger.error(f"Failed to initialize CloudSQL storage/memory: {e}", exc_info=True)
            # Set to None if initialization fails - we'll handle this gracefully
            self.agent_storage = None
            self.agent_memory = None
            raise RuntimeError(f"Failed to initialize CloudSQL storage/memory: {e}")
    
    def _init_phidata_agent(self) -> None:
        """
        Initialize the Phidata agent or team based on the configuration.
        """
        try:
            # Dynamically import the agent/team class
            module_path, class_name = self.phidata_agent_class.rsplit(".", 1)
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            
            # Initialize tools for the agent
            phidata_tools = self._init_phidata_tools()
            
            # If this is a team, initialize member agents first
            if self._is_team:
                members = self._init_team_members()
                
                # Get team model from Portkey client
                team_model = self._get_llm_from_ref(self.team_model_ref)
                
                # Initialize the team
                self.phidata_agent = agent_class(
                    members=members,
                    model=team_model,
                    mode=self.team_mode,
                    success_criteria=self.team_success_criteria,
                    instructions=self.team_instructions,
                    markdown=self.team_markdown,
                    name=self.name,
                    # Pass configured storage and memory
                    storage=self.agent_storage,
                    memory=self.agent_memory
                )
            else:
                # Get the LLM model from Portkey client
                llm_model = self._get_llm_from_ref(self.llm_ref)
                
                # Initialize a single agent
                self.phidata_agent = agent_class(
                    model=llm_model,
                    tools=phidata_tools,
                    instructions=self.instructions,
                    markdown=self.markdown,
                    show_tool_calls=self.show_tool_calls,
                    name=self.name,
                    # Pass configured storage and memory
                    storage=self.agent_storage, 
                    memory=self.agent_memory,
                    # Add additional configurations from agent_config
                    add_history_to_messages=self.agent_config.get("add_history_to_messages", True)
                )
            
            logger.info(f"Successfully initialized Phidata {'Team' if self._is_team else 'Agent'} with CloudSQL storage")
            
        except ImportError as e:
            logger.error(f"Failed to import Phidata module: {e}")
            raise ImportError(f"Phidata module not available. Please ensure Phidata/Agno is installed: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Phidata agent: {e}")
            raise RuntimeError(f"Failed to initialize Phidata agent: {e}")
    
    def _init_phidata_tools(self) -> List[Any]:
        """
        Initialize Phidata tools based on the configuration.
        
        Returns:
            List of initialized Phidata tool instances
        """
        phidata_tools = []
        
        for tool_config in self.tools_config:
            try:
                # Get tool class path and params
                tool_type = tool_config.get("type")
                tool_params = tool_config.get("params", {})
                
                if not tool_type:
                    logger.warning(f"Skipping tool definition without 'type' in config")
                    continue
                
                # Dynamically import and instantiate the tool
                module_path, class_name = tool_type.rsplit(".", 1)
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)
                
                # Initialize the tool with the provided parameters
                tool_instance = tool_class(**tool_params)
                phidata_tools.append(tool_instance)
                
                logger.info(f"Initialized Phidata tool: {tool_type}")
                
            except ImportError as e:
                logger.error(f"Failed to import Phidata tool module {tool_type}: {e}")
                # Skip this tool but continue with others
            except Exception as e:
                logger.error(f"Failed to initialize Phidata tool {tool_type}: {e}")
                # Skip this tool but continue with others
        
        return phidata_tools
    
    def _init_team_members(self) -> List[Any]:
        """
        Initialize Phidata team members based on the configuration.
        
        Returns:
            List of initialized Phidata agent instances for the team
        """
        # Import Agent class for member initialization
        try:
            agent_module_path = "agno.agent"  # Assuming this is the standard path
            agent_module = importlib.import_module(agent_module_path)
            Agent = getattr(agent_module, "Agent")
        except ImportError as e:
            logger.error(f"Failed to import Phidata Agent module: {e}")
            raise ImportError(f"Phidata Agent module not available: {e}")
        
        # Extract custom CloudSQL configuration from agent config if provided
        cloudsql_config = self.agent_config.get("cloudsql_config", {})
        
        members = []
        for member_config in self.members_config:
            try:
                # Get member-specific config
                name = member_config.get("name", f"Member{len(members) + 1}")
                role = member_config.get("role", "")
                instructions = member_config.get("instructions", [])
                model_ref = member_config.get("model_ref", self.llm_ref)
                tools_config = member_config.get("tools", [])
                
                # Get the LLM model for this member
                member_model = self._get_llm_from_ref(model_ref)
                
                # Initialize tools for this member
                member_tools = []
                for tool_config in tools_config:
                    tool_type = tool_config.get("type")
                    tool_params = tool_config.get("params", {})
                    
                    if not tool_type:
                        continue
                    
                    module_path, class_name = tool_type.rsplit(".", 1)
                    module = importlib.import_module(module_path)
                    tool_class = getattr(module, class_name)
                    
                    tool_instance = tool_class(**tool_params)
                    member_tools.append(tool_instance)
                
                # Initialize member-specific storage if needed
                member_storage = None
                member_memory = None
                
                # Check if member has specific storage config
                if "storage" in member_config:
                    # Get table name for member storage
                    storage_table = member_config["storage"].get("table_name", f"{name.lower()}_storage")
                    
                    # Use CloudSQL for member storage with partitioning
                    member_storage = get_pg_agent_storage(
                        agent_id=f"{self.id}_{name.lower()}",
                        config=cloudsql_config,
                        table_name=storage_table
                    )
                    logger.info(f"Created CloudSQL storage for member {name}: {storage_table}")
                else:
                    # Share the team's storage
                    member_storage = self.agent_storage
                
                # Check if member has specific memory config
                if "memory" in member_config:
                    # Get table name for member memory
                    memory_table = member_config["memory"].get("table_name", f"{name.lower()}_memory")
                    
                    # Use CloudSQL for member memory
                    member_memory = get_pgvector_memory(
                        user_id=f"{self.id}_{name.lower()}",
                        config=cloudsql_config,
                        table_name=memory_table
                    )
                    logger.info(f"Created CloudSQL memory for member {name}: {memory_table}")
                else:
                    # Share the team's memory
                    member_memory = self.agent_memory
                
                # Initialize the member agent with storage/memory
                member = Agent(
                    model=member_model,
                    tools=member_tools,
                    instructions=instructions,
                    name=name,
                    role=role,
                    markdown=member_config.get("markdown", self.markdown),
                    show_tool_calls=member_config.get("show_tool_calls", self.show_tool_calls),
                    storage=member_storage,
                    memory=member_memory
                )
                
                members.append(member)
                logger.info(f"Initialized team member: {name} with CloudSQL storage/memory")
                
            except Exception as e:
                logger.error(f"Failed to initialize team member: {e}")
                # Skip this member but continue with others
        
        if not members:
            raise ValueError("Failed to initialize any team members")
        
        return members
    
    def _get_llm_from_ref(self, llm_ref: str) -> Any:
        """
        Get the LLM model instance from the provided reference.
        
        Args:
            llm_ref: Reference to the LLM model in the LLM client
            
        Returns:
            Configured LLM model instance
        """
        # Currently, we assume llm_client contains pre-configured models
        # accessible by their reference names
        if not hasattr(self.llm, llm_ref):
            raise ValueError(f"LLM reference '{llm_ref}' not found in LLM client")
        
        return getattr(self.llm, llm_ref)
    
    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the Phidata agent with the provided input.
        
        This updated method:
        1. No longer needs to manually load conversation history (handled by Phidata)
        2. Passes user_id and session_id to Phidata for consistent memory retrieval
        3. No longer needs to manually store interactions (handled by Phidata)
        
        Args:
            input_data: Standard input with prompt, user_id, session_id, etc.
            
        Returns:
            Standard agent output with content and metadata
        """
        try:
            # Create parameters for the Phidata agent
            run_params = {
                "message": input_data.prompt,
                # Pass user_id and session_id for memory/storage integration
                "user_id": input_data.user_id,
                "session_id": input_data.session_id
            }
            
            # Add any additional metadata from input
            if input_data.metadata:
                run_params.update(input_data.metadata)
            
            # Execute the Phidata agent
            # Note: With native storage/memory, Phidata will handle history retrieval
            if hasattr(self.phidata_agent, "run"):
                if asyncio.iscoroutinefunction(self.phidata_agent.run):
                    response = await self.phidata_agent.run(**run_params)
                else:
                    # Run synchronous method in a thread pool to avoid blocking
                    response = await asyncio.to_thread(self.phidata_agent.run, **run_params)
            else:
                raise NotImplementedError("Phidata agent does not have a 'run' method")
            
            # Extract content from the response
            content = ""
            if hasattr(response, "content"):
                content = response.content
            elif isinstance(response, dict) and "content" in response:
                content = response["content"]
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
            
            # Extract tool calls if available for metadata
            tool_calls = None
            if hasattr(response, "tool_calls"):
                tool_calls = response.tool_calls
            
            # Create standardized output
            output = AgentOutput(
                request_id=input_data.request_id,
                agent_type=self.agent_type,
                content=content,
                content_type="text/markdown" if self.markdown else "text/plain",
                metadata={
                    "agent_name": self.name,
                    "agent_id": self.id,
                    "tool_calls": tool_calls
                }
            )
            
            return output
            
        except Exception as e:
            logger.error(f"Error executing Phidata agent: {e}", exc_info=True)
            
            # Return error response
            return AgentOutput(
                request_id=input_data.request_id,
                agent_type=self.agent_type,
                content=f"Error executing Phidata agent: {str(e)}",
                content_type="text/plain",
                metadata={
                    "agent_name": self.name,
                    "agent_id": self.id,
                    "error": str(e)
                }
            )
    
    async def health_check(self) -> bool:
        """
        Check if the Phidata agent and its CloudSQL storage/memory are operational.
        
        Returns:
            True if the agent is operational, False otherwise
        """
        # Check if agent is initialized
        if self.phidata_agent is None:
            return False
            
        # Check storage connection if available
        storage_ok = True
        if self.agent_storage:
            try:
                # For CloudSQL, check if we can access the engine and connection is alive
                if hasattr(self.agent_storage, 'db_engine'):
                    with self.agent_storage.db_engine.connect() as conn:
                        conn.execute(sqlalchemy.text("SELECT 1"))
            except Exception:
                storage_ok = False
                
        # Check memory connection if available
        memory_ok = True
        if self.agent_memory:
            try:
                # For CloudSQL PGVector, check if we can access the engine
                if hasattr(self.agent_memory, 'db_engine'):
                    with self.agent_memory.db_engine.connect() as conn:
                        conn.execute(sqlalchemy.text("SELECT 1"))
            except Exception:
                memory_ok = False
        
        return storage_ok and memory_ok
