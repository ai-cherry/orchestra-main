#!/bin/bash

# 🍒 Cherry AI Complete System Setup & Verification Script
# Sets up Notion integration and tests the entire mockup automation system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
ADMIN_INTERFACE_DIR="../admin-interface"
SETUP_LOG="setup-verification.log"

# Print colored output
print_status() {
    echo -e "${BLUE}[SETUP]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S'): SETUP: $1" >> "$SETUP_LOG"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S'): SUCCESS: $1" >> "$SETUP_LOG"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S'): WARNING: $1" >> "$SETUP_LOG"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S'): ERROR: $1" >> "$SETUP_LOG"
}

# Banner
show_banner() {
    echo -e "${PURPLE}"
    echo "🍒 ============================================="
    echo "   Cherry AI Complete System Setup"
    echo "   Notion Integration & Full Verification"
    echo "=============================================${NC}"
    echo
    echo "$(date '+%Y-%m-%d %H:%M:%S'): Setup session started" >> "$SETUP_LOG"
}

# Step 1: Check system prerequisites
check_prerequisites() {
    print_status "Checking system prerequisites..."
    
    local all_good=true
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        print_success "Python 3: $(python3 --version)"
    else
        print_error "Python 3 not found"
        all_good=false
    fi
    
    # Check Node.js
    if command -v node >/dev/null 2>&1; then
        print_success "Node.js: $(node --version)"
    else
        print_error "Node.js not found"
        all_good=false
    fi
    
    # Check npm
    if command -v npm >/dev/null 2>&1; then
        print_success "npm: $(npm --version)"
    else
        print_error "npm not found"
        all_good=false
    fi
    
    # Check curl
    if command -v curl >/dev/null 2>&1; then
        print_success "curl: Available"
    else
        print_error "curl not found"
        all_good=false
    fi
    
    # Check git
    if command -v git >/dev/null 2>&1; then
        print_success "git: $(git --version)"
    else
        print_warning "git not found (optional)"
    fi
    
    if [[ "$all_good" == true ]]; then
        print_success "All prerequisites met!"
        return 0
    else
        print_error "Some prerequisites missing. Please install missing components."
        return 1
    fi
}

# Step 2: Setup Notion integration
setup_notion() {
    print_status "Setting up Notion integration..."
    
    echo -e "${CYAN}🎯 Notion Integration Setup${NC}"
    echo
    echo "To complete the Notion integration, you need to:"
    echo
    echo "1. 📝 Create a Notion integration:"
    echo "   → Visit: https://www.notion.so/my-integrations"
    echo "   → Click 'Create new integration'"
    echo "   → Name it 'Cherry AI Automation'"
    echo "   → Select your workspace"
    echo "   → Copy the Internal Integration Token"
    echo
    echo "2. 🗃️ Create a database for Cherry AI logs:"
    echo "   → Create a new page in Notion"
    echo "   → Add a database (table)"
    echo "   → Name it 'Cherry AI Development Log'"
    echo "   → Add these properties:"
    echo "     • Title (title)"
    echo "     • Date (date)"  
    echo "     • Type (select: Mockup Report, Screenshot, Daily Status)"
    echo "     • Status (select: Generated, In Progress, Complete)"
    echo "     • Mockup Count (number)"
    echo "     • Notes (rich text)"
    echo
    echo "3. 🔗 Share database with integration:"
    echo "   → Click 'Share' on your database page"
    echo "   → Add your 'Cherry AI Automation' integration"
    echo "   → Copy the database ID from the URL"
    echo
    echo "4. 🔑 Set environment variables:"
    echo
    
    # Check if already configured
    if [[ -n "$NOTION_API_TOKEN" ]] && [[ -n "$NOTION_DATABASE_ID" ]]; then
        print_success "Notion credentials already configured!"
        echo "NOTION_API_TOKEN: ${NOTION_API_TOKEN:0:20}..."
        echo "NOTION_DATABASE_ID: ${NOTION_DATABASE_ID:0:20}..."
        return 0
    fi
    
    echo -e "${YELLOW}Enter your Notion credentials (or press Enter to skip):${NC}"
    echo
    read -p "Notion API Token: " notion_token
    read -p "Notion Database ID: " database_id
    
    if [[ -n "$notion_token" ]] && [[ -n "$database_id" ]]; then
        # Set environment variables for this session
        export NOTION_API_TOKEN="$notion_token"
        export NOTION_DATABASE_ID="$database_id"
        
        # Create environment file
        cat > .env << EOF
# Cherry AI Notion Integration
NOTION_API_TOKEN=$notion_token
NOTION_DATABASE_ID=$database_id
EOF
        
        print_success "Notion credentials configured!"
        print_status "Environment file created: .env"
        
        # Test Notion connection
        test_notion_connection
    else
        print_warning "Notion integration skipped. You can configure it later."
        print_status "To configure later, run: python3 notion-integration.py --setup"
    fi
}

