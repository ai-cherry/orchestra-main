#!/usr/bin/env python3
"""
IDE Stress Test for Cloud Workstation Environment

This script performs stress testing on the Cloud Workstation IDE environment to validate
stability and performance under load. It simulates concurrent development activities
using multiple threads and reports performance metrics.

Usage:
    python3 ide_stress_test.py --threads=32 --duration=3600

Requirements:
    - Python 3.8+
    - psutil
    - matplotlib (for visualization)
"""

import argparse
import concurrent.futures
import json
import logging
import os
import random
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import psutil
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "matplotlib", "numpy"])
    import psutil
    import matplotlib.pyplot as plt
    import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ide_stress_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IDE-Stress-Test")

class MetricsCollector:
    """Collects and stores system metrics during the test."""
    
    def __init__(self, interval=1.0):
        self.interval = interval
        self.running = False
        self.metrics = {
            "timestamps": [],
            "cpu_percent": [],
            "memory_percent": [],
            "disk_io_read": [],
            "disk_io_write": [],
            "network_sent": [],
            "network_recv": [],
            "thread_count": [],
        }
        self._thread = None
        self._lock = threading.Lock()
        
    def start(self):
        """Start collecting metrics in background thread."""
        self.running = True
        self._thread = threading.Thread(target=self._collect_metrics)
        self._thread.daemon = True
        self._thread.start()
        logger.info("Started metrics collection")
        
    def stop(self):
        """Stop metrics collection."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Stopped metrics collection")
        
    def _collect_metrics(self):
        """Background thread for metrics collection."""
        disk_io_prev = psutil.disk_io_counters()
        net_io_prev = psutil.net_io_counters()
        
        while self.running:
            start_time = time.time()
            
            # Collect current metrics
            with self._lock:
                # Timestamp
                self.metrics["timestamps"].append(datetime.now().isoformat())
                
                # CPU usage (across all cores)
                self.metrics["cpu_percent"].append(psutil.cpu_percent(interval=0.1))
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics["memory_percent"].append(memory.percent)
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                self.metrics["disk_io_read"].append(disk_io.read_bytes - disk_io_prev.read_bytes)
                self.metrics["disk_io_write"].append(disk_io.write_bytes - disk_io_prev.write_bytes)
                disk_io_prev = disk_io
                
                # Network I/O
                net_io = psutil.net_io_counters()
                self.metrics["network_sent"].append(net_io.bytes_sent - net_io_prev.bytes_sent)
                self.metrics["network_recv"].append(net_io.bytes_recv - net_io_prev.bytes_recv)
                net_io_prev = net_io
                
                # Thread count
                self.metrics["thread_count"].append(threading.active_count())
            
            # Sleep for specified interval
            elapsed = time.time() - start_time
            sleep_time = max(0.0, self.interval - elapsed)
            time.sleep(sleep_time)
    
    def save_metrics(self, filename="ide_stress_metrics.json"):
        """Save collected metrics to file."""
        with open(filename, 'w') as f:
            json.dump(self.metrics, f)
        logger.info(f"Saved metrics to {filename}")
        
    def plot_metrics(self, filename_prefix="ide_stress_metrics"):
        """Generate plots of collected metrics."""
        if not self.metrics["timestamps"]:
            logger.warning("No metrics collected to plot")
            return
            
        # Convert timestamps to seconds since start
        start_time = datetime.fromisoformat(self.metrics["timestamps"][0])
        time_seconds = [(datetime.fromisoformat(ts) - start_time).total_seconds() 
                       for ts in self.metrics["timestamps"]]
        
        plt.figure(figsize=(12, 8))
        
        # CPU and Memory Plot
        plt.subplot(2, 2, 1)
        plt.plot(time_seconds, self.metrics["cpu_percent"], label="CPU %")
        plt.plot(time_seconds, self.metrics["memory_percent"], label="Memory %")
        plt.title("CPU and Memory Usage")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Percentage")
        plt.legend()
        plt.grid(True)
        
        # Disk I/O Plot
        plt.subplot(2, 2, 2)
        plt.plot(time_seconds, self.metrics["disk_io_read"], label="Disk Read (bytes)")
        plt.plot(time_seconds, self.metrics["disk_io_write"], label="Disk Write (bytes)")
        plt.title("Disk I/O")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Bytes")
        plt.legend()
        plt.grid(True)
        
        # Network I/O Plot
        plt.subplot(2, 2, 3)
        plt.plot(time_seconds, self.metrics["network_sent"], label="Network Sent (bytes)")
        plt.plot(time_seconds, self.metrics["network_recv"], label="Network Received (bytes)")
        plt.title("Network I/O")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Bytes")
        plt.legend()
        plt.grid(True)
        
        # Thread Count Plot
        plt.subplot(2, 2, 4)
        plt.plot(time_seconds, self.metrics["thread_count"], label="Thread Count")
        plt.title("Active Threads")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Count")
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(f"{filename_prefix}.png")
        logger.info(f"Saved metrics plots to {filename_prefix}.png")

class IDEStressTest:
    """Manages the IDE stress testing process."""
    
    # Test operations to simulate development activities
    OPERATIONS = [
        "file_create",
        "file_read",
        "file_update",
        "file_delete",
        "git_operations",
        "build_operation",
        "search_operation",
        "format_operation"
    ]
    
    def __init__(self, num_threads=32, duration=3600, test_dir=None):
        """Initialize the stress test with specified parameters."""
        self.num_threads = num_threads
        self.duration = duration  # in seconds
        self.test_dir = test_dir or tempfile.mkdtemp(prefix="ide_stress_test_")
        self.files_created = []
        self.metrics = MetricsCollector()
        self.executor = None
        self._stop_event = threading.Event()
        
        # Create test directory if it doesn't exist
        Path(self.test_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized stress test with {num_threads} threads for {duration} seconds")
        logger.info(f"Test directory: {self.test_dir}")
    
    def setup(self):
        """Set up the test environment."""
        # Create a git repository for testing
        try:
            subprocess.run(["git", "init", self.test_dir], 
                          check=True, capture_output=True)
            # Create initial dummy file and commit
            readme_path = os.path.join(self.test_dir, "README.md")
            with open(readme_path, 'w') as f:
                f.write("# IDE Stress Test\n\nThis repository is used for IDE stress testing.\n")
            
            subprocess.run(["git", "-C", self.test_dir, "add", "."], 
                          check=True, capture_output=True)
            subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "test@example.com"], 
                          check=True, capture_output=True)
            subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test User"], 
                          check=True, capture_output=True)
            subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], 
                          check=True, capture_output=True)
            
            logger.info("Test git repository initialized")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize git repository: {e}")
            logger.error(f"stdout: {e.stdout.decode()}")
            logger.error(f"stderr: {e.stderr.decode()}")
            raise
    
    def run(self):
        """Run the stress test."""
        logger.info(f"Starting stress test with {self.num_threads} threads for {self.duration} seconds")
        
        # Start metrics collection
        self.metrics.start()
        
        # Create thread pool
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads)
        
        # Submit work to thread pool
        futures = []
        start_time = time.time()
        end_time = start_time + self.duration
        
        try:
            while time.time() < end_time and not self._stop_event.is_set():
                # Submit a random operation to simulate IDE workload
                operation = random.choice(self.OPERATIONS)
                futures.append(self.executor.submit(self._perform_operation, operation))
                
                # Sleep a small amount to avoid overwhelming the system with submissions
                time.sleep(0.01)
                
                # Log progress periodically
                elapsed = time.time() - start_time
                if int(elapsed) % 60 == 0 and int(elapsed) > 0:
                    logger.info(f"Test running for {int(elapsed)} seconds. {len(futures)} operations queued.")
            
            # Wait for remaining tasks to complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                except Exception as e:
                    logger.error(f"Operation failed: {e}")
        
        finally:
            # Ensure resources are cleaned up
            self._stop_event.set()
            self.executor.shutdown(wait=False)
            self.metrics.stop()
            
            # Generate reports
            self._generate_report()
            
            logger.info("Stress test completed")
    
    def _perform_operation(self, operation):
        """Perform a simulated IDE operation."""
        if operation == "file_create":
            return self._file_create()
        elif operation == "file_read":
            return self._file_read()
        elif operation == "file_update":
            return self._file_update()
        elif operation == "file_delete":
            return self._file_delete()
        elif operation == "git_operations":
            return self._git_operations()
        elif operation == "build_operation":
            return self._build_operation()
        elif operation == "search_operation":
            return self._search_operation()
        elif operation == "format_operation":
            return self._format_operation()
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def _file_create(self):
        """Create a new file with random content."""
        file_id = random.randint(1, 10000)
        filename = f"file_{file_id}.txt"
        filepath = os.path.join(self.test_dir, filename)
        
        # Create file with random content
        content_size = random.randint(1, 100) * 1024  # 1KB to 100KB
        content = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=content_size))
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        self.files_created.append(filepath)
        return {"operation": "file_create", "filepath": filepath, "size": content_size}
    
    def _file_read(self):
        """Read a file if any exist."""
        if not self.files_created:
            return {"operation": "file_read", "status": "skipped", "reason": "no files"}
        
        filepath = random.choice(self.files_created)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            return {"operation": "file_read", "filepath": filepath, "size": len(content)}
        else:
            return {"operation": "file_read", "status": "failed", "reason": "file not found"}
    
    def _file_update(self):
        """Update a file if any exist."""
        if not self.files_created:
            return {"operation": "file_update", "status": "skipped", "reason": "no files"}
        
        filepath = random.choice(self.files_created)
        if os.path.exists(filepath):
            # Append some content
            append_size = random.randint(1, 10) * 1024  # 1KB to 10KB
            content = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=append_size))
            
            with open(filepath, 'a') as f:
                f.write(content)
            
            return {"operation": "file_update", "filepath": filepath, "append_size": append_size}
        else:
            return {"operation": "file_update", "status": "failed", "reason": "file not found"}
    
    def _file_delete(self):
        """Delete a file if any exist."""
        if not self.files_created:
            return {"operation": "file_delete", "status": "skipped", "reason": "no files"}
        
        filepath = random.choice(self.files_created)
        if os.path.exists(filepath):
            os.remove(filepath)
            self.files_created.remove(filepath)
            return {"operation": "file_delete", "filepath": filepath, "status": "success"}
        else:
            if filepath in self.files_created:
                self.files_created.remove(filepath)
            return {"operation": "file_delete", "status": "failed", "reason": "file not found"}
    
    def _git_operations(self):
        """Perform git operations."""
        if not self.files_created:
            return {"operation": "git", "status": "skipped", "reason": "no files"}
        
        # Pick a random git operation to perform
        git_op = random.choice(["status", "add", "commit"])
        
        try:
            if git_op == "status":
                result = subprocess.run(["git", "-C", self.test_dir, "status"], 
                                      capture_output=True, check=True)
                return {"operation": "git_status", "status": "success"}
            
            elif git_op == "add":
                # Add a random file
                filepath = random.choice(self.files_created)
                if os.path.exists(filepath):
                    result = subprocess.run(["git", "-C", self.test_dir, "add", filepath], 
                                          capture_output=True, check=True)
                    return {"operation": "git_add", "filepath": filepath, "status": "success"}
                else:
                    return {"operation": "git_add", "status": "failed", "reason": "file not found"}
            
            elif git_op == "commit":
                # Commit changes (if any)
                result = subprocess.run(["git", "-C", self.test_dir, "commit", "-m", f"Auto commit {time.time()}"], 
                                      capture_output=True)
                if result.returncode == 0:
                    return {"operation": "git_commit", "status": "success"}
                else:
                    # This is normal if there are no changes to commit
                    return {"operation": "git_commit", "status": "no changes"}
        
        except subprocess.CalledProcessError as e:
            return {"operation": f"git_{git_op}", "status": "failed", "error": str(e)}
    
    def _build_operation(self):
        """Simulate a build operation."""
        # Create a simple Python project to build
        build_dir = os.path.join(self.test_dir, "build_test")
        os.makedirs(build_dir, exist_ok=True)
        
        # Create a simple setup.py
        setup_py = os.path.join(build_dir, "setup.py")
        if not os.path.exists(setup_py):
            with open(setup_py, 'w') as f:
                f.write("""
