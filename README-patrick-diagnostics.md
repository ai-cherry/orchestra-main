# Patrick's Orchestrator Diagnostic Tool

This diagnostic tool is specifically designed to identify and troubleshoot issues affecting Patrick's solo-user experience with the Orchestrator system. It focuses on the three key areas where runtime problems commonly occur:

1. **Persona switching failures**
2. **Memory retrieval errors**
3. **LLM integration problems**

## Key Features

- **User-Friendly Error Messages**: Provides clear, non-technical explanations of what's going wrong
- **Actionable Solutions**: Suggests specific fixes for each detected issue
- **Comprehensive Checks**: Tests all components in the interaction flow
- **Self-Contained**: Runs without external dependencies beyond what Orchestrator already uses

## Installation

The diagnostic tool is already installed in your project directory. The script is named `diagnose_patrick_issues.py` and has been made executable.

## Usage

To run a basic diagnostic scan:

```bash
./diagnose_patrick_issues.py
```

### Options

- `--env PATH`: Specify a custom path to your .env file (default: ".env")
- `--output PATH`: Save diagnostic results to a JSON file
- `--verbose` or `-v`: Enable verbose output with additional details

### Examples

```bash
# Run diagnostics with the default .env file
./diagnose_patrick_issues.py

# Run diagnostics with a custom .env file
./diagnose_patrick_issues.py --env .env.development

# Save diagnostic results to a file
./diagnose_patrick_issues.py --output diagnostics_results.json

# Run with verbose output
./diagnose_patrick_issues.py --verbose
```

## What It Checks

### Persona Switching Issues

- Persona configuration loading
- Validation of persona configuration fields
- Fallback mechanisms when a persona is not found
- Middleware error handling
- Persona information storage in request state

### Memory System Issues

- Memory manager initialization
- Storage backend connectivity (in-memory or Firestore)
- Memory item validation
- Read/write operations
- Hardcoded user IDs in interaction endpoints

### LLM Integration Issues

- API key validation
- LLM client initialization and health checks
- Error handling in LLM calls
- Rate limiting detection
- Model fallback mechanisms
- Hardcoded model references

## Interpreting Results

The diagnostic tool outputs results in a color-coded format:

- **GREEN/OK**: Component is functioning properly
- **YELLOW/WARNING**: Component has issues but is still functional
- **RED/ERROR**: Component is not functioning properly
- **BLUE/INFO**: Informational message about a component

Each issue found includes:
- A technical description of the problem
- User-friendly explanation of how it impacts your experience
- Suggested solution for fixing the issue

## Common Solutions

### For Persona Issues

- Ensure the `personas.yaml` file exists and is properly formatted
- Add or fix the 'cherry' persona configuration as a fallback
- Check that persona configurations have complete descriptions and templates

### For Memory Issues

- Add Firestore credentials to your `.env` file for persistent storage
- Fix memory item validation to prevent storage of invalid data
- Remove hardcoded user IDs from interaction endpoints

### For LLM Integration Issues

- Add required API keys to your `.env` file
- Implement proper error handling around LLM calls
- Add model fallback mechanisms to handle unavailable models
- Make model selection configurable instead of hardcoded

## Support

If you continue to experience issues after running the diagnostic tool and implementing suggested fixes, collect the diagnostic output by running:

```bash
./diagnose_patrick_issues.py --output patrick_diagnostics.json
```

Then share this file with the development team for additional assistance.
