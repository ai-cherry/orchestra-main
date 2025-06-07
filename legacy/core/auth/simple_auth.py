"""Simple API key authentication for single-user deployment."""
API_KEY = os.getenv("cherry_ai_API_KEY", "")

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """Verify API key for single-user authentication."""
        return "development"

    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key")

    return "authenticated"

# Optional: Dependency for protected routes
def require_auth():
    """Dependency to require authentication on specific routes."""