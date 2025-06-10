# 🚀 Cursor AI Development Assistant - Zapier Integration Specifications

## 📋 **INTEGRATION OVERVIEW**

**Integration Name**: Cursor AI Development Assistant  
**Description**: Autonomous AI agent for code development, infrastructure management, and workflow automation  
**Category**: Developer Tools  
**Version**: 1.0.0  
**Homepage URL**: https://github.com/ai-cherry/orchestra-main  
**Support URL**: https://github.com/ai-cherry/orchestra-main/issues  

---

## 🔐 **AUTHENTICATION CONFIGURATION**

### **Authentication Type**: API Key

### **Authentication Fields**:
```json
{
  "api_key": {
    "type": "password",
    "required": true,
    "label": "API Key",
    "help_text": "Your Cursor AI API key. Generate one at http://localhost:8010/docs"
  },
  "workspace_id": {
    "type": "string", 
    "required": false,
    "label": "Workspace ID",
    "help_text": "Optional workspace identifier for multi-workspace setups"
  }
}
```

### **Authentication Test Endpoint**:
- **URL**: `http://localhost:8001/api/v1/auth/verify`
- **Method**: GET
- **Headers**: 
  - `X-Zapier-API-Key: {{bundle.authData.api_key}}`
  - `X-Cursor-Workspace-ID: {{bundle.authData.workspace_id}}`

---

## 🎯 **TRIGGERS**

### **1. Code Updated**
**Key**: `code_updated`  
**Name**: Code Updated  
**Description**: Triggers when code changes are detected in your project  

**Endpoint**: `POST /api/v1/triggers/code-updated`

**Sample Response**:
```json
{
  "trigger": "code_updated",
  "data": {
    "file_path": "/src/components/App.js",
    "project_path": "/home/user/my-project",
    "recent_commits": [
      {
        "hash": "abc12345",
        "message": "Add new feature",
        "timestamp": "2025-06-10T17:30:00Z"
      }
    ],
    "workspace_id": "my-workspace",
    "timestamp": "2025-06-10T17:30:00Z"
  }
}
```

### **2. Deployment Complete**
**Key**: `deployment_complete`  
**Name**: Deployment Complete  
**Description**: Triggers when a deployment finishes  

**Endpoint**: `POST /api/v1/triggers/deployment-complete`

**Sample Response**:
```json
{
  "trigger": "deployment_complete",
  "data": {
    "deployment_url": "https://my-app.vercel.app",
    "environment": "production",
    "status": "success",
    "workspace_id": "my-workspace",
    "deployment_id": "dep_abc123",
    "timestamp": "2025-06-10T17:30:00Z"
  }
}
```

### **3. Error Detected**
**Key**: `error_detected`  
**Name**: Error Detected  
**Description**: Triggers when errors are found in your code  

**Endpoint**: `POST /api/v1/triggers/error-detected`

**Sample Response**:
```json
{
  "trigger": "error_detected",
  "data": {
    "error_type": "SyntaxError",
    "error_message": "Unexpected token ';'",
    "file_path": "/src/utils/helper.js",
    "line_number": 42,
    "severity": "high",
    "workspace_id": "my-workspace",
    "error_id": "err_xyz789",
    "timestamp": "2025-06-10T17:30:00Z"
  }
}
```

---

## 🚀 **ACTIONS**

### **1. Generate Code**
**Key**: `generate_code`  
**Name**: Generate Code  
**Description**: Generate code based on natural language prompts  

**Endpoint**: `POST /api/v1/actions/generate-code`

**Input Fields**:
```json
{
  "prompt": {
    "type": "text",
    "required": true,
    "label": "Code Prompt",
    "help_text": "Describe what code you want to generate"
  },
  "language": {
    "type": "string",
    "required": false,
    "default": "javascript",
    "choices": ["javascript", "python", "typescript", "react", "html", "css"],
    "label": "Programming Language"
  },
  "file_path": {
    "type": "string",
    "required": false,
    "label": "File Path",
    "help_text": "Optional path to save the generated code"
  }
}
```

**Sample Response**:
```json
{
  "action": "generate_code",
  "success": true,
  "data": {
    "generated_code": "function hello() {\n  console.log('Hello World!');\n}",
    "language": "javascript",
    "file_path": "/src/hello.js",
    "lines_of_code": 3,
    "workspace_id": "my-workspace",
    "timestamp": "2025-06-10T17:30:00Z"
  }
}
```

### **2. Deploy Project**
**Key**: `deploy_project`  
**Name**: Deploy Project  
**Description**: Deploy your project to various platforms  

**Endpoint**: `POST /api/v1/actions/deploy-project`

**Input Fields**:
```json
{
  "deployment_target": {
    "type": "string",
    "required": false,
    "default": "vercel",
    "choices": ["vercel", "netlify", "heroku", "aws", "docker"],
    "label": "Deployment Target"
  },
  "environment": {
    "type": "string",
    "required": false,
    "default": "production",
    "choices": ["development", "staging", "production"],
    "label": "Environment"
  },
  "project_path": {
    "type": "string",
    "required": false,
    "label": "Project Path",
    "help_text": "Path to your project (defaults to current directory)"
  }
}
```

**Sample Response**:
```json
{
  "action": "deploy_project",
  "success": true,
  "data": {
    "deployment_target": "vercel",
    "environment": "production",
    "deployment_url": "https://my-app-abc123.vercel.app",
    "deployment_id": "dep_xyz789",
    "status": "completed",
    "workspace_id": "my-workspace",
    "timestamp": "2025-06-10T17:30:00Z"
  }
}
```

### **3. Run Tests**
**Key**: `run_tests`  
**Name**: Run Tests  
**Description**: Execute test suites for your project  

