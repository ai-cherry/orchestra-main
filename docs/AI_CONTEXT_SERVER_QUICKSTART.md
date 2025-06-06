# AI Context Server Quick Start Guide

## What You've Built

You now have a **next-generation AI collaboration platform** that provides:

1. **Real-time codebase synchronization** - All connected AIs see changes instantly
2. **Rich contextual awareness** - File relationships, dependencies, git history
3. **Semantic search** - AI-optimized code search via Weaviate
4. **Universal compatibility** - Works with ANY AI assistant

## Quick Start

### 1. Start the Enhanced Context Server

```bash
# Replace the basic bridge with the context server
docker-compose -f docker-compose.production.yml --env-file .env.production up -d ai_context_server
```

### 2. Connect Any AI

```python
# Example: Connect any AI assistant
import websockets
import json

async def connect_to_context_server():
    ws = await websockets.connect("wss://cherry-ai.me/context/ws")
    
    # Authenticate with capabilities
    await ws.send(json.dumps({
        "ai_name": "MyAI",
        "api_key": "claude-key-2024",  # or any valid key
        "capabilities": ["code_analysis", "refactoring", "testing"]
    }))
    
    # Receive rich context
    welcome = json.loads(await ws.recv())
    print(f"Connected! Codebase has {welcome['codebase']['files']} files")
    
    # Get a file with full context
    await ws.send(json.dumps({
        "type": "get_file",
        "path": "services/ai_bridge.py"
    }))
    
    file_data = json.loads(await ws.recv())
    # Returns: content, imports, exports, dependencies, tests, git history!
```

## Key Features for AI Assistants

### 1. Real-Time File Monitoring
```python
# Subscribe to file changes
await ws.send(json.dumps({
    "type": "subscribe",
    "paths": ["services/*.py", "api/*.py"]  # or ["*"] for all
}))

# Receive instant updates when files change
# {"type": "file_changed", "path": "...", "context": {...}}
```

### 2. Intelligent Context Retrieval
```python
# Get smart context for current work
await ws.send(json.dumps({
    "type": "get_context",
    "current_file": "api/main.py",
    "context_type": "dependencies"
}))

# Returns related files, imports, tests, etc.
```

### 3. Semantic Code Search
```python
# Search across entire codebase
await ws.send(json.dumps({
    "type": "search",
    "query": "WebSocket authentication",
    "search_type": "semantic"  # or "keyword"
}))
```

### 4. Multi-AI Collaboration
```python
# Broadcast to other AIs
await ws.send(json.dumps({
    "type": "broadcast",
    "message": "Working on authentication module",
    "data": {"files": ["auth.py"], "action": "refactoring"}
}))
```

## Access Levels

- **Observer**: Read-only access, perfect for monitoring AIs
- **Contributor**: Read-write access, can modify files
- **Admin**: Full access including system commands

## Performance Benefits

1. **Cached Context**: Files are pre-analyzed and cached
2. **Dependency Graphs**: Instant relationship mapping
3. **Redis Pub/Sub**: Real-time updates with minimal latency
4. **Vector Embeddings**: Fast semantic search via Weaviate

## Integration Examples

### For Manus AI
```python
# Manus can now:
- Get any file with full context instantly
- See real-time changes from other AIs
- Search semantically across the codebase
- Understand file relationships automatically
```

### For Cursor/VS Code
```typescript
// VS Code extension can:
- Show AI suggestions in real-time
- Display which AI is working on what
- Provide context-aware completions
- Coordinate multi-AI workflows
```

### For Claude/GPT-4
```python
# Any AI can connect and:
- Access the full codebase context
- Subscribe to relevant file changes
- Collaborate with other AIs
- Execute code in sandboxed environment
```

## Deployment Options

### Local Testing (ngrok)
```bash
# Expose locally for external AIs
./expose_bridge_ngrok.sh
# Share the ngrok URL with any AI
```

### Production (Lambda Labs)
```yaml
# Optimized for performance
- GPU acceleration for embeddings
- NVMe storage for fast file access
- Redis cluster for scalability
- Multiple replicas for reliability
```

## Next Steps

1. **Test with ngrok**: Get Manus AI connected immediately
2. **Add more AIs**: Connect Claude, GPT-4, or any other AI
3. **Enable semantic search**: Fully integrate Weaviate
4. **Deploy to cloud**: Scale to production on Lambda Labs

## Why This Matters

Traditional AI assistants work in isolation with limited context. Your AI Context Server creates a **shared intelligence layer** where:

- Every AI has full codebase awareness
- Changes propagate instantly to all AIs
- Context is rich and interconnected
- Collaboration happens naturally

This transforms AI coding from isolated assistance to **true collaborative intelligence**.

---

**Ready to revolutionize AI collaboration? Start with ngrok testing today!** 