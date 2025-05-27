"""
AI CONTEXT: CODER MODE - Orchestra Project (GCP-Free Edition)
==============================================================

READ THIS ENTIRE FILE BEFORE WRITING ANY CODE!

Project: Orchestra AI (Python 3.10, pip/venv, External Services)
Role: You are implementing code for this project.

ENVIRONMENT CONSTRAINTS:
- Python 3.10 ONLY (not 3.11+, system constraint)
- pip/venv for ALL Python dependencies
- NO Poetry, Pipenv, or other dependency managers
- External managed services (MongoDB, DragonflyDB, Weaviate)
- Local development uses docker-compose for services only
- Simple, direct implementations preferred

TOOL AWARENESS:
Before implementing any functionality, check if tools already exist:
1. Use MCP tools server to search: search_tools("your query")
2. Get tool details: get_tool_details("tool_name")
3. Execute tools instead of reimplementing: execute_tool_name(params)

Available tool categories:
- cache: Redis/DragonflyDB operations (cache_get, cache_set, cache_delete)
- database: MongoDB operations (mongodb_query, mongodb_aggregate)
- search: Vector search with Weaviate (vector_search)
- system: Script execution (run_script)
- ai: LLM operations (llm_query)

CODING STANDARDS:
- Use type hints for all functions
- Google-style docstrings
- Black formatting (use: black scripts/*.py)
- subprocess.run() instead of os.system()
- Prefer built-in libraries over external dependencies
- All automation scripts in scripts/
- Configuration in .env files

REQUIRED PATTERNS:
```python
# Correct imports
import os
import sys
from typing import Dict, List, Optional

# Environment variables
from dotenv import load_dotenv
load_dotenv()

# External service connections
import pymongo  # MongoDB
import redis    # DragonflyDB
import weaviate # Vector search

# Type hints always
def process_data(data: Dict[str, Any]) -> List[str]:
    \"\"\"Process input data.

    Args:
        data: Input dictionary

    Returns:
        List of processed items
    \"\"\"
    return [str(v) for v in data.values()]
```

FORBIDDEN PATTERNS:
```python
# ❌ NO Poetry imports
from poetry import ...  # NEVER

# ❌ NO Docker SDK
import docker  # NEVER

# ❌ NO GCP imports

# ❌ NO Python 3.11+ features
match value:  # NO match/case
    case "a": ...

# ❌ NO complex dependency management
import pipenv  # NEVER
```

EXTERNAL SERVICES CONFIG:
```python
# MongoDB connection
client = pymongo.MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client.orchestra

# Redis/DragonflyDB connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True
)

# Weaviate connection (optional)
weaviate_client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL", "http://localhost:8080")
)
```

TESTING YOUR CODE:
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements/base.txt

# Validate syntax
python -m py_compile scripts/your_script.py

# Check for anti-patterns
python scripts/ai_code_reviewer.py --check-file scripts/your_script.py

# Format code
black scripts/your_script.py

# Run tests
python -m pytest tests/
```

PROJECT STRUCTURE:
- scripts/: All automation tools
- core/orchestrator/: Main orchestration logic
- mcp_server/: MCP server implementations
- requirements/: Dependency files (base.txt, dev.txt)
- .env: Environment configuration

REMEMBER:
- Check for existing tools before implementing
- Simple > Complex
- Built-in > External dependencies
- Performance > Security (within reason)
- Use existing tools from scripts/
- All code must work with Python 3.10

# This file is meant to be read by AI when coding.
# Usage: Include this filename in your prompt when coding.
# Example: "Read ai_context_coder.py and implement function X"
"""
