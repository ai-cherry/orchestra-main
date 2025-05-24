# AI Coding Standards & Consistency Guide

## 🎯 Core Development Principles

### **MUST FOLLOW - Non-Negotiable Rules**

1. **Simplicity Over Complexity**
   - ❌ NO Docker unless absolutely necessary
   - ❌ NO Poetry - use pip/venv
   - ✅ Use existing tools and patterns
   - ✅ Prefer Python's built-in libraries

2. **Performance & Stability First**
   - Optimize for speed and reliability
   - Simple > Secure (within reason)
   - Fast > Feature-rich
   - Stable > Cutting-edge

3. **Consistent Structure**
   - All Python scripts in `scripts/`
   - All configs in appropriate subdirectories
   - Use existing patterns from codebase

4. **Python Standards**
   - Python 3.10+ (not 3.11 due to system constraints)
   - Type hints for all new functions
   - Google-style docstrings
   - Black formatting

## 🚨 Common AI Tool Mistakes to Avoid

### **1. Dependency Sprawl**
```python
# ❌ AI often suggests:
import pandas as pd  # Don't add heavy deps for simple tasks
import docker       # We don't use Docker
from poetry import Poetry  # No Poetry!

# ✅ Instead use:
import csv          # Built-in for data handling
import subprocess   # For system commands
import json         # For data serialization
```

### **2. Over-Engineering**
```python
# ❌ AI loves complex patterns:
class AbstractFactoryMetaBuilder:  # Too complex!
    pass

# ✅ Keep it simple:
def build_thing(config):  # Simple function
    return Thing(**config)
```

### **3. Duplicate Functionality**
```python
# ❌ AI might create:
def validate_yaml_file():  # We already have this!
    pass

# ✅ Use existing:
from scripts.config_validator import ConfigValidator
```

### **4. Wrong Python Version**
```python
# ❌ AI assumes latest:
match value:  # Python 3.10+ only
    case "a": ...

# ✅ Use compatible:
if value == "a":  # Works on 3.10
    ...
```

## 📋 Pre-AI-Coding Checklist

Before using AI tools (Cursor, Copilot, etc.), run:

```bash
# 1. Check current state
python scripts/orchestra.py services status
python scripts/config_validator.py --verbose

# 2. Document what exists
find . -name "*.py" -path "./scripts/*" | head -20  # Check existing scripts
grep -r "def validate" --include="*.py"  # Find existing validators
grep -r "class.*Monitor" --include="*.py"  # Find existing monitors

# 3. Set AI context
# Tell the AI:
# - "We use Python 3.10, not 3.11"
# - "We use pip/venv, not Poetry/Docker"
# - "Check scripts/ directory for existing tools"
# - "Prefer subprocess.run() over os.system()"
# - "Use existing patterns from the codebase"
```

## 🛡️ Guardrails for AI Tools

