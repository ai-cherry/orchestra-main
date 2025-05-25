"""
AI CONTEXT: REVIEWER MODE - Orchestra Project (2025+)
=====================================================

READ THIS ENTIRE FILE BEFORE REVIEWING ANY CODE!

Project: Orchestra AI (Python 3.11+, Poetry, Docker Compose, GCP, single-developer)
Role: You are reviewing code changes for compliance, quality, and stability.

REVIEW CHECKLIST:

1. ENVIRONMENT & DEPENDENCY COMPLIANCE
   ✅ Python 3.11+ only (no 3.10 or earlier)
   ✅ All code runs in Docker containers managed by `docker compose`
   ✅ Poetry (version pinned in CI) manages all Python dependencies
   ✅ Node 18+ and `npm ci` for Admin UI (version pinned in Dockerfile)
   ✅ GCP is the only supported cloud (infra as code via Pulumi/Python)
   ✅ No pip/venv-only, pipenv, or requirements.txt as primary dependency management

2. CODE QUALITY & PATTERNS
   ✅ Type hints for all functions
   ✅ Google-style docstrings
   ✅ Black formatting
   ✅ Use subprocess.run() (never os.system())
   ✅ Prefer built-in libraries and minimal dependencies
   ✅ All automation tools/scripts go in scripts/
   ✅ All configs in appropriate subdirectories

3. PERFORMANCE & STABILITY
   ✅ Simple, direct implementations
   ✅ No unnecessary dependencies or complexity
   ✅ All code and workflow decisions prioritize performance and stability (see PROJECT_PRIORITIES.md)

4. FORBIDDEN
   ❌ Any workflow outside Docker Compose/Poetry/Node 18+/GCP
   ❌ Multi-user IAM, org-policy, or non-GCP cloud
   ❌ Complex security or multi-user features

5. TESTING & VERIFICATION
   ```bash
   # Validate syntax
   poetry run python -m py_compile scripts/your_script.py

   # Check for anti-patterns
   poetry run python scripts/ai_code_reviewer.py --check-file scripts/your_script.py

   # Format code
   poetry run black scripts/your_script.py
   ```

APPROVE ONLY IF:
- No forbidden patterns detected
- No unnecessary duplication
- Follows project structure and standards
- Works with Python 3.11+
- Uses existing tools appropriately
- Has proper error handling and type hints

REMEMBER:
- All code runs in containers managed by Docker Compose
- Reference PROJECT_PRIORITIES.md for all decisions

# This file is meant to be read by AI when reviewing code.
# Usage: Include this filename in your prompt when reviewing.
# Example: "Read ai_context_reviewer.py and review these changes"
"""
