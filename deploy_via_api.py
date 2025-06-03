#!/usr/bin/env python3
"""Deploy real agents by creating files directly on the server."""
print("🚀 Deploying REAL agents via API...")

# Read the real agent files
files_to_deploy = {
    "agent/app/services/real_agents.py": open("agent/app/services/real_agents.py").read(),
    "agent/app/services/__init__.py": open("agent/app/services/__init__.py").read(),
    "agent/app/routers/admin.py": open("agent/app/routers/admin.py").read(),
    "test_real_agents.py": open("test_real_agents.py").read(),
}

# Create deployment script
deploy_script = """
pkill -f "uvicorn agent.app.main" || true
sleep 2

# Install psutil
source venv/bin/activate
pip install psutil

# Test the agents
python test_real_agents.py

# Start new API
nohup python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8080 > /root/api_real.log 2>&1 &
sleep 3

# Test it's working
curl -X GET "http://localhost:8080/api/agents" -H "X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd" | jq '.'
"""
    real_agents=files_to_deploy["agent/app/services/real_agents.py"],
    services_init=files_to_deploy["agent/app/services/__init__.py"],
    admin_router=files_to_deploy["agent/app/routers/admin.py"],
    test_script=files_to_deploy["test_real_agents.py"],
)

# Save deployment script
with open("deploy_on_server.sh", "w") as f:
    f.write(deploy_script)

print("✅ Deployment script created: deploy_on_server.sh")
print("")
print("📋 Manual deployment steps:")
print("1. Copy this entire script to your clipboard")
print("2. SSH to your server: ssh root@45.32.69.157")
print("3. Create the script: nano /tmp/deploy_real_agents.sh")
print("4. Paste the content and save (Ctrl+X, Y, Enter)")
print("5. Run it: bash /tmp/deploy_real_agents.sh")
print("")
print("Or use the web terminal at https://my.vultr.com/")
