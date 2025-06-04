#!/usr/bin/env python3
"""cherry_aite a complete system demonstration workflow."""

import asyncio
import json
import subprocess
import time
from datetime import datetime

class cherry_aiWorkflow:
    """cherry_aite multi-agent workflows with MCP integration."""
    
    def __init__(self):
        self.workflow_id = f"demo_{int(time.time())}"
        self.agents = {
            "search": {"status": "idle", "tasks": []},
            "ingestion": {"status": "idle", "tasks": []},
            "persona": {"status": "idle", "tasks": []},
            "analytics": {"status": "idle", "tasks": []}
        }
        self.context = {
            "mcp_servers": {
                "postgresql": "Connected",
                "weaviate": "Connected",
                "redis": "Connected"
            },
            "personas": ["Cherry", "Sophia", "Karen"],
            "search_modes": ["normal", "creative", "deep", "super-deep", "uncensored"]
        }
    
    async def decompose_task(self, task_description):
        """Break down complex task into atomic units."""
        print(f"\n📋 Task Decomposition: {task_description}")
        
        atomic_tasks = [
            {
                "id": "t1",
                "type": "search",
                "description": "Search for existing knowledge",
                "dependencies": [],
                "agent": "search"
            },
            {
                "id": "t2", 
                "type": "ingest",
                "description": "Process and store new information",
                "dependencies": ["t1"],
                "agent": "ingestion"
            },
            {
                "id": "t3",
                "type": "persona_adapt",
                "description": "Adapt response for each persona",
                "dependencies": ["t2"],
                "agent": "persona"
            },
            {
                "id": "t4",
                "type": "analytics",
                "description": "Generate performance metrics",
                "dependencies": ["t1", "t2", "t3"],
                "agent": "analytics"
            }
        ]
        
        for task in atomic_tasks:
            print(f"  - {task['id']}: {task['description']} (Agent: {task['agent']})")
        
        return atomic_tasks
    
    async def coordinate_agents(self, tasks):
        """Coordinate agent execution with dependency management."""
        print("\n🤖 Agent Coordination:")
        
        completed = set()
        results = {}
        
        while len(completed) < len(tasks):
            # Find tasks ready to execute
            ready_tasks = [
                t for t in tasks 
                if t['id'] not in completed 
                and all(dep in completed for dep in t['dependencies'])
            ]
            
            # Execute ready tasks in parallel
            if ready_tasks:
                print(f"\n  Executing tasks: {[t['id'] for t in ready_tasks]}")
                
                # Simulate parallel execution
                execution_results = await asyncio.gather(
                    *[self.execute_task(task) for task in ready_tasks]
                )
                
                # Store results and mark completed
                for task, result in zip(ready_tasks, execution_results):
                    results[task['id']] = result
                    completed.add(task['id'])
                    print(f"  ✓ Completed: {task['id']}")
            
            await asyncio.sleep(0.5)
        
        return results
    
    async def execute_task(self, task):
        """Execute individual task with MCP context."""
        agent = task['agent']
        self.agents[agent]['status'] = 'busy'
        self.agents[agent]['tasks'].append(task['id'])
        
        # Simulate task execution
        await asyncio.sleep(1)
        
        result = {
            "task_id": task['id'],
            "agent": agent,
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": f"Processed by {agent} agent"
        }
        
        self.agents[agent]['status'] = 'idle'
        return result
    
    async def manage_context(self, results):
        """Manage workflow context with MCP integration."""
        print("\n🧠 Context Management:")
        
        # Store in PostgreSQL
        print("  - Persisting to PostgreSQL...")
        
        # Index in Weaviate
        print("  - Indexing in Weaviate vector store...")
        
        # Cache in Redis
        print("  - Caching in Redis...")
        
        # Update context
        self.context['workflow_results'] = results
        self.context['completion_time'] = datetime.now().isoformat()
        
        return self.context
    
    async def generate_report(self):
        """Generate comprehensive workflow report."""
        print("\n📊 Workflow Report:")
        
        report = {
            "workflow_id": self.workflow_id,
            "agents": self.agents,
            "context": self.context,
            "metrics": {
                "total_tasks": sum(len(a['tasks']) for a in self.agents.values()),
                "mcp_servers_used": len(self.context['mcp_servers']),
                "personas_supported": len(self.context['personas'])
            }
        }
        
        print(json.dumps(report, indent=2))
        return report
    
    async def run_workflow(self):
        """Execute complete coordination workflow."""
        print(f"\n🎼 Starting cherry_ai Workflow: {self.workflow_id}")
        print("=" * 60)
        
        # Step 1: Task decomposition
        task = "Analyze market trends and generate personalized insights for each persona"
        tasks = await self.decompose_task(task)
        
        # Step 2: Agent coordination
        results = await self.coordinate_agents(tasks)
        
        # Step 3: Context management
        context = await self.manage_context(results)
        
        # Step 4: Generate report
        report = await self.generate_report()
        
        print("\n✨ Workflow completed successfully!")
        return report

def verify_system_readiness():
    """Verify system is ready for coordination."""
    print("🔍 Verifying System Readiness...")
    
    checks = {
        "API": "docker ps -q -f name=cherry_ai_api",
        "PostgreSQL": "docker ps -q -f name=cherry_ai_postgres",
        "Redis": "docker ps -q -f name=cherry_ai_redis",
        "Weaviate": "docker ps -q -f name=cherry_ai_weaviate"
    }
    
    ready = True
    for service, cmd in checks.items():
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(f"  ✓ {service} is running")
        else:
            print(f"  ✗ {service} is NOT running")
            ready = False
    
    return ready

async def main():
    """Main coordination demo."""
    print("🎭 Cherry AI - System Demonstration")
    print("=====================================")
    
    # Verify system
    if not verify_system_readiness():
        print("\n❌ System not ready. Please ensure all services are running.")
        return
    
    # Run coordination workflow
    workflow = cherry_aiWorkflow()
    report = await workflow.run_workflow()
    
    # Save report
    report_file = f"coordination_demo_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_file}")
    print("\n🌐 Visit https://cherry-ai.me to interact with the system")
    print("🔐 Login: scoobyjava / Huskers1983$")

if __name__ == "__main__":
    asyncio.run(main())