# 🚀 Orchestra AI Phase 2 Setup Guide

## Overview

Phase 2 transforms the Orchestra AI admin interface into a fully functional platform with comprehensive data integration, advanced persona management, and multi-modal search capabilities.

## 🏗️ Architecture Overview

### New Components
- **PostgreSQL Database**: Structured data storage for users, personas, files, and search queries
- **Vector Database**: FAISS (local) or Weaviate (production) for semantic search
- **Enhanced File Processing**: Comprehensive support for 25+ file types with AI analysis
- **Advanced Persona Management**: Configurable AI personalities with custom behaviors
- **Multi-Modal Search**: 6 different search modes for varied use cases
- **Real-time Communication**: Enhanced WebSocket support for live updates

### Technology Stack
- **Backend**: FastAPI + SQLAlchemy + AsyncPG + Pydantic
- **Database**: PostgreSQL + Vector Store (FAISS/Weaviate)
- **AI/ML**: sentence-transformers + OpenAI + OpenRouter
- **File Processing**: PyPDF2 + pdfplumber + python-docx + BeautifulSoup
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS (existing)

## 📋 Prerequisites

### System Requirements
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- 8GB+ RAM (for local development)
- 20GB+ available disk space

### Required Services
- PostgreSQL database server
- Redis (optional, for caching)
- Weaviate (optional, for production vector store)

## 🔧 Installation Steps

### 1. Backend Setup

#### Install Python Dependencies
```bash
cd api
pip install -r requirements.txt
```

#### Database Setup
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database
sudo -u postgres createdb orchestra_ai

# Create user (optional)
sudo -u postgres createuser --interactive orchestra_user
```

#### Configuration
```bash
# Copy configuration template
cp config.example.py config.py

# Edit configuration with your settings
nano config.py
```

#### Environment Variables
Create a `.env` file in the `api/` directory:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/orchestra_ai

# Vector Store (choose one)
VECTOR_STORE_TYPE=faiss  # or weaviate
FAISS_STORAGE_PATH=./data/faiss

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=2147483648

# AI Models
EMBEDDING_MODEL=all-MiniLM-L6-v2
OPENAI_API_KEY=your-openai-key-here

# Development
DEBUG=true
LOG_LEVEL=INFO
```

### 2. Frontend Setup (Enhanced)

The existing React frontend from Phase 1 will work with Phase 2 backend. No changes needed for initial testing.

```bash
cd web
npm install
npm run dev
```

### 3. Database Initialization

The database tables will be created automatically on first startup. To manually initialize:

```bash
cd api
python -c "
import asyncio
from database.connection import init_database
asyncio.run(init_database())
"
```

### 4. Start Services

#### Backend
```bash
cd api
python main.py
```

#### Frontend (separate terminal)
```bash
cd web
npm run dev
```

## 🧪 Testing the Installation

### 1. Health Check
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "vector_store": "healthy",
  "file_service": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "2.0.0"
}
```

### 2. Test File Upload
```bash
curl -X POST "http://localhost:8000/api/files/upload/initiate" \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.txt",
    "file_size": 1024,
    "persona_type": "cherry",
    "metadata": {"type": "test"}
  }'
```

### 3. Test Search
```bash
curl -X POST "http://localhost:8000/api/search" \
  -H "Authorization: Bearer demo-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test search",
    "search_mode": "basic",
    "limit": 10
  }'
