refactor: simplify Python dependency management and enhance deployment security

## Summary

Removed Poetry in favor of pip + requirements.txt for simpler dependency management
and enhanced Docker security with multi-stage builds and non-root user.

## Changes Made

### Build Pipeline (cloudbuild.yaml)

- Removed Poetry installation and usage
- Switched to pip install -r requirements.txt
- Enhanced pre-commit step to install required Python tools
- Kept asdf for Python version management

### Docker Configuration (Dockerfile)

- Implemented multi-stage build pattern
  - Builder stage: compiles dependencies with gcc
  - Final stage: minimal runtime without build tools
- Added non-root user (appuser) for security
- Updated to specific base image: python:3.11-slim-bullseye
- Optimized layer caching and reduced image size

### Cleanup

- Deleted poetry.toml from project root
- Aligned GitHub Actions with pip-based workflow (already compatible)

### Configuration Updates

- Enhanced .cursorignore with project-specific patterns
- Updated Cursor rule files for better AI assistance

## Testing Checklist

- [ ] Verify requirements.txt is current (pip freeze > requirements.txt)
- [ ] Push to main branch to trigger deployment
- [ ] Monitor Cloud Build logs for successful completion
- [ ] Verify Cloud Run service is running with new image
- [ ] Test application endpoints for functionality

## Notes

- Cloud Run service remains publicly accessible (--allow-unauthenticated)
- Secrets continue to be managed via GCP Secret Manager
- Pre-commit hooks run in CI for code quality checks
