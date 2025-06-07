import os
#!/usr/bin/env python3
"""
Prompt Management MCP Server

Centralized management of AI tool prompts, templates, and optimization strategies.
Focuses on performance, stability, and optimization prompts for all AI coding tools.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
import aioredis
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptManager:
    """Centralized prompt management for AI coding tools."""
    
    def __init__(self):
        self.redis_client = None
        self.project_root = Path(__file__).parent.parent.parent
        self.prompts_dir = self.project_root / ".ai-tools" / "prompts"
        self.prompt_templates = {}
        
    async def initialize(self):
        """Initialize the prompt manager."""
        try:
            # Connect to Redis for caching
            redis_url = os.getenv("REDIS_URL", "redis://45.77.87.106:6379")
            self.redis_client = await aioredis.from_url(redis_url)
            logger.info("Connected to Redis for prompt caching")
            
            # Ensure prompts directory exists
            self.prompts_dir.mkdir(parents=True, exist_ok=True)
            
            # Load default prompt templates
            await self._load_default_prompts()
            
        except Exception as e:
            logger.error(f"Failed to initialize prompt manager: {e}")
            
    async def _load_default_prompts(self):
        """Load default prompt templates for AI coding tools."""
        
        # Performance optimization prompts
        performance_prompts = {
            "database_optimization": """
# Database Optimization Prompt

You are a database optimization expert. Focus on:

## Performance Priorities:
1. **Query Optimization**: Eliminate N+1 queries, use proper indexing
2. **Connection Pooling**: Efficient database connection management
3. **Caching Strategy**: Redis caching for frequently accessed data
4. **Batch Operations**: Group multiple operations when possible

## Analysis Guidelines:
- Identify slow queries (>100ms)
- Check for missing indexes
- Look for unnecessary SELECT * statements
- Verify proper use of LIMIT clauses
- Ensure connection pooling is configured

## Code Examples:
```python
# Good: Specific columns with index
SELECT id, name, email FROM users WHERE status = 'active' LIMIT 100

# Bad: All columns without index
SELECT * FROM users WHERE custom_field = 'value'
```

Focus on performance and stability over cost optimization.
""",
            
            "api_optimization": """
# API Optimization Prompt

You are an API performance expert. Focus on:

## Performance Priorities:
1. **Response Time**: Target <200ms for most endpoints
2. **Caching**: Implement Redis caching for expensive operations
3. **Batch Processing**: Group API calls when possible
4. **Error Handling**: Graceful degradation and circuit breakers

## Optimization Strategies:
- Use async/await for I/O operations
- Implement request/response caching
- Add proper timeout handling
- Use connection pooling
- Implement rate limiting

## Code Examples:
```python
# Good: Async with timeout and caching
@cache(ttl=300)
async def get_user_data(user_id: int) -> Dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"/users/{user_id}")
        return response.json()

# Bad: Synchronous without timeout
def get_user_data(user_id: int):
    response = requests.get(f"/users/{user_id}")
    return response.json()
```

Prioritize performance and reliability.
""",
            
            "memory_optimization": """
# Memory Optimization Prompt

You are a memory optimization expert. Focus on:

## Memory Priorities:
1. **Memory Leaks**: Prevent and detect memory leaks
2. **Data Structures**: Use efficient data structures
3. **Lazy Loading**: Load data only when needed
4. **Garbage Collection**: Optimize for Python GC

## Optimization Techniques:
- Use generators instead of lists for large datasets
- Implement proper cleanup in context managers
- Use weak references when appropriate
- Profile memory usage regularly

## Code Examples:
```python
# Good: Generator for large datasets
def process_large_dataset():
    for item in database.stream_results():
        yield process_item(item)

# Bad: Loading everything into memory
def process_large_dataset():
    items = database.get_all_results()  # Memory intensive
    return [process_item(item) for item in items]
```

Focus on stability and performance.
"""
        }
        
        # Debugging prompts
        debugging_prompts = {
            "systematic_debugging": """
# Systematic Debugging Prompt

You are a systematic debugging expert. Follow this methodology:

## Debugging Process:
1. **Reproduce**: Consistently reproduce the issue
2. **Isolate**: Narrow down to the smallest failing case
3. **Analyze**: Use logging, profiling, and monitoring
4. **Hypothesize**: Form testable hypotheses
5. **Test**: Verify each hypothesis systematically
6. **Fix**: Implement the minimal fix
7. **Verify**: Ensure the fix works and doesn't break anything

