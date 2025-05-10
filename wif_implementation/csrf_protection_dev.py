"""
Simplified CSRF protection for single-developer mode.

This module provides a streamlined CSRF protection functionality for development use.
In development mode, CSRF checks can be optionally bypassed to make rapid iterations easier.
"""

import logging
import os
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
    in development mode for faster iteration.
    """
    
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
            import secrets
            secret_key = secrets.token_hex(16)
        
        self.secret_key = secret_key
        self.bypass_in_dev_mode = bypass_in_dev_mode or BYPASS_CSRF
        self.dev_mode = DEV_MODE
        self.verbose = verbose
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        if self.dev_mode and self.bypass_in_dev_mode:
            logger.warning("CSRF protection is DISABLED in development mode")
        
        logger.debug("Initialized development CSRF protection")
    
    def generate_token(self) -> str:
        """
        Generate a simplified CSRF token.
        
        Returns:
            A token string
        """
        # In development mode with bypass enabled, return a fixed token
        if self.dev_mode and self.bypass_in_dev_mode:
            return "dev-mode-csrf-token"
        
        # Otherwise, generate a simple token
        import base64
        import os
        import time
        
        # Generate a random token with timestamp
        random_bytes = os.urandom(16)
        timestamp = int(time.time())
        token = base64.urlsafe_b64encode(random_bytes).decode("utf-8")
        
        return f"{token}:{timestamp}"
    
    def validate_token(self, token: str) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token: The token to validate
            
        Returns:
            True if the token is valid, False otherwise
        """
        # In development mode with bypass enabled, always return true
        if self.dev_mode and self.bypass_in_dev_mode:
            logger.debug("CSRF validation bypassed in development mode")
            return True
        
        # Otherwise, do basic validation
        try:
            parts = token.split(":")
            if len(parts) != 2:
                logger.warning("Invalid token format")
                return False
            
            # Simple expiry check (24 hours)
            token_part, timestamp_str = parts
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


def csrf_protect_dev(request: Request) -> None:
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
            form_data = request.form()
            csrf_token = form_data.get("csrf_token")
        except:
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