```

## 🎯 Key Features

### 1. Enhanced File Processing
- **25+ File Types**: PDF, DOCX, images, code, archives, etc.
- **Intelligent Chunking**: Optimized for document structure
- **Metadata Extraction**: Comprehensive analysis per file type
- **Vector Embeddings**: Automatic generation for semantic search
- **Progress Tracking**: Real-time upload and processing status

### 2. Advanced Persona Management
- **Cherry (Creative AI)**: Design, content creation, branding
- **Sophia (Strategic AI)**: Business analysis, planning, strategy
- **Karen (Operational AI)**: Process optimization, efficiency
- **Configurable Behaviors**: Custom prompts, models, preferences
- **Usage Analytics**: Performance tracking and optimization

### 3. Multi-Modal Search
- **Basic Search**: Standard semantic search across files
- **Deep Search**: Comprehensive analysis with AI synthesis
- **Super Deep Search**: Multi-step reasoning and cross-references
- **Creative Search**: Innovation and ideation support
- **Private Search**: Secure, isolated information access
- **Uncensored Search**: Unrestricted content coverage

### 4. Real-time Communication
- **WebSocket Integration**: Live updates for uploads and processing
- **Progress Streaming**: Real-time file processing status
- **Notification System**: Alerts for completed operations
- **Multi-user Support**: Concurrent connection management

## 🔒 Security Features

### Authentication & Authorization
- JWT token-based authentication
- Role-based access control
- User isolation (files/data per user)
- API rate limiting

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- File type validation
- Size limits and security scanning

### Privacy Controls
- Private search mode with enhanced security
- Data encryption at rest (configurable)
- Audit logging for all operations
- GDPR compliance features

## 📊 Performance & Scalability

### Database Optimization
- Connection pooling (20 connections)
- Query optimization with indexes
- Async database operations
- Efficient pagination

### File Processing
- Chunked uploads (8MB chunks)
- Background processing queues
- Error handling and retry logic
- Memory-efficient streaming

### Vector Search
- FAISS for local development (fast)
- Weaviate for production (scalable)
- Embedding caching
- Optimized query performance

## 🚀 Deployment

### Development
```bash
# Backend
cd api && python main.py

# Frontend
cd web && npm run dev
```

### Production

#### Using Docker (Recommended)
```bash
# Build and run with docker-compose
docker-compose up -d
```

#### Manual Deployment
```bash
# Backend with Gunicorn
cd api
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Frontend build
cd web
npm run build
# Serve dist/ with nginx or similar
```

## 📋 API Documentation

### Core Endpoints
- `GET /api/system/status` - Enhanced system metrics
- `POST /api/files/upload/initiate` - Start file upload
- `POST /api/files/{id}/upload` - Upload file chunks
- `GET /api/files/{id}/status` - Processing status
- `POST /api/files/search` - Search files
- `POST /api/personas` - Create persona
- `GET /api/personas` - List personas
- `POST /api/search` - Multi-modal search

### WebSocket
- `WS /ws/{user_id}` - Real-time communication

Full API documentation available at `http://localhost:8000/docs`

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -h localhost -U postgres -d orchestra_ai
```

#### Vector Store Initialization Failed
```bash
# For FAISS
pip install faiss-cpu

# For Weaviate
docker run -p 8080:8080 semitechnologies/weaviate:latest
```

#### File Upload Fails
```bash
# Check upload directory permissions
mkdir -p ./uploads
chmod 755 ./uploads

# Check disk space
df -h
```

#### Memory Issues
```bash
# Reduce file size limits in config
MAX_FILE_SIZE=536870912  # 512MB instead of 2GB

# Use FAISS instead of Weaviate
VECTOR_STORE_TYPE=faiss
```

### Logs
```bash
# View application logs
tail -f ./logs/orchestra-ai.log

# View database logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

## 📈 Monitoring

### Health Checks
- Database connectivity
- Vector store status
- File service availability
- Memory and CPU usage

### Metrics
- File processing queue size
- Search response times
- API request rates
- Error rates

### Performance Tuning
- Database connection pool sizing
- Vector index optimization
- File processing batch sizes
- Cache configuration

## 🔄 Migration from Phase 1

Phase 2 is fully backward compatible with Phase 1. The enhanced features are additive:

1. **Existing functionality preserved**: All Phase 1 endpoints work unchanged
2. **Enhanced capabilities**: File processing, search, and persona management
3. **Progressive upgrade**: Can be deployed alongside Phase 1
4. **Data migration**: Automatic on first startup

## 📚 Next Steps

1. **Test all functionality** with the provided examples
2. **Configure external services** (OpenAI, OpenRouter, Notion)
3. **Set up production deployment** with proper security
4. **Implement Sprint 2-4 features** as needed
5. **Monitor performance** and optimize as required

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review API documentation at `/docs`
3. Check application logs for detailed error messages
4. Verify all dependencies are properly installed

---

**🎉 Orchestra AI Phase 2 is now ready for comprehensive data integration and advanced AI capabilities!** 