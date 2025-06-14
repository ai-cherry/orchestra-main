/**
 * Vercel Serverless Function - Enhanced API Proxy to Lambda Labs Backend
 * Routes all /api/* requests to the production backend with caching and failover
 */

// Allowed origins for CORS
const ALLOWED_ORIGINS = [
  'https://orchestra-ai-admin.vercel.app',
  'https://orchestra-ai-admin-lynn-musils-projects.vercel.app',
  'http://localhost:3000',
  'http://localhost:5173'
];

// Cache configuration
const CACHE_CONFIG = {
  '/api/health/': 10, // 10 seconds
  '/api/system/status': 5, // 5 seconds
  '/api/personas': 60, // 1 minute
};

export default async function handler(req, res) {
  // Get the Lambda Labs backend URL from environment variable
  const BACKEND_URL = process.env.LAMBDA_BACKEND_URL || 'http://150.136.94.139:8000';
  
  // CORS check
  const origin = req.headers.origin;
  if (origin && !ALLOWED_ORIGINS.includes(origin)) {
    return res.status(403).json({ error: 'Forbidden - Invalid origin' });
  }
  
  // Extract the API path
  const { path } = req.query;
  const apiPath = Array.isArray(path) ? path.join('/') : path;
  
  // Build the target URL
  const targetUrl = `${BACKEND_URL}/api/${apiPath || ''}`;
  
  // Check if this endpoint should be cached
  const cacheKey = `/api/${apiPath || ''}`;
  const cacheDuration = CACHE_CONFIG[cacheKey];
  
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', origin || '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Credentials', 'true');

  // Handle OPTIONS request for CORS
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Add request ID for tracking
  const requestId = req.headers['x-request-id'] || generateRequestId();
  
  // Forward the request
  try {
    const startTime = Date.now();
    
    const response = await fetch(targetUrl, {
      method: req.method,
      headers: {
        ...req.headers,
        'host': new URL(BACKEND_URL).host,
        'x-forwarded-for': req.headers['x-forwarded-for'] || req.connection?.remoteAddress,
        'x-forwarded-proto': 'https',
        'x-forwarded-host': req.headers.host,
        'x-request-id': requestId,
        'x-vercel-deployment-url': process.env.VERCEL_URL
      },
      body: req.method !== 'GET' && req.method !== 'HEAD' ? JSON.stringify(req.body) : undefined
    });

    const duration = Date.now() - startTime;

    // Forward the response headers
    const responseHeaders = {};
    response.headers.forEach((value, key) => {
      // Skip some headers that shouldn't be forwarded
      if (!['content-encoding', 'content-length', 'transfer-encoding'].includes(key.toLowerCase())) {
        responseHeaders[key] = value;
      }
    });

    // Add performance headers
    res.setHeader('X-Response-Time', `${duration}ms`);
    res.setHeader('X-Request-ID', requestId);
    
    // Add cache headers if applicable
    if (cacheDuration && req.method === 'GET') {
      res.setHeader('Cache-Control', `s-maxage=${cacheDuration}, stale-while-revalidate`);
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
      const jsonData = JSON.parse(data);
      
      // Add metadata for debugging
      if (process.env.NODE_ENV === 'development') {
        jsonData._proxy = {
          backend: BACKEND_URL,
          duration: `${duration}ms`,
          requestId
        };
      }
      
      res.json(jsonData);
    } catch {
      res.send(data);
    }
  } catch (error) {
    console.error('Proxy error:', {
      error: error.message,
      targetUrl,
      requestId,
      method: req.method
    });
    
    // Check if it's a connection error
    if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
      res.status(503).json({ 
        error: 'Service Unavailable', 
        message: 'Backend service is temporarily unavailable',
        requestId,
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    } else {
      res.status(502).json({ 
        error: 'Bad Gateway', 
        message: 'Failed to connect to backend service',
        requestId,
        details: process.env.NODE_ENV === 'development' ? error.message : undefined
      });
    }
  }
}

function generateRequestId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
} 