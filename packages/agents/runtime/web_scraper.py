"""
Web Scraper Runtime Agent for AI Orchestration System.

This module provides a web scraper agent that can fetch content from URLs using
various scraping methods and APIs.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional
import urllib.parse

# Import the BaseAgent class
from packages.agents.base import BaseAgent
from packages.shared.src.models.base_models import AgentData

# For basic scraping
import requests

logger = logging.getLogger(__name__)


class WebScraperRuntimeAgent(BaseAgent):
    """
    Runtime Agent for scraping web content from specified URLs.

    This agent can use various tools for web scraping, including:
    - Basic requests library
    - (Placeholder) Brave Search API
    - (Placeholder) Apify
    - (Placeholder) Exa.ai
    - (Placeholder) ZenRows
    - (Placeholder) PhantomBuster

    The specific tool used depends on the configuration and context provided.
    """

    def __init__(
        self,
        config: Dict[str, Any] = None,
        persona: Dict[str, Any] = None,
        memory_manager=None,
    ):
        """
        Initialize the web scraper agent.

        Args:
            config: Agent-specific configuration.
            persona: Optional persona configuration for the agent.
            memory_manager: Optional memory manager for storing agent data.
        """
        super().__init__(config, persona)

        # Store the memory manager
        self.memory_manager = memory_manager

        # Initialize tool placeholders
        self.requests_session = None
        self.brave_client = None
        self.apify_client = None
        self.exa_client = None
        self.zenrows_client = None
        self.phantombuster_client = None

        logger.info("WebScraperRuntimeAgent initialized")

    def setup_tools(self, tools: List[str]) -> None:
        """
        Set up the specified scraping tools.

        Args:
            tools: List of tool names to set up.
        """
        logger.info(f"WebScraperAgent: Setup requested for tools: {tools}")

        if "requests_session" in tools:
            logger.info("Setting up requests session for basic scraping")
            self.requests_session = requests.Session()
            # Configure with reasonable defaults
            self.requests_session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            )

        if "brave_search" in tools:
            logger.info("Brave Search API setup requested, but not implemented yet")
            # TODO: Add logic to initialize Brave Search API client
            # self.brave_client = BraveSearchClient(api_key=self.config.get("brave_api_key"))

        if "apify" in tools:
            logger.info("Apify setup requested, but not implemented yet")
            # TODO: Add logic to initialize Apify client
            # from apify_client import ApifyClient
            # self.apify_client = ApifyClient(token=self.config.get("apify_api_key"))

        if "exa" in tools:
            logger.info("Exa.ai setup requested, but not implemented yet")
            # TODO: Add logic to initialize Exa client
            # self.exa_client = ExaClient(api_key=self.config.get("exa_api_key"))

        if "zenrows" in tools:
            logger.info("ZenRows setup requested, but not implemented yet")
            # TODO: Add logic to initialize ZenRows client
            # self.zenrows_client = ZenRowsClient(api_key=self.config.get("zenrows_api_key"))

        if "phantombuster" in tools:
            logger.info("PhantomBuster setup requested, but not implemented yet")
            # TODO: Add logic to initialize PhantomBuster client
            # self.phantombuster_client = PhantomBusterClient(api_key=self.config.get("phantombuster_api_key"))

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrape content from the specified URL and store the result in memory.

        Args:
            context: A dictionary containing:
                - url: The target URL to scrape
                - method: Optional scraping method to use ("requests", "brave", "apify", etc.)
                - params: Optional method-specific parameters

        Returns:
            Dictionary containing:
                - scraped_content: The scraped content (if successful)
                - url: The original URL
                - status: "success" or "error"
                - error: Error message (if status is "error")
        """
        # Extract URL from context
        url = context.get("url")
        if not url:
            error_msg = "No URL provided in context"
            logger.error(error_msg)
            result_dict = {"status": "error", "error": error_msg, "url": None}
            # Even though this is an error, we store it in memory
            await self._store_result_in_memory(result_dict, context)
            return result_dict

        # Validate URL
        try:
            parsed_url = urllib.parse.urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError("Invalid URL format")
        except Exception as e:
            error_msg = f"Invalid URL: {str(e)}"
            logger.error(error_msg)
            result_dict = {"status": "error", "error": error_msg, "url": url}
            # Store error result in memory
            await self._store_result_in_memory(result_dict, context)
            return result_dict

        # Log the scraping attempt
        logger.info(f"Attempting to scrape: {url}")

        # Determine which method to use
        method = context.get("method", "requests")

        # Execute the appropriate scraping method
        if method == "requests" or not method:
            result_dict = await self._scrape_with_requests(url, context)
        elif method == "brave":
            result_dict = {
                "status": "error",
                "error": "Brave Search API scraping not implemented yet",
                "url": url,
            }
        elif method == "apify":
            result_dict = {
                "status": "error",
                "error": "Apify scraping not implemented yet",
                "url": url,
            }
        elif method == "exa":
            result_dict = {
                "status": "error",
                "error": "Exa.ai scraping not implemented yet",
                "url": url,
            }
        elif method == "zenrows":
            result_dict = {
                "status": "error",
                "error": "ZenRows scraping not implemented yet",
                "url": url,
            }
        elif method == "phantombuster":
            result_dict = {
                "status": "error",
                "error": "PhantomBuster scraping not implemented yet",
                "url": url,
            }
        else:
            result_dict = {
                "status": "error",
                "error": f"Unknown scraping method: {method}",
                "url": url,
            }

        # Store the result in memory
        await self._store_result_in_memory(result_dict, context)

        # Return the result
        return result_dict

    async def _store_result_in_memory(self, result_dict: Dict[str, Any], context: Dict[str, Any]) -> None:
        """
        Store the scraping result in memory using the memory manager.

        Args:
            result_dict: The result dictionary to store
            context: The original context dictionary
        """
        if not self.memory_manager:
            logger.warning("No memory manager available, scrape result not stored")
            return

        try:
            # Create an AgentData instance with the result
            agent_data = AgentData(
                id=str(uuid.uuid4()),
                agent_id=self.id,
                data_type="web_scrape_result",
                content=result_dict,
                metadata={"context": context},
            )

            # Check if the memory manager's add_raw_agent_data method is a coroutine function
            if asyncio.iscoroutinefunction(self.memory_manager.add_raw_agent_data):
                data_id = await self.memory_manager.add_raw_agent_data(agent_data)
            else:
                # Run the synchronous method in a thread to avoid blocking
                data_id = await asyncio.to_thread(self.memory_manager.add_raw_agent_data, agent_data)

            logger.info(f"Stored web scraping result in memory with ID: {data_id}")

        except Exception as e:
            logger.error(f"Failed to store scraping result in memory: {str(e)}")

    async def _scrape_with_requests(self, url: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrape a URL using the requests library.

        Args:
            url: The URL to scrape
            context: Additional context parameters

        Returns:
            Dictionary with scraping results
        """
        # Initialize requests session if not already done
        if not self.requests_session:
            logger.info("Initializing requests session for scraping")
            self.setup_tools(["requests_session"])

        try:
            # Use asyncio to run the requests call non-blocking
            response = await asyncio.to_thread(
                self.requests_session.get,
                url,
                timeout=context.get("timeout", 30),
                allow_redirects=context.get("allow_redirects", True),
            )

            # Check if request was successful
            response.raise_for_status()

            # Return the scraped content
            return {
                "status": "success",
                "url": url,
                "scraped_content": response.text,
                "content_type": response.headers.get("Content-Type"),
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {str(e)}"
            logger.error(f"Error scraping {url}: {error_msg}")
            return {
                "status": "error",
                "url": url,
                "error": error_msg,
                "status_code": getattr(e.response, "status_code", None),
            }

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"Error scraping {url}: {error_msg}")
            return {"status": "error", "url": url, "error": error_msg}

        except requests.exceptions.Timeout as e:
            error_msg = f"Request timed out: {str(e)}"
            logger.error(f"Error scraping {url}: {error_msg}")
            return {"status": "error", "url": url, "error": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Error scraping {url}: {error_msg}")
            return {"status": "error", "url": url, "error": error_msg}

    def process_feedback(self, feedback: Dict[str, Any]) -> None:
        """
        Process feedback about the agent's performance.

        Args:
            feedback: Feedback data for the agent to process.
        """
        logger.info(f"WebScraperAgent received feedback: {feedback}")
        # Additional feedback processing logic could be added here in the future

    def shutdown(self) -> None:
        """
        Clean up resources when shutting down the agent.
        """
        logger.info("Shutting down WebScraperRuntimeAgent")

        # Close the requests session if it exists
        if self.requests_session:
            try:
                self.requests_session.close()
                logger.info("Closed requests session")
            except Exception as e:
                logger.warning(f"Error closing requests session: {e}")

        # TODO: Close other clients when implemented
