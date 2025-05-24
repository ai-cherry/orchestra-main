import sys

MIN_PYTHON_VERSION = (3, 10)  # Require Python 3.10+

def check_virtual_environment():
    """Checks if a virtual environment is active and meets Python version requirements."""
    if not hasattr(sys, 'prefix') or sys.prefix == sys.base_prefix:
        print("ERROR: No virtual environment is active.")
        print("Please activate your virtual environment (e.g., 'source venv/bin/activate')")
        sys.exit(1)
    
    print(f"Active venv: {sys.prefix}")

    current_version = sys.version_info
    print(f"Python version: {current_version.major}.{current_version.minor}")

    if current_version < MIN_PYTHON_VERSION:
        min_version_str = f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}"
        print(f"ERROR: Python {min_version_str}+ is required. Current version: {current_version.major}.{current_version.minor}")
        sys.exit(1)

    print("Virtual environment and Python version are OK.")
    sys.exit(0)

if __name__ == "__main__":
    check_virtual_environment() 