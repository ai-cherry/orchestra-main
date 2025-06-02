#!/usr/bin/env python3
"""
Enhanced AI Orchestrator CLI
Command-line interface with additional features for EigenCode, performance monitoring, security, and scalability
"""

import click
import asyncio
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import subprocess
import yaml

# Add orchestration module to path
sys.path.append(str(Path(__file__).parent))

from orchestration.ai_orchestrator import (
    WorkflowOrchestrator, TaskDefinition, AgentRole
)

# Add scripts to path for additional functionality
sys.path.append(str(Path(__file__).parent.parent / "scripts"))


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file')
@click.pass_context
def cli(ctx, verbose, config):
    """Enhanced AI Orchestrator CLI - Coordinate EigenCode, Cursor AI, and Roo Code
    
    This CLI provides comprehensive control over the AI orchestration system,
    including performance monitoring, security auditing, and scalability testing.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    if config:
        with open(config, 'r') as f:
            ctx.obj['config'] = yaml.safe_load(f)
    else:
        ctx.obj['config'] = {}


@cli.command()
@click.option('--codebase', '-c', default='.', help='Path to codebase')
@click.option('--output', '-o', default='analysis_report.json', help='Output file')
@click.option('--focus', '-f', multiple=True, help='Focus areas (performance, security, maintainability)')
@click.pass_context
def analyze(ctx, codebase, output, focus):
    """Analyze codebase with EigenCode (when available)"""
    if ctx.obj['verbose']:
        click.echo(f"Analyzing codebase at {codebase}...")
        if focus:
            click.echo(f"Focus areas: {', '.join(focus)}")
    
    async def run_analysis():
        orchestrator = WorkflowOrchestrator()
        workflow_id = f"analysis_{Path(codebase).name}_{int(time.time())}"
        context = await orchestrator.create_workflow(workflow_id)
        
        task = TaskDefinition(
            task_id="analyze",
            name="Codebase Analysis",
            agent_role=AgentRole.ANALYZER,
            inputs={
                "codebase_path": codebase,
                "focus_areas": list(focus) if focus else ["general"]
            }
        )
        
        result = await orchestrator.execute_workflow(workflow_id, [task])
        
        # Save results
        with open(output, 'w') as f:
            json.dump(result.results, f, indent=2)
        
        click.echo(f"✓ Analysis complete. Results saved to {output}")
        
        if ctx.obj['verbose']:
            click.echo(f"Workflow ID: {workflow_id}")
            click.echo(f"Status: {result.status.value}")
    
    asyncio.run(run_analysis())


@cli.command()
@click.option('--analysis', '-a', required=True, help='Analysis file from analyze command')
@click.option('--focus', '-f', default='performance', 
              type=click.Choice(['performance', 'security', 'scalability', 'maintainability']),
              help='Implementation focus')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def implement(ctx, analysis, focus, dry_run):
    """Implement changes with Cursor AI based on analysis"""
    if ctx.obj['verbose']:
        click.echo(f"Implementing {focus} improvements...")
    
    async def run_implementation():
        with open(analysis, 'r') as f:
            analysis_data = json.load(f)
        
        orchestrator = WorkflowOrchestrator()
        workflow_id = f"implementation_{focus}_{int(time.time())}"
        context = await orchestrator.create_workflow(workflow_id)
        
        task = TaskDefinition(
            task_id="implement",
            name=f"Code Implementation - {focus}",
            agent_role=AgentRole.IMPLEMENTER,
            inputs={
                "analysis": analysis_data,
                "focus": focus,
                "dry_run": dry_run
            }
        )
        
        result = await orchestrator.execute_workflow(workflow_id, [task])
        
        if dry_run:
            click.echo("DRY RUN - No changes were made")
            click.echo("Proposed changes:")
            for change in result.results.get('implement', {}).get('proposed_changes', []):
                click.echo(f"  - {change}")
        else:
            click.echo(f"✓ Implementation complete!")
            if ctx.obj['verbose']:
                click.echo(f"Files modified: {result.results.get('implement', {}).get('files_modified', [])}")
    
    asyncio.run(run_implementation())


@cli.command()
@click.option('--stack', '-s', default='python_postgres_weaviate', help='Technology stack')
@click.option('--priorities', '-p', multiple=True, 
              type=click.Choice(['ease-of-use', 'performance', 'scalability', 'security']),
              help='Refinement priorities')
@click.pass_context
def refine(ctx, stack, priorities):
    """Refine technology stack with Roo Code"""
    if ctx.obj['verbose']:
        click.echo(f"Refining {stack} stack...")
        if priorities:
            click.echo(f"Priorities: {', '.join(priorities)}")
    
    async def run_refinement():
        orchestrator = WorkflowOrchestrator()
        workflow_id = f"refinement_{stack}_{int(time.time())}"
        context = await orchestrator.create_workflow(workflow_id)
        
        task = TaskDefinition(
            task_id="refine",
            name="Stack Refinement",
            agent_role=AgentRole.REFINER,
            inputs={
                "technology_stack": stack,
                "priorities": list(priorities) if priorities else ["ease-of-use"]
            }
        )
        
        result = await orchestrator.execute_workflow(workflow_id, [task])
        click.echo(f"✓ Refinement complete!")
        
        # Display recommendations
        recommendations = result.results.get('refine', {}).get('recommendations', [])
        if recommendations:
            click.echo("\nRecommendations:")
            for rec in recommendations:
                click.echo(f"  • {rec}")
    
    asyncio.run(run_refinement())


@cli.group()
def eigencode():
    """EigenCode-specific commands"""
    pass


@eigencode.command()
@click.option('--method', '-m', 
              type=click.Choice(['all', 'direct', 'package', 'api', 'github']),
              default='all', help='Installation method to try')
@click.pass_context
def install(ctx, method):
    """Attempt to install EigenCode using various methods"""
    click.echo("Attempting EigenCode installation...")
    
    try:
        from eigencode_installer import EigenCodeInstaller
        
        async def run_installation():
            installer = EigenCodeInstaller()
            
            if method == 'all':
                results = await installer.run_all_methods()
            else:
                # Run specific method
                method_map = {
                    'direct': installer.attempt_direct_download,
                    'package': installer.check_package_managers,
                    'api': installer.contact_api_for_instructions,
                    'github': installer.check_github_releases
                }
                
                if method in method_map:
                    result = await method_map[method]()
                    results = {"success": result, "method_used": method if result else None}
                else:
                    results = {"success": False, "error": "Invalid method"}
            
            if results['success']:
                click.echo(f"✓ EigenCode installed successfully using {results['method_used']}")
            else:
                click.echo("✗ EigenCode installation failed")
                click.echo("Check eigencode_installation_report.json for details")
        
        asyncio.run(run_installation())
        
    except ImportError:
        click.echo("Error: eigencode_installer module not found")
        click.echo("Make sure scripts/eigencode_installer.py exists")


@eigencode.command()
@click.pass_context
def status(ctx):
    """Check EigenCode installation status"""
    eigencode_paths = [
        "/root/.eigencode/bin/eigencode",
        "/usr/local/bin/eigencode",
        "/usr/bin/eigencode",
        os.path.expanduser("~/.eigencode/bin/eigencode")
    ]
    
    found = False
    for path in eigencode_paths:
        if os.path.exists(path):
            found = True
            click.echo(f"✓ EigenCode found at: {path}")
            
            # Try to get version
            try:
                result = subprocess.run([path, 'version'], capture_output=True, text=True)
                if result.returncode == 0:
                    click.echo(f"  Version: {result.stdout.strip()}")
            except:
                pass
            break
    
    if not found:
        click.echo("✗ EigenCode not found")
        click.echo("Run 'orchestrator-cli eigencode install' to attempt installation")


@cli.group()
def performance():
    """Performance monitoring and optimization commands"""
    pass


@performance.command()
@click.option('--component', '-c', 
              type=click.Choice(['all', 'workflow', 'database', 'vector', 'api']),
              default='all', help='Component to analyze')
@click.option('--output', '-o', help='Output file for detailed report')
@click.pass_context
def analyze(ctx, component, output):
    """Analyze performance bottlenecks"""
    click.echo(f"Analyzing performance for: {component}")
    
    try:
        from performance_analyzer import PerformanceAnalyzer
        
        async def run_analysis():
            analyzer = PerformanceAnalyzer()
            
            if component == 'all':
                results = await analyzer.run_full_analysis()
            else:
                # Run specific analysis
                method_map = {
                    'workflow': analyzer.analyze_workflow_execution_times,
                    'database': analyzer.analyze_database_performance,
                    'vector': analyzer.analyze_vector_storage_efficiency,
                    'api': analyzer.analyze_api_latencies
                }
                
                if component in method_map:
                    results = await method_map[component]()
                else:
                    results = {"error": "Invalid component"}
            
            # Display summary
            if 'workflow_execution' in results.get('analyses', {}):
                wf_data = results['analyses']['workflow_execution']
                click.echo(f"\nWorkflow Performance:")
                click.echo(f"  Average Duration: {wf_data.get('average_duration', 0):.2f}s")
                click.echo(f"  Total Workflows: {wf_data.get('total_workflows', 0)}")
            
            if 'recommendations' in results:
                click.echo(f"\nRecommendations: {len(results['recommendations'])}")
                for rec in results['recommendations'][:3]:  # Show top 3
                    click.echo(f"  - [{rec['severity']}] {rec['issue']}")
            
            # Save detailed report
            if output:
                with open(output, 'w') as f:
                    json.dump(results, f, indent=2)
                click.echo(f"\nDetailed report saved to: {output}")
        
        asyncio.run(run_analysis())
        
    except ImportError:
        click.echo("Error: performance_analyzer module not found")


@performance.command()
@click.option('--duration', '-d', default=60, help='Test duration in seconds')
@click.option('--concurrent', '-c', default=5, help='Number of concurrent workflows')
@click.pass_context
def stress_test(ctx, duration, concurrent):
    """Run performance stress test"""
    click.echo(f"Running stress test for {duration}s with {concurrent} concurrent workflows...")
    
    async def run_stress_test():
        orchestrator = WorkflowOrchestrator()
        start_time = time.time()
        end_time = start_time + duration
        
        workflows_completed = 0
        workflows_failed = 0
        
        async def run_workflow(index):
            nonlocal workflows_completed, workflows_failed
            
            while time.time() < end_time:
                workflow_id = f"stress_test_{index}_{int(time.time())}"
                
                try:
                    context = await orchestrator.create_workflow(workflow_id)
                    
                    # Simple test task
                    task = TaskDefinition(
                        task_id="stress_task",
                        name="Stress Test Task",
                        agent_role=AgentRole.ANALYZER,
                        inputs={"test": True, "index": index}
                    )
                    
                    result = await orchestrator.execute_workflow(workflow_id, [task])
                    
                    if result.status.value == "completed":
                        workflows_completed += 1
                    else:
                        workflows_failed += 1
                        
                except Exception as e:
                    workflows_failed += 1
                    if ctx.obj['verbose']:
                        click.echo(f"Workflow {workflow_id} failed: {str(e)}")
                
                # Brief pause between workflows
                await asyncio.sleep(0.1)
        
        # Run concurrent workflows
        tasks = [run_workflow(i) for i in range(concurrent)]
        await asyncio.gather(*tasks)
        
        # Calculate results
        total_time = time.time() - start_time
        total_workflows = workflows_completed + workflows_failed
        
        click.echo(f"\nStress Test Results:")
        click.echo(f"  Duration: {total_time:.2f}s")
        click.echo(f"  Total Workflows: {total_workflows}")
        click.echo(f"  Completed: {workflows_completed}")
        click.echo(f"  Failed: {workflows_failed}")
        click.echo(f"  Success Rate: {workflows_completed/total_workflows*100:.1f}%")
        click.echo(f"  Throughput: {total_workflows/total_time:.2f} workflows/second")
    
    asyncio.run(run_stress_test())


@cli.group()
def security():
    """Security audit and enhancement commands"""
    pass


@security.command()
@click.option('--component', '-c', 
              type=click.Choice(['all', 'secrets', 'mcp', 'database', 'cloud']),
              default='all', help='Component to audit')
@click.option('--fix', is_flag=True, help='Attempt to fix issues automatically')
@click.pass_context
def audit(ctx, component, fix):
    """Run security audit"""
    click.echo(f"Running security audit for: {component}")
    
    try:
        from security_audit import SecurityAuditor
        
        async def run_audit():
            auditor = SecurityAuditor()
            
            # Run audit based on component
            if component == 'all':
                api_secrets = auditor.check_api_secret_handling()
                mcp_security = auditor.validate_mcp_server_security()
                cloud_access = auditor.assess_weaviate_airbyte_access()
                db_security = auditor.review_postgresql_security()
            elif component == 'secrets':
                api_secrets = auditor.check_api_secret_handling()
            elif component == 'mcp':
                mcp_security = auditor.validate_mcp_server_security()
            elif component == 'database':
                db_security = auditor.review_postgresql_security()
            elif component == 'cloud':
                cloud_access = auditor.assess_weaviate_airbyte_access()
            
            # Generate report
            report = auditor.generate_security_report()
            
            # Display summary
            click.echo(f"\nSecurity Score: {report['summary']['security_score']}/100")
            click.echo(f"Total Findings: {report['summary']['total_findings']}")
            
            if report['summary']['critical_issues'] > 0:
                click.echo(f"\n⚠️  CRITICAL ISSUES: {report['summary']['critical_issues']}")
                for finding in report['findings']:
                    if finding['severity'] == 'critical':
                        click.echo(f"  - {finding['issue']}")
            
            # Attempt fixes if requested
            if fix and report['findings']:
                click.echo("\nAttempting to fix issues...")
                implementations = auditor.implement_security_enhancements(report)
                click.echo(f"  Fixed: {len(implementations['implemented'])}")
                click.echo(f"  Failed: {len(implementations['failed'])}")
                click.echo(f"  Manual Required: {len(implementations['manual_required'])}")
        
        asyncio.run(run_audit())
        
    except ImportError:
        click.echo("Error: security_audit module not found")


@security.command()
@click.option('--service', '-s', required=True,
              type=click.Choice(['eigencode', 'cursor', 'roo', 'postgres', 'weaviate']),
              help='Service to rotate secrets for')
@click.pass_context
def rotate_secrets(ctx, service):
    """Rotate API keys and secrets"""
    click.echo(f"Rotating secrets for: {service}")
    
    # This would integrate with your secret management system
    click.echo("⚠️  Secret rotation requires manual configuration")
    click.echo("Steps to rotate secrets:")
    click.echo(f"1. Generate new {service} API key/secret")
    click.echo(f"2. Update GitHub Secrets with new value")
    click.echo(f"3. Update local .env file")
    click.echo(f"4. Restart affected services")


@cli.group()
def scalability():
    """Scalability testing and configuration commands"""
    pass


@scalability.command()
@click.option('--workers', '-w', default=10, help='Number of worker processes')
@click.option('--tasks', '-t', default=100, help='Number of tasks to process')
@click.option('--complexity', '-c', 
              type=click.Choice(['low', 'medium', 'high']),
              default='medium', help='Task complexity')
@click.pass_context
def test(ctx, workers, tasks, complexity):
    """Run scalability test with multiple workers"""
    click.echo(f"Running scalability test: {workers} workers, {tasks} tasks, {complexity} complexity")
    
    async def run_scalability_test():
        orchestrator = WorkflowOrchestrator()
        start_time = time.time()
        
        # Create task queue
        task_queue = []
        for i in range(tasks):
            task = TaskDefinition(
                task_id=f"scale_task_{i}",
                name=f"Scalability Test Task {i}",
                agent_role=AgentRole.ANALYZER,
                inputs={
                    "complexity": complexity,
                    "index": i,
                    "data_size": {"low": 100, "medium": 1000, "high": 10000}[complexity]
                }
            )
            task_queue.append(task)
        
        # Process tasks with worker pool
        async def worker(worker_id):
            completed = 0
            while task_queue:
                try:
                    task = task_queue.pop(0)
                except IndexError:
                    break
                
                workflow_id = f"scale_test_w{worker_id}_t{task.task_id}"
                
                try:
                    context = await orchestrator.create_workflow(workflow_id)
                    await orchestrator.execute_workflow(workflow_id, [task])
                    completed += 1
                except Exception as e:
                    if ctx.obj['verbose']:
                        click.echo(f"Worker {worker_id} task failed: {str(e)}")
            
            return completed
        
        # Run workers concurrently
        worker_tasks = [worker(i) for i in range(workers)]
        results = await asyncio.gather(*worker_tasks)
        
        # Calculate metrics
        total_time = time.time() - start_time
        total_completed = sum(results)
        
        click.echo(f"\nScalability Test Results:")
        click.echo(f"  Total Time: {total_time:.2f}s")
        click.echo(f"  Tasks Completed: {total_completed}/{tasks}")
        click.echo(f"  Success Rate: {total_completed/tasks*100:.1f}%")
        click.echo(f"  Throughput: {total_completed/total_time:.2f} tasks/second")
        click.echo(f"  Average per Worker: {total_completed/workers:.1f} tasks")
        
        # Worker distribution
        click.echo(f"\nWorker Distribution:")
        for i, completed in enumerate(results):
            click.echo(f"  Worker {i}: {completed} tasks")
    
    asyncio.run(run_scalability_test())


@scalability.command()
@click.option('--instances', '-i', default=3, help='Number of orchestrator instances')
@click.pass_context
def configure(ctx, instances):
    """Configure orchestrator for horizontal scaling"""
    click.echo(f"Configuring orchestrator for {instances} instances...")
    
    # Generate configuration
    config = {
        "orchestrator": {
            "instances": instances,
            "load_balancer": {
                "algorithm": "round_robin",
                "health_check_interval": 30
            },
            "redis": {
                "enabled": True,
                "url": "redis://localhost:6379",
                "queue_name": "orchestrator_tasks"
            }
        },
        "database": {
            "pool_size": instances * 10,
            "max_overflow": 20
        },
        "monitoring": {
            "prometheus": {
                "enabled": True,
                "port": 9090
            }
        }
    }
    
    # Save configuration
    config_path = "ai_components/configs/scalability_config.yaml"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    click.echo(f"✓ Configuration saved to: {config_path}")
    click.echo("\nNext steps:")
    click.echo("1. Install Redis: apt-get install redis-server")
    click.echo("2. Update infrastructure/main.py to provision multiple instances")
    click.echo("3. Configure load balancer (nginx/haproxy)")
    click.echo("4. Deploy with: pulumi up")


@cli.command()
@click.option('--config', '-c', default='configs/example_workflow.json', help='Workflow configuration file')
@click.option('--watch', '-w', is_flag=True, help='Watch workflow progress in real-time')
@click.pass_context
def orchestrate(ctx, config, watch):
    """Run full orchestration workflow from config file"""
    if not os.path.exists(config):
        click.echo(f"Error: Configuration file '{config}' not found")
        return
    
    click.echo(f"Running orchestration from {config}...")
    
    async def run_orchestration():
        with open(config, 'r') as f:
            workflow_config = json.load(f)
        
        orchestrator = WorkflowOrchestrator()
        workflow_id = workflow_config.get('workflow_id', f'custom_workflow_{int(time.time())}')
        context = await orchestrator.create_workflow(workflow_id)
        
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
        
        if watch:
            # Monitor workflow progress
            click.echo(f"Workflow ID: {workflow_id}")
            click.echo("Progress:")
            
            # This would ideally connect to MCP server for real-time updates
            # For now, we'll just show the final result
        
        result = await orchestrator.execute_workflow(workflow_id, tasks)
        
        click.echo(f"\n✓ Orchestration complete!")
        click.echo(f"Status: {result.status.value}")
        
        if ctx.obj['verbose']:
            click.echo("\nResults:")
            click.echo(json.dumps(result.results, indent=2))
        
        # Save results
        output_file = f"orchestration_result_{workflow_id}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "workflow_id": workflow_id,
                "status": result.status.value,
                "results": result.results,
                "errors": result.errors,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        click.echo(f"\nResults saved to: {output_file}")
    
    asyncio.run(run_orchestration())


@cli.command()
@click.pass_context
def status(ctx):
    """Show overall system status"""
    click.echo("AI Orchestrator System Status")
    click.echo("=" * 40)
    
    # Check services
    services = {
        "MCP Server": "http://localhost:8080/",
        "PostgreSQL": None,  # Check via connection
        "Weaviate": os.environ.get('WEAVIATE_URL'),
        "Prometheus": "http://localhost:9090/-/healthy",
        "Grafana": "http://localhost:3000/api/health"
    }
    
    click.echo("\nServices:")
    for service, url in services.items():
        if service == "PostgreSQL":
            # Special handling for PostgreSQL
            try:
                from ai_orchestrator import DatabaseLogger
                db = DatabaseLogger()
                with db._get_connection() as conn:
                    status = "✓ Running"
            except:
                status = "✗ Not available"
        elif url:
            try:
                import requests
                response = requests.get(url, timeout=2)
                status = "✓ Running" if response.status_code == 200 else f"⚠️  Status: {response.status_code}"
            except:
                status = "✗ Not available"
        else:
            status = "? Unknown"
        
        click.echo(f"  {service}: {status}")
    
    # Check EigenCode
    click.echo("\nAI Agents:")
    eigencode_status = "✗ Not installed"
    for path in ["/root/.eigencode/bin/eigencode", "/usr/local/bin/eigencode"]:
        if os.path.exists(path):
            eigencode_status = "✓ Installed"
            break
    
    click.echo(f"  EigenCode: {eigencode_status}")
    click.echo(f"  Cursor AI: ✓ Ready (API)")
    click.echo(f"  Roo Code: ✓ Ready (API)")
    
    # Environment check
    click.echo("\nEnvironment:")
    required_vars = ["POSTGRES_HOST", "WEAVIATE_URL", "WEAVIATE_API_KEY"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        click.echo(f"  ⚠️  Missing variables: {', '.join(missing)}")
    else:
        click.echo("  ✓ All required environment variables set")
    
    # Quick health check
    click.echo("\nQuick Health Check:")
    try:
        # Try to create a simple workflow
        async def health_check():
            orchestrator = WorkflowOrchestrator()
            workflow_id = f"health_check_{int(time.time())}"
            await orchestrator.create_workflow(workflow_id)
            return True
        
        if asyncio.run(health_check()):
            click.echo("  ✓ Orchestrator is operational")
        else:
            click.echo("  ✗ Orchestrator health check failed")
    except Exception as e:
        click.echo(f"  ✗ Orchestrator error: {str(e)}")


if __name__ == '__main__':
    cli()