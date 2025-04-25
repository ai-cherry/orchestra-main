#!/usr/bin/env node
/**
 * Figma Webhook Handler
 * 
 * This script creates a simple server that receives Figma webhook events
 * and triggers GitHub repository_dispatch events to initiate deployments.
 * 
 * It follows security best practices:
 * - Validates Figma webhook signatures
 * - Uses environment variables for sensitive values
 * - Requires HTTPS for production
 * - Logs request information for monitoring
 * 
 * Usage:
 *   node figma_webhook_handler.js
 * 
 * Required environment variables:
 *   FIGMA_WEBHOOK_SECRET - Secret used to validate Figma webhook signatures
 *   GITHUB_PAT - Personal Access Token with repo scope
 *   GITHUB_OWNER - The owner of the repository (user or organization)
 *   GITHUB_REPO - The name of the repository
 *   PORT - Port to run the server on (default: 3000)
 */

const express = require('express');
const crypto = require('crypto');
const axios = require('axios');
const morgan = require('morgan');
const dotenv = require('dotenv');
const { promises: fs } = require('fs');
const path = require('path');

// Load environment variables
dotenv.config();

// Environment variables
const FIGMA_WEBHOOK_SECRET = process.env.FIGMA_WEBHOOK_SECRET;
const GITHUB_PAT = process.env.GITHUB_PAT;
const GITHUB_OWNER = process.env.GITHUB_OWNER;
const GITHUB_REPO = process.env.GITHUB_REPO;
const PORT = process.env.PORT || 3000;

// Validation
if (!FIGMA_WEBHOOK_SECRET) {
  console.error('Error: FIGMA_WEBHOOK_SECRET is required');
  process.exit(1);
}

if (!GITHUB_PAT) {
  console.error('Error: GITHUB_PAT is required');
  process.exit(1);
}

if (!GITHUB_OWNER || !GITHUB_REPO) {
  console.error('Error: GITHUB_OWNER and GITHUB_REPO are required');
  process.exit(1);
}

// Create Express app
const app = express();

// Middleware for JSON body parsing
app.use(express.json({
  verify: (req, res, buf, encoding) => {
    // Store the raw body for signature verification
    req.rawBody = buf.toString(encoding || 'utf8');
  }
}));

// Request logging
app.use(morgan('[:date[iso]] :method :url :status :response-time ms - :res[content-length]'));

/**
 * Verify the Figma webhook signature
 */
function verifyFigmaSignature(req, res, next) {
  const signature = req.headers['x-figma-signature'];
  
  if (!signature) {
    console.error('Missing X-Figma-Signature header');
    return res.status(401).json({ error: 'Missing webhook signature' });
  }
  
  // Create HMAC using the secret
  const hmac = crypto.createHmac('sha256', FIGMA_WEBHOOK_SECRET);
  const digest = hmac.update(req.rawBody).digest('hex');
  
  // Compare digest with signature using a timing-safe comparison
  if (!crypto.timingSafeEqual(Buffer.from(digest), Buffer.from(signature))) {
    console.error('Invalid webhook signature');
    return res.status(401).json({ error: 'Invalid webhook signature' });
  }
  
  next();
}

/**
 * Trigger a GitHub repository_dispatch event
 */
async function triggerGitHubAction(eventType, payload) {
  try {
    const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/dispatches`;
    
    const response = await axios.post(url, {
      event_type: eventType,
      client_payload: payload
    }, {
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': `token ${GITHUB_PAT}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log(`GitHub Action triggered successfully: ${eventType}`);
    return true;
  } catch (error) {
    console.error('Error triggering GitHub Action:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    return false;
  }
}

/**
 * Log webhook events to file for monitoring
 */
async function logWebhookEvent(event) {
  try {
    const logsDir = path.join(__dirname, '../logs');
    
    // Create logs directory if it doesn't exist
    try {
      await fs.mkdir(logsDir, { recursive: true });
    } catch (err) {
      // Ignore directory exists error
    }
    
    const timestamp = new Date().toISOString();
    const logFile = path.join(logsDir, 'figma-webhooks.log');
    
    // Format log entry
    const logEntry = `[${timestamp}] ${JSON.stringify(event)}\n`;
    
    // Append to log file
    await fs.appendFile(logFile, logEntry);
  } catch (error) {
    console.error('Error logging webhook event:', error);
  }
}

// Webhook endpoint with signature verification
app.post('/figma-webhook', verifyFigmaSignature, async (req, res) => {
  const webhookEvent = req.body;
  
  console.log('Received Figma webhook event:', webhookEvent.event_type);
  
  // Log the webhook event
  await logWebhookEvent(webhookEvent);
  
  // Map Figma event types to GitHub event types
  let githubEventType;
  
  switch (webhookEvent.event_type) {
    case 'FILE_UPDATE':
      githubEventType = 'figma_file_update';
      break;
    case 'FILE_VERSION_UPDATE':
      githubEventType = 'figma_version_update';
      break;
    case 'LIBRARY_PUBLISH':
      githubEventType = 'figma_library_publish';
      break;
    default:
      githubEventType = `figma_${webhookEvent.event_type.toLowerCase()}`;
  }
  
  // Prepare GitHub payload with useful Figma context
  const githubPayload = {
    figma_event_type: webhookEvent.event_type,
    figma_webhook_id: webhookEvent.webhook_id,
    file_name: webhookEvent.file_name,
    file_key: webhookEvent.file_key,
    timestamp: new Date().toISOString(),
    passcode: null, // Never pass the passcode to GitHub
    // Include other non-sensitive data
    ...webhookEvent
  };
  
  // Delete sensitive fields
  delete githubPayload.passcode;
  
  // Trigger GitHub Action
  const success = await triggerGitHubAction(githubEventType, githubPayload);
  
  if (success) {
    res.status(200).json({ 
      success: true, 
      message: `Triggered GitHub Action: ${githubEventType}`
    });
  } else {
    res.status(500).json({ 
      success: false, 
      message: 'Failed to trigger GitHub Action'
    });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

// Start server
app.listen(PORT, () => {
  console.log(`Figma webhook handler listening on port ${PORT}`);
  console.log(`Webhook URL: http://localhost:${PORT}/figma-webhook`);
  console.log(`Health check URL: http://localhost:${PORT}/health`);
  console.log('Ready to receive Figma webhook events');
  
  if (process.env.NODE_ENV === 'production') {
    console.warn('WARNING: In production, you should use HTTPS for security');
  }
});
