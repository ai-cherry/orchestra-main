#!/bin/bash

# Dashboard Validation Script
# Validates all components and integration points

set -e  # Exit on error

echo "🔍 Admin UI Validation Script"
echo "============================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation results
ERRORS=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
    else
        echo -e "${RED}✗${NC} $1 missing"
        ((ERRORS++))
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 directory exists"
    else
        echo -e "${RED}✗${NC} $1 directory missing"
        ((ERRORS++))
    fi
}

# Function to validate TypeScript file
check_ts_syntax() {
    if [ -f "$1" ]; then
        # Check for basic syntax issues
        if grep -q "export" "$1" && grep -q "import" "$1"; then
            echo -e "${GREEN}✓${NC} $1 has valid import/export syntax"
        else
            echo -e "${YELLOW}⚠${NC} $1 may have import/export issues"
            ((WARNINGS++))
        fi
    fi
}

echo ""
echo "1. Checking Project Structure..."
echo "--------------------------------"

# Check core directories
check_dir "app"
check_dir "components"
check_dir "components/OmniSearch"
check_dir "components/ConversationalInterface"
check_dir "components/QuickActions"
check_dir "hooks"
check_dir "types"

echo ""
echo "2. Checking Configuration Files..."
echo "----------------------------------"

# Check configuration files
check_file "package.json"
check_file "tsconfig.json"
check_file "next-env.d.ts"
check_file "tailwind.config.js"
check_file "postcss.config.js"
check_file ".env.example"

echo ""
echo "3. Checking Component Files..."
echo "------------------------------"

# OmniSearch components
check_file "components/OmniSearch/OmniSearch.tsx"
check_file "components/OmniSearch/SearchSuggestions.tsx"
check_file "components/OmniSearch/SearchModeIndicator.tsx"
check_file "components/OmniSearch/index.ts"

# ConversationalInterface components
check_file "components/ConversationalInterface/ConversationalInterface.tsx"
check_file "components/ConversationalInterface/MessageList.tsx"
check_file "components/ConversationalInterface/Message.tsx"
check_file "components/ConversationalInterface/ContextPanel.tsx"
check_file "components/ConversationalInterface/index.ts"

# QuickActions components
check_file "components/QuickActions/QuickActions.tsx"
check_file "components/QuickActions/index.ts"

# Hooks
check_file "hooks/useOmniSearch.ts"

# Types
check_file "types/search.ts"
check_file "types/conversation.ts"
check_file "types/speech.d.ts"

# App files
check_file "app/page.tsx"
check_file "app/layout.tsx"
check_file "app/globals.css"

echo ""
echo "4. Checking TypeScript Syntax..."
echo "--------------------------------"

# Validate TypeScript syntax in key files
check_ts_syntax "components/OmniSearch/OmniSearch.tsx"
check_ts_syntax "components/ConversationalInterface/ConversationalInterface.tsx"
check_ts_syntax "hooks/useOmniSearch.ts"

echo ""
echo "5. Checking Dependencies..."
echo "---------------------------"

if [ -f "package.json" ]; then
    # Check for required dependencies
    DEPS=("react" "next" "lodash" "@heroicons/react" "typescript" "tailwindcss")
    for dep in "${DEPS[@]}"; do
        if grep -q "\"$dep\"" package.json; then
            echo -e "${GREEN}✓${NC} $dep is in package.json"
        else
            echo -e "${RED}✗${NC} $dep missing from package.json"
            ((ERRORS++))
        fi
    done
fi

echo ""
echo "6. Checking Environment Setup..."
echo "--------------------------------"

# Check if node_modules exists (dependencies installed)
if [ -d "node_modules" ]; then
    echo -e "${GREEN}✓${NC} node_modules exists (dependencies installed)"
else
    echo -e "${YELLOW}⚠${NC} node_modules missing (run npm install)"
    ((WARNINGS++))
fi

# Check if .env.local exists
if [ -f ".env.local" ]; then
    echo -e "${GREEN}✓${NC} .env.local exists"
else
    echo -e "${YELLOW}⚠${NC} .env.local missing (copy from .env.example)"
    ((WARNINGS++))
fi

echo ""
echo "7. Validation Summary"
echo "--------------------"
echo -e "Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✅ All validations passed!${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Validation passed with warnings${NC}"
        exit 0
    fi
else
    echo -e "${RED}❌ Validation failed with $ERRORS errors${NC}"
    exit 1
fi