#!/bin/bash
# Performance test runner for AI Orchestra Admin API
# This script makes it easy to run performance tests and compare results

set -e

# Default values
BASE_URL="http://localhost:8080"
CONCURRENCY=10
ITERATIONS=100
OUTPUT_DIR="performance_results"
TEST_MODE="standard"

# Text colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display usage
show_usage() {
  echo -e "${BLUE}AI Orchestra Admin API Performance Test Runner${NC}"
  echo ""
  echo "This script runs performance tests against the Admin API to measure and compare metrics."
  echo ""
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  -u, --url URL          Base URL for testing (default: $BASE_URL)"
  echo "  -c, --concurrency NUM  Number of concurrent requests (default: $CONCURRENCY)"
  echo "  -i, --iterations NUM   Number of requests per endpoint (default: $ITERATIONS)"
  echo "  -o, --output DIR       Directory for test results (default: $OUTPUT_DIR)"
  echo "  -m, --mode MODE        Test mode: standard, before-after, or continuous (default: $TEST_MODE)"
  echo "  -h, --help             Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0 --mode before-after  # Run baseline and optimized tests for comparison"
  echo "  $0 --concurrency 20     # Run with 20 concurrent requests"
  echo "  $0 --url http://admin-api-dev.cloud.run  # Test deployed API"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -u|--url)
      BASE_URL="$2"
      shift 2
      ;;
    -c|--concurrency)
      CONCURRENCY="$2"
      shift 2
      ;;
    -i|--iterations)
      ITERATIONS="$2"
      shift 2
      ;;
    -o|--output)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    -m|--mode)
      TEST_MODE="$2"
      shift 2
      ;;
    -h|--help)
      show_usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_usage
      exit 1
      ;;
  esac
done

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Check if required packages are installed
check_dependencies() {
  echo -e "${BLUE}Checking dependencies...${NC}"
  
  # Check if pip packages are installed
  python -c "import aiohttp, pandas, matplotlib" 2>/dev/null || {
    echo -e "${YELLOW}Installing required Python packages...${NC}"
    pip install aiohttp pandas matplotlib
  }
  
  echo -e "${GREEN}All dependencies satisfied.${NC}"
}

# Run a single performance test
run_test() {
  local name=$1
  local results_file="${OUTPUT_DIR}/${name}_results.csv"
  local chart_file="${OUTPUT_DIR}/${name}_chart.png"
  
  echo -e "${BLUE}Running performance test: ${name}${NC}"
  echo -e "Base URL: ${BASE_URL}"
  echo -e "Concurrency: ${CONCURRENCY}"
  echo -e "Iterations: ${ITERATIONS}"
  
  # Run the performance test and save results
  python performance_test.py \
    --base-url "$BASE_URL" \
    --concurrency "$CONCURRENCY" \
    --iterations "$ITERATIONS" \
    --output-dir "$OUTPUT_DIR" \
    --name "$name"
    
  echo -e "${GREEN}Test completed. Results saved to:${NC}"
  echo -e "  CSV: ${results_file}"
  echo -e "  Chart: ${chart_file}"
}

