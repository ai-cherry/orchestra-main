"""
AI CONTEXT: CODER MODE - Orchestra Project (Vultr-Preferred Edition)
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

# Project Stack:
# - Python 3.10 (Strictly)
# - pip/venv for dependency management
# - PostgreSQL (Relational DB)
# - Weaviate (Vector DB)
# - Primary Cloud Provider: Vultr
# - Permitted Cloud Services: Vultr Compute, Vultr Block Storage, Weaviate Cloud, PostgreSQL (on Vultr or managed by a Vultr-compatible service)
# - Prohibited Cloud Services: GCP, AWS, Azure (unless specifically part of a defined, isolated integration for a 3rd party service that *only* runs on them and is approved)
# - External services: May include others if they are cloud-agnostic or run on Vultr.
# - Local development: docker-compose for service mocks only (e.g., local Weaviate, Postgres)
#
# CODING STANDARDS & RULES:
# 1. Python 3.10 ONLY: No `match/case`, no `tomllib`. Use `Union[X, Y]` not `X | Y`.
# 2. Dependencies: `pip/venv` only. Check `requirements/base.txt`. Avoid new heavy dependencies.
#    - NO Poetry, NO Pipenv.
# 3. Formatting: Black for formatting, isort for imports.
# 4. Type Hints: PEP 484 type hints for ALL functions and methods.
# 5. Docstrings: Google-style for all public modules, classes, functions.
# 6. Error Handling: Use specific exceptions, implement `try-except` blocks appropriately.
# 7. Database: Use `shared.database.UnifiedDatabase` for ALL PostgreSQL & Weaviate ops.
#    - All new PostgreSQL queries MUST include `EXPLAIN ANALYZE` output in PRs.
#    - DO NOT use MongoDB, Redis, DragonflyDB, or other databases.
# 8. Cloud Services: Prioritize Vultr. No direct GCP/AWS/Azure SDK usage unless specifically approved.
#    - Use `pulumi_vultr` for IaC if creating/managing Vultr resources.
# 9. Performance: Optimize algorithms, benchmark critical functions/loops (>1000 iterations).
#10. Simplicity: Solutions should be simple, stable, and directly maintainable.
#11. File Management: Use `core.utils.file_management.transient_file` for temp files.
#     All significant generated files must declare purpose and expiration/review date.
#12. Existing Patterns: Leverage existing project patterns before creating new ones.
#     Integrate into existing modules (`scripts/`, `core/`, `services/`, `shared/`).
#13. Subprocesses: Use `subprocess.run()` NOT `os.system()`.
#14. Logging: Use standard Python `logging` module, configure via central config if possible.
#
# FORBIDDEN:
# - ❌ Python 3.11+ features (match/case, tomllib, etc.)
# - ❌ Poetry, Pipenv, Conda
# - ❌ Direct GCP/AWS/Azure SDK usage (unless an explicit, approved exception for a 3rd party service)
# - ❌ MongoDB, Redis, DragonflyDB, or other non-approved databases
# - ❌ `os.system()`
# - ❌ Heavy external libraries for simple tasks
# - ❌ Standalone utility scripts (integrate into existing modules or `scripts/orchestra.py`)
# - ❌ Temporary files without `transient_file` decorator or `.cleanup_registry.json` entry
#
# REQUIRED PATTERNS:
# - ✅ `from shared.database import UnifiedDatabase` for DB ops.
# - ✅ `from core.utils.file_management import transient_file` for temp files.
# - ✅ Type hints for all functions: `def my_func(param: str) -> bool:`
# - ✅ Google-style docstrings.
# - ✅ Performance benchmarks for complex functions.
# - ✅ Integration with `scripts/orchestra.py` for new CLI commands.
# - ✅ Use of Vultr SDK (`pulumi_vultr`) for IaC for Vultr resources.
#
# AI BEHAVIOR:
# 1. Ask before creating new files: "What's the lifecycle? Should this use transient_file?"
# 2. Prefer integrating into existing modules: "Should this integrate into [relevant_module.py]?"
# 3. For automation, suggest `scripts/automation_manager.py`.
# 4. Always consider how new code fits the existing project structure and rules.
# 5. If unsure, ask for clarification on requirements or constraints.

# Example of how to structure a new utility function (if it absolutely cannot go into an existing utils.py)
# from core.utils.custom_exceptions import MyCustomError # Example

# def new_utility_function(param1: str, param2: int) -> Dict[str, Any]:
#     """Google-style docstring for the new utility function.

#     Args:
#         param1: Description of param1.
#         param2: Description of param2.

#     Returns:
#         A dictionary containing results.
    
#     Raises:
#         MyCustomError: If something goes wrong.
#     """
#     # Function logic here
#     if not param1:
#         raise ValueError("param1 cannot be empty")
    
#     logger.info(f"Executing new_utility_function with {param1=}, {param2=}")
    
#     # Example of using UnifiedDatabase
#     # db = UnifiedDatabase() # Assuming it's initialized elsewhere or a singleton
#     # results = await db.execute_query("SELECT * FROM my_table WHERE id = $1", [param2])
    
#     return {"status": "success", "data": f"{param1}-{param2}"}

# Remember to add imports at the top of the file.
# Ensure all code is Python 3.10 compatible.
