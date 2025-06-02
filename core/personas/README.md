# Persona Configuration System

This module provides a comprehensive system for managing AI personas in the orchestration system. It includes models for persona configuration, a manager for loading and managing personas from YAML files, and example personas for different use cases.

## Features

- **Comprehensive Persona Models**: Full Pydantic models for persona configuration including traits, behaviors, knowledge domains, and response styles
- **YAML-based Configuration**: Load persona configurations from YAML files for easy management
- **Hot-reloading Support**: Automatically detect and reload updated persona configurations
- **Validation**: Built-in validation for persona configurations
- **Filtering and Search**: Filter personas by status, tags, and other criteria
- **Export Functionality**: Export personas back to YAML format

## Installation

The persona system requires the following dependencies:

```bash
pip install pydantic>=2.0 pyyaml>=6.0
```

For development and testing:

```bash
pip install pytest>=7.0 pytest-asyncio>=0.21
```

## Quick Start

### 1. Basic Usage

```python
from core.personas import PersonaConfigManager

# Initialize the manager with a directory containing YAML files
manager = PersonaConfigManager("./config/personas")

# Load all personas from the directory
personas = manager.load_all_personas()

# Get a specific persona
cherry = manager.get_persona("cherry")
print(f"Loaded {cherry.name}: {cherry.description}")

# List all active personas
active_personas = manager.list_personas(status="active")
for persona in active_personas:
    print(f"- {persona.name} ({persona.slug})")
```

### 2. Loading from YAML

Create a YAML file with persona configuration:

```yaml
name: "Assistant"
slug: "assistant"
description: "A helpful AI assistant"
status: "active"
created_by: "admin"

traits:
  - name: "helpfulness"
    category: "personality"
    value: 90
    weight: 2.0
    description: "Eager to help and provide assistance"

response_style:
  type: "casual"
  tone: "friendly"
  formality_level: 4
  verbosity: 6
  use_examples: true

interaction_mode: "conversational"
temperature: 0.7
max_tokens: 2000
```

### 3. Filtering Personas

```python
# Filter by status
active_personas = manager.list_personas(status=PersonaStatus.ACTIVE)

# Filter by tags
technical_personas = manager.list_personas(tags=["technical", "expert"])

# Combine filters
active_technical = manager.list_personas(
    status=PersonaStatus.ACTIVE,
    tags=["technical"]
)
```

## Included Example Personas

The `personas_detailed.yaml` file includes three example personas:

### 1. Cherry - Strategic Orchestrator
- **Focus**: High-level planning and system architecture
- **Strengths**: Strategic thinking, delegation, systems thinking
- **Use Cases**: Project planning, architecture design, workflow coordination
- **Temperature**: 0.4 (more focused/deterministic)

### 2. Sophia - Analytical Depth
- **Focus**: Data analysis and research
- **Strengths**: Analytical thinking, attention to detail, research skills
- **Use Cases**: Data analysis, research tasks, evidence-based decision making
- **Temperature**: 0.2 (highly focused/deterministic)

### 3. Karen - Creative Solutions
- **Focus**: Creative problem solving and innovation
- **Strengths**: Creativity, lateral thinking, adaptability
- **Use Cases**: Brainstorming, design thinking, finding unconventional solutions
- **Temperature**: 0.9 (more creative/varied)

## API Reference

### PersonaConfigManager

The main class for managing persona configurations.

#### Methods

- `__init__(config_dir: Union[str, Path])`: Initialize with a configuration directory
- `load_persona_from_file(file_path: Union[str, Path]) -> PersonaConfiguration`: Load a single persona
- `load_all_personas() -> Dict[str, PersonaConfiguration]`: Load all personas from directory
- `get_persona(slug: str) -> PersonaConfiguration`: Get a specific persona by slug
- `list_personas(status: Optional[PersonaStatus] = None, tags: Optional[List[str]] = None) -> List[PersonaConfiguration]`: List personas with optional filtering
- `reload_persona(slug: str, file_path: Optional[Path] = None) -> PersonaConfiguration`: Reload a specific persona
- `check_for_updates() -> Set[str]`: Check for and reload updated persona files
- `validate_all() -> Dict[str, List[str]]`: Validate all loaded personas
- `export_persona(slug: str, output_path: Union[str, Path])`: Export a persona to YAML

### PersonaConfiguration

The main model representing a complete persona configuration.

#### Key Attributes

- `name`: Display name of the persona
- `slug`: URL-safe identifier
- `description`: Detailed description
- `status`: Current status (active, inactive, draft, archived)
- `traits`: List of personality and behavioral traits
- `response_style`: Response formatting and style configuration
- `knowledge_domains`: Areas of expertise
- `behavior_rules`: Behavioral rules and constraints
- `interaction_mode`: Primary interaction mode
- `memory_config`: Memory and context configuration
- `temperature`: LLM temperature setting
- `max_tokens`: Maximum response tokens

### Models

#### PersonaTrait
Defines individual traits with categories, values, and weights.

#### ResponseStyle
Configures how the persona structures and delivers responses.

#### KnowledgeDomain
Represents areas of expertise with topics and related tools.

#### BehaviorRule
Defines conditional behaviors and actions.

#### MemoryConfiguration
Configures memory retention and context management.

## Error Handling

The module provides specific exceptions:

- `PersonaConfigError`: General configuration errors
- `PersonaNotFoundError`: When a requested persona doesn't exist

```python
try:
    persona = manager.get_persona("nonexistent")
except PersonaNotFoundError:
    print("Persona not found")
```

## Best Practices

1. **Organize Personas by Purpose**: Group related personas in subdirectories
2. **Use Meaningful Slugs**: Choose clear, descriptive slugs for easy reference
3. **Version Control**: Keep persona YAML files in version control
4. **Validate Regularly**: Run validation after making changes
5. **Document Changes**: Include comments in YAML files for complex configurations

## Development

### Running Tests

```bash
# Run all tests
python -m pytest core/personas/test_manager.py -v

# Run with coverage
python -m pytest core/personas/test_manager.py --cov=core.personas
```

### Adding New Personas

1. Create a new YAML file in the personas directory
2. Define all required fields (name, slug, description, etc.)
3. Add at least one trait and configure response style
4. Test loading with the manager
5. Validate the configuration

## Architecture Notes

- **Pydantic Models**: All data models use Pydantic for validation and serialization
- **Type Safety**: Full type hints throughout the codebase
- **Modular Design**: Clear separation between models, manager, and utilities
- **Performance**: File caching and lazy loading for efficient operations
- **Extensibility**: Easy to add new trait categories, response styles, etc.

## Future Enhancements

- Async support for loading large numbers of personas
- Database backend option (PostgreSQL/Weaviate)
- Persona inheritance/composition
- A/B testing support for persona variations
- Integration with LLM providers for automatic optimization