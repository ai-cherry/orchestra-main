"""
AI CONTEXT: CODER MODE - Orchestra Project
==========================================

READ THIS ENTIRE FILE BEFORE WRITING ANY CODE!

Project: Orchestra AI (Python 3.10, pip/venv, GCP-focused)
Role: You are implementing code for this project

ENVIRONMENT CONSTRAINTS:
- Python 3.10.12 (NOT 3.11+)
- Ubuntu Linux 5.15.0
- pip/venv for dependencies
- GCP project: cherry-ai-project

CODE PATTERNS TO FOLLOW:

1. FILE STRUCTURE:
```python
#!/usr/bin/env python3
'''
Short description of what this does.

Detailed description here.

Usage:
    python scripts/scriptname.py --option value
'''

import os
import sys
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
```

2. SUBPROCESS USAGE (SECURE):
```python
# ✅ CORRECT - Use argument lists
result = subprocess.run(
    ["git", "status", "--porcelain"],
    capture_output=True,
    text=True,
    timeout=30
)

# ❌ WRONG - Never use these
os.system("git status")  # FORBIDDEN
subprocess.run("git status", shell=True)  # FORBIDDEN
```

3. ERROR HANDLING:
```python
try:
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    if result.returncode != 0:
        logger.error(f"Command failed: {result.stderr}")
        return False
except subprocess.TimeoutExpired:
    logger.error("Command timed out")
    return False
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return False
```

4. CLASS STRUCTURE (SIMPLE):
```python
class MyTool:
    '''Simple tool class.'''

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def process(self, data: str) -> Dict[str, Any]:
        '''Process data and return results.'''
        # Simple, direct implementation
        return {"status": "success", "result": data}
```

5. TYPE HINTS (REQUIRED):
```python
def process_data(
    input_file: str,
    options: Dict[str, Any],
    timeout: int = 60
) -> Dict[str, Any]:
    '''
    Process data from file.

    Args:
        input_file: Path to input file
        options: Processing options
        timeout: Maximum time in seconds

    Returns:
        Dictionary with status and results
    '''
```

IMPORT ORDER:
```python
# Standard library
import os
import sys
from typing import Dict, List

# Third-party
import yaml
import requests
from google.cloud import firestore

# Local - use existing tools!
from scripts.config_validator import ConfigValidator
from scripts.health_monitor import HealthMonitor
```

EXISTING TOOLS TO REUSE:
- ConfigValidator: from scripts.config_validator import ConfigValidator
- HealthMonitor: from scripts.health_monitor import HealthMonitor
- OrchestaCLI: from scripts.orchestra import OrchestaCLI
- Notifications: See admin-ui/src/api/notifications.js pattern

FORBIDDEN PATTERNS:
❌ class AbstractBaseFactory(ABC, metaclass=Meta)  # Too complex
❌ from docker import ...  # No Docker
❌ import poetry  # No Poetry
❌ match/case statements  # Python 3.11+
❌ := walrus operator everywhere  # Keep it simple
❌ Multiple inheritance
❌ Metaclasses

GOOD CODE EXAMPLE:
```python
def check_service_health(service_name: str, port: int) -> bool:
    '''Check if service is healthy.'''
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            return s.connect_ex(('localhost', port)) == 0
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
```

FILE LOCATIONS:
- New scripts: scripts/your_script.py
- Config files: appropriate config directory
- NO new directories without discussion
- NO requirements-*.txt (use requirements/base.txt)

DEPENDENCIES:
- Check requirements/base.txt before adding
- Prefer built-in libraries
- No heavy dependencies for simple tasks
- If you need pandas for CSV, use csv module instead

TESTING YOUR CODE:
```bash
# Validate syntax
python -m py_compile scripts/your_script.py

# Check for anti-patterns
python scripts/ai_code_reviewer.py --check-file scripts/your_script.py

# Format code
black scripts/your_script.py
```

REMEMBER:
- Simple > Complex
- Existing tools > New tools
- subprocess.run() > os.system()
- Type hints on all functions
- Google docstrings
- Check scripts/ first!
"""

# This file is meant to be read by AI when coding
# Usage: Include this filename in your prompt when coding
# Example: "Read ai_context_coder.py and implement function X"
