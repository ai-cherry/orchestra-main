#!/usr/bin/env python3
"""
Test suite for AI Orchestrator components
Tests workflow execution, agent coordination, and context management
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from orchestration.ai_orchestrator import (
    WorkflowOrchestrator,
    TaskDefinition,
    AgentRole,
    TaskStatus,
    WorkflowContext,
    AgentCoordinator,
    DatabaseLogger,
    WeaviateManager,
    MCPContextManager
)


class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator functionality"""
    
    @pytest.fixture
    def mock_db_logger(self):
        """Mock database logger"""
        with patch('orchestration.ai_orchestrator.DatabaseLogger') as mock:
            logger = Mock()
            logger.log_action = Mock()
            mock.return_value = logger
            yield logger
    
    @pytest.fixture
    def mock_weaviate_manager(self):
        """Mock Weaviate manager"""
        with patch('orchestration.ai_orchestrator.WeaviateManager') as mock:
            manager = Mock()
            manager.store_context = Mock()
            manager.retrieve_context = Mock(return_value=[])
            mock.return_value = manager
            yield manager
    
    @pytest.fixture
    def orchestrator(self, mock_db_logger, mock_weaviate_manager):
        """Create orchestrator with mocked dependencies"""
        with patch('orchestration.ai_orchestrator.DatabaseLogger', return_value=mock_db_logger):
            with patch('orchestration.ai_orchestrator.WeaviateManager', return_value=mock_weaviate_manager):
                return WorkflowOrchestrator()
    
    @pytest.mark.asyncio
    async def test_create_workflow(self, orchestrator):
        """Test workflow creation"""
        workflow_id = "test_workflow_001"
        context = await orchestrator.create_workflow(workflow_id)
        
        assert context.workflow_id == workflow_id
        assert context.status == TaskStatus.PENDING
        assert workflow_id in orchestrator.workflows
    
    @pytest.mark.asyncio
    async def test_simple_task_execution(self, orchestrator):
        """Test execution of a simple task"""
        workflow_id = "test_workflow_002"
        context = await orchestrator.create_workflow(workflow_id)
        
        task = TaskDefinition(
            task_id="test_task",
            name="Test Analysis",
            agent_role=AgentRole.ANALYZER,
            inputs={"test": True}
        )
        
        with patch.object(orchestrator.agent_coordinator, 'execute_task', 
                         return_value={"result": "success"}):
            result = await orchestrator.execute_workflow(workflow_id, [task])
        
        assert result.status == TaskStatus.COMPLETED
        assert "test_task" in result.results
        assert result.results["test_task"]["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_task_dependencies(self, orchestrator):
        """Test task execution with dependencies"""
        workflow_id = "test_workflow_003"
        context = await orchestrator.create_workflow(workflow_id)
        
        tasks = [
            TaskDefinition(
                task_id="task1",
                name="First Task",
                agent_role=AgentRole.ANALYZER,
                inputs={"order": 1}
            ),
            TaskDefinition(
                task_id="task2",
                name="Second Task",
                agent_role=AgentRole.IMPLEMENTER,
                inputs={"order": 2},
                dependencies=["task1"]
            ),
            TaskDefinition(
                task_id="task3",
                name="Third Task",
                agent_role=AgentRole.REFINER,
                inputs={"order": 3},
                dependencies=["task1", "task2"]
            )
        ]
        
        execution_order = []
        
        async def mock_execute_task(task, context):
            execution_order.append(task.task_id)
            return {"order": task.inputs["order"]}
        
        with patch.object(orchestrator.agent_coordinator, 'execute_task', 
                         side_effect=mock_execute_task):
            result = await orchestrator.execute_workflow(workflow_id, tasks)
        
        # Verify execution order respects dependencies
        assert execution_order.index("task1") < execution_order.index("task2")
        assert execution_order.index("task2") < execution_order.index("task3")
        assert result.status == TaskStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self, orchestrator):
        """Test parallel task execution"""
        workflow_id = "test_workflow_004"
        context = await orchestrator.create_workflow(workflow_id)
        
        # Create tasks that can run in parallel
        tasks = [
            TaskDefinition(
                task_id=f"parallel_task_{i}",
                name=f"Parallel Task {i}",
                agent_role=AgentRole.ANALYZER,
                inputs={"index": i}
            )
            for i in range(3)
        ]
        
        execution_times = {}
        
        async def mock_execute_task(task, context):
            execution_times[task.task_id] = datetime.now()
            await asyncio.sleep(0.1)  # Simulate work
            return {"completed": True}
        
        with patch.object(orchestrator.agent_coordinator, 'execute_task', 
                         side_effect=mock_execute_task):
            result = await orchestrator.execute_workflow(workflow_id, tasks)
        
        # Verify tasks ran in parallel (execution times should be close)
        times = list(execution_times.values())
        time_diffs = [(times[i+1] - times[i]).total_seconds() 
                      for i in range(len(times)-1)]
        
        # If running in parallel, time differences should be < 0.05s
        assert all(diff < 0.05 for diff in time_diffs)
        assert result.status == TaskStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_task_failure_handling(self, orchestrator):
        """Test handling of task failures"""
        workflow_id = "test_workflow_005"
        context = await orchestrator.create_workflow(workflow_id)
        
        task = TaskDefinition(
            task_id="failing_task",
            name="Failing Task",
            agent_role=AgentRole.ANALYZER,
            inputs={"fail": True}
        )
        
        async def mock_execute_task(task, context):
            raise Exception("Task execution failed")
        
        with patch.object(orchestrator.agent_coordinator, 'execute_task', 
                         side_effect=mock_execute_task):
            result = await orchestrator.execute_workflow(workflow_id, [task])
        
        assert result.status == TaskStatus.FAILED
        assert len(result.errors) > 0
        assert "Task execution failed" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_task_timeout(self, orchestrator):
        """Test task timeout handling"""
        workflow_id = "test_workflow_006"
        context = await orchestrator.create_workflow(workflow_id)
        
        task = TaskDefinition(
            task_id="slow_task",
            name="Slow Task",
            agent_role=AgentRole.ANALYZER,
            inputs={"slow": True},
            timeout=1  # 1 second timeout
        )
        
        async def mock_execute_task(task, context):
            await asyncio.sleep(2)  # Sleep longer than timeout
            return {"completed": True}
        
        with patch.object(orchestrator.agent_coordinator, 'execute_task', 
                         side_effect=mock_execute_task):
            result = await orchestrator.execute_workflow(workflow_id, [task])
        
        assert result.status == TaskStatus.FAILED
        assert any("timed out" in error for error in result.errors)


