#!/usr/bin/env python3
"""
GitHub PAT Rotation Tool for AI Orchestra.

This script automates the secure rotation of GitHub Personal Access Tokens
across multiple repositories with minimal disruption to workflows.
"""

import argparse
import os
import logging
import requests
import json
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("pat_rotation")

class GitHubPATRotator:
    """Manages secure rotation of GitHub Personal Access Tokens."""
    
    def __init__(self, github_username: str, current_pat: str):
        """Initialize the PAT rotator.
        
        Args:
            github_username: GitHub username for API operations
            current_pat: Current PAT with sufficient permissions for token creation
        """
        self.github_username = github_username
        self.current_pat = current_pat
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {current_pat}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def create_new_token(self, token_name: str, scopes: List[str]) -> Optional[Dict]:
        """Create a new GitHub PAT with specified scopes.
        
        Args:
            token_name: Descriptive name for the new token
            scopes: List of GitHub permission scopes
            
        Returns:
            Dictionary containing token details or None if creation failed
        """
        endpoint = f"{self.api_base}/authorizations"
        
        data = {
            "note": f"{token_name} (created: {datetime.now().strftime('%Y-%m-%d')})",
            "scopes": scopes
        }
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create new token: {str(e)}")
            return None
    
    def update_github_secret(self, repo_name: str, secret_name: str, secret_value: str) -> bool:
        """Update a GitHub repository secret with the new PAT.
        
        Args:
            repo_name: Name of the repository to update
            secret_name: Name of the secret to update
            secret_value: New value for the secret
            
        Returns:
            True if update was successful, False otherwise
        """
        # Get public key for the repository
        key_endpoint = f"{self.api_base}/repos/{self.github_username}/{repo_name}/actions/secrets/public-key"
        
        try:
            key_response = requests.get(key_endpoint, headers=self.headers)
            key_response.raise_for_status()
            key_data = key_response.json()
            
            # Use the public key to encrypt the secret
            from nacl import encoding, public
            
            public_key = public.PublicKey(key_data["key"].encode("utf-8"), encoding.Base64Encoder())
            sealed_box = public.SealedBox(public_key)
            encrypted_secret = sealed_box.encrypt(secret_value.encode("utf-8"))
            encrypted_secret_base64 = encoding.Base64Encoder.encode(encrypted_secret).decode("utf-8")
            
            # Update the secret
            secret_endpoint = f"{self.api_base}/repos/{self.github_username}/{repo_name}/actions/secrets/{secret_name}"
            secret_data = {
                "encrypted_value": encrypted_secret_base64,
                "key_id": key_data["key_id"]
            }
            
            secret_response = requests.put(secret_endpoint, headers=self.headers, json=secret_data)
            secret_response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to update secret in {repo_name}: {str(e)}")
            return False
    
    def rotate_pat(self, token_name: str, scopes: List[str], repos_to_update: List[str], secret_name: str = "GITHUB_PAT") -> bool:
        """Perform a complete PAT rotation process.
        
        Args:
            token_name: Name for the new token
            scopes: List of permission scopes for the new token
            repos_to_update: List of repositories to update with new token
            secret_name: Name of the secret to update
            
        Returns:
            True if rotation was successful overall, False otherwise
        """
        logger.info(f"Creating new PAT with scopes: {', '.join(scopes)}")
        new_token = self.create_new_token(token_name, scopes)
        
        if not new_token:
            logger.error("Failed to create new token")
            return False
        
        new_token_value = new_token["token"]
        logger.info(f"Successfully created new PAT: {token_name}")
        
        # Update the PAT in all specified repositories
        success_count = 0
        for repo in repos_to_update:
            logger.info(f"Updating PAT in repository: {repo}")
            if self.update_github_secret(repo, secret_name, new_token_value):
                success_count += 1
                logger.info(f"Successfully updated PAT in {repo}")
            else:
                logger.warning(f"Failed to update PAT in {repo}")
        
        # Allow time for GitHub to propagate the secrets
        if success_count > 0:
            logger.info(f"Waiting for GitHub to propagate secrets...")
            time.sleep(30)  # Wait 30 seconds for propagation
        
        # Return success if at least half of the repositories were updated
        return success_count >= len(repos_to_update) / 2


def main():
    """Entry point for the script."""
    parser = argparse.ArgumentParser(description="Rotate GitHub Personal Access Tokens safely")
    parser.add_argument("--username", required=True, help="GitHub username")
    parser.add_argument("--current-pat", required=True, help="Current GitHub PAT with sufficient permissions")
    parser.add_argument("--token-name", required=True, help="Name for the new PAT")
    parser.add_argument("--scopes", required=True, help="Comma-separated list of scopes for the new PAT")
    parser.add_argument("--repos", required=True, help="Comma-separated list of repositories to update")
    parser.add_argument("--secret-name", default="GITHUB_PAT", help="Name of the secret to update (default: GITHUB_PAT)")
    
    args = parser.parse_args()
    
    rotator = GitHubPATRotator(args.username, args.current_pat)
    scopes = [s.strip() for s in args.scopes.split(",")]
    repos = [r.strip() for r in args.repos.split(",")]
    
    success = rotator.rotate_pat(args.token_name, scopes, repos, args.secret_name)
    
    if success:
        logger.info("PAT rotation completed successfully")
        return 0
    else:
        logger.error("PAT rotation failed")
        return 1


if __name__ == "__main__":
    exit(main())