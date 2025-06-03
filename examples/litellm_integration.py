#!/usr/bin/env python3
"""
"""
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("litellm-example")

# Apply nest_asyncio to handle event loop issues when mixing async libraries (httpx/aiohttp)
try:

    pass
    import nest_asyncio

    nest_asyncio.apply()
    logger.info("Applied nest_asyncio to handle event loop conflicts")
except Exception:

    pass
    logger.warning("nest_asyncio not found, may encounter event loop issues with mixed async libraries")

try:


    pass
    import litellm
    from litellm import completion
except Exception:

    pass
    logger.error("LiteLLM not installed. Run: poetry install")
    sys.exit(1)

# Try to import optional dependencies
try:

    pass
    import portkey_ai

    HAS_PORTKEY = True
except Exception:

    pass
    HAS_PORTKEY = False
    logger.warning("Portkey not installed. Run: poetry install --with llm_gateways")

try:


    pass
    pass

    HAS_OPENROUTER = True
    # Set OpenRouter environment variables if not already set
    if not os.environ.get("OR_SITE_URL"):
        os.environ["OR_SITE_URL"] = "https://orchestra.example.com"
    if not os.environ.get("OR_APP_NAME"):
        os.environ["OR_APP_NAME"] = "OrchestraLLM"
    logger.info(f"OpenRouter configured with site: {os.environ.get('OR_SITE_URL')}")
except Exception:

    pass
    HAS_OPENROUTER = False
    logger.warning("OpenRouter not installed. Run: poetry install --with llm_gateways")

def setup_litellm() -> None:
    """Initialize LiteLLM with configuration"""
    config_path = Path(__file__).parent.parent / "config" / "litellm_config.yaml"

    if config_path.exists():
        logger.info(f"Loading LiteLLM config from {config_path}")
        litellm.config.load_config(str(config_path))
        # Override with environment variables if needed
        if os.getenv("LITELLM_VERBOSE"):
            litellm.set_verbose = os.getenv("LITELLM_VERBOSE").lower() == "true"
    else:
        logger.warning(f"Config file not found at {config_path}, using environment variables")
        # Configure LiteLLM with environment variables
        litellm.set_verbose = os.getenv("LITELLM_VERBOSE", "false").lower() == "true"

        # Add model mappings
        if os.getenv("AZURE_API_KEY") and os.getenv("AZURE_API_BASE"):
            litellm.add_model(
                {
                    "model_name": "gpt-4",
                    "litellm_params": {
                        "model": "azure/gpt-4",
                        "api_key": os.getenv("AZURE_API_KEY"),
                        "api_base": os.getenv("AZURE_API_BASE"),
                        "api_version": "2023-07-01-preview",
                    },
                }
            )

        if os.getenv("ANTHROPIC_API_KEY"):
            litellm.add_model(
                {
                    "model_name": "claude-3-opus",
                    "litellm_params": {
                        "model": "anthropic/claude-3-opus-20240229",
                        "api_key": os.getenv("ANTHROPIC_API_KEY"),
                    },
                }
            )

    # Set up fallback strategy if not in config
    if not hasattr(litellm.config, "fallbacks") or not litellm.config.fallbacks:
        litellm.fallbacks = [
            {"gpt-4": ["claude-3-opus"]},
            {"claude-3-opus": ["gpt-4"]},
        ]

    # Enable caching if Redis is available
    if all(os.getenv(var) for var in ["REDIS_HOST", "REDIS_PORT"]):
        redis_url = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"
        if os.getenv("REDIS_PASSWORD"):
            redis_url = f"redis://:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}"
        litellm.cache = litellm.Cache(type="redis", redis_url=redis_url)
        logger.info("Redis caching enabled")

def basic_completion_example() -> None:
    """Demonstrate basic completion with LiteLLM"""
    logger.info("Running basic completion example...")

    prompt = "Explain the advantages of using Poetry for Python dependency management in 3 bullet points."

    try:


        pass
        response = completion(
            model="gpt-3.5-turbo",  # Will be routed to the appropriate provider
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )

        logger.info(f"Response from: {response.model}")
        logger.info(f"Content: {response.choices[0].message.content}")
        logger.info(
            f"Tokens: {response.usage.total_tokens} (Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens})"
        )
        logger.info(f"Cost: ${response.usage.cost_usd:.6f} USD")

    except Exception:


        pass
        logger.error(f"Error in basic completion: {str(e)}")

