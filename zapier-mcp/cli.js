#!/usr/bin/env node
/**
 * 🛠️ Cursor AI Zapier MCP CLI Tool
 * Command-line interface for managing Zapier integrations
 * 
 * @version 1.0.0
 * @author Orchestra AI System
 */

const { Command } = require('commander');
const fs = require('fs').promises;
const path = require('path');
const { spawn, exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);
const program = new Command();

program
  .name('zapier-mcp')
  .description('Cursor AI Zapier MCP Server CLI')
  .version('1.0.0');

// 🚀 Start server command
program
  .command('start')
  .description('Start the Zapier MCP server')
  .option('-p, --port <port>', 'Server port', '8001')
  .option('-e, --env <environment>', 'Environment', 'production')
  .option('-d, --daemon', 'Run as daemon')
  .action(async (options) => {
    console.log('🚀 Starting Cursor AI Zapier MCP Server...');
    
    try {
      // Load environment variables
      await loadEnvironment();
      
      const port = options.port || process.env.MCP_SERVER_PORT || 8001;
      const env = options.env || process.env.NODE_ENV || 'production';
      
      console.log(`📋 Configuration:`);
      console.log(`   Port: ${port}`);
      console.log(`   Environment: ${env}`);
      
      if (options.daemon) {
        console.log('🔄 Starting as daemon...');
        const child = spawn('node', ['server.js'], {
          detached: true,
          stdio: 'ignore',
          env: { ...process.env, MCP_SERVER_PORT: port, NODE_ENV: env }
        });
        child.unref();
        console.log(`✅ Server started as daemon with PID: ${child.pid}`);
      } else {
        console.log('🔄 Starting server...');
        const child = spawn('node', ['server.js'], {
          stdio: 'inherit',
          env: { ...process.env, MCP_SERVER_PORT: port, NODE_ENV: env }
        });
        
        process.on('SIGINT', () => {
          console.log('\n🛑 Shutting down server...');
          child.kill('SIGTERM');
          process.exit(0);
        });
      }
    } catch (error) {
      console.error('❌ Failed to start server:', error.message);
      process.exit(1);
    }
  });

// 🛑 Stop server command
program
  .command('stop')
  .description('Stop the Zapier MCP server')
  .action(async () => {
    console.log('🛑 Stopping Zapier MCP server...');
    
    try {
      const { stdout } = await execAsync("ps aux | grep 'node.*server.js' | grep -v grep | awk '{print $2}'");
      const pids = stdout.trim().split('\n').filter(pid => pid);
      
      if (pids.length === 0) {
        console.log('ℹ️  No running server found.');
        return;
      }
      
      for (const pid of pids) {
        await execAsync(`kill ${pid}`);
        console.log(`✅ Stopped server with PID: ${pid}`);
      }
    } catch (error) {
      console.error('❌ Failed to stop server:', error.message);
      process.exit(1);
    }
  });

// 🏥 Health check command
program
  .command('health')
  .description('Check server health')
  .option('-p, --port <port>', 'Server port', '8001')
  .action(async (options) => {
    const port = options.port || process.env.MCP_SERVER_PORT || 8001;
    const healthUrl = `http://localhost:${port}/health`;
    
    console.log(`🏥 Checking server health at ${healthUrl}...`);
    
    try {
      const response = await fetch(healthUrl);
      const data = await response.json();
      
      if (response.ok) {
        console.log('✅ Server is healthy!');
        console.log(`📊 Status: ${data.status}`);
        console.log(`⏱️  Uptime: ${Math.floor(data.uptime)}s`);
        console.log(`🔧 Version: ${data.version}`);
      } else {
        console.log('❌ Server is unhealthy!');
        console.log(`📊 Status: ${response.status}`);
      }
    } catch (error) {
      console.log('❌ Server is not responding!');
      console.log(`🔍 Error: ${error.message}`);
      process.exit(1);
    }
  });

