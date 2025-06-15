# Orchestra AI Platform - Setup Guide

## 🚀 Quick Start Guide

This guide will help you set up the Orchestra AI platform with advanced persona management and search capabilities.

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** 
- **Docker & Docker Compose**
- **PostgreSQL** (for production) or SQLite (for development)
- **Git**

### 1. Clone Repository

```bash
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your configuration
nano .env
```

**Required Environment Variables:**
```bash
# Database (Production)
DATABASE_HOST=localhost
DATABASE_NAME=orchestra_prod
DATABASE_USER=orchestra
DATABASE_PASSWORD=Orchestra_Prod_2025_Secure

# Optional: Advanced Search API Keys
EXA_AI_API_KEY=your_exa_key
SERP_API_KEY=your_serp_key
APIFY_API_KEY=your_apify_key
PHANTOMBUSTER_API_KEY=your_phantombuster_key
ZENROWS_API_KEY=your_zenrows_key

# Optional: Voice Integration
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### 3. Database Setup

#### Option A: Docker Database (Recommended)
```bash
# Start PostgreSQL with Docker
docker-compose -f docker-compose.database.yml up -d

# Verify database is running
docker-compose -f docker-compose.database.yml ps
```

#### Option B: Local PostgreSQL
```bash
# Install PostgreSQL locally
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE orchestra_prod;
CREATE USER orchestra WITH PASSWORD 'Orchestra_Prod_2025_Secure';
GRANT ALL PRIVILEGES ON DATABASE orchestra_prod TO orchestra;
\q
```

### 4. Python Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import fastapi, psycopg2, aiohttp; print('Dependencies OK')"
```

### 5. Database Schema

```bash
# Apply database schema
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    database='orchestra_prod', 
    user='orchestra',
    password='Orchestra_Prod_2025_Secure'
)
cursor = conn.cursor()

# Create schema
cursor.execute('CREATE SCHEMA IF NOT EXISTS orchestra;')

# Create personas table with extensions
cursor.execute('''
CREATE TABLE IF NOT EXISTS orchestra.personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    persona_type VARCHAR(50) NOT NULL,
    description TEXT,
    communication_style JSONB,
    knowledge_domains TEXT[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    domain_leanings JSONB,
    voice_settings JSONB,
    api_access_config JSONB,
    search_preferences JSONB
);
''')

# Insert default personas
cursor.execute('''
INSERT INTO orchestra.personas (name, persona_type, description, communication_style, knowledge_domains)
VALUES 
    ('Cherry', 'assistant', 'Creative AI specialized in content creation, design, and innovation', 
     '{\"tone\": \"friendly\", \"style\": \"creative\"}', ARRAY['creative', 'design', 'content']),
    ('Sophia', 'analyst', 'Strategic AI focused on analysis, planning, and complex problem-solving', 
     '{\"tone\": \"professional\", \"style\": \"analytical\"}', ARRAY['analysis', 'strategy', 'business']),
    ('Karen', 'manager', 'Operational AI focused on execution, automation, and workflow management', 
     '{\"tone\": \"authoritative\", \"style\": \"structured\"}', ARRAY['operations', 'automation', 'management'])
ON CONFLICT (name) DO NOTHING;
''')

conn.commit()
cursor.close()
conn.close()
print('Database schema applied successfully!')
"
```

### 6. Start Backend API

```bash
# Start the production API server
python3 production_api.py

# Verify API is running
curl http://localhost:8000/health
curl http://localhost:8000/api/personas
```

### 7. Frontend Setup

```bash
# Navigate to frontend directory
cd modern-admin

# Install dependencies
pnpm install

# Development mode (with hot reload)
pnpm run dev

# Production build
pnpm run build
```

### 8. Verify Installation

```bash
# Test persona management
curl http://localhost:8000/api/personas

# Test search modes
curl http://localhost:8000/api/search/modes

# Test search sources
curl http://localhost:8000/api/search/sources

# Test advanced search
curl -X POST http://localhost:8000/api/search/advanced \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence trends",
    "search_mode": "normal",
    "persona": "sophia",
    "max_results": 5
  }'
```

## 🎯 Feature Overview

