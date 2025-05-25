# 🚨 FIX PYTHON/NPM ISSUES ONCE AND FOR ALL

## THE PERMANENT FIX - FOLLOW THESE STEPS

### 1. STOP AND READ THIS FIRST
- **Python Version**: We use **Python 3.10** (NOT 3.11!)
- **Package Manager**: We use **pip/venv** (NOT Docker, NOT Poetry!)
- **Node Version**: We use **Node 18+ with NPM 9+**

### 2. COMPLETE RESET (Nuclear Option)
If you're having issues, do this COMPLETE RESET:

```bash
# 1. Exit any virtual environment
deactivate

# 2. Remove old virtual environment
rm -rf venv

# 3. Create fresh virtual environment with Python 3.10
python3.10 -m venv venv

# 4. Activate it
source venv/bin/activate

# 5. Upgrade pip
pip install --upgrade pip

# 6. Install fixed requirements
pip install -r requirements/base.txt
```

### 3. CHECK EVERYTHING
```bash
# Run our validator
python scripts/validate_environment.py

# Should show:
# ✅ Python version OK: 3.10
# ✅ Virtual environment active
# ✅ Node.js installed
# ✅ NPM installed
```

### 4. COMMON FIXES

#### Python Version Error:
```bash
# Install Python 3.10 if needed
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```

#### NPM/Node Issues:
```bash
# Install Node 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Dependency Conflicts:
```bash
# Clear pip cache
pip cache purge

# Reinstall everything
pip install --force-reinstall -r requirements/base.txt
```

### 5. DAILY WORKFLOW
```bash
# ALWAYS start with this:
cd ~/orchestra-main
source venv/bin/activate
python scripts/validate_environment.py

# If all green, you're good to go!
```

### 6. PROJECT RULES - NEVER BREAK THESE
1. **NO DOCKER** - We don't use it, don't suggest it
2. **NO POETRY** - We use pip/venv only
3. **Python 3.10** - Not 3.11, not 3.12, just 3.10
4. **Check existing tools first** - Don't recreate what exists

### 7. IF SOMEONE TELLS YOU TO UPGRADE
- **DON'T** upgrade to Python 3.11
- **DON'T** switch to Docker
- **DON'T** use Poetry
- **DO** point them to `.python-version-lock` file

### 8. THE GOLDEN COMMANDS
```bash
# Setup from scratch
chmod +x setup_environment.sh
./setup_environment.sh

# Daily check
source venv/bin/activate
python scripts/validate_environment.py

# Fix dependencies
pip install -r requirements/base.txt
```

## REMEMBER
This project values:
- **Simple > Complex**
- **Existing tools > New tools**
- **Python 3.10 > Python 3.11**
- **pip/venv > Docker/Poetry**

---
**LAST UPDATED**: 2024-01-25
**STANDARDIZED ON**: Python 3.10 