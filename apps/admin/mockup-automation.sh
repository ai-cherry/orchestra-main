#!/bin/bash

# 🍒 Cherry AI Admin Interface - Mockup Automation Script
# Provides easy commands for building, serving, and managing mockups

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

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
show_banner() {
    echo -e "${PURPLE}"
    echo "🍒 =================================="
    echo "   Cherry AI Mockup Automation"
    echo "   Easy Interface Management"
    echo "==================================${NC}"
    echo
}

# Check if we're in the admin-interface directory
check_directory() {
    if [[ ! -f "package.json" ]] || [[ ! -d "src" ]]; then
        print_error "Please run this script from the admin-interface directory"
        exit 1
    fi
}

# Start simple HTTP server for mockups
start_mockup_server() {
    print_status "Starting mockup server on port $PORT..."
    
    # Kill existing server if running
    pkill -f "python3 -m http.server $PORT" 2>/dev/null || true
    
    # Start new server
    python3 -m http.server $PORT --directory . > /dev/null 2>&1 &
    SERVER_PID=$!
    
    sleep 2
    
    if kill -0 $SERVER_PID 2>/dev/null; then
        print_success "Mockup server started successfully!"
        echo -e "${CYAN}📱 Mockup Gallery: http://localhost:$PORT/$MOCKUP_INDEX${NC}"
        echo -e "${CYAN}📁 File Browser: http://localhost:$PORT/${NC}"
        echo -e "${YELLOW}💡 Tip: Keep this terminal open to maintain the server${NC}"
        echo
        return 0
    else
        print_error "Failed to start mockup server"
        return 1
    fi
}

# Build the React app for production
build_app() {
    print_status "Building React application..."
    
    if [[ ! -d "node_modules" ]]; then
        print_warning "Node modules not found. Installing dependencies..."
        npm install
    fi
    
    # Build the app
    npm run build
    
    if [[ -d "$BUILD_DIR" ]]; then
        print_success "Build completed successfully!"
        
        # Copy built files as a new mockup
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        BUILT_MOCKUP="built-interface-$TIMESTAMP.html"
        
        if [[ -f "$BUILD_DIR/index.html" ]]; then
            cp "$BUILD_DIR/index.html" "$BUILT_MOCKUP"
            print_success "Created new mockup: $BUILT_MOCKUP"
        fi
        
        return 0
    else
        print_error "Build failed - output directory not found"
        return 1
    fi
}

# Generate screenshots of mockups (requires puppeteer)
generate_screenshots() {
    print_status "Generating mockup screenshots..."
    
    SCREENSHOT_DIR="screenshots"
    mkdir -p "$SCREENSHOT_DIR"
    
    # Check if we have puppeteer available
    if ! command -v node >/dev/null 2>&1; then
        print_warning "Node.js not available for screenshot generation"
        return 1
    fi
    
    # Create a simple screenshot script
    cat > screenshot-generator.js << 'EOF'
const puppeteer = require('puppeteer');
const fs = require('fs');

const mockups = [
    'enhanced-production-interface.html',
    'enhanced-admin-interface.html',
    'ai-tools-dashboard.html',
    'production-admin-interface.html',
    'chat.html',
    'enhanced-index.html'
];

async function generateScreenshots() {
    const browser = await puppeteer.launch();
    
    for (const mockup of mockups) {
        if (fs.existsSync(mockup)) {
            const page = await browser.newPage();
            await page.setViewport({ width: 1200, height: 800 });
            await page.goto(`file://${__dirname}/${mockup}`);
            await page.waitForTimeout(2000);
            
            const filename = mockup.replace('.html', '.png');
            await page.screenshot({ 
                path: `screenshots/${filename}`,
                fullPage: true 
            });
            
            console.log(`✅ Generated: screenshots/${filename}`);
            await page.close();
        }
    }
    
    await browser.close();
    console.log('🎉 All screenshots generated!');
}

generateScreenshots().catch(console.error);
EOF

    if npm list puppeteer >/dev/null 2>&1; then
        node screenshot-generator.js
        print_success "Screenshots generated in $SCREENSHOT_DIR/"
    else
        print_warning "Puppeteer not installed. Run: npm install puppeteer"
        print_status "Screenshots can be generated manually by visiting mockups in browser"
    fi
    
    # Clean up
    rm -f screenshot-generator.js
}