def advanced_routing_example(input_length: int = 500) -> None:
    """Demonstrate advanced routing based on input length"""
    logger.info("Running advanced routing example...")

    # Generate a prompt of the specified length (roughly)
    words_per_char = 1 / 6  # Approximate words per character
    word_count = int(input_length * words_per_char)
    prompt = f"Write {word_count} words about Poetry, the Python dependency management tool."

    try:


        pass
        # For shorter prompts, use a smaller model
        if len(prompt) < 1000:
            logger.info("Using standard model for short prompt")
            model = "gpt-3.5-turbo"
        else:
            # For longer prompts, use a model with larger context window
            logger.info("Using model with larger context for long prompt")
            model = "gpt-4"

        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )

        logger.info(f"Response from: {response.model}")
        logger.info(f"Content snippet: {response.choices[0].message.content[:100]}...")
        logger.info(f"Tokens: {response.usage.total_tokens}")

    except Exception:


        pass
        logger.error(f"Error in advanced routing: {str(e)}")

def portkey_integration_example() -> None:
    """Demonstrate integration with Portkey for advanced features"""
        logger.warning("Skipping Portkey example - package not installed")
        return

    logger.info("Running Portkey integration example...")

    prompt = "What are the key considerations when choosing between LiteLLM, Portkey, and OpenRouter?"

    try:


        pass
        # Initialize Portkey
        portkey = portkey_ai.Portkey(
            api_key=os.getenv("PORTKEY_API_KEY", "demo"),
            virtual_key=os.getenv("PORTKEY_VIRTUAL_KEY"),
        )

        # Use Portkey with LiteLLM
        with portkey.as_litellm():
            response = completion(
                model="anthropic/claude-3-sonnet",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                metadata={
                    "trace_id": "portkey-demo-1",
                    "user_id": "example-user",
                },
            )

        logger.info(f"Portkey response from: {response.model}")
        logger.info(f"Content snippet: {response.choices[0].message.content[:100]}...")

    except Exception:


        pass
        logger.error(f"Error in Portkey integration: {str(e)}")

def openrouter_integration_example() -> None:
    """Demonstrate integration with OpenRouter for wide model access"""
        logger.warning("Skipping OpenRouter example - package not installed")
        return

    logger.info("Running OpenRouter integration example...")

    prompt = "Compare the performance characteristics of LLaMA 3 and Mixtral models."

    try:


        pass
        # Configure LiteLLM for OpenRouter
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        if not openrouter_key:
            logger.warning("OPENROUTER_API_KEY not set, using demo mode")

        # Use OpenRouter via LiteLLM
        response = completion(
            model="openrouter/anthropic/claude-3-haiku",  # OpenRouter model format
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            api_key=openrouter_key or None,  # Will use demo mode if empty
            api_base="https://openrouter.ai/api/v1",
        )

        logger.info(f"OpenRouter response from: {response.model}")
        logger.info(f"Content snippet: {response.choices[0].message.content[:100]}...")

    except Exception:


        pass
        logger.error(f"Error in OpenRouter integration: {str(e)}")

def fallback_example() -> None:
    """Demonstrate fallback behavior when a model fails"""
    logger.info("Running fallback example...")

    prompt = "Explain how LiteLLM handles fallbacks between different model providers."

    try:


        pass
        # Use a purposely invalid API key to trigger a fallback
        original_api_key = os.environ.get("AZURE_API_KEY", "")
        os.environ["AZURE_API_KEY"] = "invalid-key-to-trigger-fallback"

        response = completion(
            model="gpt-4",  # This should fail and trigger fallback to claude
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )

        logger.info(f"Fallback response from: {response.model}")
        logger.info(f"Content snippet: {response.choices[0].message.content[:100]}...")

    except Exception:


        pass
        logger.error(f"Error in fallback example: {str(e)}")
    finally:
        # Restore the original API key
        if original_api_key:
            os.environ["AZURE_API_KEY"] = original_api_key
        else:
            os.environ.pop("AZURE_API_KEY", None)

