# Version Management Implementation Guide

## Quick Start

This guide provides step-by-step instructions for implementing the comprehensive version management system for the Orchestra platform.

## Phase 1: Immediate Stabilization (Week 1)

### Day 1-2: Lock Current Versions

#### Step 1: Python Dependencies
```bash
# Create a unified requirements lock file
cd /root/orchestra-main

# Install pip-tools if not present
pip install pip-tools

# Compile all requirements into a locked file
pip-compile requirements/base.txt \
    requirements/dev.txt \
    requirements/monitoring.txt \
    --output-file=requirements/locked-all.txt \
    --generate-hashes \
    --resolver=backtracking

# Create timestamp-based snapshot
cp requirements/locked-all.txt \
    requirements/frozen/complete_lock_$(date +%Y%m%d_%H%M%S).txt
```

#### Step 2: JavaScript Dependencies
```bash
cd admin-ui

# Remove conflicting lock files
rm package-lock.json

# Use pnpm for consistency
pnpm install --frozen-lockfile

# Update package.json to use specific versions
cat > scripts/lock-versions.js << 'EOF'
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));

// Replace "latest" with current resolved versions
const lockfile = JSON.parse(fs.readFileSync('pnpm-lock.yaml', 'utf8'));

for (const [name, version] of Object.entries(pkg.dependencies || {})) {
  if (version === 'latest' || version === '*') {
    // Get actual version from lockfile
    const locked = lockfile.packages[name];
    if (locked) {
      pkg.dependencies[name] = `^${locked.version}`;
    }
  }
}

fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
EOF

node scripts/lock-versions.js
```

#### Step 3: Create Version Registry
```yaml
# Create .versions.yaml at project root
cat > .versions.yaml << 'EOF'
# Orchestra Platform Version Registry
# Generated: 2025-01-06
# Schema Version: 1.0.0

metadata:
  schema_version: "1.0.0"
  last_updated: "2025-01-06T00:00:00Z"
  update_policy: "manual-approval"

runtimes:
  python:
    version: "3.10.12"
    docker_image: "python:3.10.12-slim-bookworm"
    digest: "sha256:abc123..."  # Update with actual digest
    
  node:
    version: "18.19.0"
    docker_image: "node:18.19.0-alpine3.18"
    digest: "sha256:def456..."  # Update with actual digest

databases:
  postgresql:
    version: "14.10"
    extensions:
      pgvector: "0.5.1"
      uuid-ossp: "1.1"
      
  weaviate:
    version: "1.24.1"
    modules:
      - text2vec-openai
      - reranker-openai

infrastructure:
  docker:
    version: "24.0.7"
    compose_version: "2.23.0"
    
  pulumi:
    version: "3.94.2"
    providers:
      vultr: "2.18.0"

core_dependencies:
  python:
    fastapi: "0.104.1"
    pydantic: "2.5.2"
    sqlalchemy: "2.0.23"
    weaviate-client: "3.24.1"
    pulumi: "3.94.2"
    
  javascript:
    react: "18.2.0"
    typescript: "5.3.3"
    vite: "5.0.10"
    "@tanstack/react-router": "1.15.0"
    "@tanstack/react-query": "5.17.0"
EOF
```

### Day 3-4: Security Fixes

#### Step 1: Python Security Audit
```bash
# Install safety for vulnerability scanning
pip install safety

# Run security scan
safety check --json > security-report-python.json

# Create fix script
cat > scripts/fix-python-vulnerabilities.py << 'EOF'
#!/usr/bin/env python3
"""Fix known Python vulnerabilities"""

import json
import subprocess
import sys

def fix_vulnerabilities():
    with open('security-report-python.json', 'r') as f:
        report = json.load(f)
    
    fixes = {
        'aiohttp': '3.9.1',
        'cryptography': '41.0.7',
        'requests': '2.31.0',
        'urllib3': '2.1.0'
    }
    
    for vuln in report.get('vulnerabilities', []):
        pkg = vuln['package_name']
        if pkg in fixes:
            print(f"Updating {pkg} to {fixes[pkg]}")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 
                f"{pkg}=={fixes[pkg]}"
            ])

if __name__ == '__main__':
    fix_vulnerabilities()
EOF

python scripts/fix-python-vulnerabilities.py
```

#### Step 2: JavaScript Security Audit
```bash
cd admin-ui

# Run npm audit
npm audit --json > ../security-report-npm.json

# Fix automatically where possible
npm audit fix

# For remaining issues, update manually
pnpm update postcss vite
```

### Day 5: Docker Security

#### Update All Dockerfiles
```bash
# Create secure Dockerfile template
cat > Dockerfile.secure-template << 'EOF'
# Multi-stage build for security and size optimization
ARG PYTHON_VERSION=3.10.12
ARG PYTHON_DIGEST=sha256:specific-hash-here

FROM python:${PYTHON_VERSION}-slim-bookworm@${PYTHON_DIGEST} AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /build

# Copy requirements first for better caching
COPY requirements/locked-all.txt .
RUN pip install --user --no-cache-dir -r locked-all.txt

# Runtime stage
FROM python:${PYTHON_VERSION}-slim-bookworm@${PYTHON_DIGEST}

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Set up app directory
WORKDIR /app
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy application code
COPY --chown=appuser:appuser . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
