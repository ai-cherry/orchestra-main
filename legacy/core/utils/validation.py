"""
Enhanced validation utilities for AI Cherry
Focused on data integrity and error prevention
"""

import re
import yaml
import json
from typing import Any, Dict, List, Optional, Union, Callable, Type
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ValidationError
import logging

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a validation operation"""
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        """Add an error to the result"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning to the result"""
        self.warnings.append(warning)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }


class EnhancedValidator:
    """Enhanced validation utilities for MCP configurations"""
    
    # Resource validation patterns
    CPU_PATTERN = re.compile(r'^(\d+(\.\d+)?)(m)?$')
    MEMORY_PATTERN = re.compile(r'^(\d+(\.\d+)?)(Ki|Mi|Gi|Ti|K|M|G|T)?$')
    
    # Name validation
    NAME_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\-_\.]*[a-zA-Z0-9]$')
    
    # Docker image validation
    DOCKER_IMAGE_PATTERN = re.compile(r'^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*(?::[a-zA-Z0-9][a-zA-Z0-9._-]*)?$')
    
    @staticmethod
    def validate_server_name(name: str) -> ValidationResult:
        """Validate MCP server name"""
        result = ValidationResult()
        
        if not name:
            result.add_error("Server name cannot be empty")
            return result
        
        if len(name) < 3:
            result.add_error("Server name must be at least 3 characters long")
        
        if len(name) > 100:
            result.add_error("Server name cannot exceed 100 characters")
        
        if not EnhancedValidator.NAME_PATTERN.match(name):
            result.add_error(
                "Server name must start and end with alphanumeric characters and can contain hyphens,
                underscores,
                and dots"
            )
        
        # Check for reserved names
        if name.lower() in reserved_names:
            result.add_warning(f"'{name}' is a reserved name and may cause conflicts")
        
        return result
    
    @staticmethod
    def validate_cpu_resource(cpu: str) -> ValidationResult:
        """Validate CPU resource specification"""
        result = ValidationResult()
        
        if not cpu:
            result.add_error("CPU specification cannot be empty")
            return result
        
        match = EnhancedValidator.CPU_PATTERN.match(cpu)
        if not match:
            result.add_error(f"Invalid CPU format: {cpu}. Expected format: '1', '1.5', '500m'")
            return result
        
        try:
            value = float(match.group(1))
            unit = match.group(3)
            
            # Convert to cores
            if unit == 'm':
                cores = value / 1000
            else:
                cores = value
            
            if cores <= 0:
                result.add_error("CPU allocation must be greater than 0")
            elif cores > 32:
                result.add_warning(f"CPU allocation of {cores} cores is very high")
            elif cores < 0.1:
                result.add_warning(f"CPU allocation of {cores} cores is very low")
                
        except ValueError:
            result.add_error(f"Invalid CPU value: {cpu}")
        
        return result
    
    @staticmethod
    def validate_memory_resource(memory: str) -> ValidationResult:
        """Validate memory resource specification"""
        result = ValidationResult()
        
        if not memory:
            result.add_error("Memory specification cannot be empty")
            return result
        
        match = EnhancedValidator.MEMORY_PATTERN.match(memory)
        if not match:
            result.add_error(f"Invalid memory format: {memory}. Expected format: '1Gi', '512Mi', '2G'")
            return result
        
        try:
            value = float(match.group(1))
            unit = match.group(3) or ""
            
            # Convert to bytes for validation
            multipliers = {
                'Ki': 1024, 'Mi': 1024**2, 'Gi': 1024**3, 'Ti': 1024**4,
                'K': 1000, 'M': 1000**2, 'G': 1000**3, 'T': 1000**4,
                '': 1
            }
            
            bytes_value = value * multipliers.get(unit, 1)
            
            if bytes_value <= 0:
                result.add_error("Memory allocation must be greater than 0")
            elif bytes_value < 128 * 1024 * 1024:  # 128MB
                result.add_warning("Memory allocation is very low (< 128MB)")
            elif bytes_value > 64 * 1024**3:  # 64GB
                result.add_warning("Memory allocation is very high (> 64GB)")
                
        except ValueError:
            result.add_error(f"Invalid memory value: {memory}")
        
        return result
    
    @staticmethod
    def validate_docker_image(image: str) -> ValidationResult:
        """Validate Docker image name"""
        result = ValidationResult()
        
        if not image:
            result.add_error("Docker image cannot be empty")
            return result
        
        if not EnhancedValidator.DOCKER_IMAGE_PATTERN.match(image.lower()):
            result.add_error(f"Invalid Docker image format: {image}")
        
        # Check for common issues
        if ':' not in image:
            result.add_warning("Docker image has no tag specified, 'latest' will be used")
        
        if image.startswith('http://') or image.startswith('https://'):
            result.add_error("Docker image should not include protocol (http/https)")
        
        return result
    
    @staticmethod
    def validate_environment_variables(env_vars: Dict[str, str]) -> ValidationResult:
        """Validate environment variables"""
        result = ValidationResult()
        
        if not isinstance(env_vars, dict):
            result.add_error("Environment variables must be a dictionary")
            return result
        
        # Pattern for valid environment variable names
        env_name_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        
        for key, value in env_vars.items():
            if not env_name_pattern.match(key):
                result.add_error(f"Invalid environment variable name: {key}")
            
            if not isinstance(value, str):
                result.add_error(f"Environment variable value must be string: {key}={value}")
            
            # Check for sensitive data patterns
            sensitive_patterns = [
                r'password', r'secret', r'key', r'token', r'credential'
            ]
            
            for pattern in sensitive_patterns:
                if re.search(pattern, key.lower()) and value:
                    result.add_warning(f"Environment variable '{key}' appears to contain sensitive data")
                    break
        
        return result
    
    @staticmethod
    def validate_yaml_content(yaml_content: str) -> ValidationResult:
        """Validate YAML content"""
        result = ValidationResult()
        
        if not yaml_content:
            result.add_error("YAML content cannot be empty")
            return result
        
        try:
            yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            result.add_error(f"Invalid YAML syntax: {e}")
        
        return result
    
    @staticmethod
    def validate_json_content(json_content: str) -> ValidationResult:
        """Validate JSON content"""
        result = ValidationResult()
        
        if not json_content:
            result.add_error("JSON content cannot be empty")
            return result
        
        try:
            json.loads(json_content)
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON syntax: {e}")
        
        return result
    
    @staticmethod
    def validate_ai_provider_config(provider_config: Dict[str, Any]) -> ValidationResult:
        """Validate AI provider configuration"""
        result = ValidationResult()
        
        required_fields = ['name']
        for field in required_fields:
            if field not in provider_config:
                result.add_error(f"Missing required field: {field}")
        
        if 'name' in provider_config:
            valid_providers = ['openai', 'claude', 'gemini', 'copilot', 'custom']
            if provider_config['name'] not in valid_providers:
                result.add_error(f"Invalid AI provider: {provider_config['name']}. Valid options: {valid_providers}")
        
        # Validate API key reference
        if 'api_key_secret_name' in provider_config:
            key_name = provider_config['api_key_secret_name']
            if not key_name or not isinstance(key_name, str):
                result.add_error("API key secret name must be a non-empty string")
        
        return result
    
    @staticmethod
    def validate_context_source(context_source: Dict[str, Any]) -> ValidationResult:
        """Validate context source configuration"""
        result = ValidationResult()
        
        if 'type' not in context_source:
            result.add_error("Context source must have a 'type' field")
            return result
        
        source_type = context_source['type']
        valid_types = ['git_repo', 'weaviate_collection', 'file_path', 'url_list']
        
        if source_type not in valid_types:
            result.add_error(f"Invalid context source type: {source_type}. Valid options: {valid_types}")
            return result
        
        # Type-specific validation
        if source_type == 'git_repo':
            if 'uri' not in context_source:
                result.add_error("Git repository context source must have 'uri' field")
            else:
                uri = context_source['uri']
                if not uri.startswith(('http://', 'https://', 'git://', 'ssh://')):
                    result.add_warning("Git URI should start with a valid protocol")
        
        elif source_type == 'file_path':
            if 'paths' not in context_source or not context_source['paths']:
                result.add_error("File path context source must have non-empty 'paths' field")
        
        elif source_type == 'url_list':
            if 'paths' not in context_source or not context_source['paths']:
                result.add_error("URL list context source must have non-empty 'paths' field")
            else:
                for url in context_source['paths']:
                    if not url.startswith(('http://', 'https://')):
                        result.add_warning(f"URL should start with http:// or https://: {url}")
        
        return result
    
    @staticmethod
    def validate_pydantic_model(model_class: Type[BaseModel], data: Dict[str, Any]) -> ValidationResult:
        """Validate data against a Pydantic model"""
        result = ValidationResult()
        
        try:
            model_class(**data)
        except ValidationError as e:
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                message = error['msg']
                result.add_error(f"Field '{field}': {message}")
        except Exception as e:
            result.add_error(f"Validation error: {e}")
        
        return result