class TestAgentCoordinator:
    """Test AgentCoordinator functionality"""
    
    @pytest.fixture
    def coordinator(self, mock_db_logger, mock_weaviate_manager):
        """Create agent coordinator with mocked dependencies"""
        return AgentCoordinator(mock_db_logger, mock_weaviate_manager)
    
    @pytest.mark.asyncio
    async def test_agent_execution(self, coordinator):
        """Test agent task execution"""
        task = TaskDefinition(
            task_id="test_task",
            name="Test Task",
            agent_role=AgentRole.ANALYZER,
            inputs={"test": True}
        )
        
        context = WorkflowContext(
            workflow_id="test_workflow",
            task_id="test_task"
        )
        
        result = await coordinator.execute_task(task, context)
        
        assert "analysis" in result
        assert result["analysis"]["structure"] == "Analyzed project structure"
    
    @pytest.mark.asyncio
    async def test_agent_role_mapping(self, coordinator):
        """Test correct agent is selected for role"""
        roles_and_results = [
            (AgentRole.ANALYZER, "analysis"),
            (AgentRole.IMPLEMENTER, "implementation"),
            (AgentRole.REFINER, "refinement")
        ]
        
        for role, expected_key in roles_and_results:
            task = TaskDefinition(
                task_id=f"test_{role.value}",
                name=f"Test {role.value}",
                agent_role=role,
                inputs={"test": True}
            )
            
            context = WorkflowContext(
                workflow_id="test_workflow",
                task_id=task.task_id
            )
            
            result = await coordinator.execute_task(task, context)
            assert expected_key in result


