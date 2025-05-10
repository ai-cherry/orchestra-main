"""
CSRF Protection Loader.

This module loads the appropriate CSRF protection implementation based on environment variables.
"""

import os
import logging

# Configure logging
logger = logging.getLogger("wif_implementation.csrf_loader")

# Check for development mode
DEV_MODE = os.environ.get("WIF_DEV_MODE", "false").lower() == "true"
BYPASS_CSRF = os.environ.get("WIF_BYPASS_CSRF", "false").lower() == "true"

if DEV_MODE:
    logger.info("Loading development CSRF protection")
    try:
        from .csrf_protection_dev import csrf_protection as csrf_protection
        from .csrf_protection_dev import csrf_protect_dev as csrf_protect
    except ImportError:
        logger.warning("Development CSRF protection not found, falling back to production version")
        from .csrf_protection import csrf_protection, csrf_protect
else:
    logger.info("Loading production CSRF protection")
    from .csrf_protection import csrf_protection, csrf_protect

__all__ = ["csrf_protection", "csrf_protect"]
