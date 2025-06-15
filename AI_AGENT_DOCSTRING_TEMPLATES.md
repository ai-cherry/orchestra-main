# 🎯 Enhanced Docstring Templates for AI Agents

## 📋 **Overview**

This document provides comprehensive docstring templates optimized for AI coding agents working on the Orchestra AI platform. These templates ensure consistent, informative documentation that helps AI agents understand context, integration points, and usage patterns.

## 🐍 **Python Function Docstring Template**

### **Standard Function Template**
```python
async def process_file(
    file_id: UUID,
    processing_options: ProcessingOptions,
    db: AsyncSession
) -> ProcessedFileResult:
    """
    Process a file with specified options for Orchestra AI platform.
    
    This function handles file processing with comprehensive error handling,
    health monitoring integration, and proper logging for AI agent context.
    
    Args:
        file_id: Unique identifier for the file to process
        processing_options: Configuration object with format, quality settings
        db: Async database session for data operations
        
    Returns:
        ProcessedFileResult: Contains processing status, metadata, and file URLs
        
    Raises:
        FileNotFoundError: If file_id doesn't exist in database
        ProcessingError: If file processing fails due to format/corruption
        DatabaseError: If database operations fail
        
    Example:
        >>> options = ProcessingOptions(format="pdf", quality="high")
        >>> result = await process_file(file_id, options, db_session)
        >>> print(f"Status: {result.status}, URL: {result.processed_url}")
        
    AI Agent Context:
        - Integrates with health monitoring system
        - Uses enhanced secret manager for external API calls
        - Follows async/await patterns throughout
        - Includes structured logging for debugging
        
    Related Functions:
        - validate_file_format(): Pre-processing validation
        - get_processing_status(): Check processing progress
        - cleanup_temp_files(): Post-processing cleanup
        
    Integration Points:
        - Health Monitor: Updates processing metrics
        - Secret Manager: Accesses external API keys
        - Database: Stores processing results
        - Vector Store: Indexes processed content
    """
```

### **API Endpoint Template**
```python
@router.post(
    "/files/process",
    response_model=FileProcessingResponse,
    summary="Process uploaded file",
    description="""
    Process an uploaded file with specified options.
    
    This endpoint handles file processing for the Orchestra AI platform,
    including format conversion, quality optimization, and metadata extraction.
    
    **AI Agent Usage:**
    - Always check health status before processing large files
    - Use appropriate processing options based on file type
    - Monitor processing status via WebSocket or polling
    
    **Integration Points:**
    - Health monitoring: Affects system load metrics
    - Secret manager: May require external API keys for processing
    - Database: Stores processing results and metadata
    """,
    responses={
        200: {"description": "Processing started successfully"},
        400: {"description": "Invalid file format or processing options"},
        500: {"description": "Internal processing error"},
    },
    tags=["file-processing"]
)
async def process_file_endpoint(
    file_data: FileProcessingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> FileProcessingResponse:
    """
    API endpoint for file processing with comprehensive error handling.
    
    This endpoint provides a RESTful interface for file processing operations,
    integrating with the Orchestra AI platform's monitoring and security systems.
    
    Args:
        file_data: File processing request with options and metadata
        background_tasks: FastAPI background tasks for async processing
        db: Database session dependency for data operations
        
    Returns:
        FileProcessingResponse: Processing status and tracking information
        
    Raises:
        HTTPException: 400 for invalid requests, 500 for server errors
        
    AI Agent Context:
        - Uses FastAPI dependency injection patterns
        - Integrates with background task processing
        - Follows REST API conventions
        - Includes comprehensive error responses
        
    Security:
        - Validates file types and sizes
        - Uses secret manager for external API access
        - Logs all processing attempts for audit
        
    Monitoring:
        - Updates health metrics during processing
        - Tracks processing duration and success rates
        - Alerts on processing failures or timeouts
    """
```

### **Class Template**
```python
class FileProcessor:
    """
    Handles file processing operations for Orchestra AI platform.
    
    This class provides comprehensive file processing capabilities including
    format conversion, quality optimization, metadata extraction, and
    integration with the platform's monitoring and storage systems.
    
    Attributes:
        supported_formats: List of supported file formats
        max_file_size: Maximum file size in bytes
        processing_timeout: Timeout for processing operations
        
    AI Agent Context:
        - Singleton pattern for resource management
        - Async methods for all I/O operations
        - Integrates with health monitoring system
        - Uses structured logging throughout
        
    Integration Points:
        - Secret Manager: External API credentials
        - Health Monitor: Processing metrics and status
        - Database: Metadata and result storage
        - Vector Store: Content indexing and search
        
    Example:
        >>> processor = FileProcessor()
        >>> await processor.initialize()
        >>> result = await processor.process_file(file_id, options)
        
    Thread Safety:
        - All methods are async and thread-safe
        - Uses connection pooling for database operations
        - Implements proper resource cleanup
    """
    
    def __init__(self, config: ProcessingConfig):
        """
        Initialize file processor with configuration.
        
        Args:
            config: Processing configuration with limits and options
            
        AI Agent Context:
            - Validates configuration on initialization
            - Sets up logging and monitoring integration
            - Initializes connection pools and resources
        """
```

