# Memory System Data Separation Guide

This document outlines how the memory system separates development context notes from personal user information during deployment, providing guidelines for proper data isolation and security.

## Overview

The memory system stores two distinct types of data:

1. **Development Context**: Technical documentation, architecture decisions, implementation notes, and other development-related information
2. **Personal Information**: User conversation history, preferences, and other user-specific data that may contain personal identifiable information (PII)

These data types have different characteristics and requirements:

| Characteristic | Development Context | Personal Information                     |
| -------------- | ------------------- | ---------------------------------------- |
| Privacy Level  | Generally lower     | Potentially high                         |
| Retention      | Longer term         | Subject to data protection laws          |
| Access Pattern | Team-wide           | User-specific with strict access control |
| Classification | By component/system | By user/privacy level                    |
| Regulation     | Internal policies   | External regulations (GDPR, CCPA, etc.)  |

## Implementation Components

Our implementation separates these data types through:

1. **Enhanced Configuration System** (`StorageConfig`)
2. **Metadata Schema Validation** (`DevNoteMetadata` vs `UserDataMetadata`)
3. **Specialized Managers** (`DevNotesManager` vs `PrivacyEnhancedMemoryManager`)
4. **Collection Namespacing** (Environment, privacy level, tenant separation)
5. **PostgreSQL

## Deployment Strategy

During deployment, we employ multiple strategies to ensure proper data separation:

### 1. Configuration Setup

```python
# Development data configuration (typically in a development environment)
dev_config = StorageConfig(
    environment="dev",
    enable_dev_notes=True,
    default_privacy_level="standard"
)

# Production data configuration (for user-facing systems)
prod_config = StorageConfig(
    environment="prod",
    enable_dev_notes=False,  # Often disabled in production
    default_privacy_level="sensitive",
    enforce_privacy_classification=True
)

# Multi-tenant configuration (for SaaS deployments)
tenant_config = StorageConfig(
    namespace=f"tenant_{tenant_id}",
    environment="prod",
    enforce_privacy_classification=True
)
```

### 2. Different Collection Names

Development notes and personal information are stored in separate collections:

```
# Development Context Collections
dev_notes_dev
agent_data_dev

# User Data Collections (with privacy levels)
memory_items_standard_prod
memory_items_sensitive_prod
memory_items_critical_prod
```

This separation is managed by the `get_collection_name()` function in `StorageConfig`, which applies the appropriate prefixes and suffixes based on:

- Environment (dev, staging, prod)
- Privacy level (standard, sensitive, critical)
- Namespace (for multi-tenant deployments)

### 3. Specialized Managers with Different Access Patterns

```python
# Development context manager (used by development tools)
dev_notes_manager = DevNotesManager(
    memory_manager=PostgreSQL
    config=dev_config
)

# Personal information manager (used by user-facing systems)
privacy_manager = PrivacyEnhancedMemoryManager(
    underlying_manager=PostgreSQL
    config=prod_config
)
```

Each manager encapsulates the appropriate validation, storage, and access patterns for its data type.

## PostgreSQL

The separation is enforced at the database level through PostgreSQL

```javascript
rules_version = '2';
service cloud.PostgreSQL
  match /databases/{database}/documents {
    // Development notes access - restricted to developers
    match /dev_notes_{environment}/{document=**} {
      allow read: if request.auth.token.role in ['developer', 'architect', 'admin'];
      allow write: if request.auth.token.role in ['developer', 'architect', 'admin'];
    }

    match /agent_data_{environment}/{document=**} {
      allow read: if request.auth.token.role in ['developer', 'architect', 'admin', 'support'];
      allow write: if request.auth.token.role in ['developer', 'architect', 'admin'];
    }

    // User data access - restricted by user_id and service roles
    match /memory_items_{privacy_level}_{environment}/{document} {
      // Users can only access their own data
      allow read: if request.auth.uid == resource.data.user_id;

      // Services can access data according to their permissions
      allow read: if request.auth.token.role == 'service' &&
                   request.auth.token.service_name in ['conductor', 'memory_service'];

      // Write permissions are strictly limited to authorized services
      allow write: if request.auth.token.role == 'service' &&
                   request.auth.token.service_name in ['conductor', 'memory_service'] &&
                   request.auth.token.write_access == true;
    }

    // Multi-tenant isolation
    match /{tenant_namespace}/{collection}/{document} {
      allow read, write: if request.auth.token.tenant_id == tenant_namespace;
    }
  }
}
```

