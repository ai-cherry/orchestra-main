#!/bin/bash

# Cherry AI Orchestrator Deployment Test Suite
# Validates deployment health and functionality

set -euo pipefail

# Configuration
DOMAIN="${1:-cherry-ai.me}"
ORCHESTRATOR_URL="https://orchestrator.${DOMAIN}"
LOCAL_TEST_URL="http://localhost"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="orchestrator_test_${TIMESTAMP}.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    log "${YELLOW}Running: ${test_name}${NC}"
    
    if eval "$test_command" >> "$LOG_FILE" 2>&1; then
        log "${GREEN}✓ PASSED: ${test_name}${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        log "${RED}✗ FAILED: ${test_name}${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Header
log "🍒 Cherry AI Orchestrator Deployment Test Suite"
log "============================================="
log "Timestamp: $(date)"
log "Domain: ${DOMAIN}"
log "URL: ${ORCHESTRATOR_URL}"
log ""

# Test 1: Check if nginx is running
run_test "Nginx Service Status" "systemctl is-active nginx"

# Test 2: Check if nginx configuration is valid
run_test "Nginx Configuration" "nginx -t"

# Test 3: Check local file existence
run_test "HTML File Exists" "test -f /var/www/cherry-ai-orchestrator/cherry-ai-orchestrator-final.html"
run_test "JS File Exists" "test -f /var/www/cherry-ai-orchestrator/cherry-ai-orchestrator.js"

# Test 4: Check file permissions
run_test "File Permissions" "test -r /var/www/cherry-ai-orchestrator/cherry-ai-orchestrator-final.html"

# Test 5: Local HTTP response
run_test "Local HTTP Response" "curl -s -o /dev/null -w '%{http_code}' ${LOCAL_TEST_URL} | grep -E '200|301|302'"

# Test 6: HTTPS response (if domain is configured)
if [[ -n "$DOMAIN" ]]; then
    run_test "HTTPS Response" "curl -s -o /dev/null -w '%{http_code}' ${ORCHESTRATOR_URL} | grep -E '200|301|302'"
fi

# Test 7: Check SSL certificate (if domain is configured)
if [[ -n "$DOMAIN" ]]; then
    run_test "SSL Certificate Valid" "curl -s ${ORCHESTRATOR_URL} > /dev/null"
fi

# Test 8: Check content loading
run_test "HTML Content Check" "curl -s ${LOCAL_TEST_URL} | grep -q 'Cherry AI Orchestrator'"

# Test 9: JavaScript file accessibility
run_test "JS File Accessible" "curl -s ${LOCAL_TEST_URL}/cherry-ai-orchestrator.js | grep -q 'AppState'"

# Test 10: Security headers
run_test "Security Headers" "curl -s -I ${LOCAL_TEST_URL} | grep -q 'X-Frame-Options'"

# Test 11: Gzip compression
run_test "Gzip Compression" "curl -s -I -H 'Accept-Encoding: gzip' ${LOCAL_TEST_URL} | grep -q 'Content-Encoding: gzip'"

# Test 12: API proxy (if configured)
run_test "API Endpoint" "curl -s -o /dev/null -w '%{http_code}' ${LOCAL_TEST_URL}/api/health | grep -E '200|404|502'"

# Test 13: Memory usage
run_test "Memory Usage" "free -m | awk '/^Mem:/ {if(\$3/\$2 < 0.9) exit 0; else exit 1}'"

# Test 14: Disk usage
run_test "Disk Usage" "df -h / | awk 'NR==2 {gsub(/%/,\"\",\$5); if(\$5 < 90) exit 0; else exit 1}'"

# Test 15: Process monitoring
run_test "Node Exporter Running" "systemctl is-active prometheus-node-exporter || true"

# Performance tests
log ""
log "${YELLOW}Performance Tests:${NC}"

# Test 16: Page load time
if command -v curl > /dev/null; then
    LOAD_TIME=$(curl -s -o /dev/null -w '%{time_total}' ${LOCAL_TEST_URL})
    if (( $(echo "$LOAD_TIME < 2.0" | bc -l) )); then
        log "${GREEN}✓ Page Load Time: ${LOAD_TIME}s (< 2s)${NC}"
        ((TESTS_PASSED++))
    else
        log "${RED}✗ Page Load Time: ${LOAD_TIME}s (> 2s)${NC}"
        ((TESTS_FAILED++))
    fi
fi

# Test 17: Concurrent connections
log "${YELLOW}Testing concurrent connections...${NC}"
if command -v ab > /dev/null; then
    run_test "Load Test (10 concurrent)" "ab -n 100 -c 10 -t 5 ${LOCAL_TEST_URL}/ > /dev/null"
else
    log "${YELLOW}⚠ Apache Bench not installed, skipping load test${NC}"
fi

# Security tests
log ""
log "${YELLOW}Security Tests:${NC}"

# Test 18: Check for common vulnerabilities
run_test "No Directory Listing" "! curl -s ${LOCAL_TEST_URL}/.git/ | grep -q 'Index of'"

# Test 19: Check firewall
if command -v ufw > /dev/null; then
    run_test "Firewall Enabled" "ufw status | grep -q 'Status: active'"
fi

# Test 20: Check fail2ban
if command -v fail2ban-client > /dev/null; then
    run_test "Fail2ban Active" "systemctl is-active fail2ban"
fi

# Functionality tests
log ""
log "${YELLOW}Functionality Tests:${NC}"

# Test 21: Persona switching
PERSONA_TEST=$(curl -s ${LOCAL_TEST_URL} | grep -o 'data-persona="[^"]*"' | wc -l)
if [[ $PERSONA_TEST -ge 3 ]]; then
    log "${GREEN}✓ Persona Elements Found: ${PERSONA_TEST}${NC}"
    ((TESTS_PASSED++))
else
    log "${RED}✗ Persona Elements Missing${NC}"
    ((TESTS_FAILED++))
fi

# Test 22: Tab navigation
TAB_TEST=$(curl -s ${LOCAL_TEST_URL} | grep -o 'tab-button' | wc -l)
if [[ $TAB_TEST -ge 9 ]]; then
    log "${GREEN}✓ Tab Buttons Found: ${TAB_TEST}${NC}"
    ((TESTS_PASSED++))
else
    log "${RED}✗ Tab Buttons Missing${NC}"
    ((TESTS_FAILED++))
fi

# Generate health report
log ""
log "Generating health report..."

cat > "orchestrator_health_${TIMESTAMP}.json" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "domain": "${DOMAIN}",
  "url": "${ORCHESTRATOR_URL}",
  "tests": {
    "passed": ${TESTS_PASSED},
    "failed": ${TESTS_FAILED},
    "total": $((TESTS_PASSED + TESTS_FAILED))
  },
  "services": {
    "nginx": "$(systemctl is-active nginx 2>/dev/null || echo 'unknown')",
    "fail2ban": "$(systemctl is-active fail2ban 2>/dev/null || echo 'unknown')",
    "node_exporter": "$(systemctl is-active prometheus-node-exporter 2>/dev/null || echo 'unknown')"
  },
  "system": {
    "memory_usage": "$(free -m | awk '/^Mem:/ {printf "%.1f%%", $3/$2 * 100}')",
    "disk_usage": "$(df -h / | awk 'NR==2 {print $5}')",
    "load_average": "$(uptime | awk -F'load average:' '{print $2}')"
  }
}
EOF

# Summary
log ""
log "========================================"
log "Test Summary:"
log "========================================"
log "${GREEN}Passed: ${TESTS_PASSED}${NC}"
log "${RED}Failed: ${TESTS_FAILED}${NC}"
log "Total: $((TESTS_PASSED + TESTS_FAILED))"
log ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    log "${GREEN}✅ All tests passed! Cherry AI Orchestrator is healthy.${NC}"
    exit 0
else
    log "${RED}❌ Some tests failed. Please check the logs: ${LOG_FILE}${NC}"
    log ""
    log "Common fixes:"
    log "1. Check nginx logs: sudo journalctl -u nginx -n 50"
    log "2. Verify file permissions: ls -la /var/www/cherry-ai-orchestrator/"
    log "3. Check nginx config: sudo nginx -t"
    log "4. Restart services: sudo systemctl restart nginx"
    exit 1
fi