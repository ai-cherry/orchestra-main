"""
A simple test script to verify imports are working correctly.
"""

try:
    print("Testing imports...")
    
    # Import from packages.shared.src.models
    print("Importing base_models...")
    from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
    print("  Success: base_models imports work")
    
    # Import from packages.shared.src.memory
    print("Importing memory_manager...")
    from packages.shared.src.memory.memory_manager import MemoryManager, InMemoryMemoryManager
    print("  Success: memory_manager imports work")
    
    # Import from packages.shared.src.memory
    print("Importing stubs...")
    from packages.shared.src.memory.stubs import PatrickMemoryManager
    print("  Success: stubs imports work")
    
    print("All imports successful!")
    
except ImportError as e:
    print(f"Import Error: {e}")
    import sys
    print(f"Python path: {sys.path}")
