# Vultr Development Migration Plan

## Current Situation
- **Development**: Paperspace (64.62.255.67)
- **Production**: Vultr (45.32.69.157)
- **Issues**: Confusion, duplicate work, authentication complexity

## Benefits of Migration
1. **Single server** - Reduce costs and complexity
2. **Same environment** - Dev/prod parity
3. **Simplified auth** - One set of SSH keys/passwords
4. **Easier deployment** - Just pull and restart locally
5. **No more "wrong server" issues**

## Migration Steps

### 1. Backup Paperspace Data
```bash
# On Paperspace
tar -czf orchestra-dev-backup.tar.gz \
  ~/orchestra-main/.env \
  ~/orchestra-main/venv \
  ~/orchestra-main/.secrets \
  ~/.ssh/vultr_orchestra*
```

### 2. Setup Dev Environment on Vultr
```bash
# Create dev user on Vultr
ssh root@45.32.69.157
useradd -m -s /bin/bash dev
usermod -aG sudo dev
```

### 3. Clone Dev Setup
```bash
# As dev user
cd /home/dev
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main
python3 -m venv venv
source venv/bin/activate
pip install -r requirements/production/requirements.txt
```

### 4. Configure Dev Ports
- Dev backend: Port 8001
- Prod backend: Port 8000
- This allows both to run simultaneously

### 5. Update GitHub Actions
- Use Vultr server for both dev and prod deployments
- Different directories: `/home/dev/orchestra-main` vs `/root/orchestra-main`

## Alternative: Docker-based Separation
If you prefer to keep some separation:
```yaml
# docker-compose.yml
version: '3.8'
services:
  dev:
    build: .
    ports:
      - "8001:8000"
    volumes:
      - ./:/app
    environment:
      - ENV=development

  prod:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
```

## Recommendation
**Migrate to Vultr with user-based separation**:
- `root` user for production
- `dev` user for development
- Same server, different environments
- Shared nginx can route based on subdomain:
  - `cherry-ai.me` → Production
  - `dev.cherry-ai.me` → Development