from setuptools import setup, find_packages

setup(
    name="stress_test_pkg",
    version="0.1",
    packages=find_packages(),
)
""")
        
        # Create a package directory
        pkg_dir = os.path.join(build_dir, "stress_test_pkg")
        os.makedirs(pkg_dir, exist_ok=True)
        
        # Create __init__.py
        init_py = os.path.join(pkg_dir, "__init__.py")
        if not os.path.exists(init_py):
            with open(init_py, 'w') as f:
                f.write('"""Stress test package."""\n')
        
        # Add a module file
        module_py = os.path.join(pkg_dir, "module.py")
        with open(module_py, 'w') as f:
            f.write(f"""
def function_{random.randint(1, 10000)}():
    \"\"\"A random function.\"\"\"
    return {random.randint(1, 1000)}
""")
        
        # Simulate build using setup.py
        try:
            subprocess.run(["python", setup_py, "build"], 
                         cwd=build_dir, capture_output=True, check=True)
            return {"operation": "build", "status": "success"}
        except subprocess.CalledProcessError as e:
            return {"operation": "build", "status": "failed", "error": str(e)}
    
    def _search_operation(self):
        """Simulate a search operation."""
        if not self.files_created:
            return {"operation": "search", "status": "skipped", "reason": "no files"}
        
        # Generate a random search term
        search_chars = random.choices('abcdefghijklmnopqrstuvwxyz', k=3)
        search_term = ''.join(search_chars)
        
        try:
            # Use grep to search files
            result = subprocess.run(["grep", "-r", search_term, self.test_dir], 
                                  capture_output=True)
            return {
                "operation": "search", 
                "term": search_term, 
                "matches": len(result.stdout.decode().splitlines())
            }
        except subprocess.CalledProcessError as e:
            return {"operation": "search", "status": "failed", "error": str(e)}
    
    def _format_operation(self):
        """Simulate a code formatting operation."""
        # Create a Python file with bad formatting
        file_id = random.randint(1, 10000)
        filename = f"format_test_{file_id}.py"
        filepath = os.path.join(self.test_dir, filename)
        
        # Write poorly formatted Python code
        with open(filepath, 'w') as f:
            f.write(f"""
