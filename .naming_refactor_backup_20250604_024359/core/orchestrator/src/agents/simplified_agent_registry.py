"""
"""
    """
    """
    TEXT_GENERATION = "text_generation"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    CODE_GENERATION = "code_generation"
    GENERAL = "general"  # For basic agents that don't have specialized capabilities

class SimplifiedAgentRegistry:
    """
    """
        """Initialize the simplified agent registry."""
        logger.info("SimplifiedAgentRegistry initialized")

    def register_agent(self, agent: Agent) -> None:
        """
        """
        if hasattr(agent, "capabilities"):
            self._capabilities[agent_type] = agent.capabilities
        else:
            # Default to general capability
            self._capabilities[agent_type] = [AgentCapability.GENERAL]

        # Set as default if first agent
        if self._default_agent_type is None:
            self._default_agent_type = agent_type

        logger.info(f"Registered agent: {agent_type}")

    def register_agent_type(self, agent_type: str, agent_class: Type[Agent]) -> None:
        """
        """
        logger.info(f"Registered agent type: {agent_type}")

    def set_default_agent_type(self, agent_type: str) -> None:
        """
        """
            logger.info(f"Set default agent type: {agent_type}")
        else:
            logger.warning(f"Unknown agent type '{agent_type}' cannot be set as default")

    def get_agent(self, agent_type: Optional[str] = None) -> Agent:
        """
        """
                raise KeyError("No default agent type set")

        # Return existing instance if available
        if agent_type in self._agents:
            return self._agents[agent_type]

        # Create new instance if type is registered
        if agent_type in self._agent_types:
            agent = self._agent_types[agent_type]()
            self._agents[agent_type] = agent

            # Store capabilities if available
            if hasattr(agent, "capabilities"):
                self._capabilities[agent_type] = agent.capabilities
            else:
                # Default to general capability
                self._capabilities[agent_type] = [AgentCapability.GENERAL]

            return agent

        # Raise error if not found
        raise KeyError(f"Agent type '{agent_type}' not registered")

    def select_agent_for_context(self, context: AgentContext) -> Agent:
        """
        """
            raise RuntimeError("No agents registered")

        # Check if a specific agent is requested
        requested_agent = context.metadata.get("agent_type")
        if requested_agent:
            try:

                pass
                return self.get_agent(requested_agent)
            except Exception:

                pass
                logger.warning(f"Requested agent '{requested_agent}' not found, using selection logic")

        # Simple keyword-based selection
        user_input = context.user_input.lower()

        # Check for code generation
        if any(kw in user_input for kw in ["code", "function", "class", "programming"]):
            for agent_type, capabilities in self._capabilities.items():
                if AgentCapability.CODE_GENERATION in capabilities:
                    logger.info(f"Selected agent {agent_type} for code generation")
                    return self.get_agent(agent_type)

        # Check for question answering
        if "?" in user_input or any(kw in user_input for kw in ["what", "how", "why", "when", "where"]):
            for agent_type, capabilities in self._capabilities.items():
                if AgentCapability.QUESTION_ANSWERING in capabilities:
                    logger.info(f"Selected agent {agent_type} for question answering")
                    return self.get_agent(agent_type)

        # Check for summarization
        if any(kw in user_input for kw in ["summarize", "summary", "summarization"]):
            for agent_type, capabilities in self._capabilities.items():
                if AgentCapability.SUMMARIZATION in capabilities:
                    logger.info(f"Selected agent {agent_type} for summarization")
                    return self.get_agent(agent_type)

        # Default to text generation or general capability
        for agent_type, capabilities in self._capabilities.items():
            if AgentCapability.TEXT_GENERATION in capabilities:
                logger.info(f"Selected agent {agent_type} for text generation")
                return self.get_agent(agent_type)

        # Fall back to default agent
        logger.info(f"Using default agent: {self._default_agent_type}")
        return self.get_agent(self._default_agent_type)

    def get_agent_status(self) -> Dict[str, Any]:
        """
        """
            "registered_agents": list(self._agents.keys()),
            "registered_agent_types": list(self._agent_types.keys()),
            "default_agent_type": self._default_agent_type,
            "agent_count": len(self._agents),
        }

# Global agent registry instance
_simplified_agent_registry = None

def get_simplified_agent_registry() -> SimplifiedAgentRegistry:
    """
    """
    """
    """
    registry.register_agent_type("simple_text", PersonaAwareAgent)
    registry.register_agent_type("llm_agent", LLMAgent)

    # Create and register default instances
    persona_agent = PersonaAwareAgent()
    # Set capabilities if the class supports it
    if hasattr(persona_agent, "capabilities"):
        persona_agent.capabilities = [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.GENERAL,
        ]
    registry.register_agent(persona_agent)

    llm_agent = LLMAgent()
    # Set capabilities if the class supports it
    if hasattr(llm_agent, "capabilities"):
        llm_agent.capabilities = [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.QUESTION_ANSWERING,
            AgentCapability.CODE_GENERATION,
        ]
    registry.register_agent(llm_agent)

    # Try to register PhidataAgentWrapper if available
    try:

        pass
        from packages.agents.src.phidata_agent import PhidataAgentWrapper

        phidata_agent = PhidataAgentWrapper()
        # Set capabilities if the class supports it
        if hasattr(phidata_agent, "capabilities"):
            phidata_agent.capabilities = [
                AgentCapability.TEXT_GENERATION,
                AgentCapability.QUESTION_ANSWERING,
                AgentCapability.SUMMARIZATION,
            ]
        registry.register_agent(phidata_agent)
        logger.info("Registered PhidataAgentWrapper instance")
    except Exception:

        pass
        logger.info("PhidataAgentWrapper not available - skipping registration")

    # Set default agent type
    registry.set_default_agent_type("llm_agent")

    logger.info("Registered default agents in simplified registry")
