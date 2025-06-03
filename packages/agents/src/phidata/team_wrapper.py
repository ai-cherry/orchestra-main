"""
"""
    """
    """
        """
        """
            agent_module_path = "agno.agent"
            agent_module = importlib.import_module(agent_module_path)
            Agent = getattr(agent_module, "Agent")
        except Exception:

            pass
            logger.error(f"Failed to import Phidata Agent module: {e}")
            raise ImportError(f"Phidata Agent module not available: {e}")

        # Extract custom CloudSQL configuration from agent config if provided
        cloudsql_config = self.agent_config.get("cloudsql_config", {})

        # Get registry for resolving references
        registry = get_registry()

        members = []
        for member_entry in self.members_config:
            try:

                pass
                # Check if this is a direct configuration or a reference
                if isinstance(member_entry, str):
                    # This is a reference to another agent definition
                    member_id = member_entry
                    logger.info(f"Resolving team member reference: {member_id}")

                    # Get the agent configuration from the registry
                    from core.orchestrator.src.core.config import get_agent_config

                    member_config = get_agent_config(member_id)

                    if not member_config:
                        logger.error(f"Failed to resolve team member reference: {member_id}")
                        continue

                    # Create agent instance with resolved config
                    member_agent = registry.create_agent(
                        agent_id=member_id,
                        agent_config=member_config,
                        memory_manager=self.memory,
                        llm_client=self.llm,
                        tool_registry=self.tools,
                    )

                    if not member_agent:
                        logger.error(f"Failed to instantiate agent for member reference: {member_id}")
                        continue

                    # Extract the underlying Phidata agent from the wrapper
                    if hasattr(member_agent, "phidata_agent"):
                        phidata_agent = member_agent.phidata_agent
                        members.append(phidata_agent)
                        logger.info(f"Successfully initialized referenced team member: {member_id}")
                    else:
                        logger.error(f"Referenced agent doesn't have a phidata_agent attribute: {member_id}")

                else:
                    # This is a direct configuration (existing behavior)
                    # Get member-specific config
                    member_config = member_entry
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

                            pass
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

                        except Exception:


                            pass
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
                            table_name=storage_table,
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
                            table_name=memory_table,
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
                        memory=member_memory,
                    )

                    members.append(member)
                    logger.info(f"Initialized directly configured team member: {name}")

            except Exception:


                pass
                logger.error(f"Failed to initialize team member: {e}")
                # Skip this member but continue with others

        if not members:
            raise ValueError("Failed to initialize any team members")

        return members
