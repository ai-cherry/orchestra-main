# AI Orchestra GCP Migration Monitoring Toolkit

This toolkit provides monitoring, resilience, and reporting tools for the GCP migration process. These components run independently from the main migration process and can be deployed immediately without interfering with ongoing work.

## Overview

The Migration Monitoring Toolkit consists of four main components:

1. **Migration Monitor** - Real-time monitoring of migration progress and phase detection
2. **Vector Search Circuit Breaker** - Resilience mechanism for vector search operations during migration
3. **Status Report Generator** - Comprehensive migration status reports for stakeholders 
4. **Daily Report Scheduler** - Automated setup for daily status reports

Each component works independently and can be deployed immediately without interfering with the existing migration process. They're designed to provide visibility, resilience, and communication throughout the migration.

## Migration Monitor

The Migration Monitor (`migration_monitor.py`) tracks migration progress by analyzing log files, detecting conflicts, and monitoring active processes.

### Features

- Real-time migration phase tracking
- Conflict detection between phases
- Active process monitoring
- Continuous status file updates
- Daily activity reports

### Usage

Run the monitor in continuous mode to track the migration in real-time:

```bash
# Start continuous monitoring (runs in background with 60s refresh)
./migration_monitor.py --mode=monitor --interval=60

# Generate a one-time status report
./migration_monitor.py --mode=status

# Generate a comprehensive daily report
./migration_monitor.py --mode=daily --output=daily_report_$(date +%Y%m%d).md
```

## Vector Search Circuit Breaker

The Circuit Breaker (`circuit_breaker.py`) provides resilience for vector search operations during migration by detecting failures and providing graceful degradation.

### Features

- Automatic failure detection
- Three-state circuit: CLOSED (normal), OPEN (failing), HALF-OPEN (testing recovery)
- Fallback mechanisms for graceful degradation
- Detailed telemetry and metrics
- Support for both synchronous and asynchronous code

### Integration

There are two ways to use the circuit breaker in your code:

#### 1. Decorator Pattern

```python
from gcp_migration.circuit_breaker import circuit_break

# Simple usage with defaults
@circuit_break
def search_vectors(query_vector, top_k=5):
    # Vector search implementation
    ...

# Advanced usage with custom parameters
@circuit_break(
    name="custom_search",
    failure_threshold=3,
    recovery_timeout=60.0,
    fallback_function=my_fallback_function
)
async def search_vectors_async(query_vector, top_k=5):
    # Async vector search implementation
    ...
```

#### 2. Direct Instance Usage

```python
from gcp_migration.circuit_breaker import VectorSearchCircuitBreaker

# Create a circuit breaker instance
breaker = VectorSearchCircuitBreaker(
    name="vector_search",
    failure_threshold=5,
    recovery_timeout=30.0
)

# Use it to protect a function
def search_vectors(query_vector, top_k=5):
    return breaker(actual_search_function)(query_vector, top_k)
```

## Status Report Generator

The Status Report Generator (`generate_status_report.py`) creates comprehensive status reports for stakeholders with progress tracking, recent activities, risks, and metrics.

### Features

- Migration progress summary
- Phase status tracking
- Recent activity logging
- Potential risk identification
- Performance metrics (optional)
- Multiple output formats (file, email, GCS)

### Usage

Generate status reports in different formats:

```bash
# Generate a report as a file
./generate_status_report.py --output=file --path=reports/

# Send a report by email
./generate_status_report.py --output=email --recipients=team@example.com,cto@example.com

# Upload a report to Google Cloud Storage
./generate_status_report.py --output=gcs --bucket=migration-reports

# Include performance metrics
./generate_status_report.py --output=file --metrics
```

## Daily Report Scheduler

The Daily Report Scheduler (`setup_daily_reports.sh`) configures automated daily status reports using cron.

### Features

- Automated daily report generation
- Flexible scheduling options
- Multiple output formats (file, email, GCS)
- On-demand report script generation

### Usage

Set up daily status reports:

```bash
# Basic setup with file output
./setup_daily_reports.sh

# Email reports to the team at 8:00 AM
./setup_daily_reports.sh --output=email --email-recipients=team@example.com --time=08:00

# Upload reports to GCS at 7:30 AM
./setup_daily_reports.sh --output=gcs --gcs-bucket=migration-reports --time=07:30

# Include performance metrics in daily reports
./setup_daily_reports.sh --metrics
```

## Integration with Migration Process

The monitoring toolkit is designed to work alongside the existing migration process without interference. Here's how the components integrate:

1. **Migration Monitor** - Analyzes migration logs to track progress without modifying the core migration process
2. **Circuit Breaker** - Acts as a wrapper around vector search operations to provide resilience without changing implementation details
3. **Status Reports** - Generate reports based on migration status files and logs without direct dependencies on migration code
4. **Daily Reports** - Run independently via cron to provide regular status updates without requiring migration process changes

## Recommended Usage Pattern

For immediate deployment, we recommend the following sequence:

1. Start the Migration Monitor in continuous mode to track progress:
   ```bash
   ./migration_monitor.py --mode=monitor
   ```

2. Apply the Circuit Breaker to critical vector search operations:
   ```python
   # Add this import to files with vector search operations
   from gcp_migration.circuit_breaker import circuit_break
   
   # Apply the decorator to vector search functions
   @circuit_break
   def your_existing_vector_search_function(...):
       # Existing implementation
       ...
   ```

3. Set up daily status reports for stakeholders:
   ```bash
   ./setup_daily_reports.sh --output=email --email-recipients=migration-team@example.com,stakeholders@example.com
   ```

4. Generate on-demand reports for important milestones:
   ```bash
   ./generate_status_report.py --output=file --path=milestone-reports/ --metrics
   ```

## Monitoring Dashboard

The Migration Monitor automatically creates a `migration_status.json` file that can be consumed by monitoring dashboards. You can build a custom dashboard using your preferred monitoring tool, or use the status reports generated by the toolkit.

## Performance Impact

All components in this toolkit are designed to have minimal performance impact:

- **Migration Monitor**: Reads log files without modifying them, with configurable polling intervals
- **Circuit Breaker**: Minimal overhead (microseconds) for normal operation in closed state
- **Status Reports**: Generated on-demand or at scheduled times, not during critical operations
- **Daily Reports**: Run via cron at off-peak hours (default 7:00 AM)

## Logs and Troubleshooting

Each component writes logs to help with troubleshooting:

- Migration Monitor: `migration_monitor.log`
- Circuit Breaker: Standard logging output
- Status Reports: Log entries in the reports themselves
- Daily Reports: Logs in `gcp_migration/logs/`

## Security Considerations

- Email credentials are provided via command-line arguments and can be sourced from environment variables
- GCS authentication uses standard Google Cloud credential mechanisms
- No sensitive information is stored in logs or status files

## What to Expect During Migration

As the migration progresses through different phases, you'll see:

1. **Phase transitions** reported in the status reports
2. **Circuit breaker activations** during periods of instability (logged to standard output)
3. **Daily status reports** delivered at the configured time
4. **Conflict warnings** if competing migration operations are detected

## Conclusion

The Migration Monitoring Toolkit provides essential visibility, resilience, and communication during the GCP migration process. By deploying these components immediately, you can ensure a smoother migration process with minimal disruption.