def badly_formatted_function(   a,    b,c):
  x=a+b
  if x>10:
   return x
  else:return c
          
class BadlyFormattedClass:
 def __init__(self):self.value=0
 
 def method(self,x   ):
      self.value=x
          
def another_function(  ):
    return [ x*x for x in range(10)   ]
""")
        
        # Auto-format with autopep8 if available
        try:
            # Try to install autopep8 if not available
            try:
                import autopep8
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "autopep8"])
                import autopep8
            
            # Format the file
            subprocess.run(["autopep8", "--in-place", filepath], 
                         capture_output=True, check=True)
            
            return {"operation": "format", "filepath": filepath, "status": "success"}
        
        except (ImportError, subprocess.CalledProcessError) as e:
            # If autopep8 fails, just simulate formatting
            with open(filepath, 'w') as f:
                f.write(f"""
def badly_formatted_function(a, b, c):
    x = a + b
    if x > 10:
        return x
    else:
        return c


class BadlyFormattedClass:
    def __init__(self):
        self.value = 0

    def method(self, x):
        self.value = x


def another_function():
    return [x*x for x in range(10)]
""")
            return {"operation": "format", "filepath": filepath, "status": "simulated"}
    
    def _generate_report(self):
        """Generate a report of the stress test results."""
        # Save metrics data
        self.metrics.save_metrics()
        
        # Generate plots
        self.metrics.plot_metrics()
        
        # Generate summary report
        summary = {
            "timestamp": datetime.now().isoformat(),
            "duration": self.duration,
            "threads": self.num_threads,
            "test_directory": self.test_dir,
            "files_created": len(self.files_created),
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "platform": sys.platform,
                "python_version": sys.version
            }
        }
        
        # Add some summary metrics
        if self.metrics.metrics["cpu_percent"]:
            summary["metrics_summary"] = {
                "cpu_avg": sum(self.metrics.metrics["cpu_percent"]) / len(self.metrics.metrics["cpu_percent"]),
                "cpu_max": max(self.metrics.metrics["cpu_percent"]),
                "memory_avg": sum(self.metrics.metrics["memory_percent"]) / len(self.metrics.metrics["memory_percent"]),
                "memory_max": max(self.metrics.metrics["memory_percent"]),
                "thread_max": max(self.metrics.metrics["thread_count"])
            }
        
        # Save summary
        with open("ide_stress_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Generated report: ide_stress_summary.json")

def main():
    """Parse arguments and run the stress test."""
    parser = argparse.ArgumentParser(description="IDE Stress Test")
    parser.add_argument("--threads", type=int, default=32,
                        help="Number of concurrent threads (default: 32)")
    parser.add_argument("--duration", type=int, default=3600,
                        help="Test duration in seconds (default: 3600)")
    parser.add_argument("--test-dir", type=str, default=None,
                        help="Directory to use for test files (default: temp directory)")
    
    args = parser.parse_args()
    
    # Run the stress test
    test = IDEStressTest(
        num_threads=args.threads,
        duration=args.duration,
        test_dir=args.test_dir
    )
    
    try:
        test.setup()
        test.run()
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.exception(f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
