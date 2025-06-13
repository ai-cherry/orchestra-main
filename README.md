# 🎼 Orchestra AI Platform

Welcome to the Orchestra AI Platform, a comprehensive environment for advanced AI orchestration, data integration, and development with deep Cursor AI integration.

## 🚀 Architecture Overview (Production Grade)

The Orchestra AI platform is designed for stability and scalability using a containerized architecture managed by Docker Compose. This ensures a consistent, isolated, and "always-active" environment.

- **Backend API**: A robust FastAPI server running in a Python 3.11 container.
- **Frontend UI**: A professional React/Vite application, built and served by a lightweight Nginx container.
- **MCP Memory Server**: A dedicated service for Cursor AI's contextual memory, running in its own Python 3.11 container.
- **Data Persistence**: A dedicated Docker volume for the SQLite database ensures data is saved across container restarts.
- **Auto-Restart**: All services are configured to restart automatically unless explicitly stopped, ensuring high availability.

---

## ⚙️ Getting Started (Recommended Method)

This is the simplest and most reliable way to run the entire Orchestra AI platform.

### Prerequisites

1.  **Docker Desktop**: Ensure Docker Desktop is installed and running on your system.
2.  **Cursor**: For the best development experience.

### Single-Command-Startup

Navigate to the project root directory (`orchestra-dev`) in your terminal and run the following command:

```bash
docker-compose up --build
```

**What this command does:**
- `build`: Creates the container images for each service (a one-time process unless you change the Dockerfiles).
- `up`: Starts all the services, connects them on a dedicated network, and displays their logs in your terminal.

### Accessing the Platform

Once the containers are running, the platform will be available at:

