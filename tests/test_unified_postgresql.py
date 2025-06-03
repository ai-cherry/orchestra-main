#!/usr/bin/env python3
"""
"""
    """Test the connection manager singleton and pooling."""
        """Test that connection manager is a singleton."""
        assert manager1 is manager2, "Connection manager should be a singleton"

    @pytest.mark.asyncio
    async def test_connection_pool(self):
        """Test connection pool functionality."""
        result = await manager.fetchval("SELECT 1")
        assert result == 1

        # Test pool stats
        stats = await manager.get_pool_stats()
        assert stats["total_connections"] > 0
        assert stats["idle_connections"] >= 0
        assert stats["used_connections"] >= 0

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality."""
        assert health["status"] == "healthy"
        assert "pool" in health
        assert "database" in health
        assert health["database"]["connected"] is True

    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test concurrent connection usage."""
            task = manager.fetchval(f"SELECT {i}")
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Verify all queries completed
        assert results == list(range(10))

        # Check pool didn't exceed limits
        stats = await manager.get_pool_stats()
        assert stats["total_connections"] <= 20  # Max pool size

class TestUnifiedPostgreSQL:
    """Test the unified PostgreSQL client."""
        """Test cache functionality."""
        key = f"test_key_{uuid.uuid4()}"
        value = {"test": "data", "number": 42}

        await client.cache_set(key, value, ttl=60)
        retrieved = await client.cache_get(key)

        assert retrieved == value

        # Test with tags
        tagged_key = f"tagged_{uuid.uuid4()}"
        await client.cache_set(tagged_key, "tagged_value", ttl=60, tags=["test", "cache"])

        # Test delete
        await client.cache_delete(key)
        deleted_value = await client.cache_get(key)
        assert deleted_value is None

        # Test get by tags
        tagged_items = await client.cache_get_by_tags(["test", "cache"])
        assert len(tagged_items) > 0
        assert any(item["key"] == tagged_key for item in tagged_items)

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache TTL and expiration."""
        key = f"expire_test_{uuid.uuid4()}"
        await client.cache_set(key, "will_expire", ttl=1)

        # Should exist immediately
        assert await client.cache_get(key) == "will_expire"

        # Wait for expiration
        await asyncio.sleep(2)

        # Should be expired
        assert await client.cache_get(key) is None

    @pytest.mark.asyncio
    async def test_session_operations(self):
        """Test session functionality."""
        session_data = {"user_id": "test_user", "agent_id": "test_agent", "context": {"key": "value"}}

        session_id = await client.session_create(
            user_id="test_user", agent_id="test_agent", data=session_data, ttl=3600
        )

        assert session_id is not None

        # Get session
        retrieved = await client.session_get(session_id)
        assert retrieved is not None
        assert retrieved["user_id"] == "test_user"
        assert retrieved["agent_id"] == "test_agent"

        # Update session
        updated_data = {"updated": True, "new_field": "new_value"}
        await client.session_update(session_id, updated_data)

        updated = await client.session_get(session_id)
        assert updated["data"]["updated"] is True
        assert updated["data"]["new_field"] == "new_value"

        # List sessions
        user_sessions = await client.session_list(user_id="test_user")
        assert len(user_sessions) > 0
        assert any(s["id"] == session_id for s in user_sessions)

        # Delete session
        await client.session_delete(session_id)
        deleted = await client.session_get(session_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_agent_operations(self):
        """Test agent CRUD operations."""
            "name": f"Test Agent {uuid.uuid4()}",
            "type": "assistant",
            "config": {"model": "gpt-4", "temperature": 0.7},
            "capabilities": ["chat", "code"],
            "status": "active",
        }

        agent_id = await client.agent_create(**agent_data)
        assert agent_id is not None

        # Get agent
        agent = await client.agent_get(agent_id)
        assert agent["name"] == agent_data["name"]
        assert agent["type"] == agent_data["type"]
        assert agent["config"] == agent_data["config"]

        # Update agent
        await client.agent_update(agent_id, status="inactive", config={"model": "gpt-3.5"})

        updated = await client.agent_get(agent_id)
        assert updated["status"] == "inactive"
        assert updated["config"]["model"] == "gpt-3.5"

        # List agents
        agents = await client.agent_list(type="assistant")
        assert len(agents) > 0
        assert any(a["id"] == agent_id for a in agents)

        # Delete agent
        await client.agent_delete(agent_id)
        deleted = await client.agent_get(agent_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_workflow_operations(self):
        """Test workflow CRUD operations."""
            "name": f"Test Workflow {uuid.uuid4()}",
            "description": "Test workflow for unit tests",
            "definition": {
                "steps": [
                    {"id": "step1", "type": "input"},
                    {"id": "step2", "type": "process"},
                    {"id": "step3", "type": "output"},
                ],
                "connections": [{"from": "step1", "to": "step2"}, {"from": "step2", "to": "step3"}],
            },
            "status": "draft",
        }

        workflow_id = await client.workflow_create(**workflow_data)
        assert workflow_id is not None

        # Get workflow
        workflow = await client.workflow_get(workflow_id)
        assert workflow["name"] == workflow_data["name"]
        assert workflow["definition"] == workflow_data["definition"]

        # Update workflow
        await client.workflow_update(workflow_id, status="active")

        updated = await client.workflow_get(workflow_id)
        assert updated["status"] == "active"

        # List workflows
        workflows = await client.workflow_list(status="active")
        assert len(workflows) > 0
        assert any(w["id"] == workflow_id for w in workflows)

        # Delete workflow
        await client.workflow_delete(workflow_id)
        deleted = await client.workflow_get(workflow_id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_audit_log(self):
        """Test audit logging functionality."""
            action="test_action",
            entity_type="test_entity",
            entity_id="test_123",
            user_id="test_user",
            details={"test": "data"},
            metadata={"source": "unit_test"},
        )

        # Query audit logs
        logs = await client.audit_query(action="test_action", limit=10)

        assert len(logs) > 0
        assert logs[0]["action"] == "test_action"
        assert logs[0]["entity_type"] == "test_entity"
        assert logs[0]["details"]["test"] == "data"

    @pytest.mark.asyncio
    async def test_memory_snapshot(self):
        """Test memory snapshot functionality."""
            "conversation_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
            "context": {"topic": "greeting"},
            "metadata": {"session_id": "test_session"},
        }

        snapshot_id = await client.memory_snapshot_create(
            agent_id="test_agent", user_id="test_user", snapshot_data=snapshot_data
        )

        assert snapshot_id is not None

        # Get snapshot
        snapshot = await client.memory_snapshot_get(snapshot_id)
        assert snapshot["agent_id"] == "test_agent"
        assert snapshot["snapshot_data"] == snapshot_data

        # List snapshots
        snapshots = await client.memory_snapshot_list(agent_id="test_agent", user_id="test_user")

        assert len(snapshots) > 0
        assert any(s["id"] == snapshot_id for s in snapshots)

class TestUnifiedDatabase:
    """Test the unified database interface."""
        """Test agent operations with caching."""
            "name": f"Cached Agent {uuid.uuid4()}",
            "type": "assistant",
            "config": {"model": "gpt-4"},
            "capabilities": ["chat"],
            "status": "active",
        }

        agent_id = await db.create_agent(**agent_data)

        # First get (from database)
        start_time = time.time()
        agent1 = await db.get_agent(agent_id)
        db_time = time.time() - start_time

        # Second get (from cache)
        start_time = time.time()
        agent2 = await db.get_agent(agent_id)
        cache_time = time.time() - start_time

        # Cache should be faster
        assert cache_time < db_time
        assert agent1 == agent2

        # Update should invalidate cache
        await db.update_agent(agent_id, status="inactive")

        updated = await db.get_agent(agent_id)
        assert updated["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_parallel_search(self):
        """Test parallel search across data types."""
            name="Search Test Agent", type="assistant", config={}, capabilities=["search"], status="active"
        )

        workflow_id = await db.create_workflow(
            name="Search Test Workflow",
            description="Workflow for search testing",
            definition={"steps": []},
            status="active",
        )

        # Search
        results = await db.search("Search Test")

        assert "agents" in results
        assert "workflows" in results
        assert len(results["agents"]) > 0
        assert len(results["workflows"]) > 0

        # Cleanup
        await db.delete_agent(agent_id)
        await db.delete_workflow(workflow_id)

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test unified database health check."""
        assert health["status"] == "healthy"
        assert health["postgresql"]["status"] == "healthy"
        assert health["weaviate"]["status"] == "healthy"
        assert "cache_stats" in health

    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test performance tracking."""
                name=f"Perf Test Agent {i}", type="assistant", config={}, capabilities=[], status="active"
            )
            await db.get_agent(agent_id)
            await db.delete_agent(agent_id)

        # Get metrics
        metrics = await db.get_performance_metrics()

        assert "operations" in metrics
        assert "cache" in metrics
        assert metrics["operations"]["total"] >= 15  # 3 ops per iteration * 5
        assert metrics["cache"]["hit_rate"] >= 0

class TestBackgroundTasks:
    """Test background cleanup tasks."""
        """Test automatic cache cleanup."""
        expired_key = f"expired_{uuid.uuid4()}"
        await client.cache_set(expired_key, "will_be_cleaned", ttl=-1)  # Already expired

        # Create valid cache entry
        valid_key = f"valid_{uuid.uuid4()}"
        await client.cache_set(valid_key, "should_remain", ttl=3600)

        # Run cleanup
        deleted = await client._cleanup_expired_cache()

        assert deleted > 0
        assert await client.cache_get(expired_key) is None
        assert await client.cache_get(valid_key) == "should_remain"

    @pytest.mark.asyncio
    async def test_session_cleanup(self):
        """Test automatic session cleanup."""
            user_id="test_user", agent_id="test_agent", data={}, ttl=-1  # Already expired
        )

        # Create valid session
        valid_id = await client.session_create(user_id="test_user", agent_id="test_agent", data={}, ttl=3600)

        # Run cleanup
        deleted = await client._cleanup_expired_sessions()

        assert deleted > 0
        assert await client.session_get(expired_id) is None
        assert await client.session_get(valid_id) is not None

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    """Cleanup after each test."""
if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
