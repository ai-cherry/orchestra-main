#!/usr/bin/env python3
# validate_secrets.py - Validates Secret Manager access

import sys
import argparse
try:
    from google.cloud import secretmanager
except ImportError:
    print("Google Cloud Secret Manager library not installed.")
    print("Install it with: pip install google-cloud-secret-manager")
    sys.exit(1)

def validate_secrets(project_id):
    """Validate access to required secrets"""
    required_secrets = [
        "OPENAI_API_KEY", 
        "PORTKEY_API_KEY"
    ]
    
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_path = f"projects/{project_id}"
        
        # List all available secrets
        secrets = client.list_secrets(request={"parent": project_path})
        available_secrets = [s.name.split("/")[-1] for s in secrets]
        
        print(f"* Found {len(available_secrets)} secrets in project")
        
        # Check for required secrets
        results = {}
        for secret_id in required_secrets:
            has_secret = secret_id in available_secrets
            
            # Try to access the secret if it exists
            secret_accessible = False
            if has_secret:
                try:
                    name = f"{project_path}/secrets/{secret_id}/versions/latest"
                    client.access_secret_version(name=name)
                    secret_accessible = True
                except Exception as e:
                    print(f"* Error accessing {secret_id}: {str(e)}")
            
            results[secret_id] = {
                "exists": has_secret,
                "accessible": secret_accessible
            }
        
        return True, results
    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description="Validate Secret Manager access")
    parser.add_argument("--project", required=True, help="GCP Project ID")
    parser.add_argument("--location", required=True, help="GCP Location")
    args = parser.parse_args()
    
    print("### Secret Manager Validation")
    success, results = validate_secrets(args.project)
    
    if success and isinstance(results, dict):
        for secret_id, status in results.items():
            exists_status = "✅" if status["exists"] else "❌"
            access_status = "✅" if status["accessible"] else "❌"
            print(f"* {secret_id}: Exists: {exists_status}, Accessible: {access_status}")
        
        # Overall status
        all_exist = all(r["exists"] for r in results.values())
        all_accessible = all(r["accessible"] for r in results.values())
        print(f"\n### Overall Secret Manager Validation: {'✅' if all_exist and all_accessible else '❌'}")
        
        return 0 if all_exist and all_accessible else 1
    else:
        print(f"* Failed to validate secrets: {results}")
        print(f"\n### Overall Secret Manager Validation: ❌")
        return 1

if __name__ == "__main__":
    sys.exit(main())
