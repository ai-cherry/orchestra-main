# Pulumi Infrastructure Migration Framework

A comprehensive, production-ready framework for migrating existing cloud infrastructure to Pulumi with advanced features including state management, deduplication, dependency resolution, and rollback capabilities.

## Features

### Core Capabilities
- **🔍 Resource Discovery**: Automatically discover and catalog existing infrastructure resources
- **🔄 State Management**: Persistent state tracking with checkpoints and rollback points
- **🚫 Deduplication**: Intelligent detection and handling of duplicate resources
- **🔗 Dependency Resolution**: Automatic dependency graph construction and topological sorting
- **♻️ Retry Logic**: Sophisticated retry mechanism with exponential backoff and circuit breakers
- **⚡ Performance Optimized**: Async operations, batching, and memory-efficient processing
- **📊 Progress Monitoring**: Real-time progress tracking with detailed metrics
- **🔙 Rollback Support**: Safe rollback capabilities with state restoration

### Advanced Features
- **Parallel Execution**: Configurable parallelism with rate limiting
- **Memory Management**: Automatic memory pressure detection and mitigation
- **Comprehensive Logging**: Structured logging with multiple output formats
- **CLI Interface**: Full-featured command-line interface with multiple commands
- **Report Generation**: Detailed migration reports and analytics
- **Multi-Provider Support**: Extensible architecture for multiple cloud providers

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/pulumi-migration
cd infrastructure/pulumi/migration

# Install dependencies
npm install

# Build the project
npm run build

# Link for global usage (optional)
npm link
```

## Configuration

### Pulumi Configuration

Create a `Pulumi.<stack>.yaml` file:

```yaml
config:
  gcp:project: your-project-id
  gcp:region: us-central1
  migration:projectId: your-project-id
  migration:parallelism: 10
  migration:retryAttempts: 3
  migration:apiKey:
    secure: <encrypted-api-key>
  migration:gcpServiceAccountKey:
    secure: <encrypted-service-account-key>
```

### Environment Variables

```bash
# Required
export PULUMI_ACCESS_TOKEN=your-pulumi-token
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Optional
export MIGRATION_LOG_FILE=/var/log/migration.log
export VERBOSE=true
```

## Usage

### Basic Migration

```bash
# Run a complete migration
pulumi-migrate migrate --project my-project --region us-central1

# Dry run mode
pulumi-migrate migrate --dry-run

# With custom parallelism
pulumi-migrate migrate --parallelism 20

# Skip confirmation prompts
pulumi-migrate migrate --yes
```

### Pre-Migration Validation

```bash
# Validate prerequisites
pulumi-migrate validate --project my-project

# Verbose validation
pulumi-migrate validate --verbose
```

### Resource Discovery

```bash
# Discover all resources
pulumi-migrate discover --project my-project

# Save discovery report
pulumi-migrate discover --output discovery-report.json
```

### Check Migration Status

```bash
# Show current migration status
pulumi-migrate status

# For specific stack
pulumi-migrate status --stack production
```

### Rollback

```bash
# Rollback the migration
pulumi-migrate rollback

# Skip confirmation
pulumi-migrate rollback --yes
```

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Interface (index.ts)                 │
├─────────────────────────────────────────────────────────────┤
│              Enhanced conductor (conductor-enhanced.ts) │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│   State     │  Resource   │ Dependency  │     Retry       │
│  Manager    │  Discovery  │  Resolver   │    Manager      │
│  (Async)    │             │             │                 │
├─────────────┼─────────────┼─────────────┼─────────────────┤
│ Validator   │Deduplicator │   Logger    │    Metrics      │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

### Migration Phases

1. **Initialization**: Load configuration, initialize components
2. **Validation**: Pre-migration checks (APIs, permissions, quotas)
3. **Discovery**: Scan and catalog existing resources
4. **Planning**: Build dependency graph, determine migration order
5. **Execution**: Migrate resources in dependency order
6. **Verification**: Post-migration validation
7. **Cleanup**: Generate reports, clean up temporary data

## Advanced Usage

### Custom Resource Discovery

```typescript
import { DiscoveryProvider } from "./src/resource-discovery";

