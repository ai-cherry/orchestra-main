#!/usr/bin/env python3
"""
WIF Error Handler and Recovery

This script provides enhanced error handling and recovery procedures for the
Workload Identity Federation (WIF) implementation in the AI Orchestra project.
It helps ensure robust error handling by:

1. Providing comprehensive error handling for WIF setup and verification
2. Implementing recovery procedures for partial failures
3. Setting up detailed logging for better troubleshooting
4. Offering a wrapper for WIF scripts with enhanced error handling

Usage:
    python wif_error_handler.py [options] [command]

Options:
    --log-file PATH       Path to write logs to (default: wif_error.log)
    --log-level LEVEL     Logging level (default: INFO)
    --backup              Create backups before recovery attempts
    --verbose             Show detailed output during processing
    --help                Show this help message and exit

Commands:
    wrap SCRIPT [ARGS]    Wrap a WIF script with enhanced error handling
    recover               Attempt to recover from a failed WIF setup
    diagnose              Diagnose issues with WIF setup
    monitor               Monitor WIF operations in real-time
"""

import argparse
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


# Configure logging
def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_file: Optional path to write logs to
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Create logger
    logger = logging.getLogger("wif_error_handler")
    logger.setLevel(level)
    logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Initialize logger with default settings
logger = setup_logging()


class ErrorCategory(Enum):
    """Categories of errors that can occur during WIF operations."""
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    NETWORK = "network"
    SCRIPT = "script"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class WIFError:
    """Represents an error that occurred during WIF operations."""
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    script: Optional[str] = None
    command: Optional[str] = None
    exit_code: Optional[int] = None
    output: Optional[str] = None
    traceback: Optional[str] = None
    recoverable: bool = False
    recovery_steps: List[str] = field(default_factory=list)


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    success: bool
    message: str
    errors: List[WIFError] = field(default_factory=list)
    recovery_steps_taken: List[str] = field(default_factory=list)


