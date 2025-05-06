# Maximizing Phidata Agent UI Integration

This guide explains how to maximize the utility of the pre-built Phidata Agent UI container that's connected to your Orchestra backend. Since direct UI code customization isn't feasible with the pre-built container, we'll focus on configuring your backend and agents for optimal UI display.

## Table of Contents

- [Overview](#overview)
- [Key Integration Points](#key-integration-points)
- [Markdown Support](#markdown-support)
- [Structured Output Formatting](#structured-output-formatting)
- [Tool Call Visibility](#tool-call-visibility)
- [Session Management](#session-management)
- [Agent Configuration Examples](#agent-configuration-examples)
- [Testing Your Integration](#testing-your-integration)

## Overview

The Phidata Agent UI provides a web interface for interacting with your Orchestra backend. By properly configuring your backend and agents, you can ensure that responses are displayed in a readable, well-formatted manner in the UI.

Key components:
- **Backend API Endpoint**: The `/phidata/chat` endpoint processes requests from the UI
- **Phidata Agent Wrapper**: Handles agent initialization with proper storage/memory
- **Structured Output Formatting**: Converts structured data to readable markdown

## Key Integration Points

1. **`/phidata/chat` Endpoint**: We've enhanced this endpoint to:
   - Accept session identifiers for conversation persistence
   - Return properly formatted markdown responses
   - Handle structured outputs by converting them to markdown
   - Control tool call visibility based on agent configuration

2. **`PhidataAgentWrapper`**: This wrapper now:
   - Properly initializes agents with CloudSQL PgVector storage
   - Configures markdown output and tool call visibility
   - Handles structured outputs via response_model configuration

3. **Agent YAML Configurations**: Your agent YAML files should include:
   - `markdown: true` setting for readable UI output
   - `show_tool_calls` setting (true for dev, false for prod)
   - Proper storage/memory configuration for session persistence

## Markdown Support

Markdown makes responses significantly more readable in the UI by enabling:

- Code blocks with syntax highlighting
- Bulleted and numbered lists
- Headings and subheadings
- Bold/italic text
- Tables for structured data

### How to Enable Markdown

1. In your YAML agent configurations:
   ```yaml
   phidata_agent:
     # Other configuration...
     markdown: true  # This enables markdown formatting
   ```

2. For teams, enable at both team and member levels:
   ```yaml
   phidata_team:
     # Team configuration...
     team_markdown: true
     members:
       - name: "Member1"
         # Member configuration...
         markdown: true
   ```

3. The `/phidata/chat` endpoint now automatically sets `content_format: "markdown"` in responses.

## Structured Output Formatting

When agents return structured data (like JSON objects instead of plain text), we automatically convert these to well-formatted markdown for display in the UI.

### How It Works

1. The updated `/phidata/chat` endpoint detects structured outputs (dictionaries or objects)
2. Our `format_structured_output_as_markdown` utility converts the structure to markdown
3. Special formatters exist for common output types:
   - Movie scripts
   - Salesforce query results
   - Analysis reports
   - General dictionaries and lists

### Response Models

For agents that should return specific data structures, use a response model:

```yaml
phidata_movie_script_agent:
  phidata_agent_class: "agno.structured.StructuredAgent"
  # Other configuration...
  response_model_path: "packages.models.movie.MovieScript"
```

The response will automatically be formatted as markdown for display in the UI.

## Tool Call Visibility

Tool calls can be displayed or hidden in the UI based on your configuration.

### Development vs. Production

- **Development**: Show tool calls for debugging
  ```yaml
  phidata_dev_agent:
    # Other configuration...
    show_tool_calls: true
  ```

- **Production**: Hide tool calls for a cleaner interface
  ```yaml
  phidata_prod_agent:
    # Other configuration...
    show_tool_calls: false
  ```

The `/phidata/chat` endpoint respects this setting when returning responses to the UI.

## Session Management

Proper session management ensures conversation history is maintained correctly.

### How It Works

1. The Phidata UI passes a `session_id` with each request
2. Our `/phidata/chat` endpoint passes this to the agent wrapper
3. The agent wrapper configures Phidata's native PgAgentStorage with this session_id
4. This allows retrieving and storing conversation history per session

### Requirements

1. Configure CloudSQL PgVector storage in your agent YAML:
   ```yaml
   phidata_agent:
     # Other configuration...
     storage:
       table_name: "agent_storage"
       schema_name: "llm"
     memory:
       table_name: "agent_memory"
       schema_name: "llm"
   ```

2. Ensure the CloudSQL instance is properly configured with the pgvector extension.

## Agent Configuration Examples

See [core/orchestrator/examples/phidata_agent_ui_config.yaml](../core/orchestrator/examples/phidata_agent_ui_config.yaml) for complete examples, including:

- Development agent (with visible tool calls)
- Production agent (with clean UI)
- Structured output agent (movie script generator)
- Team agent (research team)

## Testing Your Integration

1. **Verify Markdown Rendering**:
   - Test with various markdown features (code blocks, lists, tables)
   - Ensure they render correctly in the UI

2. **Test Structured Output**:
   - Use an agent with a response_model
   - Verify the output is formatted legibly in the UI

3. **Check Conversation History**:
   - Have a multi-turn conversation
   - Refresh the page and verify history is maintained

4. **Verify Tool Call Visibility**:
   - Compare dev and prod agent configurations
   - Ensure tool calls are visible/hidden as configured

## Advanced Customization

### Custom Structured Output Formatters

If you need to add custom formatters for specific output types, extend the `format_structured_output_as_markdown` function in `core/orchestrator/src/api/utils/format_structured_output.py`.

Example for a custom output type:

```python
def format_custom_output(data: Dict[str, Any]) -> str:
    """Format a custom output type as markdown."""
    markdown = "# Custom Output\n\n"
    # Add custom formatting logic...
    return markdown

# Then add to the main function:
def format_structured_output_as_markdown(data: Any, output_type: Optional[str] = None) -> str:
    # Existing code...
    
    # Add your custom type:
    if output_type == "custom_type":
        return format_custom_output(data)
    
    # Existing code...
```

### Agent Name and Role Display

The UI can display agent names and roles. Ensure your YAML configs include:

```yaml
phidata_agent:
  name: "Helpful Assistant"  # Displayed in the UI
  role: "I help answer questions about..."  # Can be displayed in the UI
```

These fields will be passed to the UI for display.
