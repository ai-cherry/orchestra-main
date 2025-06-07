"""
"""
    """Base class for items stored in memory."""
    user_id: str = ""
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    item_type: str = "generic"
    content: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class MemoryProvider(ABC):
    """Abstract base class for memory providers."""
        """
        """
        """
        """
        """
        """
    """Memory provider that stores items in memory."""
        """Initialize the in-memory provider."""
        """Add an item to memory."""
        """Get an item from memory by ID."""
        """Get items from memory."""
    """
    """
        """
        """
        logger.info(f"MemoryManager initialized with provider: {self._provider.__class__.__name__}")

    def add_memory(
        self,
        user_id: str,
        content: Any,
        session_id: str = None,
        item_type: str = "conversation",
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        """
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        # Create memory item
        item = MemoryItem(
            user_id=user_id,
            session_id=session_id,
            item_type=item_type,
            content=content,
            metadata=metadata or {},
        )

        # Add to provider
        return self._provider.add_item(item)

    def get_memory(self, item_id: str) -> Optional[MemoryItem]:
        """
        """
        """
        """
            item_type="conversation",
            limit=limit,
        )

    def get_memories_by_type(
        self,
        user_id: str,
        item_type: str,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryItem]:
        """
        """
    """
    """