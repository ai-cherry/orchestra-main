#!/usr/bin/env python3
"""
Tests for the ToolManager class.
"""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from mcp_server.tools.tool_manager import ToolManager

class TestToolManager(unittest.TestCase):
    """Test cases for the ToolManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.memory_store = MagicMock()
        self.config = {
            "roo": {
                "enabled": True,
                "api_endpoint": "http://localhost:8081",
            },
            "cline": {
                "enabled": False,
                "api_endpoint": "http://localhost:8082",
            },
            "gemini": {
                "enabled": True,
                "api_key_env": "GEMINI_API_KEY",
            },
            "copilot": {
                "enabled": False,
            }
        }
        self.tool_manager = ToolManager(self.config, self.memory_store)
    
    def test_initialization(self):
        """Test initialization of the tool manager."""
        # Check that the tool manager was initialized correctly
        self.assertEqual(self.tool_manager.memory_store, self.memory_store)
        self.assertEqual(len(self.tool_manager.tools), 2)  # Only enabled tools
        self.assertIn("roo", self.tool_manager.tools)
        self.assertIn("gemini", self.tool_manager.tools)
        self.assertNotIn("cline", self.tool_manager.tools)
        self.assertNotIn("copilot", self.tool_manager.tools)
    
    def test_get_enabled_tools(self):
        """Test getting enabled tools."""
        enabled_tools = self.tool_manager.get_enabled_tools()
        self.assertEqual(set(enabled_tools), {"roo", "gemini"})
    
    @patch("subprocess.run")
    def test_execute_roo(self, mock_run):
        """Test executing a prompt with Roo."""
        # Mock subprocess.run to return a successful result
        mock_process = MagicMock()
        mock_process.stdout = "Roo response"
        mock_run.return_value = mock_process
        
        # Execute a prompt
        result = self.tool_manager.execute("roo", "code", "Write a function")
        
        # Check that subprocess.run was called with the correct arguments
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0][0], "roo-cli")
        self.assertEqual(args[0][1], "code")
        self.assertEqual(args[0][2], "Write a function")
        self.assertEqual(kwargs["capture_output"], True)
        self.assertEqual(kwargs["text"], True)
        self.assertEqual(kwargs["check"], True)
        
        # Check the result
        self.assertEqual(result, "Roo response")
    
    @patch("subprocess.run")
    def test_execute_roo_with_context(self, mock_run):
        """Test executing a prompt with Roo and context."""
        # Mock subprocess.run to return a successful result
        mock_process = MagicMock()
        mock_process.stdout = "Roo response with context"
        mock_run.return_value = mock_process
        
        # Execute a prompt with context
        context = "Previous conversation"
        result = self.tool_manager.execute("roo", "code", "Write a function", context)
        
        # Check that subprocess.run was called with the correct arguments
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0][0], "roo-cli")
        self.assertEqual(args[0][1], "code")
        self.assertEqual(args[0][2], "Write a function")
        
        # Check that the context file was created and used
        self.assertEqual(args[0][3], "--context-file")
        context_file_path = args[0][4]
        context_file = Path(context_file_path)
        self.assertTrue(context_file.name.startswith("roo_context"))
        
        # Check the result
        self.assertEqual(result, "Roo response with context")
    
    @patch("subprocess.run")
    def test_execute_roo_error(self, mock_run):
        """Test executing a prompt with Roo when an error occurs."""
        # Mock subprocess.run to raise an exception
        mock_run.side_effect = Exception("Command failed")
        
        # Execute a prompt
        result = self.tool_manager.execute("roo", "code", "Write a function")
        
        # Check that the result is None
        self.assertIsNone(result)
    
    def test_execute_disabled_tool(self):
        """Test executing a prompt with a disabled tool."""
        result = self.tool_manager.execute("cline", "code", "Write a function")
        self.assertIsNone(result)
    
    def test_execute_unknown_tool(self):
        """Test executing a prompt with an unknown tool."""
        result = self.tool_manager.execute("unknown", "code", "Write a function")
        self.assertIsNone(result)
    
    @patch("mcp_server.tools.tool_manager.logger")
    def test_execute_gemini_not_implemented(self, mock_logger):
        """Test executing a prompt with Gemini (not implemented)."""
        result = self.tool_manager.execute("gemini", "code", "Write a function")
        self.assertIsNone(result)
        mock_logger.error.assert_called_once_with("Gemini integration not yet implemented")
    
    @patch("mcp_server.tools.tool_manager.logger")
    def test_execute_copilot_not_implemented(self, mock_logger):
        """Test executing a prompt with Copilot (not implemented and disabled)."""
        result = self.tool_manager.execute("copilot", "code", "Write a function")
        self.assertIsNone(result)
        mock_logger.error.assert_called_once_with("Tool not enabled: copilot")
    
    @patch("cline_integration.ClineModeManager")
    def test_execute_cline_import_error(self, mock_cline_manager):
        """Test executing a prompt with Cline when the module is not found."""
        # Mock the import to raise an ImportError
        mock_cline_manager.side_effect = ImportError("Module not found")
        
        # Enable the cline tool for this test
        self.tool_manager.tools["cline"] = {
            "config": self.config["cline"],
            "status": "initialized",
        }
        
        # Execute a prompt
        result = self.tool_manager.execute("cline", "code", "Write a function")
        
        # Check that the result is None
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()