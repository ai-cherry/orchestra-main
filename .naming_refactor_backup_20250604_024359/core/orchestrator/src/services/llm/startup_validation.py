"""
        logger.error("LLM environment validation failed. See logs for details.")
        sys.exit(1)
"""
    "litellm": {
        "required": [],
        "optional": ["LITELLM_MASTER_KEY", "LITELLM_VERBOSE", "LITELLM_LOG"],
    },
    "openai": {
        "required": ["OPENAI_API_KEY"],
        "optional": ["OPENAI_API_BASE", "OPENAI_API_VERSION", "OPENAI_ORGANIZATION"],
    },
    "azure": {
        "required": ["AZURE_API_KEY", "AZURE_API_BASE"],
        "optional": ["AZURE_API_VERSION"],
    },
    "anthropic": {"required": ["ANTHROPIC_API_KEY"], "optional": ["ANTHROPIC_VERSION"]},
    "portkey": {
        "required": ["PORTKEY_API_KEY"],
        "optional": ["PORTKEY_CONFIG", "PORTKEY_VIRTUAL_KEY"],
    },
    "openrouter": {
        "required": ["OPENROUTER_API_KEY"],
        "optional": ["OR_SITE_URL", "OR_APP_NAME"],
    },
    "redis": {
        "required": [],
        "optional": ["REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD"],
    },
}

# Required Python packages for each provider
PROVIDER_REQUIRED_PACKAGES = {
    "litellm": ["litellm", "httpx", "pyjwt"],
    "portkey": ["portkey_ai", "aiohttp", "authlib"],
    "openrouter": ["openrouter", "httpx"],
    "redis": ["redis"],
    "google_cloud": ["google-cloud-secretmanager", "google-auth"],
    "monitoring": ["prometheus_client"],
    "retry": ["tenacity"],
}

def check_docker_buildkit_support() -> bool:
    """
    """
    if os.environ.get("DOCKER_BUILDKIT") == "1":
        return True

    # Check Docker version
    try:

        pass
        import subprocess

        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=True)
        version_str = result.stdout

        # Parse version string
        import re

        match = re.search(r"version (\d+)\.(\d+)\.(\d+)", version_str)
        if match:
            major, minor, patch = map(int, match.groups())
            # BuildKit is integrated since Docker 18.09
            if (major > 18) or (major == 18 and minor >= 9):
                return True
    except Exception:

        pass
        logger.warning(f"Error checking Docker version: {str(e)}")

    return False

def check_environment_variables(
    providers: Optional[List[str]] = None,
) -> Tuple[bool, Dict[str, List[str]]]:
    """
    """
            logger.warning(f"Unknown provider: {provider}")
            continue

        provider_missing = []
        for var in PROVIDER_REQUIRED_ENV_VARS[provider]["required"]:
            if not os.environ.get(var):
                provider_missing.append(var)

        if provider_missing:
            missing_vars[provider] = provider_missing
            success = False

    return success, missing_vars

def check_optional_environment_variables(
    providers: Optional[List[str]] = None,
) -> Dict[str, List[str]]:
    """
    """
        for var in PROVIDER_REQUIRED_ENV_VARS[provider]["optional"]:
            if not os.environ.get(var):
                provider_missing.append(var)

        if provider_missing:
            missing_vars[provider] = provider_missing

    return missing_vars

def check_package_availability(provider: str) -> Tuple[bool, List[str]]:
    """
    """
            importlib.import_module(package.replace("-", "_"))
        except Exception:

            pass
            missing_packages.append(package)

    return len(missing_packages) == 0, missing_packages

def init_providers(providers: Optional[List[str]] = None) -> bool:
    """
    """
        providers = ["litellm", "portkey", "openrouter"]

    success = True

    # Try to import and initialize provider-specific modules
    for provider in providers:
        # LiteLLM
        if provider == "litellm":
            try:

                pass
                import litellm

                litellm.set_verbose = os.environ.get("LITELLM_VERBOSE", "false").lower() == "true"
                logger.info("LiteLLM initialized successfully")
            except Exception:

                pass
                logger.warning("LiteLLM not available. Install with: pip install litellm")
                success = False
            except Exception:

                pass
                logger.error(f"Error initializing LiteLLM: {str(e)}")
                success = False

        # Portkey
        elif provider == "portkey":
            try:

                pass
                pass

                logger.info("Portkey initialized successfully")
            except Exception:

                pass
                logger.warning("Portkey not available. Install with: pip install portkey-ai")
                # Not critical, don't set success to False
            except Exception:

                pass
                logger.error(f"Error initializing Portkey: {str(e)}")
                # Not critical, don't set success to False

        # OpenRouter
        elif provider == "openrouter":
            try:

                pass
                pass

                # Set OpenRouter environment variables if not already set
                if not os.environ.get("OR_SITE_URL"):
                    os.environ["OR_SITE_URL"] = "https://cherry_ai.example.com"
                    logger.info("Set default OR_SITE_URL")
                if not os.environ.get("OR_APP_NAME"):
                    os.environ["OR_APP_NAME"] = "cherry_aiLLM"
                    logger.info("Set default OR_APP_NAME")

                logger.info("OpenRouter initialized successfully")
            except Exception:

                pass
                logger.warning("OpenRouter not available. Install with: pip install openrouter")
                # Not critical, don't set success to False
            except Exception:

                pass
                logger.error(f"Error initializing OpenRouter: {str(e)}")
                # Not critical, don't set success to False

    return success

