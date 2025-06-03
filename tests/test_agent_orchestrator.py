"""
"""
    """Test circuit breaker functionality"""
        """Test circuit breaker starts closed"""
        """Test circuit breaker opens after failure threshold"""
        """Test circuit breaker resets on success"""
        """Test circuit breaker recovers after timeout"""
    """Test workflow task functionality"""
        """Test creating a workflow task"""
            id="task1",
            agent_type=AgentType.PERSONAL,
            task_data={"query": "test"},
            dependencies=["task0"]
        )
        
        assert task.id == "task1"
        assert task.agent_type == AgentType.PERSONAL
        assert task.status == TaskStatus.PENDING
        assert task.dependencies == ["task0"]
        assert task.retry_count == 0
        assert task.max_retries == 3

class TestAgentOrchestrator:
    """Test agent orchestrator functionality"""
        """Test workflow creation"""
                "id": "task1",
                "agent_type": "personal",
                "data": {"query": "test"},
                "dependencies": []
            },
            {
                "id": "task2",
                "agent_type": "pay_ready",
                "data": {"listing": "test"},
                "dependencies": ["task1"]
            }
        ]
        
        workflow = await orchestrator.create_workflow("Test Workflow", tasks)
        
        assert workflow.name == "Test Workflow"
        assert len(workflow.tasks) == 2
        assert workflow.status == WorkflowStatus.PENDING
        assert "task1" in workflow.tasks
        assert "task2" in workflow.tasks
        assert workflow.tasks["task2"].dependencies == ["task1"]
    
    @pytest.mark.asyncio
    async def test_validate_dependencies_with_cycle(self, orchestrator):
        """Test that cyclic dependencies are detected"""
                "id": "task1",
                "agent_type": "personal",
                "data": {},
                "dependencies": ["task2"]
            },
            {
                "id": "task2",
                "agent_type": "personal",
                "data": {},
                "dependencies": ["task1"]
            }
        ]
        
        with pytest.raises(ValueError, match="cycles"):
            await orchestrator.create_workflow("Cyclic Workflow", tasks)
    
    @pytest.mark.asyncio
    async def test_build_execution_plan(self, orchestrator):
        """Test building parallel execution plan"""
            id="test",
            name="Test",
            tasks={
                "task1": WorkflowTask("task1", AgentType.PERSONAL, {}, []),
                "task2": WorkflowTask("task2", AgentType.PERSONAL, {}, []),
                "task3": WorkflowTask("task3", AgentType.PERSONAL, {}, ["task1", "task2"]),
                "task4": WorkflowTask("task4", AgentType.PERSONAL, {}, ["task3"])
            }
        )
        
        plan = orchestrator._build_execution_plan(workflow)
        
        # First batch should have parallel tasks
        assert len(plan[0]) == 2
        assert set(plan[0]) == {"task1", "task2"}
        
        # Second batch depends on first
        assert len(plan[1]) == 1
        assert plan[1][0] == "task3"
        
        # Third batch depends on second
        assert len(plan[2]) == 1
        assert plan[2][0] == "task4"
    
    @pytest.mark.asyncio
    async def test_execute_single_task_success(self, orchestrator):
        """Test successful task execution"""
        workflow = Workflow(id="test", name="Test", tasks={})
        task = WorkflowTask(
            id="task1",
            agent_type=AgentType.PERSONAL,
            task_data={"query": "test"}
        )
        
        # Mock agent
        with patch('agent.app.services.agent_orchestrator.get_specialized_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.process_task = AsyncMock(return_value={"result": "success"})
            mock_get_agent.return_value = mock_agent
            
            await orchestrator._execute_single_task(workflow, task)
            
            assert task.status == TaskStatus.COMPLETED
            assert task.result == {"result": "success"}
            assert task.started_at is not None
            assert task.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_execute_single_task_with_retry(self, orchestrator):
        """Test task execution with retry on failure"""
        workflow = Workflow(id="test", name="Test", tasks={})
        task = WorkflowTask(
            id="task1",
            agent_type=AgentType.PERSONAL,
            task_data={"query": "test"},
            max_retries=2
        )
        
        # Mock agent that fails once then succeeds
        with patch('agent.app.services.agent_orchestrator.get_specialized_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.process_task = AsyncMock(
                side_effect=[Exception("First failure"), {"result": "success"}]
            )
            mock_get_agent.return_value = mock_agent
            
            await orchestrator._execute_single_task(workflow, task)
            
            assert task.status == TaskStatus.COMPLETED
            assert task.retry_count == 1
            assert mock_agent.process_task.call_count == 2
    
    @pytest.mark.asyncio
    async def test_execute_single_task_circuit_breaker(self, orchestrator):
        """Test circuit breaker prevents execution"""
        workflow = Workflow(id="test", name="Test", tasks={})
        task = WorkflowTask(
            id="task1",
            agent_type=AgentType.PERSONAL,
            task_data={"type": "search", "query": "test"}
        )
        
        # Open circuit breaker
        breaker_key = f"{task.agent_type.value}:search"
        orchestrator.circuit_breakers[breaker_key] = CircuitBreaker()
        orchestrator.circuit_breakers[breaker_key].is_open = True
        
        await orchestrator._execute_single_task(workflow, task)
        
        assert task.status == TaskStatus.FAILED
        assert task.error == "Circuit breaker open"
    
    @pytest.mark.asyncio
    async def test_create_checkpoint(self, orchestrator):
        """Test checkpoint creation"""
            id="test",
            name="Test",
            tasks={
                "task1": WorkflowTask(
                    "task1",
                    AgentType.PERSONAL,
                    {},
                    status=TaskStatus.COMPLETED,
                    result={"data": "result"}
                )
            }
        )
        
        await orchestrator._create_checkpoint(workflow)
        
        assert len(workflow.checkpoints) == 1
        checkpoint = workflow.checkpoints[0]
        assert "timestamp" in checkpoint
        assert checkpoint["task_states"]["task1"]["status"] == TaskStatus.COMPLETED.value
        assert checkpoint["task_states"]["task1"]["result"] == {"data": "result"}
    
    @pytest.mark.asyncio
    async def test_workflow_execution_end_to_end(self, orchestrator):
        """Test complete workflow execution"""
                "id": "task1",
                "agent_type": "personal",
                "data": {"query": "test1"},
                "dependencies": []
            },
            {
                "id": "task2",
                "agent_type": "personal",
                "data": {"query": "test2"},
                "dependencies": ["task1"]
            }
        ]
        
        workflow = await orchestrator.create_workflow("Test Workflow", tasks)
        
        # Mock agents
        with patch('agent.app.services.agent_orchestrator.get_specialized_agent') as mock_get_agent:
            mock_agent = Mock()
            mock_agent.process_task = AsyncMock(
                side_effect=[
                    {"result": "result1"},
                    {"result": "result2"}
                ]
            )
            mock_get_agent.return_value = mock_agent
            
            # Execute workflow
            result = await orchestrator.execute_workflow(workflow.id)
            
            assert result["status"] == "completed"
            assert result["results"]["task1"] == {"result": "result1"}
            assert result["results"]["task2"] == {"result": "result2"}
            assert workflow.status == WorkflowStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_cancel_workflow(self, orchestrator):
        """Test workflow cancellation"""
            "Test",
            [{"id": "task1", "agent_type": "personal", "data": {}, "dependencies": []}]
        )
        workflow.status = WorkflowStatus.RUNNING
        
        await orchestrator.cancel_workflow(workflow.id)
        
        assert workflow.status == WorkflowStatus.CANCELLED
        assert workflow.tasks["task1"].status == TaskStatus.SKIPPED
    
    @pytest.mark.asyncio
    async def test_get_workflow_status(self, orchestrator):
        """Test getting workflow status"""
            "Test",
            [
                {"id": "task1", "agent_type": "personal", "data": {}, "dependencies": []},
                {"id": "task2", "agent_type": "personal", "data": {}, "dependencies": []}
            ]
        )
        
        workflow.tasks["task1"].status = TaskStatus.COMPLETED
        
        status = await orchestrator.get_workflow_status(workflow.id)
        
        assert status["workflow_id"] == workflow.id
        assert status["name"] == "Test"
        assert status["progress"] == 50.0  # 1 of 2 tasks completed
        assert status["tasks"]["task1"]["status"] == TaskStatus.COMPLETED.value
        assert status["tasks"]["task2"]["status"] == TaskStatus.PENDING.value

