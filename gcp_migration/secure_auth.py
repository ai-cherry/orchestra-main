#!/usr/bin/env python3
"""
Secure GCP Authentication Module for AI Orchestra

This module provides secure authentication methods for GCP services,
properly handling service account credentials and workload identity federation.
Implements best practices for credential management and cleanup.
"""

import base64
import json
import logging
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import uuid
import atexit
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("secure-auth")

# Add parent directory to the Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


class AuthMethod(Enum):
    """Authentication methods supported by the module."""
    SERVICE_ACCOUNT_KEY = "service_account_key"
    SERVICE_ACCOUNT_IMPERSONATION = "service_account_impersonation"
    WORKLOAD_IDENTITY = "workload_identity"
    APPLICATION_DEFAULT = "application_default"


@dataclass
class GCPConfig:
    """Configuration for GCP authentication."""
    project_id: str
    region: str
    zone: Optional[str] = None


@dataclass
class GitHubConfig:
    """Configuration for GitHub authentication."""
    org_name: str
    repo_name: Optional[str] = None
    token: Optional[str] = None
    use_fine_grained_token: bool = False


class SecureCleanup:
    """Manages secure cleanup of temporary credential files."""
    
    def __init__(self):
        """Initialize secure cleanup."""
        self._temp_files: List[Path] = []
        self._temp_dirs: List[Path] = []
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def register_temp_file(self, file_path: Union[str, Path]) -> None:
        """Register a temporary file for cleanup.
        
        Args:
            file_path: Path to temporary file
        """
        path = Path(file_path)
        self._temp_files.append(path)
        logger.debug(f"Registered temporary file for cleanup: {path}")
    
    def register_temp_dir(self, dir_path: Union[str, Path]) -> None:
        """Register a temporary directory for cleanup.
        
        Args:
            dir_path: Path to temporary directory
        """
        path = Path(dir_path)
        self._temp_dirs.append(path)
        logger.debug(f"Registered temporary directory for cleanup: {path}")
    
    def cleanup(self) -> None:
        """Perform cleanup of all temporary files and directories."""
        # Clean up temporary files
        for file_path in self._temp_files:
            if file_path.exists():
                try:
                    # Securely delete by overwriting with zeros
                    with open(file_path, "wb") as f:
                        f.write(b'\x00' * file_path.stat().st_size)
                    file_path.unlink()
                    logger.debug(f"Securely deleted temporary file: {file_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up temporary file {file_path}: {e}")
        
        # Clean up temporary directories
        for dir_path in self._temp_dirs:
            if dir_path.exists():
                try:
                    for item in dir_path.glob('**/*'):
                        if item.is_file():
                            # Securely delete each file
                            with open(item, "wb") as f:
                                f.write(b'\x00' * item.stat().st_size)
                            item.unlink()
                    dir_path.rmdir()
                    logger.debug(f"Securely deleted temporary directory: {dir_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up temporary directory {dir_path}: {e}")
        
        # Clear the lists
        self._temp_files = []
        self._temp_dirs = []
    
    def _signal_handler(self, sig, frame) -> None:
        """Handle signals to ensure cleanup before exit.
        
        Args:
            sig: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {sig}, cleaning up...")
        self.cleanup()
        sys.exit(1)


# Create global cleanup instance
secure_cleanup = SecureCleanup()


class GCPAuth:
    """Securely manages GCP authentication."""
    
    def __init__(
        self, 
        gcp_config: GCPConfig,
        auth_method: AuthMethod = AuthMethod.SERVICE_ACCOUNT_KEY,
        service_account_key: Optional[str] = None,
        service_account_email: Optional[str] = None,
        workload_identity_provider: Optional[str] = None
    ):
        """Initialize GCP authentication.
        
        Args:
            gcp_config: GCP configuration
            auth_method: Authentication method to use
            service_account_key: Service account key JSON (if using key authentication)
            service_account_email: Service account email (if using impersonation)
            workload_identity_provider: Workload identity provider (if using WIF)
        """
        self.gcp_config = gcp_config
        self.auth_method = auth_method
        self.service_account_key = service_account_key
        self.service_account_email = service_account_email
        self.workload_identity_provider = workload_identity_provider
        self.authenticated = False
        self.temp_dir = None
        self._key_file_path = None
    
    def authenticate(self) -> bool:
        """Authenticate with GCP using the configured method.
        
        Returns:
            True if authentication successful, False otherwise
        """
        logger.info(f"Authenticating with GCP using {self.auth_method.value}")
        
        try:
            if self.auth_method == AuthMethod.SERVICE_ACCOUNT_KEY:
                return self._authenticate_with_key()
            elif self.auth_method == AuthMethod.SERVICE_ACCOUNT_IMPERSONATION:
                return self._authenticate_with_impersonation()
            elif self.auth_method == AuthMethod.WORKLOAD_IDENTITY:
                return self._authenticate_with_workload_identity()
            elif self.auth_method == AuthMethod.APPLICATION_DEFAULT:
                return self._authenticate_with_application_default()
            else:
                logger.error(f"Unsupported authentication method: {self.auth_method}")
                return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _create_secure_temp_dir(self) -> Path:
        """Create a secure temporary directory with restricted permissions.
        
        Returns:
            Path to the temporary directory
        """
        # Create a temporary directory with restrictive permissions (0700)
        temp_dir = tempfile.mkdtemp(prefix="gcp_auth_")
        temp_path = Path(temp_dir)
        
        # Set permissions to owner-only
        temp_path.chmod(0o700)
        
        # Register for cleanup
        secure_cleanup.register_temp_dir(temp_path)
        
        self.temp_dir = temp_path
        logger.debug(f"Created secure temporary directory: {temp_path}")
        return temp_path
    
    def _write_key_to_secure_file(self) -> Path:
        """Write the service account key to a secure temporary file.
        
        Returns:
            Path to the key file
        """
        if not self.service_account_key:
            raise ValueError("Service account key is required for key authentication")
        
        if not self.temp_dir:
            self._create_secure_temp_dir()
        
        # Create a unique filename
        key_file = self.temp_dir / f"sa_key_{uuid.uuid4().hex}.json"
        
        # Write the key to the file
        with open(key_file, "w") as f:
            f.write(self.service_account_key)
        
        # Set restrictive permissions
        key_file.chmod(0o600)
        
        # Register for cleanup
        secure_cleanup.register_temp_file(key_file)
        
        self._key_file_path = key_file
        logger.debug(f"Wrote service account key to secure file: {key_file}")
        return key_file
    
    def _authenticate_with_key(self) -> bool:
        """Authenticate with a service account key.
        
        Returns:
            True if authentication successful, False otherwise
        """
        key_file = self._write_key_to_secure_file()
        
        # Activate service account
        result = subprocess.run(
            ["gcloud", "auth", "activate-service-account", "--key-file", str(key_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to authenticate with service account key: {result.stderr}")
            return False
        
        # Set project
        result = subprocess.run(
            ["gcloud", "config", "set", "project", self.gcp_config.project_id],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to set project: {result.stderr}")
            return False
        
        # Set region
        result = subprocess.run(
            ["gcloud", "config", "set", "compute/region", self.gcp_config.region],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to set region: {result.stderr}")
            return False
        
        # Set zone if provided
        if self.gcp_config.zone:
            result = subprocess.run(
                ["gcloud", "config", "set", "compute/zone", self.gcp_config.zone],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to set zone: {result.stderr}")
                return False
        
        self.authenticated = True
        logger.info("Successfully authenticated with service account key")
        return True
    
    def _authenticate_with_impersonation(self) -> bool:
        """Authenticate by impersonating a service account.
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not self.service_account_email:
            raise ValueError("Service account email is required for impersonation")
        
        # First authenticate with the key
        if not self._authenticate_with_key():
            return False
        
        # Impersonate the service account
        result = subprocess.run(
            ["gcloud", "config", "set", "auth/impersonate_service_account", self.service_account_email],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to configure service account impersonation: {result.stderr}")
            return False
        
        logger.info(f"Successfully configured impersonation of {self.service_account_email}")
        return True
    
    def _authenticate_with_workload_identity(self) -> bool:
        """Authenticate using workload identity federation.
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not self.workload_identity_provider:
            raise ValueError("Workload identity provider is required for WIF authentication")
        
        # Configure workload identity
        result = subprocess.run(
            [
                "gcloud", "config", "set", "auth/credential_file_override",
                "/tmp/tmp.json"  # This is a placeholder, the actual file is managed by gcloud
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to configure workload identity: {result.stderr}")
            return False
        
        # Configure impersonation
        if self.service_account_email:
            result = subprocess.run(
                ["gcloud", "config", "set", "auth/impersonate_service_account", self.service_account_email],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to configure service account impersonation for WIF: {result.stderr}")
                return False
        
        # Set project
        result = subprocess.run(
            ["gcloud", "config", "set", "project", self.gcp_config.project_id],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to set project: {result.stderr}")
            return False
        
        self.authenticated = True
        logger.info("Successfully configured workload identity federation")
        return True
    
    def _authenticate_with_application_default(self) -> bool:
        """Authenticate using application default credentials.
        
        Returns:
            True if authentication successful, False otherwise
        """
        # Check if already authenticated
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Already authenticated with application default credentials")
        else:
            # If service account key is provided, use it to generate ADC
            if self.service_account_key:
                key_file = self._write_key_to_secure_file()
                
                result = subprocess.run(
                    ["gcloud", "auth", "application-default", "login", "--no-launch-browser"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.error(f"Failed to authenticate with application default credentials: {result.stderr}")
                    return False
            else:
                logger.error("No service account key provided for application default authentication")
                return False
        
        # Set project
        result = subprocess.run(
            ["gcloud", "config", "set", "project", self.gcp_config.project_id],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"Failed to set project: {result.stderr}")
            return False
        
        self.authenticated = True
        logger.info("Successfully authenticated with application default credentials")
        return True
    
    def clean_up(self) -> None:
        """Clean up authentication resources."""
        secure_cleanup.cleanup()
        logger.info("Cleaned up authentication resources")
    
    def __del__(self):
        """Ensure cleanup when object is destroyed."""
        try:
            self.clean_up()
        except:
            pass


class GitHubAuth:
    """Securely manages GitHub authentication."""
    
    def __init__(
        self,
        github_config: GitHubConfig
    ):
        """Initialize GitHub authentication.
        
        Args:
            github_config: GitHub configuration
        """
        self.github_config = github_config
        self.authenticated = False
        self.temp_dir = None
        self._token_file_path = None
    
    def authenticate(self) -> bool:
        """Authenticate with GitHub using the provided token.
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not self.github_config.token:
            logger.error("GitHub token is required for authentication")
            return False
        
        logger.info("Authenticating with GitHub")
        
        try:
            # Create a secure temporary directory
            if not self.temp_dir:
                self._create_secure_temp_dir()
            
            # Write token to secure file
            token_file = self.temp_dir / f"gh_token_{uuid.uuid4().hex}.txt"
            with open(token_file, "w") as f:
                f.write(self.github_config.token)
            
            # Set restrictive permissions
            token_file.chmod(0o600)
            
            # Register for cleanup
            secure_cleanup.register_temp_file(token_file)
            self._token_file_path = token_file
            
            # Authenticate with GitHub CLI
            result = subprocess.run(
                ["gh", "auth", "login", "--with-token"],
                input=self.github_config.token,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to authenticate with GitHub: {result.stderr}")
                return False
            
            # Verify authentication
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to verify GitHub authentication: {result.stderr}")
                return False
            
            self.authenticated = True
            logger.info("Successfully authenticated with GitHub")
            return True
        except Exception as e:
            logger.error(f"GitHub authentication failed: {e}")
            return False
    
    def _create_secure_temp_dir(self) -> Path:
        """Create a secure temporary directory with restricted permissions.
        
        Returns:
            Path to the temporary directory
        """
        # Create a temporary directory with restrictive permissions (0700)
        temp_dir = tempfile.mkdtemp(prefix="github_auth_")
        temp_path = Path(temp_dir)
        
        # Set permissions to owner-only
        temp_path.chmod(0o700)
        
        # Register for cleanup
        secure_cleanup.register_temp_dir(temp_path)
        
        self.temp_dir = temp_path
        logger.debug(f"Created secure temporary directory: {temp_path}")
        return temp_path
    
    def clean_up(self) -> None:
        """Clean up authentication resources."""
        secure_cleanup.cleanup()
        logger.info("Cleaned up GitHub authentication resources")
    
    def __del__(self):
        """Ensure cleanup when object is destroyed."""
        try:
            self.clean_up()
        except:
            pass


def main():
    """Main function to demonstrate usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Secure GCP Authentication CLI")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--region", required=True, help="GCP region")
    parser.add_argument("--zone", help="GCP zone")
    parser.add_argument("--method", choices=[m.value for m in AuthMethod], 
                       default=AuthMethod.SERVICE_ACCOUNT_KEY.value, help="Authentication method")
    parser.add_argument("--service-account-key", help="Service account key JSON")
    parser.add_argument("--service-account-email", help="Service account email for impersonation")
    parser.add_argument("--workload-identity-provider", help="Workload identity provider ID")
    parser.add_argument("--github-org", help="GitHub organization name")
    parser.add_argument("--github-repo", help="GitHub repository name")
    parser.add_argument("--github-token", help="GitHub access token")
    parser.add_argument("--use-fine-grained-token", action="store_true", 
                       help="Indicates if the GitHub token is a fine-grained token")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Configure GCP authentication
    gcp_config = GCPConfig(
        project_id=args.project_id,
        region=args.region,
        zone=args.zone
    )
    
    auth_method = AuthMethod(args.method)
    
    # Get service account key from file or environment variable
    service_account_key = args.service_account_key
    if not service_account_key:
        service_account_key = os.environ.get("GCP_MASTER_SERVICE_JSON")
    
    # Get GitHub token from environment variable if not provided
    github_token = args.github_token
    if not github_token:
        if args.use_fine_grained_token:
            github_token = os.environ.get("GH_FINE_GRAINED_TOKEN")
        else:
            github_token = os.environ.get("GH_CLASSIC_PAT_TOKEN")
    
    # Initialize GCP authentication
    gcp_auth = GCPAuth(
        gcp_config=gcp_config,
        auth_method=auth_method,
        service_account_key=service_account_key,
        service_account_email=args.service_account_email,
        workload_identity_provider=args.workload_identity_provider
    )
    
    # Authenticate with GCP
    if gcp_auth.authenticate():
        logger.info("GCP authentication successful")
    else:
        logger.error("GCP authentication failed")
        return 1
    
    # Initialize GitHub authentication if requested
    if args.github_org or args.github_token:
        github_config = GitHubConfig(
            org_name=args.github_org or "",
            repo_name=args.github_repo,
            token=github_token,
            use_fine_grained_token=args.use_fine_grained_token
        )
        
        github_auth = GitHubAuth(github_config=github_config)
        
        # Authenticate with GitHub
        if github_auth.authenticate():
            logger.info("GitHub authentication successful")
        else:
            logger.error("GitHub authentication failed")
            return 1
    
    logger.info("Authentication completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())