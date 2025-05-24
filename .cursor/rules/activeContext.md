# Cursor AI Context – orchestra-main

The following context should be provided to the AI assistant for every session.

---

## High-level architecture

See `docs/PROJECT_BLUEPRINT.md` for details.
• Dev on Paperspace VM via SSH (Cursor)
• Secrets via Secret Manager – exported at login by `~/.gcp_env_setup.sh`
• Deployment: GitHub Actions ➜ Cloud Build ➜ Cloud Run (`ai-orchestra-minimal` in `us-central1`).

## Key directories (keep short)

```
app.py            # Flask entry-point (Gunicorn target)
agent/            # FastAPI agent micro-service
orchestra_system/ # core libraries/utilities
scripts/          # helper & maintenance scripts
.github/workflows/ # CI/CD
```

## Coding conventions

1. Python 3.11, use type-hints & docstrings (Google style).
2. Access secrets via `os.getenv()` only.
3. Keep Dockerfile minimal; requirements pinned.
4. Lint: `flake8 --ignore=E501` (line length offloaded to Black).

---

_(Generated automatically 2025-05-22)_
