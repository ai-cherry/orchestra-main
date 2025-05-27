# Vector Search Integration Guide

This guide explains how to use the new vector search capabilities in the AI Orchestra project. It covers configuration, usage, and migration of existing embeddings.

## Overview

The AI Orchestra project now supports pluggable vector search backends for semantic search operations. This allows for more efficient and scalable semantic search, especially for large datasets.

Two vector search backends are currently supported:

1. **In-Memory Vector Search**: A simple in-memory implementation suitable for development and testing.
2. **## Configuration

### MongoDB

The `MongoDB

```python
from packages.shared.src.storage.MongoDB

# Using in-memory vector search (default)
memory_manager = MongoDB
    project_id="your-project-id",
    namespace="your-namespace",
    vector_search_provider="in_memory"
)

# Using memory_manager = MongoDB
    project_id="your-project-id",
    namespace="your-namespace",
    vector_search_provider="vertex",
    vector_search_config={
        "project_id": "your-project-id",
        "location": "us-west4",
        "index_endpoint_id": "your-index-endpoint-id",
        "index_id": "your-index-id"
    }
)

# Initialize the memory manager
await memory_manager.initialize()
```

### Vector Search Factory

You can also use the `VectorSearchFactory` directly to create vector search instances:

```python
from packages.shared.src.storage.vector.factory import VectorSearchFactory

# Create in-memory vector search
in_memory_search = VectorSearchFactory.create_vector_search(
    provider="in_memory",
    config={"dimensions": 768}
)

# Create vertex_search = VectorSearchFactory.create_vector_search(
    provider="vertex",
    config={
        "project_id": "your-project-id",
        "location": "us-west4",
        "index_endpoint_id": "your-index-endpoint-id",
        "index_id": "your-index-id"
    }
)

# Initialize the vector search
await in_memory_search.initialize()
```

## Usage

### Storing Embeddings

Embeddings are automatically stored in the configured vector search backend when adding memory items with embeddings:

```python
from packages.shared.src.models.base_models import MemoryItem

# Create a memory item with embedding
memory_item = MemoryItem(
    user_id="user123",
    text_content="This is a test memory item",
    embedding=[0.1, 0.2, 0.3, ...]  # Your embedding vector
)

# Add the memory item
item_id = await memory_manager.add_memory_item(memory_item)
```

### Semantic Search

Semantic search now uses the configured vector search backend:

```python
# Perform semantic search
results = await memory_manager.semantic_search(
    user_id="user123",
    query_embedding=[0.1, 0.2, 0.3, ...],  # Your query embedding vector
    top_k=5
)

# Process results
for item in results:
    print(f"ID: {item.id}, Content: {item.text_content}")
```

## Migration

To migrate existing embeddings from MongoDB

```bash
# Migrate to in-memory vector search (for testing)
python scripts/migrate_embeddings_to_vector_search.py --namespace your-namespace --provider in_memory

# Migrate to python scripts/migrate_embeddings_to_vector_search.py \
    --namespace your-namespace \
    --provider vertex \
    --project-id your-project-id \
    --location us-west4 \
    --index-endpoint-id your-index-endpoint-id \
    --index-id your-index-id
```

### Migration Options

The migration script supports the following options:

- `--batch-size`: Number of embeddings to process in each batch (default: 100)
- `--namespace`: Namespace to migrate (default: "default")
- `--provider`: Vector search provider to use (default: "in_memory")
- `--dry-run`: Run without making changes

For
- `--project-id`: - `--location`: - `--index-endpoint-id`: Vector Search index endpoint ID
- `--index-id`: Vector Search index ID

## Setting Up
To use
1. **Create an Index**:

```bash
gcloud ai indexes create \
    --project=your-project-id \
    --region=us-west4 \
    --display-name=memory-embeddings \
    --dimensions=768 \
    --distance-measure-type=COSINE \
    --metadata-schema=user_id:string,persona:string,namespace:string
```

2. **Create an Index Endpoint**:

```bash
gcloud ai index-endpoints create \
    --project=your-project-id \
    --region=us-west4 \
    --display-name=memory-embeddings-endpoint
```

3. **Deploy the Index to the Endpoint**:

```bash
gcloud ai index-endpoints deploy-index \
    --project=your-project-id \
    --region=us-west4 \
    --index-endpoint=your-index-endpoint-id \
    --index=your-index-id \
    --deployed-index-id=memory-embeddings-deployed
```

## Performance Considerations

- **In-Memory Vector Search**: Suitable for small datasets (up to a few thousand embeddings). All embeddings are loaded into memory, which can be memory-intensive for large datasets.

- **
- **Batch Operations**: When adding multiple memory items with embeddings, consider using batch operations to reduce the number of API calls.

- **Connection Pooling**: The system uses connection pooling for both MongoDB

## Troubleshooting

### Vector Search Not Available

If vector search is not available, the system will fall back to the original implementation using MongoDB

```
Vector search not available, falling back to direct MongoDB
```

### Migration Failures

If migration fails, check the logs for error messages. Common issues include:

- Invalid credentials or permissions
- Invalid index or index endpoint IDs
- Network connectivity issues

You can run the migration script with the `--dry-run` option to test the migration without making changes.

## Next Steps

- **Hybrid Search**: Combining vector search with keyword search for better results
- **Vector Search Caching**: Caching vector search results for improved performance
- **Custom Embedding Models**: Supporting custom embedding models for different use cases
