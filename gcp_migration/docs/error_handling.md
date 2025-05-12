wwwsw# GCP Migration Error Handling

This document outlines the robust error handling strategy implemented in the GCP Migration toolkit. The error system is designed to provide consistent, detailed error information while maintaining proper error propagation and recovery mechanisms.

## Error Hierarchy

The GCP Migration toolkit uses a refined exception hierarchy with the following key components:

### Base Exception Class

`MigrationError` is the base exception class for all migration-related errors. It provides:

- Standardized metadata tracking
- Error chaining capabilities
- Severity levels for appropriate handling
- Detailed context preservation

### Error Categories

Errors are organized into logical categories:

1. **Infrastructure Errors**
   - `InfrastructureError`: Base class for infrastructure issues
   - `NetworkError`: Network-related failures
   - `TimeoutError`: Operation timeouts
   - `ConnectionError`: Connection issues
   - `ResourceExhaustedError`: Resource limits reached

2. **Authentication and Authorization Errors**
   - `AuthenticationError`: Authentication failures
   - `AuthorizationError`: Permission issues
   - `CredentialError`: Credential-specific problems

3. **Resource Errors**
   - `ResourceError`: Base class for resource issues
   - `ResourceNotFoundError`: Resource not found
   - `ResourceAlreadyExistsError`: Duplicate resource creation attempts
   - `ResourceStateError`: Invalid resource state for operations

4. **Data Errors**
   - `DataError`: Base class for data issues
   - `ValidationError`: Data validation failures
   - `SerializationError`: Data serialization problems
   - `DataConsistencyError`: Data inconsistency issues

5. **GCP Service Errors**
   - `GCPError`: Base class for GCP service issues
   - `APIError`: API request failures
   - `QuotaError`: Quota exceedance
   - `ConfigurationError`: Configuration issues
   - `SecretError`: Secret Manager problems
   - `StorageError`: Cloud Storage issues
   - `FirestoreError`: Firestore database problems
   - `VertexAIError`: Vertex AI operations failures

6. **Migration Process Errors**
   - `MigrationProcessError`: Base class for process issues
   - `PlanningError`: Migration planning failures
   - `ExecutionError`: Migration execution failures
   - `VerificationError`: Migration verification failures

7. **Component Errors**
   - `ComponentError`: Base class for component issues
   - `InitializationError`: Component initialization failures
   - `CircuitBreakerError`: Circuit breaker issues
   - `CircuitOpenError`: Open circuit failures
   - `BatchProcessingError`: Batch processing issues
   - `PoolExhaustedError`: Resource pool depletion
   - `CacheError`: Cache operation failures

## Error Mapping

The toolkit provides automatic mapping between standard Python and Google Cloud exceptions to the domain-specific error hierarchy. This mapping is maintained in the `ERROR_MAPPING` dictionary, which associates exception class names with appropriate `MigrationError` subtypes.

Example mappings:

```python
ERROR_MAPPING = {
    # Network errors
    "RequestException": NetworkError,
    "ConnectionError": ConnectionError,
    "Timeout": TimeoutError,
    
    # GCP-specific errors
    "NotFound": ResourceNotFoundError,
    "AlreadyExists": ResourceAlreadyExistsError,
    "InvalidArgument": ValidationError,
    
    # Authentication errors
    "DefaultCredentialsError": CredentialError,
    "UnauthenticatedError": AuthenticationError,
    "PermissionDenied": AuthorizationError,
}
```

## Exception Mapping Functions

### `map_exception`

The `map_exception` function provides flexible mapping capabilities with two forms:

1. **Explicit target type**: 
   ```python
   map_exception(e, SpecificError, "Message")
   ```

2. **Automatic mapping**: 
   ```python
   map_exception(e, "Message")
   ```

This function ensures that appropriate context is preserved when converting exceptions.

## Exception Handling Decorator

### `handle_exception`

The `handle_exception` decorator provides comprehensive exception handling with:

- Logging (with configurable severity)
- Mapping to domain-specific errors
- Optional re-raising
- Traceback preservation

Example usage:

```python
@handle_exception(
    logger=custom_logger,
    default_error_type=MigrationError,
    error_message="Failed to migrate project",
    re_raise=True,
    log_traceback=True,
    severity=ErrorSeverity.ERROR
)
def migrate_project():
    # Migration implementation
```

## Best Practices

When working with the error handling system:

1. **Use specific error types** rather than generic ones when possible
2. **Preserve context** by using the `cause` parameter when creating new exceptions
3. **Include relevant details** in the exception message
4. **Use appropriate severity levels** based on operational impact
5. **Apply the `handle_exception` decorator** to high-level functions
6. **Add specific exception handling** for recoverable errors

## Integration with Migration Scripts

The error handling system is integrated with migration scripts through structured logging and checkpoint mechanisms. When errors occur:

1. The error is logged with appropriate context
2. A checkpoint is created with error status
3. The error is propagated to higher levels or handled locally
4. Recovery is attempted when possible

## Error Reporting

Errors are reported through multiple channels:

1. **Terminal output** with color-coded severity
2. **Log files** in the `migration_logs` directory
3. **Checkpoint files** for tracking migration progress

## Error Recovery

The system implements recovery strategies for common error scenarios:

1. **Permission issues**: Automatic re-granting of missing roles
2. **API enablement failures**: Multiple retry attempts
3. **Resource creation failures**: Cleanup and recreation
4. **Network issues**: Exponential backoff with jitter