## Auditing and Monitoring

To ensure ongoing separation of concerns:

1. **Access Logging**: All access to development notes and personal information is logged
2. **Regular Audits**: Periodic reviews ensure data is properly classified and stored
3. **Automated Classification Checks**: Validation that data is stored in the correct collections

## Deployment Checklist

When deploying the memory system, ensure:

- [ ] Configuration uses the correct environment and privacy settings
- [ ] PostgreSQL
- [ ] Development notes are not migrated to production environments
- [ ] Personal information is properly classified by privacy level
- [ ] PII detection and redaction is enabled in production
- [ ] Data retention periods are configured according to regulations
- [ ] Access auditing is enabled for sensitive collections

## Handling Migration Between Environments

When moving from development to staging/production:

1. **Development Notes**:

   - Document key architecture decisions in permanent repositories
   - Do not migrate dev_notes or agent_data to production
   - If needed, create sanitized versions for production documentation

2. **Personal Information**:
   - Anonymize or use synthetic data in development/staging
   - Use privacy classification to determine migration strategy
   - Apply data minimization before migrating to production
   - Enforce shorter retention periods in production

## Accessing Development Context in Production

On rare occasions when access to development context is needed in production:

1. Use a read-only secure interface with strict access controls
2. Implement specific approval workflows for production access
3. Consider a separate "documentation" database that's maintained separately
4. Log all access attempts and reasons

## Example: Adding Development Notes During Deployment

```python
# During deployment, capture important implementation details
async def record_deployment_notes(deployment_id: str, version: str, changes: List[str]):
    """Record deployment notes for future reference."""
    dev_notes_manager = DevNotesManager(
        memory_manager=PostgreSQL
        config=StorageConfig(environment="prod", enable_dev_notes=True)
    )

    await dev_notes_manager.initialize()

    # Record the deployment as an implementation note
    await dev_notes_manager.add_implementation_note(
        component="memory_system",
        overview=f"Deployment {version} - Memory System Enhancement",
        implementation_details="Implemented privacy enhancements and dev notes manager",
        affected_files=[
            "packages/shared/src/storage/config.py",
            "packages/shared/src/models/metadata_schemas.py",
            "packages/shared/src/memory/dev_notes_manager.py",
            "packages/shared/src/memory/privacy_enhanced_memory_manager.py"
        ],
        testing_status="integration_tests_passed",
        metadata={
            "deployment_id": deployment_id,
            "version": version,
            "commit_id": "abc123def456",
            "priority": "normal",
            "expiration": datetime.utcnow() + timedelta(days=180)  # 6 month retention
        }
    )

    await dev_notes_manager.close()
```

## Example: Storing Personal Information

```python
async def store_user_conversation(user_id: str, session_id: str, message: str):
    """Store a user conversation message with privacy protections."""
    # Create underlying manager
    base_manager = PostgreSQL
        project_id="my-project",
        namespace=f"tenant_{get_tenant_for_user(user_id)}"
    )

    # Wrap with privacy enhancements
    privacy_manager = PrivacyEnhancedMemoryManager(
        underlying_manager=base_manager,
        config=StorageConfig(
            environment="prod",
            enforce_privacy_classification=True
        )
    )

    await privacy_manager.initialize()

    # Create memory item
    item = MemoryItem(
        user_id=user_id,
        session_id=session_id,
        item_type="conversation",
        text_content=message,
        metadata={
            "source": "chat_interface",
            "retention_period": 90  # days
        }
    )

    # Store with automatic PII detection and classification
    await privacy_manager.add_memory_item(item)

    await privacy_manager.close()
```

## Conclusion

By implementing these separation strategies, the system ensures:

1. Development context is preserved for technical understanding without exposing it to production environments
2. Personal information is properly protected with privacy controls and data minimization
3. Both data types have appropriate access controls, retention policies, and validation
4. Deployment processes respect the separation and apply the correct configurations

This approach provides a robust foundation for maintaining development context while protecting personal information throughout the system lifecycle.
