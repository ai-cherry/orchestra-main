#!/usr/bin/env python3
"""
Tests for the configuration system.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from mcp_server.config.models import (
    MCPConfig, ServerConfig, MemoryConfig, SecurityConfig, ToolConfig, ConfigOverride
)
from mcp_server.config.loader import (
    load_config, save_config, load_config_from_file, get_config_path_from_env
)
from mcp_server.exceptions import ConfigFileError, ConfigValidationError


class TestConfigModels(unittest.TestCase):
    """Test cases for configuration models."""
    
    def test_server_config(self):
        """Test ServerConfig model."""
        # Test default values
        config = ServerConfig()
        self.assertEqual(config.host, "0.0.0.0")
        self.assertEqual(config.port, 8080)
        self.assertEqual(config.debug, False)
        
        # Test custom values
        config = ServerConfig(host="127.0.0.1", port=9000, debug=True)
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 9000)
        self.assertEqual(config.debug, True)
        
        # Test validation
        with self.assertRaises(ValueError):
            ServerConfig(port=0)
        with self.assertRaises(ValueError):
            ServerConfig(port=65536)
    
    def test_memory_config(self):
        """Test MemoryConfig model."""
        # Test default values
        config = MemoryConfig()
        self.assertEqual(config.storage_path, "/workspaces/orchestra-main/.mcp_memory")
        self.assertEqual(config.ttl_seconds, 86400)
        self.assertEqual(config.max_items_per_key, 1000)
        self.assertEqual(config.enable_compression, True)
        
        # Test custom values
        config = MemoryConfig(
            storage_path="/tmp/memory",
            ttl_seconds=3600,
            max_items_per_key=100,
            enable_compression=False
        )
        self.assertEqual(config.storage_path, "/tmp/memory")
        self.assertEqual(config.ttl_seconds, 3600)
        self.assertEqual(config.max_items_per_key, 100)
        self.assertEqual(config.enable_compression, False)
        
        # Test validation
        with self.assertRaises(ValueError):
            MemoryConfig(ttl_seconds=0)
        with self.assertRaises(ValueError):
            MemoryConfig(max_items_per_key=0)
    
    def test_security_config(self):
        """Test SecurityConfig model."""
        # Test default values
        config = SecurityConfig()
        self.assertEqual(config.enable_auth, False)
        self.assertEqual(config.token_required, False)
        self.assertEqual(config.allowed_origins, ["*"])
        
        # Test custom values
        config = SecurityConfig(
            enable_auth=True,
            token_required=True,
            allowed_origins=["http://localhost:3000"]
        )
        self.assertEqual(config.enable_auth, True)
        self.assertEqual(config.token_required, True)
        self.assertEqual(config.allowed_origins, ["http://localhost:3000"])
    
    def test_tool_config(self):
        """Test ToolConfig model."""
        # Test default values
        config = ToolConfig()
        self.assertEqual(config.enabled, False)
        self.assertEqual(config.api_endpoint, None)
        self.assertEqual(config.api_key_env, None)
        self.assertEqual(config.memory_sync, False)
        
        # Test custom values
        config = ToolConfig(
            enabled=True,
            api_endpoint="http://localhost:8081",
            memory_sync=True
        )
        self.assertEqual(config.enabled, True)
        self.assertEqual(config.api_endpoint, "http://localhost:8081")
        self.assertEqual(config.api_key_env, None)
        self.assertEqual(config.memory_sync, True)
        
        # Test validation
        with self.assertRaises(ValueError):
            ToolConfig(enabled=True)
    
    def test_mcp_config(self):
        """Test MCPConfig model."""
        # Test default values
        config = MCPConfig()
        self.assertIsInstance(config.server, ServerConfig)
        self.assertIsInstance(config.memory, MemoryConfig)
        self.assertIsInstance(config.security, SecurityConfig)
        self.assertEqual(config.tools, {})
        
        # Test custom values
        config = MCPConfig(
            server=ServerConfig(host="127.0.0.1", port=9000),
            memory=MemoryConfig(storage_path="/tmp/memory"),
            security=SecurityConfig(enable_auth=True),
            tools={
                "roo": ToolConfig(enabled=True, api_endpoint="http://localhost:8081"),
                "cline": ToolConfig(enabled=False),
            }
        )
        self.assertEqual(config.server.host, "127.0.0.1")
        self.assertEqual(config.server.port, 9000)
        self.assertEqual(config.memory.storage_path, "/tmp/memory")
        self.assertEqual(config.security.enable_auth, True)
        self.assertEqual(len(config.tools), 2)
        self.assertEqual(config.tools["roo"].enabled, True)
        self.assertEqual(config.tools["roo"].api_endpoint, "http://localhost:8081")
        self.assertEqual(config.tools["cline"].enabled, False)
    
    def test_config_override(self):
        """Test ConfigOverride model."""
        # Create a base config
        config = MCPConfig(
            server=ServerConfig(host="0.0.0.0", port=8080),
            memory=MemoryConfig(storage_path="/tmp/memory"),
            security=SecurityConfig(enable_auth=False),
        )
        
        # Create an override
        override = ConfigOverride(
            server_host="127.0.0.1",
            server_port=9000,
            security_enable_auth=True,
        )
        
        # Apply the override
        updated_config = override.apply_to_config(config)
        
        # Check that the override was applied
        self.assertEqual(updated_config.server.host, "127.0.0.1")
        self.assertEqual(updated_config.server.port, 9000)
        self.assertEqual(updated_config.memory.storage_path, "/tmp/memory")  # Unchanged
        self.assertEqual(updated_config.security.enable_auth, True)


class TestConfigLoader(unittest.TestCase):
    """Test cases for configuration loader."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()
    
    def test_load_json_config(self):
        """Test loading configuration from a JSON file."""
        # Create a test configuration file
        config_path = self.config_dir / "config.json"
        test_config = {
            "server": {
                "host": "127.0.0.1",
                "port": 9000,
            },
            "memory": {
                "storage_path": "/tmp/memory",
            },
            "tools": {
                "roo": {
                    "enabled": True,
                    "api_endpoint": "http://localhost:8081",
                },
            },
        }
        
        with open(config_path, "w") as f:
            json.dump(test_config, f)
        
        # Load the configuration
        config = load_config_from_file(config_path)
        
        # Check that the configuration was loaded correctly
        self.assertEqual(config["server"]["host"], "127.0.0.1")
        self.assertEqual(config["server"]["port"], 9000)
        self.assertEqual(config["memory"]["storage_path"], "/tmp/memory")
        self.assertEqual(config["tools"]["roo"]["enabled"], True)
        self.assertEqual(config["tools"]["roo"]["api_endpoint"], "http://localhost:8081")
    
    def test_load_yaml_config(self):
        """Test loading configuration from a YAML file."""
        # Skip if PyYAML is not installed
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        
        # Create a test configuration file
        config_path = self.config_dir / "config.yaml"
        with open(config_path, "w") as f:
            f.write("""
server:
  host: 127.0.0.1
  port: 9000
memory:
  storage_path: /tmp/memory
tools:
  roo:
    enabled: true
    api_endpoint: http://localhost:8081
            """)
        
        # Load the configuration
        config = load_config_from_file(config_path)
        
        # Check that the configuration was loaded correctly
        self.assertEqual(config["server"]["host"], "127.0.0.1")
        self.assertEqual(config["server"]["port"], 9000)
        self.assertEqual(config["memory"]["storage_path"], "/tmp/memory")
        self.assertEqual(config["tools"]["roo"]["enabled"], True)
        self.assertEqual(config["tools"]["roo"]["api_endpoint"], "http://localhost:8081")
    
    def test_load_config_file_not_found(self):
        """Test loading configuration from a non-existent file."""
        config_path = self.config_dir / "nonexistent.json"
        
        # Check that the correct exception is raised
        with self.assertRaises(ConfigFileError):
            load_config_from_file(config_path)
    
    def test_load_config_invalid_format(self):
        """Test loading configuration from a file with an invalid format."""
        config_path = self.config_dir / "config.txt"
        with open(config_path, "w") as f:
            f.write("This is not a valid configuration file")
        
        # Check that the correct exception is raised
        with self.assertRaises(ConfigFileError):
            load_config_from_file(config_path)
    
    def test_save_config(self):
        """Test saving configuration to a file."""
        # Create a configuration
        config = MCPConfig(
            server=ServerConfig(host="127.0.0.1", port=9000),
            memory=MemoryConfig(storage_path="/tmp/memory"),
            tools={
                "roo": ToolConfig(enabled=True, api_endpoint="http://localhost:8081"),
            },
        )
        
        # Save the configuration to a JSON file
        config_path = self.config_dir / "config.json"
        save_config(config, config_path)
        
        # Check that the file was created
        self.assertTrue(config_path.exists())
        
        # Load the configuration back
        loaded_config = load_config_from_file(config_path)
        
        # Check that the configuration was saved correctly
        self.assertEqual(loaded_config["server"]["host"], "127.0.0.1")
        self.assertEqual(loaded_config["server"]["port"], 9000)
        self.assertEqual(loaded_config["memory"]["storage_path"], "/tmp/memory")
        self.assertEqual(loaded_config["tools"]["roo"]["enabled"], True)
        self.assertEqual(loaded_config["tools"]["roo"]["api_endpoint"], "http://localhost:8081")
    
    @patch("os.environ")
    def test_get_config_path_from_env(self, mock_environ):
        """Test getting configuration path from environment variable."""
        # Set up the mock
        mock_environ.get.return_value = "/path/to/config.json"
        
        # Get the configuration path
        config_path = get_config_path_from_env()
        
        # Check that the correct path was returned
        self.assertEqual(config_path, Path("/path/to/config.json"))
        
        # Check that the correct environment variable was used
        mock_environ.get.assert_called_once_with("MCP_CONFIG_PATH")
    
    @patch("os.environ")
    def test_config_override_from_env(self, mock_environ):
        """Test creating a configuration override from environment variables."""
        # Set up the mock
        mock_environ.__contains__.side_effect = lambda x: x in {
            "MCP_SERVER_HOST", "MCP_SERVER_PORT", "MCP_SECURITY_ENABLE_AUTH"
        }
        mock_environ.get.side_effect = lambda x, default=None: {
            "MCP_SERVER_HOST": "127.0.0.1",
            "MCP_SERVER_PORT": "9000",
            "MCP_SECURITY_ENABLE_AUTH": "true",
        }.get(x, default)
        
        # Create a configuration override
        from mcp_server.config.models import ConfigOverride
        override = ConfigOverride.from_env()
        
        # Check that the override was created correctly
        self.assertEqual(override.server_host, "127.0.0.1")
        self.assertEqual(override.server_port, 9000)
        self.assertEqual(override.security_enable_auth, True)
        self.assertIsNone(override.memory_storage_path)


if __name__ == "__main__":
    unittest.main()