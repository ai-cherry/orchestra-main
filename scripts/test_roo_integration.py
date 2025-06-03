#!/usr/bin/env python3
"""Comprehensive test suite for Roo AI Orchestrator integration."""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import pytest
from rich.console import Console
from rich.table import Table

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_components.orchestration.mcp_integration import UnifiedContextManager
from ai_components.orchestration.mode_transition_manager import (
    ModeTransitionManager,
    RooMode,
    TransitionType,
)
from ai_components.orchestration.roo_mcp_adapter import RooMCPAdapter
from ai_components.orchestration.unified_api_router import UnifiedAPIRouter
from shared.database import UnifiedDatabase

console = Console()
logger = logging.getLogger(__name__)


class IntegrationTester:
    """Test harness for Roo integration."""

    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")

    async def test_database_connectivity(self) -> bool:
        """Test database connection and schema."""
        try:
            async with UnifiedDatabase() as db:
                # Check if tables exist
                result = await db.fetch_one(
                    """
                    SELECT COUNT(*) as count FROM information_schema.tables 
                    WHERE table_name IN ('roo_mode_executions', 'mode_transitions')
                    """
                )
                
                if result["count"] != 2:
                    self.results.append(
                        ("Database Schema", False, "Missing required tables")
                    )
                    return False
                
                # Test insert/select
                await db.execute(
                    """
                    INSERT INTO roo_mode_executions (mode, task, context, result)
                    VALUES ($1, $2, $3, $4)
                    """,
                    "test", "test task", "{}", "test result"
                )
                
                test_row = await db.fetch_one(
                    "SELECT * FROM roo_mode_executions WHERE mode = $1", "test"
                )
                
                if test_row:
                    # Cleanup
                    await db.execute(
                        "DELETE FROM roo_mode_executions WHERE mode = $1", "test"
                    )
                    self.results.append(("Database Connectivity", True, "OK"))
                    return True
                else:
                    self.results.append(
                        ("Database Connectivity", False, "Insert/Select failed")
                    )
                    return False
                    
        except Exception as e:
            self.results.append(("Database Connectivity", False, str(e)))
            return False

    async def test_api_authentication(self) -> bool:
        """Test OpenRouter API authentication."""
        if not self.api_key:
            self.results.append(
                ("API Authentication", False, "OPENROUTER_API_KEY not set")
            )
            return False

        try:
            adapter = RooMCPAdapter(self.api_key)
            
            # Test with a minimal request
            result = await adapter.execute_mode_task(
                RooMode.ASK,
                "What is 2+2?",
                {"max_tokens": 10}
            )
            
            await adapter.close()
            
            if result and "result" in result:
                self.results.append(("API Authentication", True, "OK"))
                return True
            else:
                self.results.append(
                    ("API Authentication", False, "Invalid response")
                )
                return False
                
        except Exception as e:
            self.results.append(("API Authentication", False, str(e)))
            return False

    async def test_mode_transitions(self) -> bool:
        """Test mode transition logic."""
        try:
            manager = ModeTransitionManager()
            
            # Test transition initiation
            transition_id = await manager.initiate_transition(
                "test_session",
                RooMode.CODE,
                RooMode.DEBUG,
                {"task": "Debug test", "error": "Test error"},
                TransitionType.AUTOMATIC
            )
            
            # Test transition execution
            context = await manager.execute_transition(transition_id)
            
            if context and context.to_mode == RooMode.DEBUG:
                self.results.append(("Mode Transitions", True, "OK"))
                return True
            else:
                self.results.append(
                    ("Mode Transitions", False, "Transition failed")
                )
                return False
                
        except Exception as e:
            self.results.append(("Mode Transitions", False, str(e)))
            return False

    async def test_circuit_breaker(self) -> bool:
        """Test circuit breaker functionality."""
        try:
            router = UnifiedAPIRouter(
                self.api_key or "test_key",
                "http://localhost:8000",
                "https://openrouter.ai/api/v1"
            )
            
            # Test circuit breaker states
            breaker = router.circuit_breakers["openrouter"]
            
            # Simulate failures
            for _ in range(5):
                breaker.record_failure()
            
            if breaker.state.value == "open":
                # Test recovery
                breaker.last_failure_time = breaker.last_failure_time.replace(
                    second=breaker.last_failure_time.second - 61
                )
                
                if breaker.can_request():
                    await router.close()
                    self.results.append(("Circuit Breaker", True, "OK"))
                    return True
                    
            await router.close()
            self.results.append(
                ("Circuit Breaker", False, "State transition failed")
            )
            return False
            
        except Exception as e:
            self.results.append(("Circuit Breaker", False, str(e)))
            return False

    async def test_context_sync(self) -> bool:
        """Test context synchronization."""
        try:
            if not self.api_key:
                self.results.append(
                    ("Context Sync", False, "API key required")
                )
                return False
                
            context_manager = UnifiedContextManager(
                os.getenv("WEAVIATE_URL", "http://localhost:8080"),
                self.api_key
            )
            
            # Test Roo to MCP conversion
            roo_context = {
                "mode": RooMode.CODE.value,
                "task": "Test task",
                "result": "Test result",
                "history": [],
                "files": ["test.py"],
            }
            
            mcp_context = await context_manager.sync_context_bidirectional(
                "test_session", "roo", roo_context
            )
            
            if mcp_context and "agent_id" in mcp_context:
                self.results.append(("Context Sync", True, "OK"))
                return True
            else:
                self.results.append(
                    ("Context Sync", False, "Conversion failed")
                )
                return False
                
        except Exception as e:
            self.results.append(("Context Sync", False, str(e)))
            return False

    async def test_performance_metrics(self) -> bool:
        """Test performance monitoring."""
        try:
            router = UnifiedAPIRouter(
                self.api_key or "test_key",
                "http://localhost:8000",
                "https://openrouter.ai/api/v1"
            )
            
            # Get initial metrics
            health = router.get_service_health()
            
            if "openrouter" in health and "orchestrator" in health:
                await router.close()
                self.results.append(("Performance Metrics", True, "OK"))
                return True
            else:
                await router.close()
                self.results.append(
                    ("Performance Metrics", False, "Missing metrics")
                )
                return False
                
        except Exception as e:
            self.results.append(("Performance Metrics", False, str(e)))
            return False

    async def run_all_tests(self) -> None:
        """Run all integration tests."""
        tests = [
            ("Database Connectivity", self.test_database_connectivity),
            ("API Authentication", self.test_api_authentication),
            ("Mode Transitions", self.test_mode_transitions),
            ("Circuit Breaker", self.test_circuit_breaker),
            ("Context Sync", self.test_context_sync),
            ("Performance Metrics", self.test_performance_metrics),
        ]
        
        console.print("\n[bold]Running Integration Tests...[/bold]\n")
        
        for test_name, test_func in tests:
            console.print(f"Testing {test_name}...", end=" ")
            try:
                success = await test_func()
                if success:
                    console.print("[green]✓[/green]")
                else:
                    console.print("[red]✗[/red]")
            except Exception as e:
                console.print(f"[red]✗ ({str(e)})[/red]")
                self.results.append((test_name, False, str(e)))

    def display_results(self) -> None:
        """Display test results in a table."""
        table = Table(title="\nTest Results Summary")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details", style="yellow")
        
        for test_name, success, details in self.results:
            status = "[green]PASS[/green]" if success else "[red]FAIL[/red]"
            table.add_row(test_name, status, details)
        
        console.print(table)
        
        # Summary
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        console.print(f"\n[bold]Total: {passed}/{total} tests passed[/bold]")
        
        if passed < total:
            console.print("\n[yellow]Issues to address:[/yellow]")
            for test_name, success, details in self.results:
                if not success:
                    console.print(f"  - {test_name}: {details}")


async def main():
    """Main test runner."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/roo_integration_test.log"),
        ],
    )
    
    tester = IntegrationTester()
    await tester.run_all_tests()
    tester.display_results()


if __name__ == "__main__":
    asyncio.run(main())