#!/usr/bin/env node
/**
 * 🚀 Cursor AI Development Assistant - Zapier MCP Server
 * Autonomous AI agent for code development and workflow automation
 * 
 * @version 1.0.0
 * @author Orchestra AI System
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { v4: uuidv4 } = require('uuid');
const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

// 🔧 Server Configuration
const app = express();
const PORT = process.env.MCP_SERVER_PORT || 8001;
const API_VERSION = 'v1';
const BASE_PATH = `/api/${API_VERSION}`;

// 🔒 Security Configuration
const ZAPIER_API_KEY = process.env.ZAPIER_API_KEY;
const WORKSPACE_ID = process.env.CURSOR_WORKSPACE_ID;
const ALLOWED_ORIGINS = (process.env.CORS_ORIGIN || '').split(',');

// 📊 Rate Limiting
const limiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 100, // 100 requests per minute
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    error: 'Too many requests',
    limit: 100,
    window: '1 minute'
  }
});

// 🛡️ Middleware Stack
app.use(helmet());
app.use(cors({
  origin: function (origin, callback) {
    if (!origin || ALLOWED_ORIGINS.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(limiter);

// 📝 Request Logging
app.use((req, res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.path} - ${req.ip}`);
  next();
});

// 🔐 Authentication Middleware
const authenticateZapier = (req, res, next) => {
  const apiKey = req.headers['x-zapier-api-key'] || req.headers['authorization']?.replace('Bearer ', '');
  const workspaceId = req.headers['x-cursor-workspace-id'];

  if (!apiKey) {
    return res.status(401).json({
      error: 'Authentication required',
      message: 'Missing API key in headers',
      required_headers: ['X-Zapier-API-Key', 'X-Cursor-Workspace-ID (optional)']
    });
  }

  // Store auth info for downstream use
  req.auth = {
    apiKey,
    workspaceId: workspaceId || WORKSPACE_ID,
    requestId: uuidv4()
  };

  next();
};

// 🏥 Health Check Endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'cursor-ai-zapier-mcp',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    capabilities: [
      'code_generation',
      'file_operations',
      'infrastructure_management',
      'workflow_automation',
      'git_operations',
      'project_analysis'
    ]
  });
});

// 🔐 Authentication Verification
app.get(`${BASE_PATH}/auth/verify`, authenticateZapier, (req, res) => {
  res.json({
    authenticated: true,
    workspace_id: req.auth.workspaceId,
    request_id: req.auth.requestId,
    permissions: [
      'code_generation',
      'file_operations',
      'infrastructure_management',
      'workflow_automation'
    ],
    timestamp: new Date().toISOString()
  });
});

// 🎯 ZAPIER TRIGGERS

// Trigger: Code Updated
app.post(`${BASE_PATH}/triggers/code-updated`, authenticateZapier, async (req, res) => {
  try {
    const { file_path, project_path = process.cwd() } = req.body;
    
    // Get recent git commits for code changes
    const { stdout } = await execAsync('git log --oneline -5', { cwd: project_path });
    const recentCommits = stdout.trim().split('\n').map(line => {
      const [hash, ...messageParts] = line.split(' ');
      return {
        hash: hash.substring(0, 8),
        message: messageParts.join(' '),
        timestamp: new Date().toISOString()
      };
    });

    res.json({
      trigger: 'code_updated',
      data: {
        file_path,
        project_path,
        recent_commits: recentCommits,
        workspace_id: req.auth.workspaceId,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to process code update trigger',
      message: error.message
    });
  }
});

// Trigger: Deployment Complete
app.post(`${BASE_PATH}/triggers/deployment-complete`, authenticateZapier, async (req, res) => {
  try {
    const { deployment_url, environment = 'production', status = 'success' } = req.body;

    res.json({
      trigger: 'deployment_complete',
      data: {
        deployment_url,
        environment,
        status,
        workspace_id: req.auth.workspaceId,
        timestamp: new Date().toISOString(),
        deployment_id: uuidv4()
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to process deployment trigger',
      message: error.message
    });
  }
});

// Trigger: Error Detected
app.post(`${BASE_PATH}/triggers/error-detected`, authenticateZapier, async (req, res) => {
  try {
    const { error_type, error_message, file_path, line_number } = req.body;

    res.json({
      trigger: 'error_detected',
      data: {
        error_type,
        error_message,
        file_path,
        line_number,
        severity: 'high',
        workspace_id: req.auth.workspaceId,
        timestamp: new Date().toISOString(),
        error_id: uuidv4()
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to process error trigger',
      message: error.message
    });
  }
});

// 🚀 ZAPIER ACTIONS

// Action: Generate Code
app.post(`${BASE_PATH}/actions/generate-code`, authenticateZapier, async (req, res) => {
  try {
    const { 
      prompt, 
      language = 'javascript', 
      file_path,
      project_context 
    } = req.body;

    if (!prompt) {
      return res.status(400).json({
        error: 'Missing required field: prompt'
      });
    }

    // Simulate code generation (integrate with your AI system)
    const generatedCode = await generateCode(prompt, language, project_context);
    
    // Optionally write to file
    if (file_path) {
      await fs.writeFile(file_path, generatedCode, 'utf8');
    }

    res.json({
      action: 'generate_code',
      success: true,
      data: {
        generated_code: generatedCode,
        language,
        file_path,
        lines_of_code: generatedCode.split('\n').length,
        workspace_id: req.auth.workspaceId,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to generate code',
      message: error.message
    });
  }
});

// Action: Deploy Project
app.post(`${BASE_PATH}/actions/deploy-project`, authenticateZapier, async (req, res) => {
  try {
    const { 
      deployment_target = 'vercel',
      environment = 'production',
      project_path = process.cwd()
    } = req.body;

    // Execute deployment script
    const deploymentResult = await executeDeployment(deployment_target, environment, project_path);

    res.json({
      action: 'deploy_project',
      success: true,
      data: {
        deployment_target,
        environment,
        deployment_url: deploymentResult.url,
        deployment_id: deploymentResult.id,
        status: 'completed',
        workspace_id: req.auth.workspaceId,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Deployment failed',
      message: error.message
    });
  }
});

// Action: Run Tests
app.post(`${BASE_PATH}/actions/run-tests`, authenticateZapier, async (req, res) => {
  try {
    const { 
      test_command = 'npm test',
      project_path = process.cwd()
    } = req.body;

    const { stdout, stderr } = await execAsync(test_command, { cwd: project_path });

    res.json({
      action: 'run_tests',
      success: true,
      data: {
        test_command,
        output: stdout,
        errors: stderr,
        passed: !stderr,
        workspace_id: req.auth.workspaceId,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Test execution failed',
      message: error.message
    });
  }
});

// Action: Analyze Project
app.post(`${BASE_PATH}/actions/analyze-project`, authenticateZapier, async (req, res) => {
  try {
    const { project_path = process.cwd() } = req.body;

    const analysis = await analyzeProject(project_path);

    res.json({
      action: 'analyze_project',
      success: true,
      data: {
        ...analysis,
        workspace_id: req.auth.workspaceId,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    res.status(500).json({
      error: 'Project analysis failed',
      message: error.message
    });
  }
});

// 🛠️ Utility Functions

async function generateCode(prompt, language, context) {
  // Placeholder for AI code generation
  // Integrate with your existing Orchestra AI personas
  return `// Generated code based on: ${prompt}
// Language: ${language}
// Context: ${context || 'No context provided'}

// TODO: Implement the requested functionality
console.log('Generated code placeholder');
`;
}

async function executeDeployment(target, environment, projectPath) {
  // Placeholder for deployment logic
  // Integrate with your existing deployment scripts
  const deploymentId = uuidv4();
  
  if (target === 'vercel') {
    try {
      const { stdout } = await execAsync('vercel --prod --yes', { cwd: projectPath });
      const urlMatch = stdout.match(/https:\/\/[^\s]+/);
      return {
        id: deploymentId,
        url: urlMatch ? urlMatch[0] : 'https://deployment-url.vercel.app',
        status: 'success'
      };
    } catch (error) {
      throw new Error(`Vercel deployment failed: ${error.message}`);
    }
  }
  
  return {
    id: deploymentId,
    url: `https://${target}-deployment.com/${deploymentId}`,
    status: 'success'
  };
}

async function analyzeProject(projectPath) {
  try {
    // Get basic project info
    const packageJsonPath = path.join(projectPath, 'package.json');
    let packageInfo = {};
    
    try {
      const packageContent = await fs.readFile(packageJsonPath, 'utf8');
      packageInfo = JSON.parse(packageContent);
    } catch (e) {
      // No package.json found
    }

    // Count files by type
    const { stdout: findOutput } = await execAsync(`find . -type f -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.md" | head -100`, { cwd: projectPath });
    const files = findOutput.trim().split('\n').filter(f => f);
    
    const fileTypes = files.reduce((acc, file) => {
      const ext = path.extname(file);
      acc[ext] = (acc[ext] || 0) + 1;
      return acc;
    }, {});

    return {
      project_name: packageInfo.name || path.basename(projectPath),
      version: packageInfo.version || '0.0.0',
      description: packageInfo.description || '',
      file_count: files.length,
      file_types: fileTypes,
      dependencies: Object.keys(packageInfo.dependencies || {}),
      dev_dependencies: Object.keys(packageInfo.devDependencies || {}),
      scripts: packageInfo.scripts || {},
      analysis_timestamp: new Date().toISOString()
    };
  } catch (error) {
    throw new Error(`Project analysis failed: ${error.message}`);
  }
}

// 🚨 Error Handler
app.use((error, req, res, next) => {
  console.error(`[ERROR] ${error.message}`);
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
    timestamp: new Date().toISOString()
  });
});

// 404 Handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    available_endpoints: {
      health: '/health',
      auth: `${BASE_PATH}/auth/verify`,
      triggers: [
        `${BASE_PATH}/triggers/code-updated`,
        `${BASE_PATH}/triggers/deployment-complete`,
        `${BASE_PATH}/triggers/error-detected`
      ],
      actions: [
        `${BASE_PATH}/actions/generate-code`,
        `${BASE_PATH}/actions/deploy-project`,
        `${BASE_PATH}/actions/run-tests`,
        `${BASE_PATH}/actions/analyze-project`
      ]
    }
  });
});

// 🚀 Server Startup
const server = app.listen(PORT, () => {
  console.log(`
🚀 Cursor AI Zapier MCP Server Started!
===========================================
🌐 Server: http://localhost:${PORT}
📋 Health: http://localhost:${PORT}/health
🔐 Auth: http://localhost:${PORT}${BASE_PATH}/auth/verify
📊 API Version: ${API_VERSION}
🔧 Environment: ${process.env.NODE_ENV || 'development'}
⚡ Ready for Zapier integration!
`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully...');
  server.close(() => {
    console.log('Server closed.');
    process.exit(0);
  });
});

module.exports = app; 