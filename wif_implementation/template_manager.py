"""
Template manager for the WIF implementation.

This module provides functionality to manage templates for the WIF implementation.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape, Template

from .error_handler import WIFError, ErrorSeverity, handle_exception

# Configure logging
logger = logging.getLogger("wif_implementation.template_manager")


class TemplateError(WIFError):
    """Exception raised when there is a template error."""
    
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


class TemplateManager:
    """
    Manager for templates.
    
    This class provides functionality to manage templates for the WIF implementation.
    """
    
    def __init__(
        self,
        template_dir: Optional[Union[str, Path]] = None,
        verbose: bool = False,
    ):
        """
        Initialize the template manager.
        
        Args:
            template_dir: The directory containing templates
            verbose: Whether to show detailed output during processing
        """
        # If template_dir is not provided, use the default templates directory
        if template_dir is None:
            # Get the directory of this file
            current_dir = Path(__file__).parent
            template_dir = current_dir / "templates"
        
        self.template_dir = Path(template_dir).resolve()
        self.verbose = verbose
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.debug(f"Initialized template manager with template directory: {self.template_dir}")
        
        # Initialize Jinja2 environment
        self._init_environment()
    
    def _init_environment(self) -> None:
        """
        Initialize the Jinja2 environment.
        
        Raises:
            TemplateError: If the template directory does not exist
        """
        try:
            # Check if the template directory exists
            if not self.template_dir.exists():
                raise TemplateError(
                    f"Template directory does not exist: {self.template_dir}",
                    details={"template_dir": str(self.template_dir)},
                )
            
            # Create the Jinja2 environment
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(["html", "xml"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            
            logger.debug("Jinja2 environment initialized successfully")
            
        except TemplateError:
            # Re-raise template errors
            raise
        except Exception as e:
            logger.error(f"Error initializing Jinja2 environment: {str(e)}")
            raise TemplateError(
                f"Failed to initialize Jinja2 environment",
                cause=e,
            )
    
    @handle_exception
    def get_template(self, template_name: str) -> Template:
        """
        Get a template by name.
        
        Args:
            template_name: The name of the template to get
            
        Returns:
            The template
            
        Raises:
            TemplateError: If the template does not exist
        """
        try:
            # Get the template
            template = self.env.get_template(template_name)
            
            logger.debug(f"Template {template_name} retrieved successfully")
            return template
            
        except Exception as e:
            logger.error(f"Error getting template {template_name}: {str(e)}")
            raise TemplateError(
                f"Failed to get template {template_name}",
                details={"template_name": template_name},
                cause=e,
            )
    
    @handle_exception
    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: The name of the template to render
            context: The context to render the template with
            
        Returns:
            The rendered template
            
        Raises:
            TemplateError: If the template does not exist or cannot be rendered
        """
        try:
            # Get the template
            template = self.get_template(template_name)
            
            # Render the template
            rendered = template.render(**context)
            
            logger.debug(f"Template {template_name} rendered successfully")
            return rendered
            
        except TemplateError:
            # Re-raise template errors
            raise
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}")
            raise TemplateError(
                f"Failed to render template {template_name}",
                details={"template_name": template_name, "context": context},
                cause=e,
            )
    
    @handle_exception
    def list_templates(self) -> List[str]:
        """
        List all available templates.
        
        Returns:
            A list of template names
            
        Raises:
            TemplateError: If the templates cannot be listed
        """
        try:
            # List all templates
            templates = self.env.list_templates()
            
            logger.debug(f"Listed {len(templates)} templates")
            return templates
            
        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            raise TemplateError(
                f"Failed to list templates",
                cause=e,
            )


# Create a global template manager
template_manager = TemplateManager()