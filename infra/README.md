# GCP Infrastructure as Code (`infra/`)

This directory contains all infrastructure-as-code for GCP using [Pulumi](https://www.pulumi.com/) with Python.
**No Poetry or extra tooling required—just Python venv and pip for maximum simplicity and reproducibility.**

---

## Dependency Management

### Requirements Structure

- `requirements/base.txt`: Core dependencies
- `requirements/development.txt`: Dev/test/lint tools
- `requirements/production.txt`: Production-only extras
- `requirements/webscraping.txt`: Web scraping agent dependencies

All environments inherit from `base.txt` for consistency.

## Setup

**Python 3.11+ is required for all infrastructure work.**

**Pulumi state backend:**
- All stacks use the GCS bucket `gs://cherry-ai-project-pulumi-state` for state storage.

**Admin UI stack:**
- The static admin UI is managed in `infra/admin_ui_site/` and deployed via the `admin-ui` Pulumi stack (see `.github/workflows/admin-ui.yml` and `scripts/deploy_admin_ui.py`).

1. Create a virtual environment:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   ```
2. Install infra dependencies:
   ```bash
   pip install -r ../requirements.txt
   ```

## Quickstart

1. **Bootstrap the Environment**

   ```bash
   cd infra
   bash bootstrap_pulumi_venv.sh
   ```

   This creates a Python virtual environment, installs all dependencies, and prints next steps.

2. **Initialize Pulumi Project (First Time Only)**

   ```bash
   pulumi new gcp-python
   # Follow prompts for project name, stack, and region.
   ```

3. **Configure Your Stack**

   ```bash
   pulumi stack init dev
   pulumi config set gcp:project <your-gcp-project-id>
   pulumi config set gcp:region <your-gcp-region>
   ```

4. **Define Infrastructure**

   - Edit [`__main__.py`](./__main__.py) to add/modify GCP resources.
   - Example: A storage bucket is included as a template.

5. **Deploy**

   ```bash
   pulumi up
   ```

6. **Teardown**

   ```bash
   pulumi destroy
   ```

---

## Best Practices

- Use stack configuration for project/region.
- Store secrets using `pulumi config set --secret`.
- Keep resource names deterministic for reproducibility.
- Document all changes and keep this README up to date.

---

## Troubleshooting

- **Virtual environment issues:**
  Re-run `source venv/bin/activate` in `infra/`.

- **Pulumi CLI not found:**
  Ensure `venv/bin` is in your PATH or install Pulumi globally.

- **GCP authentication:**
  Make sure you are authenticated with `gcloud auth application-default login`.

---

## Extending

- Add new GCP resources in [`__main__.py`](./__main__.py).
- For multi-env (dev/prod), use separate stacks:
  `pulumi stack init prod`

---

## Philosophy

- **Minimal dependencies:** Only venv + pip.
- **Performance & stability:** No unnecessary complexity.
- **Single-developer focus:** No multi-user IAM or org-policy overhead.

See [`docs/gcp-optimization-checklist.md`](../docs/gcp-optimization-checklist.md) for further optimization tips.
