#!/usr/bin/env python3
"""
deploy_admin_ui_api.py - Deploy Admin UI to DigitalOcean App Platform

This script deploys the Admin UI static site to DigitalOcean App Platform using
the DigitalOcean API. It handles authentication, app creation/update, domain
configuration, and uploading the contents of the admin-ui/dist directory.

Usage:
    python deploy_admin_ui_api.py --token YOUR_DO_API_TOKEN [--skip-build]

Requirements:
    - requests library: pip install requests
    - Admin UI built (run `cd admin-ui && pnpm build` first)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
import requests
import mimetypes
import base64

# Constants
API_BASE_URL = "https://api.digitalocean.com/v2"
APP_NAME = "admin-ui-prod"
DOMAIN = "cherry-ai.me"
REGION = "sfo2"  # San Francisco region

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Deploy Admin UI to DigitalOcean App Platform")
    parser.add_argument("--token", required=True, help="DigitalOcean API token")
    parser.add_argument("--skip-build", action="store_true", help="Skip building the Admin UI")
    return parser.parse_args()


def build_admin_ui():
    """Build the Admin UI using pnpm."""
    logger.info("Building Admin UI...")
    
    # Get the repository root directory
    repo_root = Path(__file__).resolve().parent
    admin_ui_dir = repo_root / "admin-ui"
    
    # Check if the admin-ui directory exists
    if not admin_ui_dir.exists():
        logger.error(f"Admin UI directory not found at {admin_ui_dir}")
        sys.exit(1)
    
    # Change to the admin-ui directory
    os.chdir(admin_ui_dir)
    
    # Install dependencies
    logger.info("Installing dependencies...")
    result = os.system("pnpm install")
    if result != 0:
        logger.error("Failed to install dependencies")
        sys.exit(1)
    
    # Build the project
    logger.info("Running build...")
    result = os.system("pnpm build")
    if result != 0:
        logger.error("Build failed")
        sys.exit(1)
    
    # Check if build was successful
    dist_dir = admin_ui_dir / "dist"
    index_html = dist_dir / "index.html"
    if not dist_dir.exists() or not index_html.exists():
        logger.error("Build failed: dist directory or index.html is missing")
        sys.exit(1)
    
    logger.info("Build successful!")
    return dist_dir


def get_headers(token):
    """Get API request headers with authorization."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def get_app_by_name(token, app_name):
    """Get app by name if it exists."""
    headers = get_headers(token)
    response = requests.get(f"{API_BASE_URL}/apps", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to list apps: {response.text}")
        return None
    
    apps = response.json().get("apps", [])
    for app in apps:
        if app.get("spec", {}).get("name") == app_name:
            return app
    
    return None


def create_or_update_app(token, dist_dir):
    """Create or update the app on DigitalOcean App Platform."""
    headers = get_headers(token)
    
    # Check if app already exists
    existing_app = get_app_by_name(token, APP_NAME)
    
    # Prepare app spec
    app_spec = {
        "name": APP_NAME,
        "region": REGION,
        "static_sites": [
            {
                "name": "admin-ui-site",
                "source_dir": str(dist_dir),
                "output_dir": ".",
                "index_document": "index.html",
                "error_document": "index.html",
                "catchall_document": "index.html",
                "routes": [
                    {"path": "/"}
                ]
            }
        ],
        "domains": [
            {
                "domain": DOMAIN,
                "type": "PRIMARY"
            }
        ]
    }
    
    if existing_app:
        logger.info(f"Updating existing app: {APP_NAME}")
        app_id = existing_app.get("id")
        response = requests.put(
            f"{API_BASE_URL}/apps/{app_id}",
            headers=headers,
            json={"spec": app_spec}
        )
    else:
        logger.info(f"Creating new app: {APP_NAME}")
        response = requests.post(
            f"{API_BASE_URL}/apps",
            headers=headers,
            json={"spec": app_spec}
        )
    
    if response.status_code not in (200, 201):
        logger.error(f"Failed to create/update app: {response.text}")
        sys.exit(1)
    
    app_data = response.json().get("app")
    logger.info(f"App {app_data.get('id')} created/updated successfully")
    return app_data


def upload_static_files(token, app_id, dist_dir):
    """Upload static files to the app."""
    headers = get_headers(token)
    
    # Get deployment ID
    response = requests.get(
        f"{API_BASE_URL}/apps/{app_id}/deployments",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get deployments: {response.text}")
        sys.exit(1)
    
    deployments = response.json().get("deployments", [])
    if not deployments:
        logger.error("No deployments found")
        sys.exit(1)
    
    # Use the latest deployment
    deployment_id = deployments[0].get("id")
    
    # Create a new deployment
    response = requests.post(
        f"{API_BASE_URL}/apps/{app_id}/deployments",
        headers=headers
    )
    
    if response.status_code != 201:
        logger.error(f"Failed to create deployment: {response.text}")
        sys.exit(1)
    
    new_deployment = response.json().get("deployment")
    new_deployment_id = new_deployment.get("id")
    
    # Upload files
    logger.info("Uploading static files...")
    
    # Walk through the dist directory and upload each file
    for root, _, files in os.walk(dist_dir):
        for file in files:
            file_path = Path(root) / file
            relative_path = file_path.relative_to(dist_dir)
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(str(file_path))
            if content_type is None:
                content_type = "application/octet-stream"
            
            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()
            
            # Encode file content as base64
            encoded_content = base64.b64encode(file_content).decode("utf-8")
            
            # Upload file
            upload_headers = get_headers(token)
            upload_headers["Content-Type"] = content_type
            
            upload_response = requests.put(
                f"{API_BASE_URL}/apps/{app_id}/deployments/{new_deployment_id}/components/admin-ui-site/files/{relative_path}",
                headers=upload_headers,
                data=encoded_content
            )
            
            if upload_response.status_code != 200:
                logger.error(f"Failed to upload {relative_path}: {upload_response.text}")
            else:
                logger.info(f"Uploaded {relative_path}")
    
    # Finalize deployment
    response = requests.post(
        f"{API_BASE_URL}/apps/{app_id}/deployments/{new_deployment_id}/actions/finalize",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to finalize deployment: {response.text}")
        sys.exit(1)
    
    logger.info("Deployment finalized successfully")
    return new_deployment_id


def check_deployment_status(token, app_id, deployment_id):
    """Check the status of the deployment."""
    headers = get_headers(token)
    
    logger.info("Checking deployment status...")
    
    # Poll for deployment status
    for _ in range(30):  # Try for 5 minutes (30 * 10 seconds)
        response = requests.get(
            f"{API_BASE_URL}/apps/{app_id}/deployments/{deployment_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get deployment status: {response.text}")
            break
        
        deployment = response.json().get("deployment", {})
        phase = deployment.get("phase")
        
        logger.info(f"Deployment status: {phase}")
        
        if phase == "ACTIVE":
            logger.info("Deployment completed successfully!")
            return True
        elif phase in ("ERROR", "CANCELED", "FAILED"):
            logger.error(f"Deployment failed with status: {phase}")
            return False
        
        # Wait before checking again
        time.sleep(10)
    
    logger.warning("Deployment status check timed out")
    return False


def check_site_accessibility():
    """Check if the site is accessible."""
    logger.info(f"Checking if {DOMAIN} is accessible...")
    
    try:
        response = requests.get(f"https://{DOMAIN}", timeout=10)
        status_code = response.status_code
        
        if status_code == 200:
            logger.info(f"Site is accessible! Status code: {status_code}")
            return True
        else:
            logger.warning(f"Site returned status code: {status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"Site is not yet accessible: {e}")
        return False


def main():
    """Main function."""
    args = parse_args()
    token = args.token
    
    # Build Admin UI if not skipped
    if not args.skip_build:
        dist_dir = build_admin_ui()
    else:
        logger.info("Skipping build step...")
        # Get the repository root directory
        repo_root = Path(__file__).resolve().parent
        dist_dir = repo_root / "admin-ui" / "dist"
        
        # Check if dist directory exists
        if not dist_dir.exists():
            logger.error(f"Dist directory not found at {dist_dir}")
            sys.exit(1)
    
    # Create or update app
    app_data = create_or_update_app(token, dist_dir)
    app_id = app_data.get("id")
    
    # Upload static files
    deployment_id = upload_static_files(token, app_id, dist_dir)
    
    # Check deployment status
    deployment_success = check_deployment_status(token, app_id, deployment_id)
    
    if deployment_success:
        # Check site accessibility
        site_accessible = check_site_accessibility()
        
        if site_accessible:
            logger.info(f"Deployment complete! Site is accessible at https://{DOMAIN}")
        else:
            logger.info(f"Deployment complete, but site is not yet accessible at https://{DOMAIN}")
            logger.info("This is normal during initial deployment or DNS propagation.")
            logger.info("Please check again in a few minutes.")
    else:
        logger.error("Deployment failed or timed out")
        sys.exit(1)


if __name__ == "__main__":
    main()
