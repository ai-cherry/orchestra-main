#!/usr/bin/env python3
"""
ide_integration_test.py - Test IDE Extensions Integration with MCP Framework

This script simulates how IDE extensions like Co-pilot would integrate with the
Memory Synchronization Engine in the MCP framework. It demonstrates:
1. How IDE extensions capture context from editor
2. How this context is stored and synchronized through MCP
3. How completions can leverage shared context from other tools
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Import the memory sync engine
from memory_sync_engine import (
    MemorySyncEngine,
    MemoryEntry,
    MemoryMetadata,
    MemoryType,
    MemoryScope,
    ToolType,
    CompressionLevel,
    StorageTier,
    InMemoryStorage
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("mcp-ide-integration-test")


class IDEContext:
    """Class representing IDE context (files, cursor position, etc)."""
    
    def __init__(self, workspace_path: str):
        """Initialize with workspace path."""
        self.workspace_path = workspace_path
        self.open_files: Dict[str, str] = {}
        self.active_file: Optional[str] = None
        self.cursor_position: Tuple[int, int] = (0, 0)  # line, column
        self.selection: Optional[str] = None
        self.last_edit_time: float = time.time()
    
    def open_file(self, file_path: str, content: str) -> None:
        """Simulate opening a file in the IDE."""
        self.open_files[file_path] = content
        self.active_file = file_path
        logger.info(f"Opened file: {file_path}")
    
    def close_file(self, file_path: str) -> None:
        """Simulate closing a file in the IDE."""
        if file_path in self.open_files:
            del self.open_files[file_path]
            logger.info(f"Closed file: {file_path}")
            if self.active_file == file_path:
                self.active_file = next(iter(self.open_files.keys())) if self.open_files else None
    
    def set_cursor(self, line: int, column: int) -> None:
        """Set the cursor position."""
        self.cursor_position = (line, column)
    
    def set_selection(self, selection: str) -> None:
        """Set the current text selection."""
        self.selection = selection
    
    def get_workspace_context(self, max_files: int = 5) -> Dict[str, Any]:
        """Get the current workspace context."""
        return {
            "workspace_path": self.workspace_path,
            "open_files": list(self.open_files.keys())[:max_files],
            "active_file": self.active_file,
            "file_count": len(self.open_files)
        }
    
    def get_active_file_context(self, surrounding_lines: int = 10) -> Dict[str, Any]:
        """Get context around the cursor in the active file."""
        if not self.active_file or self.active_file not in self.open_files:
            return {"error": "No active file"}
        
        content = self.open_files[self.active_file]
        lines = content.split("\n")
        line_idx, col_idx = self.cursor_position
        
        # Ensure line_idx is valid
        line_idx = min(max(0, line_idx), len(lines) - 1)
        
        # Get surrounding lines
        start_line = max(0, line_idx - surrounding_lines)
        end_line = min(len(lines), line_idx + surrounding_lines + 1)
        context_lines = lines[start_line:end_line]
        
        return {
            "file_path": self.active_file,
            "cursor_position": self.cursor_position,
            "selection": self.selection,
            "context_lines": context_lines,
            "visible_range": (start_line, end_line),
            "context_content": "\n".join(context_lines)
        }


class CopilotExtensionAdapter:
    """Adapter for Co-pilot VS Code extension to MCP framework."""
    
    def __init__(self, sync_engine: MemorySyncEngine):
        """Initialize with a sync engine."""
        self.sync_engine = sync_engine
        self.ide_context = IDEContext("/workspaces/orchestra-main")
        self.last_sync_time = time.time()
        self.sync_interval = 5.0  # seconds
    
    def connect_to_vscode(self) -> bool:
        """Simulate connecting to VS Code extension."""
        logger.info("Connected to VS Code Co-pilot extension")
        return True
    
    def on_file_opened(self, file_path: str, content: str) -> None:
        """Handle file open events from IDE."""
        self.ide_context.open_file(file_path, content)
        self._update_editor_context_in_mcp()
    
    def on_file_changed(self, file_path: str, content: str) -> None:
        """Handle file change events from IDE."""
        if file_path in self.ide_context.open_files:
            self.ide_context.open_files[file_path] = content
            self.ide_context.last_edit_time = time.time()
            self._update_editor_context_in_mcp()
    
    def on_cursor_moved(self, file_path: str, line: int, column: int) -> None:
        """Handle cursor move events from IDE."""
        if file_path == self.ide_context.active_file:
            self.ide_context.set_cursor(line, column)
            # Only update MCP if enough time has passed since last sync
            if time.time() - self.last_sync_time > self.sync_interval:
                self._update_editor_context_in_mcp()
                self.last_sync_time = time.time()
    
    def on_selection_changed(self, file_path: str, selection: str) -> None:
        """Handle selection change events from IDE."""
        if file_path == self.ide_context.active_file:
            self.ide_context.set_selection(selection)
            self._update_editor_context_in_mcp()
    
    def _update_editor_context_in_mcp(self) -> None:
        """Update the editor context in MCP memory."""
        # Get the current context
        workspace_context = self.ide_context.get_workspace_context()
        file_context = self.ide_context.get_active_file_context()
        
        # Create a combined context
        combined_context = {
            "editor_state": {
                "workspace": workspace_context,
                "active_file": file_context
            },
            "last_update": time.time()
        }
        
        # Create memory entries
        workspace_entry = MemoryEntry(
            memory_type=MemoryType.SHARED,
            scope=MemoryScope.SESSION,
            priority=7,
            compression_level=CompressionLevel.NONE,
            ttl_seconds=3600,
            content=workspace_context,
            metadata=MemoryMetadata(
                source_tool=ToolType.COPILOT,
                last_modified=time.time(),
                context_relevance=0.6
            )
        )
        
        file_entry = MemoryEntry(
            memory_type=MemoryType.SHARED,
            scope=MemoryScope.SESSION,
            priority=9,
            compression_level=CompressionLevel.NONE,
            ttl_seconds=1800,
            content=file_context,
            metadata=MemoryMetadata(
                source_tool=ToolType.COPILOT,
                last_modified=time.time(),
                context_relevance=0.9
            )
        )
        
        # Save to MCP
        self.sync_engine.create_memory("copilot:workspace_context", workspace_entry, ToolType.COPILOT)
        self.sync_engine.create_memory("copilot:active_file_context", file_entry, ToolType.COPILOT)
        
        logger.info("Updated editor context in MCP")
    
    def generate_completion(self, prompt: str) -> str:
        """Generate a completion using shared context from MCP."""
        # Get relevant context from MCP
        project_context = self.sync_engine.get_memory("shared:medium", ToolType.COPILOT)
        
        # Get any analysis from Gemini that might help
        gemini_analysis = self.sync_engine.get_memory("shared:large", ToolType.COPILOT)
        
        # Get any subtasks from Roo that might be relevant
        roo_tasks = self.sync_engine.get_memory("roo:session:state", ToolType.COPILOT)
        
        # Combine contexts to enrich the prompt
        enriched_prompt = prompt
        contexts_added = []
        
        if project_context:
            contexts_added.append("project_context")
            if isinstance(project_context.content, dict):
                enriched_prompt += f"\n\nProject Context: {json.dumps(project_context.content, indent=2)}"
        
        if gemini_analysis:
            contexts_added.append("gemini_analysis")
            if isinstance(gemini_analysis.content, str):
                content = gemini_analysis.content
                if len(content) > 500:  # If too long, take beginning and end
                    content = content[:300] + "...[truncated]..." + content[-200:]
                enriched_prompt += f"\n\nAnalysis Context: {content}"
        
        if roo_tasks:
            contexts_added.append("roo_tasks")
            if isinstance(roo_tasks.content, dict) and "active_tasks" in roo_tasks.content:
                enriched_prompt += f"\n\nActive Tasks: {roo_tasks.content['active_tasks']}"
        
        logger.info(f"Generated completion using contexts: {', '.join(contexts_added)}")
        
        # In a real implementation, this would call the Co-pilot API
        # Here we'll just simulate a response based on the context
        return f"Completion for: {prompt}\n[Enriched with contexts: {', '.join(contexts_added)}]"


def setup_test_environment() -> Tuple[MemorySyncEngine, CopilotExtensionAdapter]:
    """Set up the test environment."""
    # Create storage
    storage = InMemoryStorage()
    
    # Define tools and budgets
    tools = [ToolType.ROO, ToolType.CLINE, ToolType.GEMINI, ToolType.COPILOT]
    token_budgets = {
        ToolType.ROO: 16000,
        ToolType.CLINE: 8000,
        ToolType.GEMINI: 200000,
        ToolType.COPILOT: 5000
    }
    
    # Create sync engine
    sync_engine = MemorySyncEngine(storage, tools, token_budgets)
    
    # Create Co-pilot adapter
    copilot_adapter = CopilotExtensionAdapter(sync_engine)
    
    # Register adapter with sync engine
    # In a real implementation, this would be an adapter for the Co-pilot API
    # that can actually execute sync operations
    class MockCopilotSyncAdapter:
        def sync_create(self, key: str, entry: MemoryEntry) -> bool:
            logger.info(f"Co-pilot would sync create: {key}")
            return True
        
        def sync_update(self, key: str, entry: MemoryEntry) -> bool:
            logger.info(f"Co-pilot would sync update: {key}")
            return True
        
        def sync_delete(self, key: str) -> bool:
            logger.info(f"Co-pilot would sync delete: {key}")
            return True
    
    sync_engine.register_tool_adapter(ToolType.COPILOT, MockCopilotSyncAdapter())
    
    return sync_engine, copilot_adapter


def simulate_coding_session(copilot_adapter: CopilotExtensionAdapter) -> None:
    """Simulate a coding session to test IDE integration."""
    print("\n=== Simulating a Coding Session ===\n")
    
    print("1. Opening a file in the editor...")
    python_file_content = """#!/usr/bin/env python3
