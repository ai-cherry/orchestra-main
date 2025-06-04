"""
"""
        """
        """
        self.id = agent_config.get("id", "phidata_team_agent")
        self.name = agent_config.get("name", "Phidata Team Agent")

        # Set flag indicating this is a Team
        self._is_team = True

        # Import required Phidata/Agno modules
        try:

            pass
            agno_team = importlib.import_module("agno.team")
            agno_agent = importlib.import_module("agno.agent")
            Team = getattr(agno_team, "Team")
            Agent = getattr(agno_agent, "Agent")
        except Exception:

            pass
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


                pass
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

            except Exception:


                pass
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
        """
            raise ValueError(f"LLM reference '{model_ref}' not found in LLM client")

        return getattr(self.llm, model_ref)

    def _init_member_tools(self, tools_config: List[Dict], member_name: str) -> List:
        """
        """
                tool_type = tool_config.get("type")
                tool_params = tool_config.get("params", {})
                tool_name = tool_config.get("name")

                if not tool_type:
                    logger.warning(f"Skipping tool config without 'type' for member '{member_name}'")
                    continue

                # Handle tools from the registry
                if tool_type.startswith("registry:"):
                    tool_id = tool_type.replace("registry:", "").strip()
                    cherry_ai_tool = self.tools.get_tool(tool_id)

                    if cherry_ai_tool and hasattr(cherry_ai_tool, "to_phidata_tool"):
                        phidata_tool = cherry_ai_tool.to_phidata_tool(**tool_params)
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

            except Exception:


                pass
                logger.error(f"Failed to initialize tool for member '{member_name}': {e}")
                # Continue with other tools even if one fails

        return member_tools

    def _init_member_storage(self, member_config: Dict, member_name: str, cloudsql_config: Dict) -> Any:
        """
        """
        if "storage" in member_config:
            storage_table = member_config["storage"].get("table_name", f"{member_name.lower()}_storage")

            try:


                pass
                storage = get_pg_agent_storage(
                    agent_id=f"{self.id}_{member_name.lower()}",
                    config=cloudsql_config,
                    table_name=storage_table,
                )
                logger.info(f"Initialized member-specific storage for '{member_name}'")
            except Exception:

                pass
                logger.error(f"Failed to initialize storage for member '{member_name}': {e}")
                # Fall back to team storage
                storage = self.agent_storage

        return storage

    def _init_member_memory(self, member_config: Dict, member_name: str, cloudsql_config: Dict) -> Any:
        """
        """
        if "memory" in member_config:
            memory_table = member_config["memory"].get("table_name", f"{member_name.lower()}_memory")

            try:


                pass
                memory = get_pgvector_memory(
                    user_id=f"{self.id}_{member_name.lower()}",
                    config=cloudsql_config,
                    table_name=memory_table,
                )
                logger.info(f"Initialized member-specific memory for '{member_name}'")
            except Exception:

                pass
                logger.error(f"Failed to initialize memory for member '{member_name}': {e}")
                # Fall back to team memory
                memory = self.agent_memory

        return memory