def init_secret_manager() -> bool:
    """
    """
        project_id = os.environ.get("VULTR_PROJECT_ID")

        # Initialize the Secret Manager
        secret_manager = get_secret_manager(project_id=project_id)

        # Test getting a secret
        test_key = None
        for key in ["LITELLM_MASTER_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            if os.environ.get(key):
                test_key = key
                break

        if test_key:
            value = secret_manager.get_secret(test_key)
            if value:
                logger.info("Secret Manager initialized and tested successfully")
                return True
            else:
                logger.warning("Secret Manager initialized but test secret not found")
                return True  # Still return True since this isn't critical
        else:
            logger.warning("Secret Manager initialized but no test keys available")
            return True  # Still return True since this isn't critical

    except Exception:


        pass
        logger.warning("Secret Manager module not available")
        return True  # Not critical, can fall back to environment variables
    except Exception:

        pass
        logger.error(f"Error initializing Secret Manager: {str(e)}")
        return False

def init_circuit_breaker() -> bool:
    """
    """
        logger.info("Circuit Breaker initialized successfully")

        # Start Prometheus server if available and configured
        if os.environ.get("START_METRICS_SERVER", "").lower() == "true":
            try:

                pass
                import prometheus_client

                prometheus_client.start_http_server(port=int(os.environ.get("METRICS_PORT", "8000")))
                logger.info(f"Prometheus metrics server started on port {os.environ.get('METRICS_PORT', '8000')}")
            except Exception:

                pass
                logger.warning("Prometheus client not available. Metrics server not started.")
            except Exception:

                pass
                logger.error(f"Error starting Prometheus metrics server: {str(e)}")

        return True
    except Exception:

        pass
        logger.warning("Circuit Breaker module not available")
        return True  # Not critical
    except Exception:

        pass
        logger.error(f"Error initializing Circuit Breaker: {str(e)}")
        return False

def setup_header_validation(app: Any) -> bool:
    """
    """
        app.middleware("http")(validate_headers_middleware)

        logger.info("Header validation middleware set up successfully")
        return True
    except Exception:

        pass
        logger.warning("Header validation module not available")
        return True  # Not critical
    except Exception:

        pass
        logger.error(f"Error setting up header validation: {str(e)}")
        return False

def validate_poetry_install() -> bool:
    """
    """
        result = subprocess.run(["poetry", "env", "info"], capture_output=True, text=True, check=True)

        logger.info("Poetry environment is available")

        # Check for the existence of our custom dependency groups
        result = subprocess.run(["poetry", "show", "--tree"], capture_output=True, text=True)

        # List of packages that should be present
        required_packages = [
            "litellm",
            "httpx",
            "pyjwt",
            "tenacity",
            "prometheus-client",
            "google-cloud-secretmanager",
        ]

        missing = []
        for package in required_packages:
            if package not in result.stdout:
                missing.append(package)

        if missing:
            missing_str = ", ".join(missing)
            logger.warning(f"Missing required packages: {missing_str}")
            logger.warning("Run: poetry install --with litellm,portkey,openrouter")
            return False

        return True
    except Exception:

        pass
        logger.warning("Poetry environment not available or command failed")
        return False
    except Exception:

        pass
        logger.error(f"Error validating Poetry environment: {str(e)}")
        return False

def validate_llm_environment() -> bool:
    """
    """
    if os.environ.get("CONTAINER", "").lower() == "true":
        buildkit_supported = check_docker_buildkit_support()
        if not buildkit_supported:
            logger.warning("Docker BuildKit not supported. Container builds may fail.")
            logger.warning("Set DOCKER_BUILDKIT=1 environment variable before building.")
            # This is not critical for runtime, so don't set success to False

    # Check required environment variables
    env_success, missing_vars = check_environment_variables()
    if not env_success:
        for provider, vars in missing_vars.items():
            vars_str = ", ".join(vars)
            logger.error(f"Missing required environment variables for {provider}: {vars_str}")
        success = False

    # Check optional environment variables
    missing_optional = check_optional_environment_variables()
    for provider, vars in missing_optional.items():
        vars_str = ", ".join(vars)
        logger.warning(f"Missing optional environment variables for {provider}: {vars_str}")

    # Validate Poetry install
    poetry_success = validate_poetry_install()
    if not poetry_success:
        logger.warning("Poetry environment validation failed. Some features may not work.")
        # Not critical for runtime if dependencies were installed through other means

    # Initialize providers
    providers_success = init_providers()
    if not providers_success:
        logger.error("Failed to initialize LLM providers")
        success = False

    # Initialize Secret Manager
    secret_manager_success = init_secret_manager()
    if not secret_manager_success:
        logger.error("Failed to initialize Secret Manager")
        success = False

    # Initialize Circuit Breaker
    circuit_breaker_success = init_circuit_breaker()
    if not circuit_breaker_success:
        logger.error("Failed to initialize Circuit Breaker")
        success = False

    if success:
        logger.info("LLM environment validation completed successfully")
    else:
        logger.error("LLM environment validation failed")

    return success

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run validation and exit with appropriate status code
    success = validate_llm_environment()
    if not success:
        logger.error("LLM environment validation failed. Fix issues before deployment.")
        sys.exit(1)
    else:
        logger.info("LLM environment is valid and ready for deployment.")
        sys.exit(0)
