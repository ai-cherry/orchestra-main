#!/bin/bash

# 🍒 Cherry AI Admin Interface - Enhanced Mockup Automation with Notion Integration
# Provides complete mockup management with automatic Notion logging

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
PORT=8001
BUILD_DIR="out"
MOCKUP_INDEX="mockups-index.html"
NOTION_INTEGRATION="../.patrick/notion-integration.py"

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log_to_file "INFO: $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log_to_file "SUCCESS: $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log_to_file "WARNING: $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log_to_file "ERROR: $1"
}

# Logging function
log_to_file() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" >> mockup-automation.log
}

# Banner
show_banner() {
    echo -e "${PURPLE}"
    echo "🍒 ====================================="
    echo "   Cherry AI Enhanced Mockup Automation"
    echo "   With Notion Integration & Logging"
    echo "=====================================${NC}"
    echo
    log_to_file "Session started"
}

# Check if we're in the admin-interface directory
check_directory() {
    if [[ ! -f "package.json" ]] || [[ ! -d "src" ]]; then
        print_error "Please run this script from the admin-interface directory"
        exit 1
    fi
}

# Check Notion integration availability
check_notion_integration() {
    if [[ -f "$NOTION_INTEGRATION" ]]; then
        if [[ -n "$NOTION_API_TOKEN" ]] && [[ -n "$NOTION_DATABASE_ID" ]]; then
            return 0  # Notion available
        else
            print_warning "Notion credentials not set. Skipping Notion integration."
            return 1  # Notion not configured
        fi
    else
        print_warning "Notion integration script not found. Skipping."
        return 1
    fi
}

# Send report to Notion
send_to_notion() {
    local report_type="$1"
    local message="$2"
    
    if check_notion_integration; then
        print_status "Sending $report_type to Notion..."
        
        case "$report_type" in
            "mockup-report")
                python3 "$NOTION_INTEGRATION" --mockup-report || print_warning "Failed to send mockup report to Notion"
                ;;
            "daily-status")
                python3 "$NOTION_INTEGRATION" --daily-status || print_warning "Failed to send daily status to Notion"
                ;;
            *)
                print_warning "Unknown Notion report type: $report_type"
                ;;
        esac
    fi
}

# Start simple HTTP server for mockups with enhanced logging
start_mockup_server() {
    print_status "Starting enhanced mockup server on port $PORT..."
    
    # Kill existing server if running
    pkill -f "python3 -m http.server $PORT" 2>/dev/null || true
    
    # Start new server
    python3 -m http.server $PORT --directory . > mockup-server.log 2>&1 &
    SERVER_PID=$!
    
    sleep 2
    
    if kill -0 $SERVER_PID 2>/dev/null; then
        print_success "Enhanced mockup server started successfully!"
        echo -e "${CYAN}📱 Mockup Gallery: http://localhost:$PORT/$MOCKUP_INDEX${NC}"
        echo -e "${CYAN}📁 File Browser: http://localhost:$PORT/${NC}"
        echo -e "${CYAN}📊 Server Logs: tail -f mockup-server.log${NC}"
        echo -e "${YELLOW}💡 Tip: Keep this terminal open to maintain the server${NC}"
        echo
        
        # Log server access info
        log_to_file "Server started on port $PORT (PID: $SERVER_PID)"
        
        # Send status to Notion
        send_to_notion "daily-status" "Mockup server started successfully"
        
        return 0
    else
        print_error "Failed to start mockup server"
        return 1
    fi
}

# Build the React app with enhanced reporting
build_app() {
    print_status "Building React application with enhanced reporting..."
    
    local start_time=$(date +%s)
    
    if [[ ! -d "node_modules" ]]; then
        print_warning "Node modules not found. Installing dependencies..."
        npm install || {
            print_error "Failed to install dependencies"
            return 1
        }
    fi
    
    # Build the app
    print_status "Running npm build..."
    npm run build || {
        print_error "Build failed"
        return 1
    }
    
    local end_time=$(date +%s)
    local build_duration=$((end_time - start_time))
    
    if [[ -d "$BUILD_DIR" ]]; then
        print_success "Build completed successfully in ${build_duration}s!"
        
        # Copy built files as a new mockup
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        BUILT_MOCKUP="built-interface-$TIMESTAMP.html"
        
        if [[ -f "$BUILD_DIR/index.html" ]]; then
            cp "$BUILD_DIR/index.html" "$BUILT_MOCKUP"
            print_success "Created new mockup: $BUILT_MOCKUP"
            log_to_file "Built mockup: $BUILT_MOCKUP (build time: ${build_duration}s)"
        fi
        
        # Generate build report
        generate_build_report "$build_duration"
        
        # Send report to Notion
        send_to_notion "mockup-report" "Build completed in ${build_duration}s, new mockup created"
        
        return 0
    else
        print_error "Build failed - output directory not found"
        return 1
    fi
}