class TestMCPContextManager:
    """Test MCP context manager functionality"""
    
    @pytest.mark.asyncio
    async def test_task_creation(self):
        """Test creating task in MCP server"""
        async with MCPContextManager("http://localhost:8080") as mcp:
            task = TaskDefinition(
                task_id="mcp_test_task",
                name="MCP Test Task",
                agent_role=AgentRole.ANALYZER,
                inputs={"test": True}
            )
            
            with patch.object(mcp.session, 'post') as mock_post:
                mock_response = AsyncMock()
                mock_response.json = AsyncMock(return_value={"task_id": task.task_id})
                mock_post.return_value.__aenter__.return_value = mock_response
                
                result = await mcp.create_task(task)
                
                assert result["task_id"] == task.task_id
                mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_status_update(self):
        """Test updating task status in MCP server"""
        async with MCPContextManager("http://localhost:8080") as mcp:
            task_id = "test_task_id"
            
            with patch.object(mcp.session, 'patch') as mock_patch:
                mock_response = AsyncMock()
                mock_response.json = AsyncMock(return_value={"status": "completed"})
                mock_patch.return_value.__aenter__.return_value = mock_response
                
                result = await mcp.update_task_status(
                    task_id, 
                    TaskStatus.COMPLETED,
                    {"result": "success"}
                )
                
                assert result["status"] == "completed"
                mock_patch.assert_called_once()


class TestDatabaseLogger:
    """Test database logging functionality"""
    
    @pytest.fixture
    def mock_connection(self):
        """Mock database connection"""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            yield mock_conn, mock_cursor
    
    def test_log_action(self, mock_connection):
        """Test logging an action"""
        mock_conn, mock_cursor = mock_connection
        
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_DB': 'test_db',
            'POSTGRES_USER': 'test_user',
            'POSTGRES_PASSWORD': 'test_pass'
        }):
            logger = DatabaseLogger()
            
            logger.log_action(
                workflow_id="test_workflow",
                task_id="test_task",
                agent_role="analyzer",
                action="task_start",
                status="running",
                metadata={"test": True}
            )
            
            # Verify INSERT was called
            mock_cursor.execute.assert_called()
            call_args = mock_cursor.execute.call_args[0]
            assert "INSERT INTO orchestration_logs" in call_args[0]


class TestWeaviateManager:
    """Test Weaviate manager functionality"""
    
    @pytest.fixture
    def mock_client(self):
        """Mock Weaviate client"""
        with patch('weaviate.Client') as mock_client_class:
            mock_client = Mock()
            mock_client.schema.create_class = Mock()
            mock_client.data_object.create = Mock()
            mock_client.query.get.return_value.with_where.return_value.with_limit.return_value.do.return_value = {
                "data": {"Get": {"OrchestrationContext": []}}
            }
            mock_client_class.return_value = mock_client
            yield mock_client
    
    def test_store_context(self, mock_client):
        """Test storing context in Weaviate"""
        with patch.dict(os.environ, {
            'WEAVIATE_URL': 'http://localhost:8080',
            'WEAVIATE_API_KEY': 'test_key'
        }):
            manager = WeaviateManager()
            
            manager.store_context(
                workflow_id="test_workflow",
                task_id="test_task",
                context_type="checkpoint",
                content="test content",
                metadata={"test": True}
            )
            
            mock_client.data_object.create.assert_called_once()
            call_args = mock_client.data_object.create.call_args
            assert call_args[1]["class_name"] == "OrchestrationContext"
            assert call_args[1]["data_object"]["workflow_id"] == "test_workflow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])