## ⚛️ **React Component Docstring Template**

### **Functional Component Template**
```typescript
/**
 * HealthDashboard Component
 * 
 * Displays real-time system health metrics for Orchestra AI platform.
 * Integrates with health monitoring API and provides visual status indicators.
 * 
 * @component
 * @example
 * ```tsx
 * <HealthDashboard 
 *   refreshInterval={30000}
 *   showDetailedMetrics={true}
 *   onHealthChange={(status) => console.log('Health changed:', status)}
 * />
 * ```
 * 
 * @param {number} refreshInterval - How often to refresh health data (ms)
 * @param {boolean} showDetailedMetrics - Whether to show detailed system metrics
 * @param {function} onHealthChange - Callback when health status changes
 * 
 * AI Agent Context:
 * - Fetches data from /api/health/ endpoint
 * - Uses Tailwind CSS classes for styling
 * - Implements proper error boundaries
 * - Follows Orchestra AI design system patterns
 * 
 * Related Components:
 * - SystemMetricsCard: Individual metric display
 * - AlertBanner: Health alert notifications
 * - StatusBadge: Health status indicator
 * 
 * Integration Points:
 * - Health Monitor API: Real-time health data
 * - WebSocket Service: Live updates
 * - Error Boundary: Graceful error handling
 * 
 * State Management:
 * - Uses React hooks for local state
 * - Implements proper cleanup on unmount
 * - Handles loading and error states
 * 
 * Accessibility:
 * - ARIA labels for screen readers
 * - Keyboard navigation support
 * - High contrast mode compatible
 */
interface HealthDashboardProps {
  refreshInterval?: number;
  showDetailedMetrics?: boolean;
  onHealthChange?: (status: HealthStatus) => void;
}

export const HealthDashboard: React.FC<HealthDashboardProps> = ({
  refreshInterval = 30000,
  showDetailedMetrics = false,
  onHealthChange
}) => {
  // Implementation with comprehensive error handling and loading states
};
```

### **Custom Hook Template**
```typescript
/**
 * useHealthMonitoring Hook
 * 
 * Custom React hook for monitoring system health status.
 * Provides real-time health data with automatic refresh and error handling.
 * 
 * @hook
 * @example
 * ```tsx
 * const { healthData, isLoading, error, refresh } = useHealthMonitoring({
 *   refreshInterval: 30000,
 *   autoRefresh: true
 * });
 * ```
 * 
 * @param {object} options - Configuration options for health monitoring
 * @param {number} options.refreshInterval - Refresh interval in milliseconds
 * @param {boolean} options.autoRefresh - Whether to auto-refresh data
 * 
 * @returns {object} Health monitoring state and actions
 * @returns {HealthData} healthData - Current health status and metrics
 * @returns {boolean} isLoading - Whether data is currently loading
 * @returns {string|null} error - Error message if request failed
 * @returns {function} refresh - Manual refresh function
 * 
 * AI Agent Context:
 * - Implements proper cleanup on unmount
 * - Uses AbortController for request cancellation
 * - Follows React hooks best practices
 * - Integrates with error boundary system
 * 
 * Integration Points:
 * - Health Monitor API: /api/health/ endpoint
 * - Error Tracking: Logs errors for monitoring
 * - Performance: Optimized for minimal re-renders
 * 
 * Error Handling:
 * - Network errors: Retry with exponential backoff
 * - API errors: Display user-friendly messages
 * - Timeout errors: Graceful degradation
 */
interface UseHealthMonitoringOptions {
  refreshInterval?: number;
  autoRefresh?: boolean;
}

interface UseHealthMonitoringReturn {
  healthData: HealthData | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export const useHealthMonitoring = (
  options: UseHealthMonitoringOptions = {}
): UseHealthMonitoringReturn => {
  // Implementation
};
```

## 🗄️ **Database Model Template**

