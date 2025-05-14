# Canonical Workflows for AI Orchestra

## Active Workflows

- **deploy-gcp-migration.yml**: The only supported workflow for GCP migration, deployment, and verification.
- **python-tests.yml**: The only supported workflow for Python code linting and tests.

## All other workflows in `.github/workflows/` are deprecated and should be archived, deleted, or disabled to prevent CI/CD conflicts and instability.

## Best Practices

- Validate all workflow YAMLs with `yamllint` and `actionlint` before pushing.
- Use only the canonical workflows for deployment and testing.
- All GCP secrets must be referenced directly in workflow steps.
- Docker build context and COPY paths must be explicit and correct.
- Run `terraform validate` and `poetry check` in CI to catch errors early.

## To Archive/Disable

Move all non-canonical workflow files to `.github/workflows/archived/` or delete them from the repo.