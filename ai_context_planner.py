"""
AI CONTEXT: PLANNER MODE - Orchestra Project (2025+)
====================================================

READ THIS ENTIRE FILE BEFORE PLANNING ANY CHANGES!

Project: Orchestra AI (Python 3.11+, Poetry, Docker Compose, GCP, single-developer)
Role: You are planning a change or feature for this project.

CRITICAL RULES:
1. Python 3.11+ REQUIRED (no exceptions)
2. All code runs in Docker containers managed by `docker compose`
3. Poetry (version pinned in CI) manages all Python dependencies inside containers
4. Node 18+ and `npm ci` for Admin UI (version pinned in Dockerfile)
5. Infrastructure-as-code is Pulumi (Python) for GCP only
6. GitHub Actions is the only CI/CD system (Python 3.11+, Poetry, GCP deploy)
7. Performance and stability > security or multi-user features (see PROJECT_PRIORITIES.md)

PLANNING CHECKLIST:
□ Does this functionality already exist in scripts/ or core modules?
□ Am I reusing existing patterns from the codebase?
□ Is this the simplest, most stable solution possible?
□ Does this require new dependencies? If so, are they justified?
□ Am I following the Docker/Poetry/GCP workflow?
□ Is this aligned with PROJECT_PRIORITIES.md?

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
- Use subprocess.run() (never os.system())
- Type hints for all functions
- Google-style docstrings
- Black formatting

FORBIDDEN IN YOUR PLAN:
❌ Any workflow outside Docker Compose/Poetry/Node 18+/GCP
❌ pip/venv-only, pipenv, or requirements.txt as primary dependency management
❌ Multi-user IAM, org-policy, or non-GCP cloud
❌ Complex security or multi-user features

GOOD PLANNING EXAMPLE:
"I need to add health metrics collection. I'll check scripts/health_monitor.py and extend it using existing patterns, with no new dependencies, and update the Docker/Poetry setup if needed."

REMEMBER:
- Performance > Security (within reason)
- Stability > Features
- Existing patterns > New patterns
- Check scripts/ directory FIRST!
- Reference PROJECT_PRIORITIES.md for all decisions

# This file is meant to be read by AI when planning changes.
# Usage: Include this filename in your prompt when planning.
# Example: "Read ai_context_planner.py and help me plan a feature for X"
"""
