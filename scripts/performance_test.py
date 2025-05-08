#!/usr/bin/env python3
"""
Performance testing script for AI Orchestra API.

This script tests the performance of the API by sending multiple requests
and measuring response times and throughput.
"""

import asyncio
import time
import statistics
import argparse
import json
from typing import Dict, Any, List, Optional
import aiohttp


async def test_endpoint(
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    num_requests: int = 100,
    concurrency: int = 10
) -> Dict[str, float]:
    """
    Test an endpoint by sending multiple requests and measuring performance.
    
    Args:
        url: The URL of the endpoint to test
        payload: The JSON payload to send
        headers: The HTTP headers to include
        num_requests: The total number of requests to send
        concurrency: The number of concurrent requests
        
    Returns:
        A dictionary containing performance metrics
    """
    async def make_request() -> float:
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                await response.json()
                return time.time() - start_time
    
    tasks = []
    for _ in range(num_requests):
        tasks.append(asyncio.create_task(make_request()))
    
    # Execute in batches to control concurrency
    results = []
    for i in range(0, len(tasks), concurrency):
        batch = tasks[i:i+concurrency]
        batch_results = await asyncio.gather(*batch)
        results.extend(batch_results)
    
    return {
        "min": min(results),
        "max": max(results),
        "avg": statistics.mean(results),
        "p50": statistics.median(results),
        "p95": statistics.quantiles(results, n=20)[18],
        "p99": statistics.quantiles(results, n=100)[98],
        "requests_per_second": num_requests / sum(results)
    }


async def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Performance test for AI Orchestra API')
    parser.add_argument('--url', required=True, help='API endpoint URL')
    parser.add_argument('--requests', type=int, default=100, help='Number of requests')
    parser.add_argument('--concurrency', type=int, default=10, help='Concurrency level')
    parser.add_argument('--payload', type=str, default='{}', help='JSON payload')
    args = parser.parse_args()
    
    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON payload: {args.payload}")
        return
    
    headers = {"Content-Type": "application/json"}
    
    print(f"Running performance test with {args.requests} requests at concurrency {args.concurrency}...")
    results = await test_endpoint(args.url, payload, headers, args.requests, args.concurrency)
    
    print("\nPerformance Results:")
    print(f"Min response time: {results['min']:.4f}s")
    print(f"Max response time: {results['max']:.4f}s")
    print(f"Average response time: {results['avg']:.4f}s")
    print(f"Median response time (p50): {results['p50']:.4f}s")
    print(f"95th percentile (p95): {results['p95']:.4f}s")
    print(f"99th percentile (p99): {results['p99']:.4f}s")
    print(f"Requests per second: {results['requests_per_second']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())