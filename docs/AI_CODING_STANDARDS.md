# AI Coding Standards & Consistency Guide

## 🎯 Core Development Principles

### **MUST FOLLOW - Non-Negotiable Rules**

1. **Simplicity Over Complexity**

   - ✅ All development and deployment must use Docker Compose v2 and Poetry for Python dependency management.
   - ✅ Python 3.10+ is required for all services and scripts.
   - ✅ Use existing tools and patterns from the codebase.
   - ✅ Prefer Python's built-in libraries and minimal dependencies.

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
   - Python 3.10+ (standardized across all environments and CI)
   - Type hints for all new functions
   - Google-style docstrings
   - Black formatting

## 🚀 NEW: AI Context Files System

We now have specialized AI context files for each development phase:

### **Quick Start - Just Copy & Paste**

- **Planning**: `Read ai_context_planner.py`
- **Coding**: `Read ai_context_coder.py`
- **Reviewing**: `Read ai_context_reviewer.py`
- **Debugging**: `Read ai_context_debugger.py`

See `AI_CONTEXT_FILES.md` for detailed usage examples.

## 🚨 Common AI Tool Mistakes to Avoid

### **1. Dependency Sprawl**

```python
# ❌ AI often suggests:
import pandas as pd  # Don't add heavy deps for simple tasks

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

Before using AI tools (Cursor, Copilot, etc.):

### **Step 1: Use the Right Context File**

```bash
# For planning new features
"Read ai_context_planner.py and help me plan..."

# For writing code
"Read ai_context_coder.py and implement..."

# For reviewing changes
"Read ai_context_reviewer.py and review..."

# For debugging issues
"Read ai_context_debugger.py and debug..."
```

### **Step 2: Check Current State**

```bash
# Check current state
python scripts/orchestra.py services status
python scripts/config_validator.py --verbose

# Document what exists
find . -name "*.py" -path "./scripts/*" | head -20  # Check existing scripts
grep -r "def validate" --include="*.py"  # Find existing validators
grep -r "class.*Monitor" --include="*.py"  # Find existing monitors
```

### **Step 3: Create Checkpoint**

```bash
make before-ai-coding  # Creates git checkpoint and documents state
```

## 🛡️ Guardrails for AI Tools

### **1. MCP Server Guidelines**

- Port 8002: Secret Manager (don't duplicate)
- Port 8080: Firestore/Orchestrator (shared)
- Port 3000: Admin UI
- Check `mcp-servers/` before creating new ones

### **2. Configuration Files**

- `pyproject.toml` - All Python dependencies managed by Poetry
- `scripts/` - All automation tools
- `Makefile` - Build targets (check before adding)
- NO `Pipfile`, `requirements.txt` (except those exported from Poetry), or legacy dependency files

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

The `.cursorrules` file is already configured. Additionally, use context files:

```
For any task, start with: Read ai_context_[planner|coder|reviewer|debugger].py
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

Always reference: ai_context_planner.py, ai_context_coder.py, ai_context_reviewer.py, ai_context_debugger.py
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
# Step 1: Run automated review
make ai-review-changes  # Uses ai_code_reviewer.py

# Step 2: Full validation
make after-ai-coding    # Runs ai-review + validate

# Step 3: Manual checks
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

   - `Pipfile`, `setup.cfg`, or any requirements files not exported from Poetry

2. **Container files**

   - Only use `Dockerfile`, `docker-compose.yml`, `.dockerignore` as part of the standardized workflow

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

# Check for Python 3.10+ features
python -m py_compile scripts/*.py  # Will fail on syntax errors

# Find and review os.system usage
grep -n "os\.system" scripts/*.py

# Check for duplicate functionality
diff -u <(grep "def " scripts/health_monitor.py | sort) <(grep "def " scripts/new_ai_file.py | sort)
```

## 🎯 Final Checklist

Before committing AI-generated code:

- [ ] Used appropriate ai*context*\*.py file for the task
- [ ] No new dependency management tools (Pipenv, Pipfile, etc.)
- [ ] Only use Docker/Poetry as specified
- [ ] Uses Python 3.10+ features as standard
- [ ] Uses existing patterns from scripts/
- [ ] Follows naming conventions
- [ ] Has proper type hints
- [ ] Passes `make validate`
- [ ] No duplicate functionality
- [ ] Simple solution, not over-engineered
- [ ] Uses subprocess.run(), not os.system()
- [ ] Ran `make ai-review-changes`

---

**Remember: Always start with the appropriate ai*context*\*.py file for your task!**