class ConfigurationValidator:
    """Comprehensive configuration validator for MCP servers"""
    
    def __init__(self):
        self.validator = EnhancedValidator()
    
    def validate_complete_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Validate a complete MCP server configuration"""
        result = ValidationResult()
        
        # Validate basic fields
        if 'name' in config_data:
            name_result = self.validator.validate_server_name(config_data['name'])
            result.merge(name_result)
        
        # Validate resources
        if 'resources' in config_data:
            resources = config_data['resources']
            if isinstance(resources, dict):
                if 'cpu' in resources:
                    cpu_result = self.validator.validate_cpu_resource(resources['cpu'])
                    result.merge(cpu_result)
                
                if 'memory' in resources:
                    memory_result = self.validator.validate_memory_resource(resources['memory'])
                    result.merge(memory_result)
        
        # Validate Docker image
        if 'base_docker_image' in config_data:
            image_result = self.validator.validate_docker_image(config_data['base_docker_image'])
            result.merge(image_result)
        
        # Validate environment variables
        if 'custom_environment_variables' in config_data:
            env_result = self.validator.validate_environment_variables(config_data['custom_environment_variables'])
            result.merge(env_result)
        
        # Validate AI providers
        if 'ai_providers' in config_data:
            for i, provider in enumerate(config_data['ai_providers']):
                provider_result = self.validator.validate_ai_provider_config(provider)
                if not provider_result.is_valid:
                    for error in provider_result.errors:
                        result.add_error(f"AI Provider {i}: {error}")
                for warning in provider_result.warnings:
                    result.add_warning(f"AI Provider {i}: {warning}")
        
        # Validate context sources
        if 'context_sources' in config_data:
            for i, source in enumerate(config_data['context_sources']):
                source_result = self.validator.validate_context_source(source)
                if not source_result.is_valid:
                    for error in source_result.errors:
                        result.add_error(f"Context Source {i}: {error}")
                for warning in source_result.warnings:
                    result.add_warning(f"Context Source {i}: {warning}")
        
        # Validate generated YAML if present
        if 'generated_mcp_internal_config_yaml' in config_data:
            yaml_content = config_data['generated_mcp_internal_config_yaml']
            if yaml_content:
                yaml_result = self.validator.validate_yaml_content(yaml_content)
                result.merge(yaml_result)
        
        return result
    
    def validate_config_consistency(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Validate internal consistency of configuration"""
        result = ValidationResult()
        
        # Check consistency between enabled tools and overrides
        enabled_tools = config_data.get('enabled_internal_tools', [])
        
        if 'copilot' in enabled_tools and 'copilot_config_override' not in config_data:
            result.add_warning("Copilot is enabled but no configuration override provided")
        
        if 'gemini' in enabled_tools and 'gemini_config_override' not in config_data:
            result.add_warning("Gemini is enabled but no configuration override provided")
        
        # Check if overrides are provided for disabled tools
        if 'copilot' not in enabled_tools and config_data.get('copilot_config_override'):
            result.add_warning("Copilot configuration override provided but Copilot is not enabled")
        
        if 'gemini' not in enabled_tools and config_data.get('gemini_config_override'):
            result.add_warning("Gemini configuration override provided but Gemini is not enabled")
        
        # Validate target AI coders consistency
        target_coders = config_data.get('target_ai_coders', [])
        if 'Copilot' in target_coders and 'copilot' not in enabled_tools:
            result.add_warning("Copilot is listed as target AI coder but not enabled in internal tools")
        
        if 'Gemini' in target_coders and 'gemini' not in enabled_tools:
            result.add_warning("Gemini is listed as target AI coder but not enabled in internal tools")
        
        return result


# Global validator instance
config_validator = ConfigurationValidator()

