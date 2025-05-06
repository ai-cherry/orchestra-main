# Memory System V2 Migration Guide

This guide provides instructions for migrating the AI Orchestra memory system from V1 to V2 implementation.

## Overview

The AI Orchestra memory system has been enhanced with a new V2 implementation that offers several improvements:

- **Fully asynchronous operations** with proper connection pooling
- **Improved error handling and health monitoring**
- **Optimized semantic search** with vector operations
- **Enhanced batching capabilities** for better performance
- **Comprehensive telemetry** for monitoring and debugging

This guide will help you understand the changes and migrate your data from V1 to V2.

## Architecture Changes

### Memory Manager Factory

The `MemoryManager` class now acts as a factory that can create either V1 or V2 backend implementations based on configuration:

```python
memory_manager = MemoryManager(
    memory_backend_type="firestore_v2",  # Use V2 implementation
    project_id="cherry-ai-project",
    # Other configuration parameters...
)
```

### Async/Sync Interface

The V2 implementation is fully asynchronous, but synchronous wrappers are provided for backward compatibility:

```python
# Asynchronous usage
await memory_manager.initialize()
await memory_manager.add_memory_item(item)
await memory_manager.close()

# Synchronous usage (using wrappers)
memory_manager.initialize_sync()
memory_manager.add_memory_item_sync(item)
memory_manager.close_sync()
```

### Configuration

The memory backend type can be configured through environment variables:

```bash
# Use V1 implementation (default)
export MEMORY_BACKEND_TYPE=firestore_v1

# Use V2 implementation
export MEMORY_BACKEND_TYPE=firestore_v2
```

## Migration Process

### Step 1: Update Configuration

Update your environment configuration to use the V2 backend:

```bash
export MEMORY_BACKEND_TYPE=firestore_v2
```

### Step 2: Run the Migration Tool

Use the provided migration tool to migrate your data from V1 to V2:

```bash
# Dry run (no actual changes)
./scripts/migrate_memory_v1_to_v2.py --project-id cherry-ai-project --dry-run

# Actual migration
./scripts/migrate_memory_v1_to_v2.py --project-id cherry-ai-project

# With custom credentials
./scripts/migrate_memory_v1_to_v2.py --project-id cherry-ai-project --credentials-path /path/to/credentials.json

# With validation and output
./scripts/migrate_memory_v1_to_v2.py --project-id cherry-ai-project --output validation_results.json
```

### Step 3: Verify Migration

After running the migration tool, verify that your data has been successfully migrated:

1. Check the validation results (if you specified an output file)
2. Run your application with the V2 backend and verify functionality
3. Monitor for any errors or performance issues

## Migration Tool Options

The migration tool (`scripts/migrate_memory_v1_to_v2.py`) supports the following options:

- `--project-id`: (Required) Google Cloud project ID
- `--credentials-path`: Path to service account credentials file
- `--batch-size`: Number of items to process in each batch (default: 100)
- `--dry-run`: Don't actually write to the target (for testing)
- `--no-validate`: Skip validation
- `--sample-size`: Number of items to sample for validation (default: 10)
- `--output`: Path to write validation results to

## Rollback Procedure

If you encounter issues with the V2 implementation, you can roll back to V1:

1. Update your environment configuration:
   ```bash
   export MEMORY_BACKEND_TYPE=firestore_v1
   ```

2. Restart your application

## Troubleshooting

### Common Issues

1. **Async/Sync Mismatch**
   
   If you see errors related to async/sync operations, make sure you're using the appropriate methods:
   - Use async methods with `await` in async contexts
   - Use sync wrapper methods (with `_sync` suffix) in synchronous contexts

2. **Connection Issues**
   
   If you experience connection issues:
   - Check your credentials
   - Verify your project ID
   - Ensure Firestore is enabled in your GCP project

3. **Missing Data**
   
   If data appears to be missing after migration:
   - Run the migration tool with validation
   - Check the validation results for any mismatches or missing items
   - Run the migration tool again if needed

### Logging

The migration tool logs detailed information to both the console and a log file (`memory_migration.log`). Check these logs for any errors or warnings.

## Performance Considerations

The V2 implementation includes several performance optimizations:

- **Connection pooling**: Reuses connections for better performance
- **Batched operations**: Processes data in batches for efficiency
- **Optimized vector operations**: Uses NumPy when available for faster semantic search

Monitor your application's performance after migration to ensure these optimizations are working as expected.

## Future Enhancements

Future enhancements to the memory system may include:

- Integration with Vertex Vector Search for improved semantic search at scale
- Multi-tier memory architecture with Redis for short-term memory
- Automatic summarization and importance-based retention
- Event-driven memory updates using Pub/Sub

Stay tuned for updates!