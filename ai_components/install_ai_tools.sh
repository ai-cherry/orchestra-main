#!/bin/bash
# AI Tools Installation Script
# Installs EigenCode, Cursor AI, and  Code with proper configuration

set -e  # Exit on error

echo "=========================================="
echo "AI coordination Tools Installation Script"
echo "=========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

if [[ $EUID -ne 0 ]]; then
   exit 1
fi

# Base directory
cd $BASE_DIR

# Create necessary directories
print_status "Creating directory structure..."

# Install Python dependencies
print_status "Installing Python dependencies..."
cat > requirements.txt << EOF
psycopg2-binary==2.9.9
aiohttp==3.9.1
weaviate-client==3.24.2
pydantic==2.5.2
python-dotenv==1.0.0
asyncio==3.4.3
click==8.1.7
rich==13.7.0
EOF

pip install -r requirements.txt

# Create configuration files
print_status "Creating configuration files..."

# Main configuration
cat > configs/conductor_config.yaml << EOF
# AI conductor Configuration
conductor:
  workflow_timeout: 3600  # 1 hour
  max_parallel_tasks: 5
  checkpoint_interval: 300  # 5 minutes
  
agents:
  eigencode:
    enabled: true
    timeout: 600
    retry_attempts: 3
    
  cursor_ai:
    enabled: true
    timeout: 900
    retry_attempts: 2
    
    enabled: true
    timeout: 600
    retry_attempts: 3

mcp_server:
  url: "http://localhost:8080"
  health_check_interval: 30
  
database:
  connection_pool_size: 10
  query_timeout: 30
  
weaviate:
  batch_size: 100
  timeout: 30
  
logging:
  level: INFO
  max_file_size: 100MB
  backup_count: 5
EOF

# Environment template
cat > configs/.env.template << EOF
# GitHub Secrets Configuration Template
# Copy this to .env and fill in your actual values

# PostgreSQL Configuration
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=conductor_db
POSTGRES_USER=your_postgres_user
POSTGRES_PASSWORD=your_postgres_password

# Weaviate Cloud Configuration
WEAVIATE_URL=https://your-instance.weaviate.network
WEAVIATE_API_KEY=your_weaviate_api_key

# Airbyte Cloud Configuration
AIRBYTE_API_URL=https://api.airbyte.com
AIRBYTE_API_KEY=your_airbyte_api_key
AIRBYTE_WORKSPACE_ID=your_workspace_id

# AI Tool API Keys
EIGENCODE_API_KEY=your_eigencode_api_key
CURSOR_AI_API_KEY=your_cursor_ai_api_key

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8080
MCP_SERVER_API_KEY=your_mcp_api_key

# GitHub Configuration
GITHUB_TOKEN=your_github_token
GITHUB_ORG=your_github_org
GITHUB_REPO=your_github_repo
EOF

# EigenCode installation placeholder
print_status "Setting up EigenCode directory..."
cat > eigencode/install_eigencode.sh << 'EOF'
#!/bin/bash
# EigenCode Installation Script
# This will be updated when EigenCode service is available

echo "EigenCode installation placeholder"
echo "The service is currently unavailable (404 error)"
echo "Please check https://www.eigencode.dev for updates"

# Create placeholder executable
cat > eigencode << 'EIGENCODE'
#!/bin/bash
echo "EigenCode CLI placeholder - awaiting proper installation"
echo "Visit https://www.eigencode.dev for installation instructions"
exit 1
EIGENCODE

chmod +x eigencode
EOF
chmod +x eigencode/install_eigencode.sh

# Cursor AI setup
print_status "Setting up Cursor AI integration..."
cat > cursor_ai/cursor_integration.py << 'EOF'
#!/usr/bin/env python3
"""
Cursor AI Integration Module
Provides API wrapper for Cursor AI operations
"""

import os
import json
import aiohttp
from typing import Dict, List, Optional

