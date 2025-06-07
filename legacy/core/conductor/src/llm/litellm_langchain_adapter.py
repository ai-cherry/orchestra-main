"""
"""
    """
    """
        return "litellm"

    def __init__(
        self,
        client: LiteLLMClient,
        model: Optional[str] = None,
        temperature: float = 0.02,
    ):
        super().__init__()
        self.client = client
        self.model = model
        self.temperature = temperature

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """
        """
        """
        """
    """
    """
        return "litellm-chat"

    def __init__(
        self,
        client: LiteLLMClient,
        model: Optional[str] = None,
        temperature: float = 0.02,
    ):
        super().__init__()
        self.client = client
        self.model = model
        self.temperature = temperature

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """
        """
            generations=[[ChatGeneration(message=ChatMessage(role="assistant", content=response))]],
            llm_output={"provider": "litellm"},
        )

    async def _achat(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        """