#!/usr/bin/env python3
"""
"""
    """Enum representing the source of credentials."""
    ENV_VAR = "environment_variable"
    FILE = "file"
    os.environ = "os.environ"
    WORKLOAD_IDENTITY = "workload_identity"

@dataclass
class ServiceAccountInfo:
    """Class for storing service account information."""
    def from_json(cls, json_data: Dict[str, Any]) -> "ServiceAccountInfo":
        """Create a ServiceAccountInfo instance from a JSON dictionary."""
            project_id=json_data.get("project_id", ""),
            client_email=json_data.get("client_email", ""),
            private_key_id=json_data.get("private_key_id", ""),
            private_key=json_data.get("private_key", ""),
            client_id=json_data.get("client_id", ""),
        )

    def to_json(self) -> Dict[str, Any]:
        """Convert the ServiceAccountInfo to a JSON dictionary."""
            "type": "service_account",
            "project_id": self.project_id,
            "private_key_id": self.private_key_id,
            "private_key": self.private_key,
            "client_email": self.client_email,
            "client_id": self.client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{self.client_email.replace('@', '%40')}",
        }

    def to_temp_file(self) -> str:
        """Write the service account info to a temporary file and return the path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
            json.dump(self.to_json(), temp_file, indent=2)
            temp_file_path = temp_file.name

        # Set appropriate permissions
        os.chmod(temp_file_path, 0o600)

        return temp_file_path

class CredentialManager:
    """
    """
    def __init__(self, env_prefix: str = "ORCHESTRA"):
        """
        """
        """Load credentials from environment variables."""
        service_account_json = os.environ.get(f"{self.env_prefix}_SERVICE_ACCOUNT_JSON")
        if service_account_json:
            try:

                pass
                # Try to parse as JSON
                service_account_data = json.loads(service_account_json)
                self._service_account_info = ServiceAccountInfo.from_json(service_account_data)
                logger.info("Loaded service account info from environment variable")
            except Exception:

                pass
                # Try to decode as base64
                try:

                    pass
                    decoded = base64.b64decode(service_account_json).decode("utf-8")
                    service_account_data = json.loads(decoded)
                    self._service_account_info = ServiceAccountInfo.from_json(service_account_data)
                    logger.info("Loaded base64-encoded service account info from environment variable")
                except Exception:

                    pass
                    logger.warning(f"Failed to decode service account info from environment variable: {e}")

        # Check for service account key file path
        service_account_path = os.environ.get(f"{self.env_prefix}_SERVICE_ACCOUNT_PATH")
        if service_account_path and not self._service_account_info:
            self.load_service_account_from_file(service_account_path)

    def load_service_account_from_file(self, file_path: Union[str, Path]) -> bool:
        """
        """
            with open(file_path, "r") as f:
                service_account_data = json.load(f)

            self._service_account_info = ServiceAccountInfo.from_json(service_account_data)
            logger.info(f"Loaded service account info from file: {file_path}")
            return True
        except Exception:

            pass
            logger.warning(f"Failed to load service account info from file {file_path}: {e}")
            return False

    def get_service_account_key(self) -> Optional[ServiceAccountInfo]:
        """
        """
        """
        """
        """
        """
        return os.environ.get(f"{self.env_prefix}_PROJECT_ID") or os.environ.get("VULTR_PROJECT_ID")

    def secure_service_account_key(self, file_path: Union[str, Path]) -> bool:
        """
        """
                logger.info(f"Removed service account key file: {file_path}")
                return True
            except Exception:

                pass
                logger.warning(f"Failed to remove service account key file {file_path}: {e}")
                return False
        return False

    def cleanup(self) -> None:
        """Clean up temporary files."""
                logger.warning(f"Failed to remove temporary file {temp_file}: {e}")

        self._temp_files = []

    def __del__(self) -> None:
        """Destructor to ensure cleanup."""
    """
    """
        "service-account-key.json",
        ".credentials/service-account-key.json",
    ]

    for file_path in service_account_files:
        if os.path.exists(file_path):
            logger.info(f"Securing service account key file: {file_path}")
            credential_manager.secure_service_account_key(file_path)

    # Store the project ID in an environment variable
    project_id = credential_manager.get_project_id()
    if project_id:
        logger.info(f"Setting environment variable ORCHESTRA_PROJECT_ID={project_id}")
        os.environ["ORCHESTRA_PROJECT_ID"] = project_id

    logger.info("Credentials secured successfully")

if __name__ == "__main__":
    secure_credentials()
