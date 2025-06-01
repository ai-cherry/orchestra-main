# Development on Vultr Server

## Quick Start
```bash
# SSH to Vultr production server
ssh -i ~/.ssh/vultr_orchestra root@45.32.69.157

# For development, use screen/tmux
screen -S dev

# Edit code
cd /root/orchestra-main
vim agent/app/services/real_agents.py

# Test changes locally
source venv/bin/activate
python -m agent.app.main  # Runs on port 8080

# Deploy changes
git add -A && git commit -m "Your changes"
git push origin main
systemctl restart orchestra-api  # or whatever service name

# Detach from screen: Ctrl+A, D
# Reattach: screen -r dev
```

## Benefits
- No confusion about which server
- Changes tested in production environment
- Instant deployment (just restart service)
- Same Python version, dependencies, OS

## Port Usage
- Production API: 8000
- Development/testing: 8001 or 8080
- Admin UI: served by nginx on 80/443

## Best Practices
1. Always use screen/tmux for long sessions
2. Test on different port before deploying
3. Use git branches for major changes
4. Keep production service running while developing

## Automated Provisioning
Use `scripts/vultr_provision.py` to spin up a fresh Vultr VM and attach block storage.

```bash
export VULTR_API_KEY=your-api-key
python scripts/vultr_provision.py --region ewr --plan vc2-1c-2gb --os 215 \
    --label orchestra-dev --ssh-key <key_id> --volume <volume_id>
```

The script interacts with the Vultr API to create the server and optionally attach an existing volume.
