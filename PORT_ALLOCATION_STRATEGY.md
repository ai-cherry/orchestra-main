# 🔌 Orchestra AI Port Allocation Strategy & Best Practices

## 📊 Current Port Usage Analysis

### **Production Services (docker-compose.production.yml)**
| Service | Internal Port | External Port | Protocol | Purpose |
|---------|--------------|---------------|----------|---------|
| **PostgreSQL** | 5432 | 5432 | TCP | Primary database |
| **Redis** | 6379 | 6379 | TCP | Cache & session storage |
| **Weaviate** | 8080 | 8080 | HTTP | Vector database |
| **API Server** | 8000 | 8000 | HTTP | Main Orchestra API |
| **Nginx** | 80/443 | 80/443 | HTTP/HTTPS | Reverse proxy & SSL |
| **Fluentd** | 24224 | 24224 | TCP/UDP | Log aggregation |

### **MCP Services (from deploy_production_complete.sh)**
| Service | Port | Purpose | Mode |
|---------|------|---------|------|
| **MCP Unified (Personas)** | 8000 | AI Personas API | MCP-only/Hybrid |
| **MCP Conductor** | 8002 | Orchestration service | All modes |
| **MCP Memory** | 8003 | Memory management | All modes |
| **MCP Tools** | 8006 | Tool coordination | All modes |
| **MCP Weaviate Bridge** | 8001 | Vector DB bridge | All modes |
| **Docker API (Hybrid)** | 8010 | Main API (when MCP on 8000) | Hybrid mode |

### **Remote Services (Lambda Labs)**
| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Zapier MCP** | 80 | 192.9.142.8:80 | Zapier integration |
| **Personas API** | 8000 | 192.9.142.8:8000 | Remote personas |
| **Main API** | 8010 | 192.9.142.8:8010 | Remote main API |
| **Infrastructure** | 8080 | 192.9.142.8:8080 | Remote Weaviate |

### **Development & Monitoring**
| Service | Port | Purpose |
|---------|------|---------|
| **Admin Interface** | 3000 | React development server |
| **Grafana** | 3001 | Metrics visualization |
| **Prometheus** | 9090 | Metrics collection |
| **Loki** | 3100 | Log aggregation |

## 🚨 Identified Port Conflicts

### **Critical Conflicts**
1. **Port 8000**: 
   - Docker API Server (docker-compose.production.yml)
   - MCP Unified/Personas (hybrid mode)
   - **Resolution**: Use deployment modes (docker-only, mcp-only, hybrid)

2. **Port 8080**:
   - Weaviate (docker-compose.production.yml)
   - Infrastructure services
   - **Resolution**: Ensure only one Weaviate instance runs

3. **Port 3000**:
   - Admin Interface development
   - Grafana (mapped to 3001 externally)
   - **Resolution**: Already resolved with port mapping

## 🎯 Best Practices Port Allocation Strategy

### **Port Range Allocation**
```
1000-1999: Reserved for system services
2000-2999: Reserved for development tools
3000-3999: Frontend applications
4000-4999: Reserved for future microservices
5000-5999: Database services
6000-6999: Cache and message queue services
7000-7999: Reserved for custom protocols
8000-8999: API and web services
9000-9999: Monitoring and metrics
10000+:    Dynamic/temporary services
```

### **Recommended Port Assignments**

#### **Core Infrastructure (5000-6999)**
```
5432: PostgreSQL (Primary)
5433: PostgreSQL (Replica/Dev)
6379: Redis (Primary)
6380: Redis (Replica)
6381: Redis (Sessions)
```

#### **API Services (8000-8999)**
```
8000: Primary API Gateway
8001: MCP Weaviate Bridge
8002: MCP Conductor
8003: MCP Memory Service
8004: Reserved for Auth Service
8005: Reserved for Notification Service
8006: MCP Tools Service
8007: Reserved for Search Service
8008: Reserved for Analytics Service
8009: Reserved for Webhook Service
8010: Secondary API (Hybrid mode)
8080: Weaviate Vector DB
```

#### **Frontend & UI (3000-3999)**
```
3000: Primary Frontend (Dev)
3001: Grafana Dashboard
3002: Admin Dashboard (Dev)
3003: Mobile API Gateway
3004-3009: Reserved for additional UIs
```

#### **Monitoring & Observability (9000-9999)**
```
9090: Prometheus
9091: Prometheus Pushgateway
9092: Reserved for Jaeger
9093: Reserved for Zipkin
9100: Node Exporter
9200: Reserved for ElasticSearch
```

## 🛠️ Implementation Strategy

### **1. Environment-Based Configuration**
```bash
# .env.production
POSTGRES_PORT=5432
REDIS_PORT=6379
WEAVIATE_PORT=8080
API_PORT=8000
MCP_UNIFIED_PORT=8000
MCP_CONDUCTOR_PORT=8002
MCP_MEMORY_PORT=8003
MCP_TOOLS_PORT=8006

# .env.development
POSTGRES_PORT=5433
REDIS_PORT=6380
WEAVIATE_PORT=8081
API_PORT=8010
```

