#!/usr/bin/env python3
"""Validate Python syntax for all files in the project."""
    """Validate a single Python file for syntax errors."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Try to parse the file
        ast.parse(content, filename=str(file_path))
        return True, "OK"
    except Exception:

        pass
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception:

        pass
        return False, f"Error: {str(e)}"

    """Find all Python files in the project."""
    skip_dirs = {".venv", "venv", "__pycache__", ".git", "node_modules", ".mypy_cache"}

        # Remove skip directories from the search
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if file.endswith(".py"):

    return python_files

def main():
    """Main function to validate all Python files."""
    print("=" * 60)

    print(f"Found {len(python_files)} Python files\n")

    errors = []

    for file_path in python_files:
        valid, message = validate_python_file(file_path)

        if not valid:
            errors.append((relative_path, message))
            print(f"❌ {relative_path}")
            print(f"   {message}")
        else:
            # Only show progress for every 50th file to reduce output
            if len(errors) == 0 and len(python_files) > 50:
                if python_files.index(file_path) % 50 == 0:
                    print(f"✓ Checked {python_files.index(file_path)} files...")

    print("\n" + "=" * 60)

    if errors:
        print(f"\n❌ Found {len(errors)} files with syntax errors:\n")
        for file_path, error in errors:
            print(f"  • {file_path}: {error}")
        return 1
    else:
        print(f"\n✅ All {len(python_files)} Python files have valid syntax!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
