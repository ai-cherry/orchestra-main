/**
 * Vercel Serverless Function - API Proxy to Lambda Labs Backend
 * Routes all /api/* requests to the production backend
 */

export default async function handler(req, res) {
  // Get the Lambda Labs backend URL from environment variable
  const BACKEND_URL = process.env.LAMBDA_BACKEND_URL || 'http://150.136.94.139:8000';
  
  // Extract the API path
  const { path } = req.query;
  const apiPath = Array.isArray(path) ? path.join('/') : path;
  
  // Build the target URL
  const targetUrl = `${BACKEND_URL}/api/${apiPath || ''}`;
  
  // Forward the request
  try {
    const response = await fetch(targetUrl, {
      method: req.method,
      headers: {
        ...req.headers,
        'host': new URL(BACKEND_URL).host,
        'x-forwarded-for': req.headers['x-forwarded-for'] || req.connection.remoteAddress,
        'x-forwarded-proto': 'https',
        'x-forwarded-host': req.headers.host
      },
      body: req.method !== 'GET' && req.method !== 'HEAD' ? JSON.stringify(req.body) : undefined
    });

    // Forward the response headers
    const responseHeaders = {};
    response.headers.forEach((value, key) => {
      // Skip some headers that shouldn't be forwarded
      if (!['content-encoding', 'content-length', 'transfer-encoding'].includes(key.toLowerCase())) {
        responseHeaders[key] = value;
      }
    });

    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    // Handle OPTIONS request for CORS
    if (req.method === 'OPTIONS') {
      return res.status(200).end();
    }

    // Forward other headers
    Object.entries(responseHeaders).forEach(([key, value]) => {
      res.setHeader(key, value);
    });

    // Get the response body
    const data = await response.text();
    
    // Send the response
    res.status(response.status);
    
    // Try to parse as JSON, otherwise send as text
    try {
      res.json(JSON.parse(data));
    } catch {
      res.send(data);
    }
  } catch (error) {
    console.error('Proxy error:', error);
    res.status(502).json({ 
      error: 'Bad Gateway', 
      message: 'Failed to connect to backend service',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
} 