```python
class FileRecord(Base):
    """
    Database model for file records in Orchestra AI platform.
    
    Stores metadata and processing information for uploaded files,
    including processing status, file paths, and integration data.
    
    Table: file_records
    
    Relationships:
        - user: Many-to-one with User model
        - processing_jobs: One-to-many with ProcessingJob model
        - search_queries: Many-to-many with SearchQuery model
        
    Indexes:
        - file_hash: Unique index for deduplication
        - created_at: Index for time-based queries
        - status: Index for status filtering
        
    AI Agent Context:
        - Uses UUID primary keys for scalability
        - Includes audit fields (created_at, updated_at)
        - Implements soft delete pattern
        - Uses enum types for status fields
        
    Integration Points:
        - Vector Store: file_path used for content indexing
        - Health Monitor: status changes trigger metrics updates
        - File Service: processing_status tracked here
        
    Example:
        >>> file_record = FileRecord(
        ...     filename="document.pdf",
        ...     file_path="/uploads/uuid/document.pdf",
        ...     file_size=1024000,
        ...     user_id=user.id
        ... )
        >>> db.add(file_record)
        >>> await db.commit()
    """
    
    __tablename__ = "file_records"
    
    # Primary key and identifiers
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4,
        comment="Unique identifier for the file record"
    )
    
    # File metadata
    filename: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        comment="Original filename as uploaded by user"
    )
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when record was created"
    )
```

## 🔧 **Service Class Template**

```python
class FileService:
    """
    Service class for file operations in Orchestra AI platform.
    
    Provides high-level file management operations including upload,
    processing, search, and deletion with proper error handling and
    integration with platform services.
    
    Dependencies:
        - Database: File metadata storage
        - Secret Manager: External API credentials
        - Health Monitor: Operation metrics
        - Vector Store: Content indexing
        
    AI Agent Context:
        - All methods are async for non-blocking operations
        - Uses dependency injection for testability
        - Implements comprehensive error handling
        - Integrates with monitoring and logging systems
        
    Error Handling:
        - FileNotFoundError: File doesn't exist
        - ProcessingError: File processing failed
        - StorageError: Storage operation failed
        - ValidationError: Invalid file or parameters
        
    Example:
        >>> service = FileService(db_session, secret_manager)
        >>> result = await service.upload_file(file_data, user_id)
        >>> status = await service.get_processing_status(result.file_id)
    """
    
    def __init__(
        self,
        db: AsyncSession,
        secret_manager: SecretManager,
        health_monitor: HealthMonitor
    ):
        """
        Initialize file service with dependencies.
        
        Args:
            db: Database session for data operations
            secret_manager: Secret manager for API credentials
            health_monitor: Health monitor for metrics tracking
            
        AI Agent Context:
            - Uses dependency injection pattern
            - Validates dependencies on initialization
            - Sets up logging and monitoring integration
        """
```

## 📊 **Configuration Class Template**

```python
class ProcessingConfig:
    """
    Configuration class for file processing operations.
    
    Defines processing parameters, limits, and options for the
    Orchestra AI file processing system with validation and defaults.
    
    Attributes:
        max_file_size: Maximum file size in bytes (default: 100MB)
        supported_formats: List of supported file formats
        processing_timeout: Timeout for processing operations (seconds)
        quality_settings: Quality options for different output formats
        
    AI Agent Context:
        - Uses Pydantic for validation and serialization
        - Provides sensible defaults for all settings
        - Includes validation methods for configuration
        - Supports environment variable overrides
        
    Environment Variables:
        - PROCESSING_MAX_FILE_SIZE: Override max file size
        - PROCESSING_TIMEOUT: Override processing timeout
        - PROCESSING_QUALITY: Override default quality setting
        
    Example:
        >>> config = ProcessingConfig()
        >>> config.max_file_size = 50 * 1024 * 1024  # 50MB
        >>> config.validate()
        
    Validation:
        - File size limits are reasonable
        - Timeout values are positive
        - Supported formats are valid
        - Quality settings are within range
    """
```

## 🎯 **Best Practices for AI Agents**

### **Documentation Standards**
1. **Always include AI Agent Context section** - Helps agents understand integration points
2. **Provide concrete examples** - Show actual usage patterns
3. **Document error conditions** - List all possible exceptions and causes
4. **Include integration points** - Show how the code connects to other systems
5. **Add related functions/components** - Help agents find related code

### **Template Usage Guidelines**
1. **Choose appropriate template** - Match template to code type
2. **Customize for context** - Adapt template to specific use case
3. **Include all sections** - Don't skip sections, mark as N/A if not applicable
4. **Update regularly** - Keep documentation current with code changes
5. **Cross-reference** - Link to related documentation and code

### **AI Agent Optimization**
1. **Use structured format** - Consistent structure helps AI parsing
2. **Include keywords** - Use terms AI agents can search for
3. **Provide context** - Explain why code exists and how it fits
4. **Show patterns** - Demonstrate established coding patterns
5. **Link resources** - Reference related documentation and examples

---

**These templates ensure consistent, comprehensive documentation that enables AI coding agents to understand, extend, and maintain the Orchestra AI platform effectively.**

