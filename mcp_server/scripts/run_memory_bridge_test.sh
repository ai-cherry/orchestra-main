#!/bin/bash
# Script to run memory bridge tests

set -e

# Change to the project root directory
cd /workspaces/orchestra-main

# Run the memory bridge test
python -m mcp_server.tests.test_memory_bridge

echo "Memory bridge tests completed successfully!"