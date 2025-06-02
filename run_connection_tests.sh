#!/bin/bash
# Script to run the automated Firestore/Redis connection tests

# Set script to exit on error
set -e

# Display help message
function show_help {
  echo "Firestore/Redis Connection Testing Tool"
  echo ""
  echo "Usage: ./run_connection_tests.sh [options]"
  echo ""
  echo "Options:"
  echo "  -c, --config PATH      Specify a custom config file path"
  echo "  -f, --firestore-only   Test only Firestore connections"
  echo "  -r, --redis-only       Test only Redis connections"
  echo "  -o, --output PATH      Specify output report path (default: connection_test_report.json)"
  echo "  -v, --verbose          Enable verbose logging"
  echo "  -h, --help             Show this help message"
  echo ""
  echo "Examples:"
  echo "  ./run_connection_tests.sh                    # Run all tests with default settings"
  echo "  ./run_connection_tests.sh -f                 # Test only Firestore"
  echo "  ./run_connection_tests.sh -c custom_config.json  # Use custom configuration"
  echo ""
}

# Parse command line arguments
ARGS=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--config)
      ARGS="$ARGS --config $2"
      shift 2
      ;;
    -f|--firestore-only)
      ARGS="$ARGS --firestore-only"
      shift
      ;;
    -r|--redis-only)
      ARGS="$ARGS --redis-only"
      shift
      ;;
    -o|--output)
      ARGS="$ARGS --output $2"
      shift 2
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# Make sure the Python script is executable
chmod +x automate_connection_testing.py

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d " " -f 2)
echo "Using Python $PYTHON_VERSION"

# Check Vultr auth environment
if [ -z "$  echo "⚠️ Warning:   echo "Firestore tests may fail without proper Vultr authentication"
  echo ""
fi

if [ -z "$Vultr_SA_KEY_PATH" ] && [ -z "$Vultr_SA_KEY_JSON" ]; then
  echo "⚠️ Warning: Neither Vultr_SA_KEY_PATH nor Vultr_SA_KEY_JSON is set"
  echo "Firestore tests may fail without proper Vultr authentication"
  echo ""
fi

# Display test information
echo "=================================="
echo " Running Connection Tests"
echo "=================================="
if [[ $ARGS == *"--firestore-only"* ]]; then
  echo "Testing: Firestore only"
elif [[ $ARGS == *"--redis-only"* ]]; then
  echo "Testing: Redis only"
else
  echo "Testing: Firestore and Redis"
fi

echo ""
echo "Starting tests..."
echo ""

# Run the Python script
if [ "$VERBOSE" = true ]; then
  python3 -u automate_connection_testing.py $ARGS
else
  python3 -u automate_connection_testing.py $ARGS | grep -v "DEBUG"
fi

# Check if the test was successful
if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Connection tests completed successfully!"
  echo ""
  echo "View reports:"
  if [[ ! $ARGS == *"--redis-only"* ]]; then
    echo "- firestore_test_report.json"
  fi
  if [[ ! $ARGS == *"--firestore-only"* ]]; then
    echo "- redis_test_report.json"
  fi

  # Determine output file name
  OUTPUT_FILE="connection_test_report.json"
  if [[ $ARGS == *"--output"* ]]; then
    OUTPUT_FILE=$(echo $ARGS | grep -oP '(?<=--output )[^ ]+')
  fi
  echo "- $OUTPUT_FILE (combined)"
else
  echo ""
  echo "❌ Connection tests failed!"
  echo "Check the logs for details"
  exit 1
fi
