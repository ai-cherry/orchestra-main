#!/bin/bash
# Script to run memory bridge tests

set -e

cd /workspaces/cherry_ai-main

# Run the memory bridge test
python -m mcp_server.tests.test_memory_bridge

echo "Memory bridge tests completed successfully!"