### Persona Management System
- **3 Pre-configured Personas**: Cherry (Creative), Sophia (Strategic), Karen (Operational)
- **Domain Leanings**: Keyword-based preference learning
- **Voice Integration**: ElevenLabs voice configuration
- **Analytics**: Usage tracking and performance metrics

### Advanced Search Engine
- **Normal Mode**: Database + DuckDuckGo (Free, 2-5s)
- **Deep Mode**: 4 sources including APIs ($0.02-0.05, 10-20s)
- **Super Deep**: 6 sources with scraping ($0.05-0.10, 20-30s)
- **Uncensored**: Alternative sources ($0.03-0.08, 15-25s)

### Modern UI Features
- **Persona Management Page**: `/personas` route
- **Advanced Search Interface**: Search button in chat
- **Real-time Results**: Professional results display
- **Cost Tracking**: Transparent pricing information

## 🔧 Configuration

### Persona Configuration
Access the persona management interface at `/personas` to configure:
- **Identity Settings**: Name, description, personality traits
- **Domain Leanings**: Keywords and preference weights
- **Voice Settings**: ElevenLabs voice configuration
- **Search Preferences**: Default search modes and options

### Search API Configuration
To enable advanced search modes, add API keys to your `.env` file:
```bash
# For Deep and Super Deep modes
EXA_AI_API_KEY=your_exa_key
SERP_API_KEY=your_serp_key

# For Super Deep mode (web scraping)
APIFY_API_KEY=your_apify_key
PHANTOMBUSTER_API_KEY=your_phantombuster_key

# For Uncensored mode
ZENROWS_API_KEY=your_zenrows_key
VENICE_AI_API_KEY=your_venice_key
```

## 🚀 Deployment

### Development Deployment
```bash
# Start all services
docker-compose -f docker-compose.database.yml up -d
python3 production_api.py &
cd modern-admin && pnpm run dev
```

### Production Deployment
```bash
# Build frontend
cd modern-admin
pnpm run build

# Deploy frontend (automatically handled by Manus hosting)
# Backend runs on production server with environment variables
```

## 📊 Monitoring

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Database connection
curl http://localhost:8000/api/system/status

# Search capabilities
curl http://localhost:8000/api/search/sources
```

### Performance Monitoring
- **API Response Times**: Available in logs
- **Search Cost Tracking**: Real-time cost estimation
- **Persona Analytics**: Usage patterns and preferences
- **Database Performance**: Query optimization metrics

## 🔒 Security

### Database Security
- **Encrypted Connections**: SSL/TLS for database connections
- **User Isolation**: Dedicated database user with limited privileges
- **Password Security**: Strong passwords required

### API Security
- **Rate Limiting**: Prevents abuse and controls costs
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Secure error messages without data leakage

### Search Privacy
- **Query Anonymization**: Optional query anonymization
- **Cost Controls**: Per-user cost limits and tracking
- **Source Isolation**: Separate API keys for different sources

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check database status
docker-compose -f docker-compose.database.yml ps

# Restart database
docker-compose -f docker-compose.database.yml restart

# Check logs
docker-compose -f docker-compose.database.yml logs postgres
```

#### API Not Starting
```bash
# Check Python dependencies
pip install -r requirements.txt

# Check database connection
python3 -c "import psycopg2; print('PostgreSQL OK')"

# Check port availability
lsof -i :8000
```

#### Frontend Build Issues
```bash
# Clear cache and reinstall
cd modern-admin
rm -rf node_modules package-lock.json
pnpm install
pnpm run build
```

#### Search API Issues
```bash
# Test search endpoints
curl http://localhost:8000/api/search/sources

# Check API key configuration
grep -E "(EXA|SERP|APIFY)" .env

# Test basic search
curl -X POST http://localhost:8000/api/search/advanced \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "search_mode": "normal"}'
```

## 📞 Support

### Documentation
- **API Documentation**: Available at `http://localhost:8000/docs`
- **Implementation Progress**: See `todo.md`
- **Deployment Guide**: See `DEPLOYMENT_SOLUTION_COMPLETE.md`

### Getting Help
1. Check the troubleshooting section above
2. Review logs for error messages
3. Verify environment configuration
4. Test individual components separately

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes and test thoroughly
4. Submit a pull request with detailed description

---

**Orchestra AI Setup Complete! 🎉**

Your advanced AI orchestration platform with persona management and intelligent search is now ready for use.

