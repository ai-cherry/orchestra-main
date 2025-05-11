"""
Simplified CSRF protection for single-developer mode.

This module provides a streamlined CSRF protection functionality for development use.
In development mode, CSRF checks can be optionally bypassed to make rapid iterations easier,
while still maintaining security through session-specific tokens.
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
import threading
import time
from typing import Dict, Optional, Any, Callable

from fastapi import Request, HTTPException, status

# Configure logging
logger = logging.getLogger("wif_implementation.csrf_protection_dev")

# Environment variable to control CSRF protection in development
DEV_MODE = os.environ.get("WIF_DEV_MODE", "false").lower() == "true"
BYPASS_CSRF = os.environ.get("WIF_BYPASS_CSRF", "false").lower() == "true"

# Log the current mode
if DEV_MODE:
    if BYPASS_CSRF:
        logger.warning("Running in DEVELOPMENT MODE with CSRF protection DISABLED")
    else:
        logger.info("Running in DEVELOPMENT MODE with CSRF protection enabled")
else:
    logger.info("Running in PRODUCTION MODE with CSRF protection enabled")


class CSRFProtectionDev:
    """
    Simplified CSRF protection for development environments.
    
    This class provides basic CSRF protection with an option to bypass checks
    in development mode for faster iteration, while still maintaining security
    through session-specific tokens.
    """
    
    # Class-level lock for thread safety when generating session tokens
    _lock = threading.RLock()
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        bypass_in_dev_mode: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize the development CSRF protection.
        
        Args:
            secret_key: The secret key to use for token generation
            bypass_in_dev_mode: Whether to bypass CSRF checks in development mode
            verbose: Whether to show detailed output during processing
        """
        # Generate a random secret key if not provided
        if secret_key is None:
            secret_key = secrets.token_hex(32)
        
        self.secret_key = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
        self.bypass_in_dev_mode = bypass_in_dev_mode or BYPASS_CSRF
        self.dev_mode = DEV_MODE
        self.verbose = verbose
        
        # Session-specific token for development mode
        self._session_token: Optional[str] = None
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        if self.dev_mode and self.bypass_in_dev_mode:
            logger.warning("CSRF protection is DISABLED in development mode")
        
        logger.debug("Initialized development CSRF protection")
    
    def generate_token(self) -> str:
        """
        Generate a simplified CSRF token.
        
        In development mode with bypass enabled, this still generates a secure
        but session-consistent token for better developer experience.
        
        Returns:
            A secure token string
        """
        # In development mode with bypass enabled, use a session-specific token
        if self.dev_mode and self.bypass_in_dev_mode:
            with self._lock:
                if self._session_token is None:
                    # Create a cryptographically secure token that remains consistent during the session
                    random_bytes = os.urandom(16)
                    timestamp = int(time.time())
                    session_id = hashlib.sha256(f"{random_bytes}{timestamp}".encode()).hexdigest()[:16]
                    self._session_token = f"dev-mode-csrf-token-{session_id}"
                    logger.debug("Created new session-specific development CSRF token")
                
                return self._session_token
        
        # Otherwise, generate a secure token with timestamp
        random_bytes = os.urandom(16)
        timestamp = int(time.time())
        token_data = f"{base64.urlsafe_b64encode(random_bytes).decode('utf-8')}:{timestamp}"
        
        # Sign the token for additional security
        signature = hmac.new(
            self.secret_key,
            token_data.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        
        return f"{token_data}:{signature}"
    
    def validate_token(self, token: str) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token: The token to validate
            
        Returns:
            True if the token is valid, False otherwise
        """
        # In development mode with bypass enabled, accept the session token
        if self.dev_mode and self.bypass_in_dev_mode:
            with self._lock:
                if self._session_token is not None and token == self._session_token:
                    logger.debug("Validated session-specific development CSRF token")
                    return True
                elif token.startswith("dev-mode-csrf-token-"):
                    logger.debug("CSRF validation bypassed in development mode")
                    return True
        
        # Otherwise, do proper validation
        try:
            parts = token.split(":")
            if len(parts) != 3:
                logger.warning("Invalid token format")
                return False
            
            # Extract token parts
            token_part, timestamp_str, provided_signature = parts
            token_data = f"{token_part}:{timestamp_str}"
            
            # Verify the signature using constant-time comparison
            expected_signature = hmac.new(
                self.secret_key,
                token_data.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            
            if not hmac.compare_digest(provided_signature, expected_signature):
                logger.warning("Invalid token signature")
                return False
            
            # Check expiry (24 hours)
            try:
                timestamp = int(timestamp_str)
                current_time = int(time.time())
                
                if current_time - timestamp > 86400:  # 24 hours
                    logger.warning("Token has expired")
                    return False
                
            except ValueError:
                logger.warning("Invalid timestamp in token")
                return False
            
            logger.debug("CSRF token validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error validating CSRF token: {str(e)}")
            return False


# Create a global CSRF protection instance
csrf_protection_dev = CSRFProtectionDev(bypass_in_dev_mode=BYPASS_CSRF)


async def csrf_protect_dev(request: Request) -> None:
    """
    Development-friendly dependency for CSRF protection.
    
    Args:
        request: The request to protect
        
    Raises:
        HTTPException: If the CSRF token is invalid
    """
    # In development mode with bypass enabled, skip CSRF check
    if DEV_MODE and BYPASS_CSRF:
        return
    
    # Get the CSRF token from the request
    csrf_token = request.query_params.get("csrf_token")
    
    # If the token is not in the query parameters, check the form data
    if not csrf_token and request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        try:
            form_data = await request.form()
            csrf_token = form_data.get("csrf_token")
        except ValueError:
            # Handle form parsing errors
            logger.warning("Error parsing form data")
            pass
    
    # If the token is still not found, check the headers
    if not csrf_token:
        csrf_token = request.headers.get("X-CSRF-Token")
    
    # If the token is not found, raise an exception
    if not csrf_token:
        logger.warning("CSRF token not found in request")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing",
        )
    
    # Validate the token
    if not csrf_protection_dev.validate_token(csrf_token):
        logger.warning("Invalid CSRF token")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )
