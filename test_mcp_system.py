#!/usr/bin/env python3
"""
"""
GATEWAY_URL = "http://localhost:8000"
TESTS = []

def test(name: str):
    """Decorator to register tests"""
@test("Gateway Health Check")
async def test_gateway_health():
    """Test gateway health endpoint"""
        response = await client.get(f"{GATEWAY_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        return f"Gateway status: {data['status']}"

@test("Server Status Check")
async def test_server_status():
    """Test detailed server status"""
        response = await client.get(f"{GATEWAY_URL}/status")
        assert response.status_code == 200
        data = response.json()

        results = []
        for server_id, health in data["servers"].items():
            results.append(f"{server_id}: {health['healthy']}")

        return "\n".join(results)

@test("List Available Tools")
async def test_list_tools():
    """Test listing all MCP tools"""
        response = await client.get(f"{GATEWAY_URL}/mcp/tools")
        assert response.status_code == 200
        data = response.json()

        tool_count = sum(len(server["tools"]) for server in data.values())
        return f"Found {tool_count} tools across {len(data)} servers"

@test("Store Memory")
async def test_store_memory():
    """Test storing a memory"""
            "server": "memory",
            "action": "store_memory",
            "params": {
                "content": f"Test memory created at {datetime.now().isoformat()}",
                "importance": 0.7,
                "metadata": {"type": "test", "source": "mcp_test"},
                "memory_type": "test",
            },
        }

        response = await client.post(f"{GATEWAY_URL}/mcp/execute", json=memory_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        return f"Memory stored in {len(data['layers_stored'])} layers"

@test("Query Memory")
async def test_query_memory():
    """Test querying memories"""
            "server": "memory",
            "action": "query_memory",
            "params": {"query": "test memory", "max_results": 5},
        }

        response = await client.post(f"{GATEWAY_URL}/mcp/execute", json=query_data)
        assert response.status_code == 200
        data = response.json()

        return f"Found {len(data)} memories"

@test("Create Secret")
async def test_create_secret():
    """Test creating a secret"""
            "server": "secrets",
            "action": "create_secret",
            "params": {
                "secret_id": "mcp-test-secret",
                "value": "test-value-123",
                "labels": {"created_by": "mcp_test", "environment": "test"},
            },
        }

        response = await client.post(f"{GATEWAY_URL}/mcp/execute", json=secret_data)

        # It's okay if it already exists
        if response.status_code == 200:
            return "Secret created successfully"
        else:
            data = response.json()
            if "already exists" in data.get("detail", ""):
                return "Secret already exists (OK)"
            else:
                raise Exception(f"Failed to create secret: {data}")

@test("Switch Mode")
async def test_switch_mode():
    """Test switching conductor mode"""
            "server": "conductor",
            "action": "switch_mode",
            "params": {"mode": "performance", "context": {"test": True}},
        }

        response = await client.post(f"{GATEWAY_URL}/mcp/execute", json=mode_data)
        assert response.status_code == 200
        data = response.json()

        return f"Switched from {data['previous_mode']} to {data['current_mode']}"

@test("Run Workflow")
async def test_run_workflow():
    """Test running a workflow"""
            "server": "conductor",
            "action": "run_workflow",
            "params": {"name": "code_review", "params": {"test": True}},
        }

        response = await client.post(f"{GATEWAY_URL}/mcp/execute", json=workflow_data)
        assert response.status_code == 200
        data = response.json()

        return f"Started workflow: {data['workflow_id']}"

@test("Get conductor Status")
async def test_conductor_status():
    """Test getting conductor status"""
            "server": "conductor",
            "action": "get_status",
            "params": {"include_workflows": True, "include_tasks": True},
        }

        response = await client.post(f"{GATEWAY_URL}/mcp/execute", json=status_data)
        assert response.status_code == 200
        data = response.json()

        return f"Mode: {data['current_mode']}, Active workflows: {data['workflows']['active']}"

@test("Prometheus Metrics")
async def test_metrics():
    """Test Prometheus metrics endpoint"""
        response = await client.get(f"{GATEWAY_URL}/metrics")
        assert response.status_code == 200
        assert "mcp_gateway_requests_total" in response.text

        # Count metric lines
        metric_lines = [l for l in response.text.split("\n") if l and not l.startswith("#")]
        return f"Found {len(metric_lines)} metrics"

async def run_tests():
    """Run all tests"""
            "[bold blue]MCP System Integration Tests[/bold blue]\n" f"Testing {len(TESTS)} components...",
            border_style="blue",
        )
    )

    # Create results table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Test", style="cyan", width=30)
    table.add_column("Status", width=10)
    table.add_column("Result", width=50)

    passed = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        for test_name, test_func in TESTS:
            task = progress.add_task(f"Running {test_name}...", total=None)

            try:


                pass
                result = await test_func()
                table.add_row(test_name, "[green]✓ PASS[/green]", result)
                passed += 1
            except Exception:

                pass
                table.add_row(test_name, "[red]✗ FAIL[/red]", f"[red]{str(e)}[/red]")
                failed += 1

            progress.remove_task(task)

    console.print("\n")
    console.print(table)
    console.print("\n")

    # Summary
    total = passed + failed
    if failed == 0:
        console.print(f"[bold green]All {total} tests passed! ✨[/bold green]")
    else:
        console.print(f"[bold yellow]Tests completed: {passed}/{total} passed[/bold yellow]")
        if failed > 0:
            console.print(f"[bold red]{failed} tests failed[/bold red]")

    return failed == 0

async def main():
    """Main test runner"""
    console.print("[yellow]Waiting for servers to be ready...[/yellow]")
    await asyncio.sleep(2)

    try:


        pass
        success = await run_tests()
        exit(0 if success else 1)
    except Exception:

        pass
        console.print(f"[bold red]Test execution failed: {e}[/bold red]")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
