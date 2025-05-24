# Contributing Guide

Thank you for contributing to Orchestra AI!

## Quick Start

```bash
# Clone repository
$ git clone https://github.com/ai-cherry/orchestra-main.git
$ cd orchestra-main

# Create and activate Python 3.10 venv
$ python3.10 -m venv venv
$ source venv/bin/activate

# Install prod + dev dependencies
$ make install-dev

# Install git hooks (one-time)
$ pre-commit install
```

## Common Tasks

| Task                       | Command           |
| -------------------------- | ----------------- |
| Format code (Black + Ruff) | `make format`     |
| Lint (Ruff/Flake8)         | `make lint`       |
| Type-check (Mypy)          | `make type-check` |
| Run tests (pytest)         | `make test`       |
| Full validation            | `make validate`   |

## Commit Workflow

1.  Stage your changes → `git add …`
2.  `git commit` – pre-commit hooks will run automatically.
3.  If hooks fail:
    - Fix issues (or run `make format`),
    - `git add` any modified files,
    - Repeat commit.

## CI

GitHub Actions run `make validate` on every push/PR. A red ❌ means code-quality checks failed.

## Python Version

• Target version: **3.10** (until fleet upgrades to 3.11).
• `check_venv.py` will abort if a lower version is activated.

## Troubleshooting

- **Double (venv)** prompt → run `deactivate` until prompt clears, then `source venv/bin/activate` once.
- Port 8080 in use → `lsof -i :8080` then `kill <PID>`.

Happy hacking! 🎶
