"""
AI CONTEXT: PLANNER MODE - Orchestra Project
============================================

READ THIS ENTIRE FILE BEFORE PLANNING ANY CHANGES!

Project: Orchestra AI (Python 3.11+, pip/venv, GCP-focused)
Role: You are planning a change/feature for this project

CRITICAL RULES:
1. Python 3.11+ REQUIRED (minimum 3.11)
2. pip/venv ONLY - NO Docker, Poetry, Pipenv
3. Check existing tools FIRST before planning new ones
4. Simple solutions > Complex architectures

EXISTING TOOLS YOU MUST CHECK FIRST:
- scripts/config_validator.py - Configuration validation
- scripts/health_monitor.py - Service health monitoring
- scripts/orchestra.py - Unified CLI for all operations
- scripts/ai_code_reviewer.py - AI code anti-pattern checker
- scripts/check_venv.py - Virtual environment validation
- scripts/check_dependencies.py - Dependency checking

SERVICE PORTS (DO NOT DUPLICATE):
- 8002: MCP Secret Manager (already exists)
- 8080: Core Orchestrator/Firestore (already exists)
- 3000: Admin UI
- 6379: Redis (if running)

PLANNING CHECKLIST:
□ Have I checked if this functionality already exists in scripts/?
□ Am I reusing existing patterns from the codebase?
□ Is this the simplest solution possible?
□ Does this require any new heavy dependencies?
□ Am I avoiding Docker/Poetry/complex patterns?

BEFORE PLANNING NEW FEATURES:
```bash
# Check what already exists
ls -la scripts/*.py
grep -r "def.*${FEATURE_KEYWORD}" scripts/
python scripts/orchestra.py services status
```

ARCHITECTURAL PRINCIPLES:
- All automation tools go in scripts/
- All configs in appropriate subdirectories
- Use subprocess.run(), never os.system()
- Type hints for all functions
- Google-style docstrings
- Black formatting

FORBIDDEN IN YOUR PLAN:
❌ Docker, docker-compose, containers
❌ Poetry, Pipenv, complex dependency management
⚠️  Complex Python 3.11+ features (e.g., metaprogramming with `match`/`case`, excessive `tomllib` use) — keep implementations simple and readable
❌ Creating new services on ports 8002, 8080

GOOD PLANNING EXAMPLE:
"I need to add health metrics collection. Let me check existing tools:
- scripts/health_monitor.py already monitors health
- I can extend it rather than create new tool
- Will use existing notification system in admin-ui/src/api/notifications.js
- No new dependencies needed, uses existing patterns"

BAD PLANNING EXAMPLE:
"I'll create a new monitoring service using Docker with Prometheus..."

REMEMBER:
- Performance > Security (within reason)
- Stability > Features
- Existing patterns > New patterns
- Check scripts/ directory FIRST!

When planning, always ask:
1. Does this already exist?
2. Can I extend existing tools?
3. What's the simplest approach?
4. Am I following project patterns?
"""

# This file is meant to be read by AI when planning changes
# Usage: Include this filename in your prompt when planning
# Example: "Read ai_context_planner.py and help me plan a feature for X"