def multi_provider_example() -> None:
    """Demonstrate using all three tools in the same environment"""
        logger.warning("Skipping multi-provider example - required packages not installed")
        return

    logger.info("Running multi-provider example with LiteLLM, Portkey, and OpenRouter...")

    # Function to route requests based on requirements
    def smart_model_router(prompt: str, requirement: str) -> Dict:
        """Route to different providers based on requirements"""
        if requirement == "speed":
            # Use OpenRouter for edge-computing low latency
            return {
                "provider": "openrouter",
                "model": "openrouter/anthropic/claude-3-haiku",
                "api_base": "https://openrouter.ai/api/v1",
                "api_key": os.getenv("OPENROUTER_API_KEY", ""),
            }
        elif requirement == "governance":
            # Use Portkey for enterprise governance
            return {
                "provider": "portkey",
                "model": "anthropic/claude-3-sonnet",
                "virtual_key": os.getenv("PORTKEY_VIRTUAL_KEY", ""),
                "api_key": os.getenv("PORTKEY_API_KEY", "demo"),
            }
        else:  # "reliability"
            # Use LiteLLM for fallbacks and reliability
            return {
                "provider": "litellm",
                "model": "gpt-4",
            }

    test_cases = [
        {
            "prompt": "Summarize the advantages of edge computing in 2 sentences.",
            "requirement": "speed",
        },
        {
            "prompt": "What are the security implications of using multiple LLM providers?",
            "requirement": "governance",
        },
        {
            "prompt": "Explain the concept of model fallbacks in highly available systems.",
            "requirement": "reliability",
        },
    ]

    for case in test_cases:
        logger.info(f"Processing case with requirement: {case['requirement']}")
        route = smart_model_router(case["prompt"], case["requirement"])

        try:


            pass
            if route["provider"] == "openrouter":
                response = completion(
                    model=route["model"],
                    messages=[{"role": "user", "content": case["prompt"]}],
                    api_base=route["api_base"],
                    api_key=route["api_key"] or None,
                )
            elif route["provider"] == "portkey":
                portkey = portkey_ai.Portkey(
                    api_key=route["api_key"],
                    virtual_key=route["virtual_key"],
                )
                with portkey.as_litellm():
                    response = completion(
                        model=route["model"],
                        messages=[{"role": "user", "content": case["prompt"]}],
                    )
            else:  # litellm direct
                response = completion(
                    model=route["model"],
                    messages=[{"role": "user", "content": case["prompt"]}],
                )

            logger.info(f"Provider: {route['provider']}, Model: {response.model}")
            logger.info(f"Response: {response.choices[0].message.content[:100]}...")

        except Exception:


            pass
            logger.error(f"Error with {route['provider']}: {str(e)}")

if __name__ == "__main__":
    # Initialize LiteLLM
    setup_litellm()

    # Check for any required environment variables
    if not any(
        [
            os.getenv("AZURE_API_KEY"),
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("OPENROUTER_API_KEY"),
            os.getenv("PORTKEY_API_KEY"),
        ]
    ):
        logger.warning("No API keys detected. Examples will use demo mode where possible.")

    # Run examples
    try:

        pass
        basic_completion_example()
        advanced_routing_example()

        if HAS_PORTKEY:
            portkey_integration_example()

        if HAS_OPENROUTER:
            openrouter_integration_example()

        # Only run if both are available
        if all(os.getenv(var) for var in ["AZURE_API_KEY", "ANTHROPIC_API_KEY"]):
            fallback_example()

        if HAS_PORTKEY and HAS_OPENROUTER:
            multi_provider_example()

    except Exception:


        pass
        logger.info("Examples interrupted.")
        sys.exit(0)
    except Exception:

        pass
        logger.error(f"Error running examples: {str(e)}")
        sys.exit(1)

    logger.info("All examples completed successfully.")