### **1. MCP Server Guidelines**
- Port 8002: Secret Manager (don't duplicate)
- Port 8080: Firestore/Orchestrator (shared)
- Port 3000: Admin UI
- Check `mcp-servers/` before creating new ones

### **2. Configuration Files**
- `requirements/base.txt` - Core dependencies only
- `scripts/` - All automation tools
- `Makefile` - Build targets (check before adding)
- NO `poetry.lock`, `Pipfile`, `docker-compose.yml`

### **3. Import Patterns**
```python
# Standard imports first
import os
import sys
from typing import Dict, List

# Third-party imports
import yaml
import requests

# GCP imports
from google.cloud import firestore

# Local imports
from scripts.config_validator import ConfigValidator
```

## 🔍 Duplication Detection Commands

Run these before creating new functionality:

```bash
# Find existing health/monitoring code
grep -r "health" --include="*.py" | grep -E "(def|class)"

# Find existing validators
grep -r "validat" --include="*.py" | grep -E "(def|class)"

# Find existing CLI commands
grep -r "argparse\|click" --include="*.py"

# Find service management
grep -r "start.*service\|stop.*service" --include="*.py"

# Check for existing API endpoints
find . -path "*/api/*" -name "*.py" | xargs grep -l "route\|endpoint"
```

## 🤖 AI Tool Configuration

### **Cursor Settings**
Add to `.cursor/rules` or mention in every session:
```
Project uses:
- Python 3.10 (NOT 3.11+)
- pip/venv (NOT Poetry/Docker)
- subprocess.run() (NOT os.system)
- Existing tools in scripts/ directory
- Simple solutions over complex patterns
```

### **GitHub Copilot**
Create `.github/copilot-instructions.md`:
```markdown
This project prioritizes:
1. Simplicity over complexity
2. Performance over security
3. Using existing patterns
4. No Docker/Poetry
5. Python 3.10 compatibility
```

## 📊 Regular Maintenance Tasks

### **Weekly Checks**
```bash
# 1. Check for duplicates
make config-validate

# 2. Check for conflicts
git status
grep -r "TODO\|FIXME\|XXX" --include="*.py"

# 3. Check dependencies
pip list | wc -l  # Should stay under 100

# 4. Run pre-commit
make pre-commit-run
```

### **Before Major AI Sessions**
```bash
# Create a checkpoint
git add -A && git commit -m "checkpoint: before AI coding session"

# Document current state
python scripts/orchestra.py services status > pre-ai-status.txt
pip freeze > pre-ai-requirements.txt

# Run full validation
make validate
```

### **After AI Changes**
```bash
# Check what changed
git diff --name-only
git diff --stat

# Validate changes
python scripts/config_validator.py
python scripts/health_monitor.py --check-services

# Look for anti-patterns
grep -r "poetry\|docker\|pipenv" --include="*.py" --include="*.txt" --include="*.yml"
grep -r "os\.system" --include="*.py"  # Should use subprocess

# Check for version issues
grep -r "3\.11\|match.*case\|tomllib" --include="*.py"
```

## 🚦 Red Flags in AI-Generated Code

Watch for these warning signs:

1. **New dependency management files**
   - `Pipfile`, `poetry.lock`, `setup.cfg`, `pyproject.toml`
   
2. **Container files**
   - `Dockerfile`, `docker-compose.yml`, `.dockerignore`
   
3. **Complex patterns**
   - Abstract base classes for simple tasks
   - Metaclasses
   - Multiple inheritance
   - Overly generic solutions

4. **Version assumptions**
   - `match/case` statements (3.10+)
   - `tomllib` (3.11+)
   - `:=` walrus operator usage everywhere

5. **Duplicate services**
   - New monitoring when we have health_monitor.py
   - New validators when we have config_validator.py
   - New CLI tools when we have orchestra.py

## 📝 Documentation Standards

When AI generates documentation:

### **Good Documentation**
```python
def wait_for_service(self, service_name: str, timeout: int = 60) -> bool:
    """
    Wait for a service to become healthy.
    
    Args:
        service_name: Name of the service (e.g., 'mcp_firestore')
        timeout: Maximum seconds to wait
        
    Returns:
        True if service became healthy, False if timeout
    """
```

### **Bad Documentation**
```python
def wait_for_service(self, service_name: str, timeout: int = 60) -> bool:
    """Waits for the specified service to become healthy within the given timeout period using advanced monitoring techniques and sophisticated algorithms."""  # Too verbose!
```

## 🔧 Quick Fixes for Common AI Mistakes

```bash
# Fix import sorting
isort scripts/*.py

# Fix formatting
black scripts/*.py

# Remove unused imports
autoflake --remove-all-unused-imports -i scripts/*.py

# Check for Python 3.11+ features
python -m py_compile scripts/*.py  # Will fail on syntax errors

# Find and review os.system usage
grep -n "os\.system" scripts/*.py

# Check for duplicate functionality
diff -u <(grep "def " scripts/health_monitor.py | sort) <(grep "def " scripts/new_ai_file.py | sort)
```

## 🎯 Final Checklist

Before committing AI-generated code:

- [ ] No new dependency management tools (Poetry, Pipenv)
- [ ] No Docker/container files
- [ ] No Python 3.11+ only features
- [ ] Uses existing patterns from scripts/
- [ ] Follows naming conventions
- [ ] Has proper type hints
- [ ] Passes `make validate`
- [ ] No duplicate functionality
- [ ] Simple solution, not over-engineered
- [ ] Uses subprocess.run(), not os.system()

---

**Remember: When in doubt, check what already exists in `scripts/` before creating new tools!** 