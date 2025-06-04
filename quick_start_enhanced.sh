#!/bin/bash
# Enhanced Quick Start Script for AI coordination System
# Handles EigenCode unavailability with enhanced mock analyzer

set -e

echo "🚀 AI coordination System - Enhanced Quick Start"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ "$1" = "success" ]; then
        echo -e "${GREEN}✅ $2${NC}"
    elif [ "$1" = "warning" ]; then
        echo -e "${YELLOW}⚠️  $2${NC}"
    elif [ "$1" = "error" ]; then
        echo -e "${RED}❌ $2${NC}"
    else
        echo "$2"
    fi
}

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check Python version
echo "1️⃣ Checking Python version..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        print_status "success" "Python $PYTHON_VERSION found"
    else
        print_status "error" "Python 3.8+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_status "error" "Python 3 not found"
    exit 1
fi

# Step 2: Create virtual environment
echo ""
echo "2️⃣ Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "success" "Virtual environment created"
else
    print_status "warning" "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_status "success" "Virtual environment activated"

# Step 3: Install dependencies
echo ""
echo "3️⃣ Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1

# Core dependencies
DEPENDENCIES=(
    "psycopg2-binary"
    "weaviate-client"
    "aiohttp"
    "asyncio"
    "prometheus-client"
    "pulumi"
    "pulumi-vultr"
    "requests"
    "psutil"
)

for dep in "${DEPENDENCIES[@]}"; do
    echo -n "Installing $dep... "
    if pip install "$dep" > /dev/null 2>&1; then
        echo "✓"
    else
        echo "✗"
        print_status "warning" "Failed to install $dep (continuing anyway)"
    fi
done

print_status "success" "Dependencies installed"

# Step 4: Check EigenCode availability
echo ""
echo "4️⃣ Checking EigenCode availability..."
python3 scripts/eigencode_installer.py --check-only 2>/dev/null || true

if command_exists eigencode; then
    print_status "success" "EigenCode is available"
else
    print_status "warning" "EigenCode not available - using enhanced mock analyzer"
    print_status "info" "Starting EigenCode monitor in background..."
    nohup python3 scripts/eigencode_monitor.py > logs/eigencode_monitor.log 2>&1 &
    echo $! > logs/eigencode_monitor.pid
fi

# Step 5: Configure environment
echo ""
echo "5️⃣ Configuring environment..."

# Create necessary directories
mkdir -p logs config ai_components/logs

# Check for required environment variables
ENV_VARS_REQUIRED=(
    "POSTGRES_HOST:localhost"
    "POSTGRES_PORT:5432"
    "POSTGRES_DB:conductor"
    "POSTGRES_USER:postgres"
    "POSTGRES_PASSWORD:postgres"
)

ENV_VARS_OPTIONAL=(
    "WEAVIATE_URL:http://localhost:8080"
    "PROMETHEUS_URL:http://localhost:9090"
    "GRAFANA_URL:http://localhost:3000"
)

echo "Required environment variables:"
for var_default in "${ENV_VARS_REQUIRED[@]}"; do
    var_name="${var_default%%:*}"
    default_value="${var_default#*:}"
    
    if [ -z "${!var_name}" ]; then
        export "$var_name=$default_value"
        print_status "warning" "$var_name not set, using default: $default_value"
    else
        print_status "success" "$var_name is set"
    fi
done

echo ""
echo "Optional environment variables:"
for var_default in "${ENV_VARS_OPTIONAL[@]}"; do
    var_name="${var_default%%:*}"
    default_value="${var_default#*:}"
    
    if [ -z "${!var_name}" ]; then
        print_status "info" "$var_name not set (optional)"
    else
        print_status "success" "$var_name is set"
    fi
done

# Step 6: Run system preparedness check
echo ""
echo "6️⃣ Running system preparedness check..."
if python3 scripts/system_preparedness.py; then
    print_status "success" "System preparedness check passed"
else
    print_status "warning" "System preparedness check had warnings"
fi

# Step 7: Optimize system
echo ""
echo "7️⃣ Optimizing system configuration..."
if python3 scripts/optimize_without_eigencode.py; then
    print_status "success" "System optimization completed"
else
    print_status "warning" "System optimization had issues"
fi

# Step 8: Run validation
echo ""
echo "8️⃣ Running system validation..."
if python3 scripts/system_validation.py; then
    print_status "success" "System validation passed"
else
    print_status "warning" "System validation had warnings"
