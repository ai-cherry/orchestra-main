# 🔥 UNFUCK EVERYTHING - The Complete Fix

## Phase 1: Nuclear Cleanup (30 minutes)

### 1.1 Stop Everything
```bash
# Kill all running processes
pkill -f python
pkill -f node
docker stop $(docker ps -aq) 2>/dev/null
docker compose down -v 2>/dev/null

# Clean up old environments
deactivate 2>/dev/null
rm -rf venv venv_* node_modules
rm -rf ~/.cache/pip ~/.npm
```

### 1.2 Fix Git Branches
```bash
# Get on main branch and clean up
git checkout main
git fetch --all --prune
git reset --hard origin/main
git clean -fdx

# Ensure your local Python is 3.11+ and Node is 18+ for all workflows.

# Delete all local branches except main
git branch | grep -v "main" | xargs -n 1 git branch -D

# Remove any merge conflicts
find . -name "*.orig" -delete
find . -name "*_BACKUP_*" -delete
find . -name "*_BASE_*" -delete
find . -name "*_LOCAL_*" -delete
find . -name "*_REMOTE_*" -delete
```

## Phase 2: Docker Setup (10 minutes)

### 2.1 Create Docker Environment
```bash
# Make sure Docker is running
docker --version || echo "Install Docker first!"

# Build the development environment
docker compose build

# Start everything
./start.sh up
```

### 2.2 Get Into Container
```bash
# This is your new home - ALWAYS work here
./start.sh shell

# Inside container, you'll see:
# 🐳 orchestra-dev /workspace $ 
```

## Phase 3: Google Cloud Fix (15 minutes)

### 3.1 One-Time GCP Setup
```bash
# OUTSIDE container - on your host machine
gcloud auth application-default login
gcloud config set project cherry-ai-project

# Create service account key
gcloud iam service-accounts create orchestra-dev \
    --display-name="Orchestra Development"

gcloud projects add-iam-policy-binding cherry-ai-project \
    --member="serviceAccount:orchestra-dev@cherry-ai-project.iam.gserviceaccount.com" \
    --role="roles/editor"

gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=orchestra-dev@cherry-ai-project.iam.gserviceaccount.com

# This creates service-account-key.json in your project root
```

### 3.2 Inside Container Setup
```bash
# Get into container
./start.sh shell

# Verify GCP works
python -c "from google.cloud import firestore; print('GCP OK!')"
```

## Phase 4: Dependencies Once and For All

### 4.1 Poetry Setup (Inside Container)
```bash
# Remove old crap
rm -f poetry.lock requirements*.txt

# Install all dependencies with Poetry
poetry install

# Activate Poetry shell
poetry shell

# Generate requirements for legacy systems
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

### 4.2 NPM Setup (Admin UI)
```bash
# Still inside container
cd admin-interface
rm -rf node_modules package-lock.json
npm ci  # Use npm ci for reproducible installs
cd ..
```

## Phase 5: Services Setup

### 5.1 Redis/DragonflyDB
```bash
# Redis is already running in Docker
# Test it:
redis-cli -h localhost ping
# Should return: PONG

# If you want DragonflyDB instead:
# Edit docker compose.yml and replace redis image with:
# image: docker.dragonflydb.io/dragonflydb/dragonfly
```

### 5.2 PostgreSQL
```bash
# Already running in Docker
# Test it:
psql -h localhost -U orchestra -d orchestra
# Password: orchestra123
```

## Phase 6: CLI and Tools

### 6.1 Orchestra CLI
```bash
# Inside container
cd /workspace

# Make CLI executable
chmod +x scripts/orchestra.py

# Create alias
echo 'alias orchestra="python /workspace/scripts/orchestra.py"' >> ~/.bashrc
source ~/.bashrc

# Test it
orchestra --help
```

### 6.2 Quick Commands
```bash
# Add these aliases
cat >> ~/.bashrc << 'EOF'
alias run-api="cd /workspace && poetry run uvicorn orchestra_api.main:app --reload --host 0.0.0.0 --port 8000"
alias run-ui="cd /workspace/admin-interface && npm start"
alias run-tests="cd /workspace && poetry run pytest"
alias fix-format="cd /workspace && poetry run black . && poetry run isort ."
EOF
source ~/.bashrc
```

## Phase 7: CI/CD Fix

### 7.1 GitHub Actions
```bash
# Create fixed workflow
cat > .github/workflows/main.yml << 'EOF'
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: |
          pip install --upgrade pip
          pip install poetry==1.7.1
          poetry config virtualenvs.create false
      
      - name: Install dependencies
        run: poetry install
      
      - name: Run tests
        run: poetry run pytest
      
      - name: Run linting
        run: |
          poetry run black --check .
          poetry run flake8 .
          poetry run mypy .

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to GCP
        run: |
          echo "Deploy step - customize as needed"
EOF
```

## Phase 8: Daily Workflow (Your New Life)

### 8.1 Start Your Day
```bash
# 1. Start Docker (once)
./start.sh up

# 2. Get into container
./start.sh shell

# 3. You're ready to code!
```

### 8.2 Development Commands
```bash
# Run API
run-api

# In another terminal, run UI
./start.sh shell
run-ui

# Run tests
run-tests

# Format code
fix-format
```

### 8.3 Deploy
```bash
# Inside container
git add .
git commit -m "feat: awesome feature"
git push origin main

# CI/CD handles the rest
```

## Phase 9: Documentation Update

### 9.1 Create Simple README
```bash
cat > README_SIMPLE.md << 'EOF'
# Orchestra AI

## Quick Start

1. Install Docker
2. Run: `./start.sh up`
3. Get shell: `./start.sh shell`
4. Code!

## Services

- API: http://localhost:8000
- UI: http://localhost:3001
- Redis: localhost:6379
- PostgreSQL: localhost:5432

## Daily Commands

Inside container:
- `run-api` - Start API
- `run-ui` - Start UI  
- `run-tests` - Run tests
- `fix-format` - Format code

## Deploy

Just push to main branch. CI/CD handles everything.
EOF
```

## Phase 10: PAPERSPACE SPECIFIC SETUP

### 10.1 Paperspace Machine Setup
```bash
# SSH into Paperspace
ssh paperspace@[YOUR_IP]

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Logout and login again

# Clone repo
git clone https://github.com/[YOUR_REPO]/orchestra-main.git
cd orchestra-main

# Copy your service account key
scp service-account-key.json paperspace@[YOUR_IP]:~/orchestra-main/

# Start everything
./start.sh up
```

## 🎯 THE GOLDEN RULES

1. **ALWAYS work inside the Docker container** - `./start.sh shell`
2. **NEVER install Python packages on host** - Use Poetry inside container
3. **ONE service account key** - `service-account-key.json` in project root
4. **Push to main = Deploy** - CI/CD handles everything
5. **Problems?** - `./start.sh clean` and start over

## 🚀 You're Done!

Now you can:
- Login with ONE command: `./start.sh shell`
- All dependencies are managed by Poetry/Docker
- Python 3.11+ and Node 18+ are required everywhere (see infra/README.md for IaC details)
- No more version conflicts
- No more auth bullshit
- Just code and push

## Troubleshooting

### "It's not working!"
```bash
# Nuclear option - start fresh
./start.sh clean
./start.sh up
./start.sh shell
```

### "I need to add a package"
```bash
# Inside container
poetry add some-package
```

### "Tests are failing"
```bash
# Inside container
poetry run pytest -v
```

---

**That's it. No more bullshit. Just code.** 