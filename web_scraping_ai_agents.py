#!/usr/bin/env python3
"""
Web Scraping AI Agent Team for Orchestra AI
Comprehensive web search and scraping system with specialized agents.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

# AI and ML imports
import openai
import redis
from bs4 import BeautifulSoup

# Web scraping imports
from playwright.async_api import Page, async_playwright
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Types of web scraping agents."""

    SEARCH_SPECIALIST = "search_specialist"
    SCRAPER_SPECIALIST = "scraper_specialist"
    DATA_PROCESSOR = "data_processor"
    CONTENT_ANALYZER = "content_analyzer"
    MONITORING_AGENT = "monitoring_agent"
    QUALITY_ASSURANCE = "quality_assurance"

class ScrapingStrategy(Enum):
    """Web scraping strategies."""

    FAST_STATIC = "fast_static"  # requests + BeautifulSoup
    DYNAMIC_CONTENT = "dynamic_content"  # Playwright
    STEALTH_MODE = "stealth_mode"  # Zenrows/Apify
    BULK_EXTRACTION = "bulk_extraction"  # PhantomBuster

class TaskPriority(Enum):
    """Task priority levels."""

    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class ScrapingTask:
    """Represents a web scraping task."""

    task_id: str
    url: str
    task_type: str
    priority: TaskPriority
    strategy: ScrapingStrategy
    parameters: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    assigned_agent: Optional[str] = None
    status: str = "pending"
    retries: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ScrapingResult:
    """Represents the result of a scraping operation."""

    task_id: str
    url: str
    status: str
    data: Dict[str, Any]
    extracted_content: str
    structured_data: Dict[str, Any]
    metadata: Dict[str, Any]
    agent_id: str
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    quality_score: float = 0.0
    extracted_links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)