# Compare baseline and optimized test results
compare_results() {
  echo -e "${BLUE}Comparing test results...${NC}"
  
  python -c "
import pandas as pd
import matplotlib.pyplot as plt
import os

# Load the baseline and optimized results
baseline_file = os.path.join('$OUTPUT_DIR', 'baseline_results.csv')
optimized_file = os.path.join('$OUTPUT_DIR', 'optimized_results.csv')

if not (os.path.exists(baseline_file) and os.path.exists(optimized_file)):
    print('${RED}Error: Missing result files. Run both baseline and optimized tests first.${NC}')
    exit(1)

baseline = pd.read_csv(baseline_file)
optimized = pd.read_csv(optimized_file)

# Convert string values to float (removing 'ms' and '%')
for df in [baseline, optimized]:
    for col in df.columns:
        if col.endswith('(ms)'):
            df[col] = df[col].str.replace('ms', '').astype(float)
        elif col == 'Success Rate':
            df[col] = df[col].str.replace('%', '').astype(float)
        elif col == 'Req/sec':
            df[col] = df[col].astype(float)

# Merge datasets on Endpoint
comparison = pd.merge(baseline, optimized, on='Endpoint', suffixes=('_baseline', '_optimized'))

# Calculate improvements
comparison['Avg_improvement_%'] = ((comparison['Avg (ms)_baseline'] - comparison['Avg (ms)_optimized']) / 
                                  comparison['Avg (ms)_baseline']) * 100
comparison['Throughput_improvement_%'] = ((comparison['Req/sec_optimized'] - comparison['Req/sec_baseline']) /
                                       comparison['Req/sec_baseline']) * 100

# Create comparison table
result_table = comparison[['Endpoint', 
                          'Avg (ms)_baseline', 'Avg (ms)_optimized', 'Avg_improvement_%',
                          'Req/sec_baseline', 'Req/sec_optimized', 'Throughput_improvement_%']]

print('\nPerformance Improvement Summary:')
print(result_table.to_string(index=False, float_format=lambda x: f'{x:.2f}'))

# Calculate overall average improvement
avg_perf_improvement = comparison['Avg_improvement_%'].mean()
avg_throughput_improvement = comparison['Throughput_improvement_%'].mean()

print(f'\nOverall average response time improvement: {avg_perf_improvement:.2f}%')
print(f'Overall average throughput improvement: {avg_throughput_improvement:.2f}%')

# Create comparison chart
plt.figure(figsize=(12, 8))

endpoints = comparison['Endpoint'].tolist()
baseline_times = comparison['Avg (ms)_baseline'].tolist()
optimized_times = comparison['Avg (ms)_optimized'].tolist()

x = range(len(endpoints))
width = 0.35

plt.bar([i - width/2 for i in x], baseline_times, width, label='Baseline')
plt.bar([i + width/2 for i in x], optimized_times, width, label='Optimized')

plt.xlabel('Endpoint')
plt.ylabel('Avg Response Time (ms)')
plt.title('Performance Comparison: Baseline vs. Optimized')
plt.xticks(x, endpoints, rotation=45, ha='right')
plt.legend()
plt.tight_layout()

comparison_chart = os.path.join('$OUTPUT_DIR', 'performance_comparison.png')
plt.savefig(comparison_chart)
print(f'\n${GREEN}Comparison chart saved to: {comparison_chart}${NC}')
"
}

# Main function
main() {
  check_dependencies
  
  case "$TEST_MODE" in
    "standard")
      # Run a single performance test
      run_test "standard"
      ;;
    "before-after")
      # Run baseline test with original configuration
      echo -e "${YELLOW}STEP 1: Running baseline test with original configuration${NC}"
      echo -e "${YELLOW}Make sure you're using the pre-optimization code for this test${NC}"
      read -p "Press Enter to start baseline test..."
      run_test "baseline"
      
      # Run optimized test with performance improvements
      echo -e "\n${YELLOW}STEP 2: Running optimized test with performance improvements${NC}"
      echo -e "${YELLOW}Make sure you've applied all performance optimizations before this test${NC}"
      read -p "Press Enter to start optimized test..."
      run_test "optimized"
      
      # Compare results
      echo -e "\n${YELLOW}STEP 3: Comparing baseline vs. optimized results${NC}"
      compare_results
      ;;
    "continuous")
      # Run continuous performance tests (one per hour for 24 hours)
      echo -e "${YELLOW}Starting continuous performance testing (24 hours)${NC}"
      for i in {1..24}; do
        echo -e "\n${BLUE}Running test $i of 24${NC}"
        run_test "continuous_$i"
        
        # Sleep for one hour unless it's the last iteration
        if [ $i -lt 24 ]; then
          echo "Waiting for next test run (1 hour)..."
          sleep 3600
        fi
      done
      ;;
    *)
      echo -e "${RED}Unknown test mode: $TEST_MODE${NC}"
      show_usage
      exit 1
      ;;
  esac
  
  echo -e "\n${GREEN}Performance testing completed!${NC}"
}

# Run the script
main