import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
export let errorRate = new Rate('errors');

// Test configuration
export let options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 20 }, // Ramp up to 20 users
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete below 2s
    http_req_failed: ['rate<0.1'],     // Error rate must be below 10%
    errors: ['rate<0.1'],              // Custom error rate must be below 10%
  },
};

// Base URL - update this to match your deployment
const BASE_URL = 'https://orchestra-ai-admin.vercel.app';
const API_URL = 'http://10.19.86.201:8000'; // Lambda Labs backend

// Test data
const testCredentials = {
  username: 'demo',
  password: 'demo123'
};

// Authentication token (will be set during setup)
let authToken = '';

export function setup() {
  // Login to get authentication token
  let loginResponse = http.post(`${API_URL}/auth/login`, JSON.stringify(testCredentials), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  if (loginResponse.status === 200) {
    let loginData = JSON.parse(loginResponse.body);
    authToken = loginData.access_token;
    console.log('Authentication successful');
    return { authToken: authToken };
  } else {
    console.error('Authentication failed:', loginResponse.status);
    return { authToken: '' };
  }
}

export default function(data) {
  // Use auth token from setup
  const headers = {
    'Authorization': `Bearer ${data.authToken}`,
    'Content-Type': 'application/json',
  };

  // Test 1: Frontend Health Check
  let frontendResponse = http.get(`${BASE_URL}/`);
  check(frontendResponse, {
    'Frontend is accessible': (r) => r.status === 200,
    'Frontend response time < 2s': (r) => r.timings.duration < 2000,
  }) || errorRate.add(1);

  sleep(1);

  // Test 2: API Health Check
  let apiHealthResponse = http.get(`${API_URL}/`);
  check(apiHealthResponse, {
    'API is accessible': (r) => r.status === 200,
    'API response time < 1s': (r) => r.timings.duration < 1000,
    'API returns correct status': (r) => {
      try {
        let body = JSON.parse(r.body);
        return body.status === 'operational';
      } catch (e) {
        return false;
      }
    },
  }) || errorRate.add(1);

  sleep(1);

  // Test 3: System Status (Authenticated)
  if (data.authToken) {
    let statusResponse = http.get(`${API_URL}/api/system/status`, { headers });
    check(statusResponse, {
      'System status accessible': (r) => r.status === 200,
      'System status response time < 3s': (r) => r.timings.duration < 3000,
      'System status has required fields': (r) => {
        try {
          let body = JSON.parse(r.body);
          return body.active_agents !== undefined && 
                 body.memory_usage_percent !== undefined &&
                 body.database_status !== undefined;
        } catch (e) {
          return false;
        }
      },
    }) || errorRate.add(1);
  }

  sleep(1);

  // Test 4: Agent Management
  if (data.authToken) {
    let agentsResponse = http.get(`${API_URL}/api/agents`, { headers });
    check(agentsResponse, {
      'Agents endpoint accessible': (r) => r.status === 200,
      'Agents response time < 2s': (r) => r.timings.duration < 2000,
      'Agents returns array': (r) => {
        try {
          let body = JSON.parse(r.body);
          return Array.isArray(body);
        } catch (e) {
          return false;
        }
      },
    }) || errorRate.add(1);
  }

  sleep(1);

  // Test 5: File Upload Initiation
  if (data.authToken) {
    let uploadRequest = {
      filename: `test_file_${__VU}_${__ITER}.txt`,
      file_size: 1024,
      content_type: 'text/plain',
      metadata: { description: 'Performance test file' }
    };

    let uploadResponse = http.post(`${API_URL}/api/files/upload/initiate`, 
      JSON.stringify(uploadRequest), { headers });
    
    check(uploadResponse, {
      'File upload initiation works': (r) => r.status === 200,
      'Upload response time < 3s': (r) => r.timings.duration < 3000,
      'Upload returns file_id': (r) => {
        try {
          let body = JSON.parse(r.body);
          return body.file_id !== undefined;
        } catch (e) {
          return false;
        }
      },
    }) || errorRate.add(1);
  }

  sleep(1);

  // Test 6: Search Functionality
  if (data.authToken) {
    let searchRequest = {
      query: 'test search query',
      search_mode: 'semantic',
      limit: 10
    };

    let searchResponse = http.post(`${API_URL}/api/search`, 
      JSON.stringify(searchRequest), { headers });
    
    check(searchResponse, {
      'Search endpoint responds': (r) => r.status === 200 || r.status === 404 || r.status === 501,
      'Search response time < 5s': (r) => r.timings.duration < 5000,
    }) || errorRate.add(1);
  }

  sleep(2);
}

export function teardown(data) {
  // Cleanup if needed
  console.log('Performance test completed');
}

// Additional test scenarios for stress testing
export function stressTest() {
  return {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '1m', target: 50 },  // Ramp up to 50 users
      { duration: '3m', target: 50 },  // Stay at 50 users
      { duration: '1m', target: 100 }, // Ramp up to 100 users
      { duration: '3m', target: 100 }, // Stay at 100 users
      { duration: '2m', target: 0 },   // Ramp down
    ],
  };
}

// Spike test scenario
export function spikeTest() {
  return {
    executor: 'ramping-vus',
    startVUs: 0,
    stages: [
      { duration: '30s', target: 10 },  // Normal load
      { duration: '30s', target: 200 }, // Spike to 200 users
      { duration: '30s', target: 10 },  // Back to normal
    ],
  };
}

