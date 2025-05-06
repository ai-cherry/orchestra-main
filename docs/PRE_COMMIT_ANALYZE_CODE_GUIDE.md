# Pre-commit Analyze Code Integration Guide

This document explains how the `analyze_code.sh` script is integrated with pre-commit hooks to enable automatic code analysis during the commit process.

## Overview

The `analyze_code.sh` script performs Gemini-powered code analysis on specified files, but it expects files to be provided as a comma-separated list in a single argument. This created an issue with pre-commit hooks, which typically pass files as separate arguments.

The solution implemented here uses a Python wrapper script to bridge this gap.

## Components

### 1. analyze_code.sh

This script performs the actual code analysis using Gemini AI. It takes a single argument that should be a comma-separated list of files to analyze.

Example usage:
```bash
./analyze_code.sh file1.py,file2.py,file3.py
```

### 2. analyze_code_wrapper.py

This wrapper script:
1. Receives individual file paths from pre-commit
2. Joins them into a comma-separated string
3. Calls `analyze_code.sh` with the properly formatted argument

The wrapper handles:
- Path resolution to find `analyze_code.sh`
- Error checking for missing files
- Output handling from the analysis script

### 3. Pre-commit Configuration

The `.pre-commit-config.yaml` has been updated to use the wrapper script:

```yaml
-   repo: local
    hooks:
    -   id: analyze-code
        name: Gemini Code Analysis
        entry: scripts/analyze_code_wrapper.py
        language: python
        types: [python]
        pass_filenames: true
        verbose: true
```

## How It Works

1. When you attempt to commit code, pre-commit runs the `analyze-code` hook
2. Pre-commit passes the staged Python files to `analyze_code_wrapper.py` as separate arguments
3. The wrapper joins these files into a comma-separated string
4. The wrapper calls `analyze_code.sh` with this string as a single argument
5. Analysis results are displayed in the terminal

## Troubleshooting

If you encounter issues with the code analysis:

1. **Check script permissions**:
   ```bash
   chmod +x scripts/analyze_code_wrapper.py
   chmod +x analyze_code.sh
   ```

2. **Verify paths**:
   The wrapper assumes `analyze_code.sh` is in the project root. If it's elsewhere, update the path in `analyze_code_wrapper.py`.

3. **Debug output**:
   Both scripts have verbose output to help diagnose issues. Look for error messages in the terminal.

4. **Test manually**:
   You can test the wrapper directly:
   ```bash
   ./scripts/analyze_code_wrapper.py path/to/file1.py path/to/file2.py
   ```

## Customization

If you need to modify the analysis behavior:
- For changes to analysis parameters, modify `analyze_code.sh`
- For changes to file selection or pre-commit integration, modify `analyze_code_wrapper.py` or the hook configuration in `.pre-commit-config.yaml`
