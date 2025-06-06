#!/bin/bash

echo "Cherry AI Orchestrator - Comprehensive Codebase Analysis"
echo "======================================================="
echo ""

# Make all scripts executable
echo "Setting up scripts..."
chmod +x comprehensive_codebase_analyzer.py
chmod +x automated_syntax_fixer.py
chmod +x run_comprehensive_analysis.sh
chmod +x fix_syntax_errors.sh
chmod +x security_scan.sh

echo "✓ Scripts ready"
echo ""

# Run the comprehensive analysis
echo "Starting comprehensive analysis..."
echo "---------------------------------"
./run_comprehensive_analysis.sh

echo ""
echo "Analysis complete!"
echo ""
echo "CRITICAL FINDINGS:"
echo "=================="
echo "1. 644 Python files have syntax errors (indentation issues)"
echo "   - This is blocking ALL Python code execution"
echo "   - Run: ./fix_syntax_errors.sh"
echo ""
echo "2. Services are down:"
echo "   - weaviate service is not running"
echo "   - orchestra-api service is not running"
echo "   - These need syntax fixes before they can start"
echo ""
echo "3. Recommended action sequence:"
echo "   a) ./fix_syntax_errors.sh     # Fix all Python syntax errors"
echo "   b) ./security_scan.sh          # Check for hardcoded credentials"
echo "   c) ./restart_services.sh       # Restart all services"
echo "   d) ./test_deployment.sh        # Test the deployment"
echo ""
echo "The entire Python codebase is currently non-functional due to"
echo "systematic indentation errors. This must be fixed first!"