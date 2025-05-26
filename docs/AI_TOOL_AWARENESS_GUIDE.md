# AI Tool Awareness & Smart API Access Guide

## 🎯 Overview

This guide implements intelligent tool awareness for AI coding assistants in Orchestra AI, enabling them to:
- Discover available tools dynamically
- Select the right tool based on task complexity
- Chain tools together for complex workflows
- Learn from tool execution feedback

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER TASK/REQUEST                     │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  AI ASSISTANT (Cursor/Claude)            │
│                    with MCP Integration                  │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    TOOLS MCP SERVER                      │
│              (Tool Discovery & Execution)                │
└────────────────────┬───────────────────────────────────┘
                     │
        ┌────────────┴────────────┬─────────────────┐
        ▼                         ▼                 ▼
┌───────────────┐       ┌───────────────┐   ┌───────────────┐
│ Tool Registry │       │ Tool Executor │   │ Tool Router   │
│ (Rich Metadata)│      │ (Error Handle)│   │ (Planning)    │
└───────────────┘       └───────────────┘   └───────────────┘
```

## 📚 Implementation Components

### 1. Tool Registry (`core/orchestrator/src/tools/registry.py`)

The registry maintains rich metadata for each tool:

```python
class ToolDefinition:
    name: str                    # Unique identifier
    description: str             # What it does
    category: str               # database, cache, search, system, ai
    parameters: List[...]       # Input parameters with types
    output_type: str           # What it returns
    when_to_use: str          # Guidance for AI
    constraints: Optional[str] # Limitations
    examples: Optional[List]   # Usage examples
    cost_indicator: str       # low, medium, high
    related_tools: List[str]  # Similar/complementary tools
```

### 2. Tool Executor (`core/orchestrator/src/tools/executor.py`)

Handles tool execution with:
- Parameter validation
- Error handling
- Execution timing
- Result tracking
- Statistics collection

### 3. MCP Tools Server (`mcp_server/servers/tools_server.py`)

Exposes tools to AI assistants via MCP protocol:
- `search_tools` - Find tools by query
- `get_tool_details` - Get full tool documentation
- `list_tool_categories` - Browse available categories
- `execute_*` - Execute any registered tool

## 🚀 Usage Examples

### For AI Assistants

When an AI assistant needs to accomplish a task, it can:

1. **Search for relevant tools:**
```
User: "I need to cache some API responses"
AI: [Calls search_tools("cache")]
Result: Found cache_get, cache_set, cache_delete tools
```

2. **Get detailed information:**
```
AI: [Calls get_tool_details("cache_set")]
Result: Full documentation with parameters, examples, constraints
```

3. **Execute the tool:**
```
AI: [Calls execute_cache_set({
  "key": "api:weather:NYC",
  "value": "{\"temp\": 72, \"conditions\": \"sunny\"}",
  "ttl": 3600
})]
Result: ✅ Cached successfully
```

### Tool Selection Based on Complexity

The AI can intelligently choose tools based on task requirements:

#### Simple Task
```
User: "Check if we have weather data cached for NYC"
AI Analysis: Simple cache lookup needed
Tool Selected: cache_get("api:weather:NYC")
```

#### Medium Complexity
```
User: "Find all error logs from the last hour"
AI Analysis: Need to query database with time filter
Tool Selected: mongodb_query("logs", {
  "level": "error",
  "timestamp": {"$gte": <1 hour ago>}
})
```

#### Complex Task
```
User: "Analyze user behavior patterns and cache the results"
AI Analysis: Multiple steps needed
Tool Sequence:
1. mongodb_query - Get user data
2. llm_query - Analyze patterns
3. cache_set - Store results
```

## 🔧 Adding New Tools

### 1. Define the Tool

Add to `registry.py`:

```python
self.register_tool(ToolDefinition(
    name="email_send",
    description="Send email notifications",
    category="notification",
    parameters=[
        ToolParameter(name="to", type="string", description="Recipient email"),
        ToolParameter(name="subject", type="string", description="Email subject"),
        ToolParameter(name="body", type="string", description="Email body"),
        ToolParameter(name="html", type="boolean", description="HTML format",
                     required=False, default=False)
    ],
    output_type="dict",
    when_to_use="For sending notifications, alerts, or reports via email",
    constraints="Rate limited to 100 emails/hour; requires SMTP config",
    examples=[
        'email_send("user@example.com", "Alert", "System is down")',
        'email_send("admin@co.com", "Report", "<h1>Daily Stats</h1>", html=True)'
    ],
    cost_indicator="low",
    related_tools=["sms_send", "slack_notify"]
))
```

### 2. Implement the Tool

Create implementation in `implementations/notification_tools.py`:

```python
import smtplib
from email.mime.text import MIMEText

