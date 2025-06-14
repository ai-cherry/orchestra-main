/**
 * Simplified Vercel Proxy for Orchestra AI
 * Minimal, reliable proxy to Lambda Labs backend
 */

export default async function handler(req, res) {
  // CORS headers first
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    // Get backend URL
    const BACKEND_URL = process.env.LAMBDA_BACKEND_URL || 'http://150.136.94.139:8000';
    
    // Extract path
    const { path } = req.query;
    const apiPath = Array.isArray(path) ? path.join('/') : path || '';
    
    // Build target URL
    let targetUrl;
    if (apiPath === 'health' || apiPath.startsWith('health')) {
      targetUrl = `${BACKEND_URL}/health`;
    } else if (apiPath) {
      targetUrl = `${BACKEND_URL}/api/${apiPath}`;
    } else {
      targetUrl = `${BACKEND_URL}/health`;
    }

    console.log(`Proxying to: ${targetUrl}`);

    // Make request
    const response = await fetch(targetUrl, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Vercel-Proxy'
      },
      body: req.method !== 'GET' && req.body ? JSON.stringify(req.body) : undefined
    });

    const data = await response.text();
    
    // Set response headers
    res.setHeader('Content-Type', response.headers.get('content-type') || 'application/json');
    res.status(response.status);
    
    // Send response
    try {
      const jsonData = JSON.parse(data);
      res.json(jsonData);
    } catch {
      res.send(data);
    }
    
  } catch (error) {
    console.error('Proxy error:', error);
    res.status(503).json({ 
      error: 'Service Unavailable',
      message: 'Cannot connect to backend',
      details: error.message
    });
  }
}

