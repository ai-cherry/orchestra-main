# Orchestra AI Project Structure

## 🏗️ Directory Overview

```
orchestra-main/
├── scripts/                    # ALL automation tools go here
│   ├── config_validator.py     # Comprehensive config validation
│   ├── health_monitor.py       # Service health monitoring
│   ├── orchestra.py            # Unified CLI interface
│   ├── ai_code_reviewer.py     # AI code consistency checker
│   ├── check_venv.py           # Virtual environment validation
│   └── check_dependencies.py   # Dependency checking
│
├── ai_context_*.py            # AI context files (root level)
│   ├── ai_context_planner.py  # Planning phase guidance
│   ├── ai_context_coder.py    # Coding patterns & examples
│   ├── ai_context_reviewer.py # Review checklist
│   └── ai_context_debugger.py # Debug workflows
│
├── requirements/               # Dependency management (pip-based)
│   ├── base.txt               # Core dependencies
│   ├── development.txt        # Dev dependencies
│   └── production.txt         # Prod dependencies
│
├── mcp-servers/               # MCP server implementations
│   ├── secret_manager.py      # Port 8002
│   └── gcp-resources-server.yaml
│
├── core/orchestrator/         # Core orchestration logic
│   └── src/
│       ├── api/               # API endpoints
│       │   └── app.py        # Main FastAPI app (port 8080)
│       └── config/           # Configuration files
│
├── admin-ui/                  # Admin interface
│   └── src/
│       └── api/
│           └── notifications.js  # Notification system
│
├── docs/                      # Documentation
│   ├── AI_CODING_STANDARDS.md # AI tool guidelines
│   ├── PROJECT_STRUCTURE.md   # This file
│   ├── AI_WORKFLOW_INTEGRATION.md # How AI tools work together
│   └── AUTOMATION_SUMMARY.md  # Automation overview
│
├── AI_CONTEXT_FILES.md       # Quick reference for context files
├── Makefile                   # Build automation
├── .cursorrules              # Cursor AI rules
└── .pre-commit-config.yaml   # Pre-commit hooks
```

## 🛠️ Key Components

### **1. Automation Scripts (scripts/)**

All automation tools MUST go in the `scripts/` directory:

| Script                | Purpose                                    | Usage                                                |
| --------------------- | ------------------------------------------ | ---------------------------------------------------- |
| `config_validator.py` | Validates YAML, env vars, GCP connectivity | `python scripts/config_validator.py`                 |
| `health_monitor.py`   | Dynamic health checks, replaces sleep      | `python scripts/health_monitor.py --monitor`         |
| `orchestra.py`        | Unified CLI for all operations             | `python scripts/orchestra.py services status`        |
| `ai_code_reviewer.py` | Checks for AI anti-patterns                | `python scripts/ai_code_reviewer.py --check-changes` |

### **2. Service Ports**

Fixed port assignments - DO NOT duplicate:

- **8002**: MCP Secret Manager
- **8080**: Core Orchestrator / Firestore MCP
- **3000**: Admin UI
- **6379**: Redis (if running)

### **3. Configuration Files**

- `requirements/base.txt` - Core Python dependencies
- `mcp-servers/*.yaml` - MCP server configs
- `core/orchestrator/src/config/*.yaml` - Service configs
- NO Docker files, NO Poetry files, NO Pipfile

### **4. Makefile Targets**

Key automation targets:

```bash
# Development
make dev-start              # Full dev environment setup
make validate              # Run all validations

# Services
make service-status        # Check what's running
make start-services        # Start all services
make stop-services         # Stop all services

# Health & Monitoring
make health-check          # One-time health check
make health-monitor        # Continuous monitoring
make wait-for-mcp         # Smart waiting (no sleep!)

# AI Code Review
make ai-review-changes     # Review git changes
make before-ai-coding      # Prep for AI session
make after-ai-coding       # Validate AI changes
```

## 📋 Before Adding New Code

### **Check Existing Tools**

```bash
# Find existing validators
grep -r "def.*validat" scripts/

# Find existing monitors
grep -r "def.*monitor\|health" scripts/

# Find existing CLI commands
grep -r "argparse" scripts/

# List all automation tools
ls -la scripts/*.py
```

### **Common Patterns to Follow**

#### **1. Script Structure**

```python
#!/usr/bin/env python3
"""One-line description.

Longer description of what this does.

Usage:
    python scripts/myscript.py --option value
"""

import standard_libs
import third_party_libs
from typing import Dict, List

logger = logging.getLogger(__name__)

class MyTool:
    """Tool description."""

    def __init__(self):
        pass

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser()
    # ... args

if __name__ == "__main__":
    sys.exit(main())
```

#### **2. Error Handling**

```python
# Good - specific, graceful
try:
    result = subprocess.run(cmd, capture_output=True, timeout=30)
except subprocess.TimeoutExpired:
    logger.error("Command timed out")
    return False
```

#### **3. Subprocess Usage**

```python
# ✅ GOOD - Secure
subprocess.run(["terraform", "plan", "-out=tfplan"], check=True)

# ❌ BAD - Insecure
os.system(f"terraform plan -out=tfplan")
subprocess.run(cmd, shell=True)  # Avoid shell=True
```

## 🚫 What NOT to Add

### **Forbidden Files**

- `Dockerfile`, `docker-compose.yml`
- `Pipfile`, `poetry.lock`, `pyproject.toml`
- `setup.py`, `setup.cfg`
- `requirements-*.txt` (use requirements/ directory)

### **Forbidden Dependencies**

- `docker`, `docker-compose`
- `poetry`, `pipenv`
- `pandas` (for simple tasks)
- Heavy ML libraries (unless absolutely needed)

### **Forbidden Patterns**

- Multiple inheritance
- Metaclasses
- Abstract base classes for simple tasks
- Python 3.10+ only features

## 🔍 Quick Reference

### **Find Stuff**

```bash
# Find API endpoints
find . -path "*/api/*" -name "*.py"

# Find config files
find . -name "*.yaml" -o -name "*.yml" | grep -v venv

# Find service definitions
grep -r "port.*80" --include="*.py"

# Find existing functionality
grep -r "class.*${PATTERN}" --include="*.py" scripts/
```

### **Validate Changes**

```bash
# After making changes
make ai-review-changes     # Check for anti-patterns
make validate             # Run all validations
make health-check         # Verify services still work
```

---

**Remember: If you're not sure if something exists, it probably does! Check `scripts/` first!**
