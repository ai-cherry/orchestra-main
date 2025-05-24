# Orchestra API Service

A high-performance, async-ready Python API for AI/data orchestration, designed for Cloud Run and GCP-native deployment.

---

## Features

- **Async FastAPI** for ultra-low latency and high concurrency
- **requirements.txt + pip-tools** for deterministic, reproducible dependency management
- **Pre-commit hooks** for linting, formatting, and type checks
- **Unit and integration test scaffolding** with pytest and httpx
- **Google Cloud integration** (Firestore, Pub/Sub, Secret Manager, DragonflyDB, Qdrant)
- **Dockerfile** optimized for Cloud Run
- **Load/chaos testing** scaffolding

---

## Quickstart

```bash
# 1. Bootstrap environment (installs pip-tools, compiles requirements, installs dependencies, sets up pre-commit and .env)
./bootstrap.sh

# 2. Run locally
uvicorn orchestra_api.main:app --reload

# 3. Run tests
pytest

# 4. Build and deploy to Cloud Run (see GCP deployment scripts for infra)
```

---

## Dependency Management

- All dependencies are managed via `requirements/base.in` and `requirements/dev.in`.
- Use `pip-compile` (from pip-tools) to generate fully pinned `requirements/base.txt` and `requirements/dev.txt`.
- The bootstrap script handles compilation and installation automatically.
- To update dependencies:
  ```bash
  pip-compile requirements/base.in
  pip-compile requirements/dev.in
  ```

---

## Structure

- `main.py` - FastAPI entrypoint
- `memory/` - Unified memory abstraction (DragonflyDB, Qdrant, Firestore)
- `tests/` - Unit and integration tests
- `Dockerfile` - Cloud Run optimized container
- `bootstrap.sh` - One-command setup (pip, pip-tools, pre-commit, env, secret sync)
- `.pre-commit-config.yaml` - Linting, formatting, type checks

---

## GCP Integration

- Reads secrets from Google Secret Manager (see bootstrap.sh for integration points)
- Connects to Firestore, Pub/Sub, DragonflyDB, Qdrant
- Ready for VPC, autoscaling, and regional co-location

---

## Secret Management

- Local `.env` is created and can be automatically synced from Google Secret Manager.
- Customize the secret sync section in `bootstrap.sh` to fetch secrets using `gcloud` or the Python SDK.

---

## Load/Chaos Testing

- See `tests/load/` for Locust/k6 scaffolding

---

## Documentation

- See `ARCHITECTURE.md` for diagrams and integration details.

---