class TestWorkflowCreation:
    """Test workflow creation helpers"""
        """Test creating a comprehensive search workflow"""
                    id="test",
                    name="Comprehensive Search",
                    tasks={}
                )
            )
            mock_get.return_value = mock_orchestrator
            
            workflow = await create_comprehensive_search_workflow(
                user_id="user123",
                search_query="AI research",
                include_medical=True
            )
            
            assert workflow.id == "test"
            assert workflow.name == "Comprehensive Search"
            
            # Check that create_workflow was called with correct tasks
            call_args = mock_orchestrator.create_workflow.call_args
            tasks = call_args[0][1]  # Second positional argument
            
            # Should have personal search task
            assert any(t["id"] == "personal_search" for t in tasks)
            
            # Should have medical search task when include_medical=True
            assert any(t["id"] == "medical_search" for t in tasks)
            
            # Should have analysis task that depends on searches
            analysis_task = next(t for t in tasks if t["id"] == "analyze_results")
            assert "personal_search" in analysis_task["dependencies"]
            assert "medical_search" in analysis_task["dependencies"]

@pytest.mark.asyncio
async def test_singleton_orchestrator():
    """Test that orchestrator is a singleton"""
    """Test inter-agent message processing"""
                "type": "task_completed",
                "workflow_id": "test",
                "task_id": "task1",
                "result": {"shared_data": {"key": "value"}}
            }
            
            await orchestrator.message_queue.put(message)
            
            # Process one message
            await orchestrator._message_processor()
            
            # Check shared context was updated
            assert orchestrator.shared_context["key"] == "value"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])