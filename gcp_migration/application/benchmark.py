"""
Benchmark service for measuring performance metrics across environments.

This module provides implementation of the IBenchmarkService interface
for benchmarking GitHub Codespaces and GCP Workstations environments.
"""

import asyncio
import json
import os
import platform
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

from gcp_migration.config.settings import settings
from gcp_migration.domain.exceptions import BenchmarkError
from gcp_migration.domain.interfaces import IBenchmarkService
from gcp_migration.domain.models import BenchmarkResult, PerformanceMetric
from gcp_migration.utils.errors import async_wrap_exceptions, error_context
from gcp_migration.utils.logging import get_logger


logger = get_logger(__name__)


class BenchmarkService(IBenchmarkService):
    """
    Service for benchmarking GitHub Codespaces and GCP Workstations environments.
    
    This service measures various performance metrics including:
    - Startup time (approximated)
    - Git operations
    - File I/O
    - Build performance
    - Network latency to GCP services
    """
    
    def __init__(self):
        """Initialize the benchmark service."""
        self._temp_dir = Path(tempfile.mkdtemp(prefix="benchmark_"))
        logger.info(f"Created temporary directory for benchmarks: {self._temp_dir}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        self._cleanup()
        
    def __del__(self):
        """Ensure cleanup on object destruction."""
        self._cleanup()
        
    def _cleanup(self):
        """Clean up any temporary resources."""
        if hasattr(self, '_temp_dir') and self._temp_dir.exists():
            logger.debug(f"Cleaning up temporary directory: {self._temp_dir}")
            shutil.rmtree(self._temp_dir, ignore_errors=True)
    
    @async_wrap_exceptions(BenchmarkError, (subprocess.SubprocessError, OSError, ValueError), 
                         "Failed to benchmark GitHub Codespaces")
    async def benchmark_github_codespaces(self) -> BenchmarkResult:
        """
        Benchmark the GitHub Codespaces environment.
        
        Returns:
            The benchmark results for GitHub Codespaces
            
        Raises:
            BenchmarkError: If benchmarking fails
        """
        logger.info("Starting GitHub Codespaces benchmarks")
        
        # Create a result object
        result = BenchmarkResult(
            environment_type="github_codespaces",
            timestamp=datetime.now(),
            system_info=await self._collect_system_info(),
            metrics=[]
        )
        
        # Run benchmarks
        await self._run_benchmarks(result)
        
        logger.info(f"Completed GitHub Codespaces benchmarks with {len(result.metrics)} metrics")
        return result
    
    @async_wrap_exceptions(BenchmarkError, (subprocess.SubprocessError, OSError, ValueError),
                         "Failed to benchmark GCP Workstation")
    async def benchmark_gcp_workstation(self, workstation_name: str) -> BenchmarkResult:
        """
        Benchmark a GCP Workstation environment.
        
        Args:
            workstation_name: The name of the GCP Workstation
            
        Returns:
            The benchmark results for the GCP Workstation
            
        Raises:
            BenchmarkError: If benchmarking fails
            ResourceNotFoundError: If the workstation doesn't exist
        """
        logger.info(f"Starting GCP Workstation benchmarks for: {workstation_name}")
        
        # Create a result object
        result = BenchmarkResult(
            environment_type="gcp_workstation",
            timestamp=datetime.now(),
            system_info=await self._collect_system_info(),
            metrics=[]
        )
        
        # Add workstation name to system info
        result.system_info["workstation_name"] = workstation_name
        
        # Run benchmarks
        await self._run_benchmarks(result)
        
        logger.info(f"Completed GCP Workstation benchmarks with {len(result.metrics)} metrics")
        return result
    
    async def compare_environments(
        self, github_benchmark: BenchmarkResult, gcp_benchmark: BenchmarkResult
    ) -> Dict[str, float]:
        """
        Compare benchmark results between GitHub Codespaces and GCP Workstations.
        
        Args:
            github_benchmark: Benchmark results for GitHub Codespaces
            gcp_benchmark: Benchmark results for GCP Workstations
            
        Returns:
            Dictionary mapping metric names to improvement ratios
        """
        logger.info("Comparing benchmark results between environments")
        
        # Create comparison dictionary
        comparison: Dict[str, float] = {}
        
        # List of metrics present in both environments
        github_metrics = {m.name: m for m in github_benchmark.metrics}
        gcp_metrics = {m.name: m for m in gcp_benchmark.metrics}
        
        # Compare common metrics
        for name, github_metric in github_metrics.items():
            if name in gcp_metrics:
                gcp_metric = gcp_metrics[name]
                
                # Skip if units don't match
                if github_metric.unit != gcp_metric.unit:
                    logger.warning(f"Units don't match for metric {name}: "
                                  f"{github_metric.unit} vs {gcp_metric.unit}")
                    continue
                
                # Calculate improvement ratio
                # Higher values are better for rates (ops/sec)
                if name.endswith("_rate") or name.endswith("_throughput") or github_metric.unit.endswith("/s"):
                    # Higher is better
                    if github_metric.value > 0:
                        ratio = gcp_metric.value / github_metric.value
                    else:
                        ratio = float('inf') if gcp_metric.value > 0 else 1.0
                else:
                    # Lower is better (time, latency)
                    if gcp_metric.value > 0:
                        ratio = github_metric.value / gcp_metric.value
                    else:
                        ratio = float('inf') if github_metric.value > 0 else 1.0
                
                comparison[name] = ratio
                
                # Log the comparison
                if ratio > 1.0:
                    logger.info(f"Metric {name}: GCP Workstation is {ratio:.2f}x faster")
                else:
                    logger.info(f"Metric {name}: GitHub Codespaces is {1/ratio:.2f}x faster")
        
        return comparison
    
    async def _collect_system_info(self) -> Dict[str, Any]:
        """
        Collect system information.
        
        Returns:
            Dictionary with system information
        """
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "hostname": platform.node(),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Try to get memory info on Linux
        if platform.system() == "Linux":
            try:
                with open("/proc/meminfo") as f:
                    meminfo = f.read()
                
                # Parse memory info
                mem_total = None
                for line in meminfo.splitlines():
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1])
                        break
                
                if mem_total:
                    info["memory_kb"] = mem_total
                    info["memory_gb"] = round(mem_total / 1024 / 1024, 2)
            except Exception as e:
                logger.warning(f"Failed to get memory info: {e}")
        
        # Get disk info
        try:
            total, used, free = shutil.disk_usage("/")
            info["disk_total_gb"] = round(total / 1024 / 1024 / 1024, 2)
            info["disk_used_gb"] = round(used / 1024 / 1024 / 1024, 2)
            info["disk_free_gb"] = round(free / 1024 / 1024 / 1024, 2)
        except Exception as e:
            logger.warning(f"Failed to get disk info: {e}")
        
        # Get environment variables related to the benchmark
        env_keys = ['GITHUB_CODESPACES', 'CODESPACE_NAME', 'CLOUD_SHELL',
                   'DEVSHELL_PROJECT_ID', 'GCE_METADATA_HOST']
        for key in env_keys:
            if key in os.environ:
                info[f"env_{key}"] = os.environ[key]
        
        return info
    
    async def _run_benchmarks(self, result: BenchmarkResult) -> None:
        """
        Run all benchmarks and add metrics to the result.
        
        Args:
            result: The benchmark result to update
        """
        # Run benchmarks in parallel for efficiency
        tasks = []
        
        # Add benchmark tasks
        tasks.append(self._benchmark_file_io(result))
        tasks.append(self._benchmark_git_operations(result))
        tasks.append(self._benchmark_network_latency(result))
        tasks.append(self._benchmark_cpu_performance(result))
        
        # Run all benchmarks
        await asyncio.gather(*tasks)
    
    async def _benchmark_file_io(self, result: BenchmarkResult) -> None:
        """
        Benchmark file I/O operations.
        
        Args:
            result: The benchmark result to update
        """
        with error_context(BenchmarkError, "Failed to benchmark file I/O"):
            logger.debug("Benchmarking file I/O")
            
            # Test file sizes (1MB, 10MB, 100MB)
            sizes_mb = [1, 10, 100]
            iterations = settings.benchmark_iterations
            
            for size_mb in sizes_mb:
                size_bytes = size_mb * 1024 * 1024
                test_file = self._temp_dir / f"test_{size_mb}mb.dat"
                
                # Test sequential write
                write_times = []
                for i in range(iterations):
                    start_time = time.time()
                    with open(test_file, 'wb') as f:
                        f.write(os.urandom(size_bytes))
                    write_times.append(time.time() - start_time)
                
                avg_write_time = sum(write_times) / len(write_times)
                write_throughput = size_mb / avg_write_time  # MB/s
                
                result.add_metric(
                    name=f"file_write_{size_mb}mb",
                    value=avg_write_time,
                    unit="seconds",
                    metadata={"file_size_mb": size_mb, "operation": "write"}
                )
                
                result.add_metric(
                    name=f"file_write_throughput_{size_mb}mb",
                    value=write_throughput,
                    unit="MB/s",
                    metadata={"file_size_mb": size_mb, "operation": "write"}
                )
                
                # Test sequential read
                read_times = []
                for i in range(iterations):
                    start_time = time.time()
                    with open(test_file, 'rb') as f:
                        _ = f.read()
                    read_times.append(time.time() - start_time)
                
                avg_read_time = sum(read_times) / len(read_times)
                read_throughput = size_mb / avg_read_time  # MB/s
                
                result.add_metric(
                    name=f"file_read_{size_mb}mb",
                    value=avg_read_time,
                    unit="seconds",
                    metadata={"file_size_mb": size_mb, "operation": "read"}
                )
                
                result.add_metric(
                    name=f"file_read_throughput_{size_mb}mb",
                    value=read_throughput,
                    unit="MB/s",
                    metadata={"file_size_mb": size_mb, "operation": "read"}
                )
                
                # Clean up
                if test_file.exists():
                    test_file.unlink()
    
    async def _benchmark_git_operations(self, result: BenchmarkResult) -> None:
        """
        Benchmark Git operations.
        
        Args:
            result: The benchmark result to update
        """
        with error_context(BenchmarkError, "Failed to benchmark Git operations"):
            logger.debug("Benchmarking Git operations")
            
            git_dir = self._temp_dir / "git_test"
            git_dir.mkdir(exist_ok=True)
            
            # Initialize git repo
            await self._run_command("git init", cwd=git_dir)
            
            # Create test file
            test_file = git_dir / "test.txt"
            with open(test_file, 'w') as f:
                f.write("Test content\n" * 1000)
            
            # Benchmark git add
            start_time = time.time()
            await self._run_command("git add .", cwd=git_dir)
            add_time = time.time() - start_time
            
            result.add_metric(
                name="git_add",
                value=add_time,
                unit="seconds",
                metadata={"operation": "git add", "file_count": 1}
            )
            
            # Benchmark git commit
            start_time = time.time()
            await self._run_command('git config user.email "test@example.com"', cwd=git_dir)
            await self._run_command('git config user.name "Test User"', cwd=git_dir)
            await self._run_command('git commit -m "Test commit"', cwd=git_dir)
            commit_time = time.time() - start_time
            
            result.add_metric(
                name="git_commit",
                value=commit_time,
                unit="seconds",
                metadata={"operation": "git commit", "file_count": 1}
            )
            
            # Create more test files for status benchmark
            for i in range(100):
                with open(git_dir / f"file_{i}.txt", 'w') as f:
                    f.write(f"Content for file {i}\n" * 10)
            
            # Benchmark git status
            start_time = time.time()
            await self._run_command("git status", cwd=git_dir)
            status_time = time.time() - start_time
            
            result.add_metric(
                name="git_status",
                value=status_time,
                unit="seconds",
                metadata={"operation": "git status", "file_count": 101}
            )
    
    async def _benchmark_network_latency(self, result: BenchmarkResult) -> None:
        """
        Benchmark network latency to GCP services.
        
        Args:
            result: The benchmark result to update
        """
        with error_context(BenchmarkError, "Failed to benchmark network latency"):
            logger.debug("Benchmarking network latency")
            
            # List of GCP endpoints to test
            endpoints = [
                # GCP service endpoints
                "storage.googleapis.com",
                "firestore.googleapis.com",
                "secretmanager.googleapis.com",
                f"{settings.gcp_region}-aiplatform.googleapis.com",
                
                # General internet endpoints for reference
                "google.com",
                "github.com",
            ]
            
            for endpoint in endpoints:
                # Use TCP ping (measuring time to establish a connection)
                try:
                    tcp_latencies = []
                    for _ in range(5):  # 5 measurements
                        start_time = time.time()
                        proc = await asyncio.create_subprocess_exec(
                            "nc", "-z", "-w", "5", endpoint, "443",
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await proc.communicate()
                        tcp_latencies.append((time.time() - start_time) * 1000)  # Convert to ms
                    
                    # Filter out any failed attempts (negative or very long times)
                    valid_latencies = [lat for lat in tcp_latencies if 0 < lat < 5000]
                    
                    if valid_latencies:
                        avg_latency = sum(valid_latencies) / len(valid_latencies)
                        result.add_metric(
                            name=f"network_latency_{endpoint}",
                            value=avg_latency,
                            unit="ms",
                            metadata={"endpoint": endpoint, "protocol": "tcp"}
                        )
                except Exception as e:
                    logger.warning(f"Failed to measure TCP latency to {endpoint}: {e}")
            
            # Also measure HTTPS latency with curl for more realistic app performance
            for endpoint in endpoints:
                try:
                    url = f"https://{endpoint}/"
                    curl_output = await self._run_command(
                        f"curl -o /dev/null -s -w '%{{time_connect}} %{{time_starttransfer}} %{{time_total}}' {url}"
                    )
                    
                    # Parse curl output (connect time, time to first byte, total time)
                    parts = curl_output.strip().split()
                    if len(parts) == 3:
                        connect_time, ttfb, total_time = map(float, parts)
                        
                        # Convert to milliseconds
                        connect_time *= 1000
                        ttfb *= 1000
                        total_time *= 1000
                        
                        result.add_metric(
                            name=f"https_connect_{endpoint}",
                            value=connect_time,
                            unit="ms",
                            metadata={"endpoint": endpoint, "protocol": "https"}
                        )
                        
                        result.add_metric(
                            name=f"https_ttfb_{endpoint}",
                            value=ttfb,
                            unit="ms",
                            metadata={"endpoint": endpoint, "protocol": "https"}
                        )
                        
                        result.add_metric(
                            name=f"https_total_{endpoint}",
                            value=total_time,
                            unit="ms",
                            metadata={"endpoint": endpoint, "protocol": "https"}
                        )
                except Exception as e:
                    logger.warning(f"Failed to measure HTTPS latency to {endpoint}: {e}")
    
    async def _benchmark_cpu_performance(self, result: BenchmarkResult) -> None:
        """
        Benchmark CPU performance.
        
        Args:
            result: The benchmark result to update
        """
        with error_context(BenchmarkError, "Failed to benchmark CPU performance"):
            logger.debug("Benchmarking CPU performance")
            
            # Simple CPU benchmark: matrix multiplication
            code = """
import numpy as np
import time

def matrix_mult_benchmark(size, iterations):
    times = []
    for _ in range(iterations):
        a = np.random.rand(size, size)
        b = np.random.rand(size, size)
        
        start = time.time()
        c = a @ b  # Matrix multiplication
        times.append(time.time() - start)
    
    return sum(times) / iterations

# Run the benchmark with different matrix sizes
sizes = [500, 1000, 2000]
results = {}

for size in sizes:
    avg_time = matrix_mult_benchmark(size, 3)
    results[size] = avg_time
    print(f"{size},{avg_time}")
"""
            
            # Save to a temporary file
            benchmark_file = self._temp_dir / "cpu_benchmark.py"
            with open(benchmark_file, 'w') as f:
                f.write(code)
            
            # Run the benchmark
            output = await self._run_command(f"python {benchmark_file}")
            
            # Parse results
            for line in output.strip().split('\n'):
                if ',' in line:
                    size, time_val = line.split(',')
                    size = int(size)
                    time_val = float(time_val)
                    
                    result.add_metric(
                        name=f"matrix_mult_{size}",
                        value=time_val,
                        unit="seconds",
                        metadata={"matrix_size": size, "operation": "matrix_multiplication"}
                    )
                    
                    # Calculate operations per second (approximate)
                    # For matrix multiplication: ~2*size^3 operations
                    ops = 2 * (size ** 3)
                    ops_per_second = ops / time_val if time_val > 0 else 0
                    
                    result.add_metric(
                        name=f"matrix_mult_rate_{size}",
                        value=ops_per_second,
                        unit="ops/sec",
                        metadata={"matrix_size": size, "operation": "matrix_multiplication"}
                    )
    
    async def _run_command(self, cmd: str, cwd: Optional[Union[str, Path]] = None) -> str:
        """
        Run a shell command asynchronously.
        
        Args:
            cmd: The command to run
            cwd: Working directory
            
        Returns:
            Command output
            
        Raises:
            subprocess.SubprocessError: If the command fails
        """
        logger.debug(f"Running command: {cmd}")
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise subprocess.SubprocessError(
                f"Command '{cmd}' failed with exit code {process.returncode}: {stderr.decode()}"
            )
        
        return stdout.decode().strip()
    
    def save_results(self, result: BenchmarkResult, output_path: Path) -> None:
        """
        Save benchmark results to a file.
        
        Args:
            result: The benchmark results
            output_path: Path to save the results
        """
        # Convert to JSON-serializable dictionary
        result_dict = result.model_dump()
        
        # Convert datetime objects to strings
        result_dict["timestamp"] = result_dict["timestamp"].isoformat()
        for metric in result_dict["metrics"]:
            metric["timestamp"] = metric["timestamp"].isoformat()
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(result_dict, f, indent=2)
            
        logger.info(f"Saved benchmark results to {output_path}")
    
    @classmethod
    def load_results(cls, input_path: Path) -> BenchmarkResult:
        """
        Load benchmark results from a file.
        
        Args:
            input_path: Path to load the results from
            
        Returns:
            The loaded benchmark results
        """
        # Read JSON file
        with open(input_path, 'r') as f:
            result_dict = json.load(f)
        
        # Convert timestamp strings back to datetime
        result_dict["timestamp"] = datetime.fromisoformat(result_dict["timestamp"])
        for metric in result_dict["metrics"]:
            metric["timestamp"] = datetime.fromisoformat(metric["timestamp"])
        
        # Create metrics
        metrics = [PerformanceMetric(**m) for m in result_dict["metrics"]]
        
        # Create benchmark result
        return BenchmarkResult(
            environment_type=result_dict["environment_type"],
            timestamp=result_dict["timestamp"],
            system_info=result_dict["system_info"],
            metrics=metrics
        )