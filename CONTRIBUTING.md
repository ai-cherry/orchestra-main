# Contributing to Orchestra System

Welcome! To ensure a smooth and reproducible development experience, please follow these steps when setting up your environment and contributing code.

## 1. Tooling Setup (asdf)

We use [asdf](https://asdf-vm.com/) to manage tool versions. Install asdf and the required plugins:

```bash
# Install asdf (if not already installed)
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
. "$HOME/.asdf/asdf.sh"

# Install plugins
asdf plugin add python || true
asdf plugin add poetry || true
asdf plugin add terraform || true
asdf plugin add nodejs || true

# Install pinned versions
asdf install --all
```

## 2. Python & Poetry Workspace

- Use Poetry 2.x (pinned in `.tool-versions`).
- All dependencies are managed in the root `pyproject.toml` as a workspace.
- Use `poetry install` to set up your environment.

## 3. Pre-commit Hooks

We use [pre-commit](https://pre-commit.com/) to enforce code quality and formatting. Install and activate hooks:

```bash
pip install pre-commit
pre-commit install
```

You can run all hooks manually with:

```bash
pre-commit run --all-files
```

## 4. Docker

Use the provided `docker/Dockerfile.app` as a template for service containers. Build with:

```bash
docker build -f docker/Dockerfile.app .
```

## 5. Infrastructure as Code

- Use Terragrunt or Terraform, but not both for backends. Run `terraform/lint-backend.sh` to check compliance.
- Providers are pinned in `terraform/versions.tf`.

## 6. Secrets & Auth

- Use `.envrc` and [direnv](https://direnv.net/) for local secrets and environment variables.
- Copy `.envrc` to `.envrc.local` and edit as needed. Never commit secrets.

## 7. Dependency Updates

- We use Renovate for automated dependency and tool upgrades. Review and merge Renovate PRs regularly.

## 8. CI/CD

- Ensure CI uses `asdf install --all` and Poetry 2.x.
- Add pre-commit, lint, and terraform checks to CI.

---

For any questions, see the `README.md` or ask in the project chat.
