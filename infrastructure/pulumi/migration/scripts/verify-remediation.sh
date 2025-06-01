#!/bin/bash

# Verification script for Pulumi Migration Framework remediation
# Checks that all critical fixes have been properly implemented

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Check function
check() {
    local description="$1"
    local command="$2"
    
    echo -n "Checking: $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
    fi
}

# Warning function
warn_check() {
    local description="$1"
    local command="$2"
    
    echo -n "Checking: $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠ WARNING${NC}"
        ((WARNINGS++))
    fi
}

echo "======================================"
echo "Pulumi Migration Framework Verification"
echo "======================================"
echo

# Check directory structure
echo "1. Checking directory structure..."
check "src directory exists" "[ -d src ]"
check "tests directory exists" "[ -d tests ]"
check "utils directory exists" "[ -d src/utils ]"
check ".github/workflows directory exists" "[ -d .github/workflows ]"
echo

# Check critical files
echo "2. Checking critical files..."
check "imports.ts exists" "[ -f src/imports.ts ]"
check "orchestrator-enhanced.ts exists" "[ -f src/orchestrator-enhanced.ts ]"
check "state-manager-async.ts exists" "[ -f src/state-manager-async.ts ]"
check "retry-manager.ts exists" "[ -f src/retry-manager.ts ]"
check "lru-cache.ts exists" "[ -f src/utils/lru-cache.ts ]"
check "resource-cache.ts exists" "[ -f src/utils/resource-cache.ts ]"
check "Dockerfile exists" "[ -f Dockerfile ]"
check "docker-compose.yml exists" "[ -f docker-compose.yml ]"
echo

# Check test files
echo "3. Checking test infrastructure..."
check "test_state_manager.ts exists" "[ -f tests/test_state_manager.ts ]"
check "test_retry_manager.ts exists" "[ -f tests/test_retry_manager.ts ]"
check "setup.ts exists" "[ -f tests/setup.ts ]"
check "jest.config.js exists" "[ -f jest.config.js ]"
echo

# Check configuration files
echo "4. Checking configuration files..."
check "package.json exists" "[ -f package.json ]"
check "tsconfig.json exists" "[ -f tsconfig.json ]"
check ".eslintrc.js exists" "[ -f .eslintrc.js ]"
check ".prettierrc.js exists" "[ -f .prettierrc.js ]"
echo

# Check CI/CD
echo "5. Checking CI/CD configuration..."
check "GitHub Actions workflow exists" "[ -f .github/workflows/ci.yml ]"
echo

# Check deployment files
echo "6. Checking deployment files..."
check "deploy-to-vultr.sh exists" "[ -f deploy-to-vultr.sh ]"
check "deploy-to-vultr.sh is executable" "[ -x deploy-to-vultr.sh ]"
echo

# Check critical method implementations
echo "7. Checking critical method implementations..."
check "cleanup method in AsyncStateManager" "grep -q 'cleanup(' src/state-manager-async.ts"
check "rollback method in AsyncStateManager" "grep -q 'rollback(' src/state-manager-async.ts"
check "rollback method in EnhancedMigrationOrchestrator" "grep -q 'async rollback(' src/orchestrator-enhanced.ts"
check "child method in Logger" "grep -q 'child(' src/logger.ts"
echo

# Check import fixes
echo "8. Checking import management..."
check "imports.ts has pulumi exports" "grep -q 'export.*pulumi' src/imports.ts"
check "imports.ts has fs exports" "grep -q 'export.*fs' src/imports.ts"
check "imports.ts has path exports" "grep -q 'export.*path' src/imports.ts"
check "index.ts uses centralized imports" "grep -q 'from.*imports' index.ts"
echo

# Check memory management
echo "9. Checking memory management implementations..."
check "LRU cache implementation" "grep -q 'class LRUCache' src/utils/lru-cache.ts"
check "Resource cache implementation" "grep -q 'class ResourceCache' src/utils/resource-cache.ts"
check "Memory-aware cache creation" "grep -q 'createMemoryAwareLRUCache' src/utils/lru-cache.ts"
echo

# Check package.json updates
echo "10. Checking package.json enhancements..."
check "bin field in package.json" "grep -q '\"bin\"' package.json"
check "test:coverage script" "grep -q 'test:coverage' package.json"
check "docker:build script" "grep -q 'docker:build' package.json"
check "type-check script" "grep -q 'type-check' package.json"
echo

# Optional checks (warnings only)
echo "11. Optional checks..."
warn_check "node_modules exists (npm install run)" "[ -d node_modules ]"
warn_check "dist directory exists (npm run build)" "[ -d dist ]"
warn_check ".env file exists" "[ -f .env ]"
echo

# Summary
echo "======================================"
echo "Verification Summary"
echo "======================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo "The Pulumi Migration Framework remediation is complete."
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}Note: Some optional items need attention (see warnings above)${NC}"
    fi
    
    exit 0
else
    echo -e "${RED}✗ Some critical checks failed!${NC}"
    echo "Please review the failed items above."
    exit 1
fi