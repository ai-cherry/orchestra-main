"""Simple authentication for single-user deployment."""

from .simple_auth import api_key_header, require_auth, verify_api_key

__all__ = ["verify_api_key", "require_auth", "api_key_header"]
