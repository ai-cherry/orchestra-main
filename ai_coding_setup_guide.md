# 🚀 Complete AI Coding Tools Setup Guide

**Cherry AI Orchestrator - Optimized for Performance, Stability, and AI-Assisted Development**

---

## 📋 Prerequisites

### Local Development Machine (macOS)
- **Git** installed and configured
- **Cursor IDE** installed ([download here](https://cursor.sh/))
- **SSH access** to your Lambda servers
- **GitHub access** to ai-cherry/orchestra-main repository

### Remote Servers (Lambda Infrastructure)
- **Production Server:** 45.32.69.157 (4 CPU, 8GB RAM)
- **Database Server:** 45.77.87.106 (8 CPU, 32GB RAM)
- **Staging Server:** 207.246.108.201 (4 CPU, 8GB RAM)

---

## 🎯 Step 1: Local Repository Setup

### 1.1 Clone and Setup Repository

**On your Mac:**
```bash
# Clone the repository
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main

# Open in Cursor IDE
cursor .
```

### 1.2 Verify Repository Structure

**In Cursor IDE, you should see:**
```
orchestra-main/
├── .ai-tools/              # 🆕 AI tool configurations
├── admin-interface/        # Enhanced admin interface
├── infrastructure/         # Infrastructure management
├── mcp_server/            # MCP servers for AI tools
├── scripts/               # Utility scripts
└── README.md
```

**✅ Verification:** File explorer shows these directories in Cursor IDE

---

## 🔧 Step 2: Cursor IDE Optimization

### 2.1 Apply Workspace Settings

**In Cursor IDE:**
1. Open Command Palette (`Cmd+Shift+P`)
2. Type "Preferences: Open Workspace Settings (JSON)"
3. Replace content with:

```json
{
    "workbench.colorTheme": "Default Dark+",
    "editor.fontSize": 14,
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true,
        "source.fixAll": true
    },
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "git.autofetch": true,
    "git.enableSmartCommit": true,
    "extensions.autoUpdate": true,
    "ai.performance.priority": true,
    "ai.stability.focus": true,
    "ai.optimization.enabled": true,
    "remote.SSH.remotePlatform": {
        "45.32.69.157": "linux",
        "45.77.87.106": "linux", 
        "207.246.108.201": "linux"
    }
}
```

### 2.2 Install Recommended Extensions

**In Cursor IDE Extensions panel:**
- **Remote - SSH** (for server development)
- **Python** (Python language support)
- **GitLens** (Enhanced Git capabilities)
- **Thunder Client** (API testing)
- **Docker** (Container management)

**✅ Verification:** Extensions installed and workspace settings applied

---

## 🦘 Step 3:  Coder Setup

### 3.1 Verify  Configuration

**Check existing  setup:**
```bash
# In Cursor terminal
```

### 3.2 Test  Modes

**In  Coder:**
1. Open  interface
2. Try switching modes:
   - `switch to architect mode`
   - `switch to developer mode`
   - `switch to debugger mode`

### 3.3 Verify OpenRouter Integration

**Check API configuration:**
```bash
# Verify OpenRouter API key is set
echo $OPENROUTER_API_KEY
```

**✅ Verification:**  modes switch successfully and show different personalities

---

## 🤖 Step 4: OpenAI Codex Setup (SSH Integration)

### 4.1 SSH to Production Server

**From your Mac:**
```bash
# SSH to production server

# Navigate to project directory
cd ~/orchestra-main
```

### 4.2 Install Codex CLI (On Server)

**On the remote server:**
```bash
# Install Node.js if not present
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Codex CLI
npm install -g @openai/codex

# Set up environment
export OPENAI_API_KEY="your-openai-api-key"
echo 'export OPENAI_API_KEY="your-openai-api-key"' >> ~/.bashrc

# Test Codex
codex --version
```

### 4.3 Test Codex Integration

**On the remote server:**
```bash
# Test basic functionality
codex "Add a simple health check endpoint to this FastAPI app"

# Test with approval mode
codex --approval-mode full-auto "Optimize database queries in this file"
```

**✅ Verification:** Codex responds and can execute tasks on the server

---

## 🔍 Step 5: Google Jules Integration

### 5.1 Set Up Google API

**Configure Google API key:**
```bash
# On your Mac or server
export GOOGLE_API_KEY="your-google-api-key"
```

### 5.2 Test Jules Integration

**In Cursor IDE or terminal:**
```bash
# Test Google Jules via API
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Analyze this code for performance improvements"}' \
     https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp:generateContent
```

**✅ Verification:** Google API responds successfully

---

## 🏭 Step 6: Factory AI Integration

### 6.1 Check Factory AI API Availability

**Research Factory AI API:**
1. Visit [factory.ai](https://www.factory.ai/)
2. Look for API documentation
3. Sign up for API access if available

### 6.2 Configure Factory AI (If Available)

**If API is available:**
```bash
export FACTORY_AI_API_KEY="your-factory-ai-key"
```

**If API is not available:**
- Use the configuration as a template for future integration
- Focus on other AI tools for now

**✅ Verification:** Factory AI configuration ready (or noted as unavailable)

---

## 📊 Step 7: MCP Server Setup

### 7.1 Start MCP Servers

**On the production server:**
```bash
# Navigate to project directory
cd ~/orchestra-main

# Start MCP servers
python mcp_server/servers/ai_coding_assistant.py &
python mcp_server/servers/prompt_management.py &

# Check if servers are running
ps aux | grep mcp_server
```

### 7.2 Test MCP Server Connectivity

**Test the AI coding assistant:**
```bash
# Test MCP server endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
```

**✅ Verification:** MCP servers running and responding

---

## 🎨 Step 8: AI Tools Dashboard

### 8.1 Access the Dashboard

**Open in browser:**
- **Enhanced Admin Interface:** https://fcqjsoot.manus.space
- **AI Tools Dashboard:** https://fcqjsoot.manus.space/ai-tools-dashboard.html

### 8.2 Test Dashboard Functionality

**In the dashboard:**
1. **Tool Status:** Verify all AI tools show correct status
2. **Performance Metrics:** Check metrics are updating
3. **Prompt Management:** Test prompt loading and creation
4. **Terminal:** Execute test commands
5. **Repository Cleanup:** Run cleanup preview

**✅ Verification:** Dashboard loads and all features work

---

## 🧹 Step 9: Repository Cleanup

### 9.1 Preview Cleanup

**Run cleanup preview:**
```bash
# In project directory
python scripts/cleanup_repository.py --optimize-structure
```

### 9.2 Execute Cleanup (Optional)

**If preview looks good:**
```bash
# Execute actual cleanup
python scripts/cleanup_repository.py --execute --optimize-structure
```

**✅ Verification:** Repository cleaned and optimized for AI tools

---

## 🔗 Step 10: API Integration Testing

### 10.1 Test All APIs

**Run comprehensive API test:**
```bash
# Test OpenRouter
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models

# Test Portkey
curl -H "Authorization: Bearer $PORTKEY_API_KEY" \
     https://api.portkey.ai/v1/models

# Test OpenAI
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

### 10.2 Verify API Routing

**Test centralized API management:**
```bash
# Check unified API configuration
cat .ai-tools/apis/unified_config.json
```

**✅ Verification:** All APIs respond and routing works

---

## ✅ Step 11: Final Verification

### 11.1 Complete System Test

**Test each AI tool:**

1. ** Coder:**
   ```
   switch to architect mode
   optimize for performance
   ensure stability
   ```

2. **Cursor AI:**
   ```
   Ctrl+K: "Optimize this function for performance"
   @workspace: "Add error handling to API endpoints"
   ```

3. **OpenAI Codex (SSH):**
   ```bash
   codex "Add comprehensive logging to this module"
   ```

4. **Dashboard:**
   - All tools show "Active" status
   - Metrics are updating
   - Commands execute successfully

### 11.2 Performance Verification

**Check system performance:**
- **API Response Times:** < 2 seconds
- **MCP Server Uptime:** 99%+
- **Database Queries:** < 100ms
- **Memory Usage:** Optimal

**✅ Verification:** All systems operational and performing well

---

## 🎯 Usage Examples

### Daily Development Workflow

**1. Start Development Session:**
```bash
# On Mac
cd orchestra-main
cursor .

# SSH to server (in Cursor terminal)
cd ~/orchestra-main
```

**2. Use AI Tools for Coding:**

** Coder:**
- `switch to developer mode` - For implementation
- `optimize for performance` - For performance improvements
- `ensure stability` - For error handling and resilience

**Cursor AI:**
- `Ctrl+K` + "Add caching to this API endpoint"
- `@workspace` + "Find all database queries that need optimization"
- `Ctrl+I` + Select code + "Make this async"

**OpenAI Codex (on server):**
```bash
codex "Add comprehensive error handling to all API endpoints"
codex "Optimize database queries for better performance"
codex --approval-mode full-auto "Add Redis caching to frequently accessed data"
```

**3. Monitor and Optimize:**
- Check AI Tools Dashboard for performance metrics
- Use prompt management for consistent optimization
- Run repository cleanup as needed

### Performance Optimization Workflow

**1. Analyze Performance:**
```bash
# Use AI coding assistant
python -c "
from mcp_server.servers.ai_coding_assistant import *
ai_assistant = AICodingAssistant()
ai_assistant.analyze_performance({'directory': 'src/', 'include_database': True})
"
```

**2. Apply Optimizations:**
- Use performance prompts from dashboard
- Apply  Coder performance mode
- Execute Codex optimization tasks

**3. Verify Improvements:**
- Check metrics in dashboard
- Monitor API response times
- Verify database query performance

---

## 🚨 Troubleshooting

### Common Issues and Solutions

**1. Cursor IDE not connecting to servers:**
```bash
# Check SSH configuration

# Verify SSH keys
ls -la ~/.ssh/
```

**2.  Coder modes not working:**
- Ensure OpenRouter API key is set
- Restart  Coder after configuration changes

**3. MCP servers not responding:**
```bash
# Check server status
ps aux | grep mcp_server

# Restart servers
pkill -f mcp_server
python mcp_server/servers/ai_coding_assistant.py &
```

**4. API rate limits:**
- Check API usage in dashboard
- Use Portkey for rate limiting and fallbacks
- Implement caching for frequent requests

**5. Performance issues:**
- Run repository cleanup
- Check database query performance
- Monitor memory usage
- Optimize API response times

---

## 📈 Success Metrics

### Performance Targets
- **API Response Time:** < 200ms average
- **AI Tool Response:** < 2 seconds
- **Database Queries:** < 100ms
- **System Uptime:** > 99.9%

### Productivity Metrics
- **Code Quality Score:** Improved AST analysis
- **Development Speed:** Faster task completion
- **Error Rate:** Reduced production errors
- **Test Coverage:** Increased automated testing

### AI Tool Effectiveness
- **Context Accuracy:** AI tools understand project
- **Suggestion Quality:** Relevant and useful suggestions
- **Automation Level:** High percentage of automated tasks
- **Developer Satisfaction:** Improved development experience

---

## 🔄 Maintenance and Updates

### Weekly Tasks
- Review AI tool performance metrics
- Update prompt templates based on usage
- Check API usage and costs
- Monitor system health and performance

### Monthly Tasks
- Update AI tool configurations
- Review and optimize MCP servers
- Update documentation and guides
- Evaluate new AI tools and APIs

### Quarterly Tasks
- Major configuration updates
- Performance benchmarking
- Security and compliance review
- Evaluate new AI coding tools

---

**🎉 Congratulations! Your Cherry AI Orchestrator is now optimized for AI-assisted development with performance, stability, and optimization as the primary focus.**

