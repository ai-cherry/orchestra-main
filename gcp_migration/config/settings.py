"""
Configuration settings for the GCP Migration toolkit.

This module uses Pydantic to load and validate configuration from
environment variables, dotenv files, and defaults.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, SecretStr, field_validator


class LogLevel(str, Enum):
    """Valid log levels."""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TerraformBackend(str, Enum):
    """Valid Terraform backends."""
    
    LOCAL = "local"
    GCS = "gcs"


class Settings(BaseModel):
    """
    Configuration settings for the migration toolkit.
    
    This class defines all configurable parameters for the application
    and handles loading them from environment variables, .env files,
    and default values.
    """
    
    # Project info
    app_name: str = "gcp-migration"
    app_version: str = "0.1.0"
    env: str = Field(default="development", description="Environment name (development, staging, production)")
    
    # Logging
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "%(levelname)s | %(asctime)s | %(name)s | %(message)s"
    log_file: Optional[Path] = None
    
    # GitHub settings
    github_token: Optional[SecretStr] = None
    github_organization: Optional[str] = None
    github_repositories: List[str] = Field(default_factory=list)
    
    # GCP settings
    gcp_project_id: str = Field(..., description="GCP Project ID for the Workstations")
    gcp_region: str = "us-central1"
    gcp_zone: str = "us-central1-a"
    gcp_credentials_file: Optional[Path] = None
    
    # Terraform settings
    terraform_path: Path = Path("terraform")
    terraform_backend: TerraformBackend = TerraformBackend.LOCAL
    terraform_state_bucket: Optional[str] = None
    terraform_state_prefix: str = "workstations/terraform/state"
    
    # Docker settings
    docker_registry: Optional[str] = Field(
        default=None,
        description="Docker registry for Workstation images (e.g., gcr.io/project-id or region-docker.pkg.dev/project-id/repo)"
    )
    docker_image_tag: str = "latest"
    docker_build_args: Dict[str, str] = Field(default_factory=dict)
    
    # Workstation settings
    workstation_idle_timeout_minutes: int = Field(default=20, ge=1, le=1440)
    workstation_machine_types: Dict[str, str] = Field(
        default_factory=lambda: {
            "standard": "e2-standard-8",
            "ml": "n1-standard-16",
        }
    )
    workstation_use_gpu: bool = True
    workstation_gpu_type: str = "nvidia-tesla-t4"
    workstation_gpu_count: int = 1
    workstation_boot_disk_size_gb: int = 100
    workstation_persistent_disk_size_gb: int = 200
    workstation_disable_public_ip: bool = False
    
    # Network settings
    network_cidr_range: str = "10.2.0.0/16"
    network_enable_private_google_access: bool = True
    network_enable_cloud_nat: bool = True
    
    # Performance settings
    performance_optimized: bool = True
    benchmark_iterations: int = 3
    enable_parallel_execution: bool = True
    max_concurrent_operations: int = 5
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    cache_dir: Path = Path(".cache")
    
    # Security settings
    disable_ssl_verification: bool = False
    enforce_https: bool = True
    sensitive_env_vars: List[str] = Field(
        default_factory=lambda: [
            "GITHUB_TOKEN",
            "GCP_CREDENTIALS",
            "API_KEY",
            "PASSWORD",
            "SECRET",
        ]
    )
    
    @field_validator("terraform_path", "cache_dir", mode="after")
    @classmethod
    def ensure_directory_exists(cls, v: Path) -> Path:
        """Validate that the directory exists, creating it if necessary."""
        if not v.exists():
            v.mkdir(parents=True, exist_ok=True)
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if the environment is development."""
        return self.env.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if the environment is production."""
        return self.env.lower() == "production"
    
    @property
    def is_staging(self) -> bool:
        """Check if the environment is staging."""
        return self.env.lower() == "staging"
    
    @property
    def terraform_var_map(self) -> Dict[str, Union[str, bool, int]]:
        """Generate a map of Terraform variables based on settings."""
        var_map: Dict[str, Union[str, bool, int]] = {
            "project_id": self.gcp_project_id,
            "region": self.gcp_region,
            "zone": self.gcp_zone,
            "project_prefix": self.app_name,
            "enable_gpu": self.workstation_use_gpu,
            "gpu_type": self.workstation_gpu_type,
            "gpu_count": self.workstation_gpu_count,
            "boot_disk_size_gb": self.workstation_boot_disk_size_gb,
            "persistent_disk_size_gb": self.workstation_persistent_disk_size_gb,
            "disable_public_ip": self.workstation_disable_public_ip,
            "auto_shutdown_minutes": self.workstation_idle_timeout_minutes,
            "enable_monitoring": not self.is_development,
            "performance_optimized": self.performance_optimized,
            "ip_cidr_range": self.network_cidr_range,
        }
        
        # Add container image if Docker registry is available
        if self.docker_registry:
            container_image = f"{self.docker_registry}/{self.app_name}:{self.docker_image_tag}"
            var_map["container_image"] = container_image
        # Add machine types if available
        if "standard" in self.workstation_machine_types:
            var_map["standard_machine_type"] = self.workstation_machine_types["standard"]
        if "ml" in self.workstation_machine_types:
            var_map["ml_machine_type"] = self.workstation_machine_types["ml"]
            
        return var_map


# Load settings from environment
def load_settings() -> Settings:
    """
    Load settings from environment variables and .env file.
    
    Returns:
        Configured Settings instance
    """
    # Try to load environment variables from .env file
    env_file = Path('.env')
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Override with actual environment variables
    for key, value in os.environ.items():
        env_vars[key] = value
    
    # Filter to only include settings fields
    # and handle type conversions as appropriate
    settings_fields = {}
    for field_name in Settings.model_fields:
        env_key = field_name.upper()
        if env_key in env_vars:
            value = env_vars[env_key]
            field_info = Settings.model_fields[field_name]
            
            # Perform type conversion based on the field type
            if field_info.annotation == bool:
                settings_fields[field_name] = value.lower() in ('true', 't', 'yes', 'y', '1')
            elif field_info.annotation == int:
                settings_fields[field_name] = int(value)
            elif field_info.annotation == Path or "Path" in str(field_info.annotation):
                settings_fields[field_name] = Path(value)
            elif 'LogLevel' in str(field_info.annotation):
                settings_fields[field_name] = LogLevel(value)
            elif 'TerraformBackend' in str(field_info.annotation):
                settings_fields[field_name] = TerraformBackend(value)
            elif 'List[str]' in str(field_info.annotation):
                # Handle list of strings - expect comma-separated values
                settings_fields[field_name] = [s.strip() for s in value.split(',')]
            elif 'Dict[str, str]' in str(field_info.annotation):
                # Handle dict - expect JSON or key=value pairs
                if value.startswith('{'):
                    import json
                    settings_fields[field_name] = json.loads(value)
                else:
                    # Simple key=value format for dictionaries
                    settings_fields[field_name] = {}
                    for pair in value.split(','):
                        if '=' in pair:
                            k, v = pair.split('=', 1)
                            settings_fields[field_name][k.strip()] = v.strip()
            elif 'SecretStr' in str(field_info.annotation):
                from pydantic import SecretStr
                settings_fields[field_name] = SecretStr(value)
            else:
                # Default to string for other types
                settings_fields[field_name] = value
    
    # Special handling for docker_registry
    # If docker_registry is not provided but gcp_project_id is available, derive the registry from it
    if 'docker_registry' not in settings_fields and 'gcp_project_id' in settings_fields:
        # Use Artifact Registry format (preferred for new projects)
        project_id = settings_fields['gcp_project_id']
        region = settings_fields.get('gcp_region', 'us-central1')
        settings_fields['docker_registry'] = f"{region}-docker.pkg.dev/{project_id}/workstations"
        print(f"Auto-configured Docker registry: {settings_fields['docker_registry']}")
        
    try:
        return Settings(**settings_fields)
    except Exception as e:
        # Provide helpful error messages for common configuration issues
        if "docker_registry" in str(e):
            print("\n=== CONFIGURATION ERROR ===")
            print("Missing required configuration: docker_registry")
            print("\nPlease set this value using one of these methods:")
            print("1. Add to .env file: DOCKER_REGISTRY=gcr.io/your-project-id")
            print("2. Set environment variable: export DOCKER_REGISTRY=gcr.io/your-project-id")
            print("\nExample Docker registry formats:")
            print("- Google Container Registry: gcr.io/your-project-id")
            print("- Artifact Registry: region-docker.pkg.dev/your-project-id/repository-name")
            print("===========================\n")
        raise


# Create a global settings instance
settings = load_settings()