# Update mockup index with current file stats
update_mockup_index() {
    print_status "Updating mockup index..."
    
    # This could be enhanced to dynamically update the HTML
    # For now, just update the timestamp
    if [[ -f "$MOCKUP_INDEX" ]]; then
        print_success "Mockup index is ready"
    else
        print_warning "Mockup index not found. Please ensure mockups-index.html exists."
    fi
}

# Clean up old builds and temporary files
cleanup() {
    print_status "Cleaning up temporary files..."
    
    # Remove old screenshots
    if [[ -d "screenshots" ]]; then
        find screenshots -name "*.png" -mtime +7 -delete 2>/dev/null || true
    fi
    
    # Remove old built mockups
    find . -name "built-interface-*.html" -mtime +3 -delete 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Show available mockups
list_mockups() {
    print_status "Available mockups:"
    echo
    
    for file in *.html; do
        if [[ -f "$file" && "$file" != "index.html" ]]; then
            size=$(du -h "$file" | cut -f1)
            echo -e "  ${CYAN}📄 $file${NC} (${size})"
        fi
    done
    echo
}

# Watch for changes and auto-rebuild
watch_mode() {
    print_status "Starting watch mode..."
    print_warning "This requires 'entr' to be installed (brew install entr / apt install entr)"
    
    if command -v entr >/dev/null 2>&1; then
        print_status "Watching for changes in src/ directory..."
        find src -name "*.tsx" -o -name "*.jsx" -o -name "*.ts" -o -name "*.js" | entr -r ./mockup-automation.sh build
    else
        print_error "Please install 'entr' for watch mode"
        print_status "Alternative: Use 'npm run dev' for development server"
    fi
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
        "update"|"u")
            update_mockup_index
            ;;
        "list"|"l")
            list_mockups
            ;;
        "cleanup"|"c")
            cleanup
            ;;
        "watch"|"w")
            watch_mode
            ;;
        "all"|"a")
            build_app && update_mockup_index && start_mockup_server
            ;;
        "dev"|"d")
            print_status "Starting development server..."
            npm run dev
            ;;
        "help"|"h"|*)
            echo -e "${CYAN}Cherry AI Mockup Automation Commands:${NC}"
            echo
            echo -e "  ${GREEN}serve${NC}     (s)  - Start HTTP server for mockups"
            echo -e "  ${GREEN}build${NC}     (b)  - Build React app and create mockup"
            echo -e "  ${GREEN}screenshots${NC} (ss) - Generate PNG screenshots of mockups"
            echo -e "  ${GREEN}update${NC}    (u)  - Update mockup index page"
            echo -e "  ${GREEN}list${NC}      (l)  - List all available mockups"
            echo -e "  ${GREEN}cleanup${NC}   (c)  - Clean old files and temporary data"
            echo -e "  ${GREEN}watch${NC}     (w)  - Watch for changes and auto-rebuild"
            echo -e "  ${GREEN}all${NC}       (a)  - Build, update, and serve (full workflow)"
            echo -e "  ${GREEN}dev${NC}       (d)  - Start development server (npm run dev)"
            echo -e "  ${GREEN}help${NC}      (h)  - Show this help message"
            echo
            echo -e "${YELLOW}Examples:${NC}"
            echo -e "  ./mockup-automation.sh serve"
            echo -e "  ./mockup-automation.sh build"
            echo -e "  ./mockup-automation.sh all"
            echo
            echo -e "${CYAN}Quick Start:${NC}"
            echo -e "  1. Run: ${GREEN}./mockup-automation.sh serve${NC}"
            echo -e "  2. Open: ${BLUE}http://localhost:$PORT/$MOCKUP_INDEX${NC}"
            echo -e "  3. Review all your mockups in one place!"
            echo
            ;;
    esac
}

# Handle script termination
trap 'print_warning "Script interrupted"' INT TERM

# Run main function
main "$@" 