class WebScrapingAgent(ABC):
    """Abstract base class for web scraping agents."""

    def __init__(self, agent_id: str, agent_type: AgentType, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config
        self.is_busy = False
        self.completed_tasks = 0
        self.success_rate = 1.0
        self.last_activity = datetime.now()

        # Redis for task coordination
        self.redis_client = redis.Redis(
            host=config.get("redis_host", "localhost"),
            port=config.get("redis_port", 6379),
            db=config.get("redis_db", 0),
            decode_responses=True,
        )

        # AI model for content analysis
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    @abstractmethod
    async def process_task(self, task: ScrapingTask) -> ScrapingResult:
        """Process a scraping task."""

    async def update_status(self, status: str):
        """Update agent status in Redis."""
        await self.redis_client.hset(
            f"agent:{self.agent_id}",
            mapping={
                "status": status,
                "last_activity": datetime.now().isoformat(),
                "completed_tasks": self.completed_tasks,
                "success_rate": self.success_rate,
            },
        )

    def calculate_quality_score(self, content: str, structured_data: Dict) -> float:
        """Calculate quality score for extracted data."""
        score = 0.0

        # Content length score (0-0.3)
        if content:
            content_score = min(len(content) / 1000, 1.0) * 0.3
            score += content_score

        # Structured data score (0-0.4)
        if structured_data:
            data_score = min(len(structured_data) / 10, 1.0) * 0.4
            score += data_score

        # Content quality indicators (0-0.3)
        if content:
            # Check for meaningful content
            words = content.split()
            if len(words) > 50:
                score += 0.1
            if any(word.lower() in content.lower() for word in ["title", "description", "article"]):
                score += 0.1
            if not any(spam in content.lower() for spam in ["error", "404", "403", "forbidden"]):
                score += 0.1

        return min(score, 1.0)

class SearchSpecialistAgent(WebScrapingAgent):
    """Specialized agent for web search operations."""

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentType.SEARCH_SPECIALIST, config)
        self.search_engines = {
            "google": "https://www.google.com/search?q={}",
            "bing": "https://www.bing.com/search?q={}",
            "duckduckgo": "https://duckduckgo.com/?q={}",
        }

    async def process_task(self, task: ScrapingTask) -> ScrapingResult:
        """Process search task."""
        start_time = time.time()

        try:
            query = task.parameters.get("query", "")
            search_engine = task.parameters.get("engine", "google")
            max_results = task.parameters.get("max_results", 10)

            logger.info(f"Search agent {self.agent_id} processing query: {query}")

            # Use appropriate scraping strategy
            if task.strategy == ScrapingStrategy.STEALTH_MODE:
                results = await self._stealth_search(query, search_engine, max_results)
            elif task.strategy == ScrapingStrategy.DYNAMIC_CONTENT:
                results = await self._dynamic_search(query, search_engine, max_results)
            else:
                results = await self._fast_search(query, search_engine, max_results)

            # Structure the search results
            structured_data = {
                "query": query,
                "engine": search_engine,
                "results": results,
                "total_results": len(results),
            }

            content = f"Search results for '{query}' from {search_engine}\n"
            content += "\n".join([f"{i+1}. {r['title']} - {r['url']}" for i, r in enumerate(results)])

            quality_score = self.calculate_quality_score(content, structured_data)

            return ScrapingResult(
                task_id=task.task_id,
                url=task.url,
                status="success",
                data={"search_results": results},
                extracted_content=content,
                structured_data=structured_data,
                metadata={"query": query, "engine": search_engine},
                agent_id=self.agent_id,
                processing_time=time.time() - start_time,
                quality_score=quality_score,
                extracted_links=[r["url"] for r in results],
            )

        except Exception as e:
            logger.error(f"Search agent {self.agent_id} failed: {str(e)}")
            return ScrapingResult(
                task_id=task.task_id,
                url=task.url,
                status="failed",
                data={"error": str(e)},
                extracted_content="",
                structured_data={},
                metadata={},
                agent_id=self.agent_id,
                processing_time=time.time() - start_time,
            )

    async def _stealth_search(self, query: str, engine: str, max_results: int) -> List[Dict]:
        """Search using stealth mode (Zenrows)."""
        # Implementation would use Zenrows API
        logger.info("Using Zenrows for stealth search")
        return await self._fast_search(query, engine, max_results)  # Fallback for now

    async def _dynamic_search(self, query: str, engine: str, max_results: int) -> List[Dict]:
        """Search using dynamic content scraping."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                search_url = self.search_engines[engine].format(query)
                await page.goto(search_url, wait_until="networkidle")

                # Extract search results (engine-specific selectors)
                results = []
                if engine == "google":
                    results = await self._extract_google_results(page, max_results)
                elif engine == "bing":
                    results = await self._extract_bing_results(page, max_results)

                await browser.close()
                return results

            except Exception as e:
                await browser.close()
                raise e

    async def _fast_search(self, query: str, engine: str, max_results: int) -> List[Dict]:
        """Fast search using requests."""
        # Simplified implementation - would use proper search APIs in production
        return [
            {
                "title": f"Result {i+1} for {query}",
                "url": f"https://example.com/result-{i+1}",
                "description": f"Description for result {i+1}",
                "rank": i + 1,
            }
            for i in range(min(max_results, 5))
        ]

    async def _extract_google_results(self, page: Page, max_results: int) -> List[Dict]:
        """Extract Google search results."""
        results = []
        search_results = await page.query_selector_all("div.g")

        for i, result in enumerate(search_results[:max_results]):
            try:
                title_elem = await result.query_selector("h3")
                link_elem = await result.query_selector("a")
                desc_elem = await result.query_selector(".VwiC3b")

                title = await title_elem.inner_text() if title_elem else ""
                url = await link_elem.get_attribute("href") if link_elem else ""
                description = await desc_elem.inner_text() if desc_elem else ""

                if title and url:
                    results.append(
                        {
                            "title": title,
                            "url": url,
                            "description": description,
                            "rank": i + 1,
                        }
                    )
            except Exception as e:
                logger.warning(f"Error extracting Google result {i}: {e}")

        return results

    async def _extract_bing_results(self, page: Page, max_results: int) -> List[Dict]:
        """Extract Bing search results."""
        # Similar implementation for Bing
        return []

class ScraperSpecialistAgent(WebScrapingAgent):
    """Specialized agent for web scraping operations."""

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentType.SCRAPER_SPECIALIST, config)
        self.zenrows_api_key = config.get("zenrows_api_key")
        self.apify_api_key = config.get("apify_api_key")

    async def process_task(self, task: ScrapingTask) -> ScrapingResult:
        """Process scraping task."""
        start_time = time.time()

        try:
            logger.info(f"Scraper agent {self.agent_id} processing URL: {task.url}")

            # Choose scraping method based on strategy
            if task.strategy == ScrapingStrategy.STEALTH_MODE:
                result_data = await self._scrape_with_zenrows(task)
            elif task.strategy == ScrapingStrategy.BULK_EXTRACTION:
                result_data = await self._scrape_with_apify(task)
            elif task.strategy == ScrapingStrategy.DYNAMIC_CONTENT:
                result_data = await self._scrape_with_playwright(task)
            else:
                result_data = await self._scrape_fast_static(task)

            quality_score = self.calculate_quality_score(result_data["content"], result_data["structured_data"])

            return ScrapingResult(
                task_id=task.task_id,
                url=task.url,
                status="success",
                data=result_data,
                extracted_content=result_data["content"],
                structured_data=result_data["structured_data"],
                metadata=result_data.get("metadata", {}),
                agent_id=self.agent_id,
                processing_time=time.time() - start_time,
                quality_score=quality_score,
                extracted_links=result_data.get("links", []),
                images=result_data.get("images", []),
            )

        except Exception as e:
            logger.error(f"Scraper agent {self.agent_id} failed: {str(e)}")
            return ScrapingResult(
                task_id=task.task_id,
                url=task.url,
                status="failed",
                data={"error": str(e)},
                extracted_content="",
                structured_data={},
                metadata={},
                agent_id=self.agent_id,
                processing_time=time.time() - start_time,
            )

    async def _scrape_with_zenrows(self, task: ScrapingTask) -> Dict[str, Any]:
        """Scrape using Zenrows for anti-detection."""
        if not self.zenrows_api_key:
            raise ValueError("Zenrows API key not configured")

        async with aiohttp.ClientSession() as session:
            proxy_params = {
                "url": task.url,
                "js_render": "true" if task.parameters.get("js_render") else "false",
                "premium_proxy": "true",
                "proxy_country": task.parameters.get("proxy_country", "US"),
            }

            async with session.get(
                "https://api.zenrows.com/v1/",
                headers={"apikey": self.zenrows_api_key},
                params=proxy_params,
            ) as response:
                html_content = await response.text()

                return self._parse_html_content(html_content, task.url)

    async def _scrape_with_apify(self, task: ScrapingTask) -> Dict[str, Any]:
        """Scrape using Apify platform."""
        if not self.apify_api_key:
            raise ValueError("Apify API key not configured")

        # Use Apify Web Scraper actor
        actor_input = {
            "startUrls": [{"url": task.url}],
            "pseudoUrls": task.parameters.get("pseudo_urls", []),
            "pageFunction": task.parameters.get("page_function", "context => context"),
            "maxRequestsPerCrawl": task.parameters.get("max_requests", 1),
        }

        async with aiohttp.ClientSession() as session:
            # Start actor run
            async with session.post(
                "https://api.apify.com/v2/acts/apify~web-scraper/runs",
                headers={"Authorization": f"Bearer {self.apify_api_key}"},
                json=actor_input,
            ) as response:
                run_data = await response.json()
                run_id = run_data["data"]["id"]

            # Wait for completion and get results
            while True:
                await asyncio.sleep(2)
                async with session.get(
                    f"https://api.apify.com/v2/actor-runs/{run_id}",
                    headers={"Authorization": f"Bearer {self.apify_api_key}"},
                ) as response:
                    run_status = await response.json()
                    if run_status["data"]["status"] in ["SUCCEEDED", "FAILED"]:
                        break

            # Get dataset items
            async with session.get(
                f'https://api.apify.com/v2/datasets/{run_status["data"]["defaultDatasetId"]}/items',
                headers={"Authorization": f"Bearer {self.apify_api_key}"},
            ) as response:
                results = await response.json()

                if results:
                    return {
                        "content": str(results[0]),
                        "structured_data": results[0],
                        "metadata": {"apify_run_id": run_id},
                        "links": [],
                        "images": [],
                    }
                else:
                    return {
                        "content": "",
                        "structured_data": {},
                        "metadata": {},
                        "links": [],
                        "images": [],
                    }

    async def _scrape_with_playwright(self, task: ScrapingTask) -> Dict[str, Any]:
        """Scrape using Playwright for dynamic content."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Configure page based on task parameters
                if task.parameters.get("user_agent"):
                    await page.set_extra_http_headers({"User-Agent": task.parameters["user_agent"]})

                await page.goto(task.url, wait_until="networkidle")

                # Wait for specific elements if specified
                if task.parameters.get("wait_for_selector"):
                    await page.wait_for_selector(task.parameters["wait_for_selector"])

                # Execute custom JavaScript if provided
                if task.parameters.get("custom_js"):
                    await page.evaluate(task.parameters["custom_js"])

                html_content = await page.content()

                # Extract links and images
                links = await page.evaluate(
                    """
                    () => Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.href)
                        .filter(href => href.startsWith('http'))
                """
                )

                images = await page.evaluate(
                    """
                    () => Array.from(document.querySelectorAll('img[src]'))
                        .map(img => img.src)
                        .filter(src => src.startsWith('http'))
                """
                )

                await browser.close()

                parsed_data = self._parse_html_content(html_content, task.url)
                parsed_data["links"] = links
                parsed_data["images"] = images

                return parsed_data

            except Exception as e:
                await browser.close()
                raise e

    async def _scrape_fast_static(self, task: ScrapingTask) -> Dict[str, Any]:
        """Fast static content scraping using requests."""
        headers = {
            "User-Agent": task.parameters.get(
                "user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(task.url) as response:
                html_content = await response.text()
                return self._parse_html_content(html_content, task.url)

    def _parse_html_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """Parse HTML content and extract structured data."""
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract basic metadata
        title = soup.find("title")
        title_text = title.get_text().strip() if title else ""

        meta_description = soup.find("meta", attrs={"name": "description"})
        description = meta_description.get("content", "") if meta_description else ""

        # Extract main content
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text_content = soup.get_text()
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        content = " ".join(chunk for chunk in chunks if chunk)

        # Extract links
        links = [urljoin(url, a.get("href", "")) for a in soup.find_all("a", href=True)]
        links = [link for link in links if link.startswith("http")]

        # Extract images
        images = [urljoin(url, img.get("src", "")) for img in soup.find_all("img", src=True)]
        images = [img for img in images if img.startswith("http")]

        # Extract structured data (JSON-LD, microdata, etc.)
        structured_data = {}
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            try:
                structured_data.update(json.loads(script.string))
            except (json.JSONDecodeError, AttributeError):
                pass

        return {
            "content": content,
            "structured_data": {
                "title": title_text,
                "description": description,
                "url": url,
                "word_count": len(content.split()),
                "json_ld": structured_data,
            },
            "metadata": {
                "content_length": len(content),
                "links_count": len(links),
                "images_count": len(images),
            },
            "links": links[:50],  # Limit to first 50 links
            "images": images[:20],  # Limit to first 20 images
        }

class ContentAnalyzerAgent(WebScrapingAgent):
    """Specialized agent for content analysis and processing."""

    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, AgentType.CONTENT_ANALYZER, config)
        self.openai_client = openai.OpenAI(api_key=config.get("openai_api_key"))

    async def process_task(self, task: ScrapingTask) -> ScrapingResult:
        """Process content analysis task."""
        start_time = time.time()

        try:
            content = task.parameters.get("content", "")
            analysis_type = task.parameters.get("analysis_type", "summary")

            logger.info(f"Content analyzer {self.agent_id} processing {analysis_type}")

            if analysis_type == "summary":
                analysis_result = await self._summarize_content(content)
            elif analysis_type == "sentiment":
                analysis_result = await self._analyze_sentiment(content)
            elif analysis_type == "entities":
                analysis_result = await self._extract_entities(content)
            elif analysis_type == "keywords":
                analysis_result = await self._extract_keywords(content)
            else:
                analysis_result = await self._general_analysis(content)

            # Generate embeddings for semantic search
            embeddings = self.embedding_model.encode(content).tolist()

            structured_data = {
                "analysis_type": analysis_type,
                "result": analysis_result,
                "content_length": len(content),
                "embeddings": embeddings,
            }

            quality_score = self.calculate_quality_score(str(analysis_result), structured_data)

            return ScrapingResult(
                task_id=task.task_id,
                url=task.url,
                status="success",
                data=analysis_result,
                extracted_content=str(analysis_result),
                structured_data=structured_data,
                metadata={"analysis_type": analysis_type},
                agent_id=self.agent_id,
                processing_time=time.time() - start_time,
                quality_score=quality_score,
            )

        except Exception as e:
            logger.error(f"Content analyzer {self.agent_id} failed: {str(e)}")
            return ScrapingResult(
                task_id=task.task_id,
                url=task.url,
                status="failed",
                data={"error": str(e)},
                extracted_content="",
                structured_data={},
                metadata={},
                agent_id=self.agent_id,
                processing_time=time.time() - start_time,
            )

    async def _summarize_content(self, content: str) -> Dict[str, Any]:
        """Summarize content using AI."""
        response = await self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes web content.",
                },
                {
                    "role": "user",
                    "content": f"Summarize this content in 2-3 sentences:\n\n{content[:2000]}",
                },
            ],
            max_tokens=150,
        )

        return {
            "summary": response.choices[0].message.content,
            "original_length": len(content),
            "compression_ratio": len(content) / len(response.choices[0].message.content),
        }

    async def _analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment of content."""
        response = await self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Analyze the sentiment of the given text. Respond with JSON containing sentiment (positive/negative/neutral), confidence (0-1), and key phrases.",
                },
                {"role": "user", "content": content[:1000]},
            ],
            max_tokens=100,
        )

        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"sentiment": "neutral", "confidence": 0.5, "key_phrases": []}

    async def _extract_entities(self, content: str) -> Dict[str, Any]:
        """Extract named entities from content."""
        response = await self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Extract named entities (people, organizations, locations) from the text. Respond with JSON.",
                },
                {"role": "user", "content": content[:1000]},
            ],
            max_tokens=150,
        )

        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"people": [], "organizations": [], "locations": []}

    async def _extract_keywords(self, content: str) -> Dict[str, Any]:
        """Extract keywords from content."""
        words = content.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top 10 keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "keywords": [{"word": k[0], "frequency": k[1]} for k in keywords],
            "total_words": len(words),
            "unique_words": len(word_freq),
        }

    async def _general_analysis(self, content: str) -> Dict[str, Any]:
        """Perform general content analysis."""
        return {
            "character_count": len(content),
            "word_count": len(content.split()),
            "paragraph_count": len(content.split("\n\n")),
            "reading_time_minutes": len(content.split()) / 200,  # Average reading speed
        }

class WebScrapingOrchestrator:
    """Main orchestrator for the web scraping AI agent team."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents: Dict[str, WebScrapingAgent] = {}
        self.task_queue = asyncio.Queue()
        self.results_storage = []
        self.is_running = False

        # Redis for coordination
        self.redis_client = redis.Redis(
            host=config.get("redis_host", "localhost"),
            port=config.get("redis_port", 6379),
            db=config.get("redis_db", 0),
            decode_responses=True,
        )

        # Initialize agents
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize specialized agents."""
        # Search specialists
        for i in range(self.config.get("search_agents", 2)):
            agent_id = f"search_agent_{i+1}"
            self.agents[agent_id] = SearchSpecialistAgent(agent_id, self.config)

        # Scraper specialists
        for i in range(self.config.get("scraper_agents", 3)):
            agent_id = f"scraper_agent_{i+1}"
            self.agents[agent_id] = ScraperSpecialistAgent(agent_id, self.config)

        # Content analyzers
        for i in range(self.config.get("analyzer_agents", 2)):
            agent_id = f"analyzer_agent_{i+1}"
            self.agents[agent_id] = ContentAnalyzerAgent(agent_id, self.config)

        logger.info(f"Initialized {len(self.agents)} specialized agents")

    async def start(self):
        """Start the orchestrator and all agents."""
        self.is_running = True
        logger.info("Starting Web Scraping AI Agent Team")

        # Start agent workers
        tasks = []
        for agent in self.agents.values():
            tasks.append(asyncio.create_task(self._agent_worker(agent)))

        # Start task distributor
        tasks.append(asyncio.create_task(self._task_distributor()))

        await asyncio.gather(*tasks)

    async def stop(self):
        """Stop the orchestrator."""
        self.is_running = False
        logger.info("Stopping Web Scraping AI Agent Team")

    async def submit_task(self, task: ScrapingTask) -> str:
        """Submit a task to the agent team."""
        await self.task_queue.put(task)

        # Store task in Redis
        await self.redis_client.hset(
            f"task:{task.task_id}",
            mapping={
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "url": task.url,
                "task_type": task.task_type,
                "priority": task.priority.value,
            },
        )

        logger.info(f"Task {task.task_id} submitted to queue")
        return task.task_id

    async def get_result(self, task_id: str) -> Optional[ScrapingResult]:
        """Get result for a specific task."""
        for result in self.results_storage:
            if result.task_id == task_id:
                return result
        return None

    async def _task_distributor(self):
        """Distribute tasks to appropriate agents."""
        while self.is_running:
            try:
                # Get task from queue (with timeout)
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                # Find best agent for the task
                best_agent = self._select_best_agent(task)

                if best_agent:
                    # Assign task to agent
                    task.assigned_agent = best_agent.agent_id
                    await self.redis_client.lpush(f"agent_queue:{best_agent.agent_id}", task.task_id)
                    logger.info(f"Assigned task {task.task_id} to agent {best_agent.agent_id}")
                else:
                    # Put task back in queue
                    await self.task_queue.put(task)
                    await asyncio.sleep(1)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task distributor: {e}")

    def _select_best_agent(self, task: ScrapingTask) -> Optional[WebScrapingAgent]:
        """Select the best agent for a task based on type and availability."""
        suitable_agents = []

        # Filter agents by task type
        if task.task_type in ["search", "google_search", "bing_search"]:
            suitable_agents = [
                a for a in self.agents.values() if a.agent_type == AgentType.SEARCH_SPECIALIST and not a.is_busy
            ]
        elif task.task_type in ["scrape", "extract", "crawl"]:
            suitable_agents = [
                a for a in self.agents.values() if a.agent_type == AgentType.SCRAPER_SPECIALIST and not a.is_busy
            ]
        elif task.task_type in ["analyze", "summarize", "sentiment"]:
            suitable_agents = [
                a for a in self.agents.values() if a.agent_type == AgentType.CONTENT_ANALYZER and not a.is_busy
            ]

        if not suitable_agents:
            return None

        # Select agent with highest success rate
        return max(suitable_agents, key=lambda a: a.success_rate)

    async def _agent_worker(self, agent: WebScrapingAgent):
        """Worker function for individual agents."""
        while self.is_running:
            try:
                # Check for tasks in agent's queue
                task_id = await self.redis_client.brpop(f"agent_queue:{agent.agent_id}", timeout=1)

                if task_id:
                    task_id = task_id[1]  # brpop returns (key, value)

                    # Get task details
                    task_data = await self.redis_client.hgetall(f"task:{task_id}")

                    if task_data:
                        # Reconstruct task object
                        task = ScrapingTask(
                            task_id=task_id,
                            url=task_data["url"],
                            task_type=task_data["task_type"],
                            priority=TaskPriority(int(task_data["priority"])),
                            strategy=ScrapingStrategy(task_data.get("strategy", "fast_static")),
                            parameters=json.loads(task_data.get("parameters", "{}")),
                            created_at=datetime.fromisoformat(task_data["created_at"]),
                        )

                        # Process task
                        agent.is_busy = True
                        await agent.update_status("processing")

                        result = await agent.process_task(task)

                        # Store result
                        self.results_storage.append(result)

                        # Update agent stats
                        agent.completed_tasks += 1
                        if result.status == "success":
                            agent.success_rate = (
                                agent.success_rate * (agent.completed_tasks - 1) + 1
                            ) / agent.completed_tasks
                        else:
                            agent.success_rate = (
                                agent.success_rate * (agent.completed_tasks - 1)
                            ) / agent.completed_tasks

                        agent.is_busy = False
                        await agent.update_status("idle")

                        logger.info(f"Agent {agent.agent_id} completed task {task_id} with status {result.status}")

            except Exception as e:
                logger.error(f"Error in agent worker {agent.agent_id}: {e}")
                agent.is_busy = False
                await agent.update_status("error")

# Integration with Orchestra AI MCP Server
class WebScrapingMCPServer:
    """MCP server for web scraping agent team integration."""

    def __init__(self, orchestrator: WebScrapingOrchestrator):
        self.orchestrator = orchestrator

    async def handle_search_request(self, query: str, engine: str = "google", max_results: int = 10) -> str:
        """Handle search request from Orchestra AI."""
        task = ScrapingTask(
            task_id=f"search_{int(time.time())}",
            url="",
            task_type="search",
            priority=TaskPriority.HIGH,
            strategy=ScrapingStrategy.FAST_STATIC,
            parameters={"query": query, "engine": engine, "max_results": max_results},
        )

        task_id = await self.orchestrator.submit_task(task)

        # Wait for result (simplified - would use proper async waiting in production)
        for _ in range(30):  # Wait up to 30 seconds
            result = await self.orchestrator.get_result(task_id)
            if result:
                return f"Search completed: {len(result.extracted_links)} results found"
            await asyncio.sleep(1)

        return "Search request submitted - check back for results"

    async def handle_scrape_request(self, url: str, strategy: str = "fast_static") -> str:
        """Handle scraping request from Orchestra AI."""
        task = ScrapingTask(
            task_id=f"scrape_{int(time.time())}",
            url=url,
            task_type="scrape",
            priority=TaskPriority.HIGH,
            strategy=ScrapingStrategy(strategy),
            parameters={},
        )

        task_id = await self.orchestrator.submit_task(task)
        return f"Scraping task {task_id} submitted for {url}"

# Example usage and configuration
async def main():
    """Example usage of the web scraping agent team."""
    config = {
        "redis_host": "localhost",
        "redis_port": 6379,
        "redis_db": 0,
        "search_agents": 2,
        "scraper_agents": 3,
        "analyzer_agents": 2,
        "zenrows_api_key": "your_zenrows_api_key",
        "apify_api_key": "your_apify_api_key",
        "openai_api_key": "your_openai_api_key",
    }

    # Initialize orchestrator
    orchestrator = WebScrapingOrchestrator(config)

    # Start in background
    asyncio.create_task(orchestrator.start())

    # Example search task
    search_task = ScrapingTask(
        task_id="test_search_1",
        url="",
        task_type="search",
        priority=TaskPriority.HIGH,
        strategy=ScrapingStrategy.FAST_STATIC,
        parameters={
            "query": "AI web scraping tools",
            "engine": "google",
            "max_results": 10,
        },
    )

    await orchestrator.submit_task(search_task)

    # Example scraping task
    scrape_task = ScrapingTask(
        task_id="test_scrape_1",
        url="https://example.com",
        task_type="scrape",
        priority=TaskPriority.MEDIUM,
        strategy=ScrapingStrategy.DYNAMIC_CONTENT,
        parameters={},
    )

    await orchestrator.submit_task(scrape_task)

    # Wait a bit for processing
    await asyncio.sleep(10)

    # Check results
    search_result = await orchestrator.get_result("test_search_1")
    if search_result:
        print(f"Search result: {search_result.extracted_content[:200]}...")

    scrape_result = await orchestrator.get_result("test_scrape_1")
    if scrape_result:
        print(f"Scrape result quality: {scrape_result.quality_score}")

    await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())
