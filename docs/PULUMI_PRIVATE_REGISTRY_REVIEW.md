# Pulumi Private Registry & ESC Review

This document summarizes how the repository currently uses Pulumi and what additional features from Pulumi's Private Registry, templates, and ESC (Environments, Secrets, and Configuration) could be adopted.

## Current State

- The infrastructure is defined in `infra/` using Pulumi Python code. Components such as `WeaviateComponent` and `MonitoringComponent` are implemented as `ComponentResource` classes (e.g. `infra/components/weaviate_component.py`).
- Secrets are stored in Pulumi config and retrieved via helper scripts. The guide `docs/FINAL_SECRET_MANAGEMENT_GUIDE.md` describes generating a `.env` with `python scripts/generate_env_from_pulumi.py` and adding new secrets using `pulumi config set --secret`.
- There is no usage of Pulumi Private Registry, organization templates, or Pulumi ESC.

## Opportunities

### Private Registry for Components

Pulumi components under `infra/components/` can be published as reusable packages. Steps:
1. Tag the repository using semantic versioning (e.g. `v0.1.0`).
2. Add a README for each component describing inputs and outputs.
3. Publish with `pulumi package publish <path> --publisher <org>`.
   The private registry will generate API docs automatically.
4. Other stacks can install the component via `pulumi install` referencing the Git URL or registry version.

Publishing components helps enforce best practices and allows reuse across projects or stacks.

### Organization Templates

To standardize new infrastructure projects, create a template repository containing `Pulumi.yaml` and example stack configuration. After adding the repository as an Organization Template source, developers (or AI coders) can bootstrap new projects through the Pulumi console or CLI (`pulumi new`).

### ESC for Secrets and Config

The codebase currently uses plain Pulumi config for secrets. Pulumi ESC can provide centralized management and integrations with external secret stores (AWS Secrets Manager, Azure Key Vault, etc.).

Possible steps:
1. Create ESC environments for dev/staging/prod.
2. Configure secret providers and use `pulumi env` or `esc` CLI to fetch credentials during deployment.
3. Update existing scripts (`scripts/generate_env_from_pulumi.py`, `infra/populate_pulumi_secrets.sh`) to read from ESC if configured.

ESC also supports OIDC-based short‑lived credentials, reducing the need for long‑lived tokens in CI.

### Manual Pulumi Configuration

Certain items still require manual setup in Pulumi Cloud:
- Initial creation of stacks (e.g. `pulumi stack init dev` and selecting the backend).
- Setting secret values using `pulumi config set --secret` or by running `infra/populate_pulumi_secrets.sh`.
- Configuring deployment settings such as OIDC provider IDs for each stack.

These steps are performed once per stack and are not currently automated in the repository.

## Recommendations

1. **Publish core components** to the Private Registry with READMEs and semantic version tags. This enables discovery and documentation for AI coders.
2. **Create an organization template** that references these components to simplify new project scaffolding.
3. **Evaluate Pulumi ESC** for storing secrets that need sharing across stacks or for integrating with external secret managers. Update scripts to pull from ESC when available.
4. **Continue using the existing scripts** (`generate_env_from_pulumi.py`, `populate_pulumi_secrets.sh`) for local development until ESC adoption is finalized.

Adopting these features will make infrastructure provisioning more consistent and secure while keeping manual Pulumi steps minimal.