// 🔐 Test authentication command
program
  .command('test-auth')
  .description('Test Zapier authentication')
  .option('-k, --api-key <key>', 'API key to test')
  .option('-p, --port <port>', 'Server port', '8001')
  .action(async (options) => {
    const port = options.port || process.env.MCP_SERVER_PORT || 8001;
    const apiKey = options.apiKey || process.env.ZAPIER_API_KEY;
    
    if (!apiKey) {
      console.error('❌ No API key provided. Use --api-key or set ZAPIER_API_KEY environment variable.');
      process.exit(1);
    }
    
    const authUrl = `http://localhost:${port}/api/v1/auth/verify`;
    
    console.log('🔐 Testing authentication...');
    console.log(`📋 URL: ${authUrl}`);
    console.log(`🔑 API Key: ${apiKey.substring(0, 10)}...`);
    
    try {
      const response = await fetch(authUrl, {
        headers: {
          'X-Zapier-API-Key': apiKey,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (response.ok) {
        console.log('✅ Authentication successful!');
        console.log(`📋 Workspace ID: ${data.workspace_id}`);
        console.log(`🔧 Permissions: ${data.permissions.join(', ')}`);
      } else {
        console.log('❌ Authentication failed!');
        console.log(`📊 Status: ${response.status}`);
        console.log(`💬 Message: ${data.message}`);
      }
    } catch (error) {
      console.error('❌ Authentication test failed:', error.message);
      process.exit(1);
    }
  });

// 📋 Setup command
program
  .command('setup')
  .description('Setup Zapier MCP server')
  .action(async () => {
    console.log('🔧 Setting up Cursor AI Zapier MCP server...');
    
    try {
      // Create directories
      const dirs = ['logs', 'tests', 'config'];
      for (const dir of dirs) {
        await fs.mkdir(dir, { recursive: true });
        console.log(`📁 Created directory: ${dir}`);
      }
      
      // Copy environment template if .env doesn't exist
      const envExists = await fs.access('.env').then(() => true).catch(() => false);
      if (!envExists) {
        try {
          await fs.copyFile('environment.config', '.env');
          console.log('📋 Created .env from template');
        } catch (error) {
          console.log('⚠️  Could not create .env file. Please copy from environment.config');
        }
      }
      
      // Install dependencies
      console.log('📦 Installing dependencies...');
      await execAsync('npm install');
      console.log('✅ Dependencies installed');
      
      console.log('\n🎉 Setup complete!');
      console.log('\n📋 Next steps:');
      console.log('   1. Configure your .env file');
      console.log('   2. Run: zapier-mcp start');
      console.log('   3. Test: zapier-mcp health');
      
    } catch (error) {
      console.error('❌ Setup failed:', error.message);
      process.exit(1);
    }
  });

// 📊 Status command
program
  .command('status')
  .description('Show server status and logs')
  .option('-f, --follow', 'Follow logs')
  .action(async (options) => {
    console.log('📊 Zapier MCP Server Status');
    console.log('===========================');
    
    try {
      // Check if server is running
      const { stdout } = await execAsync("ps aux | grep 'node.*server.js' | grep -v grep");
      const processes = stdout.trim().split('\n').filter(line => line);
      
      if (processes.length > 0) {
        console.log('✅ Server is running');
        processes.forEach((process, index) => {
          const parts = process.split(/\s+/);
          console.log(`   Process ${index + 1}: PID ${parts[1]}, CPU ${parts[2]}%, Memory ${parts[3]}%`);
        });
      } else {
        console.log('❌ Server is not running');
      }
      
      // Show recent logs
      console.log('\n📝 Recent logs:');
      try {
        const logFile = './logs/zapier-mcp.log';
        const logExists = await fs.access(logFile).then(() => true).catch(() => false);
        
        if (logExists) {
          if (options.follow) {
            console.log('📺 Following logs (Ctrl+C to stop)...');
            const tail = spawn('tail', ['-f', logFile], { stdio: 'inherit' });
            
            process.on('SIGINT', () => {
              tail.kill('SIGTERM');
              process.exit(0);
            });
          } else {
            const { stdout: logs } = await execAsync(`tail -n 20 ${logFile}`);
            console.log(logs);
          }
        } else {
          console.log('   No log file found');
        }
      } catch (error) {
        console.log('   Could not read logs:', error.message);
      }
      
    } catch (error) {
      console.error('❌ Failed to get status:', error.message);
      process.exit(1);
    }
  });

// 🧪 Test triggers command
program
  .command('test-trigger')
  .description('Test Zapier trigger')
  .option('-t, --type <type>', 'Trigger type (code-updated, deployment-complete, error-detected)', null, true)
  .option('-p, --port <port>', 'Server port', '8001')
  .option('-k, --api-key <key>', 'API key')
  .action(async (options) => {
    if (!options.type) {
      console.error('❌ Type is required. Use --type or -t with one of: code-updated, deployment-complete, error-detected');
      process.exit(1);
    }
    const port = options.port || process.env.MCP_SERVER_PORT || 8001;
    const apiKey = options.apiKey || process.env.ZAPIER_API_KEY;
    
    if (!apiKey) {
      console.error('❌ No API key provided.');
      process.exit(1);
    }
    
    const triggerUrl = `http://localhost:${port}/api/v1/triggers/${options.type}`;
    
    // Test data for different trigger types
    const testData = {
      'code-updated': {
        file_path: '/test/example.js',
        project_path: process.cwd()
      },
      'deployment-complete': {
        deployment_url: 'https://test-deployment.vercel.app',
        environment: 'test',
        status: 'success'
      },
      'error-detected': {
        error_type: 'SyntaxError',
        error_message: 'Unexpected token',
        file_path: '/test/error.js',
        line_number: 42
      }
    };
    
    console.log(`🧪 Testing trigger: ${options.type}`);
    console.log(`📋 URL: ${triggerUrl}`);
    
    try {
      const response = await fetch(triggerUrl, {
        method: 'POST',
        headers: {
          'X-Zapier-API-Key': apiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(testData[options.type])
      });
      
      const data = await response.json();
      
      if (response.ok) {
        console.log('✅ Trigger test successful!');
        console.log('📊 Response:');
        console.log(JSON.stringify(data, null, 2));
      } else {
        console.log('❌ Trigger test failed!');
        console.log(`📊 Status: ${response.status}`);
        console.log('💬 Response:', JSON.stringify(data, null, 2));
      }
    } catch (error) {
      console.error('❌ Trigger test failed:', error.message);
      process.exit(1);
    }
  });

// 🛠️ Utility functions
async function loadEnvironment() {
  try {
    const envFile = await fs.readFile('.env', 'utf8');
    const lines = envFile.split('\n');
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        const value = valueParts.join('=');
        if (key && value) {
          process.env[key] = value;
        }
      }
    }
  } catch (error) {
    // .env file doesn't exist or can't be read
    console.log('⚠️  No .env file found. Using environment variables.');
  }
}

// 📋 Info command
program
  .command('info')
  .description('Show integration information for Zapier Developer Platform')
  .action(() => {
    console.log('📋 Cursor AI Development Assistant - Zapier Integration Info');
    console.log('============================================================');
    console.log('');
    console.log('🔧 Integration Details:');
    console.log('   Name: Cursor AI Development Assistant');
    console.log('   Description: Autonomous AI agent for code development and workflow automation');
    console.log('   Category: Developer Tools');
    console.log('   Authentication: API Key');
    console.log('');
    console.log('🌐 Server Details:');
    console.log(`   Base URL: http://localhost:${process.env.MCP_SERVER_PORT || 8001}`);
    console.log('   API Version: v1');
    console.log('');
    console.log('🔐 Authentication Fields:');
    console.log('   api_key (required): Your Cursor AI API key');
    console.log('   workspace_id (optional): Your workspace identifier');
    console.log('');
    console.log('🎯 Available Triggers:');
    console.log('   • Code Updated: Triggers when code changes are detected');
    console.log('   • Deployment Complete: Triggers when deployment finishes');
    console.log('   • Error Detected: Triggers when errors are found in code');
    console.log('');
    console.log('🚀 Available Actions:');
    console.log('   • Generate Code: Generate code based on prompts');
    console.log('   • Deploy Project: Deploy project to various platforms');
    console.log('   • Run Tests: Execute test suites');
    console.log('   • Analyze Project: Analyze project structure and dependencies');
    console.log('');
    console.log('📚 API Documentation: http://localhost:8001/api/v1/docs');
  });

program.parse(process.argv); 