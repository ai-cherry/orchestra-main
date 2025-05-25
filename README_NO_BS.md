# Orchestra AI - No Bullshit Guide

## One-Time Setup (2 minutes)

```bash
# 1. Clone repo
git clone [YOUR_REPO_URL]
cd orchestra-main

# 2. Build Docker containers
docker compose build

# 3. Start all services
./start.sh up

# That's it. Everything is installed and running inside Docker containers.
```

## Daily Use

```bash
# Get into your dev environment
./start.sh shell

# You're now inside Docker. Run stuff:
run-api      # Start API server
run-ui       # Start Admin UI  
run-tests    # Run tests
fix-format   # Format code
```

## Deploy

```bash
# Just push to main
git push origin main

# GitHub Actions handles the rest
```

## If Shit Breaks

```bash
# Nuclear reset
./start.sh clean
./start.sh up
./start.sh shell
```

## Architecture

- **Everything runs in Docker** - No local Python bullshit
- **Poetry manages dependencies** - Inside container only
- **One service account key** - `service-account-key.json`
- **Push to deploy** - CI/CD is automatic

## Services

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Admin UI | http://localhost:3001 |
| Redis | localhost:6379 |
| PostgreSQL | localhost:5432 |

## That's It

No more setup. No more auth hell. No more dependency conflicts.

Just code. 