# GCP Cleanup Checklist

## Completed by Script
- [x] Removed GCP-specific directories
- [x] Removed GCP-specific files
- [x] Cleaned Python dependencies
- [x] Created cleaned settings file

## Manual Tasks Required

### 1. Update Import Statements
Search and remove/replace these imports:
- `from google.cloud import *`
- `import google.cloud.*`
- `from google.api_core import *`

### 2. Update Docker Configurations
- Remove `GOOGLE_APPLICATION_CREDENTIALS` from docker-compose.yml
- Remove any GCP-related environment variables

### 3. Update GitHub Actions
- Remove GCP authentication steps
- Remove `google-github-actions/auth` actions
- Update deployment workflows for DigitalOcean

### 4. Update Documentation
- Remove GCP setup instructions
- Add DigitalOcean deployment guide
- Update README.md

### 5. Test Everything
- Run `docker-compose up` locally
- Verify all services connect properly
- Run test suite

## Rollback Instructions
If something breaks:
1. Restore requirements: `cp requirements/base.txt.backup requirements/base.txt`
2. Restore settings: `git checkout core/orchestrator/src/config/settings.py`
3. Use git to restore deleted files: `git checkout -- .`
