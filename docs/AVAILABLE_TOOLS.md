# Available Tools

## Ai Tools

### llm_query

**Description**: Query an LLM for analysis, generation, or decision-making

**When to use**: For complex analysis, content generation, or decision-making requiring AI

**Parameters**:
- `prompt` (string, required): The prompt/question for the LLM
- `model` (string, optional): Model to use (default: gpt-4)
- `temperature` (float, optional): Temperature for randomness (default: 0.7)

**Examples**:
```python
llm_query("Analyze this error and suggest fixes: {error}")
llm_query("Generate unit tests for this function", model="gpt-4", temperature=0.2)
```

**Constraints**: Costs vary by model; be mindful of token usage

**Cost**: high

**Related tools**: llm_stream, llm_embed

---

## Cache Tools

### cache_get

**Description**: Get value from Redis/DragonflyDB cache

**When to use**: For fast retrieval of frequently accessed data, session data, or temporary values

**Parameters**:
- `key` (string, required): Cache key to retrieve

**Examples**:
```python
cache_get("user:123:preferences")
cache_get("api:rate_limit:client_xyz")
```

**Constraints**: Data may expire; always handle None returns

**Cost**: low

**Related tools**: cache_set, cache_delete

---

### cache_set

**Description**: Set value in Redis/DragonflyDB cache

**When to use**: To cache frequently accessed data, API responses, or computation results

**Parameters**:
- `key` (string, required): Cache key
- `value` (string, required): Value to cache
- `ttl` (integer, optional): Time to live in seconds (default: 3600)

**Constraints**: Keep TTL appropriate to data freshness needs

**Cost**: low

**Related tools**: cache_get, cache_delete

---

## Database Tools

### mongodb_query

**Description**: Query MongoDB for agent memories and persistent data

**When to use**: When you need to retrieve stored agent memories, user data, or perform complex queries

**Parameters**:
- `collection` (string, required): MongoDB collection name
- `query` (object, required): MongoDB query object
- `projection` (object, optional): Fields to include/exclude (default: {})
- `limit` (integer, optional): Maximum number of results (default: 10)
- `sort` (object, optional): Sort criteria (default: {})

**Examples**:
```python
mongodb_query("memories", {"agent_id": "coder"}, limit=5)
mongodb_query("users", {"active": true}, projection={"name": 1})
```

**Constraints**: Queries should use indexes when possible; avoid full collection scans

**Cost**: medium

**Related tools**: cache_get, mongodb_aggregate

---

## Search Tools

### vector_search

**Description**: Semantic search using Weaviate vector database

**When to use**: For semantic/similarity search, finding related content, or AI-powered search

**Parameters**:
- `query` (string, required): Natural language search query
- `collection` (string, required): Weaviate collection to search
- `limit` (integer, optional): Maximum results (default: 5)

**Examples**:
```python
vector_search("how to deploy to cloud", "documentation", limit=3)
vector_search("error handling patterns", "code_examples")
```

**Constraints**: Requires text to be pre-indexed with embeddings

**Cost**: medium

**Related tools**: mongodb_query, text_embedding

---

## System Tools

### run_script

**Description**: Execute a Python script from the scripts/ directory

**When to use**: To run automation scripts, validators, or system checks

**Parameters**:
- `script_name` (string, required): Script filename (without path)
- `args` (list, optional): Command line arguments (default: [])

**Examples**:
```python
run_script("cherry_ai_status.py")
run_script("ai_code_reviewer.py", ["--check-file", "main.py"])
```

**Constraints**: Only scripts in scripts/ directory; runs with current environment

**Cost**: low

**Related tools**: shell_command, python_eval

---
