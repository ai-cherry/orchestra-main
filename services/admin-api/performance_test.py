#!/usr/bin/env python3
"""
Performance testing script for the AI Orchestra Admin API.

This script runs a series of load tests against the Admin API endpoints to
measure performance metrics. It's designed to establish baseline performance
and verify improvements after optimization changes.
"""
import asyncio
import time
import json
import statistics
import argparse
import logging
from typing import Dict, List, Any, Optional
import aiohttp
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define test parameters
DEFAULT_CONCURRENCY = 10
DEFAULT_ITERATIONS = 100
DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_ENDPOINTS = [
    "/api/v1/system/health",
    "/api/v1/system/stats",
    "/api/v1/agents",
    "/api/v1/memory/status"
]

class PerformanceTester:
    """Performance testing tool for the Admin API."""
    
    def __init__(
        self, 
        base_url: str, 
        endpoints: List[str], 
        concurrency: int, 
        iterations: int
    ):
        """
        Initialize the performance tester.
        
        Args:
            base_url: Base URL of the Admin API
            endpoints: List of endpoints to test
            concurrency: Number of concurrent requests
            iterations: Number of iterations per endpoint
        """
        self.base_url = base_url
        self.endpoints = endpoints
        self.concurrency = concurrency
        self.iterations = iterations
        self.results: Dict[str, List[float]] = {endpoint: [] for endpoint in endpoints}
        self.errors: Dict[str, int] = {endpoint: 0 for endpoint in endpoints}
        
    async def run_test(self) -> None:
        """Run the performance test across all endpoints."""
        logger.info(f"Starting performance test with concurrency={self.concurrency}, "
                   f"iterations={self.iterations}")
        
        start_time = time.time()
        
        for endpoint in self.endpoints:
            logger.info(f"Testing endpoint: {endpoint}")
            await self._test_endpoint(endpoint)
            
        total_time = time.time() - start_time
        logger.info(f"Total test time: {total_time:.2f} seconds")
        
        # Generate report
        await self.generate_report()
        
    async def _test_endpoint(self, endpoint: str) -> None:
        """
        Test a specific endpoint with concurrent requests.
        
        Args:
            endpoint: API endpoint to test
        """
        url = f"{self.base_url}{endpoint}"
        
        # Create a session for connection pooling
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(self.iterations):
                tasks.append(self._make_request(session, url, endpoint))
                
            # Run requests in batches for controlled concurrency
            for i in range(0, len(tasks), self.concurrency):
                batch = tasks[i:i+self.concurrency]
                await asyncio.gather(*batch)
    
    async def _make_request(
        self, 
        session: aiohttp.ClientSession, 
        url: str, 
        endpoint: str
    ) -> None:
        """
        Make a single request and record the response time.
        
        Args:
            session: aiohttp session
            url: Full URL to request
            endpoint: Endpoint name for results tracking
        """
        start_time = time.time()
        try:
            async with session.get(url) as response:
                await response.text()
                if response.status >= 400:
                    self.errors[endpoint] += 1
                    logger.warning(f"Error {response.status} for {url}")
                else:
                    elapsed = time.time() - start_time
                    self.results[endpoint].append(elapsed)
        except Exception as e:
            self.errors[endpoint] += 1
            logger.error(f"Exception during request to {url}: {str(e)}")
    
    def calculate_metrics(self, times: List[float]) -> Dict[str, float]:
        """
        Calculate performance metrics from a list of response times.
        
        Args:
            times: List of response times in seconds
            
        Returns:
            Dictionary of metrics
        """
        if not times:
            return {
                "min": 0,
                "max": 0,
                "avg": 0,
                "median": 0,
                "p95": 0,
                "p99": 0,
                "std_dev": 0,
                "requests_per_second": 0
            }
        
        sorted_times = sorted(times)
        
        return {
            "min": min(times),
            "max": max(times),
            "avg": statistics.mean(times),
            "median": statistics.median(times),
            "p95": sorted_times[int(len(sorted_times) * 0.95)],
            "p99": sorted_times[int(len(sorted_times) * 0.99)],
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "requests_per_second": 1 / statistics.mean(times)
        }
    
    async def generate_report(self) -> None:
        """Generate a performance report with metrics and charts."""
        # Create a results dataframe
        data = []
        
        for endpoint, times in self.results.items():
            if times:
                metrics = self.calculate_metrics(times)
                success_rate = 100 * (1 - self.errors[endpoint] / self.iterations)
                
                data.append({
                    "Endpoint": endpoint,
                    "Requests": len(times),
                    "Errors": self.errors[endpoint],
                    "Success Rate": f"{success_rate:.2f}%",
                    "Min (ms)": f"{metrics['min'] * 1000:.2f}",
                    "Max (ms)": f"{metrics['max'] * 1000:.2f}",
                    "Avg (ms)": f"{metrics['avg'] * 1000:.2f}",
                    "Median (ms)": f"{metrics['median'] * 1000:.2f}",
                    "95th % (ms)": f"{metrics['p95'] * 1000:.2f}",
                    "99th % (ms)": f"{metrics['p99'] * 1000:.2f}",
                    "Std Dev (ms)": f"{metrics['std_dev'] * 1000:.2f}",
                    "Req/sec": f"{metrics['requests_per_second']:.2f}"
                })
        
        df = pd.DataFrame(data)
        
        # Save results to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"performance_results_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        logger.info(f"Results saved to {csv_filename}")
        
        # Print results table
        print("\nPerformance Test Results:\n")
        print(df.to_string(index=False))
        
        # Generate charts
        self._generate_charts(timestamp)
    
    def _generate_charts(self, timestamp: str) -> None:
        """
        Generate performance charts.
        
        Args:
            timestamp: Timestamp for file naming
        """
        plt.figure(figsize=(12, 8))
        
        # Response time comparison
        avg_times = []
        labels = []
        
        for endpoint, times in self.results.items():
            if times:
                avg_times.append(statistics.mean(times) * 1000)  # Convert to ms
                labels.append(endpoint)
        
        plt.bar(labels, avg_times)
        plt.title('Average Response Time by Endpoint')
        plt.ylabel('Response Time (ms)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        chart_filename = f"performance_chart_{timestamp}.png"
        plt.savefig(chart_filename)
        logger.info(f"Chart saved to {chart_filename}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='API Performance Testing Tool')
    parser.add_argument('--base-url', default=DEFAULT_BASE_URL,
                        help=f'Base URL of the API (default: {DEFAULT_BASE_URL})')
    parser.add_argument('--endpoints', nargs='+', default=DEFAULT_ENDPOINTS,
                        help='List of endpoints to test')
    parser.add_argument('--concurrency', type=int, default=DEFAULT_CONCURRENCY,
                        help=f'Number of concurrent requests (default: {DEFAULT_CONCURRENCY})')
    parser.add_argument('--iterations', type=int, default=DEFAULT_ITERATIONS,
                        help=f'Number of iterations per endpoint (default: {DEFAULT_ITERATIONS})')
    return parser.parse_args()

async def main():
    """Main entry point for the performance test script."""
    args = parse_args()
    
    tester = PerformanceTester(
        base_url=args.base_url,
        endpoints=args.endpoints,
        concurrency=args.concurrency,
        iterations=args.iterations
    )
    
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main())
