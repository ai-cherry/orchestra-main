#!/usr/bin/env python3
"""
"""
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"  # No Color

def print_status(message: str, status: str) -> None:
    """Print colored status message."""
    color = GREEN if status == "OK" else YELLOW if status == "WARNING" else RED
    print(f"{message}: {color}{status}{NC}")

def check_python_version() -> Tuple[bool, str]:
    """Check Python version is exactly 3.10."""
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return (
        False,
        f"Python {version.major}.{version.minor}.{version.micro} (requires 3.10)",
    )

def check_virtual_env() -> Tuple[bool, str]:
    """Check if running in virtual environment."""
    if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        return True, sys.prefix
    return False, "Not in virtual environment"

def check_required_files() -> Dict[str, bool]:
    """Check existence of required files."""
        ".env": "Environment configuration",
        ".gitmessage": "Git commit template",
        "requirements/base.txt": "Base requirements",
        "infra/requirements.txt": "Pulumi requirements",
        "infra/main.py": "Pulumi main configuration",
        "scripts/deploy_optimized_infrastructure.sh": "Deployment script",
        ".github/workflows/pulumi-deploy.yml": "CI/CD workflow",
    }

    results = {}
    for file, description in required_files.items():
        path = Path(file)
        results[f"{file} ({description})"] = path.exists()

    return results

def check_environment_variables() -> Dict[str, bool]:
    """Check required environment variables."""
    required_vars = ["VULTR_PROJECT_ID", "VULTR_PROJECT_ID"]

    optional_vars = ["OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]

    results = {}

    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file) as f:
            env_content = f.read()
            for var in required_vars:
                if var in env_content:
                    results[f"{var} (required)"] = True
                else:
                    results[f"{var} (required)"] = False

            for var in optional_vars:
                if var in env_content or var in os.environ:
                    results[f"{var} (optional)"] = True
                else:
                    results[f"{var} (optional)"] = None  # None means optional and not set

    return results

def check_git_config() -> Dict[str, bool]:
    """Check Git configuration."""
            ["git", "config", "user.name"], capture_output=True, text=True, check=False
        ).stdout.strip()
        results["Git user.name"] = bool(user_name)

        user_email = subprocess.run(
            ["git", "config", "user.email"], capture_output=True, text=True, check=False
        ).stdout.strip()
        results["Git user.email"] = bool(user_email)

        # Check commit template
        commit_template = subprocess.run(
            ["git", "config", "--local", "commit.template"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        results["Git commit template"] = commit_template == ".gitmessage"

    except Exception:


        pass
        results["Git configuration"] = False

    return results

def check_dependencies() -> Dict[str, bool]:
    """Check if required tools are installed."""
        "gcloud": "Google Cloud SDK",
        "docker": "Docker",
        "kubectl": "Kubernetes CLI",
        "pulumi": "Pulumi CLI",
    }

    results = {}
    for tool, description in tools.items():
        try:

            pass
            # Add Pulumi bin to PATH for subprocess
            env = os.environ.copy()
            env["PATH"] = f"{env['PATH']}:{os.path.expanduser('~/.pulumi/bin')}"

            subprocess.run([tool, "--version"], capture_output=True, check=True, env=env)
            results[f"{tool} ({description})"] = True
        except Exception:

            pass
            results[f"{tool} ({description})"] = False

    return results

def check_gcp_auth() -> Tuple[bool, str]:
    """Check GCP authentication status."""
            ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=json"],
            capture_output=True,
            text=True,
            check=True,
        )
        accounts = json.loads(result.stdout)
        if accounts:
            return True, accounts[0].get("account", "Unknown")
        return False, "No active account"
    except Exception:

        pass
        return False, str(e)

def check_directory_structure() -> Dict[str, bool]:
    """Check required directory structure."""
        "infra/components",
        "scripts",
        "tests/unit",
        "tests/integration",
        "docs",
        ".github/workflows",
    ]

    results = {}
    for dir_path in required_dirs:
        path = Path(dir_path)
        results[dir_path] = path.exists() and path.is_dir()

    return results

def main():
    """Run all environment checks."""
    print("=" * 60)
    print("AI cherry_ai Environment Verification")
    print("=" * 60)
    print()

    # Python version
    print("1. Python Version Check")
    python_ok, python_msg = check_python_version()
    print_status("Python version", "OK" if python_ok else "ERROR")
    print(f"   {python_msg}")
    print()

    # Virtual environment
    print("2. Virtual Environment Check")
    venv_ok, venv_msg = check_virtual_env()
    print_status("Virtual environment", "OK" if venv_ok else "WARNING")
    print(f"   {venv_msg}")
    print()

    # Required files
    print("3. Required Files Check")
    file_results = check_required_files()
    all_files_ok = all(file_results.values())
    for file, exists in file_results.items():
        print_status(f"   {file}", "OK" if exists else "MISSING")
    print()

    # Environment variables
    print("4. Environment Variables Check")
    env_results = check_environment_variables()
    for var, status in env_results.items():
        if status is None:  # Optional and not set
            print_status(f"   {var}", "NOT SET")
        else:
            print_status(f"   {var}", "OK" if status else "MISSING")
    print()

    # Git configuration
    print("5. Git Configuration Check")
    git_results = check_git_config()
    for config, ok in git_results.items():
        print_status(f"   {config}", "OK" if ok else "NOT SET")
    print()

    # Dependencies
    print("6. Required Tools Check")
    dep_results = check_dependencies()
    for tool, installed in dep_results.items():
        print_status(f"   {tool}", "OK" if installed else "NOT INSTALLED")
    print()

    # GCP authentication
    print("7. GCP Authentication Check")
    gcp_ok, gcp_msg = check_gcp_auth()
    print_status("GCP authentication", "OK" if gcp_ok else "NOT AUTHENTICATED")
    if gcp_ok:
        print(f"   Active account: {gcp_msg}")
    print()

    # Directory structure
    print("8. Directory Structure Check")
    dir_results = check_directory_structure()
    for dir_path, exists in dir_results.items():
        print_status(f"   {dir_path}/", "OK" if exists else "MISSING")
    print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    critical_issues = []
    warnings = []

    if not python_ok:
        critical_issues.append("Python 3.10 is required")

    if not venv_ok:
        warnings.append("Not running in virtual environment")

    if not all_files_ok:
        missing_files = [f for f, exists in file_results.items() if not exists]
        critical_issues.append(f"Missing files: {', '.join(missing_files)}")

    required_env_missing = [var for var, status in env_results.items() if "required" in var and not status]
    if required_env_missing:
        critical_issues.append(f"Missing required env vars: {', '.join(required_env_missing)}")

    missing_tools = [tool for tool, installed in dep_results.items() if not installed]
    if missing_tools:
        critical_issues.append(f"Missing tools: {', '.join(missing_tools)}")

    if not gcp_ok:
        warnings.append("GCP authentication not configured")

    if critical_issues:
        print(f"{RED}CRITICAL ISSUES:{NC}")
        for issue in critical_issues:
            print(f"  - {issue}")
        print()

    if warnings:
        print(f"{YELLOW}WARNINGS:{NC}")
        for warning in warnings:
            print(f"  - {warning}")
        print()

    if not critical_issues and not warnings:
        print(f"{GREEN}All checks passed! Environment is properly configured.{NC}")
    elif not critical_issues:
        print(f"{YELLOW}Environment is functional but has warnings.{NC}")
    else:
        print(f"{RED}Environment has critical issues that must be resolved.{NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
