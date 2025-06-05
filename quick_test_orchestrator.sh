#!/bin/bash

# Quick local test for Cherry AI Orchestrator
# Run this to test the interface locally before deployment

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🍒 Cherry AI Orchestrator - Local Test${NC}"
echo "======================================"

# Check if files exist
if [ ! -f "cherry-ai-orchestrator-final.html" ]; then
    echo -e "${RED}Error: cherry-ai-orchestrator-final.html not found${NC}"
    exit 1
fi

if [ ! -f "cherry-ai-orchestrator.js" ]; then
    echo -e "${RED}Error: cherry-ai-orchestrator.js not found${NC}"
    exit 1
fi

# Check if Python is available for simple HTTP server
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python3 found${NC}"
    SERVER_CMD="python3 -m http.server 8080"
elif command -v python &> /dev/null; then
    echo -e "${GREEN}✓ Python found${NC}"
    SERVER_CMD="python -m SimpleHTTPServer 8080"
else
    echo -e "${RED}Error: Python not found. Please install Python to run the test server.${NC}"
    exit 1
fi

# Create a temporary test directory
TEST_DIR="orchestrator_test_$(date +%s)"
mkdir -p "$TEST_DIR"

# Copy files to test directory
echo -e "${BLUE}Setting up test environment...${NC}"
cp cherry-ai-orchestrator-final.html "$TEST_DIR/index.html"
cp cherry-ai-orchestrator.js "$TEST_DIR/"

# Create a simple test API mock
cat > "$TEST_DIR/test_api.js" << 'EOF'
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
EOF

# Inject test API into HTML
sed -i.bak '/<script src="cherry-ai-orchestrator.js"><\/script>/a\
    <script src="test_api.js"></script>' "$TEST_DIR/index.html"

# Start the server
echo -e "${GREEN}Starting test server...${NC}"
echo -e "${YELLOW}Server will run at: http://localhost:8080${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

cd "$TEST_DIR"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Cleaning up...${NC}"
    cd ..
    rm -rf "$TEST_DIR"
    echo -e "${GREEN}Test environment cleaned up${NC}"
}

trap cleanup EXIT

# Open browser if possible
if command -v open &> /dev/null; then
    # macOS
    sleep 1 && open "http://localhost:8080" &
elif command -v xdg-open &> /dev/null; then
    # Linux
    sleep 1 && xdg-open "http://localhost:8080" &
elif command -v start &> /dev/null; then
    # Windows
    sleep 1 && start "http://localhost:8080" &
fi

# Start server
$SERVER_CMD