## Tools and Techniques:
- Add comprehensive logging
- Use debugger breakpoints strategically
- Profile performance bottlenecks
- Check error monitoring dashboards
- Review recent changes in Git

## Code Examples:
```python
# Good: Comprehensive error handling with context
try:
    result = risky_operation(data)
    logger.info(f"Operation successful: {result.id}")
except SpecificException as e:
    logger.error(f"Operation failed for data {data.id}: {e}", exc_info=True)
    # Graceful fallback
    result = fallback_operation(data)
except Exception as e:
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    raise
```

Focus on systematic approach and stability.
""",
            
            "performance_debugging": """
# Performance Debugging Prompt

You are a performance debugging expert. Focus on:

## Performance Analysis:
1. **Profiling**: Use cProfile, line_profiler, memory_profiler
2. **Monitoring**: Check APM tools and metrics
3. **Database**: Analyze query performance
4. **Network**: Check API response times
5. **Memory**: Monitor memory usage patterns

## Common Performance Issues:
- Slow database queries
- N+1 query problems
- Memory leaks
- Inefficient algorithms
- Blocking I/O operations

## Debugging Tools:
```python
# Profile function performance
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return result
```

Prioritize performance and optimization.
"""
        }
        
        # Architecture prompts
        architecture_prompts = {
            "system_design": """
# System Design Prompt

You are a system architecture expert. Focus on:

## Design Principles:
1. **Performance**: Design for speed and efficiency
2. **Stability**: Build resilient, fault-tolerant systems
3. **Scalability**: Plan for growth and load
4. **Maintainability**: Keep code clean and modular

## Architecture Patterns:
- Microservices with clear boundaries
- Event-driven architecture
- CQRS for read/write separation
- Circuit breaker pattern
- Bulkhead pattern for isolation

## Technology Choices:
- PostgreSQL for ACID transactions
- Redis for caching and sessions
- Weaviate for vector search
- Pinecone for AI embeddings
- FastAPI for high-performance APIs

## Code Examples:
```python
# Good: Clean architecture with dependency injection
class UserService:
    def __init__(self, user_repo: UserRepository, cache: CacheService):
        self.user_repo = user_repo
        self.cache = cache
    
    async def get_user(self, user_id: int) -> User:
        # Check cache first
        cached_user = await self.cache.get(f"user:{user_id}")
        if cached_user:
            return User.parse_obj(cached_user)
        
        # Fetch from database
        user = await self.user_repo.get_by_id(user_id)
        await self.cache.set(f"user:{user_id}", user.dict(), ttl=300)
        return user
```

Focus on performance, stability, and optimization.
""",
            
            "microservices_design": """
# Microservices Design Prompt

You are a microservices architecture expert. Focus on:

## Service Design:
1. **Single Responsibility**: Each service has one clear purpose
2. **Data Ownership**: Each service owns its data
3. **API Design**: RESTful APIs with clear contracts
4. **Communication**: Async messaging where possible

## Cherry AI Services:
- **Cherry Service**: Personal assistant and ranch management
- **Sophia Service**: Business intelligence and Pay Ready
- **Karen Service**: Healthcare operations and ParagonRX
- **Infrastructure Service**: Monitoring and deployment
- **Data Service**: Database and vector operations

## Communication Patterns:
```python
# Good: Async event-driven communication
class EventBus:
    async def publish(self, event: Event):
        await self.redis.publish(event.topic, event.to_json())
    
    async def subscribe(self, topic: str, handler: Callable):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(topic)
        
        async for message in pubsub.listen():
            if message['type'] == 'message':
                event = Event.from_json(message['data'])
                await handler(event)
```

Prioritize performance and loose coupling.
"""
        }
        
        # Save all prompt templates
        await self._save_prompts("performance", performance_prompts)
        await self._save_prompts("debugging", debugging_prompts)
        await self._save_prompts("architecture", architecture_prompts)
        
        # Create optimization prompts
        optimization_prompts = {
            "code_review": """
# Code Review Optimization Prompt

You are a code review expert focused on performance and stability:

## Review Checklist:
1. **Performance**: Check for inefficient algorithms, database queries
2. **Stability**: Verify error handling, edge cases
3. **Security**: Basic security practices (but not primary focus)
4. **Maintainability**: Code clarity and documentation