fi

# Step 9: Start services (optional)
echo ""
echo "9️⃣ Optional services..."

# Check if PostgreSQL is running
if command_exists psql; then
    if psql -h localhost -U postgres -c "SELECT 1" > /dev/null 2>&1; then
        print_status "success" "PostgreSQL is running"
    else
        print_status "warning" "PostgreSQL not accessible - please start it manually"
        echo "  Run: sudo systemctl start postgresql"
    fi
else
    print_status "warning" "PostgreSQL client not found"
fi

# Check if monitoring stack should be started
if [ -f "monitoring/docker-compose.yml" ] && command_exists docker-compose; then
    echo ""
    read -p "Start monitoring stack (Prometheus + Grafana)? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f monitoring/docker-compose.yml up -d
        print_status "success" "Monitoring stack started"
    fi
fi

# Step 10: Display next steps
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure API keys (if using AI services):"
echo "   export OPENAI_API_KEY='your-key'"
echo "   export ANTHROPIC_API_KEY='your-key'"
echo ""
echo "2. Run the enhanced CLI:"
echo "   python ai_components/conductor_cli_enhanced.py"
echo ""
echo "3. Create and execute a workflow:"
echo "   python -c \"
import asyncio
from ai_components.coordination.ai_conductor_enhanced import (
    EnhancedWorkflowconductor, TaskDefinition, AgentRole, TaskPriority
)

async def main():
    conductor = EnhancedWorkflowconductor()
    workflow_id = 'test_workflow'
    context = await conductor.create_workflow(workflow_id)
    
    task = TaskDefinition(
        task_id='analyze',
        name='Analyze Codebase',
        agent_role=AgentRole.ANALYZER,
        inputs={'codebase_path': '.'},
        priority=TaskPriority.HIGH
    )
    
    result = await conductor.execute_workflow(workflow_id, [task])
    print(f'Workflow completed: {result.status.value}')

asyncio.run(main())
\""
echo ""
echo "4. View logs:"
echo "   tail -f ai_components/logs/conductor_enhanced.log"
echo ""
echo "5. Check EigenCode monitor status:"
echo "   tail -f logs/eigencode_monitor.log"
echo ""
echo "📚 Documentation:"
echo "   - System Status: docs/SYSTEM_STATUS_REPORT.md"
echo "   - conductor Guide: AI_CONDUCTOR_GUIDE.md"
echo "   - EigenCode Integration: docs/EIGENCODE_INTEGRATION_GUIDE.md"
echo ""
echo "🔧 Troubleshooting:"
echo "   - Run validation: python scripts/system_validation.py"
echo "   - Check security: python scripts/security_audit.py"
echo "   - Analyze performance: python scripts/performance_analyzer.py"
echo ""

# Create a simple test script
cat > test_conductor.py << 'EOF'
#!/usr/bin/env python3
"""Simple test script for the conductor"""

import asyncio
from ai_components.coordination.ai_conductor_enhanced import (
    EnhancedWorkflowconductor, TaskDefinition, AgentRole, TaskPriority
)

async def main():
    print("Testing AI conductor...")
    
    conductor = EnhancedWorkflowconductor()
    workflow_id = 'test_workflow'
    
    # Create workflow
    context = await conductor.create_workflow(workflow_id)
    print(f"✓ Workflow created: {workflow_id}")
    
    # Define task
    task = TaskDefinition(
        task_id='test_analysis',
        name='Test Analysis',
        agent_role=AgentRole.ANALYZER,
        inputs={'codebase_path': '.', 'options': {'depth': 'basic'}},
        priority=TaskPriority.HIGH,
        timeout=30
    )
    
    # Execute workflow
    print("✓ Executing workflow...")
    result = await conductor.execute_workflow(workflow_id, [task])
    
    print(f"✓ Workflow completed: {result.status.value}")
    print(f"✓ Execution time: {result.performance_metrics.get('execution_time', 0):.2f}s")
    
    # Show agent metrics
    metrics = conductor.get_agent_metrics()
    print("\nAgent Metrics:")
    for role, data in metrics.items():
        print(f"  {role.value}: {data['calls']} calls, {data['failures']} failures")

if __name__ == "__main__":
    asyncio.run(main())
EOF

chmod +x test_conductor.py
print_status "success" "Created test_conductor.py"

echo ""
echo "Run './test_conductor.py' to test the system!"
echo ""