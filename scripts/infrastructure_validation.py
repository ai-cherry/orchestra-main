# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_status(service: str, status: bool, message: str = ""):
    """Print colored status message"""
    icon = "✅" if status else "❌"
    color = GREEN if status else RED
    print(f"{color}{icon} {service}: {message}{RESET}")

def print_header(title: str):
    """Print section header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def check_env_var(var_name: str) -> Tuple[bool, str]:
    """Check if environment variable is set"""
        masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        return True, masked
    return False, "Not set"

def test_digitalocean_api(token: str) -> Tuple[bool, str]:
    """Test DigitalOcean API access"""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("https://api.digitalocean.com/v2/account", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, f"Account: {data['account']['email']}"
        else:
            return False, f"API returned {response.status_code}"
    except Exception:

        pass
        return False, str(e)

        return True, f"Connected, {len(db_names)} databases found"
    except Exception:

        pass
        return False, str(e)

def test_weaviate_connection(url: str, api_key: str) -> Tuple[bool, str]:
    """Test Weaviate connection"""
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{url}/v1/meta", headers=headers, timeout=10)
        if response.status_code == 200:
            return True, "Weaviate cluster accessible"
        else:
            return False, f"API returned {response.status_code}"
    except Exception:

        pass
        return False, str(e)

def test_github_pat(pat: str) -> Tuple[bool, str]:
    """Test GitHub Personal Access Token"""
        headers = {"Authorization": f"token {pat}"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, f"User: {data['login']}"
        else:
            return False, f"API returned {response.status_code}"
    except Exception:

        pass
        return False, str(e)

def check_pulumi_state() -> Tuple[bool, str]:
    """Check Pulumi stack state"""
        if os.path.exists("infra"):
            os.chdir("infra")

        result = subprocess.run(["pulumi", "stack", "ls", "--json"], capture_output=True, text=True)
        if result.returncode == 0:
            stacks = json.loads(result.stdout)
            if stacks:
                current = next((s for s in stacks if s.get("current")), None)
                if current:
                    return True, f"Current stack: {current['name']}"
            return True, "No stacks configured yet"
        else:
            return False, "Pulumi not configured"
    except Exception:

        pass
        return False, str(e)
    finally:
        # Return to original directory
        if os.path.basename(os.getcwd()) == "infra":
            os.chdir("..")

def main():
    """Run all infrastructure validation tests"""
    print_header("Infrastructure Validation Report")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Check environment variables
    print_header("Environment Variables")

    required_vars = {
        "DIGITALOCEAN_TOKEN": "DigitalOcean API Token",
        "OPENAI_API_KEY": "OpenAI API Key",
        "WEAVIATE_API_KEY": "Weaviate API Key",
        "WEAVIATE_URL": "Weaviate Endpoint",
        "PULUMI_CONFIG_PASSPHRASE": "Pulumi Passphrase",
        "DO_ROOT_PASSWORD": "DigitalOcean Root Password",
        "GITHUB_PAT": "GitHub Personal Access Token",
    }

    env_status = {}
    for var, desc in required_vars.items():
        exists, value = check_env_var(var)
        env_status[var] = exists
        print_status(desc, exists, value)

    # 2. Test API connections
    print_header("API Connection Tests")

    # Test DigitalOcean
    if env_status.get("DIGITALOCEAN_TOKEN"):
        success, msg = test_digitalocean_api(os.environ["DIGITALOCEAN_TOKEN"])
        print_status("DigitalOcean API", success, msg)
    else:
        print_status("DigitalOcean API", False, "Token not set")

    else:

    # Test Weaviate
    if env_status.get("WEAVIATE_URL") and env_status.get("WEAVIATE_API_KEY"):
        success, msg = test_weaviate_connection(os.environ["WEAVIATE_URL"], os.environ["WEAVIATE_API_KEY"])
        print_status("Weaviate Connection", success, msg)
    else:
        print_status("Weaviate Connection", False, "URL or API key not set")

    # Test GitHub PAT
    if env_status.get("GITHUB_PAT"):
        success, msg = test_github_pat(os.environ["GITHUB_PAT"])
        print_status("GitHub API", success, msg)
    else:
        print_status("GitHub API", False, "PAT not set")

    # 3. Check Pulumi configuration
    print_header("Pulumi Configuration")

    success, msg = check_pulumi_state()
    print_status("Pulumi State", success, msg)

    # 4. Check required files
    print_header("Required Files")

    required_files = {
        "infra/do_superagi_stack.py": "DigitalOcean Stack Definition",
        "infra/requirements.txt": "Infrastructure Dependencies",
        ".github/workflows/deploy.yaml": "CI/CD Workflow",
        "scripts/setup_local_env.sh": "Local Setup Script",
    }

    for file_path, desc in required_files.items():
        exists = os.path.exists(file_path)
        print_status(desc, exists, "Found" if exists else "Missing")

    # 5. Summary
    print_header("Summary")

    total_checks = len(required_vars) + 4 + 1 + len(required_files)  # env + apis + pulumi + files
    passed_checks = sum(
        [
            sum(1 for exists in env_status.values() if exists),
            # Add other successful checks here
        ]
    )

    print(f"\nTotal checks: {total_checks}")
    print(f"Passed: {GREEN}{passed_checks}{RESET}")
    print(f"Failed: {RED}{total_checks - passed_checks}{RESET}")

    if total_checks == passed_checks:
        print(f"\n{GREEN}✅ All infrastructure checks passed!{RESET}")
        return 0
    else:
        print(f"\n{YELLOW}⚠️  Some checks failed. Review the output above.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
