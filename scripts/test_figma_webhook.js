#!/usr/bin/env node
/**
 * Figma Webhook Test Tool
 * 
 * This script sends a test webhook payload to the local webhook handler
 * to verify that the handler is functioning correctly. It signs the request
 * with the webhook secret to simulate a real Figma webhook call.
 * 
 * Usage:
 *   node test_figma_webhook.js [--url=<webhook_url>] [--secret=<webhook_secret>]
 */

const crypto = require('crypto');
const axios = require('axios');
const { program } = require('commander');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../.env') });

// Parse command line arguments
program
  .option('--url <url>', 'URL of the webhook handler', 'http://localhost:3000/figma-webhook')
  .option('--secret <secret>', 'Webhook secret for signing the request', process.env.FIGMA_WEBHOOK_SECRET)
  .option('--event <event>', 'Event type to simulate', 'FILE_UPDATE')
  .option('--file-key <fileKey>', 'Figma file key', 'ABC123XYZ')
  .option('--file-name <fileName>', 'Figma file name', 'Design System Components')
  .option('--verbose', 'Enable verbose output')
  .parse(process.argv);

const options = program.opts();

// Validate options
if (!options.secret) {
  console.error('Error: A webhook secret is required. Provide it with --secret or set FIGMA_WEBHOOK_SECRET in your .env file.');
  process.exit(1);
}

if (options.verbose) {
  console.log('Options:', {
    url: options.url,
    event: options.event,
    fileKey: options.fileKey,
    fileName: options.fileName,
    secret: options.secret ? '***redacted***' : undefined
  });
}

/**
 * Create a mock Figma webhook payload
 */
function createMockPayload() {
  const timestamp = new Date().toISOString();
  
  return {
    event_type: options.event,
    webhook_id: 'webhook_test_' + Math.random().toString(36).substring(2, 15),
    passcode: 'test_passcode', // This would be the webhook secret in a real Figma payload
    file_key: options.fileKey,
    file_name: options.fileName,
    description: 'This is a test webhook event',
    timestamp: timestamp,
    team_id: 'test_team_id',
    triggered_by: {
      id: 'user_test',
      handle: 'test.user',
      email: 'test@example.com',
      img_url: 'https://example.com/avatar.png'
    },
    test_event: true
  };
}

/**
 * Sign the payload with the webhook secret
 */
function signPayload(payload, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  const signature = hmac.update(JSON.stringify(payload)).digest('hex');
  return signature;
}

/**
 * Send a test webhook request
 */
async function sendTestWebhook() {
  console.log(`Sending test ${options.event} webhook to ${options.url}...`);
  
  // Create mock payload
  const payload = createMockPayload();
  
  // Sign the payload
  const signature = signPayload(payload, options.secret);
  
  if (options.verbose) {
    console.log('Test payload:', JSON.stringify(payload, null, 2));
    console.log('Generated signature:', signature);
  }
  
  try {
    // Send the webhook request
    const response = await axios.post(options.url, payload, {
      headers: {
        'Content-Type': 'application/json',
        'X-Figma-Signature': signature
      }
    });
    
    console.log('Webhook test successful!');
    console.log('Status:', response.status);
    console.log('Response:', response.data);
  } catch (error) {
    console.error('Error sending webhook test:');
    
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('No response received. Is the webhook server running?');
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('Error:', error.message);
    }
    
    process.exit(1);
  }
}

// Execute the test
sendTestWebhook();
