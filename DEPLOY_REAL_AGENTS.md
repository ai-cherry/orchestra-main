# 🚀 Deploy REAL Orchestra AI Agents

Your REAL agents are ready! They actually:
- Monitor CPU, memory, disk usage
- Analyze data
- Check service status

## Quick Deploy Instructions

1. **Upload the package to your server:**
```bash
scp real_agents_deploy.tar.gz root@45.32.69.157:/root/
```

2. **SSH to your server:**
```bash
ssh root@45.32.69.157
```

3. **Run these commands on the server:**
```bash
cd /root/orchestra-main

# Extract the files
tar -xzf /root/real_agents_deploy.tar.gz

# Kill old API
pkill -f "uvicorn agent.app.main"
sleep 2

# Install psutil
source venv/bin/activate
pip install psutil

# Test the agents work
python test_real_agents.py

# Start the REAL API
nohup python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8080 > /root/api_real.log 2>&1 &
sleep 3

# Verify it's working
curl -X GET "http://localhost:8080/api/agents" \
     -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" | jq '.'
```

## What You'll See

Instead of mock data, you'll see REAL agents:
- `sys-001`: System Monitor - checks CPU, memory, disk
- `analyze-001`: Data Analyzer - analyzes data
- `monitor-001`: Service Monitor - monitors services

## Test Commands in the UI

Try these in the query box at https://cherry-ai.me:
- "Check CPU usage"
- "Check memory status"
- "Monitor system"
- "Analyze this data"

The agents will ACTUALLY run these tasks and return REAL results!

## Files Included

- `agent/app/routers/admin.py` - Updated API endpoints
- `agent/app/services/real_agents.py` - Real agent implementation
- `agent/app/services/__init__.py` - Package init
- `test_real_agents.py` - Test script to verify agents work
