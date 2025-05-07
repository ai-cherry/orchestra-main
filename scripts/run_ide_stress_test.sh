#!/bin/bash
# IDE Stress Test Runner for AGI Baby Cherry Hybrid IDE
# This script prepares and executes the IDE stress test in the Cloud Workstation environment

set -e

# Print header
echo "========================================================"
echo "AGI Baby Cherry - Hybrid IDE Stress Test Runner"
echo "========================================================"
echo "Date: $(date)"
echo "Host: $(hostname)"
echo

# Check if running in a Cloud Workstation environment
if [[ -z "${CLOUD_WORKSTATIONS_IMAGE}" ]]; then
  echo "WARNING: This doesn't appear to be a Cloud Workstation environment."
  echo "The test will still run, but results may not be representative."
  echo
fi

# Create a dedicated directory for test outputs
TEST_OUTPUT_DIR="${HOME}/ide_stress_test_results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "${TEST_OUTPUT_DIR}"
echo "Test outputs will be saved to: ${TEST_OUTPUT_DIR}"

# Install dependencies
echo "Installing required packages..."
pip install --quiet psutil matplotlib numpy

# Set test parameters
THREADS=32
DURATION=3600  # 1 hour
TEST_DIR="${TEST_OUTPUT_DIR}/test_workspace"

# Copy the test script to the output directory
cp /workspaces/orchestra-main/agent/tests/ide_stress_test.py "${TEST_OUTPUT_DIR}/"
cd "${TEST_OUTPUT_DIR}"

echo "========================================================"
echo "Starting IDE Stress Test with:"
echo "- Threads: ${THREADS}"
echo "- Duration: ${DURATION} seconds"
echo "- Test directory: ${TEST_DIR}"
echo "========================================================"

# Run the stress test
python3 ide_stress_test.py --threads=${THREADS} --duration=${DURATION} --test-dir="${TEST_DIR}"

# Check for results
if [[ -f "ide_stress_metrics.json" && -f "ide_stress_metrics.png" && -f "ide_stress_summary.json" ]]; then
  echo "========================================================"
  echo "Test completed successfully!"
  echo "Results available in: ${TEST_OUTPUT_DIR}"
  echo
  
  # Display summary results
  echo "Summary of test results:"
  echo "------------------------"
  python3 -c "
import json, sys
try:
    with open('ide_stress_summary.json', 'r') as f:
        data = json.load(f)
    if 'metrics_summary' in data:
        metrics = data['metrics_summary']
        print(f\"CPU average: {metrics['cpu_avg']:.2f}%\")
        print(f\"CPU max: {metrics['cpu_max']:.2f}%\")
        print(f\"Memory average: {metrics['memory_avg']:.2f}%\")
        print(f\"Memory max: {metrics['memory_max']:.2f}%\")
        print(f\"Maximum threads: {metrics['thread_max']}\")
    print(f\"Files created: {data['files_created']}\")
    print(f\"Test duration: {data['duration']} seconds\")
    sys.exit(0)
except Exception as e:
    print(f\"Error parsing summary: {e}\")
    sys.exit(1)
"
  
  # Suggest next steps
  echo
  echo "Next steps:"
  echo "1. Review the detailed metrics in 'ide_stress_metrics.json'"
  echo "2. Examine the visual report in 'ide_stress_metrics.png'"
  echo "3. Upload results to Cloud Storage for sharing:"
  echo "   gsutil -m cp -r ${TEST_OUTPUT_DIR} gs://cherry-ai-project-bucket/stress-test-results/"
  echo
  echo "To send metrics to Cloud Monitoring, run:"
  echo "python3 /workspaces/orchestra-main/scripts/upload_stress_test_metrics.py --input=${TEST_OUTPUT_DIR}/ide_stress_metrics.json"
else
  echo "========================================================"
  echo "ERROR: Test did not complete successfully or results are missing!"
  echo "Check the logs for errors."
  exit 1
fi
