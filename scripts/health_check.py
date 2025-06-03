#!/usr/bin/env python3
"""Health check for orchestrator services"""
    "orchestrator": "http://localhost:8002/health",
    "memory": "http://localhost:8003/health",
    "tools": "http://localhost:8006/health",
    "weaviate": "http://localhost:8001/health"
}

all_healthy = True
for name, url in services.items():
    if check_service(name, url):
        print(f"✓ {name}: Healthy")
    else:
        print(f"✗ {name}: Unhealthy")
        all_healthy = False

sys.exit(0 if all_healthy else 1)
