# 🔒 DEPENDENCY LOCKDOWN PLAN
## End the Version Hell Once and For All

### 🎯 Core Principle: FREEZE EVERYTHING
**No more moving targets. Lock down versions and stick to them.**

---

## 📌 FIXED VERSION MATRIX

### System Requirements
```bash
# Operating System
Ubuntu 20.04 LTS (or compatible)

# Core Languages
Python:     3.10.12 (EXACT - not 3.10.x, not 3.11, EXACTLY 3.10.12)
Node.js:    18.20.2 (for admin UI only)
Go:         1.21.5  (for any Go tools)

# Infrastructure Tools
Pulumi:     3.88.0  (LOCKED - no auto-updates)
Docker:     24.0.7  (LOCKED - no auto-updates)
Terraform:  1.5.7   (if needed, but prefer Pulumi)
gcloud:     455.0.0 (LOCKED - no auto-updates)
```

### Python Dependencies Strategy
```bash
# NO Poetry, NO Pipenv, NO Conda
# ONLY pip with pinned versions

# Core dependencies (requirements/base.txt)
fastapi==0.115.12
pydantic==2.11.4
sqlalchemy==2.0.30
google-cloud-aiplatform==1.93.1
google-cloud-firestore==2.20.2
google-cloud-storage==2.19.0
litellm==1.70.4
redis==5.0.1
httpx==0.28.1
uvicorn==0.29.0

# Dev dependencies (requirements/dev.txt)
pytest==7.4.3
black==24.4.2
mypy==1.8.0
flake8==7.0.0
pre-commit==3.5.0
```

---

## 🛠️ IMPLEMENTATION STEPS

### 1. Create Version Lock Files
```bash
# Create a master version file
cat > .versions.lock << 'EOF'
# DO NOT MODIFY WITHOUT TEAM APPROVAL
# Last updated: $(date)
PYTHON_VERSION=3.10.12
NODE_VERSION=18.20.2
PULUMI_VERSION=3.88.0
DOCKER_VERSION=24.0.7
GCLOUD_VERSION=455.0.0
EOF
```

### 2. Pin ALL Dependencies
```bash
# Generate exact requirements
pip freeze > requirements/frozen-$(date +%Y%m%d).txt

# Create requirements files with exact versions
echo "# Frozen on $(date)" > requirements/base.txt
pip list --format=freeze | grep -E "(fastapi|pydantic|sqlalchemy|google-cloud|litellm|redis|httpx|uvicorn)" >> requirements/base.txt
```

### 3. Docker Base Images
```dockerfile
# ALWAYS use specific tags, NEVER :latest
FROM python:3.10.12-slim-bullseye
# NOT python:3.10-slim or python:latest

FROM node:18.20.2-alpine3.18
# NOT node:18-alpine or node:latest

FROM pulumi/pulumi:3.88.0
# NOT pulumi/pulumi:latest
```

### 4. Pulumi Configuration
```yaml
# Pulumi.yaml
name: orchestra-main
runtime:
  name: python
  options:
    virtualenv: venv
    pythonVersion: "3.10.12"  # Exact version
```

### 5. CI/CD Lockdown
```yaml
# .github/workflows/ci.yml
jobs:
  build:
    runs-on: ubuntu-20.04  # Fixed OS version
    steps:
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10.12'  # Exact version
      - uses: actions/setup-node@v3
        with:
          node-version: '18.20.2'   # Exact version
```

---

## 🚫 FORBIDDEN PRACTICES

1. **NEVER use version ranges**
   - ❌ `pydantic>=2.0`
   - ❌ `fastapi~=0.115`
   - ✅ `pydantic==2.11.4`

2. **NEVER use :latest tags**
   - ❌ `FROM python:latest`
   - ❌ `FROM python:3.10`
   - ✅ `FROM python:3.10.12-slim-bullseye`

3. **NEVER auto-update tools**
   - ❌ `gcloud components update`
   - ❌ `pulumi update`
   - ✅ Manual updates only after testing

4. **NEVER use system Python**
   - ❌ `/usr/bin/python3`
   - ✅ Always use venv

---

## 📋 MAINTENANCE PROTOCOL

### Monthly Dependency Review (First Monday)
1. Create a test branch
2. Update ONE dependency at a time
3. Run full test suite
4. Document any breaking changes
5. Only merge if ALL tests pass

### Quarterly Tool Updates (First Monday of Quarter)
1. Review security advisories
2. Test infrastructure tools in isolation
3. Update documentation
4. Coordinate team-wide update

### Emergency Updates (Security Only)
1. Create hotfix branch
2. Update ONLY the affected package
3. Run security scan
4. Deploy with rollback plan

---

## 🔧 SETUP SCRIPTS

### Initial Setup (one-time)
```bash
#!/bin/bash
# setup_locked_env.sh

set -euo pipefail

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
if [[ "$PYTHON_VERSION" != "3.10.12" ]]; then
    echo "ERROR: Python 3.10.12 required, found $PYTHON_VERSION"
    echo "Install with: pyenv install 3.10.12"
    exit 1
fi

# Create venv with specific Python
python3.10 -m venv venv --prompt orchestra
source venv/bin/activate

# Install exact dependencies
pip install --no-cache-dir -r requirements/base.txt
pip install --no-cache-dir -r requirements/dev.txt

# Lock Pulumi version
curl -fsSL https://get.pulumi.com | sh -s -- --version 3.88.0

# Lock gcloud version
export CLOUDSDK_CORE_DISABLE_PROMPTS=1
curl https://sdk.cloud.google.com | bash -s -- --disable-prompts --install-dir=$HOME --version=455.0.0

echo "✅ Locked environment ready"
```

### Daily Development
```bash
#!/bin/bash
# start_dev.sh

# Always activate venv first
source venv/bin/activate

# Verify versions
python --version | grep -q "3.10.12" || echo "⚠️  Wrong Python version!"
pulumi version | grep -q "3.88.0" || echo "⚠️  Wrong Pulumi version!"

# Set environment
export PYTHONDONTWRITEBYTECODE=1
export PULUMI_SKIP_UPDATE_CHECK=1
export CLOUDSDK_CORE_DISABLE_PROMPTS=1

echo "✅ Development environment ready"
```

---

## 🎯 BENEFITS

1. **No More Surprises**: Exact versions = predictable behavior
2. **Fast CI/CD**: No version resolution, just install
3. **Easy Debugging**: Same versions everywhere
4. **Simple Onboarding**: Run one script, get exact environment

---

## 📝 TEAM AGREEMENT

By adopting this plan, we agree to:
1. NEVER update dependencies without team approval
2. ALWAYS use exact versions
3. DOCUMENT any version changes
4. TEST before updating anything
5. ROLLBACK if anything breaks

**Sign-off**: ___________________ Date: ___________

---

## 🚨 BREAK GLASS PROCEDURE

If everything is broken:
1. `git checkout last-known-good-commit`
2. `rm -rf venv node_modules`
3. `./setup_locked_env.sh`
4. `./start_dev.sh`

**Last Known Good Commit**: `________________`
**Last Known Good Date**: `________________`