- **🖥️ Main Application**: [http://localhost:3000](http://localhost:3000)
- **⚙️ Backend API**: [http://localhost:8000](http://localhost:8000)
- **🧠 Cursor AI Memory Server**: [http://localhost:8003](http://localhost:8003)

To stop all services, press `Ctrl + C` in the terminal where `docker-compose` is running.

---

## 🧑‍💻 Development Workflow

With the Docker setup, your development workflow is streamlined:

- **Live Reloading (Backend)**: Changes made to the code in the `api/`, `mcp_servers/` and `shared/` directories will automatically restart the relevant Python servers within their containers, thanks to the mounted volumes.
- **Live Reloading (Frontend)**: The frontend does **not** currently live-reload in the production Nginx container. For active frontend development, see the alternative setup below.

## Alternative Setup (Active Frontend Development)

If you are actively developing the frontend and need Hot Module Replacement (HMR), you can run the frontend separately.

1.  **Start Backend Services**:
    ```bash
    docker-compose up --build api mcp_server
    ```
2.  **Start Frontend Dev Server**:
    In a new terminal, navigate to the `web` directory and run:
    ```bash
    cd web
    npm install
    npm run dev
    ```
    The frontend will now be available with HMR, typically at `http://localhost:5173`.

## 🤝 Cursor AI Integration & Coding Guidelines

For guidelines on how to best leverage the integrated AI capabilities, please refer to the [Cursor AI Coding Guidelines](./CURSOR_AI_CODING_GUIDELINES.md).

## 🎼 Orchestra AI - Intelligent AI Orchestration Platform

**Production-Ready AI Orchestration with Lambda Labs GPU Integration**

[![Status](https://img.shields.io/badge/Status-Operational-brightgreen)](https://github.com/lynnmusil/orchestra-dev)
[![Infrastructure](https://img.shields.io/badge/Infrastructure-Pulumi-blue)](https://pulumi.com)
[![GPU](https://img.shields.io/badge/GPU-Lambda%20Labs-orange)](https://lambdalabs.com)
[![MCP](https://img.shields.io/badge/MCP-Ecosystem-purple)](https://github.com/lynnmusil/orchestra-dev)

## 🚀 **Current Status: Fully Operational**

Orchestra AI is now **production-ready** with a complete infrastructure stack powered by Pulumi:

### ✅ **Operational Services**
- **Frontend**: React + Vite on `localhost:3000` ✅
- **API**: FastAPI on `localhost:8000` ✅  
- **Database**: SQLite (dev) / PostgreSQL (staging/prod) ✅
- **Infrastructure**: Pulumi-managed with Lambda Labs GPU integration ✅
- **MCP Ecosystem**: 5-server architecture ready for deployment ✅

## 🏗️ **Architecture Overview**

```mermaid
graph TB
    subgraph "Development Layer"
        FE[React Frontend<br/>localhost:3000]
        API[FastAPI Backend<br/>localhost:8000]
        DB[(SQLite Database<br/>Local Development)]
    end
    
    subgraph "MCP Server Ecosystem"
        MEM[Memory Management<br/>Port 8003]
        CODE[Code Intelligence<br/>Port 8007]
        GIT[Git Intelligence<br/>Port 8008]
        TOOLS[Tools Registry<br/>Port 8006]
        INFRA[Infrastructure<br/>Port 8009]
    end
    
    subgraph "Lambda Labs GPU Cluster"
        GPU1[GPU Instance 1<br/>Auto-scaling]
        GPU2[GPU Instance 2<br/>Cost Optimized]
        GPU3[GPU Instance N<br/>On Demand]
    end
    
    subgraph "Infrastructure as Code"
        PULUMI[Pulumi Stack<br/>Python/TypeScript]
        MONITORING[Prometheus + Grafana<br/>Observability]
        DEPLOY[GitHub Actions<br/>CI/CD Pipeline]
    end
    
    FE --> API
    API --> DB
    API --> MEM
    API --> CODE
    API --> GIT
    API --> TOOLS
    INFRA --> GPU1
    INFRA --> GPU2
    INFRA --> GPU3
    PULUMI --> MCP
    PULUMI --> GPU1
    MONITORING --> API
    DEPLOY --> PULUMI
```

## 🚀 **Quick Start**

### **Prerequisites**
```bash
# Required software
- Python 3.11+
- Node.js 18+
- Git
- Pulumi CLI (for infrastructure)
```

### **Installation**
```bash
# 1. Clone repository
git clone https://github.com/lynnmusil/orchestra-dev.git
cd orchestra-dev

# 2. Setup development environment
./setup_dev_environment.sh

# 3. Start all services
./start_orchestra.sh

# 4. Verify health
curl http://localhost:8000/api/health
open http://localhost:3000
```

### **Validation**
```bash
# Comprehensive environment check
python3 validate_environment.py
```

## 🏗️ **Infrastructure Management**

### **Environment Tiers**

#### **Development (Local)**
- **Database**: SQLite (automatic)
- **Services**: Frontend + API only
- **Setup**: `./start_orchestra.sh`

#### **Staging**
- **Database**: PostgreSQL (45.77.87.106)
- **Services**: Full stack + MCP servers
- **Deploy**: `cd pulumi && pulumi up --stack=staging`

#### **Production**
- **Database**: PostgreSQL cluster
- **GPU**: Lambda Labs auto-scaling cluster
- **MCP**: Complete 5-server ecosystem
- **Deploy**: `cd pulumi && pulumi up --stack=production`

### **Pulumi Infrastructure Stack**

```bash
# Initialize Pulumi
cd pulumi
pulumi stack init development
pulumi config set lambda_labs_api_key --secret

# Deploy infrastructure
pulumi up --stack=development   # Local development
pulumi up --stack=staging       # Integration testing  
pulumi up --stack=production    # Full production stack
```

## 🎯 **Core Features**

### **🤖 AI Orchestration**
- **Multi-Model Support**: OpenAI, Anthropic, Lambda Labs GPU
- **Intelligent Routing**: Automatic model selection and load balancing
- **Context Management**: Advanced conversation and session handling
- **Performance Optimization**: Caching, batching, and async processing

### **🔧 Development Tools**
- **MCP Server Ecosystem**: 5 specialized servers for different capabilities
- **Code Intelligence**: AST analysis, function search, complexity metrics
- **Git Intelligence**: History analysis, blame tracking, contributor insights
- **Memory Management**: Advanced context and data persistence

### **📊 Monitoring & Observability**
- **Prometheus Metrics**: Custom metrics for AI operations
- **Grafana Dashboards**: Real-time performance visualization  
- **Health Checks**: Comprehensive system status monitoring
- **Lambda Labs Analytics**: GPU utilization and cost tracking

### **🚀 Auto-Scaling Infrastructure**
- **Dynamic GPU Allocation**: Scale based on demand
- **Cost Optimization**: Spot instances and intelligent scheduling
- **Fault Tolerance**: Automatic failover and recovery
- **Load Balancing**: Intelligent request distribution

## 📁 **Project Structure**

```
orchestra-dev/
├── api/                    # FastAPI backend
│   ├── main.py            # Main application entry
│   ├── database/          # Database models and connections
│   └── services/          # Business logic services
├── web/                   # React frontend
│   ├── src/              # Source code
│   ├── public/           # Static assets
│   └── package.json      # Dependencies
├── pulumi/               # Infrastructure as Code
│   ├── __main__.py       # Main Pulumi program
│   ├── lambda_labs.py    # GPU cluster management
│   ├── mcp_infrastructure.py  # MCP server deployment
│   └── monitoring.py     # Observability stack
├── environments/         # Environment configurations
│   ├── development/      # Local development setup
│   ├── staging/         # Integration testing
│   └── production/      # Production configuration
└── scripts/             # Automation scripts
    ├── start_orchestra.sh
    ├── deploy_to_production.sh
    └── validate_environment.py
```

## 🛠️ **Development Workflow**

### **Feature Development**
```bash
# 1. Create feature branch
git checkout -b feature/my-awesome-feature

# 2. Develop locally
./start_orchestra.sh
# ... development work ...

# 3. Test and validate
python3 validate_environment.py
./test_setup.py

# 4. Deploy to staging
git push origin feature/my-awesome-feature
cd pulumi && pulumi up --stack=staging

# 5. Production deployment
git checkout main
git merge feature/my-awesome-feature
cd pulumi && pulumi up --stack=production
```

### **MCP Server Development**
```bash
# Start MCP servers locally
./start_mcp_servers_working.sh

# Deploy specific MCP server
cd pulumi
pulumi up --stack=staging --target=mcp-memory-server
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Development (.env)
ENVIRONMENT=development
DATABASE_URL=sqlite:///data/orchestra_dev.db
API_PORT=8000
FRONTEND_PORT=3000

# Production
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@45.77.87.106:5432/orchestra_ai
LAMBDA_LABS_API_KEY=your_api_key_here
MCP_ENABLED=true
```

### **Pulumi Configuration**
```yaml
# pulumi/Pulumi.yaml
config:
  environment: development|staging|production
  mcp_enabled: true
  lambda_labs_api_key: {secret: true}
  gpu_instance_type: gpu_1x_a100
  instance_count: 2
```

## 📊 **Performance Metrics**

### **Development Targets**
- **Local Setup**: < 5 minutes
- **Build Time**: < 30 seconds  
- **Hot Reload**: < 2 seconds
- **API Response**: < 200ms

### **Production Targets**
- **Uptime**: > 99.9%
- **GPU Scaling**: < 60 seconds
- **Database Response**: < 50ms
- **Frontend Load**: < 2 seconds

## 🔒 **Security**

### **Development Security**
- Local SQLite (no external connections)
- Environment variable isolation
- Safe dependency management

### **Production Security**
- Database encryption (transit + rest)
- API key rotation and management
- Network policies and RBAC
- mTLS for service communication

## 🤝 **Contributing**

### **Development Setup**
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Install dependencies: `./setup_dev_environment.sh`
4. Make changes and test: `python3 validate_environment.py`
5. Submit pull request

### **Code Standards**
- **Python**: Follow PEP 8, use `black` formatter
- **TypeScript**: Use ESLint + Prettier
- **Testing**: Minimum 80% code coverage
- **Documentation**: Update relevant docs

## 📞 **Support & Documentation**

### **Quick Links**
- **Setup Guide**: [DEVELOPMENT_SETUP.md](./DEVELOPMENT_SETUP.md)
- **Infrastructure Guide**: [PULUMI_INFRASTRUCTURE_SETUP.md](./PULUMI_INFRASTRUCTURE_SETUP.md)
- **Deployment Guide**: [DEPLOYMENT_TEST_REPORT.md](./DEPLOYMENT_TEST_REPORT.md)
- **MCP Documentation**: [MCP_INFRASTRUCTURE_DISCOVERY_REPORT.md](./MCP_INFRASTRUCTURE_DISCOVERY_REPORT.md)

### **Health Check Commands**
```bash
# Environment validation
python3 validate_environment.py

# Service health
curl http://localhost:8000/api/health
curl http://localhost:3000

# Infrastructure status
cd pulumi && pulumi stack output
```

## 🎉 **Recent Updates**

### **✅ Infrastructure Consistency Complete**
- **Migrated to Pulumi**: Complete transition from Terraform
- **Database Auto-switching**: SQLite (dev) → PostgreSQL (staging/prod)
- **Dependency Resolution**: Fixed all import errors and missing packages
- **Path Resolution**: Complete `@/` import support for frontend

### **🚀 Production Ready**
- **Lambda Labs Integration**: Auto-scaling GPU clusters
- **MCP Ecosystem**: 5-server architecture deployed
- **Monitoring Stack**: Prometheus + Grafana + Alertmanager
- **CI/CD Pipeline**: GitHub Actions with Pulumi deployment

---

**Orchestra AI - Where AI orchestration meets enterprise-grade infrastructure. Powered by Pulumi, optimized for Lambda Labs GPUs, and designed for scale.**

[🌟 Star this repo](https://github.com/lynnmusil/orchestra-dev) • [🐛 Report Bug](https://github.com/lynnmusil/orchestra-dev/issues) • [💡 Request Feature](https://github.com/lynnmusil/orchestra-dev/issues) 