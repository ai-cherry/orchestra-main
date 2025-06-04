#!/usr/bin/env python3
"""
"""
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("quick-check")

# ANSI colors for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

def check_env_file():
    """Check if .env file exists and has required variables."""
    print(f"{Colors.BOLD}Checking environment configuration...{Colors.ENDC}")

    env_path = Path(".env")
    if not env_path.exists():
        print(f"  {Colors.RED}✗ .env file not found{Colors.ENDC}")
        print(f"    {Colors.YELLOW}→ Create a .env file based on .env.example{Colors.ENDC}")
        return False

    # Check for required API keys
    required_vars = {
        "PORTKEY_API_KEY": "Required for LLM integration",
        "OPENROUTER_API_KEY": "Alternate LLM provider (recommended as fallback)",
        "VULTR_CREDENTIALS_PATH": "Required for Firestore memory storage",
    }

    found_vars = {}
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key in required_vars and value:
                    found_vars[key] = True

    # Report results
    all_good = True
    for var, description in required_vars.items():
        if var in found_vars:
            print(f"  {Colors.GREEN}✓ {var} found{Colors.ENDC}")
        else:
            print(f"  {Colors.RED}✗ Missing {var}: {description}{Colors.ENDC}")
            all_good = False

    return all_good

def check_critical_files():
    """Check if critical files and directories exist."""
    print(f"\n{Colors.BOLD}Checking critical files and directories...{Colors.ENDC}")

    critical_paths = [
        # Core configuration
        ("core/conductor/src/config/personas.yaml", "Persona configurations"),
        # Core modules for Patrick's experience
        ("packages/shared/src/memory/memory_manager.py", "Memory management"),
        ("packages/shared/src/llm_client", "LLM integration"),
        ("core/conductor/src/personas", "Persona management"),
        # API endpoints
        (
            "core/conductor/src/api/endpoints/interaction.py",
            "API interaction endpoint",
        ),
    ]

    all_exist = True
    for path, description in critical_paths:
        full_path = Path(path)
        if full_path.exists():
            print(f"  {Colors.GREEN}✓ {path} exists{Colors.ENDC}")
        else:
            print(f"  {Colors.RED}✗ Missing {path}: {description}{Colors.ENDC}")
            all_exist = False

    return all_exist

def check_api_configuration():
    """Check if API is properly configured."""
    print(f"\n{Colors.BOLD}Checking API configuration...{Colors.ENDC}")

    # Check for the main API entrypoint
    api_app_path = Path("core/conductor/src/api/app.py")
    if not api_app_path.exists():
        print(f"  {Colors.RED}✗ API app.py not found{Colors.ENDC}")
        return False

    # Read the file to check for required route registrations
    try:

        pass
        with open(api_app_path, "r") as f:
            content = f.read()

        # Check for essential route registrations
        checks = [
            ("from shared.endpoints import interaction", "Interaction endpoint import"),
            (".include_router(interaction.router", "Interaction router registration"),
            ("from .middleware", "Middleware imports (for persona handling)"),
        ]

        all_found = True
        for pattern, description in checks:
            if pattern in content:
                print(f"  {Colors.GREEN}✓ {description} found{Colors.ENDC}")
            else:
                print(f"  {Colors.RED}✗ Missing {description}{Colors.ENDC}")
                all_found = False

        return all_found
    except Exception:

        pass
        print(f"  {Colors.RED}✗ Error checking API configuration: {e}{Colors.ENDC}")
        return False

def check_hardcoded_references():
    """Check for hardcoded user references that could affect Patrick."""
    print(f"\n{Colors.BOLD}Checking for hardcoded references...{Colors.ENDC}")

    # Files to check for hardcoded references
    files_to_check = [
        "core/conductor/src/api/endpoints/interaction.py",
        "packages/shared/src/memory/memory_manager.py",
    ]

    patterns = [
        ('user_id="patrick"', "Hardcoded user ID"),
        ("user_id='patrick'", "Hardcoded user ID"),
        ('user="patrick"', "Hardcoded user name"),
        ("user='patrick'", "Hardcoded user name"),
    ]

    issues_found = False
    for file_path in files_to_check:
        try:

            pass
            path = Path(file_path)
            if not path.exists():
                continue

            with open(path, "r") as f:
                content = f.read()

            for pattern, description in patterns:
                if pattern in content:
                    line_num = (
                        content.split("\n").index([line for line in content.split("\n") if pattern in line][0]) + 1
                    )
                    print(f"  {Colors.YELLOW}⚠ {description} found in {file_path}:{line_num}{Colors.ENDC}")
                    issues_found = True
        except Exception:

            pass
            print(f"  {Colors.YELLOW}⚠ Error checking {file_path}: {e}{Colors.ENDC}")

    if not issues_found:
        print(f"  {Colors.GREEN}✓ No hardcoded user references found{Colors.ENDC}")

    return not issues_found

def main():
    """Run all quick checks."""
    print(f"{Colors.BOLD}conductor Quick Check Tool{Colors.ENDC}")
    print(f"{Colors.BLUE}Running rapid checks for Patrick's experience...{Colors.ENDC}\n")

    # Run all checks
    env_ok = check_env_file()
    files_ok = check_critical_files()
    api_ok = check_api_configuration()
    hardcoded_ok = check_hardcoded_references()

    # Overall assessment
    print(f"\n{Colors.BOLD}Quick Check Results:{Colors.ENDC}")

    if env_ok and files_ok and api_ok and hardcoded_ok:
        print(f"\n{Colors.GREEN}✓ All basic checks passed!{Colors.ENDC}")
        print("  The system structure looks good for Patrick's experience.")
        print("  For a more thorough analysis, run: ./diagnose_patrick_issues.py")
        return 0
    elif env_ok and files_ok and api_ok:
        print(f"\n{Colors.YELLOW}⚠ Most checks passed with some minor issues{Colors.ENDC}")
        print("  The system structure is present but there are some potential issues.")
        print("  Run ./diagnose_patrick_issues.py for detailed diagnostics.")
        return 1
    else:
        print(f"\n{Colors.RED}✗ Basic structure checks failed{Colors.ENDC}")
        print("  The system has critical configuration or file structure issues.")
        print("  Fix these basic issues before running the full diagnostic.")
        return 2

if __name__ == "__main__":
    # Make script executable
    if os.name != "nt":  # Not Windows
        import stat

        script_path = Path(__file__)
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)

    sys.exit(main())