class CustomProvider implements DiscoveryProvider {
    name = "custom";
    
    async discover(): Promise<ResourceMapping[]> {
        // Custom discovery logic
        return [];
    }
}
```

### Event Handling

```typescript
conductor.on('resourceMigrated', (resource) => {
    console.log(`Migrated: ${resource.name}`);
});

conductor.on('migrationFailed', (error) => {
    console.error(`Failed: ${error.message}`);
});
```

### State Management

```typescript
// Access state directly
const stateManager = new AsyncStateManager(config);
await stateManager.initialize();

// Create manual checkpoint
await stateManager.createCheckpoint("before-critical-operation");

// Export state for backup
const backup = await stateManager.exportState();
fs.writeFileSync('backup.json', backup);
```

## Performance Tuning

### Parallelism Configuration

```yaml
# Adjust based on your infrastructure size and API limits
migration:parallelism: 20  # Number of concurrent operations
migration:rateLimitPerSecond: 10  # API calls per second
```

### Memory Management

```yaml
# Memory pressure thresholds
migration:memoryThresholdPercent: 85
migration:gcIntervalMs: 30000
```

### Batch Processing

```yaml
# State update batching
migration:stateBatchSize: 100
migration:stateFlushIntervalMs: 1000
```

## Monitoring and Debugging

### Verbose Logging

```bash
# Enable verbose logging
pulumi-migrate migrate --verbose --log-file migration.log

# View logs in real-time
tail -f migration.log | jq '.'
```

### Metrics Collection

The framework collects detailed metrics:
- Resource processing times
- API call counts
- Retry statistics
- Memory usage
- Circuit breaker states

### Generated Reports

After migration, find reports in `.pulumi-migration/reports/`:
- `state-report.json`: Complete state snapshot
- `discovery-report.json`: Discovered resources summary
- `deduplication-report.json`: Duplicate resource analysis
- `retry-report.json`: Retry and circuit breaker statistics
- `metrics-report.json`: Performance metrics

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Ensure credentials are set
   gcloud auth application-default login
   pulumi login
   ```

2. **Rate Limiting**
   ```yaml
   # Reduce parallelism
   migration:parallelism: 5
   migration:retryDelayMs: 10000
   ```

3. **Memory Issues**
   ```bash
   # Increase Node.js memory limit
   NODE_OPTIONS="--max-old-space-size=8192" pulumi-migrate migrate
   ```

4. **State Lock Issues**
   ```bash
   # Force release stale lock
   rm .pulumi-migration/*/migration-state.json.lock
   ```

### Debug Mode

```bash
# Enable debug logging
DEBUG=* pulumi-migrate migrate --verbose
```

## Best Practices

1. **Always Run Validation First**
   ```bash
   pulumi-migrate validate && pulumi-migrate migrate
   ```

2. **Use Dry Run for Testing**
   ```bash
   pulumi-migrate migrate --dry-run
   ```

3. **Create Backups**
   ```bash
   pulumi-migrate status > pre-migration-state.json
   ```

4. **Monitor Progress**
   - Use `--verbose` for detailed output
   - Check `.pulumi-migration/reports/` for analytics
   - Monitor system resources during migration

5. **Incremental Migration**
   - Start with non-critical resources
   - Increase parallelism gradually
   - Validate after each phase

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Documentation: https://docs.example.com/pulumi-migration
- Issues: https://github.com/your-org/pulumi-migration/issues
- Slack: #pulumi-migration

## Roadmap

- [ ] AWS provider support
- [ ] Azure provider support
- [ ] Kubernetes resource discovery
- [ ] Web UI for migration monitoring
- [ ] Integration with CI/CD pipelines
- [ ] Multi-region migration support
- [ ] Cost estimation before migration
- [ ] Automated rollback testing