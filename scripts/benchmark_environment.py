#!/usr/bin/env python3
"""
GitHub Codespaces Environment Benchmarking Tool

This script collects and records performance metrics from the current
GitHub Codespaces environment to establish baseline metrics for the
GCP Workstations migration.

Usage:
    python benchmark_environment.py [--output OUTPUT_FILE]
"""

import argparse
import datetime
import json
import os
import platform
import subprocess
import sys
import time
from typing import Dict, List, Any, Optional, Tuple

# Define measurement constants
NUM_ITERATIONS = 3  # Number of iterations for averaging measurements
REPO_URL = "https://github.com/username/ai-orchestra.git"  # Replace with actual repo URL
TEST_BUILD_CMD = "cd ai-orchestra && python -m pytest -xvs tests/performance"  # Adjust as needed


class EnvironmentBenchmark:
    """Collect and analyze performance metrics of the current development environment."""
    
    def __init__(self, output_file: str = "environment_benchmark_results.json"):
        """
        Initialize the benchmark tool.
        
        Args:
            output_file: Path to save benchmark results
        """
        self.output_file = output_file
        self.results: Dict[str, Any] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "system_info": {},
            "metrics": {},
        }
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """
        Run all benchmark tests and collect results.
        
        Returns:
            Dictionary containing all benchmark results
        """
        print("Starting environment benchmarks...")
        
        # Collect system information
        self.collect_system_info()
        
        # Run performance tests
        self.measure_startup_time()
        self.measure_git_operations()
        self.measure_build_performance()
        self.measure_extension_load_times()
        self.measure_file_operations()
        
        # Save results
        self.save_results()
        
        print(f"Benchmarks completed. Results saved to {self.output_file}")
        return self.results
    
    def collect_system_info(self) -> None:
        """Collect basic system information about the environment."""
        print("Collecting system information...")
        
        try:
            self.results["system_info"] = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "processor": platform.processor(),
                "cpu_count": os.cpu_count(),
                "memory_info": self._get_memory_info(),
                "disk_info": self._get_disk_info(),
                "environment_variables": {
                    k: v for k, v in os.environ.items() 
                    if k.startswith(("GITHUB_", "CODESPACES_", "VSCODE_"))
                },
                "installed_extensions": self._get_vscode_extensions(),
            }
        except Exception as e:
            print(f"Error collecting system info: {e}")
            self.results["system_info"] = {"error": str(e)}
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get system memory information."""
        # This is a simplified version - actual implementation might use psutil
        try:
            if platform.system() == "Linux":
                with open("/proc/meminfo") as f:
                    meminfo = f.read()
                
                # Extract total memory
                for line in meminfo.split("\n"):
                    if "MemTotal" in line:
                        return {"total": line.split()[1]}
            
            return {"note": "Memory info collection not implemented for this platform"}
        except Exception as e:
            return {"error": str(e)}
    
    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk space information."""
        try:
            total, used, free = self._get_disk_usage(".")
            return {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_disk_usage(self, path: str) -> Tuple[int, int, int]:
        """Get disk usage statistics for the specified path."""
        if platform.system() == "Windows":
            # Windows implementation would go here
            raise NotImplementedError("Windows disk usage not implemented")
        else:
            # Unix/Linux/MacOS
            st = os.statvfs(path)
            total = st.f_blocks * st.f_frsize
            free = st.f_bfree * st.f_frsize
            used = total - free
            return total, used, free
    
    def _get_vscode_extensions(self) -> List[str]:
        """Get list of installed VS Code extensions."""
        try:
            result = subprocess.run(
                ["code", "--list-extensions"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")
            return []
        except Exception:
            return []
    
    def measure_startup_time(self) -> None:
        """Measure the startup time of the environment."""
        print("Measuring startup time is not directly possible from within the environment.")
        print("This metric should be collected externally during environment creation.")
        
        self.results["metrics"]["startup_time"] = {
            "note": "Startup time measurement requires external timing during environment creation",
            "manual_measurement_instructions": (
                "Time from clicking 'Open in Codespace' to the IDE being fully ready"
            )
        }
    
    def measure_git_operations(self) -> None:
        """Benchmark common git operations."""
        print("Measuring git operation performance...")
        
        git_metrics = {}
        
        # Measure git clone time
        print("  Measuring git clone performance...")
        try:
            # Create a temporary directory for clone tests
            tmp_dir = "/tmp/benchmark_git_clone"
            if os.path.exists(tmp_dir):
                subprocess.run(["rm", "-rf", tmp_dir], check=False)
            os.makedirs(tmp_dir, exist_ok=True)
            
            # Measure clone time
            start_time = time.time()
            clone_result = subprocess.run(
                ["git", "clone", "--depth", "1", REPO_URL, tmp_dir],
                capture_output=True,
                text=True,
                check=False
            )
            clone_time = time.time() - start_time
            
            git_metrics["clone"] = {
                "time_seconds": clone_time,
                "success": clone_result.returncode == 0,
                "notes": "Shallow clone with depth=1"
            }
            
            # Clean up
            subprocess.run(["rm", "-rf", tmp_dir], check=False)
            
        except Exception as e:
            git_metrics["clone"] = {"error": str(e)}
        
        # Measure git status, add, commit operations on current repo
        ops = ["status", "add --dry-run .", "log -n 10"]
        for op in ops:
            op_name = op.split()[0]
            print(f"  Measuring git {op_name} performance...")
            
            try:
                # Run multiple iterations
                times = []
                for _ in range(NUM_ITERATIONS):
                    start_time = time.time()
                    subprocess.run(["git"] + op.split(), 
                                   capture_output=True, 
                                   check=False)
                    times.append(time.time() - start_time)
                
                git_metrics[op_name] = {
                    "avg_time_seconds": sum(times) / len(times),
                    "min_time_seconds": min(times),
                    "max_time_seconds": max(times),
                    "iterations": len(times)
                }
            except Exception as e:
                git_metrics[op_name] = {"error": str(e)}
        
        self.results["metrics"]["git_operations"] = git_metrics
    
    def measure_build_performance(self) -> None:
        """Measure build and test execution performance."""
        print("Measuring build performance...")
        
        try:
            # Run the test build command multiple times
            times = []
            for i in range(NUM_ITERATIONS):
                print(f"  Build test iteration {i+1}/{NUM_ITERATIONS}...")
                start_time = time.time()
                result = subprocess.run(
                    TEST_BUILD_CMD, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                times.append(time.time() - start_time)
            
            self.results["metrics"]["build_performance"] = {
                "command": TEST_BUILD_CMD,
                "avg_time_seconds": sum(times) / len(times),
                "min_time_seconds": min(times),
                "max_time_seconds": max(times),
                "success": result.returncode == 0,
                "iterations": len(times)
            }
        except Exception as e:
            self.results["metrics"]["build_performance"] = {"error": str(e)}
    
    def measure_extension_load_times(self) -> None:
        """
        Measure extension load times.
        Note: This is approximated as direct measurement requires VS Code API access.
        """
        print("Extension load times require VS Code API access.")
        print("Recording installed extensions for reference only.")
        
        self.results["metrics"]["extension_load_times"] = {
            "note": "Extension load time measurement requires VS Code API access",
            "manual_measurement_instructions": (
                "Use the Command Palette to run 'Developer: Show Running Extensions'"
            )
        }
    
    def measure_file_operations(self) -> None:
        """Benchmark file I/O operations."""
        print("Measuring file I/O performance...")
        
        file_metrics = {}
        test_dir = "/tmp/file_benchmark"
        test_file = f"{test_dir}/test_file.dat"
        
        try:
            # Create test directory
            os.makedirs(test_dir, exist_ok=True)
            
            # Test file sizes
            sizes_mb = [1, 10, 100]
            
            for size_mb in sizes_mb:
                size_bytes = size_mb * 1024 * 1024
                print(f"  Testing {size_mb}MB file I/O...")
                
                # Write test
                write_times = []
                for _ in range(NUM_ITERATIONS):
                    start_time = time.time()
                    with open(test_file, 'wb') as f:
                        f.write(os.urandom(size_bytes))
                    write_times.append(time.time() - start_time)
                
                # Read test
                read_times = []
                for _ in range(NUM_ITERATIONS):
                    start_time = time.time()
                    with open(test_file, 'rb') as f:
                        data = f.read()
                    read_times.append(time.time() - start_time)
                
                file_metrics[f"{size_mb}mb"] = {
                    "write": {
                        "avg_time_seconds": sum(write_times) / len(write_times),
                        "throughput_mbps": size_mb / (sum(write_times) / len(write_times))
                    },
                    "read": {
                        "avg_time_seconds": sum(read_times) / len(read_times),
                        "throughput_mbps": size_mb / (sum(read_times) / len(read_times))
                    },
                    "iterations": NUM_ITERATIONS
                }
            
            # Clean up
            subprocess.run(["rm", "-rf", test_dir], check=False)
            
        except Exception as e:
            file_metrics["error"] = str(e)
        
        self.results["metrics"]["file_operations"] = file_metrics
    
    def save_results(self) -> None:
        """Save benchmark results to a JSON file."""
        with open(self.output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"Results saved to {self.output_file}")


def main() -> None:
    """Main function to run the benchmark tool."""
    parser = argparse.ArgumentParser(description="GitHub Codespaces Environment Benchmarking Tool")
    parser.add_argument("--output", 
                        default="environment_benchmark_results.json",
                        help="Path to save benchmark results (default: environment_benchmark_results.json)")
    
    args = parser.parse_args()
    
    benchmark = EnvironmentBenchmark(output_file=args.output)
    benchmark.run_all_benchmarks()


if __name__ == "__main__":
    main()