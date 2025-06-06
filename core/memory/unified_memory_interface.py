"""
Memory System Compatibility Layer
Provides unified interface for all memory implementations during transition
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

# Import the advanced memory system as the primary implementation
from core.memory.advanced_memory_system import (
    MemoryRouter as AdvancedMemoryRouter,
    MemoryLayer,
    ConversationalMemory,
    EpisodicMemory, 
    SemanticMemory
)

logger = logging.getLogger(__name__)

class MemoryCompatibilityLayer:
    """
    Compatibility layer for legacy memory interfaces
    Provides unified access to all memory systems during transition
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.advanced_memory_router = AdvancedMemoryRouter()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the memory compatibility layer"""
        if not self._initialized:
            await self.advanced_memory_router.initialize()
            self._initialized = True
            self.logger.info("Memory compatibility layer initialized")
    
    # ========================================
    # UNIFIED MEMORY INTERFACE
    # ========================================
    
    async def store_memory(self, 
                          key: str, 
                          value: Any, 
                          layer: Union[MemoryLayer, str] = MemoryLayer.CONTEXTUAL,
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Unified memory storage interface
        Compatible with all legacy memory systems
        """
        try:
            # Ensure initialization
            await self.initialize()
            
            # Convert string layer to enum if needed
            if isinstance(layer, str):
                layer = MemoryLayer(layer.lower())
            
            # Store using advanced memory system
            result = await self.advanced_memory_router.store_memory(
                key=key,
                content=value,
                layer=layer,
                metadata=metadata or {}
            )
            
            return result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error storing memory {key}: {e}")
            return False
    
    async def retrieve_memory(self, 
                            key: str, 
                            layer: Union[MemoryLayer, str] = MemoryLayer.CONTEXTUAL) -> Optional[Any]:
        """
        Unified memory retrieval interface
        Compatible with all legacy memory systems
        """
        try:
            # Ensure initialization
            await self.initialize()
            
            # Convert string layer to enum if needed
            if isinstance(layer, str):
                layer = MemoryLayer(layer.lower())
            
            # Retrieve using advanced memory system
            result = await self.advanced_memory_router.retrieve_memory(key, layer)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error retrieving memory {key}: {e}")
            return None
    
    async def search_memories(self, 
                            query: str, 
                            layer: Union[MemoryLayer, str] = MemoryLayer.CONTEXTUAL,
                            limit: int = 10) -> List[Dict[str, Any]]:
        """
        Unified memory search interface
        Compatible with all legacy memory systems
        """
        try:
            # Ensure initialization
            await self.initialize()
            
            # Convert string layer to enum if needed
            if isinstance(layer, str):
                layer = MemoryLayer(layer.lower())
            
            # Search using advanced memory system
            results = await self.advanced_memory_router.search_memories(
                query=query,
                layer=layer,
                limit=limit
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching memories: {e}")
            return []
    
    async def delete_memory(self, 
                          key: str, 
                          layer: Union[MemoryLayer, str] = MemoryLayer.CONTEXTUAL) -> bool:
        """
        Unified memory deletion interface
        Compatible with all legacy memory systems
        """
        try:
            # Ensure initialization
            await self.initialize()
            
            # Convert string layer to enum if needed
            if isinstance(layer, str):
                layer = MemoryLayer(layer.lower())
            
            # Delete using advanced memory system
            result = await self.advanced_memory_router.delete_memory(key, layer)
            
            return result.get("success", False)
            
        except Exception as e:
            self.logger.error(f"Error deleting memory {key}: {e}")
            return False
    
    # ========================================
    # LEGACY INTERFACE COMPATIBILITY
    # ========================================
    
    async def store(self, key: str, value: Any) -> bool:
        """Legacy store method for backward compatibility"""
        return await self.store_memory(key, value, MemoryLayer.CONTEXTUAL)
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Legacy retrieve method for backward compatibility"""
        return await self.retrieve_memory(key, MemoryLayer.CONTEXTUAL)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Legacy get method for backward compatibility"""
        result = await self.retrieve_memory(key, MemoryLayer.CONTEXTUAL)
        return result if result is not None else default
    
    async def set(self, key: str, value: Any) -> bool:
        """Legacy set method for backward compatibility"""
        return await self.store_memory(key, value, MemoryLayer.CONTEXTUAL)
    
    async def delete(self, key: str) -> bool:
        """Legacy delete method for backward compatibility"""
        return await self.delete_memory(key, MemoryLayer.CONTEXTUAL)
    
    async def exists(self, key: str) -> bool:
        """Check if memory key exists"""
        result = await self.retrieve_memory(key, MemoryLayer.CONTEXTUAL)
        return result is not None
    
    # ========================================
    # PERSONA-SPECIFIC MEMORY METHODS
    # ========================================
    
    async def store_persona_memory(self, 
                                 persona_id: str, 
                                 memory_type: str, 
                                 content: Any,
                                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store persona-specific memory"""
        
        key = f"{persona_id}:{memory_type}:{int(datetime.now().timestamp())}"
        
        # Determine appropriate layer based on memory type
        if memory_type in ["conversation", "interaction", "session"]:
            layer = MemoryLayer.CONTEXTUAL
        elif memory_type in ["experience", "event", "relationship"]:
            layer = MemoryLayer.EPISODIC
        else:
            layer = MemoryLayer.SEMANTIC
        
        # Add persona metadata
        full_metadata = {
            "persona_id": persona_id,
            "memory_type": memory_type,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        return await self.store_memory(key, content, layer, full_metadata)
    
    async def get_persona_memories(self, 
                                 persona_id: str, 
                                 memory_type: Optional[str] = None,
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """Get memories for specific persona"""
        
        try:
            # Search across all layers for persona memories
            all_memories = []
            
            for layer in MemoryLayer:
                memories = await self.advanced_memory_router.get_persona_memories(
                    persona_id=persona_id,
                    layer=layer,
                    limit=limit
                )
                
                # Filter by memory type if specified
                if memory_type:
                    memories = [
                        memory for memory in memories 
                        if memory.get("metadata", {}).get("memory_type") == memory_type
                    ]
                
                all_memories.extend(memories)
            
            # Sort by timestamp (most recent first)
            all_memories.sort(
                key=lambda x: x.get("metadata", {}).get("timestamp", ""), 
                reverse=True
            )
            
            return all_memories[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting persona memories for {persona_id}: {e}")
            return []
    
    async def get_persona_interactions(self, 
                                     persona_id: str, 
                                     limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent interactions for persona"""
        return await self.get_persona_memories(persona_id, "interaction", limit)
    
    async def get_persona_conversations(self, 
                                      persona_id: str, 
                                      limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent conversations for persona"""
        return await self.get_persona_memories(persona_id, "conversation", limit)
    
    # ========================================
    # STATISTICS AND MONITORING
    # ========================================
    
    async def get_layer_statistics(self, layer: Union[MemoryLayer, str]) -> Dict[str, Any]:
        """Get statistics for specific memory layer"""
        
        try:
            # Convert string layer to enum if needed
            if isinstance(layer, str):
                layer = MemoryLayer(layer.lower())
            
            return await self.advanced_memory_router.get_layer_statistics(layer)
            
        except Exception as e:
            self.logger.error(f"Error getting layer statistics: {e}")
            return {}
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        
        try:
            stats = {}
            
            # Get statistics for each layer
            for layer in MemoryLayer:
                layer_stats = await self.get_layer_statistics(layer)
                stats[layer.value] = layer_stats
            
            # Calculate totals
            total_memories = sum(
                layer_stats.get("count", 0) 
                for layer_stats in stats.values()
            )
            
            total_size_mb = sum(
                layer_stats.get("size_mb", 0) 
                for layer_stats in stats.values()
            )
            
            stats["totals"] = {
                "total_memories": total_memories,
                "total_size_mb": total_size_mb,
                "layers": len(MemoryLayer),
                "last_updated": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting memory statistics: {e}")
            return {}
    
    async def cleanup_memories(self, cleanup_config: Dict[str, Any]) -> Dict[str, Any]:
        """Cleanup old or unnecessary memories"""
        
        try:
            return await self.advanced_memory_router.cleanup_memories(cleanup_config)
            
        except Exception as e:
            self.logger.error(f"Error cleaning up memories: {e}")
            return {"success": False, "error": str(e)}
    
    # ========================================
    # CONFIGURATION METHODS
    # ========================================
    
    async def get_configuration(self) -> Dict[str, Any]:
        """Get memory system configuration"""
        
        try:
            return await self.advanced_memory_router.get_configuration()
            
        except Exception as e:
            self.logger.error(f"Error getting memory configuration: {e}")
            return {}
    
    async def update_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update memory system configuration"""
        
        try:
            return await self.advanced_memory_router.update_configuration(config)
            
        except Exception as e:
            self.logger.error(f"Error updating memory configuration: {e}")
            return {"success": False, "error": str(e)}

# ========================================
# LEGACY INTERFACE CLASSES
# ========================================

class LegacyMemoryManager:
    """Legacy memory manager interface for backward compatibility"""
    
    def __init__(self):
        self.compatibility_layer = MemoryCompatibilityLayer()
    
    async def store(self, key: str, value: Any) -> bool:
        return await self.compatibility_layer.store(key, value)
    
    async def retrieve(self, key: str) -> Optional[Any]:
        return await self.compatibility_layer.retrieve(key)
    
    async def get(self, key: str, default: Any = None) -> Any:
        return await self.compatibility_layer.get(key, default)
    
    async def set(self, key: str, value: Any) -> bool:
        return await self.compatibility_layer.set(key, value)
    
    async def delete(self, key: str) -> bool:
        return await self.compatibility_layer.delete(key)

class UnifiedMemory:
    """Unified memory interface for all memory operations"""
    
    def __init__(self):
        self.compatibility_layer = MemoryCompatibilityLayer()
    
    async def initialize(self):
        await self.compatibility_layer.initialize()
    
    async def store_memory(self, key: str, value: Any, layer: str = "contextual") -> bool:
        return await self.compatibility_layer.store_memory(key, value, layer)
    
    async def retrieve_memory(self, key: str, layer: str = "contextual") -> Optional[Any]:
        return await self.compatibility_layer.retrieve_memory(key, layer)
    
    async def search_memories(self, query: str, layer: str = "contextual", limit: int = 10) -> List[Dict[str, Any]]:
        return await self.compatibility_layer.search_memories(query, layer, limit)

# ========================================
# GLOBAL INSTANCES
# ========================================

# Global compatibility layer instance
memory_compatibility = MemoryCompatibilityLayer()

# Legacy interface instances for backward compatibility
memory_manager = LegacyMemoryManager()
unified_memory = UnifiedMemory()

# Export the advanced memory router as the primary interface
memory_router = memory_compatibility.advanced_memory_router

# Export all interfaces
__all__ = [
    "MemoryCompatibilityLayer",
    "LegacyMemoryManager", 
    "UnifiedMemory",
    "memory_compatibility",
    "memory_manager",
    "unified_memory",
    "memory_router",
    "MemoryLayer"
]

