#!/bin/bash

# Orchestra AI - Secure Infrastructure Validation Script
# Validates SSH security and infrastructure configuration

set -e

echo "🔒 Orchestra AI Security Validation"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation results
PASSED=0
FAILED=0
WARNINGS=0

validate_check() {
    local check_name="$1"
    local result="$2"
    local message="$3"
    
    if [ "$result" = "pass" ]; then
        echo -e "${GREEN}✅ $check_name${NC}: $message"
        ((PASSED++))
    elif [ "$result" = "fail" ]; then
        echo -e "${RED}❌ $check_name${NC}: $message"
        ((FAILED++))
    else
        echo -e "${YELLOW}⚠️  $check_name${NC}: $message"
        ((WARNINGS++))
    fi
}

run_validation() {
    echo ""
    echo "🔍 Checking SSH Security Configuration..."

    # Check 1: No StrictHostKeyChecking=no in scripts
    if grep -r "StrictHostKeyChecking=no" . --include="*.sh" --include="*.py" --exclude="validate_security.sh" >/dev/null 2>&1; then
        validate_check "SSH Host Key Checking" "fail" "Found insecure StrictHostKeyChecking=no configurations"
    else
        validate_check "SSH Host Key Checking" "pass" "No insecure SSH configurations found"
    fi

    # Check 2: SSH key file permissions
    echo ""
    echo "🔑 Checking SSH Key Security..."

    if [ -f ~/.ssh/id_rsa ]; then
        PERMS=$(stat -c "%a" ~/.ssh/id_rsa)
        if [ "$PERMS" = "600" ]; then
            validate_check "SSH Key Permissions" "pass" "Private key has secure permissions (600)"
        else
            validate_check "SSH Key Permissions" "fail" "Private key has insecure permissions ($PERMS)"
        fi
    else
        validate_check "SSH Key Permissions" "warn" "No default SSH key found"
    fi

    # Check 3: Known hosts file exists
    if [ -f ~/.ssh/known_hosts ]; then
        validate_check "Known Hosts File" "pass" "Known hosts file exists"
    else
        validate_check "Known Hosts File" "warn" "No known_hosts file found"
    fi

    # Check 4: Secure SSH manager implementation
    echo ""
    echo "🛡️  Checking Security Implementation..."

    if [ -f "security/ssh_manager.py" ]; then
        if grep -q "StrictHostKeyChecking=yes" security/ssh_manager.py; then
            validate_check "Secure SSH Manager" "pass" "Secure SSH manager enforces host key checking"
        else
            validate_check "Secure SSH Manager" "fail" "SSH manager does not enforce host key checking"
        fi
    else
        validate_check "Secure SSH Manager" "fail" "Secure SSH manager not found"
    fi

    # Check 5: Secret management
    if [ -f "security/secret_manager.py" ]; then
        validate_check "Secret Management" "pass" "Secret manager implementation found"
    else
        validate_check "Secret Management" "fail" "Secret manager not found"
    fi

    # Check 6: Authentication system
    if [ -f "auth/authentication.py" ]; then
        if grep -q "JWT" auth/authentication.py; then
            validate_check "Authentication System" "pass" "JWT-based authentication implemented"
        else
            validate_check "Authentication System" "warn" "Authentication system found but may not use JWT"
        fi
    else
        validate_check "Authentication System" "fail" "Authentication system not found"
    fi

    # Check 7: CI/CD pipeline
    echo ""
    echo "🚀 Checking CI/CD Configuration..."

    if [ -f ".github/workflows/deploy.yml" ]; then
        if grep -q "security-scan" .github/workflows/deploy.yml; then
            validate_check "CI/CD Security" "pass" "Security scanning enabled in CI/CD"
        else
            validate_check "CI/CD Security" "warn" "CI/CD found but security scanning not configured"
        fi
    else
        validate_check "CI/CD Pipeline" "fail" "No GitHub Actions workflow found"
    fi

    # Check 8: Testing infrastructure
    if [ -d "tests" ]; then
        if [ -f "tests/unit/test_authentication.py" ]; then
            validate_check "Security Testing" "pass" "Authentication tests found"
        else
            validate_check "Security Testing" "warn" "Test directory found but no authentication tests"
        fi
    else
        validate_check "Testing Infrastructure" "fail" "No test directory found"
    fi

    # Check 9: Infrastructure as Code security
    echo ""
    echo "🏗️  Checking Infrastructure Security..."

    if [ -f "pulumi/__main__.py" ]; then
        if grep -q "secret=True" pulumi/__main__.py; then
            validate_check "IaC Secrets" "pass" "Pulumi secrets properly marked"
        else
            validate_check "IaC Secrets" "warn" "Pulumi found but secrets may not be properly protected"
        fi
    else
        validate_check "Infrastructure as Code" "warn" "No Pulumi infrastructure found"
    fi

    # Check 10: Docker security
    if [ -f "Dockerfile" ] || [ -f "Dockerfile.api-optimized" ]; then
        validate_check "Container Security" "pass" "Docker configuration found"
    else
        validate_check "Container Security" "warn" "No Docker configuration found"
    fi

    # Summary
    echo ""
    echo "📊 Security Validation Summary"
    echo "=============================="
    echo -e "${GREEN}Passed: $PASSED${NC}"
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
    echo -e "${RED}Failed: $FAILED${NC}"

    # Calculate score
    TOTAL=$((PASSED + WARNINGS + FAILED))
    if [ $TOTAL -gt 0 ]; then
        SCORE=$((PASSED * 100 / TOTAL))
        echo ""
        echo "🎯 Security Score: $SCORE/100"
        
        if [ $SCORE -ge 90 ]; then
            echo -e "${GREEN}🎉 Excellent security posture!${NC}"
        elif [ $SCORE -ge 75 ]; then
            echo -e "${YELLOW}⚠️  Good security, but room for improvement${NC}"
        else
            echo -e "${RED}❌ Security needs significant improvement${NC}"
        fi
    fi

    # Exit with appropriate code
    if [ $FAILED -gt 0 ]; then
        echo ""
        echo -e "${RED}❌ Security validation failed. Please address the issues above.${NC}"
        return 1
    else
        echo ""
        echo -e "${GREEN}✅ Security validation passed!${NC}"
        return 0
    fi
}

# Run validation if script is executed directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    run_validation
    exit $?
fi

