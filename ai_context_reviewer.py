"""
AI CONTEXT: REVIEWER MODE - Orchestra Project (Vultr-Preferred Edition)
================================================================

READ THIS ENTIRE FILE BEFORE REVIEWING ANY CODE!

Project: Orchestra AI (Python 3.10, pip/venv, External Services)
Role: You are reviewing code changes for compliance, quality, and stability.

Project Stack:
- Python 3.10 (Strictly)
- pip/venv for dependency management
- PostgreSQL (Relational DB)
- Weaviate (Vector DB)
- Primary Cloud Provider: Vultr
- Permitted Cloud Services: Vultr Compute, Vultr Block Storage, Weaviate Cloud, PostgreSQL (on Vultr or managed by a Vultr-compatible service)
- Prohibited Cloud Services: GCP, AWS, Azure (unless specifically part of a defined, isolated integration for a 3rd party service that *only* runs on them and is approved)
- External services: May include others if they are cloud-agnostic or run on Vultr.
- Local development: docker-compose for service mocks only (e.g., local Weaviate, Postgres)

REVIEW CHECKLIST:

1. ENVIRONMENT & DEPENDENCY COMPLIANCE
   ✅ Python 3.10 only (no 3.11+ features)
   ✅ pip/venv workflow (NO Poetry, Pipenv)
   ✅ External services properly configured (MongoDB, Redis, Weaviate)
   ✅ No GCP, AWS, or Azure specific dependencies or imports (unless part of an explicit, approved integration)
   ✅ No Docker SDK usage (docker-compose for services only)

2. CODE QUALITY & PATTERNS
   ✅ Type hints for all functions
   ✅ Google-style docstrings
   ✅ Black formatting applied
   ✅ subprocess.run() used (never os.system())
   ✅ Minimal external dependencies
   ✅ Scripts in scripts/ directory
   ✅ Configuration via .env files

3. PERFORMANCE & STABILITY
   ✅ Simple, direct implementations
   ✅ No unnecessary complexity
   ✅ Efficient use of external services
   ✅ Proper error handling
   ✅ Resource cleanup (close connections)

4. FORBIDDEN PATTERNS TO CHECK
   ❌ Poetry/Pipenv imports or config files
   ❌ Docker SDK usage
   ❌ GCP service imports
   ❌ Python 3.11+ syntax (match/case, tomllib)
   ❌ Complex metaclasses or multiple inheritance
   ❌ Hardcoded credentials (use env vars)

5. EXTERNAL SERVICE PATTERNS
   ✅ MongoDB connections use MONGODB_URI env var
   ✅ Redis connections use REDIS_HOST/PORT env vars
   ✅ Proper connection error handling
   ✅ Connection pooling where appropriate

REVIEW COMMANDS:
```bash
# Check Python version compatibility
python3.10 -m py_compile <file.py>

# Run anti-pattern checker
python scripts/ai_code_reviewer.py --check-file <file.py>

# Verify imports
grep -E "poetry|pipenv|google\.cloud|docker" <file.py>

# Check formatting
black --check <file.py>

# Run type checking
mypy <file.py>
```

APPROVAL CRITERIA:
- ✅ No forbidden patterns detected
- ✅ Follows pip/venv workflow
- ✅ Works with Python 3.10
- ✅ Uses external services correctly
- ✅ Has proper error handling
- ✅ Includes type hints
- ✅ Simple and maintainable

RED FLAGS:
- 🚩 Any Poetry/Pipenv references
- 🚩 GCP/AWS/Azure service imports or direct SDK usage (outside explicitly approved, isolated integrations)
- 🚩 Docker SDK usage (docker-compose for local service mocks is OK)
- 🚩 Python 3.11+ features
- 🚩 Missing type hints
- 🚩 Hardcoded service URLs/credentials
- 🚩 Complex inheritance patterns

GOOD EXAMPLE:
```python
import os
from typing import Optional
import pymongo
from dotenv import load_dotenv

load_dotenv()

def get_db_connection() -> Optional[pymongo.database.Database]:
    \"\"\"Get MongoDB connection.

    Returns:
        Database instance or None if connection fails
    \"\"\"
    try:
        client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
        return client.orchestra
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None
```

REMEMBER:
- Simplicity and stability are key
- External services > self-hosted
- pip/venv is the only way

# This file is meant to be read by AI when reviewing code.
# Usage: Include this filename in your prompt when reviewing.
# Example: "Read ai_context_reviewer.py and review these changes"
"""
