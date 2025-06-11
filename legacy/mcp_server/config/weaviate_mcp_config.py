#!/usr/bin/env python3
"""
"""
WEAVIATE_HOST: str = os.getenv("WEAVIATE_HOST", "localhost")
WEAVIATE_PORT: int = int(os.getenv("WEAVIATE_PORT", "8080"))
WEAVIATE_GRPC_PORT: int = int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))
WEAVIATE_SECURED: bool = os.getenv("WEAVIATE_SECURED", "false").lower() == "true"
WEAVIATE_SKIP_VERIFICATION: bool = os.getenv("WEAVIATE_SKIP_VERIFICATION", "false").lower() == "true"

# Authentication: Choose ONE method. API Key is common for many cloud/self-hosted.
# WCS or specific OAuth setups might use Client ID/Secret.
# Username/Password is less common for Weaviate but supported by some modules.

# 1. API Key Authentication (e.g., for Weaviate Cloud Services, or self-hosted with API key auth)
WEAVIATE_API_KEY: Optional[str] = os.getenv("WEAVIATE_API_KEY")

# 2. OAuth 2.0 Client Credentials Grant (e.g., some WCS setups or custom OIDC)
WEAVIATE_CLIENT_ID: Optional[str] = os.getenv("WEAVIATE_CLIENT_ID")
WEAVIATE_CLIENT_SECRET: Optional[str] = os.getenv("WEAVIATE_CLIENT_SECRET")
# WEAVIATE_SCOPE: Optional[str] = os.getenv("WEAVIATE_SCOPE") # Usually not needed for client.connect_to_custom

# 3. Username/Password Authentication (less common for Weaviate direct, but some modules might use it)
WEAVIATE_USERNAME: Optional[str] = os.getenv("WEAVIATE_USERNAME")
WEAVIATE_PASSWORD: Optional[str] = os.getenv("WEAVIATE_PASSWORD")

# Additional Headers (e.g., for custom proxy authentication, module-specific headers)
# Should be a JSON string like: '{"X-My-Header": "value", "Authorization": "Bearer ..."}'
WEAVIATE_ADDITIONAL_HEADERS_JSON: Optional[str] = os.getenv("WEAVIATE_ADDITIONAL_HEADERS")

def log_weaviate_config() -> None:
    """Logs the loaded Weaviate configuration, masking sensitive details."""
    logger.info("[Weaviate MCP Config Loaded]")
    logger.info(f"  HOST: {WEAVIATE_HOST}")
    logger.info(f"  HTTP PORT: {WEAVIATE_PORT}")
    logger.info(f"  GRPC PORT: {WEAVIATE_GRPC_PORT}")
    logger.info(f"  SECURED (TLS): {WEAVIATE_SECURED}")
    logger.info(f"  SKIP_TLS_VERIFICATION: {WEAVIATE_SKIP_VERIFICATION}")

    if WEAVIATE_API_KEY:
        logger.info("  Auth Method: API Key (set)")
    elif WEAVIATE_CLIENT_ID and WEAVIATE_CLIENT_SECRET:
        logger.info("  Auth Method: Client Credentials (set)")
    elif WEAVIATE_USERNAME and WEAVIATE_PASSWORD:
        logger.info("  Auth Method: Username/Password (set)")
    else:
        logger.info("  Auth Method: None or via Additional Headers")

    if WEAVIATE_ADDITIONAL_HEADERS_JSON:
        try:

            pass
            headers = json.loads(WEAVIATE_ADDITIONAL_HEADERS_JSON)
            masked_headers = {
                k: "****" if "key" in k.lower() or "token" in k.lower() or "auth" in k.lower() else v
                for k, v in headers.items()
            }
            logger.info(f"  Additional Headers: {masked_headers}")
        except Exception:

            pass
            logger.warning("  Additional Headers: Invalid JSON string provided.")
    else:
        logger.info("  Additional Headers: Not set")

def validate_weaviate_config() -> bool:
    """
    """
        logger.error("ERROR: WEAVIATE_HOST is not configured.")
        return False
    if not isinstance(WEAVIATE_PORT, int) or not (0 < WEAVIATE_PORT <= 65535):
        logger.error(f"ERROR: Invalid WEAVIATE_PORT: {WEAVIATE_PORT}")
        return False
    if not isinstance(WEAVIATE_GRPC_PORT, int) or not (0 < WEAVIATE_GRPC_PORT <= 65535):
        logger.error(f"ERROR: Invalid WEAVIATE_GRPC_PORT: {WEAVIATE_GRPC_PORT}")
        return False

    # Log the (masked) configuration details after validation
    log_weaviate_config()
    return True

