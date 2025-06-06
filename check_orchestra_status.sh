#!/bin/bash

echo "🎭 ORCHESTRA STATUS CHECK"
echo "========================="
echo "Time: $(date)"
echo

# Check if critical security remediation is complete
echo "🔒 Security Status:"
if [ -f "security_remediation_report_*.json" ]; then
    echo "✅ Security remediation complete"
    latest_report=$(ls -t security_remediation_report_*.json | head -1)
    echo "   Report: $latest_report"
else
    echo "⏳ Security remediation in progress..."
fi
echo

# Check environment configuration
echo "⚙️ Environment Configuration:"
if [ -f ".env" ]; then
    echo "✅ .env file exists"
else
    echo "❌ .env file missing (create from .env.template)"
fi

if [ -f ".env.template" ]; then
    echo "✅ .env.template exists"
else
    echo "❌ .env.template missing"
fi
echo

# Check Docker status
echo "🐳 Docker Status:"
if docker ps >/dev/null 2>&1; then
    echo "✅ Docker is running"
    running_containers=$(docker ps --format "table {{.Names}}" | tail -n +2 | wc -l)
    echo "   Running containers: $running_containers"
else
    echo "❌ Docker is not running or not accessible"
fi
echo

# Check Pulumi configuration
echo "📦 Pulumi Configuration:"
if [ -f "Pulumi.yaml" ]; then
    echo "✅ Pulumi.yaml exists"
    if command -v pulumi >/dev/null 2>&1; then
        echo "✅ Pulumi CLI installed"
    else
        echo "❌ Pulumi CLI not installed"
    fi
else
    echo "❌ Pulumi.yaml missing"
fi
echo

# Check test framework
echo "🧪 Test Framework:"
if [ -f "test_validation_framework.py" ]; then
    echo "✅ Test framework exists"
    echo "   Run: python3 test_validation_framework.py"
else
    echo "❌ Test framework missing"
fi
echo

# Check deployment framework
echo "🚀 Deployment Framework:"
if [ -f "orchestra_deployment_framework.py" ]; then
    echo "✅ Deployment framework exists"
    echo "   Run: python3 orchestra_deployment_framework.py"
else
    echo "❌ Deployment framework missing"
fi
echo

# Check for Cherry AI Orchestrator files
echo "🍒 Cherry AI Orchestrator Status:"
if [ -f "cherry-ai-orchestrator-final.html" ]; then
    echo "✅ HTML interface exists"
fi
if [ -f "cherry-ai-orchestrator.js" ]; then
    echo "✅ JavaScript implementation exists"
fi
if [ -f "deploy-cherry-orchestrator.sh" ]; then
    echo "✅ Deployment script exists"
fi
if [ -f "quick_test_orchestrator.sh" ]; then
    echo "✅ Test script exists"
    # Check if test server is running
    if lsof -i:8080 >/dev/null 2>&1; then
        echo "✅ Test server running on http://localhost:8080"
    else
        echo "❌ Test server not running"
    fi
fi
echo

# Summary
echo "📊 SUMMARY"
echo "=========="
echo "1. Complete security remediation (if not done)"
echo "2. Create .env file from .env.template"
echo "3. Configure Lambda API credentials"
echo "4. Run validation tests"
echo "5. Deploy to staging environment"
echo
echo "For detailed status, run: python3 orchestrator_deployment_summary.py"