# Generate comprehensive build report
generate_build_report() {
    local build_duration="$1"
    local report_file="build-report-$(date +%Y%m%d_%H%M%S).md"
    
    print_status "Generating build report..."
    
    cat > "$report_file" << EOF
# 🍒 Cherry AI Build Report

**Generated:** $(date)
**Build Duration:** ${build_duration} seconds
**Status:** ✅ Success

## 📊 Build Metrics
- **Total Mockups:** $(ls *.html 2>/dev/null | wc -l)
- **Total Size:** $(du -sh *.html 2>/dev/null | awk '{sum+=\$1} END {print sum}' || echo "N/A")
- **Node Version:** $(node --version 2>/dev/null || echo "Not available")
- **NPM Version:** $(npm --version 2>/dev/null || echo "Not available")

## 📱 Available Mockups
EOF

    # List all mockups with details
    for file in *.html; do
        if [[ -f "$file" && "$file" != "index.html" ]]; then
            size=$(du -h "$file" | cut -f1)
            modified=$(date -r "$file" '+%Y-%m-%d %H:%M')
            echo "- **$file** (${size}) - Modified: $modified" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF

## 🔧 System Info
- **Hostname:** $(hostname)
- **Working Directory:** $(pwd)
- **Git Branch:** $(git branch --show-current 2>/dev/null || echo "Not a git repo")
- **Last Commit:** $(git log -1 --oneline 2>/dev/null || echo "No commits")

## 📈 Performance
- **Build Time:** ${build_duration}s
- **Avg File Size:** $(find *.html -name "*.html" 2>/dev/null | xargs du -b | awk '{sum+=\$1; count++} END {if(count>0) print int(sum/count/1024)"KB"; else print "0KB"}')

---
*Generated by Cherry AI Enhanced Mockup Automation*
EOF

    print_success "Build report generated: $report_file"
    log_to_file "Build report generated: $report_file"
}

