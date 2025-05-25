"""
AI CONTEXT: DEBUGGER MODE - Orchestra Project (2025+)
=====================================================

READ THIS ENTIRE FILE BEFORE DEBUGGING!

Project: Orchestra AI (Python 3.10+, Poetry, Docker Compose, GCP, single-developer)
Role: You are debugging issues in this project.

ENVIRONMENT & WORKFLOW:
- Python 3.10+ (required everywhere)
- All code runs in Docker containers managed by `docker compose`
- Poetry (version pinned in CI) manages all Python dependencies inside containers
- Node 18+ and `npm ci` for Admin UI (version pinned in Dockerfile)
- GCP is the only supported cloud (infra as code via Pulumi/Python)
- GitHub Actions is the only CI/CD system (Python 3.10+, Poetry, GCP deploy)
- Performance and stability > security or multi-user features (see PROJECT_PRIORITIES.md)

COMMON DEBUGGING STEPS:
1. Confirm you are inside the Docker container (`./start.sh shell`)
2. Check Python and Node versions:
   ```bash
   python --version  # Should be 3.10+
   node --version    # Should be 18+
   ```
3. Check Poetry and dependency status:
   ```bash
   poetry --version
   poetry install
   poetry check
   ```
4. For Admin UI, always use `npm ci` (not `npm install`)
5. Use provided scripts for service status and logs:
   ```bash
   python scripts/orchestra.py services status
   python scripts/orchestra.py logs <service>
   ```
6. For GCP issues, check credentials and project:
   ```bash
   echo $GOOGLE_APPLICATION_CREDENTIALS
   gcloud config get-value project
   ```

TROUBLESHOOTING:
- All services should be started via `./start.sh up`
- All code, tests, and scripts should run inside the container
- If dependencies fail, run `poetry install` or `npm ci` as appropriate
- For infra, see infra/README.md for Pulumi/GCP workflows

FORBIDDEN:
❌ Any workflow outside Docker Compose/Poetry/Node 18+/GCP
❌ pip/venv-only, pipenv, or requirements.txt as primary dependency management
❌ Multi-user IAM, org-policy, or non-GCP cloud
❌ Complex security or multi-user features

REMEMBER:
- All debugging and troubleshooting happens inside the Docker container
- Reference PROJECT_PRIORITIES.md for all decisions

# This file is meant to be read by AI when debugging.
# Usage: Include this filename in your prompt when debugging.
# Example: "Read ai_context_debugger.py and help debug this error"
"""