class WIFErrorHandler:
    """
    Error handler for WIF operations.
    
    This class provides functionality to handle errors that occur during
    Workload Identity Federation operations, including error detection,
    categorization, logging, and recovery.
    """
    
    # Common error patterns and their categories
    ERROR_PATTERNS = [
        # Dependency errors
        (r"command not found: (gh|gcloud|jq)", ErrorCategory.DEPENDENCY),
        (r"Please install (.*?) first", ErrorCategory.DEPENDENCY),
        
        # Configuration errors
        (r"Error: Invalid value for .*?: (.*)", ErrorCategory.CONFIGURATION),
        (r"Error: (.*) is not a valid (.*)", ErrorCategory.CONFIGURATION),
        (r"Error: Missing required flag: (.*)", ErrorCategory.CONFIGURATION),
        
        # Authentication errors
        (r"Error: not logged in", ErrorCategory.AUTHENTICATION),
        (r"Error: You are not logged in to gcloud", ErrorCategory.AUTHENTICATION),
        (r"Error: GitHub token not available", ErrorCategory.AUTHENTICATION),
        (r"Permission 'iam.serviceAccounts.getAccessToken' denied", ErrorCategory.AUTHENTICATION),
        
        # Permission errors
        (r"Error: Permission denied", ErrorCategory.PERMISSION),
        (r"Error: You do not have permission to perform this action", ErrorCategory.PERMISSION),
        (r"Error: Required '.*' permission for '.*'", ErrorCategory.PERMISSION),
        
        # Network errors
        (r"Error: Failed to connect to (.*)", ErrorCategory.NETWORK),
        (r"Error: Connection refused", ErrorCategory.NETWORK),
        (r"Error: Connection timed out", ErrorCategory.NETWORK),
        (r"Error: Network error", ErrorCategory.NETWORK),
        
        # Script errors
        (r"syntax error", ErrorCategory.SCRIPT),
        (r"line \d+: (.*)", ErrorCategory.SCRIPT),
        
        # Resource errors
        (r"Error: Resource not found: (.*)", ErrorCategory.RESOURCE),
        (r"Error: Resource already exists: (.*)", ErrorCategory.RESOURCE),
        (r"Error: Resource exhausted: (.*)", ErrorCategory.RESOURCE),
    ]
    
    # Recovery procedures for different error categories
    RECOVERY_PROCEDURES = {
        ErrorCategory.DEPENDENCY: [
            "Check if required dependencies are installed",
            "Install missing dependencies",
            "Verify dependency versions",
        ],
        ErrorCategory.CONFIGURATION: [
            "Check configuration files for errors",
            "Verify environment variables",
            "Reset configuration to defaults",
        ],
        ErrorCategory.AUTHENTICATION: [
            "Re-authenticate with GitHub",
            "Re-authenticate with Google Cloud",
            "Check if tokens are valid",
            "Regenerate tokens if necessary",
        ],
        ErrorCategory.PERMISSION: [
            "Check if user has necessary permissions",
            "Grant missing permissions",
            "Verify service account permissions",
        ],
        ErrorCategory.NETWORK: [
            "Check network connectivity",
            "Verify firewall settings",
            "Check if APIs are accessible",
        ],
        ErrorCategory.SCRIPT: [
            "Check script syntax",
            "Verify script permissions",
            "Restore script from backup",
        ],
        ErrorCategory.RESOURCE: [
            "Check if resource exists",
            "Create missing resources",
            "Remove conflicting resources",
        ],
        ErrorCategory.UNKNOWN: [
            "Check logs for more information",
            "Retry the operation",
            "Contact support for assistance",
        ],
    }
    
    def __init__(
        self,
        log_file: Optional[str] = None,
        log_level: str = "INFO",
        backup: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize the WIF error handler.
        
        Args:
            log_file: Optional path to write logs to
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            backup: Whether to create backups before recovery attempts
            verbose: Whether to show detailed output during processing
        """
        global logger
        logger = setup_logging(log_file, log_level)
        
        self.backup = backup
        self.verbose = verbose
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.debug("Initialized WIF error handler")
    
    def categorize_error(self, error_message: str) -> Tuple[ErrorCategory, List[str]]:
        """
        Categorize an error message based on patterns.
        
        Args:
            error_message: The error message to categorize
            
        Returns:
            A tuple containing the error category and any captured groups
        """
        for pattern, category in self.ERROR_PATTERNS:
            match = re.search(pattern, error_message)
            if match:
                groups = list(match.groups())
                return category, groups
        
        return ErrorCategory.UNKNOWN, []
    
    def determine_severity(self, category: ErrorCategory, error_message: str) -> ErrorSeverity:
        """
        Determine the severity of an error based on its category and message.
        
        Args:
            category: The error category
            error_message: The error message
            
        Returns:
            The error severity
        """
        # Critical errors
        if category == ErrorCategory.AUTHENTICATION and "denied" in error_message:
            return ErrorSeverity.CRITICAL
        
        if category == ErrorCategory.PERMISSION and "denied" in error_message:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category == ErrorCategory.DEPENDENCY:
            return ErrorSeverity.HIGH
        
        if category == ErrorCategory.SCRIPT and "syntax error" in error_message:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category == ErrorCategory.NETWORK:
            return ErrorSeverity.MEDIUM
        
        if category == ErrorCategory.RESOURCE:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        if category == ErrorCategory.CONFIGURATION:
            return ErrorSeverity.LOW
        
        # Default to medium severity
        return ErrorSeverity.MEDIUM
    
    def is_recoverable(self, category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """
        Determine if an error is recoverable based on its category and severity.
        
        Args:
            category: The error category
            severity: The error severity
            
        Returns:
            True if the error is recoverable, False otherwise
        """
        # Critical errors are generally not recoverable
        if severity == ErrorSeverity.CRITICAL:
            return False
        
        # Some high severity errors are not recoverable
        if severity == ErrorSeverity.HIGH and category in [ErrorCategory.SCRIPT]:
            return False
        
        # Most other errors are recoverable
        return True
    
    def get_recovery_steps(self, category: ErrorCategory) -> List[str]:
        """
        Get recovery steps for an error category.
        
        Args:
            category: The error category
            
        Returns:
            A list of recovery steps
        """
        return self.RECOVERY_PROCEDURES.get(category, self.RECOVERY_PROCEDURES[ErrorCategory.UNKNOWN])
    
    def create_error(
        self,
        message: str,
        script: Optional[str] = None,
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
        output: Optional[str] = None,
    ) -> WIFError:
        """
        Create a WIF error object from an error message.
        
        Args:
            message: The error message
            script: The script that generated the error
            command: The command that generated the error
            exit_code: The exit code of the command
            output: The output of the command
            
        Returns:
            A WIF error object
        """
        category, _ = self.categorize_error(message)
        severity = self.determine_severity(category, message)
        recoverable = self.is_recoverable(category, severity)
        recovery_steps = self.get_recovery_steps(category) if recoverable else []
        
        error = WIFError(
            message=message,
            category=category,
            severity=severity,
            script=script,
            command=command,
            exit_code=exit_code,
            output=output,
            traceback=traceback.format_exc() if sys.exc_info()[0] else None,
            recoverable=recoverable,
            recovery_steps=recovery_steps,
        )
        
        logger.error(f"Error: {message} (Category: {category.value}, Severity: {severity.value})")
        
        return error
    
    def log_error(self, error: WIFError) -> None:
        """
        Log a WIF error.
        
        Args:
            error: The error to log
        """
        logger.error(f"Error: {error.message}")
        logger.error(f"Category: {error.category.value}")
        logger.error(f"Severity: {error.severity.value}")
        
        if error.script:
            logger.error(f"Script: {error.script}")
        
        if error.command:
            logger.error(f"Command: {error.command}")
        
        if error.exit_code is not None:
            logger.error(f"Exit Code: {error.exit_code}")
        
        if error.output:
            logger.error(f"Output: {error.output}")
        
        if error.traceback:
            logger.error(f"Traceback: {error.traceback}")
        
        logger.error(f"Recoverable: {error.recoverable}")
        
        if error.recovery_steps:
            logger.error("Recovery Steps:")
            for step in error.recovery_steps:
                logger.error(f"  - {step}")
    
    def wrap_script(self, script_path: str, args: List[str] = None) -> int:
        """
        Wrap a WIF script with enhanced error handling.
        
        Args:
            script_path: The path to the script to wrap
            args: Optional arguments to pass to the script
            
        Returns:
            The exit code of the script
        """
        if args is None:
            args = []
        
        script_path = Path(script_path).resolve()
        
        if not script_path.exists():
            error = self.create_error(f"Script not found: {script_path}")
            self.log_error(error)
            return 1
        
        if not os.access(script_path, os.X_OK):
            logger.warning(f"Script {script_path} is not executable. Making it executable...")
            try:
                os.chmod(script_path, 0o755)
            except Exception as e:
                error = self.create_error(f"Failed to make script executable: {e}")
                self.log_error(error)
                return 1
        
        # Create backup if enabled
        if self.backup:
            backup_path = f"{script_path}.wif-backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            try:
                shutil.copy2(script_path, backup_path)
                logger.debug(f"Created backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Failed to create backup: {e}")
        
        # Run the script with enhanced error handling
        logger.info(f"Running script: {script_path} {' '.join(args)}")
        
        try:
            # Run the script
            process = subprocess.Popen(
                [str(script_path)] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )
            
            # Process output in real-time
            stdout_lines = []
            stderr_lines = []
            
            while True:
                stdout_line = process.stdout.readline()
                stderr_line = process.stderr.readline()
                
                if stdout_line:
                    stdout_lines.append(stdout_line)
                    if self.verbose:
                        logger.info(stdout_line.strip())
                    else:
                        print(stdout_line.strip())
                
                if stderr_line:
                    stderr_lines.append(stderr_line)
                    if "error" in stderr_line.lower() or "warning" in stderr_line.lower():
                        logger.warning(stderr_line.strip())
                    elif self.verbose:
                        logger.debug(stderr_line.strip())
                    else:
                        print(stderr_line.strip(), file=sys.stderr)
                
                if process.poll() is not None:
                    # Process remaining output
                    for line in process.stdout:
                        stdout_lines.append(line)
                        if self.verbose:
                            logger.info(line.strip())
                        else:
                            print(line.strip())
                    
                    for line in process.stderr:
                        stderr_lines.append(line)
                        if "error" in line.lower() or "warning" in line.lower():
                            logger.warning(line.strip())
                        elif self.verbose:
                            logger.debug(line.strip())
                        else:
                            print(line.strip(), file=sys.stderr)
                    
                    break
            
            # Get exit code
            exit_code = process.returncode
            
            # Check for errors
            stdout = "".join(stdout_lines)
            stderr = "".join(stderr_lines)
            
            if exit_code != 0:
                error = self.create_error(
                    message=f"Script exited with non-zero code: {exit_code}",
                    script=str(script_path),
                    command=f"{script_path} {' '.join(args)}",
                    exit_code=exit_code,
                    output=stderr or stdout,
                )
                self.log_error(error)
                
                # Attempt recovery if the error is recoverable
                if error.recoverable:
                    logger.info("Attempting to recover from error...")
                    recovery_result = self.recover_from_error(error)
                    
                    if recovery_result.success:
                        logger.info(f"Recovery successful: {recovery_result.message}")
                        return 0
                    else:
                        logger.error(f"Recovery failed: {recovery_result.message}")
                        return exit_code
            else:
                logger.info(f"Script completed successfully with exit code {exit_code}")
            
            return exit_code
        
        except Exception as e:
            error = self.create_error(
                message=f"Exception while running script: {e}",
                script=str(script_path),
                command=f"{script_path} {' '.join(args)}",
            )
            self.log_error(error)
            return 1
    
    def recover_from_error(self, error: WIFError) -> RecoveryResult:
        """
        Attempt to recover from a WIF error.
        
        Args:
            error: The error to recover from
            
        Returns:
            The result of the recovery attempt
        """
        if not error.recoverable:
            return RecoveryResult(
                success=False,
                message=f"Error is not recoverable: {error.message}",
                errors=[error],
            )
        
        logger.info(f"Attempting to recover from error: {error.message}")
        
        recovery_steps_taken = []
        
        # Implement recovery procedures based on error category
        if error.category == ErrorCategory.DEPENDENCY:
            # Try to install missing dependencies
            if "command not found" in error.message:
                dependency = error.message.split(":")[-1].strip()
                logger.info(f"Attempting to install missing dependency: {dependency}")
                
                try:
                    if dependency == "gh":
                        # Install GitHub CLI
                        logger.info("Installing GitHub CLI...")
                        subprocess.run(
                            [
                                "bash",
                                "-c",
                                "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && sudo apt update && sudo apt install gh -y",
                            ],
                            check=True,
                        )
                        recovery_steps_taken.append(f"Installed GitHub CLI")
                    elif dependency == "gcloud":
                        # Install Google Cloud SDK
                        logger.info("Installing Google Cloud SDK...")
                        subprocess.run(
                            [
                                "bash",
                                "-c",
                                "curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-367.0.0-linux-x86_64.tar.gz && tar -xf google-cloud-sdk-367.0.0-linux-x86_64.tar.gz && ./google-cloud-sdk/install.sh --quiet && ./google-cloud-sdk/bin/gcloud components update --quiet",
                            ],
                            check=True,
                        )
                        recovery_steps_taken.append(f"Installed Google Cloud SDK")
                    elif dependency == "jq":
                        # Install jq
                        logger.info("Installing jq...")
                        subprocess.run(
                            ["sudo", "apt", "install", "jq", "-y"],
                            check=True,
                        )
                        recovery_steps_taken.append(f"Installed jq")
                    else:
                        logger.warning(f"Don't know how to install dependency: {dependency}")
                        return RecoveryResult(
                            success=False,
                            message=f"Don't know how to install dependency: {dependency}",
                            errors=[error],
                        )
                    
                    return RecoveryResult(
                        success=True,
                        message=f"Successfully installed missing dependency: {dependency}",
                        recovery_steps_taken=recovery_steps_taken,
                    )
                except subprocess.CalledProcessError as e:
                    new_error = self.create_error(
                        message=f"Failed to install dependency: {e}",
                        command=str(e.cmd),
                        exit_code=e.returncode,
                        output=e.output if hasattr(e, 'output') else None,
                    )
                    return RecoveryResult(
                        success=False,
                        message=f"Failed to install dependency: {dependency}",
                        errors=[error, new_error],
                        recovery_steps_taken=recovery_steps_taken,
                    )
        
        elif error.category == ErrorCategory.AUTHENTICATION:
            # Try to re-authenticate
            if "GitHub token not available" in error.message:
                logger.info("Attempting to re-authenticate with GitHub...")
                
                try:
                    # Run GitHub login
                    subprocess.run(
                        ["gh", "auth", "login"],
                        check=True,
                    )
                    recovery_steps_taken.append("Re-authenticated with GitHub")
                    
                    return RecoveryResult(
                        success=True,
                        message="Successfully re-authenticated with GitHub",
                        recovery_steps_taken=recovery_steps_taken,
                    )
                except subprocess.CalledProcessError as e:
                    new_error = self.create_error(
                        message=f"Failed to re-authenticate with GitHub: {e}",
                        command=str(e.cmd),
                        exit_code=e.returncode,
                        output=e.output if hasattr(e, 'output') else None,
                    )
                    return RecoveryResult(
                        success=False,
                        message="Failed to re-authenticate with GitHub",
                        errors=[error, new_error],
                        recovery_steps_taken=recovery_steps_taken,
                    )
            
            elif "not logged in to gcloud" in error.message:
                logger.info("Attempting to re-authenticate with Google Cloud...")
                
                try:
                    # Run gcloud login
                    subprocess.run(
                        ["gcloud", "auth", "login"],
                        check=True,
                    )
                    recovery_steps_taken.append("Re-authenticated with Google Cloud")
                    
                    return RecoveryResult(
                        success=True,
                        message="Successfully re-authenticated with Google Cloud",
                        recovery_steps_taken=recovery_steps_taken,
                    )
                except subprocess.CalledProcessError as e:
                    new_error = self.create_error(
                        message=f"Failed to re-authenticate with Google Cloud: {e}",
                        command=str(e.cmd),
                        exit_code=e.returncode,
                        output=e.output if hasattr(e, 'output') else None,
                    )
                    return RecoveryResult(
                        success=False,
                        message="Failed to re-authenticate with Google Cloud",
                        errors=[error, new_error],
                        recovery_steps_taken=recovery_steps_taken,
                    )
        
        # For other error categories, we don't have automated recovery yet
        return RecoveryResult(
            success=False,
            message=f"No automated recovery available for error category: {error.category.value}",
            errors=[error],
            recovery_steps_taken=recovery_steps_taken,
        )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Enhanced error handling for WIF operations."
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to write logs to (default: wif_error.log)",
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backups before recovery attempts",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output during processing",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Wrap command
    wrap_parser = subparsers.add_parser("wrap", help="Wrap a WIF script with enhanced error handling")
    wrap_parser.add_argument("script", help="Path to the script to wrap")
    wrap_parser.add_argument("args", nargs="*", help="Arguments to pass to the script")
    
    # Recover command
    recover_parser = subparsers.add_parser("recover", help="Attempt to recover from a failed WIF setup")
    
    # Diagnose command
    diagnose_parser = subparsers.add_parser("diagnose", help="Diagnose issues with WIF setup")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor WIF operations in real-time")
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()
    
    # Create error handler
    error_handler = WIFErrorHandler(
        log_file=args.log_file,
        log_level=args.log_level,
        backup=args.backup,
        verbose=args.verbose,
    )
    
    # Execute command
    if args.command == "wrap":
        return error_handler.wrap_script(args.script, args.args)
    elif args.command == "recover":
        logger.info("Recovery command not implemented yet")
        return 1
    elif args.command == "diagnose":
        logger.info("Diagnose command not implemented yet")
        return 1
    elif args.command == "monitor":
        logger.info("Monitor command not implemented yet")
        return 1
    else:
        logger.error("No command specified")
        return 1


if __name__ == "__main__":
    sys.exit(main())
