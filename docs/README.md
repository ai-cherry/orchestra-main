# Orchestra Project Documentation

---

## 🚨 Python 3.11+ and Poetry Required

**All development, deployment, and CI/CD must use Python 3.11+ and Poetry.**
- Do **not** use pip/venv, Python 3.10, or requirements.txt workflows.
- All onboarding, setup, and environment scripts enforce this requirement.
- See [`scripts/validate_python_env.sh`](../scripts/validate_python_env.sh) for automated validation.

---

## Quick Start

```bash
# One-time setup (Python 3.11+, Docker Compose v2, Poetry)
docker compose build
poetry install
poetry run pre-commit install
bash scripts/validate_python_env.sh
```

---

## Key Environment Requirements

- **Python:** 3.11+ (enforced everywhere)
- **Poetry:** 1.8+ (dependency management)
- **Docker Compose:** v2+
- **GCP SDK:** For deployment and secret management

---

## Developer Workflow

1. **Clone the repo and install Python 3.11+**
2. **Run `poetry install`** to set up all dependencies and pre-commit hooks.
3. **Run `bash scripts/validate_python_env.sh`** before every commit or deploy.
4. **Use Docker Compose for all local and cloud builds.**
5. **All code, tools, and integrations are tested and supported only on Python 3.11+.**

---

## CI/CD and Deployment

- All GitHub Actions, Dockerfiles, and deployment scripts use Python 3.11+.
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

- **Lead Developer/Architect:** Responsible for enforcing Python 3.11+ and Poetry usage, onboarding, and environment validation.
- **All Contributors:** Must use the provided scripts and follow the standardized workflow.

---

## Troubleshooting

- If you encounter errors related to Python version, Poetry, or pre-commit:
  - Run `bash scripts/validate_python_env.sh`
  - Recreate your virtual environment with Python 3.11+
  - Consult the onboarding and setup guides

---

**This documentation and all scripts are reviewed quarterly to ensure ongoing alignment and prevent environment drift.**
