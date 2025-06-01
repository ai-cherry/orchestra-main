# Debugging Methodology for Debugger Mode

## Systematic Approach
- Always reproduce the issue first
- Isolate the problem to smallest reproducible case
- Use scientific method: hypothesis, test, validate
- Document all debugging steps for future reference
- Check recent changes first (git blame/log)

## Debugging Tools
- Use debugpy for Python debugging
- Leverage logging at DEBUG level
- Use SQL EXPLAIN for query issues
- Profile memory usage with tracemalloc
- Monitor system resources during debugging

## Error Analysis
- Read entire stack traces carefully
- Check for environmental differences
- Verify all dependencies and versions
- Look for race conditions in async code
- Check for resource exhaustion issues

## Common Issues Checklist
- Database connection pool exhaustion
- Missing environment variables
- Incorrect file permissions
- Network connectivity issues
- Memory leaks in long-running processes

## Resolution Documentation
- Document root cause clearly
- Provide minimal fix with explanation
- Include prevention strategies
- Update tests to catch regression
- Add monitoring for similar issues 