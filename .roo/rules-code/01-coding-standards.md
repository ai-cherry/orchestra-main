# Code Generation Standards for Roo AI (Project Symphony)

## Language & Environment
- **Python Version**: Python 3.10 (No 3.11+ features like match/case, tomllib)
- **Package Management**: pip/venv only (No Poetry, Pipenv, or Conda)
- **Dependencies**: Check `requirements/base.txt` before adding new ones

## Code Quality Standards

### Type Hints & Documentation
- **Type Hints**: Mandatory for all functions (PEP 484)
- **Docstrings**: Google-style for all public modules, classes, and functions
- **Comments**: Explain why, not what; code should be self-documenting

### Code Structure
- **Max Line Length**: 88 characters (Black default)
- **Max Function Length**: 50 lines (prefer smaller)
- **Cyclomatic Complexity**: < 15
- **File Size**: < 700KB

### Formatting & Style
- **Formatter**: Black (required)
- **Import Sorting**: isort
- **Linting**: flake8, mypy for type checking
- **Naming**: PEP 8 compliant (snake_case for functions/variables)

## Performance Requirements

### Benchmarking
```python
@benchmark  # Required for functions with loops > 1000 iterations
def process_large_dataset(data: List[Dict]) -> List[Dict]:
    """Process dataset with performance tracking."""
    # Implementation
```

### Algorithm Complexity
- Prefer O(n log n) or better
- Document complexity in docstring
- Justify if using less efficient algorithm

### Database Operations
```python
# Required: EXPLAIN ANALYZE for new queries
async def get_user_data(user_id: int) -> Dict:
    """Get user data with query plan.
    
    Query plan:
    EXPLAIN ANALYZE SELECT * FROM users WHERE id = $1;
    -> Index Scan using users_pkey (cost=0.29..8.31 rows=1)
    """
    return await db.fetch_one(query, user_id)
```

## File Management

### Temporary Files
```python
from core.utils.file_management import transient_file

@transient_file(lifetime_hours=24)
def generate_report(data: Dict) -> Path:
    """Generate temporary report with automatic cleanup."""
    report_path = Path(f"reports/temp_{uuid4()}.json")
    report_path.write_text(json.dumps(data))
    return report_path
```

### Output Files
- Reports → `docs/` or `reports/`
- Logs → Use logging framework
- Data → `data/` with clear naming
- Never create files in module directories

## Error Handling

### Exception Handling
```python
# Use specific exceptions
try:
    result = process_data(input_data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise
except ProcessingError as e:
    logger.warning(f"Processing issue: {e}")
    return fallback_result
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed information for debugging")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical issues")
```

## Database Access

### Required Pattern
```python
from shared.database import UnifiedDatabase

async def database_operation():
    """All database access through UnifiedDatabase."""
    async with UnifiedDatabase() as db:
        # PostgreSQL operations
        result = await db.fetch_all(query)
        
        # Weaviate operations
        vectors = await db.vector_search(embedding)
```

### Connection Management
- Never create direct connections
- Use connection pooling
- Implement proper cleanup

## Anti-Patterns to Avoid

### ❌ Bad Patterns
```python
# DON'T: Direct database connection
conn = psycopg2.connect(...)

# DON'T: os.system for subprocess
os.system("rm -rf /tmp/*")

# DON'T: Print for logging
print(f"Error: {error}")

# DON'T: Standalone scripts
# create_one_off_cleanup.py

# DON'T: Temporary files without cleanup
with open("/tmp/data.txt", "w") as f:
    f.write(data)
```

### ✅ Good Patterns
```python
# DO: Use UnifiedDatabase
async with UnifiedDatabase() as db:
    result = await db.fetch_one(query)

# DO: subprocess.run
subprocess.run(["rm", "-rf", "/tmp/specific_file"], check=True)

# DO: Proper logging
logger.error(f"Operation failed: {error}")

# DO: Integrate into existing modules
# In scripts/orchestra.py: add_cleanup_command()

# DO: Managed temporary files
@transient_file(lifetime_hours=4)
def create_temp_file(data: str) -> Path:
    # Implementation
```

## Integration Requirements

### Module Extension
- Check existing modules before creating new ones
- Extend `core.utils` for utilities
- Add to `scripts/orchestra.py` for CLI commands
- Use `services/` for new service components

### Testing
```python
# Required: Unit tests for new functions
def test_process_data():
    """Test data processing with edge cases."""
    assert process_data([]) == []
    assert process_data(None) raises ValueError
    # Performance assertion
    start = time.perf_counter()
    process_data(large_dataset)
    assert time.perf_counter() - start < 1.0
```

## Automation Scripts

### Registration Required
```python
# Instead of cron entry, register with automation manager
# python scripts/automation_manager.py register \
#     "Data Sync" "scripts/automation/data_sync.py" \
#     "0 2 * * *" "Syncs data nightly" "data-team"
```

### Script Template
```python
#!/usr/bin/env python3
"""Automation script following standards."""

import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def main() -> int:
    """Main entry point."""
    try:
        # Implementation
        return 0
    except Exception as e:
        logger.error(f"Script failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Security Considerations
- No hardcoded credentials
- Use environment variables or Pulumi secrets
- Validate all inputs
- Sanitize file paths
- Use parameterized queries

## Performance Monitoring
- Add metrics collection for critical paths
- Log execution times for slow operations
- Monitor memory usage for data processing
- Profile before optimizing