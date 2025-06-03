#!/bin/bash
cd /root/orchestra-main
git pull origin main
docker-compose build
docker-compose down
docker-compose up -d
echo "✅ Deployment complete! Check https://cherry-ai.me"
