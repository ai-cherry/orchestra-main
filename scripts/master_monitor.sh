#!/bin/bash
# Master monitoring script that ensures EVERYTHING is always running

while true; do
    # Check Docker services
    if ! docker ps | grep -q "cherry_ai_postgres"; then
        docker-compose -f /root/orchestra-main/docker-compose.production.yml up -d
    fi
    
    # Check MCP servers
    for server in memory tools code_intelligence git_intelligence; do
        if ! pgrep -f "${server}_server.py" > /dev/null; then
            cd /root/orchestra-main && nohup python3 -m mcp_server.servers.${server}_server > /var/log/mcp_${server}.log 2>&1 &
        fi
    done
    
    # Check website
    if ! curl -s http://localhost > /dev/null; then
        systemctl restart cherry-ai-web.service
    fi
    
    # Check nginx
    if ! systemctl is-active nginx > /dev/null; then
        systemctl start nginx
    fi
    
    sleep 30
done
