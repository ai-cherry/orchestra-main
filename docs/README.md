# Orchestra Project Documentation

---

## 🚨 Python 3.10 and pip/venv Required

**All development, deployment, and CI/CD must use Python 3.10 and pip/venv.**
- Do **not** use Poetry, Python 3.11+, or Pipenv workflows.
- All onboarding, setup, and environment scripts enforce this requirement.
- See [`scripts/validate_python_env.sh`](../scripts/validate_python_env.sh) for automated validation.

---

## Quick Start

```bash
# One-time setup (Python 3.10, Docker Compose v2)
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements/base.txt
bash scripts/validate_python_env.sh
docker compose build
```

---

## Key Environment Requirements

- **Python:** 3.10 (enforced everywhere)
- **pip/venv:** (dependency management)
- **Docker Compose:** v2+

---

## Developer Workflow

1. **Clone the repo and install Python 3.10**
2. **Create and activate a virtual environment with venv**
3. **Install dependencies with pip and requirements/base.txt**
4. **Run `bash scripts/validate_python_env.sh`** before every commit or deploy.
5. **Use Docker Compose for all local and cloud builds.**
6. **All code, tools, and integrations are tested and supported only on Python 3.10.**

---

## CI/CD and Deployment

- All GitHub Actions, Dockerfiles, and deployment scripts use Python 3.10.
- Pre-commit hooks and CI/CD pipelines will fail early if the wrong Python version or missing dependencies are detected.
- See `.pre-commit-config.yaml` for enforced checks.

---

## Documentation Index

- [README_NO_BS.md](../README_NO_BS.md): Minimal workflow
- [UNFUCK_EVERYTHING.md](../UNFUCK_EVERYTHING.md): Full setup guide
- [docs/ADMIN_IMPROVEMENT_STRATEGY.md](ADMIN_IMPROVEMENT_STRATEGY.md): Admin interface improvement plan
- [docs/ORCHESTRA_AI_OPERATIONS_GUIDE.md](ORCHESTRA_AI_OPERATIONS_GUIDE.md): AI operations and orchestration
- [docs/PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md): Production deployment steps
- [docs/PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md): Project structure and conventions

---

## Accountability

- **Lead Developer/Architect:** Responsible for enforcing Python 3.10 and pip/venv usage, onboarding, and environment validation.
- **All Contributors:** Must use the provided scripts and follow the standardized workflow.

---

## Troubleshooting

- If you encounter errors related to Python version, pip, or pre-commit:
  - Run `bash scripts/validate_python_env.sh`
  - Recreate your virtual environment with Python 3.10
  - Consult the onboarding and setup guides

---

**This documentation and all scripts are reviewed quarterly to ensure ongoing alignment and prevent environment drift.**
