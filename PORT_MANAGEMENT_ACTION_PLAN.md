# 🎯 Orchestra AI Port Management Action Plan

## 🚨 Current Situation

**7 out of 14 critical services have port conflicts**, preventing full deployment of the Orchestra AI system. All conflicts are with existing Docker containers that have been running for 6+ days.

## 📋 Immediate Actions (Do Now)

### Option 1: Quick Fix - Use Alternative Ports (Recommended)
```bash
# 1. Generate environment with alternative ports
python3 port_manager.py allocate --service postgres --port 5433
python3 port_manager.py allocate --service redis --port 6380
python3 port_manager.py allocate --service weaviate --port 8081
python3 port_manager.py allocate --service api --port 8010
python3 port_manager.py allocate --service admin_ui --port 3002
python3 port_manager.py allocate --service grafana --port 3003
python3 port_manager.py allocate --service prometheus --port 9091

# 2. Generate new environment file
python3 port_manager.py env > .env.ports

# 3. Generate docker-compose override
python3 port_manager.py override > docker-compose.override.yml

# 4. Deploy with new ports
docker-compose -f docker-compose.production.yml -f docker-compose.override.yml up -d
```

### Option 2: Stop Existing Services
```bash
# Stop all existing orchestra containers
docker stop orchestra-main-2-api-1 orchestra-main-2-db-1 orchestra-main-2-redis-1 \
  orchestra-main-2-admin-1 orchestra-main-2-prometheus-1 orchestra-main-2-grafana-1

# Kill the Python process on 8080
kill -9 41761

# Now deploy fresh
./deploy_production_complete.sh --mode=hybrid
```

### Option 3: Hybrid Mode with Port Separation
```bash
# Set hybrid mode to separate Docker and MCP services
export DEPLOYMENT_MODE=hybrid
export DOCKER_API_PORT=8010
export MCP_UNIFIED_PORT=8000

# Deploy
./deploy_production_complete.sh --mode=hybrid --verify
```

## 🛠️ Best Practices Implementation

### 1. **Environment-Based Port Configuration**
Create separate environment files for each deployment scenario:

```bash
# .env.production
POSTGRES_PORT=5432
REDIS_PORT=6379
WEAVIATE_PORT=8080
API_PORT=8000

# .env.development
POSTGRES_PORT=5433
REDIS_PORT=6380
WEAVIATE_PORT=8081
API_PORT=8010

# .env.staging
POSTGRES_PORT=5434
REDIS_PORT=6381
WEAVIATE_PORT=8082
API_PORT=8020
```

### 2. **Automated Port Management**
Integrate port checking into deployment scripts:

```bash
#!/bin/bash
# deploy_with_port_check.sh

# Check ports before deployment
if ! ./check_ports.sh; then
    echo "Port conflicts detected. Attempting automatic resolution..."
    
    # Use port manager to allocate alternative ports
    python3 port_manager.py check
    python3 port_manager.py override > docker-compose.override.yml
    
    echo "Using alternative ports via docker-compose.override.yml"
fi

# Continue with deployment
docker-compose -f docker-compose.production.yml -f docker-compose.override.yml up -d
```

### 3. **Service Discovery**
Implement dynamic port discovery for services:

```python
# service_discovery.py
import os
from port_manager import PortManager

class ServiceDiscovery:
    def __init__(self):
        self.pm = PortManager()
    
    def get_service_url(self, service_name: str) -> str:
        """Get the URL for a service with dynamic port"""
        port = self.pm.get_service_port(service_name)
        if not port:
            # Allocate port if not already done
            port, _ = self.pm.allocate_port(service_name)
        
        host = os.getenv('SERVICE_HOST', 'localhost')
        return f"http://{host}:{port}"
    
    def get_all_services(self) -> dict:
        """Get all service URLs"""
        return {
            'postgres': self.get_service_url('postgres'),
            'redis': self.get_service_url('redis'),
            'api': self.get_service_url('api'),
            'weaviate': self.get_service_url('weaviate'),
        }
```

## 📊 Port Allocation Standards