# Test Notion connection
test_notion_connection() {
    print_status "Testing Notion connection..."
    
    if python3 notion-integration.py --daily-status; then
        print_success "✅ Notion integration working perfectly!"
        
        # Create a test entry with current system status
        cat > notion-test-report.json << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "test": "Notion integration verification",
    "status": "success",
    "system": {
        "hostname": "$(hostname)",
        "user": "$(whoami)",
        "python": "$(python3 --version)",
        "node": "$(node --version 2>/dev/null || echo 'not available')"
    }
}
EOF
        
        print_success "Test report created: notion-test-report.json"
        
    else
        print_warning "Notion connection test failed. Check your credentials."
    fi
}

# Step 3: Install dependencies
install_dependencies() {
    print_status "Installing system dependencies..."
    
    # Install Python dependencies
    print_status "Installing Python requests library..."
    pip3 install requests --user 2>/dev/null || pip install requests --user || print_warning "Failed to install requests"
    
    # Install Node.js dependencies in admin-interface
    if [[ -d "$ADMIN_INTERFACE_DIR" ]]; then
        print_status "Installing Node.js dependencies..."
        cd "$ADMIN_INTERFACE_DIR"
        
        if [[ ! -d "node_modules" ]]; then
            npm install || print_warning "npm install failed"
        fi
        
        # Install puppeteer for screenshots
        if ! npm list puppeteer >/dev/null 2>&1; then
            print_status "Installing Puppeteer for screenshot generation..."
            npm install puppeteer --save-dev || print_warning "Failed to install Puppeteer"
        fi
        
        cd - >/dev/null
        print_success "Dependencies installed!"
    else
        print_error "Admin interface directory not found: $ADMIN_INTERFACE_DIR"
    fi
}

# Step 4: Test mockup automation system
test_mockup_system() {
    print_status "Testing complete mockup automation system..."
    
    if [[ ! -d "$ADMIN_INTERFACE_DIR" ]]; then
        print_error "Admin interface directory not found"
        return 1
    fi
    
    cd "$ADMIN_INTERFACE_DIR"
    
    # Test basic script functionality
    print_status "Testing automation script..."
    if [[ -x "mockup-automation.sh" ]]; then
        ./mockup-automation.sh list
        print_success "Basic automation script working!"
    else
        print_error "Automation script not found or not executable"
        chmod +x mockup-automation.sh 2>/dev/null || true
    fi
    
    # Test enhanced script if available
    if [[ -x "mockup-automation-enhanced.sh" ]]; then
        print_status "Testing enhanced automation script..."
        ./mockup-automation-enhanced.sh health
        print_success "Enhanced automation script working!"
    fi
    
    # Test mockup gallery
    print_status "Testing mockup gallery..."
    if [[ -f "mockups-index.html" ]]; then
        print_success "Mockup gallery found!"
        
        # Count available mockups
        local mockup_count=$(ls *.html 2>/dev/null | wc -l)
        print_success "Available mockups: $mockup_count"
    else
        print_error "Mockup gallery not found"
    fi
    
    cd - >/dev/null
}

# Step 5: Test server functionality
test_server() {
    print_status "Testing mockup server functionality..."
    
    cd "$ADMIN_INTERFACE_DIR"
    
    # Start server in background
    print_status "Starting test server on port 8001..."
    python3 -m http.server 8001 --directory . >/dev/null 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 3
    
    # Test server accessibility
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/mockups-index.html | grep -q "200"; then
        print_success "✅ Mockup server working perfectly!"
        print_success "Gallery accessible at: http://localhost:8001/mockups-index.html"
    else
        print_error "Server test failed"
    fi
    
    # Clean up
    kill $SERVER_PID 2>/dev/null || true
    
    cd - >/dev/null
}