## Focus Areas:
- Database query optimization
- API response time improvements
- Memory usage efficiency
- Error handling completeness
- Test coverage adequacy

## Review Comments Format:
```
🚀 Performance: [specific improvement]
🛡️ Stability: [reliability concern]
🔧 Optimization: [efficiency suggestion]
📝 Maintainability: [code clarity issue]
```

Prioritize performance and stability improvements.
""",
            
            "continuous_optimization": """
# Continuous Optimization Prompt

You are a continuous optimization expert. Focus on:

## Optimization Cycle:
1. **Measure**: Collect performance metrics
2. **Analyze**: Identify bottlenecks and issues
3. **Optimize**: Implement targeted improvements
4. **Verify**: Confirm improvements work
5. **Monitor**: Track ongoing performance

## Key Metrics:
- API response times
- Database query performance
- Memory usage patterns
- Error rates and types
- User experience metrics

## Optimization Strategies:
```python
# Performance monitoring decorator
def monitor_performance(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise
    return wrapper
```

Focus on measurable performance improvements.
"""
        }
        
        await self._save_prompts("optimization", optimization_prompts)
        
    async def _save_prompts(self, category: str, prompts: Dict[str, str]):
        """Save prompts to the filesystem."""
        category_dir = self.prompts_dir / category
        category_dir.mkdir(exist_ok=True)
        
        for name, content in prompts.items():
            prompt_file = category_dir / f"{name}.md"
            async with aiofiles.open(prompt_file, 'w') as f:
                await f.write(content)
        
        logger.info(f"Saved {len(prompts)} prompts for category: {category}")

# Initialize the prompt manager
prompt_manager = PromptManager()

# Create MCP server
server = Server("prompt-management")

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available prompt management tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="get_prompt",
                description="Get a specific prompt template for AI tools",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["coding", "debugging", "architecture", "optimization"],
                            "description": "Prompt category"
                        },
                        "name": {"type": "string", "description": "Prompt name"},
                        "tool": {
                            "type": "string",
                            "enum": ["roo", "cursor", "codex", "jules", "factory-ai"],
                            "description": "Target AI tool (optional)"
                        }
                    },
                    "required": ["category", "name"]
                }
            ),
            Tool(
                name="list_prompts",
                description="List all available prompts by category",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["coding", "debugging", "architecture", "optimization", "all"],
                            "description": "Prompt category to list"
                        }
                    }
                }
            ),
            Tool(
                name="create_prompt",
                description="Create a new prompt template",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["coding", "debugging", "architecture", "optimization"],
                            "description": "Prompt category"
                        },
                        "name": {"type": "string", "description": "Prompt name"},
                        "content": {"type": "string", "description": "Prompt content"},
                        "tool_specific": {
                            "type": "string",
                            "enum": ["roo", "cursor", "codex", "jules", "factory-ai"],
                            "description": "Make prompt specific to a tool (optional)"
                        }
                    },
                    "required": ["category", "name", "content"]
                }
            ),
            Tool(
                name="optimize_prompt",
                description="Optimize an existing prompt for better performance",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Prompt category"},
                        "name": {"type": "string", "description": "Prompt name"},
                        "optimization_type": {
                            "type": "string",
                            "enum": ["performance", "clarity", "specificity", "tool_specific"],
                            "description": "Type of optimization"
                        }
                    },
                    "required": ["category", "name", "optimization_type"]
                }
            ),
            Tool(
                name="generate_cheat_sheet",
                description="Generate a prompt cheat sheet for AI tools",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tool": {
                            "type": "string",
                            "enum": ["roo", "cursor", "codex", "jules", "factory-ai", "all"],
                            "description": "AI tool for cheat sheet"
                        },
                        "focus": {
                            "type": "string",
                            "enum": ["performance", "debugging", "architecture", "all"],
                            "description": "Focus area for cheat sheet"
                        }
                    },
                    "required": ["tool"]
                }
            )
        ]
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls for prompt management."""
    try:
        if name == "get_prompt":
            return await get_prompt(arguments)
        elif name == "list_prompts":
            return await list_prompts(arguments)
        elif name == "create_prompt":
            return await create_prompt(arguments)
        elif name == "optimize_prompt":
            return await optimize_prompt(arguments)
        elif name == "generate_cheat_sheet":
            return await generate_cheat_sheet(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")]
            )
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

