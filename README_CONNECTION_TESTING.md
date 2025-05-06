# Firestore/Redis Connection Testing Tool

This tool provides automated testing for Firestore and Redis connections in the Orchestra platform, enabling comprehensive validation of database connectivity, performance, and reliability.

## Overview

The Firestore/Redis Connection Testing Tool was developed to address the needs identified in the priority assessment, which determined that database connection testing deserved immediate automation due to the critical nature of reliable data access for the application.

## Features

- **Comprehensive Testing**: Tests both synchronous and asynchronous connections
- **CRUD Operation Validation**: Verifies create, read, update, and delete operations
- **Connection Pool Analysis**: Tests behavior under parallel operation loads
- **Error Handling Validation**: Simulates various error conditions to validate recovery
- **Detailed Reporting**: Generates comprehensive JSON reports with test results
- **Configurable**: Supports custom test configurations via JSON

## Prerequisites

- Python 3.7+
- Google Cloud Platform credentials for Firestore
- Redis server (if testing Redis connections)
- Environment variables:
  - `GCP_PROJECT_ID`: Your Google Cloud project ID
  - `GCP_SA_KEY_PATH`: Path to service account key file
  - (Optional) `GCP_SA_KEY_JSON`: Service account key as a JSON string
  - (Optional) `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`: Redis connection details

## Installation

No additional installation is required beyond the standard Orchestra environment setup. The tool uses the same dependencies as the main application.

## Usage

The tool includes both a Python script and a convenient shell script wrapper.

### Basic Usage

```bash
# Run all tests with default settings
./run_connection_tests.sh

# Test only Firestore connections
./run_connection_tests.sh --firestore-only

# Test only Redis connections
./run_connection_tests.sh --redis-only

# Use custom configuration
./run_connection_tests.sh --config custom_config.json

# Specify output report path
./run_connection_tests.sh --output my_report.json

# Enable verbose logging
./run_connection_tests.sh --verbose
```

### Python Script Direct Usage

```bash
# Basic usage
python3 automate_connection_testing.py

# With arguments
python3 automate_connection_testing.py --firestore-only --output custom_report.json
```

## Configuration

You can customize the test behavior by providing a JSON configuration file:

```json
{
  "tests": {
    "connection_count": 5,
    "operation_count": 20,
    "run_firestore": true,
    "run_redis": true,
    "simulate_errors": true,
    "error_probability": 0.2,
    "network_latency": {
      "enabled": true,
      "min_ms": 10,
      "max_ms": 200
    }
  },
  "firestore": {
    "project_id": "your-gcp-project-id",
    "credentials_path": "/path/to/credentials.json"
  },
  "redis": {
    "host": "localhost",
    "port": 6379,
    "password": "optional-password"
  }
}
```

## Test Reports

The tool generates three types of reports:

1. **Firestore Report** (`firestore_test_report.json`): Detailed results of Firestore tests
2. **Redis Report** (`redis_test_report.json`): Detailed results of Redis tests
3. **Combined Report** (`connection_test_report.json` by default): Overview of all test results

### Sample Report Structure

```json
{
  "timestamp": "2025-04-24T23:45:12.345Z",
  "total_tests": 10,
  "successful_tests": 9,
  "failed_tests": 1,
  "success_rate": 0.9,
  "average_duration_ms": 157.3,
  "results": [
    {
      "timestamp": "2025-04-24T23:45:10.123Z",
      "test_name": "sync_connection",
      "success": true,
      "duration_ms": 125.4,
      "details": {"status": "healthy"}
    },
    {
      "timestamp": "2025-04-24T23:45:11.456Z",
      "test_name": "create_document",
      "success": false,
      "duration_ms": 189.7,
      "error": "Permission denied"
    }
  ]
}
```

## Integration with CI/CD

For continuous integration, you can add the following to your GitHub Actions workflow:

```yaml
- name: Run connection tests
  run: |
    export GCP_PROJECT_ID=${{ secrets.GCP_PROJECT_ID }}
    export GCP_SA_KEY_JSON=${{ secrets.GCP_SA_KEY_JSON }}
    ./run_connection_tests.sh --output connection_report.json
    
- name: Upload test report
  uses: actions/upload-artifact@v2
  with:
    name: connection-test-report
    path: connection_report.json
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure GCP_PROJECT_ID and either GCP_SA_KEY_PATH or GCP_SA_KEY_JSON are set
   - Verify the service account has sufficient permissions

2. **Import Errors**
   - Make sure to run the script from the project root directory
   - Check that all required dependencies are installed

3. **Redis Connection Issues**
   - Verify Redis is running and accessible
   - Check that the correct host, port, and password are configured

## Next Steps

The current implementation focuses primarily on Firestore testing with placeholder support for Redis. Future enhancements may include:

1. Full Redis implementation
2. Long-running stability tests
3. Network partition simulation
4. Metrics collection for performance benchmarking
5. Integration with monitoring systems

## Support

For issues or questions, please contact the Orchestra platform team.