### **Reserved Port Ranges by Service Type**
```
System Services:     1-1023    (Requires root)
User Services:       1024-4999 (General applications)
Database Services:   5000-5999 (PostgreSQL, MySQL, etc.)
Cache Services:      6000-6999 (Redis, Memcached, etc.)
Custom Services:     7000-7999 (Application-specific)
API Services:        8000-8999 (REST APIs, GraphQL, etc.)
Monitoring:          9000-9999 (Prometheus, Grafana, etc.)
Dynamic Allocation:  10000+    (Temporary services)
```

### **Standard Port Assignments**
```yaml
# Primary Services (Production)
postgres: 5432
redis: 6379
weaviate: 8080
api: 8000
nginx_http: 80
nginx_https: 443

# Alternative Ports (Development/Staging)
postgres_dev: 5433
redis_dev: 6380
weaviate_dev: 8081
api_dev: 8010

# MCP Services
mcp_conductor: 8002
mcp_memory: 8003
mcp_tools: 8006
mcp_weaviate: 8001

# Monitoring
prometheus: 9090
grafana: 3001
```

## 🔄 Migration Steps

### Phase 1: Immediate (Today)
1. ✅ Run `./check_ports.sh` to identify conflicts
2. ✅ Use `port_manager.py` to allocate alternative ports
3. ⬜ Deploy services with new port configuration
4. ⬜ Update documentation with new ports

### Phase 2: Short-term (This Week)
1. ⬜ Implement automated port checking in CI/CD
2. ⬜ Create staging environment with separate ports
3. ⬜ Add port monitoring to Prometheus
4. ⬜ Create Grafana dashboard for port usage

### Phase 3: Long-term (This Month)
1. ⬜ Implement service mesh for dynamic routing
2. ⬜ Add Consul/etcd for service discovery
3. ⬜ Create blue-green deployment with port switching
4. ⬜ Implement automatic port conflict resolution

## 🚀 Quick Start Commands

```bash
# 1. Check current port status
python3 port_manager.py status

# 2. Check for conflicts
./check_ports.sh

# 3. Allocate all ports automatically
for service in postgres redis weaviate api admin_ui grafana prometheus; do
    python3 port_manager.py allocate --service $service
done

# 4. Generate configuration files
python3 port_manager.py env > .env.ports
python3 port_manager.py override > docker-compose.override.yml

# 5. Deploy with new configuration
source .env.ports
docker-compose -f docker-compose.production.yml -f docker-compose.override.yml up -d

# 6. Verify deployment
./verify_deployment_status.sh
```

## 📝 Configuration Files to Update

1. **`.env`** - Add port variables
2. **`docker-compose.production.yml`** - Use environment variables for ports
3. **`nginx.conf`** - Update upstream server ports
4. **Application configs** - Update database/cache connection strings
5. **Monitoring configs** - Update scrape targets

## 🎯 Success Criteria

- [ ] All services deployed without port conflicts
- [ ] Port allocation documented in `port_config.json`
- [ ] Health checks passing on all services
- [ ] Monitoring dashboard shows all services green
- [ ] No manual port configuration required for new deployments

## 🔍 Troubleshooting

### Common Issues:
1. **"Address already in use"** - Use `lsof -i :PORT` to find process
2. **"Connection refused"** - Check if service is using correct port
3. **"Cannot bind to port"** - Check permissions (ports < 1024 need root)
4. **Docker port mapping issues** - Ensure format is `HOST:CONTAINER`

### Debug Commands:
```bash
# Check what's using a port
lsof -i :8000

# Check Docker port mappings
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Test port connectivity
nc -zv localhost 8000

# Check firewall rules
sudo iptables -L -n | grep 8000
```

## 📚 References

- [PORT_ALLOCATION_STRATEGY.md](./PORT_ALLOCATION_STRATEGY.md) - Detailed port strategy
- [check_ports.sh](./check_ports.sh) - Port checking script
- [port_manager.py](./port_manager.py) - Port management utility
- [Docker Networking Guide](https://docs.docker.com/network/)

---

**Action Plan Created**: December 12, 2024  
**Priority**: 🔴 HIGH - Blocking deployment  
**Estimated Time**: 30 minutes for quick fix, 2 hours for full implementation 