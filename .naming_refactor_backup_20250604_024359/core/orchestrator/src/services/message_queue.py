"""
"""
    """Standardized message format for agent communication"""
    """Message queue for reliable agent communication"""
        """Initialize the message queue."""
        logger.info("MessageQueue initialized")

    async def send_message(self, message: AgentMessage) -> str:
        """
        """
            await self._event_bus.publish_async("agent_message_sent", {"message": message.dict()})
        except Exception:

            pass
            logger.warning(f"Failed to publish agent_message_sent event: {e}")

        if message.recipient_id:
            # Direct message to specific agent
            if message.recipient_id not in self._queues:
                self._queues[message.recipient_id] = asyncio.Queue()
            await self._queues[message.recipient_id].put(message)
        else:
            # Broadcast to all registered handlers
            broadcast_count = 0
            for agent_id, handler_list in self._handlers.items():
                for handler in handler_list:
                    try:

                        pass
                        await handler(message)
                        broadcast_count += 1
                    except Exception:

                        pass
                        logger.error(f"Error in broadcast handler for agent {agent_id}: {e}")
                        await self._event_bus.publish_async(
                            "agent_message_error",
                            {"message_id": message.message_id, "error": str(e)},
                        )

        return message.message_id

    async def receive_message(self, agent_id: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """
        """

            return message
        except Exception:

            pass
            return None

    def register_handler(self, agent_id: str, handler: Callable[[AgentMessage], Awaitable[None]]):
        """
        """

    def unregister_handler(self, agent_id: str, handler: Callable[[AgentMessage], Awaitable[None]]) -> bool:
        """
        """
                return True
            except Exception:

                pass
                return False
        return False

    async def request_response(self, request: AgentMessage, timeout: float = 30.0) -> Optional[AgentMessage]:
        """
        """
            raise ValueError("Sender ID is required for request-response pattern")

        if not request.recipient_id:
            raise ValueError("Recipient ID is required for request-response pattern")

        # Set up for response tracking
        request.reply_to = request.sender_id

        # Create a future to wait for the response
        response_future = asyncio.Future()

        # Define a handler for the response
        async def response_handler(message: AgentMessage):
            if message.correlation_id == request.message_id or message.correlation_id == request.correlation_id:
                response_future.set_result(message)

        # Register temporary handler
        self.register_handler(request.sender_id, response_handler)

        try:


            pass
            # Send the request
            await self.send_message(request)

            # Wait for response with timeout
            return await asyncio.wait_for(response_future, timeout)
        except Exception:

            pass
            logger.warning(f"Request {request.message_id} timed out after {timeout}s")
            return None
        finally:
            # Clean up handler
            self.unregister_handler(request.sender_id, response_handler)

# Singleton instance
_message_queue = None

def get_message_queue() -> MessageQueue:
    """
    """