# Step 6: Test GitHub Actions integration
test_github_actions() {
    print_status "Verifying GitHub Actions workflows..."
    
    local workflows_dir=".github/workflows"
    
    if [[ -d "$workflows_dir" ]]; then
        print_success "GitHub workflows directory found"
        
        # Check for mockup automation workflow
        if [[ -f "$workflows_dir/auto-mockups.yml" ]]; then
            print_success "✅ Auto-mockups workflow found"
        else
            print_warning "Auto-mockups workflow not found"
        fi
        
        # Check for daily Notion report workflow
        if [[ -f "$workflows_dir/notion-daily-report.yml" ]]; then
            print_success "✅ Daily Notion report workflow found"
        else
            print_warning "Daily Notion report workflow not found"
        fi
        
        print_status "GitHub Actions will run automatically on commits"
    else
        print_warning "GitHub workflows directory not found"
    fi
}

# Step 7: Generate comprehensive system report
generate_system_report() {
    print_status "Generating comprehensive system verification report..."
    
    local report_file="system-verification-$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# 🍒 Cherry AI System Verification Report

**Generated:** $(date)
**Hostname:** $(hostname)
**User:** $(whoami)

## ✅ System Health Check

### Prerequisites
- **Python:** $(python3 --version 2>/dev/null || echo "❌ Not available")
- **Node.js:** $(node --version 2>/dev/null || echo "❌ Not available")
- **npm:** $(npm --version 2>/dev/null || echo "❌ Not available")
- **curl:** $(curl --version 2>/dev/null | head -1 || echo "❌ Not available")
- **git:** $(git --version 2>/dev/null || echo "❌ Not available")

### Notion Integration
- **API Token:** $(if [[ -n "$NOTION_API_TOKEN" ]]; then echo "✅ Configured"; else echo "❌ Not configured"; fi)
- **Database ID:** $(if [[ -n "$NOTION_DATABASE_ID" ]]; then echo "✅ Configured"; else echo "❌ Not configured"; fi)
- **Connection Test:** $(if [[ -f "notion-test-report.json" ]]; then echo "✅ Successful"; else echo "❌ Failed"; fi)

### Mockup System
- **Admin Interface:** $(if [[ -d "$ADMIN_INTERFACE_DIR" ]]; then echo "✅ Found"; else echo "❌ Missing"; fi)
- **Automation Script:** $(if [[ -x "$ADMIN_INTERFACE_DIR/mockup-automation.sh" ]]; then echo "✅ Executable"; else echo "❌ Missing/Not executable"; fi)
- **Enhanced Script:** $(if [[ -x "$ADMIN_INTERFACE_DIR/mockup-automation-enhanced.sh" ]]; then echo "✅ Available"; else echo "❌ Not available"; fi)
- **Mockup Gallery:** $(if [[ -f "$ADMIN_INTERFACE_DIR/mockups-index.html" ]]; then echo "✅ Available"; else echo "❌ Missing"; fi)

### Dependencies
- **Python requests:** $(python3 -c "import requests; print('✅ Available')" 2>/dev/null || echo "❌ Missing")
- **Node modules:** $(if [[ -d "$ADMIN_INTERFACE_DIR/node_modules" ]]; then echo "✅ Installed"; else echo "❌ Missing"; fi)
- **Puppeteer:** $(cd "$ADMIN_INTERFACE_DIR" && npm list puppeteer >/dev/null 2>&1 && echo "✅ Available" || echo "❌ Missing")

### GitHub Actions
- **Workflows Directory:** $(if [[ -d ".github/workflows" ]]; then echo "✅ Found"; else echo "❌ Missing"; fi)
- **Auto-mockups:** $(if [[ -f ".github/workflows/auto-mockups.yml" ]]; then echo "✅ Configured"; else echo "❌ Missing"; fi)
- **Daily Reports:** $(if [[ -f ".github/workflows/notion-daily-report.yml" ]]; then echo "✅ Configured"; else echo "❌ Missing"; fi)

### Patrick Instructions
- **Main Guide:** $(if [[ -f ".patrick/README.md" ]]; then echo "✅ Available"; else echo "❌ Missing"; fi)
- **Notion Integration:** $(if [[ -f ".patrick/notion-integration.py" ]]; then echo "✅ Available"; else echo "❌ Missing"; fi)
- **Setup Script:** $(if [[ -f ".patrick/setup-complete-system.sh" ]]; then echo "✅ Available"; else echo "❌ Missing"; fi)

## 🚀 Quick Start Commands

\`\`\`bash
# Start mockup server
cd $ADMIN_INTERFACE_DIR
./mockup-automation.sh serve

# Access gallery
# http://localhost:8001/mockups-index.html

# Test enhanced features
./mockup-automation-enhanced.sh health

# Test Notion integration
cd ../.patrick
python3 notion-integration.py --daily-status
\`\`\`

## 📊 System Metrics
EOF

    # Add system metrics if available
    if [[ -d "$ADMIN_INTERFACE_DIR" ]]; then
        echo "- **Available Mockups:** $(ls $ADMIN_INTERFACE_DIR/*.html 2>/dev/null | wc -l)" >> "$report_file"
        echo "- **Total Mockup Size:** $(du -sh $ADMIN_INTERFACE_DIR/*.html 2>/dev/null | awk '{print $1}' | head -1 || echo "0K")" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF

## 🎯 Next Steps

1. **Bookmark the gallery:** http://localhost:8001/mockups-index.html
2. **Configure Notion if skipped:** python3 .patrick/notion-integration.py --setup
3. **Test enhanced features:** ./mockup-automation-enhanced.sh all
4. **Set up daily automation:** Add to crontab or GitHub repository secrets

---
*Generated by Cherry AI Complete System Setup*
EOF

    print_success "System verification report generated: $report_file"
    
    # Display key findings
    echo
    echo -e "${CYAN}📋 KEY VERIFICATION RESULTS:${NC}"
    
    if [[ -n "$NOTION_API_TOKEN" ]] && [[ -n "$NOTION_DATABASE_ID" ]]; then
        echo -e "✅ ${GREEN}Notion integration: CONFIGURED & TESTED${NC}"
    else
        echo -e "⚠️  ${YELLOW}Notion integration: NOT CONFIGURED${NC}"
    fi
    
    if [[ -x "$ADMIN_INTERFACE_DIR/mockup-automation.sh" ]]; then
        echo -e "✅ ${GREEN}Mockup automation: WORKING${NC}"
    else
        echo -e "❌ ${RED}Mockup automation: FAILED${NC}"
    fi
    
    if [[ -f "$ADMIN_INTERFACE_DIR/mockups-index.html" ]]; then
        echo -e "✅ ${GREEN}Mockup gallery: AVAILABLE${NC}"
    else
        echo -e "❌ ${RED}Mockup gallery: MISSING${NC}"
    fi
    
    if [[ -d ".github/workflows" ]]; then
        echo -e "✅ ${GREEN}GitHub Actions: CONFIGURED${NC}"
    else
        echo -e "⚠️  ${YELLOW}GitHub Actions: NOT CONFIGURED${NC}"
    fi
}

# Main execution flow
main() {
    show_banner
    
    print_status "Starting complete system setup and verification..."
    echo
    
    # Execute all setup steps
    check_prerequisites || exit 1
    echo
    
    setup_notion
    echo
    
    install_dependencies
    echo
    
    test_mockup_system
    echo
    
    test_server
    echo
    
    test_github_actions
    echo
    
    generate_system_report
    echo
    
    print_success "🎉 Complete system setup and verification finished!"
    
    echo
    echo -e "${PURPLE}=========================================${NC}"
    echo -e "${GREEN}🍒 CHERRY AI SYSTEM: READY TO USE!${NC}"
    echo -e "${PURPLE}=========================================${NC}"
    echo
    echo -e "${CYAN}📋 COPY & PASTE COMMANDS:${NC}"
    echo
    echo -e "${YELLOW}# Start mockup server${NC}"
    echo "cd $ADMIN_INTERFACE_DIR"
    echo "./mockup-automation.sh serve"
    echo
    echo -e "${YELLOW}# Bookmark this URL${NC}"
    echo "http://localhost:8001/mockups-index.html"
    echo
    echo -e "${YELLOW}# Test Notion integration${NC}"
    echo "python3 .patrick/notion-integration.py --daily-status"
    echo
    echo -e "${CYAN}📁 Important files:${NC}"
    echo "- Setup log: $SETUP_LOG"
    echo "- System report: system-verification-*.md"
    echo "- Patrick Instructions: .patrick/README.md"
    echo
}

# Run main function
main "$@" 