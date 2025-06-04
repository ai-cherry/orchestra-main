"""
"""
    """
    """
        log_level: str = "INFO",
        enable_metrics: bool = True,
        enable_tracing: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        """
        logger.info(f"ObservableAgent initialized for agent_id: {agent_id}")

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        """
        context.metadata["operation_id"] = operation_id
        context.metadata["agent_id"] = self.agent_id

        # Log the start of processing
        logger.info(
            f"Agent {self.agent_id} processing started",
            extra={
                "agent_id": self.agent_id,
                "operation_id": operation_id,
                "context_type": type(context).__name__,
                "user_input_length": (len(context.user_input) if context.user_input else 0),
            },
        )

        try:


            pass
            # Process with the wrapped agent
            response = await self.wrapped_agent.process(context)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Log the successful completion
            logger.info(
                f"Agent {self.agent_id} processing completed",
                extra={
                    "agent_id": self.agent_id,
                    "operation_id": operation_id,
                    "processing_time_ms": int(processing_time * 1000),
                    "response_length": len(response.text) if response.text else 0,
                    "confidence": response.confidence,
                },
            )

            # Store in memory if available
            if self.memory:
                memory_key = f"interaction:{operation_id}"
                memory_value = {
                    "user_input": context.user_input,
                    "agent_response": response.text,
                    "confidence": response.confidence,
                    "processing_time": processing_time,
                    "timestamp": time.time(),
                }

                try:


                    pass
                    await self.memory.store(
                        key=memory_key,
                        value=memory_value,
                        layer="short_term",
                        metadata={
                            "agent_id": self.agent_id,
                            "operation_id": operation_id,
                            "interaction_type": "user_query",
                        },
                    )
                except Exception:

                    pass
                    logger.warning(f"Failed to store in memory: {e}")

            # Record metrics if enabled
            if self.enable_metrics:
                self._record_metrics(
                    operation_id=operation_id,
                    processing_time=processing_time,
                    response_length=len(response.text) if response.text else 0,
                    confidence=response.confidence,
                    success=True,
                )

            # Add observability metadata to response
            if response.metadata is None:
                response.metadata = {}
            response.metadata.update(
                {
                    "operation_id": operation_id,
                    "processing_time_ms": int(processing_time * 1000),
                    "agent_id": self.agent_id,
                }
            )

            return response

        except Exception:


            pass
            # Calculate processing time
            processing_time = time.time() - start_time

            # Log the error
            logger.error(
                f"Agent {self.agent_id} processing failed: {e}",
                extra={
                    "agent_id": self.agent_id,
                    "operation_id": operation_id,
                    "processing_time_ms": int(processing_time * 1000),
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                },
            )

            # Record metrics if enabled
            if self.enable_metrics:
                self._record_metrics(
                    operation_id=operation_id,
                    processing_time=processing_time,
                    response_length=0,
                    confidence=0.0,
                    success=False,
                    error=str(e),
                )

            # Create error response
            error_response = AgentResponse(
                text=f"An error occurred while processing your request: {e}",
                confidence=0.0,
                metadata={
                    "operation_id": operation_id,
                    "processing_time_ms": int(processing_time * 1000),
                    "agent_id": self.agent_id,
                    "error": str(e),
                },
            )

            return error_response

    def can_handle(self, context: AgentContext) -> float:
        """
        """
        """Initialize the agent asynchronously."""
        logger.info(f"Initializing agent {self.agent_id}")

        # Initialize wrapped agent if it has an initialize_async method
        if hasattr(self.wrapped_agent, "initialize_async") and callable(self.wrapped_agent.initialize_async):
            await self.wrapped_agent.initialize_async()

        logger.info(f"Agent {self.agent_id} initialized")

    async def close_async(self) -> None:
        """Close the agent and release resources asynchronously."""
        logger.info(f"Closing agent {self.agent_id}")

        # Close wrapped agent if it has a close_async method
        if hasattr(self.wrapped_agent, "close_async") and callable(self.wrapped_agent.close_async):
            await self.wrapped_agent.close_async()

        logger.info(f"Agent {self.agent_id} closed")

    def _record_metrics(
        self,
        operation_id: str,
        processing_time: float,
        response_length: int,
        confidence: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        """
            "agent_id": self.agent_id,
            "operation_id": operation_id,
            "processing_time_ms": int(processing_time * 1000),
            "response_length": response_length,
            "confidence": confidence,
            "success": success,
        }

        if error:
            metrics["error"] = error

        # In a production environment, send to Cloud Monitoring
        # For now, just log as JSON

class ObservableAgentFactory:
    """
    """
        """
        """
        log_level: str = "INFO",
        enable_metrics: bool = True,
        enable_tracing: bool = True,
        config: Optional[Dict[str, Any]] = None,
    ) -> ObservableAgent:
        """
        """