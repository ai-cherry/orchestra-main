# Performance-Optimized VS Code Extension Management

This document describes the performance-optimized extension management system implemented for the AI Orchestra project. The system is designed to improve startup performance, reduce resource usage, and provide better monitoring and management of VS Code extensions.

## Overview

The extension management system consists of the following components:

1. **Single Source of Truth**: `extensions.json` defines all extensions categorized by priority
2. **Optimized Extension Loading**: `setup_extensions_optimized.sh` implements tiered, lazy loading of extensions
3. **Performance Monitoring**: `monitor_extension_performance.py` tracks extension resource usage
4. **Background Monitoring**: `monitor_extensions.sh` runs the performance monitor periodically
5. **Integration with Startup**: `start_orchestra.sh` integrates the extension management system

## Components

### 1. extensions.json

This file serves as the single source of truth for all extensions used in the project. Extensions are categorized into:

- **critical**: Essential extensions needed for basic functionality
- **development**: Extensions that improve the development experience
- **ai**: AI-powered extensions for code assistance
- **optional**: Nice-to-have extensions that aren't essential

Example:
```json
{
  "critical": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "googlecloudtools.cloudcode",
    "ms-azuretools.vscode-docker",
    "hashicorp.terraform"
  ],
  "development": [
    "charliermarsh.ruff",
    "ms-python.black-formatter"
  ],
  "ai": [
    "github.copilot"
  ],
  "optional": [
    "ms-toolsai.jupyter",
    "redhat.vscode-yaml"
  ]
}
```

### 2. update_devcontainer_extensions.py

This script updates the `.devcontainer/devcontainer.json` file with the critical extensions from `extensions.json`. This ensures that only essential extensions are installed during container creation, improving startup performance.

Usage:
```bash
python update_devcontainer_extensions.py
```

### 3. setup_extensions_optimized.sh

This script implements a tiered approach to extension installation:

1. Critical extensions are installed immediately
2. Development extensions are installed next
3. AI extensions are installed after development extensions
4. Optional extensions are installed in the background

This approach ensures that the most important extensions are available immediately, while less important extensions are installed in the background.

Usage:
```bash
bash setup_extensions_optimized.sh
```

### 4. monitor_extension_performance.py

This script monitors the performance of VS Code extensions by tracking resource usage and identifying problematic extensions. It can be run periodically to collect data and provide recommendations for optimizing extension usage.

Usage:
```bash
python monitor_extension_performance.py
```

### 5. monitor_extensions.sh

This script runs the `monitor_extension_performance.py` script at regular intervals (default: 30 minutes) to track extension performance over time. It's designed to be started in the background during workspace initialization.

Usage:
```bash
bash monitor_extensions.sh &
```

### 6. Integration with start_orchestra.sh

The `start_orchestra.sh` script has been updated to use the optimized extension management system. It now:

1. Uses `setup_extensions_optimized.sh` if available (falls back to legacy script if not)
2. Starts extension performance monitoring in the background (in standard mode)
3. Adds a new `--no-monitor` flag to disable extension monitoring

## Benefits

The optimized extension management system provides several benefits:

1. **Faster Startup**: By prioritizing critical extensions and deferring others
2. **Reduced Resource Usage**: Through better management and monitoring of extensions
3. **Improved Developer Experience**: With automated management and optimization
4. **Better Maintainability**: Through a single source of truth for extensions
5. **Performance Insights**: Through monitoring and reporting of extension resource usage

## Usage

### Basic Usage

The extension management system is automatically used when starting Orchestra:

```bash
bash start_orchestra.sh
```

### Advanced Usage

You can control the extension management system with the following flags:

```bash
# Skip extension management
bash start_orchestra.sh --no-extensions

# Skip extension monitoring
bash start_orchestra.sh --no-monitor

# Skip both extension management and monitoring
bash start_orchestra.sh --no-extensions --no-monitor
```

### Manual Extension Management

You can also manually manage extensions:

```bash
# Update devcontainer.json with critical extensions
python update_devcontainer_extensions.py

# Install extensions with optimized loading
bash setup_extensions_optimized.sh

# Monitor extension performance
python monitor_extension_performance.py

# Start background monitoring
bash monitor_extensions.sh &
```

## Performance Monitoring

The extension performance monitor tracks:

- CPU usage of extension host processes
- Memory usage of extension host processes
- High resource usage events
- Problematic extensions based on resource usage history

Performance data is stored in `.vscode/extension_performance.json` and logs are written to `logs/extension_monitor.log`.

## Customization

To customize the extension management system:

1. Edit `extensions.json` to add, remove, or recategorize extensions
2. Update thresholds in `monitor_extension_performance.py` to adjust sensitivity
3. Modify the monitoring interval in `monitor_extensions.sh` (default: 30 minutes)

## Troubleshooting

If you encounter issues with the extension management system:

1. Check the logs in `logs/extension_install.log` and `logs/extension_monitor.log`
2. Ensure the VS Code CLI is available (`which code`)
3. Verify that `jq` is installed (`which jq`)
4. Try running the scripts manually to see if there are any errors