async def get_prompt(arguments: dict) -> CallToolResult:
    """Get a specific prompt template."""
    category = arguments.get("category")
    name = arguments.get("name")
    tool = arguments.get("tool")
    
    prompt_file = prompt_manager.prompts_dir / category / f"{name}.md"
    
    if not prompt_file.exists():
        return CallToolResult(
            content=[TextContent(type="text", text=f"Prompt not found: {category}/{name}")]
        )
    
    async with aiofiles.open(prompt_file, 'r') as f:
        content = await f.read()
    
    if tool:
        # Customize prompt for specific tool
        tool_customizations = {
            "roo": "\n\n## Roo Coder Specific:\n- Use mode transitions effectively\n- Leverage memory hooks\n- Follow performance rules",
            "cursor": "\n\n## Cursor IDE Specific:\n- Use workspace settings\n- Leverage extensions\n- Optimize for SSH development",
            "codex": "\n\n## OpenAI Codex Specific:\n- Use approval modes carefully\n- Leverage Git context\n- Focus on automation",
            "jules": "\n\n## Google Jules Specific:\n- Use Google AI capabilities\n- Integrate with Gemini models\n- Focus on code understanding",
            "factory-ai": "\n\n## Factory AI Specific:\n- Use workflow automation\n- Leverage droids effectively\n- Focus on CI/CD integration"
        }
        
        if tool in tool_customizations:
            content += tool_customizations[tool]
    
    return CallToolResult(
        content=[TextContent(type="text", text=content)]
    )

async def list_prompts(arguments: dict) -> CallToolResult:
    """List all available prompts."""
    category = arguments.get("category", "all")
    
    result = "Available Prompts:\n\n"
    
    categories = ["coding", "debugging", "architecture", "optimization"] if category == "all" else [category]
    
    for cat in categories:
        cat_dir = prompt_manager.prompts_dir / cat
        if cat_dir.exists():
            result += f"## {cat.title()} Prompts:\n"
            prompt_files = list(cat_dir.glob("*.md"))
            for prompt_file in prompt_files:
                result += f"- {prompt_file.stem}\n"
            result += "\n"
    
    return CallToolResult(
        content=[TextContent(type="text", text=result)]
    )

async def create_prompt(arguments: dict) -> CallToolResult:
    """Create a new prompt template."""
    category = arguments.get("category")
    name = arguments.get("name")
    content = arguments.get("content")
    tool_specific = arguments.get("tool_specific")
    
    # Ensure category directory exists
    category_dir = prompt_manager.prompts_dir / category
    category_dir.mkdir(exist_ok=True)
    
    # Add tool-specific header if specified
    if tool_specific:
        content = f"# {name.title()} - {tool_specific.title()} Specific\n\n{content}"
    else:
        content = f"# {name.title()}\n\n{content}"
    
    # Add performance and stability focus
    content += "\n\n## Focus Areas:\n- Performance optimization\n- Stability and reliability\n- Code quality and maintainability"
    
    prompt_file = category_dir / f"{name}.md"
    async with aiofiles.open(prompt_file, 'w') as f:
        await f.write(content)
    
    return CallToolResult(
        content=[TextContent(type="text", text=f"Created prompt: {category}/{name}")]
    )

async def optimize_prompt(arguments: dict) -> CallToolResult:
    """Optimize an existing prompt."""
    category = arguments.get("category")
    name = arguments.get("name")
    optimization_type = arguments.get("optimization_type")
    
    prompt_file = prompt_manager.prompts_dir / category / f"{name}.md"
    
    if not prompt_file.exists():
        return CallToolResult(
            content=[TextContent(type="text", text=f"Prompt not found: {category}/{name}")]
        )
    
    async with aiofiles.open(prompt_file, 'r') as f:
        content = await f.read()
    
    # Apply optimization based on type
    if optimization_type == "performance":
        content += "\n\n## Performance Optimization Focus:\n"
        content += "- Prioritize speed and efficiency\n"
        content += "- Minimize resource usage\n"
        content += "- Optimize algorithms and data structures\n"
        content += "- Use caching and memoization\n"
    
    elif optimization_type == "clarity":
        content += "\n\n## Clarity Improvements:\n"
        content += "- Use clear, specific language\n"
        content += "- Provide concrete examples\n"
        content += "- Structure information logically\n"
        content += "- Include step-by-step instructions\n"
    
    elif optimization_type == "specificity":
        content += "\n\n## Specificity Enhancements:\n"
        content += "- Target specific use cases\n"
        content += "- Include domain-specific context\n"
        content += "- Provide detailed requirements\n"
        content += "- Add measurable success criteria\n"
    
    # Save optimized prompt
    async with aiofiles.open(prompt_file, 'w') as f:
        await f.write(content)
    
    return CallToolResult(
        content=[TextContent(type="text", text=f"Optimized prompt: {category}/{name} for {optimization_type}")]
    )