**Endpoint**: `POST /api/v1/actions/run-tests`

**Input Fields**:
```json
{
  "test_command": {
    "type": "string",
    "required": false,
    "default": "npm test",
    "label": "Test Command",
    "help_text": "Command to run tests (e.g., 'npm test', 'pytest', 'jest')"
  },
  "project_path": {
    "type": "string",
    "required": false,
    "label": "Project Path"
  }
}
```

**Sample Response**:
```json
{
  "action": "run_tests",
  "success": true,
  "data": {
    "test_command": "npm test",
    "output": "✓ All tests passed\n10 tests, 10 passed",
    "errors": "",
    "passed": true,
    "workspace_id": "my-workspace",
    "timestamp": "2025-06-10T17:30:00Z"
  }
}
```

### **4. Analyze Project**
**Key**: `analyze_project`  
**Name**: Analyze Project  
**Description**: Analyze project structure, dependencies, and health  

**Endpoint**: `POST /api/v1/actions/analyze-project`

**Input Fields**:
```json
{
  "project_path": {
    "type": "string",
    "required": false,
    "label": "Project Path"
  }
}
```

**Sample Response**:
```json
{
  "action": "analyze_project",
  "success": true,
  "data": {
    "project_name": "my-awesome-app",
    "version": "1.2.3",
    "description": "An awesome web application",
    "file_count": 156,
    "file_types": {
      ".js": 45,
      ".ts": 23,
      ".css": 12,
      ".md": 5
    },
    "dependencies": ["react", "express", "lodash"],
    "dev_dependencies": ["jest", "webpack", "eslint"],
    "scripts": {
      "start": "node server.js",
      "test": "jest",
      "build": "webpack"
    },
    "workspace_id": "my-workspace",
    "timestamp": "2025-06-10T17:30:00Z"
  }
}
```

---

## 🌐 **API ENDPOINTS SUMMARY**

### **Base URL**: `http://localhost:8001`
### **API Version**: `v1`

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/health` | GET | Health check | No |
| `/api/v1/auth/verify` | GET | Authentication test | Yes |
| `/api/v1/triggers/code-updated` | POST | Code update trigger | Yes |
| `/api/v1/triggers/deployment-complete` | POST | Deployment trigger | Yes |
| `/api/v1/triggers/error-detected` | POST | Error detection trigger | Yes |
| `/api/v1/actions/generate-code` | POST | Code generation action | Yes |
| `/api/v1/actions/deploy-project` | POST | Project deployment action | Yes |
| `/api/v1/actions/run-tests` | POST | Test execution action | Yes |
| `/api/v1/actions/analyze-project` | POST | Project analysis action | Yes |

---

## 🔧 **SETUP INSTRUCTIONS**

### **1. Installation**
```bash
cd zapier-mcp
npm install
```

### **2. Configuration**
```bash
# Copy environment template
cp environment.config .env

# Edit .env file with your settings
nano .env
```

### **3. Start Server**
```bash
# Using CLI
npm run setup
zapier-mcp start

# Or directly
node server.js
```

### **4. Test Integration**
```bash
# Health check
curl http://localhost:8001/health

# Test authentication
zapier-mcp test-auth --api-key your_api_key

# Test trigger
zapier-mcp test-trigger --type code-updated
```

---

## 🎨 **LOGO SPECIFICATION**

### **ASCII Logo**:
```
   ▄████████ ███    █▄  ▄████████    ▄████████  ▄██████▄     ▄████████ 
  ███    ███ ███    ███ ███    ███   ███    ███ ███    ███   ███    ███ 
  ███    █▀  ███    ███ ███    ███   ███    █▀  ███    ███   ███    ███ 
  ███        ███    ███ ███    ███   ███        ███    ███  ▄███▄▄▄▄██▀ 
  ███        ███    ███ ███▄▄▄▄███ ▀███████████ ███    ███ ▀▀███▀▀▀▀▀   
  ███    █▄  ███    ███ ███    ███          ███ ███    ███ ▀███████████ 
  ███    ███ ███    ███ ███    ███    ▄█    ███ ███    ███   ███    ███ 
  ████████▀  ████████▀  ███    █▀   ▄████████▀   ▀██████▀    ███    ███ 
                                                              ███    ███ 
```

### **Logo Requirements**:
- **Format**: PNG, SVG
- **Size**: 256x256px minimum
- **Background**: Transparent preferred
- **Colors**: Modern, tech-focused palette
- **Style**: Clean, professional, AI-themed

---

## 📚 **ADDITIONAL RESOURCES**

### **Documentation**:
- **API Docs**: `http://localhost:8001/api/v1/docs`
- **GitHub**: https://github.com/ai-cherry/orchestra-main
- **CLI Help**: `zapier-mcp --help`

### **Support**:
- **Issues**: https://github.com/ai-cherry/orchestra-main/issues
- **Discussions**: https://github.com/ai-cherry/orchestra-main/discussions

### **Rate Limits**:
- **Requests per minute**: 100
- **Burst limit**: 20
- **Timeout**: 30 seconds

### **Security**:
- **HTTPS**: Required in production
- **CORS**: Configured for Zapier domains
- **API Key**: Required for all authenticated endpoints
- **Rate limiting**: Implemented to prevent abuse

---

## 🚀 **READY FOR ZAPIER DEVELOPER PLATFORM**

This integration is fully prepared for submission to the Zapier Developer Platform with:

✅ Complete API endpoints  
✅ Authentication system  
✅ Comprehensive documentation  
✅ CLI management tools  
✅ Production-ready configuration  
✅ Error handling and logging  
✅ Rate limiting and security  
✅ Health monitoring  

**Next Step**: Submit to Zapier Developer Platform using the specifications above! 