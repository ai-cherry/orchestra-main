"""
Python code snippet for PhidataAgentWrapper's __init__ method showing how it instantiates
an agno.team.Team based on a phidata_hn_team configuration from YAML.
"""

def __init__(self, agent_config, memory_manager, llm_client, tool_registry):
    """
    Initialize the PhidataAgentWrapper with a phidata_hn_team configuration.
    
    This method specifically demonstrates parsing the members list from config,
    instantiating each member Agent with its specific tools and model (via llm_ref),
    and then creating the Team with these members using the specified team settings.
    
    Args:
        agent_config: Contains the phidata_hn_team configuration
        memory_manager: Orchestra's memory management system
        llm_client: Portkey client with access to LLMs
        tool_registry: Registry of available tools
    """
    # Initialize base wrapper properties
    super().__init__(agent_config, memory_manager, llm_client, tool_registry)
    self._is_team = True
    
    # Import required Phidata modules
    agno_team = importlib.import_module("agno.team")
    agno_agent = importlib.import_module("agno.agent")
    Team = getattr(agno_team, "Team")
    Agent = getattr(agno_agent, "Agent")
    
    # Extract the phidata_hn_team configuration
    hn_team_config = agent_config["phidata_hn_team"]
    
    # Initialize storage and memory for the team
    self._init_storage_and_memory()
    
    # Extract team-level settings
    team_name = hn_team_config.get("name", "Hacker News Team")
    team_mode = hn_team_config.get("team_mode", "coordinate")
    team_model_ref = hn_team_config.get("team_model_ref")
    team_instructions = hn_team_config.get("team_instructions", [])
    team_success_criteria = hn_team_config.get("team_success_criteria", "")
    team_markdown = hn_team_config.get("markdown", True)
    
    # Parse the members list from config
    members_config = hn_team_config.get("members", [])
    if not members_config:
        raise ValueError("Team configuration requires at least one member")
    
    # Initialize team members
    members = []
    for member_config in members_config:
        # Get essential member configuration
        name = member_config.get("name")
        role = member_config.get("role", "")
        instructions = member_config.get("instructions", [])
        
        # Get member's LLM reference (with fallback to team default)
        member_llm_ref = member_config.get("llm_ref", 
                                          hn_team_config.get("default_llm_ref"))
        if not member_llm_ref:
            logger.warning(f"Member '{name}' missing LLM reference, skipping")
            continue
        
        # Get the actual LLM model for this member
        member_model = self._get_llm_from_ref(member_llm_ref)
        
        # Initialize tools for this member
        member_tools = []
        for tool_config in member_config.get("tools", []):
            tool_type = tool_config.get("type")
            tool_params = tool_config.get("params", {})
            
            # Handle registry tools
            if tool_type and tool_type.startswith("registry:"):
                tool_id = tool_type.replace("registry:", "").strip()
                orchestra_tool = self.tools.get_tool(tool_id)
                if orchestra_tool and hasattr(orchestra_tool, "to_phidata_tool"):
                    phidata_tool = orchestra_tool.to_phidata_tool(**tool_params)
                    if phidata_tool:
                        member_tools.append(phidata_tool)
                continue
            
            # Handle direct tool class references
            if tool_type:
                module_path, class_name = tool_type.rsplit(".", 1)
                module = importlib.import_module(module_path)
                tool_class = getattr(module, class_name)
                member_tools.append(tool_class(**tool_params))
        
        # Set up member-specific storage/memory or use team's
        member_storage = self.agent_storage
        member_memory = self.agent_memory
        
        # Use member-specific storage if configured
        if "storage" in member_config:
            storage_table = member_config["storage"].get("table_name", 
                                                       f"{name.lower()}_storage")
            member_storage = get_pg_agent_storage(
                agent_id=f"{self.id}_{name.lower()}",
                config=hn_team_config.get("cloudsql_config", {}),
                table_name=storage_table
            )
        
        # Use member-specific memory if configured
        if "memory" in member_config:
            memory_table = member_config["memory"].get("table_name", 
                                                     f"{name.lower()}_memory")
            member_memory = get_pgvector_memory(
                user_id=f"{self.id}_{name.lower()}",
                config=hn_team_config.get("cloudsql_config", {}),
                table_name=memory_table
            )
        
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
            memory=member_memory
        )
        
        members.append(member_agent)
    
    # Get the team model
    team_model = self._get_llm_from_ref(team_model_ref)
    
    # Finally, instantiate the Team with all members
    self.phidata_agent = Team(
        members=members,
        model=team_model,
        mode=team_mode,
        success_criteria=team_success_criteria,
        instructions=team_instructions,
        markdown=team_markdown,
        name=team_name,
        storage=self.agent_storage,
        memory=self.agent_memory
    )
    
    logger.info(f"Initialized Phidata Team '{team_name}' with {len(members)} members")
