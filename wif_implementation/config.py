"""
WIF Configuration for AI Orchestra.

This module provides configuration for the WIF implementation.
It defines the configuration options for Workload Identity Federation.
"""

import os
import re
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field, validator, root_validator


class WIFConfig(BaseModel):
    """
    Configuration for the WIF implementation.
    
    This class provides configuration options for the WIF implementation,
    including project ID, region, workload identity pool, and service account.
    """
    
    project_id: Optional[str] = Field(None, description="GCP project ID")
    region: str = Field("us-west4", description="GCP region")
    workload_identity_pool: Optional[str] = Field(None, description="Workload Identity Pool ID")
    workload_identity_provider: Optional[str] = Field(None, description="Workload Identity Provider ID")
    service_account: Optional[str] = Field(None, description="Service account email")
    github_org: Optional[str] = Field(None, description="GitHub organization")
    github_repo: Optional[str] = Field(None, description="GitHub repository")
    
    @validator("project_id")
    def validate_project_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate project ID format."""
        if v is not None:
            if not v.startswith("cherry-"):
                raise ValueError("Project ID must start with 'cherry-'")
            if not re.match(r"^[a-z][-a-z0-9]{4,28}[a-z0-9]$", v):
                raise ValueError("Project ID must match GCP naming requirements")
        return v
    
    @validator("region")
    def validate_region(cls, v: str) -> str:
        """Validate GCP region."""
        valid_regions = {"us-west1", "us-west2", "us-west3", "us-west4", "us-central1"}
        if v not in valid_regions:
            raise ValueError(f"Region must be one of: {', '.join(valid_regions)}")
        return v
    
    @validator("service_account")
    def validate_service_account(cls, v: Optional[str]) -> Optional[str]:
        """Validate service account email format."""
        if v is not None:
            if not re.match(r"^[a-zA-Z0-9-]+@[a-zA-Z0-9-]+\.iam\.gserviceaccount\.com$", v):
                raise ValueError("Invalid service account email format")
        return v
    
    @root_validator
    def validate_wif_configuration(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate WIF configuration consistency."""
        # If workload_identity_provider is set, project_id must be set
        if values.get("workload_identity_provider") and not values.get("project_id"):
            raise ValueError("Project ID must be set when workload_identity_provider is set")
        
        # If service_account is set, project_id must be set
        if values.get("service_account") and not values.get("project_id"):
            raise ValueError("Project ID must be set when service_account is set")
        
        # If github_repo is set, github_org must be set
        if values.get("github_repo") and not values.get("github_org"):
            raise ValueError("GitHub organization must be set when github_repo is set")
        
        return values
    
    @classmethod
    def from_env(cls) -> "WIFConfig":
        """
        Create a configuration from environment variables.
        
        Returns:
            A WIF configuration
        """
        return cls(
            project_id=os.environ.get("GCP_PROJECT_ID"),
            region=os.environ.get("GCP_REGION", "us-west4"),
            workload_identity_pool=os.environ.get("WIF_POOL_ID"),
            workload_identity_provider=os.environ.get("WIF_PROVIDER_ID"),
            service_account=os.environ.get("WIF_SERVICE_ACCOUNT"),
            github_org=os.environ.get("GITHUB_ORG"),
            github_repo=os.environ.get("GITHUB_REPO"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.
        
        Returns:
            A dictionary representation of the configuration
        """
        return self.dict(exclude_none=True)
    
    def get_workload_identity_provider_resource_name(self) -> Optional[str]:
        """
        Get the full resource name of the workload identity provider.
        
        Returns:
            The full resource name, or None if not configured
        """
        if not self.project_id or not self.workload_identity_pool or not self.workload_identity_provider:
            return None
        
        return (
            f"projects/{self.project_id}/locations/global/workloadIdentityPools/"
            f"{self.workload_identity_pool}/providers/{self.workload_identity_provider}"
        )
    
    def get_service_account_resource_name(self) -> Optional[str]:
        """
        Get the full resource name of the service account.
        
        Returns:
            The full resource name, or None if not configured
        """
        if not self.project_id or not self.service_account:
            return None
        
        return f"projects/{self.project_id}/serviceAccounts/{self.service_account}"
    
    def get_github_repository(self) -> Optional[str]:
        """
        Get the full GitHub repository name.
        
        Returns:
            The full repository name, or None if not configured
        """
        if not self.github_org or not self.github_repo:
            return None
        
        return f"{self.github_org}/{self.github_repo}"


def get_config() -> WIFConfig:
    """
    Get the WIF configuration.
    
    This function is used for dependency injection.
    
    Returns:
        The WIF configuration
    """
    return WIFConfig.from_env()
