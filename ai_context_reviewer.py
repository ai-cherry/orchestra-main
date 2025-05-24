"""
AI CONTEXT: REVIEWER MODE - Orchestra Project
=============================================

READ THIS ENTIRE FILE BEFORE REVIEWING ANY CODE!

Project: Orchestra AI (Python 3.11+, pip/venv, GCP-focused)
Role: You are reviewing code changes for compliance and quality

REVIEW CHECKLIST:

1. PYTHON VERSION COMPLIANCE
   ❌ FAIL: Using syntax/features that require **>3.11** (e.g., Python 3.12-only APIs)
   ✅ PASS: `match`/`case` statements where they improve clarity
   ✅ PASS: `tomllib` for TOML parsing where appropriate
   ✅ PASS: `ExceptionGroup`, `TaskGroup` usage where beneficial
   ⚠️  WARN: Overly complex `match`/`case` patterns that reduce readability

2. DEPENDENCY MANAGEMENT
   ❌ FAIL: from poetry import ...
   ❌ FAIL: import docker
   ❌ FAIL: Files: Dockerfile, docker-compose.yml, Pipfile, poetry.lock
   ✅ PASS: Using pip and requirements/base.txt
   ✅ PASS: Virtual environment with venv

3. SECURITY PATTERNS
   ❌ FAIL: os.system("any command")
   ❌ FAIL: subprocess.run(cmd, shell=True)
   ❌ FAIL: eval() or exec() usage
   ⚠️  WARN: subprocess with user input (needs validation)
   ✅ PASS: subprocess.run(["cmd", "arg"], capture_output=True)

4. CODE COMPLEXITY
   ❌ FAIL: Metaclasses for simple tasks
   ❌ FAIL: Multiple inheritance (except mixins)
   ❌ FAIL: Abstract base classes without clear need
   ⚠️  WARN: Classes with >10 methods
   ⚠️  WARN: Functions with >50 lines
   ✅ PASS: Simple, direct implementations

5. DUPLICATION CHECK
   Review against existing tools:
   - Config validation → scripts/config_validator.py exists!
   - Health monitoring → scripts/health_monitor.py exists!
   - CLI interface → scripts/orchestra.py exists!
   - Service management → Already in orchestra.py
   - Port 8002/8080 services → Already exist!

6. IMPORT STANDARDS
   ✅ CORRECT ORDER:
   ```python
   # Standard library
   import os
   import sys

   # Third-party
   import yaml

   # Google Cloud
   from google.cloud import firestore

   # Local
   from scripts.existing_tool import ExistingClass
   ```

7. TYPE HINTS
   ❌ FAIL: def process(data): # No type hints
   ⚠️  WARN: -> Any  # Too generic
   ✅ PASS: def process(data: str) -> Dict[str, str]:

8. ERROR HANDLING
   ❌ FAIL: except: # Bare except
   ❌ FAIL: except Exception: # Too broad without logging
   ✅ PASS: except SpecificError as e:
            logger.error(f"Failed: {e}")

9. FILE LOCATIONS
   ❌ FAIL: New directory without clear need
   ❌ FAIL: requirements-dev.txt (use requirements/dev.txt)
   ✅ PASS: scripts/new_tool.py for automation
   ✅ PASS: Reusing existing config directories

COMMON AI MISTAKES TO FLAG:

1. "Let's dockerize this" → NO! We use pip/venv
2. "I'll use Poetry for better dependency management" → NO!
3. "Here's a factory pattern with abstract base..." → Too complex!
4. "I'll create a new service on port 8080" → Already taken!
5. "Using pandas for this CSV operation" → Use csv module!

REVIEW COMMANDS TO RUN:
```bash
# Check for forbidden patterns
grep -n "os\.system\|shell=True" file.py
grep -n "docker\|poetry\|pipenv" file.py
grep -n "match.*:\|case.*:" file.py

# Check for duplication
diff -u <(grep "def " existing.py) <(grep "def " new.py)

# Validate Python 3.11 compatibility
python3.11 -m py_compile file.py

# Run our automated checker
python scripts/ai_code_reviewer.py --check-file file.py
```

GOOD REVIEW EXAMPLE:
"This code:
✅ Uses subprocess.run() correctly
✅ Has proper type hints
✅ Follows existing patterns from health_monitor.py
⚠️  Consider using ConfigValidator instead of reimplementing
❌ Remove the docker import on line 15
❌ Replace os.system() on line 42 with subprocess.run()"

BAD REVIEW EXAMPLE:
"Looks good!" (without checking for anti-patterns)

PERFORMANCE CONSIDERATIONS:
- Is this the simplest solution?
- Are we adding heavy dependencies?
- Could this use existing tools?
- Is the error handling graceful?

QUESTIONS TO ASK:
1. Does this duplicate existing functionality?
2. Is this following project patterns?
3. Will this work on Python 3.11?
4. Are all the imports necessary?
5. Could this be simpler?

APPROVE ONLY IF:
- No forbidden patterns detected
- No unnecessary duplication
- Follows project structure
- Works with Python 3.11
- Uses existing tools appropriately
- Has proper error handling
- Includes type hints
"""

# This file is meant to be read by AI when reviewing code
# Usage: Include this filename in your prompt when reviewing
# Example: "Read ai_context_reviewer.py and review these changes"