class CursorAIClient:
    """Cursor AI API Client"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('CURSOR_AI_API_KEY')
        self.base_url = "https://api.cursor.ai/v1"
        
    async def analyze_code(self, file_path: str) -> Dict:
        """Analyze code file with Cursor AI"""
        # Placeholder implementation
        return {
            "status": "analyzed",
            "file": file_path,
            "suggestions": []
        }
    
    async def implement_changes(self, changes: List[Dict]) -> Dict:
        """Implement code changes"""
        # Placeholder implementation
        return {
            "status": "implemented",
            "changes_count": len(changes)
        }
    
    async def optimize_performance(self, target_metrics: Dict) -> Dict:
        """Optimize code for performance"""
        # Placeholder implementation
        return {
            "status": "optimized",
            "improvements": {}
        }

if __name__ == "__main__":
    print("Cursor AI Integration Module")
    print("Use this module to interact with Cursor AI API")
EOF

#  Code setup
print_status "Setting up  Code integration..."
#!/usr/bin/env python3
"""
 Code Integration Module
Provides API wrapper for  Code operations
"""

import os
import json
import aiohttp
from typing import Dict, List, Optional

class CodeClient:
    """ Code API Client"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('_CODE_API_KEY')
        
    async def refine_technology_stack(self, stack_config: Dict) -> Dict:
        """Refine technology stack for ease of use"""
        # Placeholder implementation
        return {
            "status": "refined",
            "stack": stack_config,
            "recommendations": []
        }
    
    async def improve_developer_experience(self, codebase_path: str) -> Dict:
        """Improve developer experience"""
        # Placeholder implementation
        return {
            "status": "improved",
            "dx_score": 8.5
        }
    
    async def generate_documentation(self, components: List[str]) -> Dict:
        """Generate comprehensive documentation"""
        # Placeholder implementation
        return {
            "status": "documented",
            "files_created": []
        }

if __name__ == "__main__":
    print(" Code Integration Module")
    print("Use this module to interact with  Code API")
EOF

# Create MCP server integration
print_status "Creating MCP server integration..."
cat > ../mcp_server/coordinator_server.py << 'EOF'
#!/usr/bin/env python3
"""
MCP Server for AI conductor
Provides task management and context storage
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import uuid

app = FastAPI(title="AI conductor MCP Server")

# In-memory task storage (replace with persistent storage in production)
tasks = {}

class TaskCreate(BaseModel):
    task_id: str
    name: str
    agent_role: str
    inputs: Dict
    dependencies: List[str] = []
    priority: int = 0
    timeout: int = 300

class TaskUpdate(BaseModel):
    status: str
    results: Optional[Dict] = None

class Task(TaskCreate):
    status: str = "pending"
    results: Optional[Dict] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

@app.get("/")
    return {"message": "AI conductor MCP Server", "version": "1.0.0"}

@app.post("/tasks", response_model=Task)
async def create_task(task: TaskCreate):
    """Create a new task"""
    if task.task_id in tasks:
        raise HTTPException(status_code=400, detail="Task already exists")
    
    new_task = Task(**task.dict())
    tasks[task.task_id] = new_task
    return new_task

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get task by ID"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.patch("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, update: TaskUpdate):
    """Update task status"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    task.status = update.status
    if update.results:
        task.results = update.results
    task.updated_at = datetime.now()
    
    return task

