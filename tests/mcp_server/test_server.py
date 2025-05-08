#!/usr/bin/env python3
"""
Tests for the MCPServer class.
"""

import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from mcp_server.server import MCPServer, DEFAULT_CONFIG

class TestMCPServer(unittest.TestCase):
    """Test cases for the MCPServer class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for configuration
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
        
        # Create a test configuration file
        self.config_path = self.config_dir / "test_config.json"
        self.test_config = {
            "server": {
                "host": "127.0.0.1",
                "port": 9000,
                "debug": True,
            },
            "memory": {
                "storage_path": str(self.config_dir / "memory"),
                "ttl_seconds": 7200,
            },
            "tools": {
                "roo": {
                    "enabled": True,
                    "api_endpoint": "http://localhost:9001",
                },
                "cline": {
                    "enabled": False,
                },
            }
        }
        
        with open(self.config_path, "w") as f:
            json.dump(self.test_config, f)
        
        # Create memory directory
        (self.config_dir / "memory").mkdir(exist_ok=True)
        
        # Patch Flask and SocketIO to avoid actual server creation
        self.flask_patch = patch("mcp_server.server.Flask")
        self.mock_flask = self.flask_patch.start()
        self.mock_app = MagicMock()
        self.mock_flask.return_value = self.mock_app
        
        self.cors_patch = patch("mcp_server.server.CORS")
        self.mock_cors = self.cors_patch.start()
        
        self.socketio_patch = patch("mcp_server.server.SocketIO")
        self.mock_socketio = self.socketio_patch.start()
        self.mock_socketio_instance = MagicMock()
        self.mock_socketio.return_value = self.mock_socketio_instance
        
        # Patch the component classes
        self.memory_store_patch = patch("mcp_server.server.MemoryStore")
        self.mock_memory_store = self.memory_store_patch.start()
        self.mock_memory_store_instance = MagicMock()
        self.mock_memory_store.return_value = self.mock_memory_store_instance
        
        self.tool_manager_patch = patch("mcp_server.server.ToolManager")
        self.mock_tool_manager = self.tool_manager_patch.start()
        self.mock_tool_manager_instance = MagicMock()
        self.mock_tool_manager.return_value = self.mock_tool_manager_instance
        
        self.workflow_manager_patch = patch("mcp_server.server.WorkflowManager")
        self.mock_workflow_manager = self.workflow_manager_patch.start()
        self.mock_workflow_manager_instance = MagicMock()
        self.mock_workflow_manager.return_value = self.mock_workflow_manager_instance
    
    def tearDown(self):
        """Clean up test environment."""
        self.flask_patch.stop()
        self.cors_patch.stop()
        self.socketio_patch.stop()
        self.memory_store_patch.stop()
        self.tool_manager_patch.stop()
        self.workflow_manager_patch.stop()
        self.temp_dir.cleanup()
    
    def test_initialization_with_config_file(self):
        """Test initialization with a configuration file."""
        server = MCPServer(str(self.config_path))
        
        # Check that the configuration was loaded correctly
        self.assertEqual(server.config["server"]["host"], "127.0.0.1")
        self.assertEqual(server.config["server"]["port"], 9000)
        self.assertEqual(server.config["server"]["debug"], True)
        self.assertEqual(server.config["memory"]["storage_path"], str(self.config_dir / "memory"))
        self.assertEqual(server.config["memory"]["ttl_seconds"], 7200)
        
        # Check that the components were initialized correctly
        self.mock_memory_store.assert_called_once_with(server.config["memory"])
        self.mock_tool_manager.assert_called_once_with(server.config["tools"], self.mock_memory_store_instance)
        self.mock_workflow_manager.assert_called_once_with(self.mock_tool_manager_instance, self.mock_memory_store_instance)
        
        # Check that Flask and SocketIO were initialized correctly
        self.mock_flask.assert_called_once_with(__name__)
        self.mock_cors.assert_called_once_with(self.mock_app)
        self.mock_socketio.assert_called_once_with(self.mock_app, cors_allowed_origins="*")
    
    def test_initialization_with_default_config(self):
        """Test initialization with the default configuration."""
        server = MCPServer()
        
        # Check that the default configuration was used
        self.assertEqual(server.config, DEFAULT_CONFIG)
        
        # Check that the components were initialized correctly
        self.mock_memory_store.assert_called_once_with(DEFAULT_CONFIG["memory"])
        self.mock_tool_manager.assert_called_once_with(DEFAULT_CONFIG["tools"], self.mock_memory_store_instance)
        self.mock_workflow_manager.assert_called_once_with(self.mock_tool_manager_instance, self.mock_memory_store_instance)
    
    def test_initialization_with_dependency_injection(self):
        """Test initialization with dependency injection."""
        # Create mock instances
        memory_store = MagicMock()
        tool_manager = MagicMock()
        workflow_manager = MagicMock()
        
        # Initialize server with injected dependencies
        server = MCPServer(
            memory_store=memory_store,
            tool_manager=tool_manager,
            workflow_manager=workflow_manager
        )
        
        # Check that the injected dependencies were used
        self.assertEqual(server.memory_store, memory_store)
        self.assertEqual(server.tool_manager, tool_manager)
        self.assertEqual(server.workflow_manager, workflow_manager)
        
        # Check that the component classes were not called
        self.mock_memory_store.assert_not_called()
        self.mock_tool_manager.assert_not_called()
        self.mock_workflow_manager.assert_not_called()
    
    def test_route_configuration(self):
        """Test that routes are configured correctly."""
        server = MCPServer()
        
        # Check that routes were added
        route_calls = [call for call in self.mock_app.route.call_args_list]
        
        # Extract route paths and methods
        routes = [(args[0], kwargs.get("methods", ["GET"])) for args, kwargs in route_calls]
        
        # Check that all expected routes are present
        expected_routes = [
            ("/api/status", ["GET"]),
            ("/api/memory", ["GET"]),
            ("/api/memory", ["POST"]),
            ("/api/memory", ["DELETE"]),
            ("/api/memory/sync", ["POST"]),
            ("/api/execute", ["POST"]),
            ("/api/workflows", ["GET"]),
            ("/api/workflows/execute", ["POST"]),
            ("/api/workflows/cross-tool", ["POST"]),
        ]
        
        for route, methods in expected_routes:
            self.assertIn((route, methods), routes)
    
    def test_run_method(self):
        """Test the run method."""
        server = MCPServer(str(self.config_path))
        server.run()
        
        # Check that socketio.run was called with the correct arguments
        self.mock_socketio_instance.run.assert_called_once_with(
            self.mock_app,
            host="127.0.0.1",
            port=9000,
            debug=True
        )
    
    @patch("mcp_server.server.argparse.ArgumentParser")
    def test_main_function(self, mock_parser):
        """Test the main function."""
        # Mock the argument parser
        mock_parser_instance = MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_args = MagicMock()
        mock_args.config = str(self.config_path)
        mock_parser_instance.parse_args.return_value = mock_args
        
        # Mock the MCPServer class
        with patch("mcp_server.server.MCPServer") as mock_server_class:
            mock_server_instance = MagicMock()
            mock_server_class.return_value = mock_server_instance
            
            # Call the main function
            from mcp_server.server import main
            main()
            
            # Check that MCPServer was initialized with the correct arguments
            mock_server_class.assert_called_once_with(str(self.config_path))
            
            # Check that run was called
            mock_server_instance.run.assert_called_once()

if __name__ == "__main__":
    unittest.main()