async def generate_cheat_sheet(arguments: dict) -> CallToolResult:
    """Generate a prompt cheat sheet for AI tools."""
    tool = arguments.get("tool")
    focus = arguments.get("focus", "all")
    
    cheat_sheet = f"# {tool.title()} AI Tool Cheat Sheet\n\n"
    
    if tool == "roo" or tool == "all":
        cheat_sheet += """## Roo Coder Commands:
- `switch to architect mode` - System design and architecture
- `switch to developer mode` - Code implementation
- `switch to debugger mode` - Systematic debugging
- `optimize for performance` - Focus on speed and efficiency
- `ensure stability` - Add error handling and resilience
- `review code quality` - Check maintainability and best practices

### Performance Focus:
- "Optimize database queries for better performance"
- "Implement caching strategy for frequently accessed data"
- "Use async/await for I/O operations"
- "Profile and optimize memory usage"

### Stability Focus:
- "Add comprehensive error handling"
- "Implement circuit breaker pattern"
- "Add health checks and monitoring"
- "Ensure graceful degradation"

"""
    
    if tool == "cursor" or tool == "all":
        cheat_sheet += """## Cursor IDE Commands:
- `Ctrl+K` - AI chat and code generation
- `Ctrl+L` - Chat with codebase context
- `Ctrl+I` - Inline code editing
- `@workspace` - Include workspace context
- `@files` - Reference specific files

### Performance Prompts:
- "Optimize this function for better performance"
- "Add caching to reduce database calls"
- "Convert synchronous code to async"
- "Profile memory usage and optimize"

### Debugging Prompts:
- "Debug this error with systematic approach"
- "Add logging for better observability"
- "Implement error recovery mechanisms"
- "Add unit tests for edge cases"

"""
    
    if tool == "codex" or tool == "all":
        cheat_sheet += """## OpenAI Codex Commands:
- `codex "task description"` - Execute coding task
- `codex --approval-mode full-auto "task"` - Automated execution
- `codex "add error handling to all API endpoints"` - Specific improvements
- `codex "optimize database queries"` - Performance focus

### SSH Integration:
```bash
# Setup on remote server
npm install -g @openai/codex
export OPENAI_API_KEY = os.getenv('ORCHESTRA_MCP_API_KEY')
cd ~/orchestra-main
codex "optimize this codebase for performance"
```

### Performance Tasks:
- "Add database indexing for slow queries"
- "Implement Redis caching for API responses"
- "Optimize memory usage in data processing"
- "Add performance monitoring and metrics"

"""
    
    if tool == "factory-ai" or tool == "all":
        cheat_sheet += """## Factory AI Integration:
- Workflow automation for CI/CD
- Automated code review and optimization
- Performance monitoring and alerting
- Deployment automation with rollback

### Workflow Examples:
- Code review automation
- Performance regression detection
- Automated testing and deployment
- Infrastructure monitoring

"""
    
    cheat_sheet += """
## General Performance Principles:
1. **Database**: Use indexes, avoid N+1 queries, implement caching
2. **APIs**: Add timeouts, use async operations, implement rate limiting
3. **Memory**: Use generators, implement cleanup, profile usage
4. **Monitoring**: Add metrics, logging, and alerting

## Stability Principles:
1. **Error Handling**: Use specific exceptions, implement fallbacks
2. **Resilience**: Circuit breakers, retries, graceful degradation
3. **Testing**: Unit tests, integration tests, performance tests
4. **Monitoring**: Health checks, metrics collection, alerting

Focus on performance and stability over cost optimization.
"""
    
    return CallToolResult(
        content=[TextContent(type="text", text=cheat_sheet)]
    )

async def main():
    """Main entry point for the prompt management MCP server."""
    # Initialize the prompt manager
    await prompt_manager.initialize()
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="prompt-management",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