async def email_send(to: str, subject: str, body: str, html: bool = False) -> dict:
    """Send email notification."""
    msg = MIMEText(body, 'html' if html else 'plain')
    msg['Subject'] = subject
    msg['To'] = to

    # Send email logic here
    return {"sent": True, "message_id": "12345"}
```

### 3. Register Implementation

In `tools_server.py`:

```python
from core.orchestrator.src.tools.implementations import notification_tools

self.executor.register_implementation("email_send", notification_tools.email_send)
```

## 📋 Best Practices

### 1. Tool Naming
- Use verb_noun format: `cache_get`, `mongodb_query`
- Be specific: `user_create` not just `create`
- Group related tools: `cache_*`, `mongodb_*`

### 2. Rich Descriptions
- Include "when to use" guidance
- Provide real examples
- Document constraints clearly
- Indicate cost/performance

### 3. Parameter Design
- Use consistent parameter names
- Provide sensible defaults
- Validate inputs properly
- Return structured data

### 4. Error Handling
- Return clear error messages
- Include troubleshooting hints
- Log failures for debugging
- Graceful degradation

## 🎯 Integration with AI Context Files

Update AI context files to reference tool awareness:

### In `ai_context_coder.py`:
```python
TOOL DISCOVERY:
Before implementing functionality, check available tools:
1. Search for existing tools: search_tools("your query")
2. Get details: get_tool_details("tool_name")
3. Use tools instead of reimplementing

Example:
Instead of writing cache logic, use:
- cache_get, cache_set, cache_delete
```

### In `ai_context_planner.py`:
```python
PLANNING WITH TOOLS:
1. List available categories: list_tool_categories()
2. Search relevant tools for your task
3. Plan tool sequences for complex tasks
4. Consider tool costs and constraints
```

## 🚦 Tool Selection Decision Tree

```
Task Complexity Assessment
├─ Simple (single operation)
│  └─ Use single tool directly
├─ Medium (2-3 operations)
│  └─ Chain tools with context passing
└─ Complex (many operations)
   └─ Create tool sequence plan first

Cost Consideration
├─ Frequent operation → Check cache first
├─ Heavy computation → Consider caching results
└─ External API → Rate limit awareness

Error Handling
├─ Tool fails → Check related_tools
├─ Missing data → Validate inputs first
└─ Timeout → Consider async execution
```

## 📊 Benefits

1. **Discoverability**: AI can find tools without hardcoding
2. **Intelligence**: Rich metadata enables smart selection
3. **Efficiency**: Reuse instead of reimplementation
4. **Consistency**: All AI assistants use same tools
5. **Extensibility**: Easy to add new tools
6. **Observability**: Track tool usage and performance

## 🔗 Next Steps

1. **Implement RAG for tool docs** - For even richer tool discovery
2. **Add tool composition** - Combine simple tools into complex ones
3. **Usage analytics** - Learn from tool execution patterns
4. **Auto-optimization** - Suggest better tool sequences
5. **Tool versioning** - Handle tool evolution gracefully

This system transforms AI assistants from code generators to intelligent tool orchestrators!
