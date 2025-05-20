"""
CSRF Protection Loader.

This module loads the appropriate CSRF protection implementation based on environment variables.
It provides a consistent interface for CSRF protection across different environments.
"""

import os
import logging
from typing import Optional, Callable, Any

# Configure logging
logger = logging.getLogger("wif_implementation.csrf_loader")

# Check for development mode
DEV_MODE = os.environ.get("WIF_DEV_MODE", "false").lower() == "true"
BYPASS_CSRF = os.environ.get("WIF_BYPASS_CSRF", "false").lower() == "true"

# Define fallback imports in case primary imports fail
csrf_protection = None
csrf_protect = None

if DEV_MODE:
    logger.info("Loading development CSRF protection")
    try:
        from .csrf_protection_dev import csrf_protection_dev as csrf_protection
        from .csrf_protection_dev import csrf_protect_dev as csrf_protect

        logger.debug("Successfully loaded development CSRF protection")
    except ImportError as e:
        logger.warning(
            f"Development CSRF protection not found: {str(e)}, falling back to production version"
        )
        try:
            from .csrf_protection import csrf_protection, csrf_protect

            logger.debug("Successfully loaded production CSRF protection as fallback")
        except ImportError as e2:
            logger.error(f"Failed to import CSRF protection: {str(e2)}")
            raise RuntimeError("No CSRF protection implementation available") from e2
else:
    logger.info("Loading production CSRF protection")
    try:
        from .csrf_protection import csrf_protection, csrf_protect

        logger.debug("Successfully loaded production CSRF protection")
    except ImportError as e:
        logger.error(f"Failed to import production CSRF protection: {str(e)}")
        raise RuntimeError("No CSRF protection implementation available") from e

# Verify that imports succeeded
if csrf_protection is None or csrf_protect is None:
    logger.error("CSRF protection imports failed")
    raise RuntimeError("CSRF protection initialization failed")

__all__ = ["csrf_protection", "csrf_protect"]
