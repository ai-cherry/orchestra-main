"""
"""
    """
    """
        """Initialize the mixin."""
        """
        """
        """
        """
                    logger.error(f"Error in message handler: {e}")
            return True
        return False

    async def start_message_processing(self):
        """Start background task to process messages."""
        """Stop background message processing."""
        """Background task to process messages."""
        agent_id = getattr(self, "config", {}).get("agent_id", f"{self.__class__.__name__}_{id(self)}")

        message_queue = get_message_queue()

        while self._processing_messages:
            try:

                pass
                # Wait for a message with a short timeout
                message = await message_queue.receive_message(agent_id, timeout=1.0)

                if message:
                    # Try to handle the message
                    handled = await self.handle_message(message)

                    if not handled:
                        logger.warning(f"No handler for message type: {message.message_type}")
            except Exception:

                pass
                break
            except Exception:

                pass
                logger.error(f"Error processing messages: {e}")
                await asyncio.sleep(1.0)  # Avoid tight loop on errors
