# Orchestra AI - Intelligent Workflow Orchestration Platform

## Overview
Orchestra AI is a sophisticated AI-powered workflow orchestration platform that manages complex tasks through intelligent agent coordination, featuring PostgreSQL for data persistence, Weaviate for vector search, and Pulumi for infrastructure as code.

## Architecture
- **API Layer**: FastAPI-based REST API with JWT authentication
- **Database**: PostgreSQL with connection pooling and optimization
- **Vector Store**: Weaviate for semantic search and AI embeddings
- **Cache**: Redis for session management and caching
- **Infrastructure**: Pulumi IaC for Lambda Labs deployment

## Key Features
- Multi-persona AI system (Cherry, Sophia, Karen)
- Adaptive learning and personality development
- Real-time conversation engine with context awareness
- Supervisor agent architecture for task delegation
- MCP (Model Context Protocol) integration
- Comprehensive monitoring and health checks

## Quick Start

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- Weaviate 1.24+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main
```

2. Set up environment variables:
```bash
cp .env.example .env.production
# Edit .env.production with your configuration
```

3. Start services with Docker Compose:
```bash
docker-compose -f docker-compose.production.yml up -d
```

4. Initialize the database:
```bash
python scripts/initialize_database.py
```

5. Start the API server:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## API Documentation
Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure
```
orchestra-main/
├── api/                    # FastAPI application
├── admin-interface/        # Admin dashboard
├── config/                 # Configuration files
├── core/                   # Core business logic
├── mcp_server/            # MCP server implementation
├── infrastructure/         # Pulumi IaC definitions
├── scripts/               # Utility scripts
└── docker-compose.*.yml   # Docker configurations
```

## Security
- JWT-based authentication
- Environment-based configuration
- Connection pooling with limits
- Rate limiting and CORS protection

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
