#!/usr/bin/env python3
"""
Live Collaboration System Tests
Purpose: End-to-end testing of Cursor ↔ Database ↔ Manus collaboration
"""

import asyncio
import os
import tempfile
import shutil
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import pytest
import logging

# Setup logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import collaboration components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from cursor_plugin.file_watcher import CursorFileWatcher
from manus_interface.manus_client import ManusCollaborationClient
from sync_server.collaboration_server import CollaborationServer

class CollaborationTestSuite:
    """Comprehensive test suite for live collaboration system"""
    
    def __init__(self):
        self.test_workspace = None
        self.server = None
        self.cursor_watcher = None
        self.manus_client = None
        self.session_id = "test-session-001"
        
    async def setup(self):
        """Set up test environment"""
        logger.info("🔧 Setting up test environment...")
        
        # Create temporary workspace
        self.test_workspace = Path(tempfile.mkdtemp(prefix="collaboration_test_"))
        logger.info(f"📁 Test workspace: {self.test_workspace}")
        
        # Create sample files
        await self.create_sample_files()
        
        # Start collaboration server
        self.server = CollaborationServer()
        asyncio.create_task(self.server.start_server(port=8766))
        await asyncio.sleep(1)  # Give server time to start
        
        # Initialize clients
        self.cursor_watcher = CursorFileWatcher(
            str(self.test_workspace),
            "ws://localhost:8766",
            self.session_id
        )
        
        self.manus_client = ManusCollaborationClient("ws://localhost:8766")
        
        logger.info("✅ Test environment ready")

    async def teardown(self):
        """Clean up test environment"""
        logger.info("🧹 Cleaning up test environment...")
        
        if self.cursor_watcher:
            await self.cursor_watcher.disconnect_from_server()
        
        if self.manus_client:
            await self.manus_client.disconnect()
        
        if self.test_workspace and self.test_workspace.exists():
            shutil.rmtree(self.test_workspace)
        
        logger.info("✅ Cleanup complete")

    async def create_sample_files(self):
        """Create sample files for testing"""
        files = {
            'main.py': '''#!/usr/bin/env python3
"""
Sample Python file for collaboration testing
"""

def hello_world():
    print("Hello from collaboration test!")
    return "success"

if __name__ == "__main__":
    hello_world()
''',
            'utils.js': '''// JavaScript utility functions
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function calculateSum(a, b) {
    return a + b;
}

module.exports = { formatDate, calculateSum };
''',
            'config.json': '''{
    "app_name": "Collaboration Test",
    "version": "1.0.0",
    "debug": true,
    "features": {
        "real_time_sync": true,
        "file_watching": true
    }
}''',
            'README.md': '''# Collaboration Test Project

This is a test project for the live collaboration system.

## Features

- Real-time file synchronization
- Cursor IDE integration
- Manus AI visibility

## Testing

Run the collaboration test suite to verify functionality.
'''
        }
        
        for filename, content in files.items():
            file_path = self.test_workspace / filename
            file_path.write_text(content)
            
        logger.info(f"📝 Created {len(files)} sample files")

    async def test_cursor_connection(self):
        """Test Cursor file watcher connection"""
        logger.info("🧪 Testing Cursor connection...")
        
        success = await self.cursor_watcher.connect_to_server()
        assert success, "Failed to connect Cursor watcher to server"
        
        # Verify connection
        assert self.cursor_watcher.connected, "Cursor watcher should be connected"
        assert self.cursor_watcher.session_id == self.session_id, "Session ID mismatch"
        
        logger.info("✅ Cursor connection test passed")

    async def test_manus_connection(self):
        """Test Manus client connection"""
        logger.info("🧪 Testing Manus connection...")
        
        success = await self.manus_client.connect_to_session(self.session_id)
        assert success, "Failed to connect Manus client to server"
        
        # Verify connection
        assert self.manus_client.is_connected(), "Manus client should be connected"
        assert self.manus_client.get_session_id() == self.session_id, "Session ID mismatch"
        
        logger.info("✅ Manus connection test passed")

    async def test_file_sync(self):
        """Test file synchronization from Cursor to Manus"""
        logger.info("🧪 Testing file synchronization...")
        
        # Connect both clients
        await self.test_cursor_connection()
        await self.test_manus_connection()
        
        # Wait for initial sync
        await asyncio.sleep(2)
        
        # Get files from Manus perspective
        files = await self.manus_client.get_current_files()
        
        # Verify all sample files are synced
        file_names = {f['relative_path'] for f in files}
        expected_files = {'main.py', 'utils.js', 'config.json', 'README.md'}
        
        assert expected_files.issubset(file_names), f"Missing files: {expected_files - file_names}"
        
        # Verify file content
        main_py_content = await self.manus_client.get_file_content('main.py')
        assert main_py_content is not None, "Failed to get main.py content"
        assert "hello_world" in main_py_content, "File content verification failed"
        
        logger.info("✅ File sync test passed")

    async def test_real_time_changes(self):
        """Test real-time file change detection"""
        logger.info("🧪 Testing real-time file changes...")
        
        # Connect both clients
        await self.test_cursor_connection()
        await self.test_manus_connection()
        
        # Set up change detection
        changes_detected = []
        
        async def on_file_change(file_path: str, change_type: str, data: Dict[str, Any]):
            changes_detected.append({
                'file_path': file_path,
                'change_type': change_type,
                'timestamp': time.time()
            })
        
        await self.manus_client.watch_changes(on_file_change)
        
        # Modify a file
        test_file = self.test_workspace / 'main.py'
        original_content = test_file.read_text()
        new_content = original_content + '\n# Added comment for testing\n'
        
        test_file.write_text(new_content)
        
        # Wait for change detection
        await asyncio.sleep(2)
        
        # Verify change was detected
        assert len(changes_detected) > 0, "No file changes detected"
        
        change = changes_detected[0]
        assert change['file_path'] == 'main.py', "Wrong file detected"
        assert change['change_type'] in ['modify', 'scan'], f"Unexpected change type: {change['change_type']}"
        
        # Verify updated content is available to Manus
        updated_content = await self.manus_client.get_file_content('main.py')
        assert 'Added comment for testing' in updated_content, "Updated content not synced"
        
        logger.info("✅ Real-time changes test passed")

    async def test_file_creation_deletion(self):
        """Test file creation and deletion events"""
        logger.info("🧪 Testing file creation and deletion...")
        
        # Connect both clients
        await self.test_cursor_connection()
        await self.test_manus_connection()
        
        # Set up change detection
        changes_detected = []
        
        async def on_file_change(file_path: str, change_type: str, data: Dict[str, Any]):
            changes_detected.append({
                'file_path': file_path,
                'change_type': change_type,
                'timestamp': time.time()
            })
        
        await self.manus_client.watch_changes(on_file_change)
        
        # Create a new file
        new_file = self.test_workspace / 'new_test_file.py'
        new_file.write_text('# This is a new test file\nprint("New file created")\n')
        
        # Wait for creation detection
        await asyncio.sleep(1)
        
        # Delete the file
        new_file.unlink()
        
        # Wait for deletion detection
        await asyncio.sleep(1)
        
        # Verify both events were detected
        assert len(changes_detected) >= 2, f"Expected at least 2 changes, got {len(changes_detected)}"
        
        # Check for creation event
        creation_events = [c for c in changes_detected if c['change_type'] in ['create', 'scan']]
        assert len(creation_events) > 0, "File creation not detected"
        
        # Check for deletion event
        deletion_events = [c for c in changes_detected if c['change_type'] == 'delete']
        assert len(deletion_events) > 0, "File deletion not detected"
        
        logger.info("✅ File creation/deletion test passed")

    async def test_multiple_file_types(self):
        """Test synchronization of different file types"""
        logger.info("🧪 Testing multiple file types...")
        
        # Connect both clients
        await self.test_cursor_connection()
        await self.test_manus_connection()
        
        # Wait for initial sync
        await asyncio.sleep(2)
        
        # Get Python files
        python_files = await self.manus_client.get_python_files()
        assert len(python_files) >= 1, "No Python files found"
        
        # Get JavaScript files
        js_files = await self.manus_client.get_javascript_files()
        assert len(js_files) >= 1, "No JavaScript files found"
        
        # Search by extension
        md_files = await self.manus_client.search_files_by_extension('.md')
        assert len(md_files) >= 1, "No Markdown files found"
        
        json_files = await self.manus_client.search_files_by_extension('.json')
        assert len(json_files) >= 1, "No JSON files found"
        
        logger.info("✅ Multiple file types test passed")

    async def test_session_persistence(self):
        """Test session persistence and recovery"""
        logger.info("🧪 Testing session persistence...")
        
        # Connect Cursor and create initial session
        await self.test_cursor_connection()
        
        # Disconnect and reconnect Manus
        success = await self.manus_client.connect_to_session(self.session_id)
        assert success, "Failed to connect to existing session"
        
        # Verify files are still available
        files = await self.manus_client.get_current_files()
        assert len(files) > 0, "No files found in persistent session"
        
        # Get session info from database
        available_sessions = self.manus_client.get_available_sessions()
        test_sessions = [s for s in available_sessions if s['cursor_session_id'] == self.session_id]
        assert len(test_sessions) > 0, "Test session not found in database"
        
        logger.info("✅ Session persistence test passed")

    async def test_performance(self):
        """Test system performance with multiple files"""
        logger.info("🧪 Testing performance...")
        
        # Create multiple files for performance testing
        perf_files = {}
        for i in range(10):
            filename = f'perf_test_{i}.py'
            content = f'''# Performance test file {i}
def function_{i}():
    """Test function {i}"""
    data = [{{"id": {j}, "value": "test_{j}"}} for j in range(100)]
    return sum(item["id"] for item in data)

if __name__ == "__main__":
    result = function_{i}()
    print(f"Result {i}: {{result}}")
'''
            file_path = self.test_workspace / filename
            file_path.write_text(content)
            perf_files[filename] = content
        
        # Connect and measure sync time
        start_time = time.time()
        
        await self.test_cursor_connection()
        await self.test_manus_connection()
        
        # Wait for sync to complete
        await asyncio.sleep(3)
        
        sync_time = time.time() - start_time
        
        # Verify all files are synced
        files = await self.manus_client.get_current_files()
        synced_files = {f['relative_path'] for f in files}
        
        for filename in perf_files.keys():
            assert filename in synced_files, f"Performance test file {filename} not synced"
        
        logger.info(f"✅ Performance test passed - Sync time: {sync_time:.2f}s for {len(perf_files)} files")

    async def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🚀 Starting Live Collaboration Test Suite")
        logger.info("=" * 60)
        
        try:
            await self.setup()
            
            # Run all tests
            test_methods = [
                self.test_cursor_connection,
                self.test_manus_connection,
                self.test_file_sync,
                self.test_real_time_changes,
                self.test_file_creation_deletion,
                self.test_multiple_file_types,
                self.test_session_persistence,
                self.test_performance
            ]
            
            passed = 0
            failed = 0
            
            for test_method in test_methods:
                try:
                    await test_method()
                    passed += 1
                except AssertionError as e:
                    logger.error(f"❌ Test failed: {test_method.__name__}: {e}")
                    failed += 1
                except Exception as e:
                    logger.error(f"💥 Test error: {test_method.__name__}: {e}")
                    failed += 1
            
            # Print results
            logger.info("=" * 60)
            logger.info(f"🏁 Test Results: {passed} passed, {failed} failed")
            
            if failed == 0:
                logger.info("🎉 ALL TESTS PASSED! Live collaboration system is working correctly.")
                return True
            else:
                logger.error(f"😞 {failed} tests failed. Please check the errors above.")
                return False
                
        except Exception as e:
            logger.error(f"💥 Test suite error: {e}")
            return False
        finally:
            await self.teardown()

async def main():
    """Main test runner"""
    test_suite = CollaborationTestSuite()
    success = await test_suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(asyncio.run(main())) 