# Generate screenshots with enhanced metadata
generate_screenshots() {
    print_status "Generating enhanced screenshots with metadata..."
    
    SCREENSHOT_DIR="screenshots"
    mkdir -p "$SCREENSHOT_DIR"
    
    # Check if we have puppeteer available
    if ! command -v node >/dev/null 2>&1; then
        print_warning "Node.js not available for screenshot generation"
        return 1
    fi
    
    # Create enhanced screenshot script
    cat > screenshot-generator.js << 'EOF'
const puppeteer = require('puppeteer');
const fs = require('fs');

const mockups = [
    'enhanced-production-interface.html',
    'enhanced-admin-interface.html',
    'ai-tools-dashboard.html',
    'production-admin-interface.html',
    'chat.html',
    'enhanced-index.html',
    'cherry-ai-working.html',
    'working-interface.html'
];

async function generateScreenshots() {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const results = [];
    
    for (const mockup of mockups) {
        if (fs.existsSync(mockup)) {
            try {
                const page = await browser.newPage();
                await page.setViewport({ width: 1200, height: 800 });
                
                const startTime = Date.now();
                await page.goto(`file://${__dirname}/${mockup}`, { 
                    waitUntil: 'networkidle2',
                    timeout: 10000 
                });
                const loadTime = Date.now() - startTime;
                
                const filename = mockup.replace('.html', '.png');
                await page.screenshot({ 
                    path: `screenshots/${filename}`,
                    fullPage: true 
                });
                
                // Generate metadata
                const stats = fs.statSync(mockup);
                const metadata = {
                    mockup: mockup,
                    screenshot: filename,
                    fileSize: stats.size,
                    loadTime: loadTime,
                    timestamp: new Date().toISOString(),
                    viewport: { width: 1200, height: 800 }
                };
                
                fs.writeFileSync(`screenshots/${filename}.meta.json`, JSON.stringify(metadata, null, 2));
                
                results.push(metadata);
                console.log(`✅ Generated: screenshots/${filename} (${loadTime}ms)`);
                await page.close();
            } catch (error) {
                console.error(`❌ Failed to screenshot ${mockup}:`, error.message);
            }
        }
    }
    
    // Generate summary report
    fs.writeFileSync('screenshots/screenshot-report.json', JSON.stringify(results, null, 2));
    
    await browser.close();
    console.log(`🎉 Screenshot generation completed! Generated ${results.length} screenshots.`);
}

generateScreenshots().catch(console.error);
EOF

    if npm list puppeteer >/dev/null 2>&1; then
        node screenshot-generator.js
        print_success "Enhanced screenshots generated in $SCREENSHOT_DIR/"
        
        # Upload screenshots to Notion if available
        if check_notion_integration; then
            for screenshot in screenshots/*.png; do
                if [[ -f "$screenshot" ]]; then
                    python3 "$NOTION_INTEGRATION" --screenshot-upload "$screenshot" || true
                fi
            done
        fi
    else
        print_warning "Puppeteer not installed. Run: npm install puppeteer"
        print_status "Screenshots can be generated manually by visiting mockups in browser"
    fi
    
    # Clean up
    rm -f screenshot-generator.js
}

# Health check with comprehensive reporting
health_check() {
    print_status "Running comprehensive health check..."
    
    local health_report="health-check-$(date +%Y%m%d_%H%M%S).json"
    
    # Server health
    local server_status="offline"
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/mockups-index.html | grep -q "200"; then
        server_status="healthy"
    fi
    
    # File system health
    local mockup_count=$(ls *.html 2>/dev/null | wc -l)
    local total_size=$(du -sh *.html 2>/dev/null | awk '{print $1}' | head -1 || echo "0K")
    
    # Git health
    local git_status="unknown"
    if git status >/dev/null 2>&1; then
        git_status="healthy"
    fi
    
    # Generate health report
    cat > "$health_report" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "server": {
        "status": "$server_status",
        "port": $PORT,
        "url": "http://localhost:$PORT/mockups-index.html"
    },
    "mockups": {
        "count": $mockup_count,
        "totalSize": "$total_size"
    },
    "git": {
        "status": "$git_status",
        "branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')",
        "lastCommit": "$(git log -1 --oneline 2>/dev/null || echo 'none')"
    },
    "system": {
        "nodejs": "$(node --version 2>/dev/null || echo 'not installed')",
        "npm": "$(npm --version 2>/dev/null || echo 'not installed')",
        "python": "$(python3 --version 2>/dev/null || echo 'not installed')"
    }
}
EOF

    print_success "Health check completed: $health_report"
    cat "$health_report"
    
    # Send to Notion
    send_to_notion "daily-status" "Health check completed - Server: $server_status, Mockups: $mockup_count"
}

# Enhanced cleanup with logging
cleanup() {
    print_status "Running enhanced cleanup..."
    
    local cleaned_count=0
    
    # Remove old screenshots
    if [[ -d "screenshots" ]]; then
        local old_screenshots=$(find screenshots -name "*.png" -mtime +7 2>/dev/null | wc -l)
        find screenshots -name "*.png" -mtime +7 -delete 2>/dev/null || true
        cleaned_count=$((cleaned_count + old_screenshots))
    fi
    
    # Remove old built mockups
    local old_mockups=$(find . -name "built-interface-*.html" -mtime +3 2>/dev/null | wc -l)
    find . -name "built-interface-*.html" -mtime +3 -delete 2>/dev/null || true
    cleaned_count=$((cleaned_count + old_mockups))
    
    # Remove old build reports
    local old_reports=$(find . -name "build-report-*.md" -mtime +7 2>/dev/null | wc -l)
    find . -name "build-report-*.md" -mtime +7 -delete 2>/dev/null || true
    cleaned_count=$((cleaned_count + old_reports))
    
    # Remove old health reports
    local old_health=$(find . -name "health-check-*.json" -mtime +7 2>/dev/null | wc -l)
    find . -name "health-check-*.json" -mtime +7 -delete 2>/dev/null || true
    cleaned_count=$((cleaned_count + old_health))
    
    print_success "Cleanup completed - removed $cleaned_count old files"
    log_to_file "Cleanup completed - removed $cleaned_count old files"
}

# Main command handler
main() {
    show_banner
    check_directory
    
    case "${1:-help}" in
        "serve"|"s")
            start_mockup_server
            ;;
        "build"|"b")
            build_app
            ;;
        "screenshots"|"ss")
            generate_screenshots
            ;;
        "health"|"h")
            health_check
            ;;
        "cleanup"|"c")
            cleanup
            ;;
        "all"|"a")
            build_app && generate_screenshots && start_mockup_server
            ;;
        "notion-test"|"nt")
            if check_notion_integration; then
                print_status "Testing Notion integration..."
                send_to_notion "daily-status" "Manual test from enhanced automation script"
            else
                print_error "Notion integration not available"
            fi
            ;;
        "help"|*)
            echo -e "${CYAN}Cherry AI Enhanced Mockup Automation Commands:${NC}"
            echo
            echo -e "  ${GREEN}serve${NC}      (s)  - Start HTTP server for mockups"
            echo -e "  ${GREEN}build${NC}      (b)  - Build React app with comprehensive reporting"
            echo -e "  ${GREEN}screenshots${NC} (ss) - Generate enhanced screenshots with metadata"
            echo -e "  ${GREEN}health${NC}     (h)  - Run comprehensive health check"
            echo -e "  ${GREEN}cleanup${NC}    (c)  - Clean old files with detailed logging"
            echo -e "  ${GREEN}all${NC}        (a)  - Full workflow (build + screenshots + serve)"
            echo -e "  ${GREEN}notion-test${NC} (nt) - Test Notion integration"
            echo -e "  ${GREEN}help${NC}           - Show this help message"
            echo
            echo -e "${YELLOW}Enhanced Features:${NC}"
            echo -e "  • Automatic Notion integration for reports"
            echo -e "  • Comprehensive build metrics and timing"
            echo -e "  • Enhanced screenshot metadata generation"
            echo -e "  • System health monitoring and reporting"
            echo -e "  • Detailed logging to mockup-automation.log"
            echo
            echo -e "${CYAN}Notion Setup (if not configured):${NC}"
            echo -e "  export NOTION_API_TOKEN='your_token'"
            echo -e "  export NOTION_DATABASE_ID='your_database_id'"
            echo
            ;;
    esac
}

# Handle script termination
trap 'print_warning "Enhanced automation script interrupted"; log_to_file "Script interrupted"' INT TERM

# Run main function
main "$@" 