"""
LangChain Memory Adapter for Orchestra.

This module provides integration between Orchestra's memory system and
LangChain's specialized memory modules such as ConversationBufferMemory,
EntityMemory, and SummaryMemory.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Union, Type, Tuple
from datetime import datetime

from packages.shared.src.memory.base_memory_manager import MemoryProvider
from packages.shared.src.models.base_models import MemoryItem

# Configure logging
logger = logging.getLogger(__name__)


class LangChainMemoryAdapter(MemoryProvider):
    """
    Adapter for LangChain's memory modules.

    This adapter:
    1. Implements Orchestra's memory provider interface
    2. Connects to LangChain's specialized memory modules
    3. Provides features like summarization and entity extraction
    4. Enhances Orchestra's memory with structured knowledge
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LangChain Memory Adapter.

        Args:
            config: Configuration options for the adapter
        """
        self.config = config or {}
        self.langchain_memories = {}
        self.llm = None
        self.embeddings = None
        self.vectorstore = None
        self.memory_router = None
        self._initialized = False
        logger.info("LangChainMemoryAdapter initialized with config")

    async def initialize(self) -> bool:
        """Initialize LangChain memory components."""
        try:
            # Import required LangChain modules
            try:
                from langchain.memory import (
                    ConversationBufferMemory,
                    EntityMemory,
                    SummaryMemory,
                )
                from langchain.llms.gemini import Gemini
                from langchain.embeddings import VertexAIEmbeddings
                from langchain.vectorstores import Chroma
                from langchain.chains import LLMChain
                from langchain.prompts import PromptTemplate

                self.ConversationBufferMemory = ConversationBufferMemory
                self.EntityMemory = EntityMemory
                self.SummaryMemory = SummaryMemory
                self.Gemini = Gemini
                self.VertexAIEmbeddings = VertexAIEmbeddings
                self.Chroma = Chroma
                self.LLMChain = LLMChain
                self.PromptTemplate = PromptTemplate
            except ImportError:
                logger.warning(
                    "LangChain library not available. Install with: pip install langchain langchain-community"
                )
                return False

            # Initialize Gemini model for memories
            gemini_api_key = self.config.get("gemini_api_key")
            gemini_model = self.config.get("gemini_model", "gemini-2.5-flash")

            if not gemini_api_key:
                logger.warning("Gemini API key not provided")
                # Try to fetch from environment
                import os

                gemini_api_key = os.environ.get("GEMINI_API_KEY")
                if not gemini_api_key:
                    logger.error("No Gemini API key available")
                    return False

            # Initialize LLM for memory operations
            self.llm = self.Gemini(
                model_name=gemini_model,
                api_key=gemini_api_key,
                verbose=self.config.get("verbose", False),
                temperature=self.config.get("temperature", 0.2),
            )

            # Initialize embeddings
            self.embeddings = self.VertexAIEmbeddings(
                model_name=self.config.get(
                    "embedding_model", "textembedding-gecko@latest"
                )
            )

            # Set up vector store if enabled
            if self.config.get("use_vectorstore", True):
                await self._setup_vectorstore()

            # Initialize memory components
            await self._setup_memory_components()

            self._initialized = True
            logger.info("LangChainMemoryAdapter initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LangChainMemoryAdapter: {e}")
            return False

    async def _setup_vectorstore(self) -> None:
        """Set up vector store for semantic search."""
        try:
            # Configuration for vector store
            collection_name = self.config.get("collection_name", "orchestra_memories")
            persist_directory = self.config.get("persist_directory", "./chroma_db")

            # Initialize Chroma vector store
            self.vectorstore = self.Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory,
            )

            logger.info(
                f"Initialized Chroma vector store with collection: {collection_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise

    async def _setup_memory_components(self) -> None:
        """Set up LangChain memory components."""
        # Initialize Conversation Buffer Memory
        self.conversation_memory = self.ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output",
            input_key="input",
            ai_prefix=self.config.get("ai_prefix", "AI"),
            human_prefix=self.config.get("human_prefix", "Human"),
        )

        # Initialize Entity Memory
        self.entity_memory = self.EntityMemory(
            llm=self.llm,
            k=self.config.get("entity_k", 5),
            chat_history_key="chat_history",
        )

        # Initialize Summary Memory
        self.summary_memory = self.SummaryMemory(
            llm=self.llm,
            memory_key="chat_history",
            input_key="input",
            output_key="output",
            max_token_limit=self.config.get("summary_limit", 1000),
        )

        # Save references
        self.langchain_memories["conversation"] = self.conversation_memory
        self.langchain_memories["entity"] = self.entity_memory
        self.langchain_memories["summary"] = self.summary_memory

        logger.info("LangChain memory components initialized")

    async def close(self) -> None:
        """Close the adapter and release resources."""
        try:
            # Persist vector store if needed
            if self.vectorstore and hasattr(self.vectorstore, "persist"):
                self.vectorstore.persist()

            # Clear memory components
            self.langchain_memories = {}
            self.llm = None
            self.embeddings = None
            self.vectorstore = None

            logger.info("LangChainMemoryAdapter closed")
        except Exception as e:
            logger.error(f"Error closing LangChainMemoryAdapter: {e}")

    async def add_memory(self, item: MemoryItem) -> str:
        """
        Add a memory item to LangChain's memory components.

        Args:
            item: The memory item to add

        Returns:
            ID of the added memory item
        """
        if not self._initialized:
            logger.warning("LangChainMemoryAdapter not initialized")
            return None

        try:
            # Extract information from the memory item
            is_ai = item.metadata.get("source") != "user"
            content = item.text_content or ""

            # Format as input/output based on source
            input_text = content if not is_ai else ""
            output_text = content if is_ai else ""

            # Add to conversation memory
            if not is_ai:
                # Only explicitly add human messages
                self.conversation_memory.save_context(
                    {"input": content}, {"output": ""}
                )

            # Add to entity memory
            if self.config.get("use_entity_memory", True):
                await self._add_to_entity_memory(item, input_text, output_text)

            # Add to summary memory
            if self.config.get("use_summary_memory", True):
                await self._add_to_summary_memory(item, input_text, output_text)

            # Add to vector store
            if self.vectorstore and self.config.get("use_vectorstore", True):
                text_to_store = content
                metadata = {
                    "user_id": item.user_id,
                    "session_id": item.session_id,
                    "timestamp": item.timestamp.isoformat()
                    if item.timestamp
                    else datetime.now().isoformat(),
                    "is_ai": is_ai,
                    "item_type": item.item_type,
                    "persona": item.persona_active,
                }

                # Add to vector store
                ids = self.vectorstore.add_texts(
                    texts=[text_to_store], metadatas=[metadata]
                )

                memory_id = ids[0] if ids else None

                # Update memory item with LangChain ID
                if item.metadata is None:
                    item.metadata = {}
                item.metadata["langchain_memory_id"] = memory_id

                return memory_id

            # Generate a default ID if vector store not used
            import uuid

            memory_id = str(uuid.uuid4())

            # Update memory item with LangChain ID
            if item.metadata is None:
                item.metadata = {}
            item.metadata["langchain_memory_id"] = memory_id

            return memory_id
        except Exception as e:
            logger.error(f"Error adding memory to LangChain: {e}")
            return None

    async def _add_to_entity_memory(
        self, item: MemoryItem, input_text: str, output_text: str
    ) -> None:
        """Add memory item to entity memory."""
        if not input_text:
            return

        try:
            # Add to entity memory
            await asyncio.to_thread(
                self.entity_memory.save_context,
                {"input": input_text},
                {"output": output_text},
            )
        except Exception as e:
            logger.error(f"Error adding to entity memory: {e}")

    async def _add_to_summary_memory(
        self, item: MemoryItem, input_text: str, output_text: str
    ) -> None:
        """Add memory item to summary memory."""
        try:
            # Add to summary memory
            await asyncio.to_thread(
                self.summary_memory.save_context,
                {"input": input_text or ""},
                {"output": output_text or ""},
            )
        except Exception as e:
            logger.error(f"Error adding to summary memory: {e}")

    async def get_memories(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """
        Retrieve memories from LangChain memory components.

        Args:
            user_id: The user ID
            session_id: Optional session ID
            query: Optional semantic search query
            limit: Maximum number of memories to retrieve

        Returns:
            List of memory items
        """
        if not self._initialized:
            logger.warning("LangChainMemoryAdapter not initialized")
            return []

        try:
            if query and self.vectorstore:
                # Perform semantic search
                results = await self._semantic_search(query, user_id, session_id, limit)
                return results
            else:
                # Get recent memories from conversation buffer
                conversation_memories = await self._get_conversation_memories(
                    user_id, session_id, limit
                )

                # Combine with entity information if available
                if self.config.get("use_entity_memory", True):
                    entity_info = await self._get_entity_information(query)
                    if entity_info:
                        # Create a special memory item for entity information
                        entity_memory = MemoryItem(
                            user_id=user_id,
                            session_id=session_id,
                            item_type="entity_information",
                            text_content=f"Entity Information: {json.dumps(entity_info, indent=2)}",
                            metadata={"source": "system", "entities": entity_info},
                        )
                        conversation_memories.insert(0, entity_memory)

                # Add conversation summary if available
                if self.config.get("use_summary_memory", True):
                    summary = await self._get_conversation_summary()
                    if summary:
                        # Create a special memory item for summary
                        summary_memory = MemoryItem(
                            user_id=user_id,
                            session_id=session_id,
                            item_type="conversation_summary",
                            text_content=f"Conversation Summary: {summary}",
                            metadata={"source": "system", "summary": summary},
                        )
                        conversation_memories.insert(0, summary_memory)

                return conversation_memories
        except Exception as e:
            logger.error(f"Error retrieving memories from LangChain: {e}")
            return []

    async def _semantic_search(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """Perform semantic search using vector store."""
        try:
            # Add filters for user_id and session_id if needed
            filter_dict = {"user_id": user_id}
            if session_id:
                filter_dict["session_id"] = session_id

            # Execute the search
            results = await asyncio.to_thread(
                self.vectorstore.similarity_search_with_relevance_scores,
                query=query,
                k=limit,
                filter=filter_dict if filter_dict else None,
            )

            # Convert results to memory items
            memory_items = []
            for doc, score in results:
                try:
                    # Extract metadata
                    metadata = doc.metadata.copy() if hasattr(doc, "metadata") else {}

                    # Parse timestamp
                    timestamp = None
                    if "timestamp" in metadata:
                        try:
                            timestamp = datetime.fromisoformat(metadata["timestamp"])
                        except:
                            pass

                    # Create memory item
                    memory_item = MemoryItem(
                        user_id=metadata.get("user_id", user_id),
                        session_id=metadata.get("session_id", session_id),
                        timestamp=timestamp,
                        item_type=metadata.get("item_type", "retrieved_memory"),
                        persona_active=metadata.get("persona", None),
                        text_content=doc.page_content
                        if hasattr(doc, "page_content")
                        else str(doc),
                        metadata={
                            **metadata,
                            "relevance_score": score,
                            "source": "system"
                            if metadata.get("is_ai", False)
                            else "user",
                        },
                    )

                    memory_items.append(memory_item)
                except Exception as e:
                    logger.error(f"Error converting search result to memory item: {e}")

            return memory_items
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return []

    async def _get_conversation_memories(
        self, user_id: str, session_id: Optional[str] = None, limit: int = 10
    ) -> List[MemoryItem]:
        """Get memories from conversation buffer."""
        try:
            # Retrieve conversation history
            chat_history = self.conversation_memory.chat_memory.messages

            # Convert to memory items
            memory_items = []
            for i, message in enumerate(chat_history[-limit:]):
                try:
                    # Determine if AI or human
                    is_ai = getattr(message, "type", "") == "ai"

                    # Create memory item
                    memory_item = MemoryItem(
                        user_id=user_id,
                        session_id=session_id,
                        item_type="conversation",
                        text_content=getattr(message, "content", str(message)),
                        metadata={
                            "source": "system" if is_ai else "user",
                            "message_index": i,
                        },
                    )

                    memory_items.append(memory_item)
                except Exception as e:
                    logger.error(f"Error converting message to memory item: {e}")

            return memory_items
        except Exception as e:
            logger.error(f"Error retrieving conversation memories: {e}")
            return []

    async def _get_entity_information(
        self, query: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get entity information from entity memory."""
        try:
            # If query is provided, look up specific entities
            if query:
                entities = await asyncio.to_thread(
                    self.entity_memory.get_entities_from_text, text=query
                )

                # Look up each entity
                entity_info = {}
                for entity in entities:
                    info = await asyncio.to_thread(
                        self.entity_memory.load_entity_from_memory, entity=entity
                    )
                    if info:
                        entity_info[entity] = info

                return entity_info
            else:
                # Return all entities
                return self.entity_memory.entity_store.store
        except Exception as e:
            logger.error(f"Error retrieving entity information: {e}")
            return {}

    async def _get_conversation_summary(self) -> Optional[str]:
        """Get conversation summary from summary memory."""
        try:
            # Retrieve summary
            if hasattr(self.summary_memory, "buffer"):
                return self.summary_memory.buffer
            return None
        except Exception as e:
            logger.error(f"Error retrieving conversation summary: {e}")
            return None
