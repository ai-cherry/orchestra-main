"""
AI CONTEXT: DEBUGGER MODE - Orchestra Project
============================================

READ THIS ENTIRE FILE BEFORE DEBUGGING!

Project: Orchestra AI (Python 3.11+, pip/venv, GCP-focused)
Role: You are debugging issues in this project

SYSTEM INFORMATION:
- Python 3.11.6 (minimum 3.11)
- OS: Linux 5.15.0-124-generic
- Shell: /bin/bash
- Workspace: /home/paperspace/orchestra-main

COMMON ISSUES AND SOLUTIONS:

1. PYTHON VERSION ERRORS
   SYMPTOM: `SyntaxError` on features introduced **after** Python 3.11 (e.g., hypothetical 3.12-only APIs)
   CAUSE: Code written for a newer Python release than the runtime (3.11)
   FIX: Either bump the runtime to the required version or replace those constructs with Python 3.11-compatible alternatives.
   ```python
   # Example: replace newer syntax with standard approaches
   ```

2. MODULE NOT FOUND
   SYMPTOM: ImportError or ModuleNotFoundError
   CHECK:
   ```bash
   pip list | grep module_name
   python -c "import sys; print(sys.path)"
   ls -la scripts/  # Is the module there?
   ```
   FIX:
   - Check requirements/base.txt
   - Ensure virtual environment is active
   - Add to PYTHONPATH if local module

3. SERVICE CONNECTION FAILURES
   SYMPTOM: Connection refused on ports 8002, 8080
   DEBUG:
   ```bash
   # Check if services are running
   python scripts/orchestra.py services status

   # Check specific ports
   netstat -tlnp | grep -E "8002|8080"
   lsof -i :8002

   # Check logs
   tail -f logs/mcp_*.log
   ```
   FIX:
   - Start services: make start-services
   - Wait for ready: make wait-for-mcp

4. SUBPROCESS FAILURES
   SYMPTOM: Command not found or shell errors
   DEBUG:
   ```python
   # Add debugging to subprocess calls
   result = subprocess.run(cmd, capture_output=True, text=True)
   print(f"Return code: {result.returncode}")
   print(f"STDOUT: {result.stdout}")
   print(f"STDERR: {result.stderr}")
   ```
   COMMON FIXES:
   - Use full paths for commands
   - Check command exists: which command_name
   - Ensure proper argument format (list not string)

5. PERMISSION ERRORS
   SYMPTOM: PermissionError or Access Denied
   DEBUG:
   ```bash
   ls -la file_or_directory
   whoami
   groups
   ```
   FIX:
   - Check file ownership
   - Ensure script has execute permission
   - Check GCP credentials: gcloud auth list

6. GCP/FIRESTORE ERRORS
   SYMPTOM: Authentication or permission failures
   DEBUG:
   ```bash
   # Check credentials
   echo $GOOGLE_APPLICATION_CREDENTIALS
   gcloud config get-value project

   # Test connection
   python -c "from google.cloud import firestore; db = firestore.Client(); print('Connected')"
   ```
   FIX:
   - Set credentials: export GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json
   - Check project: gcloud config set project cherry-ai-project

DEBUGGING TOOLS IN PROJECT:

1. HEALTH MONITOR (scripts/health_monitor.py)
   ```bash
   # Check all services
   python scripts/health_monitor.py --check-services

   # Monitor continuously
   python scripts/health_monitor.py --monitor

   # Check prerequisites
   python scripts/health_monitor.py --check-prereqs
   ```

2. CONFIG VALIDATOR (scripts/config_validator.py)
   ```bash
   # Validate all configs
   python scripts/config_validator.py --verbose

   # Check specific config
   python scripts/config_validator.py --config path/to/config.yaml
   ```

3. ORCHESTRA CLI (scripts/orchestra.py)
   ```bash
   # Service status
   python scripts/orchestra.py services status

   # Check logs
   python scripts/orchestra.py logs mcp_firestore
   ```

DEBUGGING WORKFLOW:

1. IDENTIFY THE ISSUE
   - Read the full error message
   - Note the file and line number
   - Check if it's a known pattern

2. GATHER INFORMATION
   ```bash
   # Check environment
   python --version
   pip list
   env | grep -E "GOOGLE|PYTHON|PATH"

   # Check services
   ps aux | grep python
   netstat -tlnp
   ```

3. ISOLATE THE PROBLEM
   - Create minimal reproduction
   - Test components individually
   - Use logging liberally

4. COMMON DEBUG ADDITIONS:
   ```python
   # Add to imports
   import logging
   logging.basicConfig(level=logging.DEBUG)

   # Add debug prints
   logger.debug(f"Variable state: {variable}")

   # Add try/except with details
   try:
       risky_operation()
   except Exception as e:
       logger.error(f"Failed at line {sys.exc_info()[2].tb_lineno}: {e}")
       raise
   ```

ERROR PATTERNS TO CHECK:

1. "No module named docker/poetry" → Remove these imports
2. "SyntaxError: invalid syntax" near match → Python 3.11+ feature
3. "Connection refused" → Service not running
4. "Permission denied" → Check file permissions or GCP auth
5. "Command not found" → Missing dependency or wrong PATH

QUICK FIXES:

```bash
# Reset environment
deactivate
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements/base.txt

# Validate setup
python scripts/check_venv.py
python scripts/check_dependencies.py

# Clean restart
make stop-services
make dev-start

# Check for anti-patterns
python scripts/ai_code_reviewer.py --check-file problematic_file.py
```

REMEMBER:
- Don't add Docker to fix issues
- Check existing tools first
- Simple solutions preferred
- Use subprocess.run() for system commands
- Logs are your friend
"""

# This file is meant to be read by AI when debugging
# Usage: Include this filename in your prompt when debugging
# Example: "Read ai_context_debugger.py and help debug this error"
