# 🚀 AI Coding Tools Quick Reference

**Cherry AI Orchestrator - Performance & Stability Focused**

---

## 🎯 Quick Start Commands

### Local Setup (Mac)
```bash
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main
cursor .
```

### SSH to Production Server
```bash
cd ~/orchestra-main
```

---

## 🦘  Coder Commands

### Mode Switching
```
switch to architect mode     # System design & architecture
switch to developer mode     # Code implementation  
switch to debugger mode      # Systematic debugging
switch to conductor mode     # Workflow coordination
```

### Performance Focus
```
optimize for performance     # Speed & efficiency focus
ensure stability            # Error handling & resilience
review code quality         # Maintainability check
implement caching strategy  # Performance optimization
```

### Specific Tasks
```
add comprehensive error handling to all API endpoints
optimize database queries for better performance
implement Redis caching for frequently accessed data
add monitoring and health checks to services
```

---

## 📝 Cursor AI Commands

### Keyboard Shortcuts
- **`Ctrl+K`** - AI chat and code generation
- **`Ctrl+L`** - Chat with codebase context
- **`Ctrl+I`** - Inline code editing
- **`Cmd+Shift+P`** - Command palette

### Context Commands
```
@workspace analyze performance bottlenecks
@files optimize this function for speed
@workspace add error handling to all endpoints
@files convert this to async/await pattern
```

### Performance Prompts
```
"Optimize this function for better performance"
"Add caching to reduce database calls"
"Convert synchronous code to async"
"Profile memory usage and optimize"
"Add comprehensive error handling"
```

---

## 🤖 OpenAI Codex Commands (SSH)

### Basic Usage
```bash
codex "task description"
codex --approval-mode full-auto "automated task"
codex "add error handling to all API endpoints"
```

### Performance Tasks
```bash
codex "optimize database queries in this module"
codex "add Redis caching to API responses"
codex "implement connection pooling"
codex "add performance monitoring and metrics"
```

### Debugging Tasks
```bash
codex "add comprehensive logging to this module"
codex "implement circuit breaker pattern"
codex "add health checks and monitoring"
codex "fix memory leaks in data processing"
```

---

## 🔍 Google Jules Integration

### API Testing
```bash
export GOOGLE_API_KEY="your-key"
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "analyze code performance"}' \
     https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent
```

---

## 🏭 Factory AI (When Available)

### Workflow Commands
```
factory deploy workflow      # Automated deployment
factory review code         # Code quality review
factory monitor performance # Performance tracking
factory optimize pipeline   # CI/CD optimization
```

---

## 📊 AI Tools Dashboard

### Access URLs
- **Enhanced Admin:** https://fcqjsoot.manus.space
- **AI Dashboard:** https://fcqjsoot.manus.space/ai-tools-dashboard.html

### Dashboard Commands
```
setup all tools             # Configure all AI tools
analyze performance         # Performance analysis
optimize code              # Code optimization
cleanup repository         # Remove backup files
monitor ai tools           # Status monitoring
```

---

## 🔧 MCP Server Commands

### Start Servers
```bash
python mcp_server/servers/ai_coding_assistant.py &
python mcp_server/servers/prompt_management.py &
```

### Test Connectivity
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
ps aux | grep mcp_server
```

---

## 🧹 Repository Cleanup

### Preview Cleanup
```bash
python scripts/cleanup_repository.py --optimize-structure
```

### Execute Cleanup
```bash
python scripts/cleanup_repository.py --execute --optimize-structure
```

---

## 🔗 API Testing

### Test All APIs
```bash
# OpenRouter
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models

# Portkey  
curl -H "Authorization: Bearer $PORTKEY_API_KEY" \
     https://api.portkey.ai/v1/models

# OpenAI
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

---

## 💬 Performance-Focused Prompts

### Database Optimization
```
"Optimize this query for better performance"
"Add proper indexing to slow queries" 
"Implement connection pooling"
"Add query result caching"
"Eliminate N+1 query patterns"
```

### API Optimization
```
"Add timeout handling to HTTP requests"
"Implement async/await for I/O operations"
"Add Redis caching to expensive operations"
"Implement rate limiting and circuit breakers"
"Add comprehensive error handling"
```

### Memory Optimization
```
"Use generators instead of lists for large datasets"
"Implement proper cleanup in context managers"
"Profile memory usage and fix leaks"
"Optimize data structures for efficiency"
"Add memory monitoring and alerts"
```

### Stability Improvements
```
"Add comprehensive error handling"
"Implement graceful degradation"
"Add health checks and monitoring"
"Implement retry logic with backoff"
"Add circuit breaker pattern"
```

---

## 🎯 Daily Workflow

### 1. Start Development
```bash
# Local
cd orchestra-main && cursor .

# Remote
cd ~/orchestra-main
```

### 2. AI-Assisted Coding
- **:** `switch to developer mode`
- **Cursor:** `Ctrl+K` + performance task
- **Codex:** `codex "optimize this module"`

### 3. Performance Check
- Check AI Tools Dashboard
- Run performance analysis
- Monitor metrics and alerts

### 4. Optimization
- Apply performance prompts
- Use stability-focused commands
- Verify improvements in dashboard

---

## 🚨 Quick Troubleshooting

### SSH Issues
```bash
ls -la ~/.ssh/            # Check SSH keys
```

### MCP Server Issues
```bash
pkill -f mcp_server       # Kill servers
# Restart servers
python mcp_server/servers/ai_coding_assistant.py &
```

### API Issues
```bash
echo $OPENROUTER_API_KEY  # Check API keys
curl -I https://openrouter.ai/api/v1/models  # Test connectivity
```

### Performance Issues
```bash
python scripts/cleanup_repository.py  # Clean repository
# Check dashboard metrics
# Monitor database performance
```

---

## 📈 Performance Targets

- **API Response:** < 200ms
- **AI Tool Response:** < 2s  
- **Database Queries:** < 100ms
- **System Uptime:** > 99.9%

---

## 🔑 Key Environment Variables

```bash
export OPENROUTER_API_KEY="your-key"
export PORTKEY_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GOOGLE_API_KEY="your-key"
export FACTORY_AI_API_KEY="your-key"  # If available
```

---

## 📞 Quick Access

### Servers
- **Production:** 45.32.69.157
- **Database:** 45.77.87.106  
- **Staging:** 207.246.108.201

### Dashboards
- **Grafana:** http://207.246.108.201:3000
- **AI Tools:** https://fcqjsoot.manus.space

### Credentials
- **Grafana:** admin / OrchAI_Grafana_2024!
- **Database:** orchestra / OrchAI_DB_2024!

---

**🎯 Focus: Performance, Stability, and Optimization over Security/Cost**

