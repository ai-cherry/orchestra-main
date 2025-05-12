# AI Orchestra Environment Manager

This tool addresses several key issues with the AI Orchestra project:

1. **Workspace Enumeration Speed**: Optimizes VS Code settings to handle large repositories efficiently
2. **Environment Management**: Clearly identifies and switches between dev/staging/prod environments
3. **Repository Size Management**: Analyzes and cleans up large repositories for GitHub compatibility
4. **Environment Mixing Prevention**: Creates visual indicators that make your current environment unmistakable

## 🚀 Quick Start

```bash
# Show your current environment with visual indicators
python environment_manager.py status

# Switch to a different environment (dev, staging, prod)
python environment_manager.py switch dev

# Optimize VS Code workspace settings to improve performance
python environment_manager.py optimize-workspace

# Analyze repository size and identify large files/directories
python environment_manager.py repo-size

# Clean up unnecessary files to reduce repository size (dry run by default)
python environment_manager.py cleanup
# To actually perform the cleanup:
python environment_manager.py cleanup --no-dry-run
```

## 🔍 Solving "Enumeration taking a long time" in VS Code

The `optimize-workspace` command addresses this by:

1. **Enhanced File Exclusions**: Automatically ignores caches, build artifacts, dependencies, and large directories
2. **Search Optimizations**: Configures search.exclude to skip irrelevant directories
3. **Watcher Exclusions**: Prevents VS Code from watching large directories like node_modules
4. **Editor Optimizations**: Configures settings to reduce memory usage and improve performance
5. **Auto-Save**: Sets up auto-save to reduce manual file operations

```bash
python environment_manager.py optimize-workspace
```

After running this command, restart VS Code to apply all optimizations. You should notice significantly faster workspace loading and better overall performance.

## 🔄 Environment Management

The Environment Manager provides clear visual indication of your current environment and allows easy switching between environments:

![Environment Indicators](https://via.placeholder.com/800x100/215732/ffffff?text=CURRENT+ENVIRONMENT:+DEV)

### Features:

- **Clear Terminal Indicators**: Color-coded banners in the terminal
- **VS Code Theme Integration**: Custom colors for each environment in VS Code
- **Environment File Management**: Proper .env file handling with active status tracking
- **Consistent Environment Variables**: Sets environment variables consistently across the system

```bash
# Check current environment
python environment_manager.py status

# Switch environments
python environment_manager.py switch dev    # Development
python environment_manager.py switch staging  # Staging
python environment_manager.py switch prod   # Production
```

## 📦 Repository Size Management

GitHub has soft limits on repository size (recommended max: 1GB, preferred: under 500MB). The Environment Manager helps you:

1. **Analyze Repository Size**: Identify total size and largest files/directories
2. **Identify Large Files**: Find candidates for Git LFS or external storage
3. **Clean Up**: Remove unnecessary files like caches, logs, and build artifacts
4. **Monitor Growth**: Track repository size over time

```bash
# Analyze repository size
python environment_manager.py repo-size

# Clean up repository (dry run by default)
python environment_manager.py cleanup

# Actually perform the cleanup
python environment_manager.py cleanup --no-dry-run
```

## 🛡️ Preventing Environment Mixing

For solo developers using AI coding assistants, it's critical to have clear indicators showing which environment you're working in to prevent accidental changes to the wrong environment. This tool helps by:

1. **Unmistakable Visual Indicators**: Terminal banners and VS Code theming
2. **Environment File Management**: Ensures only one environment is active at a time
3. **Indicator Files**: Creates `.dev_mode`, `.staging_mode`, or `.prod_mode` files to track state
4. **Window Title Customization**: Adds environment name to VS Code window title

These visual cues make it immediately obvious which environment you're working in, even when switching contexts or using AI assistants.

## 🔧 Advanced Usage

### Custom VS Code Settings

The Environment Manager modifies VS Code settings in `.vscode/settings.json`. You can customize these settings further by editing this file directly after running the optimizer.

### Additional Cleanup Patterns

To add custom cleanup patterns:

1. Edit `environment_manager.py`
2. Find the `cleanup_patterns` list in the `cleanup_repository` method
3. Add your custom pattern, such as `"**/temp_files"` or `"**/*.bak"`

### Environment Variables

The tool checks for environment variables like `AI_ORCHESTRA_ENV`, `NODE_ENV`, and `PYTHON_ENV`. You can set these in your shell or in your .env files to maintain consistency.

## 💻 Development Workflow Best Practices

1. **Start Each Session with Status Check**: Run `python environment_manager.py status` at the beginning of each work session
2. **Optimize Regularly**: Run `optimize-workspace` after significant repository changes
3. **Clean Up Periodically**: Schedule regular cleanup runs to prevent repository bloat
4. **Explicit Environment Switching**: Always use the tool to switch environments rather than manual editing

This workflow ensures you always know which environment you're working in and maintains optimal performance.
