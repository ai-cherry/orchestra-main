# LLM Orchestration Deployment Checklist

## Pre-Deployment Requirements

### 1. Infrastructure Setup

#### PostgreSQL Database
- [ ] PostgreSQL 14+ installed and running
- [ ] Database created: `orchestra_db`
- [ ] User with appropriate permissions created
- [ ] Connection string configured in environment
- [ ] Run migration script: `psql -d orchestra_db -f migrations/001_llm_orchestration_schema.sql`

#### Redis
- [ ] Redis 6+ installed and running
- [ ] Connection configured in environment
- [ ] Memory allocation sufficient (min 2GB recommended)
- [ ] Persistence enabled for production

#### Weaviate
- [ ] Weaviate instance running (Docker or standalone)
- [ ] Schema created for user search history
- [ ] Connection URL configured
- [ ] Authentication configured if required

### 2. Environment Configuration

Create `.env` file with the following variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/orchestra_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Weaviate
WEAVIATE_URL=http://localhost:8080

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PORTKEY_API_KEY=pk-...
OPENROUTER_API_KEY=sk-or-...

# Application
API_HOST=0.0.0.0
API_PORT=8080
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### 3. Dependencies Installation

#### Backend (Python)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Additional dependencies for orchestration
pip install redis[hiredis]==4.5.4
pip install weaviate-client==3.19.2
pip install networkx==3.1
pip install httpx==0.24.1
```

#### Frontend (Node.js)
```bash
# Navigate to admin-ui directory
cd admin-ui

# Install dependencies
npm install

# Additional dependencies
npm install recharts@2.5.0
npm install lucide-react@0.263.1

# Build for production
npm run build
```

### 4. Database Setup

#### Run Migrations
```bash
# Apply database migrations
psql -U $DB_USER -h $DB_HOST -d orchestra_db -f migrations/001_llm_orchestration_schema.sql

# Verify tables created
psql -U $DB_USER -h $DB_HOST -d orchestra_db -c "\dt"
```

#### Seed Initial Data
```sql
-- Insert default LLM providers
INSERT INTO llm_providers (name, api_key_env_var, is_active, priority) VALUES
('openai', 'OPENAI_API_KEY', true, 1),
('anthropic', 'ANTHROPIC_API_KEY', true, 2),
('openrouter', 'OPENROUTER_API_KEY', true, 3),
('portkey', 'PORTKEY_API_KEY', true, 4);

-- Insert default use cases
INSERT INTO llm_use_cases (use_case, display_name, description) VALUES
('general_purpose', 'General Purpose', 'General conversational queries'),
('creative_writing', 'Creative Writing', 'Creative content generation'),
('code_generation', 'Code Generation', 'Programming and code assistance'),
('data_analysis', 'Data Analysis', 'Analytical and data-related queries'),
('research', 'Research', 'Deep research and investigation');
```

### 5. Service Configuration

#### Systemd Service (Linux)
Create `/etc/systemd/system/orchestra-api.service`:
```ini
[Unit]
Description=Orchestra API Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=orchestra
WorkingDirectory=/opt/orchestra
Environment="PATH=/opt/orchestra/venv/bin"
ExecStart=/opt/orchestra/venv/bin/uvicorn agent.app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name api.orchestra.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. Monitoring Setup

#### Prometheus Configuration
Add to `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'orchestra-api'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
```

#### Grafana Dashboard
Import the dashboard from `monitoring/grafana-dashboard.json`

### 7. Testing & Validation

#### API Health Check
```bash
# Test API health
curl http://localhost:8080/health

# Test orchestration health
curl http://localhost:8080/api/orchestration/system/health
```

#### Run Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_llm_intelligent_router.py -v
pytest tests/test_specialized_agents.py -v
pytest tests/test_agent_orchestrator.py -v
pytest tests/test_api_integration.py -v
```

#### Frontend Verification
```bash
# Start development server
cd admin-ui
npm run dev

# Access at http://localhost:5173
# Navigate to LLM Orchestration page
```

### 8. Production Deployment

#### Backend Deployment
```bash
# Start services
sudo systemctl start orchestra-api
sudo systemctl enable orchestra-api

# Check status
sudo systemctl status orchestra-api

# View logs
journalctl -u orchestra-api -f
```

#### Frontend Deployment
```bash
# Build production bundle
cd admin-ui
npm run build

# Deploy to web server
rsync -avz dist/ user@server:/var/www/orchestra-admin/

# Or use CDN
aws s3 sync dist/ s3://orchestra-admin-bucket/
aws cloudfront create-invalidation --distribution-id ABCD --paths "/*"
```

### 9. Post-Deployment Verification

#### Functional Tests
- [ ] Test intelligent routing with various query types
- [ ] Verify Personal Agent search and preference learning
- [ ] Test Pay Ready Agent apartment analysis
- [ ] Verify Paragon Medical Agent trial search
- [ ] Create and execute a workflow
- [ ] Check workflow status and monitoring

#### Performance Tests
- [ ] Response times < 100ms for routing decisions
- [ ] Agent task execution < 200ms
- [ ] Dashboard loads < 2 seconds
- [ ] No memory leaks after 1 hour of operation

#### Integration Tests
- [ ] LLM API calls successful
- [ ] Redis caching working
- [ ] Weaviate vector search functional
- [ ] Database queries optimized
- [ ] Circuit breakers activating correctly

### 10. Rollback Plan

#### Database Rollback
```sql
-- Rollback migration if needed
BEGIN;
DROP MATERIALIZED VIEW IF EXISTS llm_routing_analytics;
DROP TABLE IF EXISTS clinical_trial_alerts CASCADE;
DROP TABLE IF EXISTS neighborhood_scores CASCADE;
DROP TABLE IF EXISTS user_search_history CASCADE;
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS workflow_checkpoints CASCADE;
DROP TABLE IF EXISTS workflow_tasks CASCADE;
DROP TABLE IF EXISTS workflow_executions CASCADE;
DROP TABLE IF EXISTS workflow_definitions CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column();
COMMIT;
```

#### Service Rollback
```bash
# Stop new service
sudo systemctl stop orchestra-api

# Restore previous version
cd /opt/orchestra
git checkout previous-version
pip install -r requirements.txt

# Restart service
sudo systemctl start orchestra-api
```

## Security Checklist

- [ ] All API keys in environment variables
- [ ] Database connections use SSL
- [ ] Redis password configured
- [ ] API rate limiting enabled
- [ ] CORS properly configured
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified
- [ ] XSS protection enabled
- [ ] Authentication integrated
- [ ] Authorization rules applied

## Monitoring & Alerts

- [ ] CPU usage alert (> 80%)
- [ ] Memory usage alert (> 90%)
- [ ] API error rate alert (> 1%)
- [ ] Database connection pool alert
- [ ] Circuit breaker open alerts
- [ ] Workflow failure alerts
- [ ] LLM API quota alerts

## Documentation

- [ ] API documentation updated
- [ ] Runbook created for common issues
- [ ] Architecture diagrams updated
- [ ] Configuration guide completed
- [ ] Troubleshooting guide written

## Sign-off

- [ ] Development team approval
- [ ] QA team approval
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] Documentation reviewed
- [ ] Rollback plan tested

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Version**: 1.0.0  
**Status**: ⬜ PENDING | ⬜ IN PROGRESS | ⬜ COMPLETED