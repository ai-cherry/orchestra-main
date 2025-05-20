"""
Custom exceptions for the GCP Secret Manager client.
"""


class SecretAccessError(Exception):
    """Base exception for all secret access errors."""

    pass


class SecretNotFoundError(SecretAccessError):
    """Raised when a requested secret does not exist."""

    def __init__(self, secret_id, project_id=None):
        self.secret_id = secret_id
        self.project_id = project_id
        message = f"Secret '{secret_id}' not found"
        if project_id:
            message += f" in project '{project_id}'"
        super().__init__(message)


class SecretVersionNotFoundError(SecretAccessError):
    """Raised when a requested secret version does not exist."""

    def __init__(self, secret_id, version, project_id=None):
        self.secret_id = secret_id
        self.version = version
        self.project_id = project_id
        message = f"Version '{version}' of secret '{secret_id}' not found"
        if project_id:
            message += f" in project '{project_id}'"
        super().__init__(message)


class SecretAccessPermissionError(SecretAccessError):
    """Raised when the caller does not have permission to access the secret."""

    def __init__(self, secret_id, project_id=None):
        self.secret_id = secret_id
        self.project_id = project_id
        message = f"Permission denied for secret '{secret_id}'"
        if project_id:
            message += f" in project '{project_id}'"
        super().__init__(message)


class SecretOperationError(SecretAccessError):
    """Raised when an operation on a secret fails for other reasons."""

    def __init__(self, secret_id, operation, error, project_id=None):
        self.secret_id = secret_id
        self.operation = operation
        self.original_error = error
        self.project_id = project_id

        message = f"Operation '{operation}' failed for secret '{secret_id}'"
        if project_id:
            message += f" in project '{project_id}'"
        message += f": {str(error)}"

        super().__init__(message)
