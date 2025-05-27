# Manual GCP Cleanup Guide

## Overview
This guide provides instructions for manually cleaning up the remaining GCP references in the Orchestra AI codebase. The automated cleanup scripts have limitations and can introduce syntax errors, so manual cleanup is recommended for critical files.

## Files Requiring Manual Cleanup

### 1. Core Configuration Files
- **core/orchestrator/src/config/secret_manager.py**
  - Remove GCP Secret Manager integration
  - Replace with environment variable access only
  - Keep the `get_secret()` function but remove `_get_from_secret_manager()`

### 2. Memory Management Files
- **core/orchestrator/src/agents/memory/manager.py**
  - Remove Firestore imports and references
  - Replace with MongoDB implementation
  - Update class names from `FirestoreMemoryManager` to `MongoDBMemoryManager`

- **core/orchestrator/src/memory/factory.py**
  - Remove Firestore backend creation
  - Update to use MongoDB as default

- **shared/memory/unified_memory.py**
  - Remove Firestore memory backend
  - Update imports and class references

### 3. Vertex AI Files
- **shared/vertex_ai/bridge.py**
  - This entire directory can potentially be removed if not using Vertex AI
  - Or replace with OpenAI/other LLM provider implementations

- **packages/vertex_client/**
  - Consider removing this entire package if not needed
  - Or refactor to work with non-GCP LLM providers

### 4. Infrastructure Files
- **infra/components/database_component.py**
  - Remove Cloud SQL references
  - Update to use external database providers

### 5. Scripts Requiring Updates
- **scripts/migrate_all_secrets_to_pulumi.py**
  - Remove GCP Secret Manager migration logic
  - Update to work with environment variables or other secret stores

## Replacement Strategy

### GCP Service → Replacement
1. **Firestore → MongoDB Atlas**
   - Replace `from google.cloud import firestore` with MongoDB client
   - Update collection/document operations to MongoDB syntax

2. **Secret Manager → Environment Variables**
   - Replace `secretmanager.SecretManagerServiceClient()` with `os.environ`
   - Use `.env` file for local development

3. **Vertex AI → OpenAI/OpenRouter**
   - Replace `import vertexai` with appropriate LLM client
   - Update model initialization and API calls

4. **Cloud Tasks → Celery/Redis Queue**
   - Replace `from google.cloud import tasks_v2` with task queue library
   - Update task creation and execution logic

5. **Cloud Storage → S3/Local Storage**
   - Replace `from google.cloud import storage` with boto3 or filesystem
   - Update bucket/blob operations

## Testing After Cleanup

1. **Run linting**:
   ```bash
   black . && flake8
   ```

2. **Run tests**:
   ```bash
   pytest tests/
   ```

3. **Start the system**:
   ```bash
   ./start_orchestra.sh
   ```

4. **Check MCP servers**:
   ```bash
   ./check_mcp_servers.sh
   ```

## Common Pitfalls to Avoid

1. **Don't blindly replace strings** - The context matters
2. **Check imports** - Ensure replacement libraries are imported
3. **Update type hints** - Change GCP-specific types to generic ones
4. **Test incrementally** - Clean and test one module at a time
5. **Keep backups** - Use git to track changes carefully

## Final Verification

After cleanup, run:
```bash
# Check for remaining GCP references
grep -r "google-cloud\|firestore\|vertex\|secret_manager" . \
  --exclude-dir=.git \
  --exclude-dir=venv \
  --exclude-dir=.mypy_cache \
  --include="*.py"
```

The output should be empty or only show legitimate references (like in documentation or comments).
