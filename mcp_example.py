#!/usr/bin/env python3
"""
mcp_example.py - Example usage of the Simple MCP System

This script demonstrates how to use the Simple MCP System for memory
sharing between Roo and Cline.
"""

import json
from simple_mcp import (
    SimpleMemoryManager, 
    ContextSession, 
    ToolType, 
    MemoryScope,
    initialize_shared_memory
)

def basic_memory_example():
    """Demonstrate basic memory operations."""
    print("\n=== Basic Memory Operations ===\n")
    
    # Create memory manager
    memory = SimpleMemoryManager()
    
    # Save some items with metadata
    memory.save_with_metadata(
        key="design_decision",
        content="We'll use a file-based approach for simplicity",
        tags=["design", "architecture", "simplicity"],
        importance=0.8,
        source_tool=ToolType.ROO,
        scope=MemoryScope.PROJECT
    )
    
    memory.save_with_metadata(
        key="implementation_note",
        content="Use JSON for storage to maintain metadata",
        tags=["implementation", "storage", "json"],
        importance=0.6,
        source_tool=ToolType.CLINE,
        scope=MemoryScope.PROJECT
    )
    
    # Retrieve items
    design_item = memory.retrieve_with_metadata("design_decision", MemoryScope.PROJECT)
    if design_item:
        print(f"Retrieved design decision: {design_item.content}")
        print(f"Tags: {design_item.tags}")
        print(f"Importance: {design_item.importance}")
        print(f"Source tool: {design_item.source_tool}")
        print()
    
    # Search by tags
    print("Searching for items with 'design' or 'implementation' tags:")
    results = memory.retrieve_by_tags(
        tags=["design", "implementation"],
        match_all=False,
        scope=MemoryScope.PROJECT
    )
    
    for i, result in enumerate(results):
        print(f"Result {i+1}:")
        print(f"  Key: {result['key']}")
        print(f"  Tags: {result['item'].tags}")
        print(f"  Content: {result['item'].content}")
        print()

def context_session_example():
    """Demonstrate context preservation."""
    print("\n=== Context Session Example ===\n")
    
    # Create memory manager
    memory = SimpleMemoryManager()
    
    # Create a context session
    with ContextSession(memory, ToolType.ROO) as session:
        # This would normally execute with Roo, but we'll simulate it
        print("Simulating context session execution...")
        
        # First prompt
        print("Step 1: Design a feature")
        # result = session.execute_in_mode("architect", "Design a feature")
        # Simulated result
        result1 = "Feature design: A file-based memory system with metadata support"
        session.context = result1
        print(f"Result: {result1}")
        
        # Second prompt (with automatic context preservation)
        print("\nStep 2: Implement the feature")
        # result = session.execute_in_mode("code", "Implement the feature")
        # Simulated result
        result2 = "Implementation complete: Created SimpleMemoryManager class with metadata support"
        session.context = result2
        print(f"Result: {result2}")
        
        # Third prompt (with automatic context preservation)
        print("\nStep 3: Test the feature")
        # result = session.execute_in_mode("debug", "Test the feature")
        # Simulated result
        result3 = "Tests passed: SimpleMemoryManager correctly handles metadata and tagging"
        session.context = result3
        print(f"Result: {result3}")
    
    # The context is automatically saved when the session ends
    print("\nSession ended, context saved to memory")

def automatic_integration_example():
    """Demonstrate automatic integration with Roo and Cline."""
    print("\n=== Automatic Integration Example ===\n")
    
    # Initialize the shared memory system
    success = initialize_shared_memory()
    
    if success:
        print("Shared memory system initialized successfully")
        print("Now Roo and Cline will automatically use the shared memory system")
        print("Any memory operations performed by either tool will be visible to the other")
    else:
        print("Failed to initialize shared memory system")
        print("This is expected if Roo or Cline modules are not available")

def create_session_script():
    """Create an example session script file."""
    script_content = """# Example session script
# Format: mode: prompt

# First prompt
architect: Design a simple memory system for sharing context between AI tools

# Second prompt (will automatically receive context from first prompt)
code: Implement the core classes for the memory system

# Third prompt (will automatically receive context from previous prompts)
debug: Test the memory system implementation
"""
    
    with open("example_session.txt", "w") as f:
        f.write(script_content)
    
    print("\nCreated example session script: example_session.txt")
    print("You can run it with: python mcp_example.py session --tool roo --script example_session.txt")

def main():
    """Run all examples."""
    print("Simple MCP System Examples")
    print("=========================")
    
    basic_memory_example()
    context_session_example()
    automatic_integration_example()
    create_session_script()
    
    print("\nAll examples completed successfully!")
    print("\nTo use the Simple MCP System in your own code:")
    print("1. Import the necessary components from simple_mcp")
    print("2. Create a SimpleMemoryManager instance")
    print("3. Use save_with_metadata() and retrieve_with_metadata() for rich memory operations")
    print("4. Use ContextSession for automatic context preservation")
    print("5. Call initialize_shared_memory() to automatically integrate with Roo and Cline")

if __name__ == "__main__":
    main()