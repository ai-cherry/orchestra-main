"""
"""
    """
    """
    agent_type: str = "base"  # Class variable to identify the type

    def __init__(
        self,
        agent_config: Dict[str, Any],
        memory_manager: MemoryManager,
        llm_client: PortkeyClient,
        tool_registry: ToolRegistry,
    ):
        """
        """
        self.name = self.agent_config.get("name", self.__class__.__name__)
        self.id = self.agent_config.get("id", self.name.lower())

        logger.info(f"Initializing agent wrapper: {self.name} (ID: {self.id})")

    @abstractmethod
    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        """
        """
        """