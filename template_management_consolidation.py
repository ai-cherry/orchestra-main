"""
Consolidated template management framework for the entire codebase.

This implementation provides a unified approach to template management across all modules,
combining the functionality from:
- wif_implementation/template_manager.py
- wif_implementation/enhanced_template_manager.py

Usage:
    1. Import the TemplateManager or EnhancedTemplateManager class from this module
    2. Create an instance with the appropriate configuration
    3. Use the instance to render and manage templates
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Third-party imports
import yaml
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape

# Import error handling from consolidated framework
from error_handling_consolidation import (
    BaseError, 
    ErrorSeverity, 
    handle_exception
)

# Configure logging
logger = logging.getLogger(__name__)


class TemplateError(BaseError):
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


class BaseTemplateManager:
    """
    Base class for template managers.
    
    This class provides common functionality for template management that is shared
    between the regular and enhanced template managers.
    """
    
    def __init__(
        self,
        template_dir: Optional[Union[str, Path]] = None,
        verbose: bool = False,
    ):
        """
        Initialize the base template manager.
        
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
    
    @handle_exception(target_error=TemplateError)
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
    
    @handle_exception(target_error=TemplateError)
    def render_template(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
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
        if context is None:
            context = {}
        
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
    
    @handle_exception(target_error=TemplateError)
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


class TemplateManager(BaseTemplateManager):
    """
    Basic template manager (legacy version).
    
    This class is maintained for backward compatibility with existing code that
    uses the original template manager.
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
        logger.warning(
            "TemplateManager is deprecated. Use EnhancedTemplateManager instead."
        )
        super().__init__(template_dir, verbose)


class EnhancedTemplateManager(BaseTemplateManager):
    """
    Enhanced manager for templates.
    
    This class provides a more robust approach to template management,
    with support for output directories, writing templates to files,
    and creating default templates.
    """
    
    def __init__(
        self,
        template_dir: Optional[Union[str, Path]] = None,
        output_dir: Optional[Union[str, Path]] = None,
        verbose: bool = False,
        debug: bool = False,
        config: Optional[Any] = None,
    ):
        """
        Initialize the enhanced template manager.
        
        Args:
            template_dir: The directory containing templates
            output_dir: The directory to write output files to
            verbose: Whether to show detailed output during processing
            debug: Whether to enable debug logging
            config: Optional configuration object to include in template context
        """
        self.config = config
        
        # Configure logging
        if debug:
            logger.setLevel(logging.DEBUG)
        
        # Initialize template directory
        if template_dir is None:
            # Get the directory of this file
            current_dir = Path(__file__).parent
            template_dir = current_dir / "templates"
        
        # Initialize output directory
        if output_dir is None:
            # Get the current working directory
            base_dir = Path.cwd()
            self.output_dir = base_dir / "template_output"
        else:
            self.output_dir = Path(output_dir)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized output directory: {self.output_dir}")
        
        # Initialize base template manager
        super().__init__(template_dir, verbose)
        
        # Add custom filters
        self._add_custom_filters()
    
    def _add_custom_filters(self) -> None:
        """Add custom filters to the Jinja2 environment."""
        try:
            # Add YAML dump filter
            self.env.filters["yaml_dump"] = lambda x: yaml.dump(
                x, default_flow_style=False, sort_keys=False
            )
            
            logger.debug("Added custom filters to Jinja2 environment")
            
        except Exception as e:
            logger.error(f"Error adding custom filters: {str(e)}")
            raise TemplateError(
                "Failed to add custom filters to Jinja2 environment",
                cause=e,
            )
    
    @handle_exception(target_error=TemplateError)
    def render_template(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render a template with the given context.
        
        This override adds the config object to the context if available.
        
        Args:
            template_name: The name of the template to render
            context: Additional context to render the template with
            
        Returns:
            The rendered template
            
        Raises:
            TemplateError: If the template does not exist or cannot be rendered
        """
        if context is None:
            context = {}
        
        # Add config to context if available
        full_context = {}
        if self.config is not None:
            full_context["config"] = self.config
        
        # Merge with provided context
        full_context.update(context)
        
        # Use base implementation
        return super().render_template(template_name, full_context)
    
    @handle_exception(target_error=TemplateError)
    def write_template_to_file(
        self,
        template_name: str,
        output_path: Union[str, Path],
        context: Optional[Dict[str, Any]] = None,
        overwrite: bool = False,
    ) -> Path:
        """
        Render a template and write it to a file.
        
        Args:
            template_name: The name of the template to render
            output_path: The path to write the rendered template to (relative to output_dir)
            context: Additional context to render the template with
            overwrite: Whether to overwrite the file if it already exists
            
        Returns:
            The path to the written file
            
        Raises:
            TemplateError: If the template cannot be rendered or written
        """
        if context is None:
            context = {}
        
        # Resolve the output path
        if isinstance(output_path, str):
            output_path = Path(output_path)
        
        # Make the path relative to the output directory
        if output_path.is_absolute():
            full_path = output_path
        else:
            full_path = self.output_dir / output_path
        
        # Create parent directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if the file already exists
        if full_path.exists() and not overwrite:
            logger.warning(f"File {full_path} already exists, not overwriting")
            return full_path
        
        try:
            # Render the template
            rendered = self.render_template(template_name, context)
            
            # Write the rendered template to the file
            with open(full_path, "w") as f:
                f.write(rendered)
            
            logger.info(f"Wrote rendered template {template_name} to {full_path}")
            return full_path
            
        except Exception as e:
            logger.error(f"Error writing template {template_name} to {full_path}: {str(e)}")
            raise TemplateError(
                f"Failed to write template {template_name} to {full_path}",
                details={
                    "template_name": template_name,
                    "output_path": str(output_path),
                    "context": context,
                },
                cause=e,
            )
    
    @handle_exception(target_error=TemplateError)
    def create_default_templates(self) -> List[Path]:
        """
        Create default templates if they don't exist.
        
        This method creates basic templates that might be useful,
        such as README templates, configuration files, etc.
        
        Returns:
            A list of paths to the created template files
            
        Raises:
            TemplateError: If the templates cannot be created
        """
        created_templates = []
        
        # Example template - README.md
        readme_template = """# {{ project_name | default('My Project') }}

{{ description | default('A project created with the template manager.') }}

## Installation

```bash
{{ install_command | default('pip install .') }}
```

## Usage

```python
{{ usage_example | default('import myproject\\n\\nresult = myproject.run()') }}
```

## Configuration

{{ config_description | default('This project uses a YAML configuration file.') }}

```yaml
{{ config_example | default('key: value') }}
```

## License

{{ license | default('MIT') }}
"""
        
        try:
            readme_path = self.template_dir / "README.md.j2"
            with open(readme_path, "w") as f:
                f.write(readme_template)
            
            created_templates.append(readme_path)
            logger.info(f"Created README template: {readme_path}")
            
        except Exception as e:
            logger.error(f"Error creating README template: {str(e)}")
            raise TemplateError(
                "Failed to create README template",
                cause=e,
            )
        
        # Additional templates can be added here
        
        return created_templates


# Compatibility adapter function to create an appropriate template manager
def create_template_manager(
    template_dir: Optional[Union[str, Path]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    verbose: bool = False,
    enhanced: bool = True,
    config: Optional[Any] = None,
) -> Union[TemplateManager, EnhancedTemplateManager]:
    """
    Create a template manager with the given configuration.
    
    Args:
        template_dir: The directory containing templates
        output_dir: The directory to write output files to (enhanced only)
        verbose: Whether to show detailed output during processing
        enhanced: Whether to create an enhanced template manager
        config: Optional configuration object (enhanced only)
        
    Returns:
        The initialized template manager
    """
    if enhanced:
        return EnhancedTemplateManager(
            template_dir=template_dir,
            output_dir=output_dir,
            verbose=verbose,
            debug=verbose,
            config=config,
        )
    else:
        return TemplateManager(
            template_dir=template_dir,
            verbose=verbose,
        )


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create an enhanced template manager
    manager = create_template_manager(enhanced=True, verbose=True)
    
    # Create default templates
    created_templates = manager.create_default_templates()
    print(f"Created {len(created_templates)} templates")
    
    # Render and write a template
    context = {
        "project_name": "Template Manager",
        "description": "A unified template management system for the codebase.",
    }
    
    output_path = manager.write_template_to_file(
        "README.md.j2",
        "output/README.md",
        context=context,
        overwrite=True,
    )
    
    print(f"Wrote template to {output_path}")
