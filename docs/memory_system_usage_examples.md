# Memory System Usage Examples

This document provides practical examples of how to use the memory system, specifically focusing on:

1. Storing and retrieving development notes and technical context
2. Managing personal information with privacy controls
3. Configuring the system for different deployment environments

These examples demonstrate how to properly separate development context from personal information throughout the application lifecycle.

## Prerequisites

Before using these examples, make sure you have:

- PostgreSQL
- Required Python dependencies installed (`psycopg2
- Configured environment variables (or provide explicit values in code)

## Storing Development Context

Development notes capture technical decisions, implementation details, and architectural patterns that are useful for other developers.

### Basic Development Note Example

```python
import asyncio
from datetime import datetime, timedelta
from packages.shared.src.memory.dev_notes_manager import DevNotesManager
from packages.shared.src.memory.PostgreSQL
from packages.shared.src.models.metadata_schemas import DevNoteType
from packages.shared.src.storage.config import StorageConfig

async def store_development_context():
    # Create configuration for development environment
    config = StorageConfig(
        environment="dev",
        enable_dev_notes=True
    )

    # Create memory adapter
    adapter = PostgreSQL
        project_id="your-project-id",
        credentials_path="/path/to/credentials.json"
    )

    # Initialize adapter
    await adapter.initialize()

    # Create dev notes manager
    dev_notes = DevNotesManager(
        memory_manager=adapter,
        config=config,
        agent_id="dev_system"
    )

    await dev_notes.initialize()

    # Store an architecture decision note
    await dev_notes.add_architecture_note(
        component="memory_system",
        decision="Use PostgreSQL
        context="Need scalable cloud storage with transactions and flexible querying",
        alternatives=[
            "Redis for faster performance but less persistence",
            "Postgres for stronger schema validation",
            "DynamoDB for potentially lower costs at scale"
        ],
        consequences="PostgreSQL
        metadata={
            "author": "Jane Developer",
            "commit_id": "abc123def456",
            "ticket_id": "ARCH-456",
            "visibility": "team"
        }
    )

    # Store an implementation note
    await dev_notes.add_implementation_note(
        component="PostgreSQL
        overview="Implemented retry mechanism for PostgreSQL
        implementation_details="""
        Added exponential backoff retry logic for all PostgreSQL
        transient connection issues. The retry mechanism uses a maximum of 3 attempts
        with increasing delays between each attempt.
        """,
        affected_files=[
            "packages/shared/src/storage/PostgreSQL
            "packages/shared/src/storage/exceptions.py"
        ],
        testing_status="unit_tests_passed",
        metadata={
            "author": "John Coder",
            "priority": "high",
            "ticket_id": "FEAT-123"
        }
    )

    # Store an issue note
    await dev_notes.add_issue_note(
        component="privacy_manager",
        issue_description="PII detection regex for phone numbers has false positives",
        reproduction_steps=[
            "Create a memory item with text containing '123-456-7890 units'",
            "Process through the privacy manager",
            "Observe that the number is incorrectly detected as a phone number"
        ],
        impact="Some legitimate content is being redacted unnecessarily",
        proposed_solution="Update regex to require word boundaries or improve pattern",
        priority="normal",
        metadata={
            "author": "Sam Tester",
            "ticket_id": "BUG-789"
        }
    )

    # Close managers
    await dev_notes.close()
    await adapter.close()

# Run the example
asyncio.run(store_development_context())
```

### Retrieving Development Context

```python
async def retrieve_development_notes():
    # Setup similar to previous example
    config = StorageConfig(environment="dev", enable_dev_notes=True)
    adapter = PostgreSQL
    await adapter.initialize()

    dev_notes = DevNotesManager(memory_manager=adapter, config=config)
    await dev_notes.initialize()

    # Get notes for a specific component
    memory_system_notes = await dev_notes.get_component_notes(
        component="memory_system"
    )

    print(f"Found {len(memory_system_notes)} notes for memory_system component")

    # Get notes of a specific type for a component
    architecture_notes = await dev_notes.get_component_notes(
        component="memory_system",
        note_type=DevNoteType.ARCHITECTURE
    )

    print(f"Found {len(architecture_notes)} architecture notes")

    # Close managers
    await dev_notes.close()
    await adapter.close()

asyncio.run(retrieve_development_notes())
```

## Managing Personal Information

Personal information requires different handling with appropriate privacy controls.

### Storing Personal Information with Privacy Controls

```python
import asyncio
from datetime import datetime
from packages.shared.src.memory.privacy_enhanced_memory_manager import (
    PIIDetectionConfig,
    PrivacyEnhancedMemoryManager,
)
from packages.shared.src.memory.PostgreSQL
from packages.shared.src.models.base_models import MemoryItem
from packages.shared.src.storage.config import StorageConfig

async def store_personal_information():
    # Create configuration for production environment
    config = StorageConfig(
        environment="prod",
        default_privacy_level="sensitive",
        enforce_privacy_classification=True
    )

    # Configure PII detection with more strict settings for production
    pii_config = PIIDetectionConfig()
    pii_config.ENABLE_PII_REDACTION = True
    pii_config.DEFAULT_RETENTION_DAYS = 90  # Shorter retention in production

    # Create base adapter
    adapter = PostgreSQL
        project_id="your-production-project",
        credentials_path="/path/to/prod_credentials.json"
    )

    await adapter.initialize()

    # Create privacy-enhanced manager
    privacy_manager = PrivacyEnhancedMemoryManager(
        underlying_manager=adapter,
        config=config,
        pii_config=pii_config
    )

    await privacy_manager.initialize()

    # Store a conversation message that might contain PII
    message_with_pii = MemoryItem(
        user_id="user123",
        session_id="session456",
        timestamp=datetime.utcnow(),
        item_type="conversation",
        text_content="Hi, my name is John Smith and my email is john.smith@example.com. "
                     "Call me at 555-123-4567.",
        metadata={
            "source": "chat_interface",
            "retention_period": 30  # shorter retention for sensitive data
        }
    )

    # The privacy manager will automatically:
    # 1. Detect PII (name, email, phone)
    # 2. Classify the privacy level (sensitive due to PII)
    # 3. Redact PII if configured to do so
    # 4. Add appropriate metadata and set expiration
    item_id = await privacy_manager.add_memory_item(message_with_pii)

    print(f"Stored conversation with ID: {item_id}")

    # Retrieve the item to see how PII was handled
    stored_item = await privacy_manager.get_memory_item(item_id)

    if stored_item:
        print(f"Retrieved item content: {stored_item.text_content}")
        print(f"Privacy classification: {stored_item.metadata.get('data_classification')}")
        print(f"PII detected: {stored_item.metadata.get('pii_detected')}")
        print(f"PII types: {stored_item.metadata.get('pii_types')}")
        print(f"Expiration: {stored_item.expiration}")

    # Close managers
    await privacy_manager.close()
    await adapter.close()

asyncio.run(store_personal_information())
```

### Retrieving User Data with Privacy Controls

```python
async def retrieve_conversation_history():
    # Similar setup to previous example
    config = StorageConfig(environment="prod")
    adapter = PostgreSQL
    await adapter.initialize()

    privacy_manager = PrivacyEnhancedMemoryManager(
        underlying_manager=adapter,
        config=config
    )

    await privacy_manager.initialize()

    # Get conversation history for a specific user
    user_id = "user123"
    session_id = "session456"

    history = await privacy_manager.get_conversation_history(
        user_id=user_id,
        session_id=session_id,
        limit=10
    )

    print(f"Retrieved {len(history)} conversation items")

    # Note: The history items will have any configured PII redactions
    # and will respect privacy classifications

    # Close managers
    await privacy_manager.close()
    await adapter.close()

asyncio.run(retrieve_conversation_history())
```

## Multi-Environment Configuration

Different deployment environments require different configurations:

### Development Environment

```python
def create_dev_environment_config():
    return StorageConfig(
        environment="dev",
        enable_dev_notes=True,
        default_privacy_level="standard",
        enforce_privacy_classification=False
    )
```

### Staging Environment

```python
def create_staging_environment_config():
    return StorageConfig(
        environment="staging",
        enable_dev_notes=True,  # Still allowing dev notes in staging
        default_privacy_level="sensitive",
        enforce_privacy_classification=True
    )
```

### Production Environment

```python
def create_production_environment_config():
    return StorageConfig(
        environment="prod",
        enable_dev_notes=False,  # No dev notes in production
        default_privacy_level="sensitive",
        enforce_privacy_classification=True
    )
```

## Multi-Tenant Deployment

For multi-tenant applications, add namespace isolation:

```python
def create_tenant_config(tenant_id: str, environment: str):
    return StorageConfig(
        namespace=f"tenant_{tenant_id}",
        environment=environment,
        enable_dev_notes=environment != "prod",
        default_privacy_level="sensitive" if environment == "prod" else "standard",
        enforce_privacy_classification=environment in ["staging", "prod"]
    )
```

## Best Practices

When working with both development context and personal information:

1. **Always use the right manager for the data type:**

   - `DevNotesManager` for technical documentation and development context
   - `PrivacyEnhancedMemoryManager` for user data and personal information

2. **Use appropriate metadata for searchability:**

   - Development notes: component, note_type, author, ticket_id
   - Personal data: data_classification, retention_period, consent_reference

3. **Set proper expiration policies:**

   - Development notes: Longer retention (6-12 months) with archiving strategy
   - Personal data: Shorter retention based on privacy regulations and data type

4. **Implement access controls:**

   - Development notes: Limited to development team and support staff
   - Personal data: Limited to specific services and the user themselves

5. **Apply environment-specific settings:**
   - Development: More lenient with logging and fewer restrictions
   - Production: Strict privacy controls, PII redaction, and shorter retention periods

These principles ensure proper separation of concerns between development context and personal information throughout your application's lifecycle.
