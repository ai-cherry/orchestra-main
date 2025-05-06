import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import WebSocket from 'ws';
import { exec } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { promisify } from 'util';
import { GoogleAuth } from 'google-auth-library';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Promisify exec
const execAsync = promisify(exec);

// Create Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true }));

// Create HTTP server
const server = createServer(app);

// Create WebSocket server
const wss = new WebSocket.Server({ server });

// Authentication middleware
const authenticate = async (req: express.Request, res: express.Response, next: express.NextFunction) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
    
    const token = authHeader.split(' ')[1];
    
    // Verify token with Google Auth
    const auth = new GoogleAuth();
    const client = await auth.getClient();
    const tokenInfo = await client.verifyIdToken({
      idToken: token,
      audience: process.env.GOOGLE_CLIENT_ID
    });
    
    if (!tokenInfo.getPayload()) {
      return res.status(401).json({ error: 'Invalid token' });
    }
    
    // Add user info to request
    req.user = tokenInfo.getPayload();
    next();
  } catch (error) {
    console.error('Authentication error:', error);
    res.status(401).json({ error: 'Authentication failed' });
  }
};

// Define routes
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

// File synchronization endpoint
app.post('/sync', authenticate, async (req, res) => {
  try {
    const { source, destination, operation } = req.body;
    
    if (!source || !destination) {
      return res.status(400).json({ error: 'Source and destination are required' });
    }
    
    // Ensure directories exist
    const destDir = path.dirname(destination);
    await execAsync(`mkdir -p ${destDir}`);
    
    if (operation === 'delete') {
      // Delete file
      await execAsync(`rm -f ${destination}`);
      res.status(200).json({ success: true, message: 'File deleted successfully' });
    } else {
      // Sync file
      if (req.body.content) {
        // Write content to file
        fs.writeFileSync(destination, Buffer.from(req.body.content, 'base64'));
      } else {
        // Use rsync
        await execAsync(`rsync -avz ${source} ${destination}`);
      }
      
      res.status(200).json({ success: true, message: 'File synchronized successfully' });
    }
  } catch (error) {
    console.error('Sync error:', error);
    res.status(500).json({ error: 'Sync failed', details: error.message });
  }
});

// Initial sync endpoint
app.post('/sync/initial', authenticate, async (req, res) => {
  try {
    const { source, destination } = req.body;
    
    if (!source || !destination) {
      return res.status(400).json({ error: 'Source and destination are required' });
    }
    
    // Ensure destination directory exists
    await execAsync(`mkdir -p ${destination}`);
    
    // Sync all files
    await execAsync(`rsync -avz --delete ${source}/ ${destination}/`);
    
    res.status(200).json({ success: true, message: 'Initial sync completed successfully' });
  } catch (error) {
    console.error('Initial sync error:', error);
    res.status(500).json({ error: 'Initial sync failed', details: error.message });
  }
});

// Terminal WebSocket handler
wss.on('connection', (ws) => {
  console.log('WebSocket connection established');
  
  let terminal: any = null;
  
  ws.on('message', async (message: string) => {
    try {
      const data = JSON.parse(message);
      
      if (data.type === 'auth') {
        // Authenticate WebSocket connection
        try {
          const auth = new GoogleAuth();
          const client = await auth.getClient();
          const tokenInfo = await client.verifyIdToken({
            idToken: data.token,
            audience: process.env.GOOGLE_CLIENT_ID
          });
          
          if (!tokenInfo.getPayload()) {
            ws.send(JSON.stringify({ type: 'error', message: 'Authentication failed' }));
            ws.close();
            return;
          }
          
          ws.send(JSON.stringify({ type: 'auth', success: true }));
        } catch (error) {
          ws.send(JSON.stringify({ type: 'error', message: 'Authentication failed' }));
          ws.close();
        }
      } else if (data.type === 'terminal') {
        // Create terminal session
        if (data.action === 'create') {
          terminal = exec('bash');
          
          terminal.stdout.on('data', (data: Buffer) => {
            ws.send(JSON.stringify({ type: 'terminal', data: data.toString('base64') }));
          });
          
          terminal.stderr.on('data', (data: Buffer) => {
            ws.send(JSON.stringify({ type: 'terminal', data: data.toString('base64') }));
          });
          
          terminal.on('close', (code: number) => {
            ws.send(JSON.stringify({ type: 'terminal', action: 'closed', code }));
          });
          
          ws.send(JSON.stringify({ type: 'terminal', action: 'created' }));
        } else if (data.action === 'input' && terminal) {
          // Send input to terminal
          terminal.stdin.write(Buffer.from(data.data, 'base64'));
        } else if (data.action === 'resize' && terminal) {
          // Resize terminal
          // Not implemented in this simplified version
        } else if (data.action === 'close' && terminal) {
          // Close terminal
          terminal.kill();
          terminal = null;
          ws.send(JSON.stringify({ type: 'terminal', action: 'closed', code: 0 }));
        }
      }
    } catch (error) {
      console.error('WebSocket error:', error);
      ws.send(JSON.stringify({ type: 'error', message: 'Invalid message format' }));
    }
  });
  
  ws.on('close', () => {
    console.log('WebSocket connection closed');
    if (terminal) {
      terminal.kill();
      terminal = null;
    }
  });
});

// Start server
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

// Add type definitions for Express request
declare global {
  namespace Express {
    interface Request {
      user?: any;
    }
  }
}
