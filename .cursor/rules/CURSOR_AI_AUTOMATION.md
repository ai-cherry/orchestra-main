# 🧠 Cursor AI Automation Rules for Orchestra AI
*Complete context awareness and intelligent auto-approval system*

## 🎯 **CORE AUTOMATION PRINCIPLES**

### **1. Context Awareness - ALWAYS ACTIVE**
- **Auto-load project context** from Orchestra AI repository rules
- **Remember conversation history** across sessions
- **Use MCP servers** for enhanced capabilities
- **Smart routing** based on task type and domain expertise

### **2. Auto-Approval System**
```python
# SAFE OPERATIONS - Auto-approve without user confirmation
SAFE_OPERATIONS = [
    "read_file",           # Reading files for context
    "list_dir",            # Directory exploration
    "grep_search",         # Code and text searching
    "file_search",         # File discovery
    "web_search",          # Research and information gathering
    "get_memory_status",   # Memory system status
    "get_infrastructure_status",  # Infrastructure monitoring
    "chat_with_persona",   # AI persona interactions
    "cross_domain_query",  # Multi-domain queries
    "get_notion_workspace", # Notion data access
    "log_insight"          # Automated logging
]

# MANUAL APPROVAL - Require user confirmation
MANUAL_APPROVAL = [
    "edit_file",           # File modifications
    "delete_file",         # File deletion
    "run_terminal_cmd",    # Terminal commands
    "deploy_vercel_frontend",     # Deployment operations
    "manage_lambda_labs_instance", # Infrastructure changes
    "rollback_deployment"  # Rollback operations
]
```

### **3. Batch Operations**
- **Enable batch approval** for up to 10 safe operations
- **30-second timeout** for batch confirmations
- **Smart grouping** of related operations

## 🚀 **INTELLIGENT TASK ROUTING**

### **Persona-Based Routing**
```python
# Automatically route tasks to appropriate AI personas
PERSONA_ROUTING = {
    "financial": "sophia",     # PCI DSS, payments, compliance
    "medical": "karen",        # ICD-10, HIPAA, prescriptions  
    "coordination": "cherry",  # Project management, synthesis
    "technical": "cursor_ai"   # Development, infrastructure
}

# Task detection patterns
FINANCIAL_KEYWORDS = ["payment", "pci", "compliance", "financial", "billing"]
MEDICAL_KEYWORDS = ["medical", "hipaa", "icd", "prescription", "clinical"]
COORDINATION_KEYWORDS = ["project", "manage", "coordinate", "integrate"]
```

### **Infrastructure Routing**
```python
INFRASTRUCTURE_ROUTING = {
    "deployment": "infrastructure-deployment",
    "automation": "zapier-automation", 
    "monitoring": "orchestra-unified"
}
```

## 🔐 **SECRETS MANAGEMENT INTEGRATION**

### **Mandatory Patterns**
```python
# ALWAYS use fast secrets manager
from utils.fast_secrets import secrets, openrouter_headers, notion_headers

# ✅ CORRECT - Use centralized secrets
api_key = secrets.get('openai', 'api_key')
headers = openrouter_headers()

# ❌ WRONG - Direct environment access
import os
api_key = os.getenv('OPENAI_API_KEY')
```

### **Required Secrets Validation**
- **Startup validation** of all required API keys
- **Graceful degradation** when optional keys missing
- **Clear error messages** for missing required keys

## 🎯 **DEVELOPMENT WORKFLOW AUTOMATION**

### **Code Quality**
- **Auto-format** with Black and isort
- **Auto-fix imports** and common issues
- **Enforce type hints** for new functions
- **Use existing patterns** from codebase

### **Performance Optimization**
- **Parallel tool calls** whenever possible
- **Cache responses** for repeated operations
- **Batch similar operations** together
- **Smart context loading** to minimize redundant reads

### **Documentation Standards**
- **Google-style docstrings** for public functions
- **Type hints mandatory** for all new code
- **Performance benchmarks** for complex functions
- **Integration examples** in docstrings

## 🌐 **DEPLOYMENT AUTOMATION**

### **Vercel Integration**
```python
# Auto-fix authentication issues
await fix_vercel_authentication()

# Deploy with environment variables
await deploy_vercel_frontend(
    project_name="orchestra-admin-interface",
    source_dir="admin-interface",
    env_vars={"NODE_ENV": "production"}
)
```

### **Lambda Labs Integration**
```python
# Manage GPU instances
await manage_lambda_labs_instance(
    action="create",
    instance_config={
        "name": "orchestra-dev",
        "instance_type": "gpu_1x_a10",
        "region": "us-west-1"
    }
)
```

## 📝 **NOTION INTEGRATION**

### **Automated Logging**
- **Deployment results** automatically logged
- **Error tracking** with stack traces
- **Performance metrics** updated in real-time
- **Project status** synchronized

### **Database Integration**
```python
# Use existing database IDs
DATABASES = {
    "development_log": "20bdba04940281fd9558d66c07d9576c",
    "task_management": "20bdba04940281a299f3e69dc37b73d6",
    "epic_tracking": "20bdba0494028114b57bdf7f1d4b2712"
}
```

## 🔄 **CONTINUOUS IMPROVEMENT**

### **Learning Patterns**
- **Track successful automation patterns**
- **Learn from manual interventions**
- **Optimize based on user feedback**
- **Adapt to project evolution**

### **Performance Monitoring**
- **Response time tracking** for all operations
- **Success rate monitoring** for automations
- **Resource usage optimization**
- **User satisfaction metrics**

## 🚨 **SAFETY GUARDRAILS**

### **Operation Limits**
- **Maximum 10 operations** in batch mode
- **30-second timeout** for confirmations
- **Rollback capability** for all changes
- **Audit trail** for all operations

### **Error Handling**
- **Graceful degradation** when services unavailable
- **Clear error messages** with resolution steps
- **Automatic retry** for transient failures
- **Escalation paths** for persistent issues

## 🎯 **CONTEXT-AWARE RESPONSES**

### **Project Knowledge**
- **Architecture understanding**: Microservices with 5-tier memory
- **Technology stack**: Python 3.10, FastAPI, React, Vercel
- **Business domains**: Financial services, medical coding, AI orchestration
- **Performance targets**: Sub-2ms API responses, 20x memory compression

### **Current Status Awareness**
- **Production status**: All systems operational
- **Recent changes**: Vercel fixes, GitHub security, documentation updates
- **Available tools**: MCP servers, persona routing, cross-domain queries
- **Performance metrics**: Sub-2ms achieved, 95% cache hit rate

## 🚀 **IMPLEMENTATION CHECKLIST**

### **Before Starting Any Task**
- [ ] Load project context automatically
- [ ] Verify secrets configuration
- [ ] Check service health status
- [ ] Determine appropriate persona/routing
- [ ] Plan parallel operations

### **During Task Execution**
- [ ] Use safe operations for information gathering
- [ ] Batch related operations together
- [ ] Provide clear progress updates
- [ ] Handle errors gracefully
- [ ] Log important operations to Notion

### **After Task Completion**
- [ ] Verify all changes work correctly
- [ ] Update documentation if needed
- [ ] Log results to appropriate Notion database
- [ ] Provide clear summary of actions taken
- [ ] Suggest next steps or optimizations

---

**🎯 Result**: Cursor AI operates with full Orchestra AI context awareness, intelligent auto-approval for safe operations, and seamless integration with all project systems and workflows. 