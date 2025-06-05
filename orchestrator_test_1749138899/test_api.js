// Mock API responses for testing
window.mockAPI = true;

// Override fetch for testing
const originalFetch = window.fetch;
window.fetch = function(url, options) {
    console.log('Mock API call:', url);
    
    if (url.includes('/api/health')) {
        return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                status: 'healthy',
                version: '1.0.0',
                timestamp: new Date().toISOString()
            })
        });
    }
    
    if (url.includes('/api/search')) {
        return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
                query: 'test query',
                mode: 'normal',
                results: [
                    {
                        title: 'Test Result 1',
                        snippet: 'This is a test search result demonstrating the search functionality.',
                        source: 'Test Database',
                        relevance: 0.95
                    },
                    {
                        title: 'Test Result 2',
                        snippet: 'Another test result showing how results are displayed.',
                        source: 'Test Index',
                        relevance: 0.87
                    }
                ],
                responseTime: 124
            })
        });
    }
    
    // Fallback to original fetch
    return originalFetch(url, options);
};

console.log('Mock API enabled for testing');
