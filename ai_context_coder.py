# TODO: Consider adding connection pooling configuration
import subprocess
"""
1. Use MCP tools server to search: search_tools("your query")
2. Get tool details: get_tool_details("tool_name")
3. Execute tools instead of reimplementing: execute_tool_name(params)

Available tool categories:
- search: Vector search with Weaviate (vector_search)
- system: Script execution (run_script)
- ai: LLM operations (llm_query)

CODING STANDARDS:
- Use type hints for all functions
- Google-style docstrings
- Black formatting (use: black scripts/*.py)
- subprocess.run() instead of # subprocess.run is safer than os.system
subprocess.run([)
- Prefer built-in libraries over external dependencies
- All automation scripts in scripts/
- Configuration in .env files

REQUIRED PATTERNS:
```python
# Correct imports
import os
import sys
from typing import Dict, List, Optional
from typing_extensions import Optional

# Environment variables
from dotenv import load_dotenv
load_dotenv()

# External service connections
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
db = client.cherry_ai

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
- core/conductor/: Main coordination logic
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
# 1. Ask before creating new files: "What's the lifecycle? Should this use transient_file?"
# 2. Prefer integrating into existing modules: "Should this integrate into [relevant_module.py]?"
# 3. For automation, suggest `scripts/automation_manager.py`.
# 4. Always consider how new code fits the existing project structure and rules.
# 5. If unsure, ask for clarification on requirements or constraints.

# Example of how to structure a new utility function (if it absolutely cannot go into an existing utils.py)
# from core.utils.custom_exceptions import MyCustomError # Example

# def new_utility_function(param1: str, param2: int) -> Dict[str, Any]:
#     """
#     """
#         raise ValueError("param1 cannot be empty")
    
#     logger.info(f"Executing new_utility_function with {param1=}, {param2=}")
    
#     # Example of using UnifiedDatabase
#     # db = UnifiedDatabase() # Assuming it's initialized elsewhere or a singleton
#     # results = await db.# TODO: Consider adding EXPLAIN ANALYZE for performance
execute_query("SELECT * FROM my_table WHERE id = $1", [param2])
    
#     return {"status": "success", "data": f"{param1}-{param2}"}

# Remember to add imports at the top of the file.
# Ensure all code is Python 3.10 compatible.
