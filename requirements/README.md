# Cherry AI Dependency Management

We use **pip-tools** to manage dependencies while staying with pip/venv.
This gives us lockfile benefits without abandoning our familiar workflow.

## Structure

- `*.in` files - Human-readable dependency declarations
- `*.txt` files - Machine-generated locked dependencies (like lockfiles)

## Files

- `base.in` → `base.txt` - Core application dependencies
- `production.in` → `production.txt` - Production-specific additions
- `dev.in` → `dev.txt` - Development tools (linters, testers)

## Workflow

### 1. Initial Setup
```bash
# Install pip-tools
pip install pip-tools

# Generate locked files from .in files
pip-compile requirements/base.in -o requirements/base.txt
pip-compile requirements/production.in -o requirements/production.txt
pip-compile requirements/dev.in -o requirements/dev.txt
```

### 2. Installing Dependencies
```bash
# For development
pip-sync requirements/base.txt requirements/dev.txt

# For production
pip-sync requirements/base.txt requirements/production.txt
```

### 3. Adding New Dependencies
```bash
# 1. Add to appropriate .in file
echo "new-package==1.0.0" >> requirements/base.in

# 2. Recompile
pip-compile requirements/base.in -o requirements/base.txt

# 3. Install
pip-sync requirements/base.txt
```

### 4. Updating Dependencies
```bash
# Update all packages
pip-compile --upgrade requirements/base.in

# Update specific package
pip-compile --upgrade-package flask requirements/base.in

# Use our helper script
python scripts/update_dependencies.py
```

## Best Practices

1. **Always edit .in files**, never .txt files directly
2. **Commit both** .in and .txt files to version control
3. **Use pip-sync** instead of pip install for reproducible installs
4. **Pin versions** in .in files for stability
5. **Review changes** in .txt files before committing

## Constraint Files

For shared dependencies across projects:
```bash
# Create constraint file
pip-compile requirements/base.in -o requirements/constraints.txt

# Use in other projects
pip-compile requirements/other.in -c requirements/constraints.txt
```

## Why pip-tools?

- ✅ Stays with pip (no Poetry/Docker)
- ✅ Creates reproducible environments
- ✅ Handles transitive dependencies
- ✅ Simple and lightweight
- ✅ Works with existing pip workflows

## Troubleshooting

```bash
# Clear pip cache if having issues
pip cache purge

# Force recompile all dependencies
rm requirements/*.txt
pip-compile requirements/base.in
pip-compile requirements/production.in
pip-compile requirements/dev.in

# Check for conflicts
pip check
```
