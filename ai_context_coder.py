"""
AI CONTEXT: CODER MODE - Orchestra Project (2025+)
==================================================

READ THIS ENTIRE FILE BEFORE WRITING ANY CODE!

Project: Orchestra AI (Python 3.10+, Poetry, Docker Compose, GCP, single-developer)
Role: You are implementing code for this project.

ENVIRONMENT CONSTRAINTS:
- Python 3.10+ (required everywhere)
- All code runs in Docker containers managed by `docker compose`
- Poetry (version pinned in CI) manages all Python dependencies inside containers
- Node 18+ and `npm ci` for Admin UI (version pinned in Dockerfile)
- GCP is the only supported cloud (infra as code via Pulumi/Python)
- GitHub Actions is the only CI/CD system (Python 3.10+, Poetry, GCP deploy)
- Performance and stability > security or multi-user features (see PROJECT_PRIORITIES.md)

CODING STANDARDS:
- Use type hints for all functions
- Google-style docstrings
- Black formatting
- Use subprocess.run() (never os.system())
- Prefer built-in libraries and minimal dependencies
- All automation tools/scripts go in scripts/
- All configs in appropriate subdirectories

REQUIRED PATTERNS:
- Use existing tools and patterns from scripts/ and core modules
- Reuse and extend, do not duplicate
- All dependencies managed by Poetry (no requirements.txt except as exported)
- For Admin UI, use Node 18+ and `npm ci` for installs

FORBIDDEN:
❌ Any workflow outside Docker Compose/Poetry/Node 18+/GCP
❌ pip/venv-only, pipenv, or requirements.txt as primary dependency management
❌ Multi-user IAM, org-policy, or non-GCP cloud
❌ Complex security or multi-user features

TESTING YOUR CODE:
```bash
# Validate syntax
poetry run python -m py_compile scripts/your_script.py

# Check for anti-patterns
poetry run python scripts/ai_code_reviewer.py --check-file scripts/your_script.py

# Format code
poetry run black scripts/your_script.py
```

REMEMBER:
- Simple > Complex
- Existing tools > New tools
- All code runs in containers managed by Docker Compose
- Reference PROJECT_PRIORITIES.md for all decisions

# This file is meant to be read by AI when coding.
# Usage: Include this filename in your prompt when coding.
# Example: "Read ai_context_coder.py and implement function X"
"""
