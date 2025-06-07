"""Centralized error handling utilities"""
    """Base exception for cherry_ai system"""
    """Centralized error handling with logging and recovery"""
    def handle_error(error: Exception, context: str = "") -> Dict[str, Any]:
        """Handle and log errors consistently"""
        logger.error(f"Error in {context}: {error}", exc_info=True)
        return error_info
    
    @staticmethod
    async def safe_execute(coro, context: str = "", default=None):
        """Execute coroutine with error handling"""
    """Decorator for consistent error handling"""