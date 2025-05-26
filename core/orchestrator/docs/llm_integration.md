# LLM Integration for AI Orchestration System

This document describes the integration of Large Language Models (LLMs) into the AI Orchestration System using the OpenRouter API.

## Architecture

The LLM integration follows the existing architecture patterns of the AI Orchestration System:

1. **Provider Layer**: Abstract interface for LLM providers with a specific implementation for OpenRouter
2. **Agent Layer**: LLM-specific agent that leverages the provider API
3. **API Layer**: Endpoints for interacting with LLMs through the orchestration system

### Key Components

- **LLMProvider**: Abstract base class for LLM providers
- **OpenRouterProvider**: Implementation for the OpenRouter API
- **LLMAgent**: Agent that uses LLM providers to generate responses
- **ConversationFormatter**: Utility for formatting conversation history for LLM input

## Configuration

The LLM integration uses the following configuration settings in `config.py`:

```python
# LLM settings
OPENROUTER_API_KEY: Optional[str] = None
DEFAULT_LLM_MODEL: str = "openai/gpt-3.5-turbo"
```

To use the LLM integration, you need to set the `OPENROUTER_API_KEY` environment variable or update the settings in `config.py`.

## Usage

### Via API

There are two primary endpoints for interacting with LLMs:

1. **`/api/llm/interact`**: Process a user interaction using the orchestration system with LLM-based responses
2. **`/api/llm/direct`**: Send messages directly to the LLM provider without orchestration

### Example API Requests

#### Orchestrated Interaction

```http
POST /api/llm/interact
Content-Type: application/json

{
  "message": "Tell me about artificial intelligence",
  "user_id": "user123",
  "persona_id": "cherry",
  "model": "openai/gpt-4"
}
```

#### Direct Completion

```http
POST /api/llm/direct
Content-Type: application/json

[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Tell me about artificial intelligence"}
]
```

### Via Python Client

You can use the provided `llm_client.py` example script:

```bash
# Orchestrated interaction
python core/orchestrator/examples/llm_client.py --message "Tell me about artificial intelligence" --persona-id "cherry"

# Direct completion
python core/orchestrator/examples/llm_client.py --mode direct --message "Tell me about artificial intelligence" --system "You are a helpful AI expert."
```

## Integration with Existing Components

### Memory Integration

The LLM agent integrates with the memory system by:

- Retrieving conversation history for context
- Storing both user inputs and LLM responses

### Persona Integration

The LLM agent leverages personas by:

- Creating system messages based on persona traits and characteristics
- Formatting responses according to persona styles

### Orchestration Integration

The LLM agent works with the orchestration system by:

- Using the event system for interaction events
- Supporting selection based on context
- Handling fallbacks for error cases

## Extending the LLM Integration

### Adding New LLM Providers

To add a new LLM provider:

1. Create a new class that inherits from `LLMProvider`
2. Implement the required methods
3. Register the provider using `register_llm_provider`

Example:

```python
class CustomProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "custom_provider"

    async def generate_chat_completion(self, messages, model=None, temperature=0.7, max_tokens=None):
        # Implementation here
        pass
```

### Custom Prompting

The `ConversationFormatter` class can be extended or customized to implement different prompting strategies:

```python
class SpecializedFormatter(ConversationFormatter):
    @staticmethod
    def create_system_message(persona: PersonaConfig) -> Dict[str, str]:
        # Custom system message implementation
        pass
```

## Implementation Notes

- The integration is fully asynchronous for optimal performance
- Error handling follows the existing patterns with fallbacks
- Token usage tracking is enabled for monitoring purposes
- The system supports different models through the OpenRouter API
