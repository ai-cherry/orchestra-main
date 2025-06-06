"""
"""
    """Retry decorator with exponential backoff."""
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. " f"Retrying in {wait_time} seconds..."
                    )
                    # TODO: Replace with asyncio.sleep() for async code
                    time.sleep(wait_time)
            return None

        return wrapper

    return decorator

class APIKeyManager:
    """Manages API keys for various services."""
        """Load API keys from environment variables."""
        services = ["OPENAI", "ANTHROPIC", "GOOGLE", "GEMINI"]
        for service in services:
            key_name = f"{service}_API_KEY"
            self.keys[service.lower()] = os.getenv(key_name)
            if self.keys[service.lower()]:
                logger.info(f"Loaded API key for {service}")
            else:
                logger.warning(f"No API key found for {service} (looking for {key_name})")

    def get_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service."""
        """Check if API key exists for a service."""
        """Set API key for a service (runtime only)."""
        logger.info(f"Updated API key for {service}")

def get_LAMBDA_PROJECT_ID() -> str:
    """Get the Lambda project ID from environment or default."""
    project_id = os.getenv("LAMBDA_PROJECT_ID")
    if not project_id:
        logger.warning("LAMBDA_PROJECT_ID not set, using default 'cherry-ai-project'")
        return "cherry-ai-project"
    return project_id

def setup_logging(level: str = "INFO"):
    """Configure logging for the application."""
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

def load_env_file(env_file: str = ".env"):
    """Load environment variables from a .env file if it exists."""
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
            logger.info(f"Loaded environment from {env_file}")
        except Exception:

            pass
            logger.error(f"Failed to load {env_file}: {e}")
    else:
        logger.warning(f"No {env_file} file found")
