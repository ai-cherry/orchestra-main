# TODO: Consider adding connection pooling configuration
"""
"""
    """
    """
        project_id: str = "cherry-ai-project",
        spanner_instance_id: str = "orchestra-instance",
        spanner_database_id: str = "orchestra-db",
    ):
        """Initialize the agent registry with Google Cloud project details for routing."""
        """Register the built-in wrapper implementations."""
        self.register_wrapper_class("phidata", PhidataTeamAgentWrapper)

        # Register the LangChain wrapper for modular LangChain agent support
        from packages.agents.src.langchain_agent import LangChainAgentWrapper

        self.register_wrapper_class("langchain", LangChainAgentWrapper)

        # Add other built-in wrappers as they are implemented
        # Example: self.register_wrapper_class("arno", ArnoAgentWrapper)
        # Example: self.register_wrapper_class("adk", ADKAgentWrapper)

    def register_wrapper_class(self, wrapper_type: str, wrapper_class: Type[OrchestraAgentBase]) -> None:
        """
        """
            logger.warning(f"Overwriting existing wrapper class for type: {wrapper_type}")

        self._wrapper_classes[wrapper_type] = wrapper_class
        logger.info(f"Registered wrapper class for type: {wrapper_type}")

    def create_agent(
        self,
        agent_id: str,
        agent_config: Dict[str, Any],
        memory_manager: Any,
        llm_client: Any,
        tool_registry: Any,
    ) -> Optional[OrchestraAgentBase]:
        """
        """
        wrapper_type = agent_config.get("wrapper_type")
        if not wrapper_type:
            logger.error(f"No wrapper_type specified in config for agent: {agent_id}")
            return None

        if wrapper_type not in self._wrapper_classes:
            logger.error(f"Unknown wrapper_type: {wrapper_type} for agent: {agent_id}")
            return None

        try:


            pass
            # Get the wrapper class
            wrapper_class = self._wrapper_classes[wrapper_type]

            # Ensure agent_id is in the config
            config = dict(agent_config)
            config["id"] = agent_id

            # Create the wrapper instance
            agent = wrapper_class(
                agent_config=config,
                memory_manager=memory_manager,
                llm_client=llm_client,
                tool_registry=tool_registry,
            )

            # Register the agent in the routing system with initial values if provided
            initial_score = agent_config.get("initial_capability_score", 0.0)
            initial_cost = agent_config.get("initial_cost_per_request", 0.0)
            self.routing.register_agent(agent_id, initial_score, initial_cost)

            logger.info(f"Successfully created agent: {agent_id} with wrapper: {wrapper_type}")
            return agent

        except Exception:


            pass
            logger.error(
                f"Failed to create agent: {agent_id} with wrapper: {wrapper_type}: {e}",
                exc_info=True,
            )
            return None

    def get_available_wrapper_types(self) -> Dict[str, str]:
        """
        """
            doc = wrapper_class.__doc__ or ""
            # Extract the first line of the docstring as a short description
            description = doc.strip().split("\n")[0] if doc else f"Wrapper type: {wrapper_type}"
            result[wrapper_type] = description

        return result

    def load_wrapper_class_from_path(self, wrapper_type: str, class_path: str) -> bool:
        """
            class_path: Full import path to the class, e.g., "mypackage.module.MyClass"

        Returns:
            True if successfully loaded and registered, False otherwise
        """
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            wrapper_class = getattr(module, class_name)

            # Ensure it's a subclass of OrchestraAgentBase
            if not issubclass(wrapper_class, OrchestraAgentBase):
                logger.error(f"Class {class_path} is not a subclass of OrchestraAgentBase")
                return False

            # Register the wrapper
            self.register_wrapper_class(wrapper_type, wrapper_class)
            return True

        except Exception:


            pass
            logger.error(f"Failed to load wrapper class from path: {class_path}: {e}")
            return False

# Create a singleton instance with default project settings
agent_registry = AgentRegistry(
    project_id="cherry-ai-project",
    spanner_instance_id="orchestra-instance",
    spanner_database_id="orchestra-db",
)

def get_registry(
    project_id: str = "cherry-ai-project",
    spanner_instance_id: str = "orchestra-instance",
    spanner_database_id: str = "orchestra-db",
) -> AgentRegistry:
    """
    """