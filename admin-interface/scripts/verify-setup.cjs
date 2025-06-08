#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Orchestra AI Setup...\n');

let issues = 0;
let warnings = 0;

// Check environment files
console.log('📁 Checking environment files...');
const envLocal = path.join(__dirname, '../.env.local');
const envExample = path.join(__dirname, '../.env.example');

if (fs.existsSync(envLocal)) {
  console.log('✅ .env.local exists');
} else {
  console.log('❌ .env.local missing - create from .env.example');
  issues++;
}

if (fs.existsSync(envExample)) {
  console.log('✅ .env.example exists');
} else {
  console.log('❌ .env.example missing');
  issues++;
}

// Check .gitignore
console.log('\n🔒 Checking .gitignore...');
const gitignorePath = path.join(__dirname, '../.gitignore');
if (fs.existsSync(gitignorePath)) {
  const gitignoreContent = fs.readFileSync(gitignorePath, 'utf8');
  const requiredEntries = ['.env.local', '.env', '*.key', 'secrets/'];
  
  requiredEntries.forEach(entry => {
    if (gitignoreContent.includes(entry)) {
      console.log(`✅ ${entry} is in .gitignore`);
    } else {
      console.log(`⚠️  ${entry} should be in .gitignore`);
      warnings++;
    }
  });
} else {
  console.log('❌ .gitignore missing');
  issues++;
}

// Check API config service
console.log('\n⚙️  Checking API configuration...');
const apiConfigPath = path.join(__dirname, '../src/config/apiConfig.ts');
if (fs.existsSync(apiConfigPath)) {
  console.log('✅ API config service exists');
  
  const configContent = fs.readFileSync(apiConfigPath, 'utf8');
  if (configContent.includes('import.meta.env')) {
    console.log('✅ API config uses environment variables');
  } else {
    console.log('❌ API config might not be using environment variables');
    issues++;
  }
} else {
  console.log('❌ API config service missing');
  issues++;
}

// Check service files for hardcoded keys
console.log('\n🔑 Checking for hardcoded API keys...');
const serviceFiles = [
  'portkeyService.ts',
  'searchService.ts',
  'elevenLabsService.ts',
  'airbyteService.ts',
  'slideSpeakService.ts',
  'notionWorkflowService.ts',
  'aiLearningService.ts'
];

const suspiciousPatterns = [
  /apiKey\s*=\s*['"][a-zA-Z0-9\-_]{10,}['"]/,
  /token\s*=\s*['"][a-zA-Z0-9\-_]{10,}['"]/,
  /Bearer\s+[a-zA-Z0-9\-_]{20,}/
];

serviceFiles.forEach(file => {
  const filePath = path.join(__dirname, '../src/services', file);
  if (fs.existsSync(filePath)) {
    const content = fs.readFileSync(filePath, 'utf8');
    let hasHardcodedKeys = false;
    
    suspiciousPatterns.forEach(pattern => {
      if (pattern.test(content)) {
        hasHardcodedKeys = true;
      }
    });
    
    if (hasHardcodedKeys) {
      console.log(`❌ ${file} may contain hardcoded API keys`);
      issues++;
    } else if (content.includes('APIConfigService')) {
      console.log(`✅ ${file} uses APIConfigService`);
    } else if (content.includes('import.meta.env')) {
      console.log(`✅ ${file} uses environment variables`);
    } else {
      console.log(`⚠️  ${file} - verify it's not using hardcoded keys`);
      warnings++;
    }
  } else {
    console.log(`⚠️  ${file} not found`);
    warnings++;
  }
});

// Check Cursor MCP configuration
console.log('\n🤖 Checking Cursor AI MCP configuration...');
const mcpConfigPath = path.join(__dirname, '../../.cursor/mcp.json');
if (fs.existsSync(mcpConfigPath)) {
  console.log('✅ Cursor MCP configuration exists');
  
  try {
    const mcpConfig = JSON.parse(fs.readFileSync(mcpConfigPath, 'utf8'));
    const expectedServers = ['pulumi', 'sequential_thinking', 'github', 'filesystem', 'puppeteer'];
    const configuredServers = Object.keys(mcpConfig.mcpServers || {});
    
    expectedServers.forEach(server => {
      if (configuredServers.includes(server)) {
        console.log(`  ✅ ${server} MCP server configured`);
      } else {
        console.log(`  ❌ ${server} MCP server missing`);
        issues++;
      }
    });
  } catch (error) {
    console.log('❌ Invalid MCP configuration JSON');
    issues++;
  }
} else {
  console.log('❌ Cursor MCP configuration missing at', mcpConfigPath);
  issues++;
}

// Check for Error Boundary
console.log('\n🛡️  Checking error handling...');
const errorBoundaryPath = path.join(__dirname, '../src/components/ErrorBoundary.tsx');
if (fs.existsSync(errorBoundaryPath)) {
  console.log('✅ ErrorBoundary component exists');
  
  const appPath = path.join(__dirname, '../src/App.tsx');
  if (fs.existsSync(appPath)) {
    const appContent = fs.readFileSync(appPath, 'utf8');
    if (appContent.includes('ErrorBoundary')) {
      console.log('✅ ErrorBoundary is used in App.tsx');
    } else {
      console.log('⚠️  ErrorBoundary should be used in App.tsx');
      warnings++;
    }
  }
} else {
  console.log('❌ ErrorBoundary component missing');
  issues++;
}

// Check Service Manager
console.log('\n🏭 Checking Service Manager...');
const serviceManagerPath = path.join(__dirname, '../src/services/ServiceManager.ts');
if (fs.existsSync(serviceManagerPath)) {
  console.log('✅ ServiceManager exists (singleton pattern)');
} else {
  console.log('❌ ServiceManager missing');
  issues++;
}

// Summary
console.log('\n' + '='.repeat(50));
console.log('📊 VERIFICATION SUMMARY');
console.log('='.repeat(50));

if (issues === 0 && warnings === 0) {
  console.log('✅ All checks passed! Your setup is secure and optimized.');
} else {
  if (issues > 0) {
    console.log(`❌ Found ${issues} critical issue(s) that need to be fixed`);
  }
  if (warnings > 0) {
    console.log(`⚠️  Found ${warnings} warning(s) to review`);
  }
  
  console.log('\n📋 Next steps:');
  if (!fs.existsSync(envLocal)) {
    console.log('1. Create .env.local from .env.example');
  }
  if (issues > 0) {
    console.log('2. Fix all critical issues marked with ❌');
  }
  if (warnings > 0) {
    console.log('3. Review all warnings marked with ⚠️');
  }
}

console.log('\n✨ Run this script again after making changes to verify your setup.');

process.exit(issues > 0 ? 1 : 0); 