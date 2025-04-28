"""
Phidata Agent Wrapper for Orchestra with Native Postgres Storage

This module provides a wrapper for Phidata/Agno agents that utilizes
Phidata's native PostgreSQL storage and memory capabilities. It handles integration
between Orchestra's orchestration system and Phidata's agent framework while leveraging
Phidata's built-in storage and memory management.
"""

import logging
import importlib
import asyncio
import os
import sqlalchemy
from typing import Any, Dict, List, Optional, Union, AsyncGenerator, cast, Generator

from packages.agents.src._base import OrchestraAgentBase
from packages.core.src.models import AgentInput, AgentOutput
from packages.memory.src.base import MemoryManager
from packages.llm.src.portkey_client import PortkeyClient
from packages.tools.src.base import ToolRegistry
# Import our CloudSQL PGVector configuration
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
        
        # Initialize knowledge base attribute
        self.knowledge_base = None
        
        # Parse Phidata-specific configuration
        self._parse_config()
        
        # Initialize storage and memory configurations
        self._init_storage_and_memory()
        
        # Initialize knowledge base if configured
        if "knowledge" in self.agent_config:
            self._init_knowledge_base()
        
        # Handle response_model configuration for structured output
        self.response_model = None
        if self.agent_config.get("response_model_path"):
            try:
                # Parse the path to the Pydantic model class
                model_path = self.agent_config.get("response_model_path")
                module_path, class_name = model_path.rsplit(".", 1)
                
                # Dynamically import the module and get the class
                logger.info(f"Importing response model from: {module_path}")
                module = importlib.import_module(module_path)
                model_class = getattr(module, class_name)
                
                # Store the imported Pydantic model class
                self.response_model = model_class
                logger.info(f"Successfully loaded response model: {class_name} from {module_path}")
            except ImportError as e:
                logger.error(f"Failed to import response model module: {e}")
                raise ImportError(f"Response model module not found: {e}")
            except AttributeError as e:
                logger.error(f"Failed to find response model class in module: {e}")
                raise AttributeError(f"Response model class not found: {e}")
            except Exception as e:
                logger.error(f"Error loading response model: {e}", exc_info=True)
                raise RuntimeError(f"Failed to load response model: {e}")
        
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
        
        # Get response model path for structured output (if configured)
        self.response_model_path = self.agent_config.get("response_model_path")
        if self.response_model_path and not isinstance(self.response_model_path, str):
            raise ValueError("'response_model_path' must be a string")
        
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
    
    def _init_knowledge_base(self) -> None:
        """
        Initialize the knowledge base from configuration.
        
        This method handles:
        1. Dynamically importing necessary classes
        2. Creating the embedder -> vector DB -> knowledge base hierarchy
        3. Configuring each component based on the provided YAML config
        """
        try:
            # Extract knowledge configuration
            knowledge_config = self.agent_config.get("knowledge", {})
            
            # 1. EMBEDDER: Configure and instantiate embedder
            embedder_config = knowledge_config.get("embedder", {})
            embedder_class_path = embedder_config.get("embedder_class_path", "phi.embeddings.VertexAiEmbedder")
            embedder_model = embedder_config.get("model", "textembedding-gecko@latest")
            embedder_project = embedder_config.get("project", os.environ.get("GCP_PROJECT_ID"))
            embedder_location = embedder_config.get("location", "us-central1")
            
            # Import embedder class
            module_path, class_name = embedder_class_path.rsplit(".", 1)
            embedder_module = importlib.import_module(module_path)
            EmbedderClass = getattr(embedder_module, class_name)
            
            # Instantiate embedder
            embedder = EmbedderClass(
                model=embedder_model,
                project=embedder_project,
                location=embedder_location
            )
            logger.info(f"Initialized {class_name} with model {embedder_model}")
            
            # 2. VECTOR DB: Configure and instantiate vector database
            vector_db_config = knowledge_config.get("vector_db", {})
            vector_db_class_path = vector_db_config.get("vector_db_class_path", "phi.vector.PgVector")
            vector_db_collection = vector_db_config.get("collection", f"{self.id}_knowledge")
            db_conn_env_var = vector_db_config.get("db_conn_env_var", "DATABASE_URL")
            search_type = vector_db_config.get("search_type", "mmr")
            
            # Get DB connection string from environment
            db_connection_url = os.environ.get(db_conn_env_var)
            if not db_connection_url:
                raise ValueError(f"Environment variable {db_conn_env_var} not found for vector DB connection")
            
            # Import vector DB class
            module_path, class_name = vector_db_class_path.rsplit(".", 1)
            vector_db_module = importlib.import_module(module_path)
            VectorDBClass = getattr(vector_db_module, class_name)
            
            # Instantiate vector DB
            vector_db = VectorDBClass(
                collection=vector_db_collection,
                connection_string=db_connection_url,
                embedder=embedder,
                search_type=search_type
            )
            logger.info(f"Initialized {class_name} with collection {vector_db_collection}")
            
            # 3. KNOWLEDGE BASE: Configure and instantiate knowledge base
            knowledge_base_class_path = knowledge_config.get("knowledge_base_class_path", "phi.knowledge.pdf.PDFUrlKnowledgeBase")
            urls = knowledge_config.get("urls", [])
            
            # Import knowledge base class
            module_path, class_name = knowledge_base_class_path.rsplit(".", 1)
            kb_module = importlib.import_module(module_path)
            KnowledgeBaseClass = getattr(kb_module, class_name)
            
            # Instantiate knowledge base
            self.knowledge_base = KnowledgeBaseClass(
                urls=urls,
                vector_db=vector_db
            )
            
            logger.info(f"Successfully initialized {class_name} with {len(urls)} URLs and {vector_db_class_path}")
            
        except ImportError as e:
            logger.error(f"Failed to import knowledge base component: {e}")
            raise ImportError(f"Knowledge base component not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize knowledge base: {e}")
    
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
                tool_name = tool_config.get("name")
                
                if not tool_type:
                    logger.warning(f"Skipping tool definition without 'type' in config")
                    continue
                
                # Check if this is a reference to a tool in the registry
                if tool_type.startswith("registry:"):
                    # Extract tool identifier from registry reference
                    tool_id = tool_type.replace("registry:", "").strip()
                    
                    # Get the tool from the registry
                    orchestra_tool = self.tools.get_tool(tool_id)
                    if not orchestra_tool:
                        logger.warning(f"Tool '{tool_id}' not found in registry, skipping")
                        continue
                    
                    # Check if tool has a to_phidata_tool method
                    if hasattr(orchestra_tool, "to_phidata_tool") and callable(orchestra_tool.to_phidata_tool):
                        phidata_tool = orchestra_tool.to_phidata_tool(**tool_params)
                        if phidata_tool:
                            phidata_tools.append(phidata_tool)
                            logger.info(f"Added registry tool: {tool_id} to Phidata agent")
                    else:
                        logger.warning(f"Tool {tool_id} doesn't support conversion to Phidata format")
                    
                    continue
                
                # Otherwise, dynamically import and instantiate the tool
                module_path, class_name = tool_type.rsplit(".", 1)
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)
                
                # Initialize the tool with the provided parameters
                tool_instance = tool_class(**tool_params)
                
                # Set name if provided
                if tool_name and hasattr(tool_instance, "name"):
                    tool_instance.name = tool_name
                
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
                    try:
                        tool_type = tool_config.get("type")
                        tool_params = tool_config.get("params", {})
                        
                        if not tool_type:
                            continue
                        
                        # Check if this is a registry tool
                        if tool_type.startswith("registry:"):
                            tool_id = tool_type.replace("registry:", "").strip()
                            orchestra_tool = self.tools.get_tool(tool_id)
                            if orchestra_tool and hasattr(orchestra_tool, "to_phidata_tool"):
                                phidata_tool = orchestra_tool.to_phidata_tool(**tool_params)
                                if phidata_tool:
                                    member_tools.append(phidata_tool)
                            continue
                        
                        # Otherwise dynamically import
                        module_path, class_name = tool_type.rsplit(".", 1)
                        module = importlib.import_module(module_path)
                        tool_class = getattr(module, class_name)
                        
                        tool_instance = tool_class(**tool_params)
                        member_tools.append(tool_instance)
                        
                    except Exception as e:
                        logger.error(f"Failed to initialize tool for member {name}: {e}")
                
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
                
                # Prepare agent initialization parameters
                agent_params = {
                    "model": llm_model,
                    "tools": phidata_tools,
                    "instructions": self.instructions,
                    "markdown": self.markdown,
                    "show_tool_calls": self.show_tool_calls,
                    "name": self.name,
                    # Pass configured storage and memory
                    "storage": self.agent_storage, 
                    "memory": self.agent_memory,
                    # Add additional configurations from agent_config
                    "add_history_to_messages": self.agent_config.get("add_history_to_messages", True)
                }
                
                # Add knowledge_base if configured
                if hasattr(self, 'knowledge_base') and self.knowledge_base is not None:
                    agent_params["knowledge"] = self.knowledge_base
                    logger.info(f"Adding knowledge base to agent")
                
                # Add response_model if configured - this is crucial for structured output agents
                if hasattr(self, 'response_model') and self.response_model is not None:
                    agent_params["response_model"] = self.response_model
                    
                    # Log when using structured output with a response model
                    if "structured" in self.phidata_agent_class.lower():
                        logger.info(f"Initializing structured output agent with response model: {self.response_model.__name__}")
                
                # Initialize a single agent with all parameters
                self.phidata_agent = agent_class(**agent_params)
            
            logger.info(f"Successfully initialized Phidata {'Team' if self._is_team else 'Agent'} with CloudSQL storage")
            
        except ImportError as e:
            logger.error(f"Failed to import Phidata module: {e}")
            raise ImportError(f"Phidata module not available. Please ensure Phidata/Agno is installed: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Phidata agent: {e}")
            raise RuntimeError(f"Failed to initialize Phidata agent: {e}")
    
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
    
    def _is_using_openrouter_via_portkey(self) -> bool:
        """
        Check if the current LLM model is an OpenRouter model accessed via Portkey.
        
        This determines whether we need to use special message formatting for OpenRouter.
        
        Returns:
            True if using OpenRouter via Portkey, False otherwise
        """
        # Get the model from the llm_ref
        llm_model = self._get_llm_from_ref(self.llm_ref)
        
        # Check if it's an OpenRouter model (either by class name or model name attribute)
        is_openrouter = False
        
        # Check by class name
        if hasattr(llm_model, "__class__") and hasattr(llm_model.__class__, "__name__"):
            class_name = llm_model.__class__.__name__.lower()
            if "openrouter" in class_name:
                is_openrouter = True
        
        # Check by model name attribute
        if hasattr(llm_model, "model") and isinstance(llm_model.model, str):
            model_name = llm_model.model.lower()
            if "openrouter" in model_name or "openai/" in model_name or "anthropic/" in model_name:
                is_openrouter = True
                
        # Check if this is being used via Portkey
        via_portkey = False
        if hasattr(llm_model, "default_headers"):
            headers = llm_model.default_headers
            if isinstance(headers, dict) and any(key.startswith("x-portkey") for key in headers):
                via_portkey = True
                
        logger.debug(f"Model check: is_openrouter={is_openrouter}, via_portkey={via_portkey}")
        return is_openrouter and via_portkey
    
    async def _process_streaming_response(self, response_gen: Union[AsyncGenerator, Generator]) -> str:
        """
        Process a streaming response from the Phidata agent.
        
        Args:
            response_gen: Generator or AsyncGenerator yielding response chunks
            
        Returns:
            Complete response content
        """
        full_content = ""
        
        try:
            # Handle both async and sync generators
            if hasattr(response_gen, "__aiter__"):
                # Process AsyncGenerator
                async for chunk in response_gen:
                    # Extract content from the chunk based on its structure
                    if hasattr(chunk, "content"):
                        content_chunk = chunk.content
                    elif isinstance(chunk, dict) and "content" in chunk:
                        content_chunk = chunk["content"]
                    elif isinstance(chunk, str):
                        content_chunk = chunk
                    else:
                        content_chunk = str(chunk)
                    
                    full_content += content_chunk
            else:
                # Process regular Generator in an async-friendly way
                for chunk in response_gen:
                    # Extract content from the chunk based on its structure
                    if hasattr(chunk, "content"):
                        content_chunk = chunk.content
                    elif isinstance(chunk, dict) and "content" in chunk:
                        content_chunk = chunk["content"]
                    elif isinstance(chunk, str):
                        content_chunk = chunk
                    else:
                        content_chunk = str(chunk)
                    
                    full_content += content_chunk
                    
                    # Yield to the event loop occasionally to prevent blocking
                    await asyncio.sleep(0)
                    
        except Exception as e:
            logger.error(f"Error processing streaming response: {e}", exc_info=True)
            # Append error information to the content
            full_content += f"\n\nError processing streaming response: {str(e)}"
            
        return full_content
    
    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the Phidata agent with the provided input.
        
        This updated method:
        1. Passes user_id and session_id to Phidata for consistent memory retrieval
        2. Handles streaming responses by collecting content chunks
        3. No longer needs to manually load/store conversation history
        4. Handles special message formatting for OpenRouter via Portkey
        
        Args:
            input_data: Standard input with prompt, user_id, session_id, etc.
            
        Returns:
            Standard agent output with content and metadata
        """
        try:
            # Determine if we're using OpenRouter via Portkey to adjust message format
            using_openrouter_via_portkey = self._is_using_openrouter_via_portkey()
            
            # Create parameters for the Phidata agent
            if using_openrouter_via_portkey:
                # OpenRouter via Portkey needs special message formatting
                # Convert simple text message to properly formatted messages array
                run_params = {
                    "messages": [
                        {
                            "role": "user",
                            "content": input_data.prompt
                        }
                    ],
                    # Pass user_id and session_id for memory/storage integration
                    "user_id": input_data.user_id,
                    "session_id": input_data.session_id
                }
                
                # If system instructions exist in metadata, add them as system message
                if input_data.metadata and "system" in input_data.metadata:
                    system_message = {
                        "role": "system",
                        "content": input_data.metadata["system"]
                    }
                    run_params["messages"].insert(0, system_message)
                
                logger.info("Using OpenRouter via Portkey format with messages array")
            else:
                # Standard format for other providers
                run_params = {
                    "message": input_data.prompt,
                    # Pass user_id and session_id for memory/storage integration
                    "user_id": input_data.user_id,
                    "session_id": input_data.session_id
                }
            
            # Add any additional metadata from input
            if input_data.metadata:
                # Filter out 'system' which was handled specially for OpenRouter
                metadata_to_add = {k: v for k, v in input_data.metadata.items() 
                                  if not (k == "system" and using_openrouter_via_portkey)}
                run_params.update(metadata_to_add)
            
            # Execute the Phidata agent
            if hasattr(self.phidata_agent, "run"):
                # Check if the agent's run method returns a generator
                is_streaming = self.agent_config.get("streaming", False)
                
                if is_streaming:
                    # For streaming responses
                    if asyncio.iscoroutinefunction(self.phidata_agent.run):
                        # Async streaming response
                        response_gen = await self.phidata_agent.run(**run_params)
                    else:
                        # Sync streaming response
                        response_gen = await asyncio.to_thread(self.phidata_agent.run, **run_params)
                    
                    # Process the streaming response
                    content = await self._process_streaming_response(response_gen)
                    
                    # Create a mock response object for compatibility with non-streaming code path
                    response = type('StreamingResponse', (), {
                        'content': content,
                        'tool_calls': getattr(response_gen, 'tool_calls', None)
                    })
                else:
                    # For non-streaming responses
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
