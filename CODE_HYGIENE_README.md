# Orchestra Code Hygiene Guide

This document provides instructions for maintaining code quality and hygiene across the Orchestra repository.

## 1. Code Formatting and Linting

### Tools Setup

The repository is configured to use the following tools for code formatting and linting:

- **Black** - Code formatter for Python
- **isort** - Import sorter for Python
- **Ruff** - Fast Python linter that incorporates rules from Flake8, pycodestyle, etc.
- **pre-commit** - Framework to manage Git pre-commit hooks

These dependencies are included in `requirements-dev.txt` and should be installed in your development environment:

```bash
pip install -r requirements-dev.txt
```

### Pre-commit Hooks

Pre-commit hooks are set up to automatically check and format code when committing changes:

```bash
# Initial setup of pre-commit hooks (only needed once)
pre-commit install
```

### Formatting Code

To manually format code across the repository, use the provided script:

```bash
# Run formatting on all files
./format_and_lint.sh

# Check for issues without fixing them
./format_and_lint.sh --check

# Fix issues automatically where possible
./format_and_lint.sh --fix
```

## 2. Deprecation Notices

Legacy code in the repository (especially in the `future/` directory) should contain proper deprecation notices to guide developers toward newer implementations.

### Checking for Missing Deprecation Notices

```bash
# Check for missing deprecation notices
./check_deprecation_notices.py

# Get detailed information including files with proper notices
./check_deprecation_notices.py --verbose

# Automatically add deprecation notices to files missing them
./check_deprecation_notices.py --fix
```

## 3. Critical Linting Issues

To scan the codebase for critical linting issues (unused imports, undefined names, etc.):

```bash
# Find all critical issues
./find_critical_lint_issues.py

# Show detailed report
./find_critical_lint_issues.py --detailed

# Only check for code complexity issues
./find_critical_lint_issues.py --complexity-only

# Only check for critical errors
./find_critical_lint_issues.py --critical-only

# Check a specific directory
./find_critical_lint_issues.py --path ./core
```

## 4. Script Executability

All shell scripts and critical Python scripts should have appropriate execute permissions.

```bash
# Set execute permissions on all required scripts
./make_scripts_executable.sh
```

## 5. Configuration Files

### pyproject.toml

The `pyproject.toml` file contains configuration for:

- Black formatting rules (line length, exclude patterns)
- isort settings (profiles, line length)
- Ruff linting rules (enabled checks, ignores, exclusions)

### .pre-commit-config.yaml

The `.pre-commit-config.yaml` file defines the Git hooks that run on commit:

- trailing whitespace check
- end-of-file fixer
- YAML syntax check
- debug statement checker
- Black formatter
- isort import sorter
- Ruff linter

## Recommended Workflow

Follow these steps for code hygiene maintenance:

1. Install development dependencies: `pip install -r requirements-dev.txt`
2. Install pre-commit hooks: `pre-commit install`
3. Before submitting changes:
   - Run formatters: `./format_and_lint.sh --fix`
   - Check for critical issues: `./find_critical_lint_issues.py`
   - Ensure scripts are executable: `./make_scripts_executable.sh`
   - Verify deprecation notices: `./check_deprecation_notices.py`

## CI Integration

Consider integrating these checks into your CI pipeline by adding steps to:

1. Run Black, isort, and Ruff checks
2. Verify script executability
3. Check for missing deprecation notices
4. Ensure no critical linting issues are present

This will help maintain code quality across the entire development team.

---

## 6. Documentation Formatting Prompts

To ensure consistency and clarity in new documentation (e.g., new .md files or significant additions to existing ones), consider using prompts like the following with an AI assistant:

```plaintext
You are reviewing a new documentation file: `[Path to NEW_DOC_FILE.md]` (or a new section in an existing document).

1.  **Purpose & Clarity:** Does the document (or section) have a clear title and an introductory sentence/paragraph explaining its purpose and scope?
2.  **Structure & Readability:** Is the content logically organized using appropriate markdown headers (H2, H3, etc.)? Are paragraphs concise and easy to read? Is there good use of lists or bullet points for itemized information?
3.  **Markdown Correctness:** Are all markdown elements (code blocks, links, tables, bold/italics) used correctly and rendered as expected? Ensure code blocks specify the language for syntax highlighting.
4.  **Internal Linking:** Are all internal links to other project documents or sections relative and correct? Check for any broken links.
5.  **Technical Accuracy:** (If applicable) Is the technical information presented accurate and up-to-date with the current state of the project?
6.  **Conciseness & Grammar:** Is the language clear, concise, and free of jargon where possible (or is jargon clearly explained)? Check for grammatical errors, typos, and awkward phrasing.
7.  **Alignment with Existing Docs:** Does the new documentation align with the style and tone of existing key documents like `README.md` and `@docs/ARCHITECTURE.md`?

Return a list of specific, actionable suggestions for improvement, referencing line numbers or specific text where appropriate.
```