@app.get("/tasks", response_model=List[Task])
async def list_tasks(status: Optional[str] = None):
    """List all tasks, optionally filtered by status"""
    if status:
        return [t for t in tasks.values() if t.status == status]
    return list(tasks.values())

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del tasks[task_id]
    return {"message": "Task deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF

# Create CLI tool
print_status "Creating conductor CLI..."
cat > conductor_cli.py << 'EOF'
#!/usr/bin/env python3
"""
AI conductor CLI
Command-line interface for cherry_aiting AI tools
"""

import click
import asyncio
import json
from pathlib import Path
import sys

# Add coordination module to path
sys.path.append(str(Path(__file__).parent))

from coordination.ai_conductor import (
    Workflowconductor, TaskDefinition, AgentRole
)

@click.group()
def cli():
    """AI conductor CLI - Coordinate EigenCode, Cursor AI, and  Code"""
    pass

@cli.command()
@click.option('--codebase', '-c', default='.', help='Path to codebase')
@click.option('--output', '-o', default='analysis_report.json', help='Output file')
def analyze(codebase, output):
    """Analyze codebase with EigenCode"""
    click.echo(f"Analyzing codebase at {codebase}...")
    
    async def run_analysis():
        conductor = Workflowconductor()
        workflow_id = f"analysis_{Path(codebase).name}"
        context = await conductor.create_workflow(workflow_id)
        
        task = TaskDefinition(
            task_id="analyze",
            name="Codebase Analysis",
            agent_role=AgentRole.ANALYZER,
            inputs={"codebase_path": codebase}
        )
        
        result = await conductor.execute_workflow(workflow_id, [task])
        
        with open(output, 'w') as f:
            json.dump(result.results, f, indent=2)
        
        click.echo(f"Analysis complete. Results saved to {output}")
    
    asyncio.run(run_analysis())

@cli.command()
@click.option('--analysis', '-a', required=True, help='Analysis file from analyze command')
@click.option('--focus', '-f', default='performance', help='Implementation focus')
def implement(analysis, focus):
    """Implement changes with Cursor AI based on analysis"""
    click.echo(f"Implementing {focus} improvements...")
    
    async def run_implementation():
        with open(analysis, 'r') as f:
            analysis_data = json.load(f)
        
        conductor = Workflowconductor()
        workflow_id = f"implementation_{focus}"
        context = await conductor.create_workflow(workflow_id)
        
        task = TaskDefinition(
            task_id="implement",
            name="Code Implementation",
            agent_role=AgentRole.IMPLEMENTER,
            inputs={
                "analysis": analysis_data,
                "focus": focus
            }
        )
        
        result = await conductor.execute_workflow(workflow_id, [task])
        click.echo("Implementation complete!")
    
    asyncio.run(run_implementation())

@cli.command()
@click.option('--stack', '-s', default='python_postgres_weaviate', help='Technology stack')
def refine(stack):
    """Refine technology stack with  Code"""
    click.echo(f"Refining {stack} stack...")
    
    async def run_refinement():
        conductor = Workflowconductor()
        workflow_id = f"refinement_{stack}"
        context = await conductor.create_workflow(workflow_id)
        
        task = TaskDefinition(
            task_id="refine",
            name="Stack Refinement",
            agent_role=AgentRole.REFINER,
            inputs={"technology_stack": stack}
        )
        
        result = await conductor.execute_workflow(workflow_id, [task])
        click.echo("Refinement complete!")
    
    asyncio.run(run_refinement())

@cli.command()
@click.option('--config', '-c', default='workflow.json', help='Workflow configuration file')
def cherry_aite(config):
    """Run full coordination workflow from config file"""
    click.echo(f"Running coordination from {config}...")
    
    async def run_coordination():
        with open(config, 'r') as f:
            workflow_config = json.load(f)
        
        conductor = Workflowconductor()
        workflow_id = workflow_config.get('workflow_id', 'custom_workflow')
        context = await conductor.create_workflow(workflow_id)
        
        # Create tasks from config
        tasks = []
        for task_config in workflow_config.get('tasks', []):
            task = TaskDefinition(
                task_id=task_config['id'],
                name=task_config['name'],
                agent_role=AgentRole[task_config['agent'].upper()],
                inputs=task_config.get('inputs', {}),
                dependencies=task_config.get('dependencies', []),
                priority=task_config.get('priority', 0)
            )
            tasks.append(task)
        
        result = await conductor.execute_workflow(workflow_id, tasks)
        click.echo("coordination complete!")
        click.echo(json.dumps(result.results, indent=2))
    
    asyncio.run(run_coordination())

if __name__ == '__main__':
    cli()
EOF
chmod +x conductor_cli.py

# Create example workflow configuration
print_status "Creating example workflow configuration..."
cat > configs/example_workflow.json << EOF
{
  "workflow_id": "full_stack_optimization",
  "description": "Complete codebase analysis, implementation, and refinement",
  "tasks": [
    {
      "id": "analyze_codebase",
      "name": "Analyze Codebase",
      "agent": "analyzer",
      "inputs": {
        "focus_areas": ["performance", "scalability", "maintainability"]
      },
      "priority": 1
    },
    {
      "id": "implement_optimizations",
      "name": "Implement Performance Optimizations",
      "agent": "implementer",
      "inputs": {
        "optimization_targets": ["database_queries", "api_endpoints", "caching"]
      },
      "dependencies": ["analyze_codebase"],
      "priority": 2
    },
    {
      "id": "refine_architecture",
      "name": "Refine System Architecture",
      "agent": "refiner",
      "inputs": {
        "technology_stack": "python_postgres_weaviate_airbyte",
        "ease_of_use_priority": "high"
      },
      "dependencies": ["implement_optimizations"],
      "priority": 3
    }
  ]
}
EOF

# Create systemd service for MCP server
print_status "Creating systemd service for MCP server..."
cat > /etc/systemd/system/conductor-mcp.service << EOF
[Unit]
Description=AI conductor MCP Server
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Install FastAPI and Uvicorn for MCP server
print_status "Installing MCP server dependencies..."
pip install fastapi uvicorn

# Create documentation
print_status "Creating documentation..."
cat > README.md << 'EOF'
# AI coordination System

This system coordinates between EigenCode, Cursor AI, and  Code to provide comprehensive code analysis, implementation, and refinement capabilities.

## Components

1. **EigenCode** - Holistic codebase analysis
2. **Cursor AI** - Performance-focused implementation
3. ** Code** - Technology stack refinement for ease of use

## Setup

1. Copy `configs/.env.template` to `configs/.env` and fill in your API keys
2. Ensure PostgreSQL is running and accessible
3. Configure Weaviate Cloud and Airbyte Cloud connections
4. Start the MCP server: `systemctl start conductor-mcp`

## Usage

### CLI Commands

```bash
# Analyze codebase
./conductor_cli.py analyze --codebase /path/to/code --output analysis.json

# Implement changes based on analysis
./conductor_cli.py implement --analysis analysis.json --focus performance

# Refine technology stack
./conductor_cli.py refine --stack python_postgres_weaviate

# Run full coordination workflow
./conductor_cli.py cherry_aite --config configs/example_workflow.json
```

### Python API

```python
from coordination.ai_conductor import Workflowconductor, TaskDefinition, AgentRole

# Create conductor
conductor = Workflowconductor()

# Define workflow
workflow_id = "my_workflow"
context = await conductor.create_workflow(workflow_id)

# Define tasks
tasks = [
    TaskDefinition(
        task_id="analyze",
        name="Analyze Codebase",
        agent_role=AgentRole.ANALYZER,
        inputs={"codebase_path": "/path/to/code"}
    ),
    # Add more tasks...
]

# Execute workflow
result = await conductor.execute_workflow(workflow_id, tasks)
```

## Configuration

Edit `configs/conductor_config.yaml` to customize:
- Workflow timeouts
- Parallel task limits
- Agent-specific settings
- Database and service connections

## Monitoring

- Logs are stored in `logs/conductor.log`
- PostgreSQL stores all coordination actions
- Weaviate Cloud stores context and results
- MCP server provides real-time task status

## Security

- All API keys should be stored as GitHub Secrets
- Use environment variables for sensitive configuration
- Enable SSL/TLS for all external connections
- Implement proper authentication for MCP server

## Troubleshooting

1. Check logs: `tail -f logs/conductor.log`
2. Verify MCP server: `systemctl status conductor-mcp`
3. Test database connection: `python3 -c "from coordination.ai_conductor import DatabaseLogger; DatabaseLogger()"`
4. Verify API keys are properly set in environment

EOF

print_status "Installation complete!"
print_warning "Note: EigenCode installation failed due to service unavailability (404 error)"
print_status "Please:"
print_status "1. Copy configs/.env.template to configs/.env and add your API keys"
print_status "2. Start the MCP server: systemctl start conductor-mcp"
print_status "3. Run './conductor_cli.py --help' to see available commands"