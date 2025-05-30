#!/usr/bin/env python3
"""
Performance Testing Suite for SuperAGI
=====================================
Load testing and performance benchmarking for AI Orchestra
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import numpy as np
import requests
from kubernetes import client, config

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Performance test result"""

    test_name: str
    duration_seconds: float
    requests_total: int
    requests_successful: int
    requests_failed: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_rps: float
    error_rate: float
    timestamp: datetime


class PerformanceTester:
    """Performance testing for SuperAGI deployment"""

    def __init__(self, superagi_endpoint: str, prometheus_endpoint: Optional[str] = None):
        self.superagi_endpoint = superagi_endpoint.rstrip("/")
        self.prometheus_endpoint = prometheus_endpoint
        self.results: List[TestResult] = []

        # Load Kubernetes config
        try:
            config.load_incluster_config()
        except config.ConfigException as e:
            logger.warning(f"Could not load Kubernetes config, proceeding with defaults or limited functionality: {e}")
            config.load_kube_config()

        self.k8s_v1 = client.CoreV1Api()

    async def test_agent_execution(
        self,
        num_requests: int = 100,
        concurrent_requests: int = 10,
        agent_id: str = "researcher",
    ) -> TestResult:
        """Test agent execution performance"""
        logger.info(f"Starting agent execution test: {num_requests} requests, {concurrent_requests} concurrent")

        latencies = []
        errors = 0
        start_time = time.time()

        async def execute_request(session: aiohttp.ClientSession) -> float:
            """Execute a single agent request"""
            payload = {
                "agent_id": agent_id,
                "task": f"Test task {datetime.now().isoformat()}",
                "memory_context": True,
            }

            request_start = time.time()
            try:
                async with session.post(
                    f"{self.superagi_endpoint}/agents/execute",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        latency = (time.time() - request_start) * 1000  # ms
                        return latency
                    else:
                        logger.error(f"Request failed with status: {response.status}")
                        return -1
            except Exception as e:
                logger.error(f"Request error: {str(e)}")
                return -1

        # Run concurrent requests
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(concurrent_requests)

            async def bounded_request(session):
                async with semaphore:
                    return await execute_request(session)

            tasks = [bounded_request(session) for _ in range(num_requests)]
            results = await asyncio.gather(*tasks)

        # Process results
        for latency in results:
            if latency >= 0:
                latencies.append(latency)
            else:
                errors += 1

        duration = time.time() - start_time

        # Calculate metrics
        if latencies:
            latencies_array = np.array(latencies)
            result = TestResult(
                test_name="agent_execution",
                duration_seconds=duration,
                requests_total=num_requests,
                requests_successful=len(latencies),
                requests_failed=errors,
                avg_latency_ms=float(np.mean(latencies_array)),
                p50_latency_ms=float(np.percentile(latencies_array, 50)),
                p95_latency_ms=float(np.percentile(latencies_array, 95)),
                p99_latency_ms=float(np.percentile(latencies_array, 99)),
                throughput_rps=num_requests / duration,
                error_rate=errors / num_requests,
                timestamp=datetime.now(),
            )
        else:
            result = TestResult(
                test_name="agent_execution",
                duration_seconds=duration,
                requests_total=num_requests,
                requests_successful=0,
                requests_failed=errors,
                avg_latency_ms=0,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                throughput_rps=0,
                error_rate=1.0,
                timestamp=datetime.now(),
            )

        self.results.append(result)
        self._print_result(result)
        return result

    async def test_memory_operations(self, num_operations: int = 100, concurrent_operations: int = 10) -> TestResult:
        """Test memory store/retrieve performance"""
        logger.info(f"Starting memory operations test: {num_operations} operations")

        latencies = []
        errors = 0
        start_time = time.time()

        async def memory_operation(session: aiohttp.ClientSession, operation_id: int) -> float:
            """Perform a memory store and retrieve operation"""
            memory_data = {
                "agent_id": "test_agent",
                "memory_type": "short_term",
                "content": f"Test memory content {operation_id}",
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "operation_id": operation_id,
                },
            }

            request_start = time.time()
            try:
                # Store memory
                async with session.post(
                    f"{self.superagi_endpoint}/memory/store",
                    json=memory_data,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status != 200:
                        return -1

                    result = await response.json()
                    memory_id = result.get("memory_id")

                # Retrieve memory
                async with session.get(
                    f"{self.superagi_endpoint}/memory/{memory_id}",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        latency = (time.time() - request_start) * 1000  # ms
                        return latency
                    else:
                        return -1

            except Exception as e:
                logger.error(f"Memory operation error: {str(e)}")
                return -1

        # Run concurrent operations
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(concurrent_operations)

            async def bounded_operation(session, op_id):
                async with semaphore:
                    return await memory_operation(session, op_id)

            tasks = [bounded_operation(session, i) for i in range(num_operations)]
            results = await asyncio.gather(*tasks)

        # Process results
        for latency in results:
            if latency >= 0:
                latencies.append(latency)
            else:
                errors += 1

        duration = time.time() - start_time

        # Calculate metrics
        if latencies:
            latencies_array = np.array(latencies)
            result = TestResult(
                test_name="memory_operations",
                duration_seconds=duration,
                requests_total=num_operations,
                requests_successful=len(latencies),
                requests_failed=errors,
                avg_latency_ms=float(np.mean(latencies_array)),
                p50_latency_ms=float(np.percentile(latencies_array, 50)),
                p95_latency_ms=float(np.percentile(latencies_array, 95)),
                p99_latency_ms=float(np.percentile(latencies_array, 99)),
                throughput_rps=num_operations / duration,
                error_rate=errors / num_operations,
                timestamp=datetime.now(),
            )
        else:
            result = TestResult(
                test_name="memory_operations",
                duration_seconds=duration,
                requests_total=num_operations,
                requests_successful=0,
                requests_failed=errors,
                avg_latency_ms=0,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                throughput_rps=0,
                error_rate=1.0,
                timestamp=datetime.now(),
            )

        self.results.append(result)
        self._print_result(result)
        return result

    async def test_concurrent_agents(self, num_agents: int = 5, tasks_per_agent: int = 10) -> TestResult:
        """Test multiple agents running concurrently"""
        logger.info(f"Starting concurrent agents test: {num_agents} agents, {tasks_per_agent} tasks each")

        agent_ids = [f"agent_{i}" for i in range(num_agents)]
        latencies = []
        errors = 0
        start_time = time.time()

        async def agent_tasks(session: aiohttp.ClientSession, agent_id: str) -> List[float]:
            """Execute multiple tasks for a single agent"""
            agent_latencies = []

            for i in range(tasks_per_agent):
                payload = {
                    "agent_id": agent_id,
                    "task": f"Task {i} for {agent_id}",
                    "memory_context": True,
                }

                request_start = time.time()
                try:
                    async with session.post(
                        f"{self.superagi_endpoint}/agents/execute",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        if response.status == 200:
                            latency = (time.time() - request_start) * 1000  # ms
                            agent_latencies.append(latency)
                        else:
                            agent_latencies.append(-1)
                except Exception:
                    agent_latencies.append(-1)

            return agent_latencies

        # Run all agents concurrently
        async with aiohttp.ClientSession() as session:
            tasks = [agent_tasks(session, agent_id) for agent_id in agent_ids]
            all_results = await asyncio.gather(*tasks)

        # Process results
        for agent_results in all_results:
            for latency in agent_results:
                if latency >= 0:
                    latencies.append(latency)
                else:
                    errors += 1

        duration = time.time() - start_time
        total_requests = num_agents * tasks_per_agent

        # Calculate metrics
        if latencies:
            latencies_array = np.array(latencies)
            result = TestResult(
                test_name="concurrent_agents",
                duration_seconds=duration,
                requests_total=total_requests,
                requests_successful=len(latencies),
                requests_failed=errors,
                avg_latency_ms=float(np.mean(latencies_array)),
                p50_latency_ms=float(np.percentile(latencies_array, 50)),
                p95_latency_ms=float(np.percentile(latencies_array, 95)),
                p99_latency_ms=float(np.percentile(latencies_array, 99)),
                throughput_rps=total_requests / duration,
                error_rate=errors / total_requests,
                timestamp=datetime.now(),
            )
        else:
            result = TestResult(
                test_name="concurrent_agents",
                duration_seconds=duration,
                requests_total=total_requests,
                requests_successful=0,
                requests_failed=errors,
                avg_latency_ms=0,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                throughput_rps=0,
                error_rate=1.0,
                timestamp=datetime.now(),
            )

        self.results.append(result)
        self._print_result(result)
        return result

    def get_resource_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get current resource usage from Prometheus"""
        if not self.prometheus_endpoint:
            logger.warning("Prometheus endpoint not configured")
            return {}

        try:
            # Query Prometheus metrics
            response = requests.get(
                f"{self.prometheus_endpoint}/api/v1/query",
                params={"query": 'container_memory_usage_bytes{namespace="superagi"}'},
            )

            if response.status_code == 200:
                data = response.json()
                metrics = {}

                for result in data.get("data", {}).get("result", []):
                    pod = result["metric"].get("pod", "unknown")
                    value = float(result["value"][1]) / (1024 * 1024 * 1024)  # Convert to GB
                    metrics[f"{pod}_memory_gb"] = value

                return {"resources": metrics}
            else:
                logger.error(f"Failed to get metrics: {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Error getting resource metrics: {str(e)}")
            return {}

    def _print_result(self, result: TestResult):
        """Print test result summary"""
        print("\n" + "=" * 60)
        print(f"Test: {result.test_name}")
        print("=" * 60)
        print(f"Duration: {result.duration_seconds:.2f} seconds")
        print(f"Total Requests: {result.requests_total}")
        print(f"Successful: {result.requests_successful}")
        print(f"Failed: {result.requests_failed}")
        print(f"Error Rate: {result.error_rate:.2%}")
        print(f"Throughput: {result.throughput_rps:.2f} req/s")
        print(f"Avg Latency: {result.avg_latency_ms:.2f} ms")
        print(f"P50 Latency: {result.p50_latency_ms:.2f} ms")
        print(f"P95 Latency: {result.p95_latency_ms:.2f} ms")
        print(f"P99 Latency: {result.p99_latency_ms:.2f} ms")
        print("=" * 60 + "\n")

    def generate_report(self) -> str:
        """Generate performance test report"""
        report = []
        report.append("# SuperAGI Performance Test Report")
        report.append(f"\nGenerated: {datetime.now().isoformat()}")
        report.append(f"\nEndpoint: {self.superagi_endpoint}")

        for result in self.results:
            report.append(f"\n## {result.test_name}")
            report.append(f"- Duration: {result.duration_seconds:.2f}s")
            report.append(f"- Throughput: {result.throughput_rps:.2f} req/s")
            report.append(f"- Error Rate: {result.error_rate:.2%}")
            report.append("- Latencies (ms):")
            report.append(f"  - Average: {result.avg_latency_ms:.2f}")
            report.append(f"  - P50: {result.p50_latency_ms:.2f}")
            report.append(f"  - P95: {result.p95_latency_ms:.2f}")
            report.append(f"  - P99: {result.p99_latency_ms:.2f}")

        # Add resource metrics if available
        resources = self.get_resource_metrics()
        if resources:
            report.append("\n## Resource Usage")
            for metric, value in resources.get("resources", {}).items():
                report.append(f"- {metric}: {value:.2f}")

        return "\n".join(report)


async def main():
    """Main function for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description="SuperAGI Performance Testing")
    parser.add_argument("--endpoint", required=True, help="SuperAGI endpoint URL")
    parser.add_argument("--prometheus", help="Prometheus endpoint URL")
    parser.add_argument(
        "--test",
        choices=["all", "agent", "memory", "concurrent"],
        default="all",
        help="Test to run",
    )
    parser.add_argument("--requests", type=int, default=100, help="Number of requests")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--output", help="Output report file")

    args = parser.parse_args()

    tester = PerformanceTester(superagi_endpoint=args.endpoint, prometheus_endpoint=args.prometheus)

    # Run tests
    if args.test in ["all", "agent"]:
        await tester.test_agent_execution(num_requests=args.requests, concurrent_requests=args.concurrent)

    if args.test in ["all", "memory"]:
        await tester.test_memory_operations(num_operations=args.requests, concurrent_operations=args.concurrent)

    if args.test in ["all", "concurrent"]:
        await tester.test_concurrent_agents(num_agents=5, tasks_per_agent=args.requests // 5)

    # Generate report
    report = tester.generate_report()
    print("\n" + report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
