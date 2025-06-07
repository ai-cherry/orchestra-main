"""
"""
    """Test LLM coordination API endpoints"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_test_routing_endpoint(self, client):
        """Test the routing test endpoint"""
                "choices": [{"message": {"content": "Test response"}}],
                "routing_metadata": {
                    "query_type": "creative_search",
                    "model_used": "gpt-4",
                    "temperature": 0.9,
                    "max_tokens": 2000,
                    "latency_ms": 1234,
                    "reasoning": "Selected for creative query"
                }
            })
            mock_router.return_value = mock_instance
            
            response = await client.post(
                "/api/coordination/test-routing",
                json={
                    "query": "Write a creative story",
                    "force_query_type": "creative_search"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "Write a creative story"
            assert data["query_type"] == "creative_search"
            assert data["model_used"] == "gpt-4"
            assert data["temperature"] == 0.9
    
    @pytest.mark.asyncio
    async def test_routing_analytics_endpoint(self, client):
        """Test the routing analytics endpoint"""
                "query_type_distribution": {"creative_search": 10, "analytical": 5},
                "model_performance": {
                    "gpt-4": {
                        "avg_latency_ms": 1500,
                        "p95_latency_ms": 2000,
                        "success_rate": 0.98,
                        "total_requests": 100
                    }
                },
                "recent_routing_decisions": [],
                "total_queries_routed": 15
            })
            mock_router.return_value = mock_instance
            
            response = await client.get("/api/coordination/routing-analytics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_queries_routed"] == 15
            assert "creative_search" in data["query_type_distribution"]
    
    @pytest.mark.asyncio
    async def test_query_types_endpoint(self, client):
        """Test the query types endpoint"""
        response = await client.get("/api/coordination/query-types")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("value" in qt and "name" in qt for qt in data)
    
    @pytest.mark.asyncio
    async def test_agents_status_endpoint(self, client):
        """Test the agents status endpoint"""
                "id": "test-001",
                "name": "Test Agent",
                "type": "personal",
                "status": "idle",
                "tasks_completed": 10
            })
            mock_get_agent.return_value = mock_agent
            
            response = await client.get("/api/coordination/agents")
            
            assert response.status_code == 200
            data = response.json()
            assert "agents" in data
            assert data["total_agents"] == len(AgentType)
    
    @pytest.mark.asyncio
    async def test_execute_agent_task_endpoint(self, client):
        """Test executing a task on a specific agent"""
            mock_process.return_value = {"result": "success"}
            
            response = await client.post(
                "/api/coordination/agents/personal/execute",
                json={
                    "agent_type": "personal",
                    "task": {"type": "search", "query": "test"}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["agent_type"] == "personal"
            assert data["result"]["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_personal_search_endpoint(self, client):
        """Test personal agent search endpoint"""
                "query": "test query",
                "results": [{"id": "1", "content": "result"}],
                "preferences_applied": ["test_pref"],
                "search_id": "search123"
            })
            mock_get_agent.return_value = mock_agent
            
            response = await client.post(
                "/api/coordination/personal/search",
                json={
                    "user_id": "user123",
                    "query": "test query",
                    "search_type": "general"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "test query"
            assert len(data["results"]) == 1
    
    @pytest.mark.asyncio
    async def test_payready_analyze_endpoint(self, client):
        """Test Pay Ready agent analysis endpoint"""
                "id": "apt123",
                "address": "123 Test St",
                "price": 2500,
                "tech_score": 85.0,
                "neighborhood_score": 90.0,
                "overall_score": 87.5
            }
            mock_agent.analyze_listing = AsyncMock(return_value=mock_listing)
            mock_get_agent.return_value = mock_agent
            
            response = await client.post(
                "/api/coordination/payready/analyze",
                json={
                    "listing_data": {
                        "id": "apt123",
                        "address": "123 Test St",
                        "price": 2500,
                        "bedrooms": 2,
                        "bathrooms": 2,
                        "sqft": 1200,
                        "amenities": ["gym", "pool"],
                        "smart_home_features": ["smart_locks"]
                    }
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["listing"]["overall_score"] == 87.5
            assert data["recommendation"] == "recommended"
    
    @pytest.mark.asyncio
    async def test_paragon_search_trials_endpoint(self, client):
        """Test Paragon medical agent trial search endpoint"""
                "nct_id": "NCT12345",
                "title": "Test Trial",
                "phase": "Phase 3",
                "conditions": ["chronic pain"],
                "relevance_score": 85.0
            }
            mock_agent.search_clinical_trials = AsyncMock(return_value=[mock_trial])
            mock_get_agent.return_value = mock_agent
            
            response = await client.post(
                "/api/coordination/paragon/search-trials",
                json={
                    "conditions": ["chronic pain"],
                    "phases": ["Phase 3", "Phase 4"]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_found"] == 1
            assert data["trials"][0]["nct_id"] == "NCT12345"
    
    @pytest.mark.asyncio
    async def test_create_workflow_endpoint(self, client):
        """Test workflow creation endpoint"""
            mock_workflow.id = "workflow123"
            mock_workflow.name = "Test Workflow"
            mock_workflow.status.value = "pending"
            mock_workflow.tasks = {"task1": Mock()}
            mock_workflow.created_at.isoformat.return_value = "2024-01-01T00:00:00"
            
            mock_conductor.create_workflow = AsyncMock(return_value=mock_workflow)
            mock_get_orch.return_value = mock_conductor
            
            response = await client.post(
                "/api/coordination/workflows",
                json={
                    "name": "Test Workflow",
                    "tasks": [
                        {
                            "id": "task1",
                            "agent_type": "personal",
                            "data": {"query": "test"},
                            "dependencies": []
                        }
                    ]
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["workflow_id"] == "workflow123"
            assert data["name"] == "Test Workflow"
    
    @pytest.mark.asyncio
    async def test_execute_workflow_endpoint(self, client):
        """Test workflow execution endpoint"""
            response = await client.post("/api/coordination/workflows/workflow123/execute")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "execution_started"
    
    @pytest.mark.asyncio
    async def test_workflow_status_endpoint(self, client):
        """Test getting workflow status"""
                "workflow_id": "workflow123",
                "name": "Test Workflow",
                "status": "running",
                "progress": 50.0,
                "tasks": {}
            })
            mock_get_orch.return_value = mock_conductor
            
            response = await client.get("/api/coordination/workflows/workflow123/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["workflow_id"] == "workflow123"
            assert data["progress"] == 50.0
    
    @pytest.mark.asyncio
    async def test_system_health_endpoint(self, client):
        """Test system health check endpoint"""
                    mock_agent.get_status = AsyncMock(return_value={"status": "idle"})
                    mock_get_agent.return_value = mock_agent
                    
                    response = await client.get("/api/coordination/system/health")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] in ["healthy", "degraded"]
                    assert "components" in data
                    assert "llm_router" in data["components"]
                    assert "conductor" in data["components"]

class TestErrorHandling:
    """Test error handling in API endpoints"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_invalid_agent_type(self, client):
        """Test error handling for invalid agent type"""
            "/api/coordination/agents/invalid_type/execute",
            json={"agent_type": "invalid_type", "task": {}}
        )
        
        assert response.status_code == 400
        assert "Invalid agent type" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_workflow_not_found(self, client):
        """Test error handling for non-existent workflow"""
                side_effect=ValueError("Workflow not found")
            )
            mock_get_orch.return_value = mock_conductor
            
            response = await client.get("/api/coordination/workflows/nonexistent/status")
            
            assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_routing_failure(self, client):
        """Test error handling for routing failures"""
                side_effect=Exception("Routing failed")
            )
            mock_router.return_value = mock_instance
            
            response = await client.post(
                "/api/coordination/test-routing",
                json={"query": "Test query"}
            )
            
            assert response.status_code == 500
            assert "Routing failed" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])