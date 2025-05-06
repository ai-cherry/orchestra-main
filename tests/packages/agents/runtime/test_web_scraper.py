"""
Tests for the WebScraperRuntimeAgent.

This module contains tests for the web scraper agent's functionality,
ensuring it correctly fetches content from URLs and handles errors.
"""

import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import uuid
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from packages.agents.runtime.web_scraper import WebScraperRuntimeAgent
from packages.shared.src.memory.stubs import InMemoryMemoryManagerStub
from packages.shared.src.models.base_models import AgentData


class TestWebScraperRuntimeAgent(unittest.TestCase):
    """Test cases for the WebScraperRuntimeAgent."""

    def setUp(self):
        """Set up a fresh agent and memory manager for each test."""
        self.memory_manager = InMemoryMemoryManagerStub()
        self.memory_manager.initialize()
        self.config = {"name": "test_web_scraper"}
        self.agent = WebScraperRuntimeAgent(
            config=self.config,
            persona=None,
            memory_manager=self.memory_manager
        )
        self.agent.setup_tools(["requests_session"])

    def tearDown(self):
        """Clean up resources after each test."""
        if hasattr(self, 'agent') and self.agent:
            self.agent.shutdown()
        if hasattr(self, 'memory_manager') and self.memory_manager:
            self.memory_manager.close()

    @patch('requests.Session.get')
    def test_scrape_with_requests_success(self, mock_get):
        """Test successful web scraping with requests."""
        # Mock a successful response
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_get.return_value = mock_response
        
        # Test URL
        test_url = "https://example.com"
        test_context = {"url": test_url}
        
        # Run the agent
        result = asyncio.run(self.agent.run(test_context))
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["url"], test_url)
        self.assertEqual(result["scraped_content"], "<html><body>Test content</body></html>")
        self.assertEqual(result["content_type"], "text/html")
        self.assertEqual(result["status_code"], 200)
        
        # Verify that result was stored in memory
        self.assertEqual(len(self.memory_manager.agent_data), 1)
        stored_data = self.memory_manager.agent_data[0]
        self.assertEqual(stored_data.agent_id, "test_web_scraper")
        self.assertEqual(stored_data.data_type, "web_scrape_result")
        self.assertEqual(stored_data.content["status"], "success")
        self.assertEqual(stored_data.content["url"], test_url)
        self.assertEqual(stored_data.content["scraped_content"], "<html><body>Test content</body></html>")
        
    @patch('requests.Session.get')
    def test_scrape_with_requests_http_error(self, mock_get):
        """Test handling of HTTP errors during scraping."""
        # Mock an HTTP error response
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Test URL
        test_url = "https://example.com/not-found"
        test_context = {"url": test_url}
        
        # Run the agent
        result = asyncio.run(self.agent.run(test_context))
        
        # Verify the result
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["url"], test_url)
        self.assertIn("error", result)
        
        # Verify that error was stored in memory
        self.assertEqual(len(self.memory_manager.agent_data), 1)
        stored_data = self.memory_manager.agent_data[0]
        self.assertEqual(stored_data.agent_id, "test_web_scraper")
        self.assertEqual(stored_data.data_type, "web_scrape_result")
        self.assertEqual(stored_data.content["status"], "error")
        self.assertEqual(stored_data.content["url"], test_url)
        
    def test_invalid_url(self):
        """Test handling of invalid URLs."""
        # Invalid URL
        test_context = {"url": "invalid-url"}
        
        # Run the agent
        result = asyncio.run(self.agent.run(test_context))
        
        # Verify the result
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["url"], "invalid-url")
        self.assertIn("error", result)
        self.assertIn("Invalid URL", result["error"])
        
        # Verify that error was stored in memory
        self.assertEqual(len(self.memory_manager.agent_data), 1)
        
    def test_no_url(self):
        """Test handling of missing URL in context."""
        # No URL
        test_context = {}
        
        # Run the agent
        result = asyncio.run(self.agent.run(test_context))
        
        # Verify the result
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["url"], None)
        self.assertIn("error", result)
        self.assertIn("No URL provided", result["error"])
        
        # Verify that error was stored in memory
        self.assertEqual(len(self.memory_manager.agent_data), 1)


if __name__ == "__main__":
    unittest.main()