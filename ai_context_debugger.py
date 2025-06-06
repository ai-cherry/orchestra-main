# TODO: Consider adding connection pooling configuration
"""
   python -c "
   python -c "import redis; r=redis.Redis(host='$REDIS_HOST'); print(r.ping())"

   # Check service status
   python scripts/cherry_ai_status.py
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
   python -c "
   # Test specific functions
   python -c "from scripts.module import function; function()"
   ```

6. SERVICE-SPECIFIC DEBUGGING:

   ```python
      import os

   # Debug connection
   print(f"Connecting to: {uri}")

   try:


       pass
       print(client.server_info())
   except Exception:

       pass
       print(f"Connection failed: {e}")
   ```

   ```python
   import redis
   import os

   # Debug connection
   host = os.getenv("REDIS_HOST", "localhost")
   port = int(os.getenv("REDIS_PORT", "6379"))

   try:


       pass
       r = redis.Redis(host=host, port=port, socket_timeout=5)
       print(f"Ping response: {r.ping()}")
   except Exception:

       pass
       print(f"Redis error: {e}")
   ```

7. MCP SERVER DEBUGGING:
   ```bash
   # Check if MCP servers are running
   ps aux | grep -E "conductor_server|memory_server"

   # Start MCP servers manually
   python mcp_server/servers/conductor_server.py

   # Check MCP logs
   tail -f ~/.mcp/logs/*.log
   ```

FORBIDDEN DEBUGGING APPROACHES:
❌ Don't try to fix by adding Poetry/Pipenv
❌ Don't add GCP/AWS/Azure dependencies to solve issues
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

✅ Lambda CLI commands (`Lambda-cli`)
✅ Pulumi with Python for Lambda IaC
"""