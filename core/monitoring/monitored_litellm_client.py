"""
"""
    """
    """
        """
        """
            storage_backend=os.getenv("MONITOR_STORAGE_BACKEND", "memory"),
        )

        self.monitor_all_models = monitor_all_models

        logger.info("Initialized monitored LiteLLM client")

    def _should_monitor(self, model: str) -> bool:
        """Check if the model should be monitored"""
        return "claude" in model.lower()

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
        # Additional monitoring parameters
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        """
        """
        """
        messages = [LLMMessage(role="user", content=prompt)]
        return await self.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop,
            user=user,
            timeout=timeout,
            session_id=session_id,
            metadata=metadata,
        )

    async def get_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        user: Optional[str] = None,
        timeout: Optional[int] = None,
        # Additional monitoring parameters
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMEmbeddingResponse:
        """
        """
        """
        """
            "total_calls": summary.total_calls,
            "successful_calls": summary.successful_calls,
            "failed_calls": summary.failed_calls,
            "total_input_tokens": summary.total_input_tokens,
            "total_output_tokens": summary.total_output_tokens,
            "total_cost_usd": summary.total_cost_usd,
            "average_latency_ms": summary.average_latency_ms,
            "calls_by_model": dict(summary.calls_by_model),
            "tokens_by_model": dict(summary.tokens_by_model),
            "cost_by_model": dict(summary.cost_by_model),
            "errors_by_type": dict(summary.errors_by_type),
        }

    def export_monitoring_data(self, format: str = "json", **kwargs) -> str:
        """
        """