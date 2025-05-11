"""
CSRF protection for the WIF implementation.

This module provides CSRF protection functionality for the WIF implementation.
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
import time
from typing import Dict, List, Optional, Set, Tuple, Union, Any, Callable

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .error_handler import WIFError, ErrorSeverity, handle_exception

# Configure logging
logger = logging.getLogger("wif_implementation.csrf_protection")


class CSRFError(WIFError):
    """Exception raised when there is a CSRF error."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize the error.
        
        Args:
            message: The error message
            details: Additional details about the error
            cause: The underlying exception that caused this error
        """
        super().__init__(
            message=message,
            severity=ErrorSeverity.ERROR,
            details=details,
            cause=cause,
        )


class CSRFProtection:
    """
    CSRF protection for the WIF implementation.
    
    This class provides CSRF protection functionality for the WIF implementation.
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        token_expiry: int = 3600,  # 1 hour
        verbose: bool = False,
    ):
        """
        Initialize the CSRF protection.
        
        Args:
            secret_key: The secret key to use for token generation
            token_expiry: The token expiry time in seconds
            verbose: Whether to show detailed output during processing
        """
        # If secret_key is not provided, generate a random one
        if secret_key is None:
            secret_key = secrets.token_hex(32)
        
        self.secret_key = secret_key.encode("utf-8")
        self.token_expiry = token_expiry
        self.verbose = verbose
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.debug("Initialized CSRF protection")
    
    @handle_exception
    def generate_token(self) -> str:
        """
        Generate a CSRF token.
        
        Returns:
            The generated token
            
        Raises:
            CSRFError: If the token cannot be generated
        """
        try:
            # Generate a random token
            random_bytes = os.urandom(32)
            random_token = base64.urlsafe_b64encode(random_bytes).decode("utf-8")
            
            # Add timestamp to the token
            timestamp = int(time.time())
            token_data = f"{random_token}:{timestamp}"
            
            # Sign the token
            signature = hmac.new(
                self.secret_key,
                token_data.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            
            # Combine token data and signature
            token = f"{token_data}:{signature}"
            
            logger.debug("CSRF token generated successfully")
            return token
            
        except Exception as e:
            logger.error(f"Error generating CSRF token: {str(e)}")
            raise CSRFError(
                f"Failed to generate CSRF token",
                cause=e,
            )
    
    @handle_exception
    def validate_token(self, token: str) -> bool:
        """
        Validate a CSRF token.
        
        Args:
            token: The token to validate
            
        Returns:
            True if the token is valid, False otherwise
            
        Raises:
            CSRFError: If the token cannot be validated
        """
        try:
            # Split the token into data and signature
            parts = token.split(":")
            if len(parts) != 3:
                logger.warning("Invalid token format")
                return False
            
            random_token, timestamp_str, signature = parts
            
            # Reconstruct the token data
            token_data = f"{random_token}:{timestamp_str}"
            
            # Verify the signature
            expected_signature = hmac.new(
                self.secret_key,
                token_data.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("Invalid token signature")
                return False
            
            # Check if the token has expired
            try:
                timestamp = int(timestamp_str)
                current_time = int(time.time())
                
                if current_time - timestamp > self.token_expiry:
                    logger.warning("Token has expired")
                    return False
                
            except ValueError:
                logger.warning("Invalid timestamp in token")
                return False
            
            logger.debug("CSRF token validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error validating CSRF token: {str(e)}")
            raise CSRFError(
                f"Failed to validate CSRF token",
                cause=e,
            )


# Create a global CSRF protection instance
csrf_protection = CSRFProtection()


async def csrf_protect(request: Request) -> None:
    """
    Dependency for CSRF protection.
    
    Args:
        request: The request to protect
        
    Raises:
        HTTPException: If the CSRF token is invalid
    """
    # Get the CSRF token from the request
    csrf_token = request.query_params.get("csrf_token")
    
    # If the token is not in the query parameters, check the form data
    if not csrf_token and request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        try:
            form_data = await request.form()
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
    if not csrf_protection.validate_token(csrf_token):
        logger.warning("Invalid CSRF token")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )
