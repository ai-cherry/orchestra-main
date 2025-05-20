"""
Web Browser Tool for Orchestra

This module provides a web browsing tool that can be used by agents to search
and navigate the web. It is designed to be compatible with Phidata's tool system
while providing Orchestra-specific functionality.
"""

import logging
import requests
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
import urllib.parse

from packages.tools.src.base import OrchestraTool

logger = logging.getLogger(__name__)


class WebBrowserTool(OrchestraTool):
    """
    Tool for web browsing and content extraction.

    This tool allows agents to:
    1. Search the web with a query
    2. Navigate to specific URLs
    3. Extract content from web pages
    4. Follow links within a page

    It is designed to be compatible with Phidata's tool system.
    """

    # Phidata-compatible class attributes
    name: str = "web_browser"
    description: str = (
        "Browse the web, search for information, and extract content from web pages."
    )

    def __init__(
        self,
        user_agent: str = "Mozilla/5.0 Orchestra AI Web Browser Tool/1.0",
        timeout: int = 10,
        max_content_length: int = 10000,
        **kwargs,
    ):
        """
        Initialize the web browser tool.

        Args:
            user_agent: User agent string to use in requests
            timeout: Request timeout in seconds
            max_content_length: Maximum length of content to return
            **kwargs: Additional configuration parameters
        """
        super().__init__(**kwargs)

        self.user_agent = user_agent
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

        # Store the last visited URL for context
        self.last_url = None

        logger.info(f"WebBrowserTool initialized with timeout={timeout}s")

    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the web browser tool based on the provided command.

        Args:
            **kwargs: Arguments specific to the web browser operation.
                Required: action - One of "search", "navigate", "extract", "back"
                Depending on action:
                - search: query (search query string)
                - navigate: url (URL to navigate to)
                - extract: Optional selectors to extract specific content
                - back: No additional parameters

        Returns:
            Dictionary containing the tool's output including:
            - content: Extracted content from the web page
            - url: Current URL
            - title: Page title
            - links: List of links found on the page
        """
        action = kwargs.get("action")
        if not action:
            return {
                "error": "No action specified. Use 'search', 'navigate', 'extract', or 'back'."
            }

        try:
            if action == "search":
                return self._search(kwargs.get("query", ""))
            elif action == "navigate":
                return self._navigate(kwargs.get("url", ""))
            elif action == "extract":
                return self._extract(
                    selectors=kwargs.get("selectors"),
                    extract_links=kwargs.get("extract_links", True),
                )
            elif action == "back":
                return self._back()
            else:
                return {
                    "error": f"Unknown action: {action}. Use 'search', 'navigate', 'extract', or 'back'."
                }
        except Exception as e:
            logger.error(f"Error in WebBrowserTool: {e}", exc_info=True)
            return {"error": f"Error executing web browser action: {str(e)}"}

    def _search(self, query: str) -> Dict[str, Any]:
        """
        Perform a web search with the given query.

        Args:
            query: Search query string

        Returns:
            Dictionary with search results
        """
        if not query:
            return {"error": "No search query provided."}

        # Use DuckDuckGo as the search engine (no API key required)
        logger.info(f"Searching for: {query}")

        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        response = self.session.get(url, timeout=self.timeout)

        if not response.ok:
            return {
                "error": f"Search request failed with status code: {response.status_code}"
            }

        # Parse the search results
        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        # Extract search results
        for result in soup.select(".result"):
            title_elem = result.select_one(".result__title a")
            snippet_elem = result.select_one(".result__snippet")

            if title_elem:
                title = title_elem.text.strip()
                href = title_elem.get("href", "")

                # DuckDuckGo HTML results have URLs in a redirected format
                # Extract the actual URL from the href parameter
                parsed_url = urllib.parse.urlparse(href)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                actual_url = query_params.get("uddg", [href])[0]

                snippet = ""
                if snippet_elem:
                    snippet = snippet_elem.text.strip()

                results.append({"title": title, "url": actual_url, "snippet": snippet})

        # Store the search URL as the last URL
        self.last_url = url

        return {
            "content": f"Search results for '{query}'",
            "url": url,
            "title": f"Search: {query}",
            "results": results[:10],  # Limit to top 10 results
        }

    def _navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to the specified URL and extract content.

        Args:
            url: URL to navigate to

        Returns:
            Dictionary with page content information
        """
        if not url:
            return {"error": "No URL provided."}

        logger.info(f"Navigating to: {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)

            if not response.ok:
                return {
                    "error": f"Navigation request failed with status code: {response.status_code}"
                }

            # Store this URL as the last URL
            self.last_url = url

            # Parse the page content
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title = "Untitled Page"
            title_elem = soup.find("title")
            if title_elem:
                title = title_elem.text.strip()

            # Extract main content (simplified approach)
            content = ""

            # Try to find the main content area
            main_elements = soup.find_all(["main", "article", "div", "section"])
            for element in main_elements:
                if len(element.get_text(strip=True)) > len(content):
                    content = element.get_text(strip=True)

            # If we couldn't find a suitable main element, use the body
            if not content:
                body = soup.find("body")
                if body:
                    content = body.get_text(strip=True)

            # Truncate content if it's too long
            if len(content) > self.max_content_length:
                content = content[: self.max_content_length] + "... [content truncated]"

            # Extract links
            links = []
            for link in soup.find_all("a", href=True):
                href = link.get("href")

                # Handle relative URLs
                if href.startswith("/"):
                    parsed_url = urllib.parse.urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    href = urllib.parse.urljoin(base_url, href)

                text = link.get_text(strip=True)
                links.append({"text": text if text else "[no text]", "url": href})

            return {
                "content": content,
                "url": url,
                "title": title,
                "links": links[:20],  # Limit to 20 links to avoid excessive output
            }

        except requests.exceptions.Timeout:
            return {
                "error": f"Request to {url} timed out after {self.timeout} seconds."
            }
        except requests.exceptions.RequestException as e:
            return {"error": f"Error navigating to {url}: {str(e)}"}

    def _extract(
        self, selectors: Optional[List[str]] = None, extract_links: bool = True
    ) -> Dict[str, Any]:
        """
        Extract specific content from the current page using CSS selectors.

        Args:
            selectors: List of CSS selectors to extract content from
            extract_links: Whether to extract links from the selected elements

        Returns:
            Dictionary with extracted content
        """
        if not self.last_url:
            return {"error": "No page has been loaded. Use 'navigate' first."}

        try:
            response = self.session.get(self.last_url, timeout=self.timeout)

            if not response.ok:
                return {
                    "error": f"Extract request failed with status code: {response.status_code}"
                }

            # Parse the page content
            soup = BeautifulSoup(response.text, "html.parser")

            results = {}

            # If no selectors provided, use some common ones
            if not selectors:
                selectors = ["h1", "h2", "p", "main", "article"]

            # Extract content for each selector
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    results[selector] = [elem.get_text(strip=True) for elem in elements]

            # Extract links if requested
            if extract_links:
                links = []
                for link in soup.find_all("a", href=True):
                    href = link.get("href")

                    # Handle relative URLs
                    if href.startswith("/"):
                        parsed_url = urllib.parse.urlparse(self.last_url)
                        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                        href = urllib.parse.urljoin(base_url, href)

                    text = link.get_text(strip=True)
                    links.append({"text": text if text else "[no text]", "url": href})

                results["links"] = links[:20]  # Limit to 20 links

            return {"url": self.last_url, "extracted": results}

        except Exception as e:
            return {"error": f"Error extracting content: {str(e)}"}

    def _back(self) -> Dict[str, Any]:
        """
        Go back to the previous page.

        Returns:
            Dictionary with page content information or error
        """
        # In a real browser we'd have history, but for this simplified tool
        # we just return an error since we don't maintain history
        return {"error": "Browser history not maintained in this tool."}

    def to_phidata_tool(self) -> Any:
        """
        Convert this Orchestra tool to a Phidata-compatible tool.

        For WebBrowserTool, we override this method to provide better
        integration with Phidata's tool system, including more descriptive
        parameter schemas.

        Returns:
            A Phidata-compatible Tool instance
        """
        try:
            # Import Phidata tool classes
            from phidata.tools import Tool as PhidataTool

            # Create a wrapper function that calls this tool's run method
            def tool_function(**kwargs):
                return self.run(**kwargs)

            # Return a Phidata Tool that wraps our function
            phidata_tool = PhidataTool(
                name=self.name,
                description=self.description,
                function=tool_function,
                # Define parameter schema for better Phidata integration
                parameters={
                    "action": {
                        "type": "string",
                        "enum": ["search", "navigate", "extract", "back"],
                        "description": "Action to perform: search the web, navigate to a URL, extract content, or go back",
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for 'search' action",
                    },
                    "url": {
                        "type": "string",
                        "format": "uri",
                        "description": "URL to navigate to for 'navigate' action",
                    },
                    "selectors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "CSS selectors for 'extract' action",
                    },
                    "extract_links": {
                        "type": "boolean",
                        "description": "Whether to extract links for 'extract' action",
                    },
                },
            )

            return phidata_tool

        except ImportError:
            logger.warning("Phidata not installed, cannot convert to Phidata tool")
            return None
        except Exception as e:
            logger.error(f"Error converting to Phidata tool: {e}")
            return None


# Alternative implementation using Phidata's native decorator
# This shows how to create a Phidata-compatible tool using the decorator approach
# which would be preferred if directly implementing for Phidata

# Example of creating a tool with Phidata's decorator
try:
    from phidata.tools import tool

    @tool(
        name="orchestra_web_browser",
        description="Browse the web, search for information, and extract content from web pages.",
        parameters={
            "action": {
                "type": "string",
                "enum": ["search", "navigate", "extract", "back"],
                "description": "Action to perform: search the web, navigate to a URL, extract content, or go back",
            },
            "query": {
                "type": "string",
                "description": "Search query for 'search' action",
            },
            "url": {
                "type": "string",
                "format": "uri",
                "description": "URL to navigate to for 'navigate' action",
            },
            "selectors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "CSS selectors for 'extract' action",
            },
            "extract_links": {
                "type": "boolean",
                "description": "Whether to extract links for 'extract' action",
            },
        },
    )
    def phidata_web_browser(
        action: str,
        query: str = None,
        url: str = None,
        selectors: List[str] = None,
        extract_links: bool = True,
    ):
        """
        A web browser tool for Phidata agents.

        This function demonstrates how to create a Phidata-compatible tool
        using the @tool decorator provided by Phidata.
        """
        # Create an instance of our WebBrowserTool
        browser = WebBrowserTool()

        # Call the run method with the provided parameters
        return browser.run(
            action=action,
            query=query,
            url=url,
            selectors=selectors,
            extract_links=extract_links,
        )

except ImportError:
    # Phidata not installed, decorator not available
    pass