def get_weaviate_client_params() -> Dict[str, Any]:
    """
    """
        "http_host": WEAVIATE_HOST,
        "http_port": WEAVIATE_PORT,
        "http_secure": WEAVIATE_SECURED,
        "grpc_host": WEAVIATE_HOST,  # Assuming gRPC is on the same host by default
        "grpc_port": WEAVIATE_GRPC_PORT,
        "grpc_secure": WEAVIATE_SECURED,
        "skip_init_checks": False,  # Perform initial checks by default
    }

    # Authentication
    auth_credentials: Optional[Union[AuthApiKey, AuthClientPassword, AuthClientCredentials]] = None
    if WEAVIATE_API_KEY:
        auth_credentials = AuthApiKey(api_key=WEAVIATE_API_KEY)
    elif WEAVIATE_CLIENT_ID and WEAVIATE_CLIENT_SECRET:
        # Note: Weaviate's AuthClientCredentials typically requires a token endpoint.
        # If direct client_id/secret is for a custom auth flow, it might need to go via headers.
        # For standard OAuth, the client library handles token fetching if configured correctly.
        # This example assumes it's for a flow supported by AuthClientCredentials or similar.
        # If not, headers are the way.
        logger.warning(
            "Using AuthClientCredentials. Ensure your Weaviate instance supports this directly "
            "or consider using WEAVIATE_ADDITIONAL_HEADERS for custom token mechanisms."
        )
        auth_credentials = AuthClientCredentials(
            client_secret=WEAVIATE_CLIENT_SECRET,
            # scope=WEAVIATE_SCOPE if WEAVIATE_SCOPE else [], # Scope is often optional or implicit
            # client_id=WEAVIATE_CLIENT_ID # client_id might not be needed for all flows
        )
    elif WEAVIATE_USERNAME and WEAVIATE_PASSWORD:
        auth_credentials = AuthClientPassword(username=WEAVIATE_USERNAME, password=WEAVIATE_PASSWORD)

    if auth_credentials:
        params["auth_client_secret"] = auth_credentials

    # Additional Headers
    headers: Dict[str, str] = {}
    if WEAVIATE_ADDITIONAL_HEADERS_JSON:
        try:

            pass
            headers.update(json.loads(WEAVIATE_ADDITIONAL_HEADERS_JSON))
        except Exception:

            pass
            logger.error(f"Failed to parse WEAVIATE_ADDITIONAL_HEADERS_JSON: {e}")
            # Potentially raise an error or continue without them

    # If an API key is provided and not handled by auth_credentials (e.g. some custom setups),
    # it might be expected in headers. Weaviate's AuthApiKey is preferred.
    # Example: if WEAVIATE_API_KEY and not auth_credentials:
    #    headers["X-Api-Key"] = WEAVIATE_API_KEY # Or whatever header Weaviate expects

    if headers:
        params["additional_headers"] = headers

    # TLS verification skip
    # This is typically handled by the client library's underlying HTTP/gRPC client
    # For `requests` (used by Weaviate client for HTTP), `verify=False`
    # For `grpc`, channel options.
    # The Weaviate client itself doesn't have a direct `skip_verify` at the top level
    # for `connect_to_custom`. This might need to be handled by configuring
    # the underlying `requests.Session` or gRPC channel if absolutely necessary,
    # but it's highly discouraged for production.
    # For now, we'll log a warning if WEAVIATE_SKIP_VERIFICATION is true.
    if WEAVIATE_SKIP_VERIFICATION:
        logger.warning(
            "WEAVIATE_SKIP_VERIFICATION is True. TLS certificate verification will be skipped. "
            "This is insecure and not recommended for production environments."
        )
        # Note: Actual skipping of verification needs to be handled when creating the client instance,
        # often by passing custom session or channel objects, or if the client directly supports it.
        # The Weaviate Python client v4's `ConnectionParams` for `connect_to_custom`
        # does not seem to have a direct `ssl_verify_cert=False` equivalent.
        # This might imply using `weaviate.connect_to_local(..., startup_period=None)` and then
        # manually configuring the client's internal session if absolutely needed, or ensuring
        # the environment (e.g., custom CA certs) is set up correctly.

    return params

__all__ = [
    "get_weaviate_client_params",
    "validate_weaviate_config",
    "log_weaviate_config",
    "WEAVIATE_HOST",
    "WEAVIATE_PORT",
    "WEAVIATE_GRPC_PORT",
    "WEAVIATE_SECURED",
    "WEAVIATE_API_KEY",
    "WEAVIATE_CLIENT_ID",
    "WEAVIATE_CLIENT_SECRET",
    "WEAVIATE_USERNAME",
    "WEAVIATE_PASSWORD",
    "WEAVIATE_ADDITIONAL_HEADERS_JSON",
    "WEAVIATE_SKIP_VERIFICATION",
]

if __name__ == "__main__":
    # Example usage and validation
    if validate_weaviate_config():
        logger.info("Weaviate configuration is valid.")
        client_params = get_weaviate_client_params()
        logger.info(f"Generated client params: {client_params}")
    else:
        logger.error("Invalid Weaviate configuration.")
