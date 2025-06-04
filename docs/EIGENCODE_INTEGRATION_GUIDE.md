# EigenCode Integration Guide

## Overview

EigenCode is a holistic code analysis tool that provides comprehensive insights into your codebase structure, dependencies, and potential issues. This guide covers installation, configuration, common issues, and optimization strategies for integrating EigenCode with the AI conductor system.

## Table of Contents

1. [Installation](#installation)
2. [Common Issues and Solutions](#common-issues-and-solutions)
3. [Performance Optimization](#performance-optimization)
4. [Security Considerations](#security-considerations)
5. [API Integration](#api-integration)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Installation

### Prerequisites

- Linux-based system (Ubuntu 20.04+ recommended)
- Python 3.8 or higher
- At least 2GB of available RAM
- Internet connection for downloading

### Step-by-Step Installation

#### Method 1: Automated Installation Script

```bash
# Run the comprehensive installer
python scripts/eigencode_installer.py

# Check installation status
./ai_components/conductor_cli_enhanced.py eigencode status
```

#### Method 2: Manual Installation

1. **Check for Latest Release**
   ```bash
   # Check GitHub releases
   curl -s https://api.github.com/repos/eigencode/eigencode/releases/latest | jq -r '.tag_name'
   ```

2. **Download Binary**
   ```bash
   # Replace VERSION with actual version
   wget https://github.com/eigencode/eigencode/releases/download/VERSION/eigencode-linux-amd64.tar.gz
   tar -xzf eigencode-linux-amd64.tar.gz
   sudo mv eigencode /usr/local/bin/
   sudo chmod +x /usr/local/bin/eigencode
   ```

3. **Verify Installation**
   ```bash
   eigencode version
   ```

#### Method 3: Package Managers

```bash
# Snap (if available)
sudo snap install eigencode

# NPM (if Node.js package exists)
npm install -g eigencode

# Cargo (if Rust package exists)
cargo install eigencode
```

### Configuration

Create configuration file at `~/.eigencode/config.yaml`:

```yaml
# EigenCode Configuration
analysis:
  depth: comprehensive
  parallel_workers: 4
  timeout: 600  # 10 minutes
  
output:
  format: json
  verbose: true
  
integrations:
  conductor:
    enabled: true
    api_endpoint: http://localhost:8080
    
performance:
  cache_enabled: true
  cache_dir: ~/.eigencode/cache
  max_cache_size: 1GB
  
security:
  api_key: ${EIGENCODE_API_KEY}
  verify_ssl: true
```

## Common Issues and Solutions

### Issue 1: 404 Error During Installation

**Problem**: The installer returns a 404 error when trying to download EigenCode.

**Solutions**:

1. **Check Service Status**
   ```bash
   # Test if the service is available
   curl -I https://www.eigencode.dev
   ```

2. **Use Alternative URLs**
   ```bash
   # Try different endpoints
   python scripts/eigencode_installer.py --method github
   python scripts/eigencode_installer.py --method api
   ```

3. **Manual Download**
   - Visit https://www.eigencode.dev/downloads
   - Check GitHub releases: https://github.com/eigencode/eigencode/releases
   - Contact support for direct download link

### Issue 2: Permission Denied

**Problem**: Installation fails with permission errors.

**Solutions**:

```bash
# Create directory with proper permissions
sudo mkdir -p /opt/eigencode
sudo chown $USER:$USER /opt/eigencode

# Install to user directory
export EIGENCODE_HOME=$HOME/.eigencode
mkdir -p $EIGENCODE_HOME/bin
# Add to PATH
echo 'export PATH=$HOME/.eigencode/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Issue 3: Incompatible Architecture

**Problem**: Binary doesn't work on your system architecture.

**Solutions**:

1. **Check System Architecture**
   ```bash
   uname -m
   # Download appropriate version (x86_64, arm64, etc.)
   ```

2. **Build from Source**
   ```bash
   git clone https://github.com/eigencode/eigencode.git
   cd eigencode
   make build
   sudo make install
   ```

### Issue 4: API Connection Failures

**Problem**: EigenCode can't connect to the conductor API.

**Solutions**:

1. **Verify API Endpoint**
   ```bash
   # Test connection
   curl http://localhost:8080/health
   ```

2. **Check Firewall**
   ```bash
   sudo ufw allow 8080/tcp
   ```

3. **Update Configuration**
   ```yaml
   integrations:
     conductor:
       api_endpoint: http://127.0.0.1:8080
       retry_attempts: 3
       timeout: 30
   ```

## Performance Optimization

### 1. Parallel Analysis

Configure EigenCode for parallel processing:

```yaml
analysis:
  parallel_workers: $(nproc)  # Use all CPU cores
  chunk_size: 1000  # Files per chunk
  memory_limit: 4GB
```

### 2. Caching Strategy

Implement intelligent caching:

```python
# ai_components/eigencode/cache_manager.py
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta

class EigenCodeCacheManager:
    def __init__(self, cache_dir="~/.eigencode/cache"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_cache_key(self, file_path: str, options: dict) -> str:
        """Generate cache key based on file and analysis options"""
        content = f"{file_path}:{json.dumps(options, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_cached_result(self, file_path: str, options: dict, max_age_hours=24):
        """Retrieve cached analysis if available and fresh"""
        cache_key = self.get_cache_key(file_path, options)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            # Check age
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime < timedelta(hours=max_age_hours):
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        return None
    
    def cache_result(self, file_path: str, options: dict, result: dict):
        """Cache analysis result"""
        cache_key = self.get_cache_key(file_path, options)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(result, f)
```

### 3. Incremental Analysis

Only analyze changed files:

```python
# ai_components/eigencode/incremental_analyzer.py
import subprocess
from typing import List, Set

class IncrementalAnalyzer:
    def __init__(self, base_commit="HEAD~1"):
        self.base_commit = base_commit
    
    def get_changed_files(self) -> Set[str]:
        """Get list of files changed since base commit"""
        result = subprocess.run(
            ["git", "diff", "--name-only", self.base_commit],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return set(result.stdout.strip().split('\n'))
        return set()
    
    def analyze_incremental(self, eigencode_path: str) -> dict:
        """Run EigenCode only on changed files"""
        changed_files = self.get_changed_files()
        
        if not changed_files:
            return {"status": "no_changes"}
        
        # Create file list
        with open("/tmp/eigencode_files.txt", 'w') as f:
            f.write('\n'.join(changed_files))
        
        # Run analysis
        result = subprocess.run(
            [eigencode_path, "analyze", "--file-list", "/tmp/eigencode_files.txt"],
            capture_output=True,
            text=True
        )
        
        return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}
```

### 4. Resource Limits

Prevent resource exhaustion:

```bash
# Create systemd service with resource limits
cat > /etc/systemd/system/eigencode-analyzer.service << EOF
[Unit]
Description=EigenCode Analyzer Service
After=network.target

[Service]
Type=simple
User=eigencode
WorkingDirectory=/opt/eigencode
ExecStart=/usr/local/bin/eigencode serve
Restart=on-failure
RestartSec=10

# Resource limits
MemoryLimit=2G
CPUQuota=80%
TasksMax=100

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
```

## Security Considerations

### 1. API Key Management

```python
# Secure API key handling
import os
from cryptography.fernet import Fernet

class SecureEigenCodeConfig:
    def __init__(self):
        self.cipher = Fernet(self._get_or_create_key())
    
    def _get_or_create_key(self):
        key_file = Path.home() / ".eigencode" / ".key"
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.parent.mkdir(exist_ok=True)
            key_file.write_bytes(key)
            key_file.chmod(0o600)
            return key
    
    def encrypt_api_key(self, api_key: str) -> str:
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()
```

### 2. Sandboxed Execution

Run EigenCode in a container:

```dockerfile
# Dockerfile.eigencode
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip

# Install EigenCode
RUN curl -fsSL https://www.eigencode.dev/install.sh | bash

# Create non-root user
RUN useradd -m -s /bin/bash eigencode
USER eigencode

WORKDIR /workspace
ENTRYPOINT ["eigencode"]
```

### 3. Network Isolation

```yaml
# docker-compose.yml
version: '3.8'

services:
  eigencode:
    build:
      context: .
      dockerfile: Dockerfile.eigencode
    networks:
      - eigencode_net
    volumes:
      - ./code:/workspace:ro
      - eigencode_cache:/home/eigencode/.eigencode/cache
    environment:
      - EIGENCODE_API_KEY_FILE=/run/secrets/eigencode_key
    secrets:
      - eigencode_key

networks:
  eigencode_net:
    driver: bridge
    internal: true

secrets:
  eigencode_key:
    file: ./secrets/eigencode_api_key.txt

volumes:
  eigencode_cache:
```

## API Integration

### Python Client

```python
# ai_components/eigencode/client.py
import aiohttp
import asyncio
from typing import Dict, Optional

class EigenCodeClient:
    def __init__(self, api_key: str = None, base_url: str = "https://api.eigencode.dev"):
        self.api_key = api_key or os.environ.get('EIGENCODE_API_KEY')
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_codebase(self, path: str, options: Dict = None) -> Dict:
        """Analyze codebase using EigenCode API"""
        async with self.session.post(
            f"{self.base_url}/v1/analyze",
            json={
                "path": path,
                "options": options or {}
            }
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API error: {response.status} - {await response.text()}")
    
    async def get_analysis_status(self, analysis_id: str) -> Dict:
        """Check analysis status"""
        async with self.session.get(
            f"{self.base_url}/v1/analysis/{analysis_id}"
        ) as response:
            return await response.json()
```

### CLI Integration

```python
# ai_components/eigencode/cli_wrapper.py
import subprocess
import json
from typing import Dict, List

class EigenCodeCLI:
    def __init__(self, binary_path: str = "eigencode"):
        self.binary_path = binary_path
    
    def analyze(self, path: str, **kwargs) -> Dict:
        """Run analysis via CLI"""
        cmd = [self.binary_path, "analyze", path]
        
        # Add options
        for key, value in kwargs.items():
            cmd.extend([f"--{key.replace('_', '-')}", str(value)])
        
        # Add JSON output
        cmd.extend(["--output-format", "json"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise Exception(f"EigenCode error: {result.stderr}")
    
    def validate_config(self) -> bool:
        """Validate EigenCode configuration"""
        result = subprocess.run(
            [self.binary_path, "config", "validate"],
            capture_output=True
        )
        return result.returncode == 0
```

## Troubleshooting

### Diagnostic Script

```python
#!/usr/bin/env python3
# scripts/diagnose_eigencode.py

import os
import sys
import subprocess
import json
from pathlib import Path

def diagnose_eigencode():
    """Comprehensive EigenCode diagnostic"""
    diagnostics = {
        "installation": {},
        "configuration": {},
        "connectivity": {},
        "performance": {}
    }
    
    # Check installation
    print("Checking EigenCode installation...")
    
    # Check common paths
    paths = [
        "/usr/local/bin/eigencode",
        "/usr/bin/eigencode",
        os.path.expanduser("~/.eigencode/bin/eigencode"),
        "/opt/eigencode/bin/eigencode"
    ]
    
    found = False
    for path in paths:
        if os.path.exists(path):
            diagnostics["installation"]["path"] = path
            diagnostics["installation"]["found"] = True
            found = True
            
            # Check version
            try:
                result = subprocess.run(
                    [path, "version"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    diagnostics["installation"]["version"] = result.stdout.strip()
            except:
                pass
            break
    
    if not found:
        diagnostics["installation"]["found"] = False
        print("✗ EigenCode not found in standard locations")
    else:
        print(f"✓ EigenCode found at: {diagnostics['installation']['path']}")
    
    # Check configuration
    print("\nChecking configuration...")
    config_path = Path.home() / ".eigencode" / "config.yaml"
    
    if config_path.exists():
        diagnostics["configuration"]["found"] = True
        diagnostics["configuration"]["path"] = str(config_path)
        print(f"✓ Configuration found at: {config_path}")
    else:
        diagnostics["configuration"]["found"] = False
        print("✗ Configuration file not found")
    
    # Check environment variables
    print("\nChecking environment variables...")
    env_vars = ["EIGENCODE_API_KEY", "EIGENCODE_HOME", "EIGENCODE_CONFIG"]
    
    for var in env_vars:
        value = os.environ.get(var)
        diagnostics["configuration"][var] = "set" if value else "not set"
        status = "✓" if value else "✗"
        print(f"{status} {var}: {'set' if value else 'not set'}")
    
    # Check connectivity
    print("\nChecking connectivity...")
    
    # Test API endpoint
    try:
        import requests
        response = requests.get("https://api.eigencode.dev/health", timeout=5)
        diagnostics["connectivity"]["api"] = {
            "reachable": response.status_code == 200,
            "status_code": response.status_code
        }
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} API endpoint: {response.status_code}")
    except Exception as e:
        diagnostics["connectivity"]["api"] = {
            "reachable": False,
            "error": str(e)
        }
        print(f"✗ API endpoint: {e}")
    
    # Save diagnostics
    with open("eigencode_diagnostics.json", 'w') as f:
        json.dump(diagnostics, f, indent=2)
    
    print(f"\nDiagnostics saved to: eigencode_diagnostics.json")
    
    # Provide recommendations
    print("\nRecommendations:")
    
    if not diagnostics["installation"]["found"]:
        print("1. Run: python scripts/eigencode_installer.py")
    
    if not diagnostics["configuration"]["found"]:
        print("2. Create configuration: mkdir -p ~/.eigencode && cp configs/eigencode.yaml ~/.eigencode/config.yaml")
    
    if diagnostics["configuration"].get("EIGENCODE_API_KEY") == "not set":
        print("3. Set API key: export EIGENCODE_API_KEY=your_api_key")
    
    return diagnostics

if __name__ == "__main__":
    diagnose_eigencode()
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `command not found: eigencode` | Not installed or not in PATH | Add to PATH or use full path |
| `API key required` | Missing API key | Set EIGENCODE_API_KEY environment variable |
| `Connection refused` | Service not running | Start EigenCode service |
| `Timeout exceeded` | Large codebase or slow system | Increase timeout in config |
| `Permission denied` | Insufficient permissions | Check file permissions |
| `Out of memory` | Large analysis | Increase memory limit or use incremental analysis |

## Best Practices

### 1. Regular Updates

```bash
# Check for updates
eigencode update check

# Auto-update script
cat > /etc/cron.daily/eigencode-update << 'EOF'
#!/bin/bash
eigencode update --auto --quiet
EOF
chmod +x /etc/cron.daily/eigencode-update
```

### 2. Monitoring Integration

```python
# Add to monitoring stack
class EigenCodeMetrics:
    def __init__(self):
        self.analysis_counter = Counter(
            'eigencode_analyses_total',
            'Total number of analyses performed'
        )
        self.analysis_duration = Histogram(
            'eigencode_analysis_duration_seconds',
            'Analysis duration in seconds'
        )
        self.files_analyzed = Counter(
            'eigencode_files_analyzed_total',
            'Total files analyzed'
        )
```

### 3. Workflow Integration

```yaml
# Example workflow configuration
tasks:
  - id: eigencode_analysis
    name: "Code Analysis with EigenCode"
    agent: analyzer
    inputs:
      tool: eigencode
      options:
        depth: comprehensive
        include_metrics: true
        include_suggestions: true
    timeout: 600
    retry_attempts: 2
```

### 4. Error Recovery

```python
# Graceful fallback when EigenCode is unavailable
async def analyze_with_fallback(path: str) -> Dict:
    try:
        # Try EigenCode first
        return await eigencode_client.analyze_codebase(path)
    except Exception as e:
        logger.warning(f"EigenCode failed: {e}, using fallback")
        
        # Fallback to basic analysis
        return {
            "status": "fallback",
            "basic_metrics": {
                "files": count_files(path),
                "lines": count_lines(path),
                "languages": detect_languages(path)
            }
        }
```

## Conclusion

EigenCode integration enhances the AI conductor with powerful code analysis capabilities. Follow this guide for smooth installation, configuration, and troubleshooting. Regular monitoring and updates ensure optimal performance and reliability.

For additional support:
- Documentation: https://docs.eigencode.dev
- Community: https://community.eigencode.dev
- Support: support@eigencode.dev