### **2. Port Conflict Resolution Script**
```bash
#!/bin/bash
# check_ports.sh

check_port() {
    local port=$1
    local service=$2
    
    if lsof -i :$port >/dev/null 2>&1; then
        echo "❌ Port $port is in use (expected: $service)"
        lsof -i :$port | grep LISTEN
        return 1
    else
        echo "✅ Port $port is available for $service"
        return 0
    fi
}

# Check all critical ports
check_port 5432 "PostgreSQL"
check_port 6379 "Redis"
check_port 8000 "API/MCP"
check_port 8080 "Weaviate"
```

### **3. Dynamic Port Assignment**
```python
# port_manager.py
import socket
from typing import Dict, Optional

class PortManager:
    """Manages port allocation for Orchestra AI services"""
    
    # Base port assignments
    BASE_PORTS = {
        'postgres': 5432,
        'redis': 6379,
        'api': 8000,
        'weaviate': 8080,
        'mcp_conductor': 8002,
        'mcp_memory': 8003,
        'mcp_tools': 8006,
    }
    
    @staticmethod
    def is_port_available(port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False
    
    @classmethod
    def get_available_port(cls, service: str, offset: int = 0) -> Optional[int]:
        """Get an available port for a service"""
        base_port = cls.BASE_PORTS.get(service, 8000)
        
        for i in range(10):  # Try up to 10 ports
            port = base_port + offset + i
            if cls.is_port_available(port):
                return port
        
        return None
    
    @classmethod
    def generate_port_config(cls, environment: str = 'production') -> Dict[str, int]:
        """Generate port configuration for an environment"""
        offset = 0 if environment == 'production' else 1000
        
        config = {}
        for service, base_port in cls.BASE_PORTS.items():
            port = cls.get_available_port(service, offset)
            if port:
                config[f"{service.upper()}_PORT"] = port
            else:
                raise RuntimeError(f"No available port for {service}")
        
        return config
```

### **4. Docker Compose Override Strategy**
```yaml
# docker-compose.override.yml (for development)
services:
  postgres:
    ports:
      - "5433:5432"  # Different external port
  
  redis:
    ports:
      - "6380:6379"  # Different external port
  
  api:
    ports:
      - "8010:8000"  # Different external port
```

## 📋 Port Management Checklist

### **Before Deployment**
- [ ] Run `check_ports.sh` to verify port availability
- [ ] Review `.env` file for correct port assignments
- [ ] Check for duplicate port mappings in docker-compose files
- [ ] Verify no services are hardcoding ports

### **During Deployment**
- [ ] Monitor port binding errors in logs
- [ ] Use `docker ps` to verify actual port mappings
- [ ] Test service connectivity on assigned ports
- [ ] Document any port changes

### **After Deployment**
- [ ] Update firewall rules for new ports
- [ ] Update monitoring configuration
- [ ] Update documentation with actual ports
- [ ] Create port mapping diagram

## 🔍 Troubleshooting Port Issues

### **Common Issues & Solutions**

#### **1. "Address already in use" Error**
```bash
# Find process using port
lsof -i :8000
# or
sudo netstat -tlnp | grep :8000

# Kill process if needed
kill -9 <PID>
```

#### **2. Docker Port Conflicts**
```bash
# List all Docker port mappings
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Stop conflicting container
docker stop <container_name>
```

#### **3. Service Discovery Issues**
```bash
# Test internal Docker networking
docker exec <container> nc -zv <service_name> <port>

# Test external connectivity
curl -v http://localhost:<port>/health
```

## 🚀 Migration Plan

### **Phase 1: Audit Current Usage**
1. Document all services and their ports
2. Identify conflicts and dependencies
3. Create migration timeline

### **Phase 2: Implement Port Manager**
1. Deploy PortManager utility
2. Update all service configurations
3. Test in staging environment

### **Phase 3: Production Rollout**
1. Schedule maintenance window
2. Update services with new ports
3. Verify all connections
4. Update documentation

## 📊 Port Monitoring

### **Prometheus Configuration**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'port_monitor'
    static_configs:
      - targets:
        - 'localhost:5432'  # PostgreSQL
        - 'localhost:6379'  # Redis
        - 'localhost:8000'  # API
        - 'localhost:8080'  # Weaviate
    metrics_path: '/metrics'
```

### **Health Check Script**
```bash
#!/bin/bash
# health_check_ports.sh

PORTS=(5432 6379 8000 8080 8002 8003 8006)
SERVICES=("PostgreSQL" "Redis" "API" "Weaviate" "Conductor" "Memory" "Tools")

for i in "${!PORTS[@]}"; do
    port="${PORTS[$i]}"
    service="${SERVICES[$i]}"
    
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $service (port $port) is responding"
    else
        echo "❌ $service (port $port) is not responding"
    fi
done
```

## 🎯 Best Practices Summary

1. **Never hardcode ports** - Always use environment variables
2. **Document all ports** - Maintain a central port registry
3. **Use port ranges** - Assign services to specific ranges
4. **Implement health checks** - Monitor port availability
5. **Plan for scaling** - Reserve ports for future services
6. **Use service discovery** - For dynamic environments
7. **Secure exposed ports** - Implement proper firewall rules
8. **Regular audits** - Check for port drift and conflicts

## 📚 References

- [IANA Port Number Registry](https://www.iana.org/assignments/service-names-port-numbers)
- [Docker Networking](https://docs.docker.com/network/)
- [Linux Port Management](https://www.linux.com/training-tutorials/linux-port-management/)

---

*Last Updated: December 2024*  
*Version: 1.0*  
*Maintained by: Orchestra AI DevOps Team* 