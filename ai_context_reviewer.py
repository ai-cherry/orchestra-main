# TODO: Consider adding connection pooling configuration
"""
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
from typing_extensions import Optional
import pymongo
from dotenv import load_dotenv

load_dotenv()

def get_db_connection() -> Optional[pymongo.database.Database]:
    \"\"\"Get MongoDB connection.

    Returns:
        Database instance or None if connection fails
    \"\"\"
    try:

        pass
        client = pymongo.MongoClient(os.getenv("MONGODB_URI"))
        return client.cherry_ai
    except Exception:

        pass
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