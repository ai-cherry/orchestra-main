"""
"""
    """
    """
        """
        """
        """Initialize the agent asynchronously."""
        logger.info(f"MessagingAgent initialized: {self.config.get('agent_id')}")

    async def close_async(self) -> None:
        """Close the agent and release resources."""
        logger.info(f"MessagingAgent closed: {self.config.get('agent_id')}")

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        """
        if "delegate" in context.user_input.lower():
            # Get the delegate agent ID from config
            delegate_id = self.config.get("delegate_agent_id")

            if delegate_id:
                # Query the delegate agent
                delegate_response = await self.query_agent(
                    recipient_id=delegate_id,
                    query=context.user_input,
                    context={"original_context": context.dict()},
                )

                if delegate_response:
                    # Use the delegate's response
                    return AgentResponse(
                        text=f"Delegate says: {delegate_response.response}",
                        confidence=delegate_response.confidence * 0.9,
                        metadata={"delegated": True, "delegate_id": delegate_id},
                    )

        # Default processing
        return AgentResponse(
            text=f"I received your message: '{context.user_input}'",
            confidence=0.8,
            metadata={"agent_type": "MessagingAgent"},
        )

    async def query_agent(
        self, recipient_id: str, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[ProtocolResponse]:
        """
        """
        sender_id = self.config.get("agent_id", f"{self.__class__.__name__}_{id(self)}")

        # Create query content
        query_content = AgentQuery(query=query, context=context or {})

        # Create protocol message
        message_dict = create_protocol_message(sender=sender_id, recipient=recipient_id, content=query_content)

        # Convert to AgentMessage
        message = AgentMessage(**message_dict)

        # Send and wait for response
        message_queue = get_message_queue()
        response = await message_queue.request_response(message, timeout=30.0)

        if response and response.message_type == MessageType.RESPONSE:
            return ProtocolResponse(**response.content)

        return None

    async def _handle_query(self, message: AgentMessage) -> None:
        """
        """
            response_text = f"Response to: {query_data.query}"

            # Create response content
            response_content = ProtocolResponse(response=response_text, confidence=0.9)

            # Create protocol message
            response_dict = create_protocol_message(
                sender=self.config.get("agent_id", f"{self.__class__.__name__}_{id(self)}"),
                recipient=message.sender_id,
                content=response_content,
                correlation_id=message.message_id,
                conversation_id=message.conversation_id,
            )

            # Send response
            response_message = AgentMessage(**response_dict)
            message_queue = get_message_queue()
            await message_queue.send_message(response_message)

        except Exception:


            pass
            logger.error(f"Error handling query: {e}")

    async def _handle_status(self, message: AgentMessage) -> None:
        """
        """
        logger.info(f"Received status from {message.sender_id}: {message.content}")

    def can_handle(self, context: AgentContext) -> float:
        """
        """