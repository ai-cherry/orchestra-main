"""
AI CONTEXT: DEBUGGER MODE - Orchestra Project (GCP-Free Edition)
================================================================

READ THIS ENTIRE FILE BEFORE DEBUGGING!

Project: Orchestra AI (Python 3.10, pip/venv, External Services)
Role: You are debugging issues in this project.

ENVIRONMENT SETUP:
- Python 3.10 (check with: python --version)
- Virtual environment (venv) for dependencies
- External services: MongoDB, DragonflyDB, Weaviate
- Local development: docker-compose for service mocks only
- NO Poetry, Pipenv, or GCP dependencies

COMMON DEBUGGING STEPS:

1. CHECK PYTHON ENVIRONMENT:
   ```bash
   python --version  # Must be 3.10.x
   which python      # Should point to venv
   pip list          # Check installed packages
   ```

2. VERIFY VIRTUAL ENVIRONMENT:
   ```bash
   # Activate if not active
   source venv/bin/activate

   # Check it's activated
   echo $VIRTUAL_ENV

   # Reinstall dependencies if needed
   pip install -r requirements/base.txt
   ```

3. CHECK EXTERNAL SERVICES:
   ```bash
   # Test MongoDB connection
   python -c "import pymongo; print(pymongo.MongoClient('$MONGODB_URI').server_info())"

   # Test Redis/DragonflyDB
   python -c "import redis; r=redis.Redis(host='$REDIS_HOST'); print(r.ping())"

   # Check service status
   python scripts/orchestra_status.py
   ```

4. COMMON ISSUES & FIXES:

   **Import Errors:**
   - Ensure venv is activated
   - Run: pip install -r requirements/base.txt
   - Check for typos in import statements

   **Connection Errors:**
   - Check .env file exists and is loaded
   - Verify service URLs in environment
   - For local dev: docker-compose up -d

   **Python Version Issues:**
   - No match/case statements (3.10 doesn't support)
   - No tomllib (use tomli instead)
   - Use Union[X, Y] not X | Y for types

5. DEBUG COMMANDS:
   ```bash
   # Check for syntax errors
   python -m py_compile scripts/problematic_script.py

   # Run with verbose output
   python -v scripts/script.py

   # Check environment variables
   python -c "import os; print(os.environ.get('MONGODB_URI'))"

   # Test specific functions
   python -c "from scripts.module import function; function()"
   ```

6. SERVICE-SPECIFIC DEBUGGING:

   **MongoDB Issues:**
   ```python
   import pymongo
   import os

   # Debug connection
   uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
   print(f"Connecting to: {uri}")

   try:
       client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
       print(client.server_info())
   except Exception as e:
       print(f"Connection failed: {e}")
   ```

   **Redis/DragonflyDB Issues:**
   ```python
   import redis
   import os

   # Debug connection
   host = os.getenv("REDIS_HOST", "localhost")
   port = int(os.getenv("REDIS_PORT", "6379"))

   try:
       r = redis.Redis(host=host, port=port, socket_timeout=5)
       print(f"Ping response: {r.ping()}")
   except Exception as e:
       print(f"Redis error: {e}")
   ```

7. MCP SERVER DEBUGGING:
   ```bash
   # Check if MCP servers are running
   ps aux | grep -E "orchestrator_server|memory_server"

   # Start MCP servers manually
   python mcp_server/servers/orchestrator_server.py

   # Check MCP logs
   tail -f ~/.mcp/logs/*.log
   ```

FORBIDDEN DEBUGGING APPROACHES:
❌ Don't try to fix by adding Poetry/Pipenv
❌ Don't add GCP dependencies to solve issues
❌ Don't use Docker SDK for debugging
❌ Don't upgrade to Python 3.11+

DEBUGGING WORKFLOW:
1. Identify the error message
2. Check environment setup (venv, Python version)
3. Verify external service connections
4. Look for forbidden patterns
5. Test minimal reproduction
6. Fix using simple solutions

REMEMBER:
- Keep solutions simple
- Use built-in Python tools
- Check existing scripts in scripts/
- All fixes must work with Python 3.10

# This file is meant to be read by AI when debugging.
# Usage: Include this filename in your prompt when debugging.
# Example: "Read ai_context_debugger.py and help debug this error"
"""
