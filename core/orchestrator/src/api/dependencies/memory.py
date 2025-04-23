"""
Memory manager dependency for AI Orchestration System.

This module provides the dependency injection function for the memory manager.
"""

import logging
from typing import Optional

from packages.shared.src.memory.memory_manager import MemoryManager
from packages.shared.src.memory.stubs import InMemoryMemoryManagerStub

# Configure logging
logger = logging.getLogger(__name__)


def get_memory_manager() -> MemoryManager:
    """
    Get the memory manager instance.
    
    For now, this returns an InMemoryMemoryManagerStub instance.
    
    Returns:
        An initialized memory manager
    """
    memory_manager = InMemoryMemoryManagerStub()
    memory_manager.initialize()
    return memory_manager
