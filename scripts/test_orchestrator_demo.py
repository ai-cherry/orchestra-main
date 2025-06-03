# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Test the AI orchestrator with real workflow"""
    print("=== AI Orchestrator Demo ===\n")
    
    try:

    
        pass
        # Import orchestrator components
        from ai_components.orchestration.ai_orchestrator import (
            WorkflowOrchestrator, TaskDefinition, AgentRole
        )
        from datetime import datetime
        
        # Create orchestrator
        print("1. Initializing Orchestrator...")
        orchestrator = WorkflowOrchestrator()
        print("✓ Orchestrator initialized\n")
        
        # Create workflow
        print("2. Creating Workflow...")
        workflow_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        context = await orchestrator.create_workflow(workflow_id)
        print(f"✓ Workflow created: {workflow_id}\n")
        
        # Define demo tasks
        print("3. Defining Tasks...")
        tasks = [
            TaskDefinition(
                task_id="analyze_project",
                name="Analyze Orchestra Project",
                agent_role=AgentRole.ANALYZER,
                inputs={"codebase_path": "/root/orchestra-main"},
                priority=1,
                timeout=60
            ),
            TaskDefinition(
                task_id="optimize_performance",
                name="Implement Performance Optimizations",
                agent_role=AgentRole.IMPLEMENTER,
                inputs={"changes": "performance_optimizations"},
                dependencies=["analyze_project"],
                priority=2,
                timeout=60
            ),
            TaskDefinition(
                task_id="refine_architecture",
                name="Refine Technology Stack",
                agent_role=AgentRole.REFINER,
                inputs={"technology_stack": "python_postgres_weaviate"},
                dependencies=["optimize_performance"],
                priority=3,
                timeout=60
            )
        ]
        print(f"✓ Defined {len(tasks)} tasks\n")
        
        # Execute workflow
        print("4. Executing Workflow...")
        print("=" * 50)
        
        try:

        
            pass
            result = await orchestrator.execute_workflow(workflow_id, tasks)
            
            print("\n5. Workflow Results:")
            print("=" * 50)
            
            # Display results for each task
            for task_id, task_result in result.results.items():
                print(f"\n📋 Task: {task_id}")
                print("-" * 40)
                
                if task_id == "analyze_project":
                    analysis = task_result.get("analysis", {})
                    print(f"Structure: {analysis.get('structure', 'N/A')}")
                    print(f"Dependencies Found: {len(analysis.get('dependencies', []))}")
                    if analysis.get('dependencies'):
                        print("  Top Dependencies:")
                        for dep in analysis.get('dependencies', [])[:5]:
                            print(f"    - {dep}")
                    print(f"Issues: {', '.join(analysis.get('issues', ['None']))}")
                    metrics = analysis.get('performance_metrics', {})
                    print(f"Complexity: {metrics.get('complexity', 'N/A')}")
                    print(f"Maintainability: {metrics.get('maintainability', 'N/A')}")
                
                elif task_id == "optimize_performance":
                    impl = task_result.get("implementation", {})
                    print(f"Files Modified: {', '.join(impl.get('files_modified', []))}")
                    print(f"Changes Applied: {impl.get('changes_applied', False)}")
                    print(f"Performance Improvements: {impl.get('performance_improvements', 'N/A')}")
                    if impl.get('ai_service'):
                        print(f"AI Service Used: {impl.get('ai_service')}")
                
                elif task_id == "refine_architecture":
                    refinement = task_result.get("refinement", {})
                    print(f"Ease of Use Score: {refinement.get('ease_of_use_score', 0)}/10")
                    print("Optimizations:")
                    for opt in refinement.get('optimizations', [])[:3]:
                        print(f"  - {opt}")
                    print("Recommendations:")
                    for rec in refinement.get('recommendations', [])[:3]:
                        print(f"  - {rec}")
                    stack = refinement.get('stack_analysis', {})
                    if stack:
                        print(f"Stack Complexity: {stack.get('complexity', 'N/A')}")
                        print(f"Integration Quality: {stack.get('integration_quality', 'N/A')}")
            
            # Summary
            print("\n" + "=" * 50)
            print(f"✅ Workflow Status: {context.status.value}")
            print(f"✅ Tasks Completed: {len(result.results)}/{len(tasks)}")
            
            if context.errors:
                print(f"⚠️  Errors: {len(context.errors)}")
                for error in context.errors:
                    print(f"   - {error}")
            
        except Exception:

            
            pass
            print(f"\n❌ Workflow execution failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Cleanup
        if hasattr(orchestrator, 'weaviate_manager'):
            orchestrator.weaviate_manager.close()
        
    except Exception:

        
        pass
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

def main():
    """Main entry point"""
    print("\n🚀 Starting AI Orchestrator Demo...\n")
    
    # Check environment
    api_keys = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'DATABASE_URL']
    missing = [k for k in api_keys if not os.environ.get(k)]
    
    if missing:
        print("⚠️  Warning: Some API keys are missing:")
        for key in missing:
            print(f"   - {key}")
        print("\nThe demo will run with limited functionality.\n")
    
    # Run async demo
    return asyncio.run(test_orchestrator())

if __name__ == "__main__":
    sys.exit(main())