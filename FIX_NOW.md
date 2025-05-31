# 🚨 FIX YOUR WEBSITE - GET REAL AGENTS WORKING

## THE PROBLEM
Your website at https://cherry-ai.me is showing MOCK data from the OLD installation at `/opt/orchestra`

## THE SOLUTION
You have REAL working agents at `/root/orchestra-main` - just need to switch!

## MANUAL STEPS (Copy & Paste)

1. **SSH to your server:**
```bash
ssh root@45.32.69.157
# Password: z+G3D,$n9M3.=Dr}
```

2. **Run these commands:**
```bash
# Stop ALL old APIs
pkill -f uvicorn
pkill -f agent.app.main
sleep 3

# Go to the REAL installation
cd /root/orchestra-main
source venv/bin/activate

# Start the REAL API
nohup python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000 > /root/api_real.log 2>&1 &
sleep 5

# Verify it's working
curl -X GET 'http://localhost:8000/api/agents' -H 'X-API-Key: 4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd' | jq '.'
```

## WHAT YOU'LL SEE

Instead of:
- agent-001, agent-002, etc (MOCK)

You'll see:
- **sys-001**: System Monitor (REAL CPU monitoring)
- **analyze-001**: Data Analyzer (REAL data analysis)
- **monitor-001**: Service Monitor (REAL service checks)

## TEST IT

Go to https://cherry-ai.me and try:
- "Check CPU usage" - will show REAL server CPU%
- "Check memory status" - will show REAL memory usage
- "Analyze this data" - will do REAL analysis

## PERMANENT FIX

To make it start on reboot:
```bash
# Disable old service
systemctl stop orchestra-api
systemctl disable orchestra-api

# Create new service
cat > /etc/systemd/system/orchestra-real.service << 'EOF'
[Unit]
Description=Orchestra AI Real Agents
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/orchestra-main
Environment="PATH=/root/orchestra-main/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/root/orchestra-main/venv/bin/python -m uvicorn agent.app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable orchestra-real
systemctl start orchestra-real
```

## 🎉 YOUR REAL AI SYSTEM IS READY - JUST NEEDS TO BE STARTED!
