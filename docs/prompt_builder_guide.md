# PromptBuilder Module

The PromptBuilder module is a powerful component for creating dynamic, persona-driven prompts in the AI Orchestration System. It transforms basic persona configurations into rich, tailored prompts that capture each persona's unique traits, communication style, and knowledge.

## Overview

The PromptBuilder enhances persona interactions by:

1. **Translating traits into directives** - Converting abstract persona traits (like efficiency or creativity) into specific instructions
2. **Applying persona-specific formatting** - Adjusting tone, language patterns, and structure based on persona identity
3. **Incorporating memory context** - Intelligently including relevant conversation history
4. **Generating optimized prompts** - Creating LLM-ready prompts in various formats (chat, instruction, raw)

## Architecture

The PromptBuilder module consists of several key components:

```
PromptBuilder
├── Formatters
│   ├── TraitBasedFormatter
│   ├── ToneFormatter
│   └── MemoryContextFormatter
├── Templates
│   └── TemplateLibrary
└── TraitsProcessor
```

- **PromptBuilder**: Core class that orchestrates prompt creation
- **Formatters**: Transform prompts based on specific criteria
- **Templates**: Pre-defined prompt structures for different personas
- **TraitsProcessor**: Converts persona traits into actionable directives

## Usage

### Basic Usage

```python
from packages.shared.src.prompt_builder import PromptBuilder, PromptFormat
from packages.shared.src.models.base_models import PersonaConfig

# Create a prompt builder
builder = PromptBuilder()

# Define a persona
persona = PersonaConfig(
    name="Cherry", 
    description="A cheerful and energetic assistant",
    prompt_template="Respond in a cheerful tone: {input}",
    traits={"efficiency": 0.7, "empathy": 0.9}
)

# Build a prompt
prompt = builder.build_prompt(
    persona=persona,
    user_input="How does machine learning work?",
    format=PromptFormat.CHAT
)

# Use the prompt with an LLM
response = llm_client.generate_chat_completion(messages=prompt)
```

### Using with FastAPI Dependencies

The module provides dependencies for use in FastAPI applications:

```python
from fastapi import Depends
from core.orchestrator.src.api.dependencies.prompt_builder import build_prompt_for_persona

@router.post("/interact")
async def interact(
    user_input: UserInput,
    active_persona: PersonaConfig = Depends(get_active_persona),
    prompt_messages: list = Depends(build_prompt_for_persona)
):
    # prompt_messages is already built with the active persona
    response = await llm_client.generate_chat_completion(messages=prompt_messages)
    return {"response": response["content"]}
```

## Persona Traits

The PromptBuilder processes a wide range of persona traits:

| Trait | High Value (0.7-1.0) | Low Value (0.0-0.3) |
|-------|----------------------|---------------------|
| Efficiency | Concise, direct communication | Detailed, thorough explanations |
| Assertiveness | Confident, authoritative language | Gentle, suggestive language |
| Pragmatism | Practical, actionable advice | Theoretical, conceptual perspectives |
| Creativity | Innovative, novel approaches | Conventional, established approaches |
| Empathy | Emotionally aware, supportive | Factual, logical focus |
| Humor | Light-hearted, playful tone | Serious, straightforward tone |
| Formality | Professional, structured language | Casual, conversational language |
| Detail Orientation | Specific, comprehensive coverage | High-level, big picture focus |

Traits are defined in the persona configuration and automatically processed to shape the prompt.

## Prompt Formats

The PromptBuilder supports multiple output formats:

- **CHAT**: A list of message objects for chat-based LLM APIs
  ```python
  [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
  ]
  ```

- **INSTRUCTION**: A single string formatted for instruction-following models
  ```
  You are Cherry, a cheerful assistant.
  User: How are you?
  Assistant: 
  ```

- **RAW**: A simple text prompt without special formatting

## Extending the Module

### Adding New Traits

To add support for new traits, extend the `TraitsProcessor` class:

```python
def _process_analytical(self, value: float) -> Tuple[str, Dict[str, Any]]:
    """Process analytical trait."""
    params = {"analytical_level": "moderate"}
    
    if value >= 0.7:
        params["analytical_level"] = "high"
        return (
            "You have strong analytical abilities. Break down complex topics into "
            "component parts and examine relationships between concepts.",
            params
        )
    elif value <= 0.3:
        params["analytical_level"] = "low"
        return (
            "You focus more on intuition than analysis. Present holistic views "
            "rather than detailed breakdowns.",
            params
        )
    
    return "", params
```

### Adding New Templates

To add new prompt templates, use the `TemplateLibrary`:

```python
from packages.shared.src.prompt_builder import get_template_library, PromptTemplate

template_library = get_template_library()
template_library.add_template(PromptTemplate(
    "analytical",
    "You are {name}, a highly analytical assistant. Your responses should be "
    "structured, logical, and detailed, with careful examination of all aspects."
))
```

## Implementation Details

### Traits Processing Flow

1. Traits are extracted from the persona configuration
2. Each trait is processed by a specialized handler
3. Processing generates directive strings and parameter values
4. Directives are added to the system prompt
5. Parameters influence formatting decisions

### Template Selection

Templates are selected based on:

1. Exact match with persona name
2. Trait-based matching (e.g., high efficiency → efficient template)
3. Description-based matching
4. Fallback to generic template

## Best Practices

- **Define Clear Traits**: Be specific about traits to get the most benefit
- **Use Appropriate Formats**: Choose the right format for your LLM
- **Balance Traits**: Avoid contradictory trait combinations (e.g., high efficiency + high detail)
- **Test Prompts**: Verify that prompts generate the expected persona behavior