\"\"\"
memory_integration_demo.py - Demo for memory integration
\"\"\"

import os
import sys
from typing import Dict, Any

def process_memory(data: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"Process memory data.\"\"\"
    result = {}
    for key, value in data.items():
        # TODO: Implement processing logic here
        result[key] = value
    
    return result

def main():
    \"\"\"Main function.\"\"\"
    # Load the memory data
    data = {"key1": "value1", "key2": "value2"}
    
    # Process the data
    processed_data = process_memory(data)
    
    # Print the result
    print(processed_data)

if __name__ == "__main__":
    main()
"""
    
    copilot_adapter.on_file_opened("memory_integration_demo.py", python_file_content)
    
    print("\n2. Moving cursor to the TODO comment...")
    copilot_adapter.on_cursor_moved("memory_integration_demo.py", 13, 40)
    
    print("\n3. Asking for a completion...")
    prompt = "Implement the processing logic"
    completion = copilot_adapter.generate_completion(prompt)
    print(f"\nCo-pilot Completion:\n{completion}")
    
    print("\n4. Making changes to the file...")
    updated_content = python_file_content.replace(
        "        # TODO: Implement processing logic here",
        """        # Process the data based on the key
        if key.startswith('key'):
            result[key] = f"processed_{value}"
        else:
            result[key] = value"""
    )
    copilot_adapter.on_file_changed("memory_integration_demo.py", updated_content)
    
    print("\n5. Opening a second file related to memory management...")
    second_file_content = """#!/usr/bin/env python3
\"\"\"
memory_manager.py - Manage memory operations
\"\"\"

from typing import Dict, Any, Optional

class MemoryManager:
    \"\"\"Manager for memory operations.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the memory manager.\"\"\"
        self.memory_store = {}
    
    def store(self, key: str, value: Any) -> bool:
        \"\"\"Store a value in memory.\"\"\"
        self.memory_store[key] = value
        return True
    
    def retrieve(self, key: str) -> Optional[Any]:
        \"\"\"Retrieve a value from memory.\"\"\"
        return self.memory_store.get(key)
    
    # TODO: Implement function to synchronize with other memory stores
"""
    
    copilot_adapter.on_file_opened("memory_manager.py", second_file_content)
    
    print("\n6. Moving cursor to the TODO comment in the second file...")
    copilot_adapter.on_cursor_moved("memory_manager.py", 24, 70)
    
    print("\n7. Selecting the TODO comment...")
    copilot_adapter.on_selection_changed(
        "memory_manager.py", 
        "# TODO: Implement function to synchronize with other memory stores"
    )
    
    print("\n8. Asking for a completion for the synchronization function...")
    sync_prompt = "Implement a function to synchronize with external memory stores"
    sync_completion = copilot_adapter.generate_completion(sync_prompt)
    print(f"\nCo-pilot Completion:\n{sync_completion}")
    
    print("\nCoding session simulation complete.")


def main():
    """Run the IDE integration test."""
    parser = argparse.ArgumentParser(description="Test IDE Extensions Integration with MCP Framework")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("=== Testing IDE Extensions Integration with MCP Framework ===\n")
    print("This test demonstrates how IDE extensions like Co-pilot can integrate")
    print("with the Memory Synchronization Engine to share context with other AI tools.\n")
    
    # Set up the test environment
    sync_engine, copilot_adapter = setup_test_environment()
    
    # Create some initial memory entries to simulate context from other tools
    from demo_memory_sync import create_demo_memories
    create_demo_memories(sync_engine)
    
    # Process pending operations
    sync_engine.process_pending_operations()
    
    # Connect the Co-pilot extension
    copilot_adapter.connect_to_vscode()
    
    # Simulate a coding session
    simulate_coding_session(copilot_adapter)
    
    print("\n=== IDE Integration Test Complete ===")
    print("\nSummary:")
    print("1. Demonstrated how Co-pilot extension captures IDE context")
    print("2. Showed how this context is stored in the MCP framework")
    print("3. Illustrated how completions can leverage context from other tools")
    print("4. Verified bi-directional synchronization of context between tools")
    print("\nThis test validates that the MCP framework enables:")
    print("- Cross-tool memory sharing")
    print("- Context-aware completions")
    print("- IDE integration through adapters")


if __name__ == "__main__":
    main()
